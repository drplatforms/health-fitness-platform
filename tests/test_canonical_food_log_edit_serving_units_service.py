from __future__ import annotations

import database
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import (
    add_canonical_food_entry,
    delete_canonical_food_entry,
    update_canonical_food_entry,
)
from services.nutrition_serving_unit_logging_service import (
    get_serving_unit_log_metadata_for_food_entry,
    log_canonical_food_serving,
)
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


def _canonical_food_id(search_term: str) -> int:
    results = search_canonical_foods(search_term, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def _serving_unit_id(canonical_food_id: int, display_name: str) -> int:
    for serving_unit in get_active_serving_units_for_canonical_food(canonical_food_id):
        if serving_unit.display_name == display_name:
            return serving_unit.id
    raise AssertionError(f"Missing serving unit: {display_name}")


def test_update_canonical_food_entry_can_create_serving_metadata(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    serving_unit_id = _serving_unit_id(chicken_id, "4 oz cooked chicken breast")
    logged = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-07-10",
    )

    updated = update_canonical_food_entry(
        user_id=1,
        entry_id=logged["logged_food_entry_id"],
        serving_unit_id=serving_unit_id,
        quantity=1.5,
        meal_type="dinner",
        entry_date="2026-07-10",
    )

    assert updated["grams"] == 169.5
    assert updated["meal_type"] == "dinner"
    assert updated["serving_unit_id"] == serving_unit_id
    assert updated["serving_quantity"] == 1.5
    metadata = get_serving_unit_log_metadata_for_food_entry(
        logged["logged_food_entry_id"]
    )
    assert metadata is not None
    assert metadata.resolved_grams == 169.5


def test_update_canonical_food_entry_grams_edit_clears_serving_metadata(
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
    )

    updated = update_canonical_food_entry(
        user_id=1,
        entry_id=logged["logged_food_entry_id"],
        grams=150,
        entry_date="2026-07-10",
    )

    assert updated["grams"] == 150.0
    assert "serving_unit_id" not in updated
    assert (
        get_serving_unit_log_metadata_for_food_entry(logged["logged_food_entry_id"])
        is None
    )


def test_delete_canonical_food_entry_removes_serving_metadata(tmp_path, monkeypatch):
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

    delete_canonical_food_entry(user_id=1, entry_id=entry_id, entry_date="2026-07-10")

    assert get_serving_unit_log_metadata_for_food_entry(entry_id) is None
