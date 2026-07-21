from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_canonical_food_entry
from services.nutrition_serving_unit_logging_service import log_canonical_food_serving
from services.nutrition_serving_unit_service import (
    get_active_serving_units_for_canonical_food,
    seed_canonical_food_serving_units,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    seed_starter_canonical_foods()
    seed_canonical_food_serving_units()


def _client() -> TestClient:
    return TestClient(app)


def _canonical_food_id(search_term: str) -> int:
    results = search_canonical_foods(search_term, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def _serving_unit_id(canonical_food_id: int, display_name: str) -> int:
    for serving_unit in get_active_serving_units_for_canonical_food(canonical_food_id):
        if serving_unit.display_name == display_name:
            return serving_unit.id
    raise AssertionError(f"Missing serving unit: {display_name}")


def test_recent_canonical_foods_endpoint_returns_user_scoped_results(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    banana_id = _canonical_food_id("banana")
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=150,
        entry_date="2026-07-08",
        meal_type="lunch",
    )
    add_canonical_food_entry(
        user_id=2,
        canonical_food_id=banana_id,
        grams=118,
        entry_date="2026-07-08",
        meal_type="breakfast",
    )

    response = _client().get("/nutrition/1/recent-canonical-foods")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["results"] == [
        {
            "canonical_food_id": chicken_id,
            "display_name": "Chicken Breast, Cooked, Skinless",
            "original_display_name": "Chicken Breast, Cooked, Skinless",
            "custom_display_name": None,
            "last_logged_at": payload["results"][0]["last_logged_at"],
            "last_logged_date": "2026-07-08",
            "last_meal_type": "lunch",
            "last_grams": 150.0,
            "usage_count": 1,
            "nutrient_summary": {
                "calories": 247.5,
                "protein_g": 46.5,
                "carbohydrate_g": 0.0,
                "fat_g": 5.4,
            },
        }
    ]


def test_recent_canonical_foods_endpoint_returns_serving_context(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1.5,
        entry_date="2026-07-09",
        meal_type="dinner",
    )

    response = _client().get("/nutrition/1/recent-canonical-foods?limit=10")

    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["canonical_food_id"] == chicken_id
    assert item["last_grams"] == 169.5
    assert item["last_serving_unit_id"] == serving_unit_id
    assert item["last_serving_unit_label"] == "1.5 x 4 oz cooked chicken breast"
    assert item["last_quantity"] == 1.5


def test_recent_canonical_foods_endpoint_bounds_invalid_limits(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=banana_id,
        grams=118,
        entry_date="2026-07-09",
    )

    invalid = _client().get("/nutrition/1/recent-canonical-foods?limit=abc")
    too_low = _client().get("/nutrition/1/recent-canonical-foods?limit=0")

    assert invalid.status_code == 200
    assert too_low.status_code == 200
    assert len(invalid.json()["results"]) == 1
    assert len(too_low.json()["results"]) == 1


def test_recent_grams_item_can_be_relogged_through_canonical_endpoint(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=banana_id,
        grams=118,
        entry_date="2026-07-08",
        meal_type="breakfast",
    )
    recent_item = (
        _client().get("/nutrition/1/recent-canonical-foods").json()["results"][0]
    )

    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": recent_item["canonical_food_id"],
            "grams": recent_item["last_grams"],
            "entry_date": "2026-07-09",
            "meal_type": recent_item["last_meal_type"],
        },
    )
    target = _client().get("/nutrition/1/target-vs-actual?date=2026-07-09")

    assert logged.status_code == 200
    assert logged.json()["grams"] == 118.0
    assert target.status_code == 200
    assert target.json()["nutrition_actuals"]["entry_count"] == 1


def test_recent_serving_item_can_be_relogged_through_canonical_endpoint(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1,
        entry_date="2026-07-08",
        meal_type="dinner",
    )
    recent_item = (
        _client().get("/nutrition/1/recent-canonical-foods").json()["results"][0]
    )

    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": recent_item["canonical_food_id"],
            "serving_unit_id": recent_item["last_serving_unit_id"],
            "quantity": recent_item["last_quantity"],
            "entry_date": "2026-07-09",
            "meal_type": recent_item["last_meal_type"],
        },
    )
    target = _client().get("/nutrition/1/target-vs-actual?date=2026-07-09")

    assert logged.status_code == 200
    assert logged.json()["resolved_grams"] == 113.0
    assert target.status_code == 200
    actuals = target.json()["nutrition_actuals"]
    assert actuals["entry_count"] == 1
    assert actuals["logged_calories"] == 186.4
    assert actuals["logged_protein"] == 35.0
