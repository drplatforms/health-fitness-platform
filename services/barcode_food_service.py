from __future__ import annotations

import json
import math
import re
from dataclasses import replace
from typing import Protocol

from database import get_connection
from models.barcode_food_models import (
    BarcodeFoodCandidate,
    BarcodeResolveResult,
    NormalizedBarcode,
    ProviderLookupResult,
)
from models.food_normalization_models import RawFoodSourceRecord
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    get_canonical_food,
    get_nutrients_for_canonical_food,
    get_raw_food_source_record,
    link_canonical_food_to_source,
    normalize_food_name,
)
from services.nutrition_serving_unit_service import create_or_update_serving_unit
from services.open_food_facts_provider import OpenFoodFactsProvider
from services.usda_branded_food_provider import UsdaBrandedFoodProvider

SUPPORTED_BARCODE_FORMATS = {"UPC_A", "UPC_E", "EAN_8", "EAN_13", "GTIN_14"}
FORMAT_ALIASES = {
    "UPCA": "UPC_A",
    "UPC_A": "UPC_A",
    "UPC-E": "UPC_E",
    "UPCE": "UPC_E",
    "UPC_E": "UPC_E",
    "EAN8": "EAN_8",
    "EAN_8": "EAN_8",
    "EAN13": "EAN_13",
    "EAN_13": "EAN_13",
    "GTIN14": "GTIN_14",
    "GTIN_14": "GTIN_14",
}


class BarcodeProvider(Protocol):
    def lookup(self, barcode: NormalizedBarcode) -> ProviderLookupResult: ...


def _format_name(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    key = value.strip().upper().replace(" ", "_")
    normalized = FORMAT_ALIASES.get(key)
    if normalized is None:
        raise ValueError("Unsupported barcode format.")
    return normalized


def _check_digit(data_digits: str) -> int:
    total = 0
    for index, digit in enumerate(reversed(data_digits)):
        total += int(digit) * (3 if index % 2 == 0 else 1)
    return (10 - (total % 10)) % 10


def _has_valid_check_digit(digits: str) -> bool:
    return len(digits) >= 2 and int(digits[-1]) == _check_digit(digits[:-1])


def _expand_upc_e(digits: str) -> str:
    if len(digits) != 8:
        raise ValueError(
            "UPC-E input must contain 8 digits including number system and check digit."
        )
    number_system, payload, check_digit = digits[0], digits[1:7], digits[7]
    if number_system not in {"0", "1"}:
        raise ValueError("UPC-E number system must be 0 or 1.")

    last = payload[-1]
    if last in {"0", "1", "2"}:
        upc_a_data = number_system + payload[:2] + last + "0000" + payload[2:5]
    elif last == "3":
        upc_a_data = number_system + payload[:3] + "00000" + payload[3:5]
    elif last == "4":
        upc_a_data = number_system + payload[:4] + "00000" + payload[4]
    else:
        upc_a_data = number_system + payload[:5] + "0000" + last

    expanded = upc_a_data + check_digit
    if not _has_valid_check_digit(expanded):
        raise ValueError(
            "UPC-E check digit is invalid for its expanded UPC-A identity."
        )
    return expanded


def normalize_barcode(
    barcode: str,
    barcode_format: str | None = None,
) -> NormalizedBarcode:
    digits = re.sub(r"[\s-]+", "", str(barcode or ""))
    if not digits or not digits.isdigit():
        raise ValueError("Barcode must contain digits only.")

    resolved_format = _format_name(barcode_format)
    if resolved_format == "UPC_E":
        base_digits = _expand_upc_e(digits)
    else:
        expected_length = {
            "UPC_A": 12,
            "EAN_8": 8,
            "EAN_13": 13,
            "GTIN_14": 14,
        }.get(resolved_format)
        if expected_length is not None and len(digits) != expected_length:
            raise ValueError(
                f"{resolved_format} input must contain {expected_length} digits."
            )
        if resolved_format is None and len(digits) not in {8, 12, 13, 14}:
            raise ValueError(
                "Manual barcode input must be a valid EAN-8, UPC-A, EAN-13, or GTIN-14."
            )
        base_digits = digits

    if not _has_valid_check_digit(base_digits):
        raise ValueError("Barcode check digit is invalid.")

    normalized_gtin = base_digits.zfill(14)
    variants: list[str] = [normalized_gtin]
    for variant in (base_digits, digits):
        if variant not in variants:
            variants.append(variant)
    if len(base_digits) == 12:
        ean_13 = "0" + base_digits
        if ean_13 not in variants:
            variants.append(ean_13)
    elif len(base_digits) == 13 and base_digits.startswith("0"):
        upc_a = base_digits[1:]
        if upc_a not in variants:
            variants.append(upc_a)

    return NormalizedBarcode(
        barcode_input=digits,
        barcode_format=resolved_format,
        normalized_gtin=normalized_gtin,
        lookup_variants=tuple(variants),
    )


def try_normalize_barcode(
    barcode: str,
    barcode_format: str | None = None,
) -> NormalizedBarcode | None:
    try:
        return normalize_barcode(barcode, barcode_format)
    except ValueError:
        return None


def _raw_record_candidate(
    record: RawFoodSourceRecord,
    normalized_gtin: str,
) -> BarcodeFoodCandidate:
    payload: dict[str, object] = {}
    if record.source_payload_json:
        try:
            decoded = json.loads(record.source_payload_json)
            if isinstance(decoded, dict):
                payload = decoded
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}
    serving_label = (
        payload.get("_barcode_serving_label")
        or payload.get("householdServingFullText")
        or payload.get("serving_size")
    )
    return BarcodeFoodCandidate(
        source_name=record.source_name,
        source_record_id=record.source_record_id,
        barcode=record.gtin_upc or normalized_gtin,
        normalized_gtin=normalized_gtin,
        product_name=record.raw_description,
        brand_name=record.brand_name,
        food_category=record.food_category,
        calories_per_100g=record.calories_per_100g,
        protein_g_per_100g=record.protein_g_per_100g,
        carbs_g_per_100g=record.carbs_g_per_100g,
        fat_g_per_100g=record.fat_g_per_100g,
        serving_size=record.serving_size,
        serving_size_unit=record.serving_size_unit,
        serving_label=str(serving_label).strip() if serving_label else None,
        raw_food_source_record_id=record.id,
        license=record.license,
        source_url=record.source_url,
        source_payload=payload,
    )


def candidate_is_complete(candidate: BarcodeFoodCandidate) -> bool:
    if not candidate.product_name.strip() or not try_normalize_barcode(
        candidate.normalized_gtin
    ):
        return False
    limits = (
        (candidate.calories_per_100g, 1000.0),
        (candidate.protein_g_per_100g, 100.0),
        (candidate.carbs_g_per_100g, 100.0),
        (candidate.fat_g_per_100g, 100.0),
    )
    return all(
        value is not None
        and math.isfinite(float(value))
        and 0 <= float(value) <= maximum
        for value, maximum in limits
    )


def _matching_raw_records(normalized_gtin: str) -> list[RawFoodSourceRecord]:
    ensure_food_normalization_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, gtin_upc FROM raw_food_source_records WHERE gtin_upc IS NOT NULL AND TRIM(gtin_upc) != '' ORDER BY id"
    )
    matching_ids = [
        int(row["id"])
        for row in cursor.fetchall()
        if (identity := try_normalize_barcode(str(row["gtin_upc"])))
        and identity.normalized_gtin == normalized_gtin
    ]
    conn.close()
    return [
        record
        for record_id in matching_ids
        if (record := get_raw_food_source_record(record_id)) is not None
    ]


def _canonical_owners(raw_records: list[RawFoodSourceRecord]) -> tuple[int, ...]:
    if not raw_records:
        return ()
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in raw_records)
    cursor.execute(
        f"""
        SELECT DISTINCT food_source_links.canonical_food_id
        FROM food_source_links
        JOIN canonical_foods ON canonical_foods.id = food_source_links.canonical_food_id
        WHERE food_source_links.raw_food_source_record_id IN ({placeholders})
          AND canonical_foods.active = 1
        ORDER BY food_source_links.canonical_food_id
        """,
        tuple(record.id for record in raw_records),
    )
    owners = tuple(int(row["canonical_food_id"]) for row in cursor.fetchall())
    conn.close()
    return owners


def _public_canonical_food(canonical_food_id: int) -> dict[str, object]:
    food = get_canonical_food(canonical_food_id)
    if food is None or not food.active:
        raise ValueError("Canonical food not found.")
    nutrient_summary: dict[str, float] = {}
    keys = {
        "calories": "calories_per_100g",
        "protein": "protein_g_per_100g",
        "carbohydrate": "carbohydrate_g_per_100g",
        "fat": "fat_g_per_100g",
    }
    for nutrient in get_nutrients_for_canonical_food(food.id):
        normalized_name = normalize_food_name(nutrient.nutrient_name)
        key = keys.get(normalized_name)
        if key:
            nutrient_summary[key] = nutrient.amount_per_100g
    return {
        "canonical_food_id": food.id,
        "display_name": food.display_name,
        "food_type": food.food_type,
        "default_unit": food.default_unit,
        "default_grams": food.default_grams,
        "search_priority": food.search_priority,
        "matched_on": "barcode",
        "aliases": [],
        "nutrient_summary": nutrient_summary,
    }


def _local_resolution(identity: NormalizedBarcode) -> BarcodeResolveResult | None:
    records = _matching_raw_records(identity.normalized_gtin)
    owners = _canonical_owners(records)
    if len(owners) > 1:
        return BarcodeResolveResult(
            status="conflict",
            normalized_barcode=identity,
            provider="local",
            reason="This barcode is linked to multiple canonical foods.",
            conflict_canonical_food_ids=owners,
        )
    if len(owners) == 1:
        return BarcodeResolveResult(
            status="resolved",
            normalized_barcode=identity,
            provider="local",
            canonical_food=_public_canonical_food(owners[0]),
        )

    source_priority = {"USDA FoodData Central": 0, "Open Food Facts": 1}
    records.sort(key=lambda item: (source_priority.get(item.source_name, 10), item.id))
    for record in records:
        candidate = _raw_record_candidate(record, identity.normalized_gtin)
        if candidate_is_complete(candidate):
            return BarcodeResolveResult(
                status="candidate",
                normalized_barcode=identity,
                provider="local_raw",
                candidate=candidate,
            )
    return None


def _cache_candidate(candidate: BarcodeFoodCandidate) -> BarcodeFoodCandidate:
    source_payload = dict(candidate.source_payload)
    if candidate.serving_label:
        source_payload["_barcode_serving_label"] = candidate.serving_label
    record = create_raw_food_source_record(
        source_name=candidate.source_name,
        source_record_id=candidate.source_record_id,
        raw_description=candidate.product_name,
        brand_name=candidate.brand_name,
        food_category=candidate.food_category,
        data_type="branded",
        gtin_upc=candidate.barcode,
        serving_size=candidate.serving_size,
        serving_size_unit=candidate.serving_size_unit,
        calories_per_100g=candidate.calories_per_100g,
        protein_g_per_100g=candidate.protein_g_per_100g,
        carbs_g_per_100g=candidate.carbs_g_per_100g,
        fat_g_per_100g=candidate.fat_g_per_100g,
        import_batch="barcode_lookup_v1",
        source_payload=source_payload,
        license=candidate.license,
        source_url=candidate.source_url,
    )
    return replace(candidate, raw_food_source_record_id=record.id)


def resolve_barcode_food(
    barcode: str,
    barcode_format: str | None = None,
    *,
    usda_provider: BarcodeProvider | None = None,
    open_food_facts_provider: BarcodeProvider | None = None,
) -> BarcodeResolveResult:
    try:
        identity = normalize_barcode(barcode, barcode_format)
    except ValueError as exc:
        return BarcodeResolveResult(status="invalid_barcode", reason=str(exc))

    local = _local_resolution(identity)
    if local is not None:
        return local

    providers: tuple[BarcodeProvider, ...] = (
        usda_provider or UsdaBrandedFoodProvider(),
        open_food_facts_provider or OpenFoodFactsProvider(),
    )
    results: list[ProviderLookupResult] = []
    incomplete_candidate: BarcodeFoodCandidate | None = None
    for provider in providers:
        result = provider.lookup(identity)
        results.append(result)
        if result.candidate is not None:
            cached = _cache_candidate(result.candidate)
            if result.status == "found" and candidate_is_complete(cached):
                return BarcodeResolveResult(
                    status="candidate",
                    normalized_barcode=identity,
                    provider=result.provider,
                    candidate=cached,
                )
            incomplete_candidate = incomplete_candidate or cached

    if incomplete_candidate is not None:
        return BarcodeResolveResult(
            status="incomplete",
            normalized_barcode=identity,
            provider=incomplete_candidate.source_name,
            candidate=incomplete_candidate,
            reason="The product was found, but required nutrition is incomplete.",
        )
    if any(result.status == "unavailable" for result in results):
        return BarcodeResolveResult(
            status="provider_unavailable",
            normalized_barcode=identity,
            reason="One or more barcode providers could not be queried.",
        )
    return BarcodeResolveResult(
        status="not_found",
        normalized_barcode=identity,
        reason="No exact product match was found for this barcode.",
    )


def _canonical_name_exists(display_name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM canonical_foods WHERE normalized_name = ? AND food_type = 'branded' LIMIT 1",
        (normalize_food_name(display_name),),
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def _barcode_safe_display_name(
    record: RawFoodSourceRecord, normalized_gtin: str
) -> str:
    product_name = " ".join(record.raw_description.strip().split())
    brand_name = " ".join((record.brand_name or "").strip().split())
    candidates = [product_name]
    if brand_name and brand_name.casefold() not in product_name.casefold():
        candidates.append(f"{product_name} — {brand_name}")
    candidates.append(f"{candidates[-1]} · {normalized_gtin[-4:]}")
    for candidate in candidates:
        if not _canonical_name_exists(candidate):
            return candidate
    raise ValueError("Unable to create a collision-safe canonical product name.")


def _ensure_source_link(canonical_food_id: int, raw_record_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM food_source_links WHERE canonical_food_id = ? AND raw_food_source_record_id = ? LIMIT 1",
        (canonical_food_id, raw_record_id),
    )
    exists = cursor.fetchone() is not None
    conn.close()
    if not exists:
        link_canonical_food_to_source(
            canonical_food_id,
            raw_record_id,
            relationship_type="equivalent",
        )


def materialize_barcode_food(
    raw_food_source_record_id: int,
    expected_normalized_gtin: str,
) -> BarcodeResolveResult:
    expected_identity = try_normalize_barcode(expected_normalized_gtin)
    if expected_identity is None:
        return BarcodeResolveResult(
            status="invalid_barcode",
            reason="Expected normalized GTIN is invalid.",
        )

    record = get_raw_food_source_record(raw_food_source_record_id)
    if record is None:
        return BarcodeResolveResult(
            status="not_found",
            normalized_barcode=expected_identity,
            reason="Raw barcode source record was not found.",
        )
    record_identity = try_normalize_barcode(record.gtin_upc or "")
    if (
        record_identity is None
        or record_identity.normalized_gtin != expected_identity.normalized_gtin
    ):
        return BarcodeResolveResult(
            status="invalid_barcode",
            normalized_barcode=expected_identity,
            reason="Raw source barcode does not match the expected normalized GTIN.",
        )

    candidate = _raw_record_candidate(record, record_identity.normalized_gtin)
    if not candidate_is_complete(candidate):
        return BarcodeResolveResult(
            status="incomplete",
            normalized_barcode=record_identity,
            provider=record.source_name,
            candidate=candidate,
            reason="Required product nutrition is incomplete or implausible.",
        )

    records = _matching_raw_records(record_identity.normalized_gtin)
    owners = _canonical_owners(records)
    if len(owners) > 1:
        return BarcodeResolveResult(
            status="conflict",
            normalized_barcode=record_identity,
            provider="local",
            reason="This barcode is linked to multiple canonical foods.",
            conflict_canonical_food_ids=owners,
        )
    if len(owners) == 1:
        _ensure_source_link(owners[0], record.id)
        return BarcodeResolveResult(
            status="resolved",
            normalized_barcode=record_identity,
            provider="local",
            canonical_food=_public_canonical_food(owners[0]),
        )

    display_name = _barcode_safe_display_name(record, record_identity.normalized_gtin)
    canonical_food = create_canonical_food(
        display_name=display_name,
        food_type="branded",
        default_unit="grams",
        default_grams=100.0,
        search_priority=100,
        active=True,
        notes="Confirmed barcode product materialized from a server-owned raw source record.",
    )
    if normalize_food_name(record.raw_description) != canonical_food.normalized_name:
        create_canonical_food_alias(
            canonical_food.id, record.raw_description, priority=50
        )

    nutrients = (
        ("Calories", "kcal", candidate.calories_per_100g),
        ("Protein", "g", candidate.protein_g_per_100g),
        ("Carbohydrate", "g", candidate.carbs_g_per_100g),
        ("Fat", "g", candidate.fat_g_per_100g),
    )
    for nutrient_name, unit, amount in nutrients:
        create_canonical_food_nutrient(
            canonical_food.id,
            nutrient_name,
            unit,
            float(amount),
            source_policy="direct_source",
            confidence="Moderate",
        )
    link_canonical_food_to_source(
        canonical_food.id, record.id, relationship_type="primary"
    )

    serving_unit = (record.serving_size_unit or "").strip().casefold()
    if (
        record.serving_size is not None
        and record.serving_size > 0
        and serving_unit in {"g", "gram", "grams"}
    ):
        create_or_update_serving_unit(
            canonical_food_id=canonical_food.id,
            unit_name="serving",
            unit_quantity=1,
            display_name=candidate.serving_label or "1 serving",
            grams_default=record.serving_size,
            grams_min=record.serving_size,
            grams_max=record.serving_size,
            confidence="High",
            source=f"barcode_source:{record.source_name}",
            source_note="Direct gram serving from the linked barcode source record.",
            active=True,
            sort_order=10,
        )

    return BarcodeResolveResult(
        status="resolved",
        normalized_barcode=record_identity,
        provider="local",
        canonical_food=_public_canonical_food(canonical_food.id),
    )
