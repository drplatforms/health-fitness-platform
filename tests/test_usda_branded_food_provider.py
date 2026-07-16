from __future__ import annotations

import json

from services.barcode_food_service import normalize_barcode
from services.usda_branded_food_provider import UsdaBrandedFoodProvider


def _nutrients() -> list[dict]:
    return [
        {"nutrient": {"id": 1008, "name": "Energy", "unitName": "kcal"}, "amount": 250},
        {"nutrient": {"id": 1003, "name": "Protein", "unitName": "g"}, "amount": 20},
        {
            "nutrient": {
                "id": 1005,
                "name": "Carbohydrate, by difference",
                "unitName": "g",
            },
            "amount": 30,
        },
        {
            "nutrient": {"id": 1004, "name": "Total lipid (fat)", "unitName": "g"},
            "amount": 8,
        },
    ]


def test_usda_accepts_only_exact_gtin_then_fetches_full_detail():
    calls: list[tuple[str, str, dict | None]] = []

    def fetch(method, url, headers, body, timeout):
        calls.append((method, url, json.loads(body) if body else None))
        if method == "POST":
            return {
                "foods": [
                    {
                        "fdcId": 1,
                        "gtinUpc": "012345678905",
                        "description": "Fuzzy product",
                    },
                    {
                        "fdcId": 2,
                        "gtinUpc": "036000291452",
                        "description": "Exact product",
                    },
                ]
            }
        return {
            "fdcId": 2,
            "gtinUpc": "036000291452",
            "description": "Exact Protein Bar",
            "brandOwner": "Example Brand",
            "foodCategory": "Snack Bars",
            "servingSize": 50,
            "servingSizeUnit": "g",
            "householdServingFullText": "1 bar",
            "foodNutrients": _nutrients(),
        }

    result = UsdaBrandedFoodProvider(api_key="test-key", fetch_json=fetch).lookup(
        normalize_barcode("036000291452", "UPC_A")
    )

    assert result.status == "found"
    assert result.candidate is not None
    assert result.candidate.source_record_id == "2"
    assert result.candidate.normalized_gtin == "00036000291452"
    assert result.candidate.serving_label == "1 bar"
    assert result.candidate.calories_per_100g == 250
    assert calls[0][2] == {
        "query": "036000291452",
        "dataType": ["Branded"],
        "pageSize": 25,
    }
    assert calls[1][0] == "GET"


def test_usda_fuzzy_only_result_is_not_accepted():
    def fetch(method, url, headers, body, timeout):
        return {"foods": [{"fdcId": 1, "gtinUpc": "012345678905"}]}

    result = UsdaBrandedFoodProvider(api_key="test-key", fetch_json=fetch).lookup(
        normalize_barcode("036000291452")
    )

    assert result.status == "not_found"
    assert result.candidate is None


def test_usda_is_unavailable_without_server_side_key():
    result = UsdaBrandedFoodProvider(api_key="").lookup(
        normalize_barcode("036000291452")
    )

    assert result.status == "unavailable"
    assert "FDC_API_KEY" in (result.reason or "")


def test_usda_missing_required_macro_is_incomplete():
    def fetch(method, url, headers, body, timeout):
        if method == "POST":
            return {"foods": [{"fdcId": 2, "gtinUpc": "036000291452"}]}
        return {
            "fdcId": 2,
            "gtinUpc": "036000291452",
            "description": "Incomplete product",
            "foodNutrients": _nutrients()[:-1],
        }

    result = UsdaBrandedFoodProvider(api_key="test-key", fetch_json=fetch).lookup(
        normalize_barcode("036000291452")
    )

    assert result.status == "incomplete"
    assert result.candidate is not None
    assert result.candidate.fat_g_per_100g is None
