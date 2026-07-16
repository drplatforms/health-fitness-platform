from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.barcode_food_service import normalize_barcode
from services.food_normalization_service import (
    create_raw_food_source_record,
    ensure_food_normalization_tables,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _client() -> TestClient:
    return TestClient(app)


def _raw_complete_product():
    return create_raw_food_source_record(
        source_name="USDA FoodData Central",
        source_record_id="1001",
        raw_description="API Protein Bar",
        brand_name="API Brand",
        data_type="branded",
        gtin_upc="036000291452",
        serving_size=50,
        serving_size_unit="g",
        calories_per_100g=250,
        protein_g_per_100g=20,
        carbs_g_per_100g=30,
        fat_g_per_100g=8,
        source_payload={"private_provider_field": "must-not-leak"},
    )


def test_barcode_resolve_returns_public_safe_local_candidate(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_complete_product()

    response = _client().post(
        "/foods/barcode/resolve",
        json={"barcode": "036000291452", "barcode_format": "UPC_A"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "candidate"
    assert payload["provider"] == "local_raw"
    assert payload["normalized_gtin"] == "00036000291452"
    assert payload["candidate"]["raw_food_source_record_id"] == raw.id
    serialized = response.text.casefold()
    assert "private_provider_field" not in serialized
    assert "source_payload" not in serialized
    assert "api_key" not in serialized
    assert "traceback" not in serialized


def test_barcode_resolve_rejects_invalid_input_without_provider_call(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().post(
        "/foods/barcode/resolve",
        json={"barcode": "036000291453"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "invalid_barcode"


def test_barcode_materialize_returns_canonical_search_shape_and_is_idempotent(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_complete_product()
    normalized_gtin = normalize_barcode(raw.gtin_upc).normalized_gtin

    first = _client().post(
        "/foods/barcode/materialize",
        json={
            "raw_food_source_record_id": raw.id,
            "normalized_gtin": normalized_gtin,
        },
    )
    second = _client().post(
        "/foods/barcode/materialize",
        json={
            "raw_food_source_record_id": raw.id,
            "normalized_gtin": normalized_gtin,
        },
    )

    assert first.status_code == second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["status"] == second_payload["status"] == "resolved"
    canonical = first_payload["canonical_food"]
    assert (
        canonical["canonical_food_id"]
        == second_payload["canonical_food"]["canonical_food_id"]
    )
    assert canonical["food_type"] == "branded"
    assert canonical["nutrient_summary"] == {
        "calories_per_100g": 250.0,
        "protein_g_per_100g": 20.0,
        "carbohydrate_g_per_100g": 30.0,
        "fat_g_per_100g": 8.0,
    }


def test_barcode_materialize_handles_expected_gtin_mismatch_and_missing_raw(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_complete_product()

    mismatch = _client().post(
        "/foods/barcode/materialize",
        json={
            "raw_food_source_record_id": raw.id,
            "normalized_gtin": normalize_barcode("012345678905").normalized_gtin,
        },
    )
    missing = _client().post(
        "/foods/barcode/materialize",
        json={
            "raw_food_source_record_id": 999999,
            "normalized_gtin": normalize_barcode("036000291452").normalized_gtin,
        },
    )

    assert mismatch.status_code == missing.status_code == 200
    assert mismatch.json()["status"] == "invalid_barcode"
    assert missing.json()["status"] == "not_found"
