from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_logging_recents_service import get_recent_canonical_foods
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_serving_unit_logging_service import (
    get_serving_unit_log_metadata_for_food_entry,
    log_canonical_food_serving,
)
from services.nutrition_serving_unit_service import (
    create_or_update_serving_unit,
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


def test_patch_canonical_log_can_update_grams_entry_to_serving_unit(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": chicken_id,
            "grams": 100,
            "entry_date": "2026-07-10",
            "meal_type": "lunch",
        },
    )
    assert logged.status_code == 200
    entry_id = logged.json()["logged_food_entry_id"]

    updated = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={
            "serving_unit_id": serving_unit_id,
            "quantity": 1.5,
            "meal_type": "dinner",
            "entry_date": "2026-07-10",
        },
    )

    assert updated.status_code == 200
    entry = updated.json()["entry"]
    assert entry["entry_id"] == entry_id
    assert entry["grams"] == 169.5
    assert entry["meal_type"] == "dinner"
    assert entry["calories"] == 279.7
    assert entry["protein_g"] == 52.5
    assert entry["serving_unit_id"] == serving_unit_id
    assert entry["serving_quantity"] == 1.5
    assert entry["serving_display"] == "1.5 x 4 oz cooked chicken breast"
    assert entry["resolved_grams"] == 169.5
    assert entry["amount_source"] == "serving_unit_estimate"
    assert entry["serving_unit_confidence"] == "High"

    daily_logs = _client().get("/nutrition/1/canonical-logs?date=2026-07-10")
    assert daily_logs.status_code == 200
    assert daily_logs.json()["entries"] == [entry]

    actuals = _client().get("/nutrition/1/target-vs-actual?date=2026-07-10")
    assert actuals.status_code == 200
    assert actuals.json()["nutrition_actuals"]["logged_calories"] == 279.7

    recent = get_recent_canonical_foods(user_id=1)[0]
    assert recent["last_serving_unit_id"] == serving_unit_id
    assert recent["last_quantity"] == 1.5


def test_patch_canonical_log_grams_edit_clears_stale_serving_metadata(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    logged = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1,
        entry_date="2026-07-10",
        meal_type="dinner",
    )
    entry_id = logged["logged_food_entry_id"]
    assert get_serving_unit_log_metadata_for_food_entry(entry_id) is not None

    updated = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={
            "grams": 150,
            "meal_type": "dinner",
            "entry_date": "2026-07-10",
        },
    )

    assert updated.status_code == 200
    entry = updated.json()["entry"]
    assert entry["grams"] == 150.0
    assert "serving_unit_id" not in entry
    assert get_serving_unit_log_metadata_for_food_entry(entry_id) is None

    daily_entry = (
        _client()
        .get("/nutrition/1/canonical-logs?date=2026-07-10")
        .json()["entries"][0]
    )
    assert "serving_unit_id" not in daily_entry

    recent = get_recent_canonical_foods(user_id=1)[0]
    assert "last_serving_unit_id" not in recent
    assert recent["last_grams"] == 150.0


def test_patch_canonical_log_meal_only_preserves_serving_metadata(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    logged = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1,
        entry_date="2026-07-10",
        meal_type="lunch",
    )

    updated = _client().patch(
        f"/nutrition/1/canonical-logs/{logged['logged_food_entry_id']}",
        json={"meal_type": "snack", "entry_date": "2026-07-10"},
    )

    assert updated.status_code == 200
    entry = updated.json()["entry"]
    assert entry["meal_type"] == "snack"
    assert entry["grams"] == 113.0
    assert entry["serving_unit_id"] == serving_unit_id
    assert entry["serving_quantity"] == 1.0


def test_patch_canonical_log_rejects_invalid_serving_unit_modes(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    rice_id = _canonical_food_id("rice")
    chicken_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    rice_unit_id = _serving_unit_id(rice_id, "1 cup cooked white rice")
    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": chicken_id,
            "grams": 100,
            "entry_date": "2026-07-10",
        },
    )
    entry_id = logged.json()["logged_food_entry_id"]
    inactive_unit, _ = create_or_update_serving_unit(
        canonical_food_id=chicken_id,
        unit_name="inactive serving",
        unit_quantity=1,
        display_name="inactive chicken serving",
        grams_default=100,
        confidence="High",
        active=False,
    )

    both = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={
            "grams": 100,
            "serving_unit_id": chicken_unit_id,
            "quantity": 1,
            "entry_date": "2026-07-10",
        },
    )
    missing_quantity = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={"serving_unit_id": chicken_unit_id, "entry_date": "2026-07-10"},
    )
    wrong_food = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={
            "serving_unit_id": rice_unit_id,
            "quantity": 1,
            "entry_date": "2026-07-10",
        },
    )
    inactive = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={
            "serving_unit_id": inactive_unit.id,
            "quantity": 1,
            "entry_date": "2026-07-10",
        },
    )
    wrong_user = _client().patch(
        f"/nutrition/2/canonical-logs/{entry_id}",
        json={"grams": 150, "entry_date": "2026-07-10"},
    )

    assert both.status_code == 400
    assert both.json()["detail"] == (
        "Provide either grams or serving_unit_id with quantity, not both."
    )
    assert missing_quantity.status_code == 400
    assert missing_quantity.json()["detail"] == (
        "serving_unit_id and quantity are required for serving-unit logging."
    )
    assert wrong_food.status_code == 400
    assert "does not belong" in wrong_food.json()["detail"]
    assert inactive.status_code == 400
    assert inactive.json()["detail"] == "Serving unit is inactive."
    assert wrong_user.status_code == 404


def test_delete_canonical_log_removes_serving_metadata(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    logged = log_canonical_food_serving(
        user_id=1,
        canonical_food_id=chicken_id,
        serving_unit_id=serving_unit_id,
        quantity=1,
        entry_date="2026-07-10",
    )
    entry_id = logged["logged_food_entry_id"]

    response = _client().delete(
        f"/nutrition/1/canonical-logs/{entry_id}?date=2026-07-10"
    )

    assert response.status_code == 200
    assert get_serving_unit_log_metadata_for_food_entry(entry_id) is None
