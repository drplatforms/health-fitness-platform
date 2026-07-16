from __future__ import annotations

from services.barcode_food_service import normalize_barcode
from services.open_food_facts_provider import OpenFoodFactsProvider


def test_open_food_facts_reads_exact_product_with_100g_macros_and_gram_serving():
    captured_headers: dict[str, str] = {}

    def fetch(method, url, headers, body, timeout):
        captured_headers.update(headers)
        return {
            "status": 1,
            "product": {
                "code": "036000291452",
                "product_name": "Protein Bar",
                "brands": "Example Brand",
                "serving_size": "1 bar (50 g)",
                "serving_quantity": 50,
                "serving_quantity_unit": "g",
                "nutriments": {
                    "energy-kcal_100g": 250,
                    "proteins_100g": 20,
                    "carbohydrates_100g": 30,
                    "fat_100g": 8,
                },
            },
        }

    result = OpenFoodFactsProvider(
        user_agent="HealthFitnessPlatform/1.0 (test@example.com)",
        fetch_json=fetch,
    ).lookup(normalize_barcode("036000291452"))

    assert result.status == "found"
    assert result.candidate is not None
    assert result.candidate.serving_size == 50
    assert result.candidate.serving_size_unit == "g"
    assert captured_headers["User-Agent"].startswith("HealthFitnessPlatform/")


def test_open_food_facts_returns_not_found_for_missing_or_mismatched_product():
    def missing(method, url, headers, body, timeout):
        return {"status": 0}

    result = OpenFoodFactsProvider(
        user_agent="test/1.0 (test@example.com)", fetch_json=missing
    ).lookup(normalize_barcode("036000291452"))
    assert result.status == "not_found"

    def mismatch(method, url, headers, body, timeout):
        return {"status": 1, "product": {"code": "012345678905"}}

    result = OpenFoodFactsProvider(
        user_agent="test/1.0 (test@example.com)", fetch_json=mismatch
    ).lookup(normalize_barcode("036000291452"))
    assert result.status == "not_found"


def test_open_food_facts_requires_identifying_user_agent():
    result = OpenFoodFactsProvider(user_agent="").lookup(
        normalize_barcode("036000291452")
    )

    assert result.status == "unavailable"
    assert "OPEN_FOOD_FACTS_USER_AGENT" in (result.reason or "")


def test_open_food_facts_does_not_convert_volume_serving_to_grams():
    def fetch(method, url, headers, body, timeout):
        return {
            "status": 1,
            "product": {
                "code": "036000291452",
                "product_name": "Drink",
                "serving_quantity": 250,
                "serving_quantity_unit": "ml",
                "nutriments": {
                    "energy-kcal_100g": 50,
                    "proteins_100g": 2,
                    "carbohydrates_100g": 10,
                    "fat_100g": 1,
                },
            },
        }

    result = OpenFoodFactsProvider(
        user_agent="test/1.0 (test@example.com)", fetch_json=fetch
    ).lookup(normalize_barcode("036000291452"))

    assert result.status == "found"
    assert result.candidate is not None
    assert result.candidate.serving_size is None
    assert result.candidate.serving_size_unit is None
