from __future__ import annotations

import json
import math
import os
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from models.barcode_food_models import (
    BarcodeFoodCandidate,
    NormalizedBarcode,
    ProviderLookupResult,
)

USDA_PROVIDER_NAME = "USDA FoodData Central"
USDA_API_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
USDA_LICENSE = "Public Domain"

JsonFetcher = Callable[[str, str, dict[str, str], bytes | None, float], dict[str, Any]]


def _default_json_fetcher(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    timeout: float,
) -> dict[str, Any]:
    request = Request(url, data=body, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _text(value: object) -> str | None:
    normalized = " ".join(str(value or "").strip().split())
    return normalized or None


def _finite_non_negative(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    return parsed


def _nutrient_identity(entry: dict[str, Any]) -> tuple[int | None, str, str]:
    nutrient = entry.get("nutrient")
    nested = nutrient if isinstance(nutrient, dict) else {}
    raw_id = entry.get("nutrientId", nested.get("id"))
    try:
        nutrient_id = int(raw_id) if raw_id is not None else None
    except (TypeError, ValueError):
        nutrient_id = None
    name = _text(entry.get("nutrientName", nested.get("name"))) or ""
    unit = _text(entry.get("unitName", nested.get("unitName"))) or ""
    return nutrient_id, name.casefold(), unit.casefold()


def _nutrient_amount(entry: dict[str, Any]) -> float | None:
    return _finite_non_negative(entry.get("amount", entry.get("value")))


def _extract_macros(payload: dict[str, Any]) -> dict[str, float | None]:
    entries = payload.get("foodNutrients")
    if not isinstance(entries, list):
        entries = []

    result: dict[str, float | None] = {
        "calories": None,
        "protein": None,
        "carbs": None,
        "fat": None,
    }
    calorie_fallback: float | None = None
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            continue
        nutrient_id, name, unit = _nutrient_identity(raw_entry)
        amount = _nutrient_amount(raw_entry)
        if amount is None:
            continue
        if nutrient_id == 1008:
            result["calories"] = amount
        elif nutrient_id in {2047, 2048} and unit == "kcal":
            calorie_fallback = (
                calorie_fallback if calorie_fallback is not None else amount
            )
        elif nutrient_id == 1003:
            result["protein"] = amount
        elif nutrient_id == 1005:
            result["carbs"] = amount
        elif nutrient_id == 1004:
            result["fat"] = amount
        elif name == "energy" and unit == "kcal" and calorie_fallback is None:
            calorie_fallback = amount
        elif name == "protein" and result["protein"] is None:
            result["protein"] = amount
        elif (
            name in {"carbohydrate, by difference", "carbohydrate"}
            and result["carbs"] is None
        ):
            result["carbs"] = amount
        elif (
            name in {"total lipid (fat)", "total fat", "fat"} and result["fat"] is None
        ):
            result["fat"] = amount

    if result["calories"] is None:
        result["calories"] = calorie_fallback
    return result


class UsdaBrandedFoodProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        fetch_json: JsonFetcher | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.api_key = (
            api_key if api_key is not None else os.getenv("FDC_API_KEY", "")
        ).strip()
        self.fetch_json = fetch_json or _default_json_fetcher
        self.timeout_seconds = timeout_seconds

    def lookup(self, barcode: NormalizedBarcode) -> ProviderLookupResult:
        if not self.api_key:
            return ProviderLookupResult(
                status="unavailable",
                provider=USDA_PROVIDER_NAME,
                reason="FDC_API_KEY is not configured.",
            )

        query_barcode = (
            barcode.lookup_variants[1]
            if len(barcode.lookup_variants) > 1
            else barcode.normalized_gtin
        )
        search_url = f"{USDA_API_BASE_URL}/foods/search?api_key={self.api_key}"
        search_body = json.dumps(
            {"query": query_barcode, "dataType": ["Branded"], "pageSize": 25}
        ).encode("utf-8")

        try:
            search_payload = self.fetch_json(
                "POST",
                search_url,
                {"Accept": "application/json", "Content-Type": "application/json"},
                search_body,
                self.timeout_seconds,
            )
            exact_match = self._find_exact_match(search_payload, barcode)
            if exact_match is None:
                return ProviderLookupResult(
                    status="not_found",
                    provider=USDA_PROVIDER_NAME,
                    reason="USDA returned no exact branded GTIN match.",
                )

            fdc_id = exact_match.get("fdcId")
            if fdc_id is None:
                return ProviderLookupResult(
                    status="not_found",
                    provider=USDA_PROVIDER_NAME,
                    reason="USDA exact match did not include an FDC ID.",
                )
            detail_url = f"{USDA_API_BASE_URL}/food/{fdc_id}?api_key={self.api_key}"
            detail_payload = self.fetch_json(
                "GET",
                detail_url,
                {"Accept": "application/json"},
                None,
                self.timeout_seconds,
            )
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ):
            return ProviderLookupResult(
                status="unavailable",
                provider=USDA_PROVIDER_NAME,
                reason="USDA FoodData Central could not be reached.",
            )

        candidate = self._build_candidate(detail_payload, exact_match, barcode)
        return ProviderLookupResult(
            status="found" if _candidate_has_all_macros(candidate) else "incomplete",
            provider=USDA_PROVIDER_NAME,
            candidate=candidate,
            reason=None
            if _candidate_has_all_macros(candidate)
            else "USDA product nutrition is incomplete.",
        )

    @staticmethod
    def _find_exact_match(
        payload: dict[str, Any],
        barcode: NormalizedBarcode,
    ) -> dict[str, Any] | None:
        foods = payload.get("foods")
        if not isinstance(foods, list):
            return None
        from services.barcode_food_service import try_normalize_barcode

        for food in foods:
            if not isinstance(food, dict):
                continue
            provider_barcode = try_normalize_barcode(str(food.get("gtinUpc") or ""))
            if (
                provider_barcode
                and provider_barcode.normalized_gtin == barcode.normalized_gtin
            ):
                return food
        return None

    @staticmethod
    def _build_candidate(
        detail: dict[str, Any],
        search_match: dict[str, Any],
        barcode: NormalizedBarcode,
    ) -> BarcodeFoodCandidate:
        merged = {**search_match, **detail}
        macros = _extract_macros(merged)
        serving_size = _finite_non_negative(merged.get("servingSize"))
        serving_unit = _text(merged.get("servingSizeUnit"))
        serving_label = _text(merged.get("householdServingFullText"))
        fdc_id = str(merged.get("fdcId") or search_match.get("fdcId") or "")
        provider_barcode = _text(merged.get("gtinUpc")) or barcode.lookup_variants[-1]
        return BarcodeFoodCandidate(
            source_name=USDA_PROVIDER_NAME,
            source_record_id=fdc_id,
            barcode=provider_barcode,
            normalized_gtin=barcode.normalized_gtin,
            product_name=_text(merged.get("description")) or "",
            brand_name=_text(merged.get("brandOwner") or merged.get("brandName")),
            food_category=_text(merged.get("foodCategory")),
            calories_per_100g=macros["calories"],
            protein_g_per_100g=macros["protein"],
            carbs_g_per_100g=macros["carbs"],
            fat_g_per_100g=macros["fat"],
            serving_size=serving_size,
            serving_size_unit=serving_unit,
            serving_label=serving_label,
            license=USDA_LICENSE,
            source_url=f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{fdc_id}",
            source_payload=detail,
        )


def _candidate_has_all_macros(candidate: BarcodeFoodCandidate) -> bool:
    return all(
        value is not None
        for value in (
            candidate.calories_per_100g,
            candidate.protein_g_per_100g,
            candidate.carbs_g_per_100g,
            candidate.fat_g_per_100g,
        )
    )
