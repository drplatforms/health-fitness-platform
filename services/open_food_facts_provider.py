from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from models.barcode_food_models import (
    BarcodeFoodCandidate,
    NormalizedBarcode,
    ProviderLookupResult,
)

OPEN_FOOD_FACTS_PROVIDER_NAME = "Open Food Facts"
OPEN_FOOD_FACTS_API_BASE_URL = "https://world.openfoodfacts.org/api/v2"
OPEN_FOOD_FACTS_LICENSE = "Open Database License (ODbL)"

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


def _serving_grams(product: dict[str, Any]) -> tuple[float | None, str | None]:
    quantity = _finite_non_negative(product.get("serving_quantity"))
    unit = (_text(product.get("serving_quantity_unit")) or "").casefold()
    if quantity and unit in {"g", "gram", "grams"}:
        return quantity, _text(product.get("serving_size"))

    serving_size = _text(product.get("serving_size"))
    if serving_size:
        match = re.fullmatch(
            r"\s*(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\s*", serving_size, re.IGNORECASE
        )
        if match:
            return float(match.group(1)), serving_size
    return None, None


class OpenFoodFactsProvider:
    def __init__(
        self,
        *,
        user_agent: str | None = None,
        fetch_json: JsonFetcher | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.user_agent = (
            user_agent
            if user_agent is not None
            else os.getenv("OPEN_FOOD_FACTS_USER_AGENT", "")
        ).strip()
        self.fetch_json = fetch_json or _default_json_fetcher
        self.timeout_seconds = timeout_seconds

    def lookup(self, barcode: NormalizedBarcode) -> ProviderLookupResult:
        if not self.user_agent:
            return ProviderLookupResult(
                status="unavailable",
                provider=OPEN_FOOD_FACTS_PROVIDER_NAME,
                reason="OPEN_FOOD_FACTS_USER_AGENT is not configured.",
            )

        query_barcode = (
            barcode.lookup_variants[1]
            if len(barcode.lookup_variants) > 1
            else barcode.normalized_gtin
        )
        fields = (
            "code,product_name,product_name_en,brands,categories,nutriments,"
            "serving_size,serving_quantity,serving_quantity_unit"
        )
        endpoint = (
            f"{OPEN_FOOD_FACTS_API_BASE_URL}/product/{query_barcode}.json?"
            + urlencode({"fields": fields})
        )
        try:
            payload = self.fetch_json(
                "GET",
                endpoint,
                {"Accept": "application/json", "User-Agent": self.user_agent},
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
                provider=OPEN_FOOD_FACTS_PROVIDER_NAME,
                reason="Open Food Facts could not be reached.",
            )

        if payload.get("status") != 1 or not isinstance(payload.get("product"), dict):
            return ProviderLookupResult(
                status="not_found",
                provider=OPEN_FOOD_FACTS_PROVIDER_NAME,
                reason="Open Food Facts has no product for this barcode.",
            )

        product = payload["product"]
        from services.barcode_food_service import try_normalize_barcode

        provider_barcode = _text(product.get("code") or payload.get("code"))
        provider_identity = try_normalize_barcode(provider_barcode or "")
        if (
            provider_identity is None
            or provider_identity.normalized_gtin != barcode.normalized_gtin
        ):
            return ProviderLookupResult(
                status="not_found",
                provider=OPEN_FOOD_FACTS_PROVIDER_NAME,
                reason="Open Food Facts returned a different barcode identity.",
            )

        nutriments = product.get("nutriments")
        nutrition = nutriments if isinstance(nutriments, dict) else {}
        serving_size, serving_label = _serving_grams(product)
        candidate = BarcodeFoodCandidate(
            source_name=OPEN_FOOD_FACTS_PROVIDER_NAME,
            source_record_id=provider_barcode or query_barcode,
            barcode=provider_barcode or query_barcode,
            normalized_gtin=barcode.normalized_gtin,
            product_name=(
                _text(product.get("product_name"))
                or _text(product.get("product_name_en"))
                or ""
            ),
            brand_name=_text(product.get("brands")),
            food_category=_text(product.get("categories")),
            calories_per_100g=_finite_non_negative(nutrition.get("energy-kcal_100g")),
            protein_g_per_100g=_finite_non_negative(nutrition.get("proteins_100g")),
            carbs_g_per_100g=_finite_non_negative(nutrition.get("carbohydrates_100g")),
            fat_g_per_100g=_finite_non_negative(nutrition.get("fat_100g")),
            serving_size=serving_size,
            serving_size_unit="g" if serving_size is not None else None,
            serving_label=serving_label,
            license=OPEN_FOOD_FACTS_LICENSE,
            source_url=f"https://world.openfoodfacts.org/product/{provider_barcode or query_barcode}",
            source_payload=payload,
        )
        complete = all(
            value is not None
            for value in (
                candidate.calories_per_100g,
                candidate.protein_g_per_100g,
                candidate.carbs_g_per_100g,
                candidate.fat_g_per_100g,
            )
        )
        return ProviderLookupResult(
            status="found" if complete else "incomplete",
            provider=OPEN_FOOD_FACTS_PROVIDER_NAME,
            candidate=candidate,
            reason=None
            if complete
            else "Open Food Facts product nutrition is incomplete.",
        )
