from __future__ import annotations

import database
from services.food_logging_recents_service import get_recent_canonical_foods
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    create_raw_food_source_record,
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


def _seed_starter_foods(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
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


def test_recent_canonical_foods_are_user_scoped_distinct_and_ordered(
    tmp_path,
    monkeypatch,
):
    _seed_starter_foods(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    banana_id = _canonical_food_id("banana")

    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-07-07",
        meal_type="lunch",
    )
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=150,
        entry_date="2026-07-08",
        meal_type="dinner",
    )
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=banana_id,
        grams=118,
        entry_date="2026-07-09",
        meal_type="breakfast",
    )
    add_canonical_food_entry(
        user_id=2,
        canonical_food_id=chicken_id,
        grams=200,
        entry_date="2026-07-09",
        meal_type="snack",
    )

    results = get_recent_canonical_foods(user_id=1, limit=10)

    assert [item["canonical_food_id"] for item in results] == [
        banana_id,
        chicken_id,
    ]
    assert results[0]["display_name"] == "Banana"
    assert results[0]["last_grams"] == 118.0
    assert results[0]["last_meal_type"] == "breakfast"
    assert results[0]["usage_count"] == 1
    assert results[1]["last_grams"] == 150.0
    assert results[1]["last_meal_type"] == "dinner"
    assert results[1]["usage_count"] == 2


def test_recent_canonical_foods_include_serving_metadata_when_available(
    tmp_path,
    monkeypatch,
):
    _seed_starter_foods(tmp_path, monkeypatch)
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

    results = get_recent_canonical_foods(user_id=1)

    assert len(results) == 1
    assert results[0]["canonical_food_id"] == chicken_id
    assert results[0]["last_grams"] == 169.5
    assert results[0]["last_serving_unit_id"] == serving_unit_id
    assert results[0]["last_serving_unit_label"] == ("1.5 x 4 oz cooked chicken breast")
    assert results[0]["last_quantity"] == 1.5
    assert results[0]["nutrient_summary"] == {
        "calories": 279.7,
        "protein_g": 52.5,
        "carbohydrate_g": 0.0,
        "fat_g": 6.1,
    }


def test_recent_canonical_foods_fall_back_to_grams_without_serving_metadata(
    tmp_path,
    monkeypatch,
):
    _seed_starter_foods(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")

    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=banana_id,
        grams=118,
        entry_date="2026-07-09",
        meal_type="breakfast",
    )

    results = get_recent_canonical_foods(user_id=1)

    assert results[0]["canonical_food_id"] == banana_id
    assert results[0]["last_grams"] == 118.0
    assert "last_serving_unit_id" not in results[0]
    assert "last_serving_unit_label" not in results[0]
    assert "last_quantity" not in results[0]


def test_recent_canonical_foods_skip_inactive_foods(tmp_path, monkeypatch):
    _seed_starter_foods(tmp_path, monkeypatch)
    banana_id = _canonical_food_id("banana")

    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=banana_id,
        grams=118,
        entry_date="2026-07-09",
    )
    conn = database.get_connection()
    conn.execute("UPDATE canonical_foods SET active = 0 WHERE id = ?", (banana_id,))
    conn.commit()
    conn.close()

    assert get_recent_canonical_foods(user_id=1) == []


def test_recent_canonical_foods_keep_missing_macros_missing(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    protein_food = create_canonical_food("Protein Only Recent Food", "generic")
    create_canonical_food_nutrient(protein_food.id, "Protein", "g", 20)

    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=protein_food.id,
        grams=100,
        entry_date="2026-07-09",
    )

    results = get_recent_canonical_foods(user_id=1)

    assert results[0]["nutrient_summary"] == {"protein_g": 20.0}


def test_recent_canonical_foods_are_bounded_and_public_safe(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="raw-secret",
        raw_description="Raw source payload should stay private",
        source_payload={"private": True},
    )
    for index in range(30):
        food = create_canonical_food(f"Recent Bound Food {index}", "generic")
        create_canonical_food_nutrient(food.id, "Calories", "kcal", 100 + index)
        add_canonical_food_entry(
            user_id=1,
            canonical_food_id=food.id,
            grams=100,
            entry_date="2026-07-09",
        )

    results = get_recent_canonical_foods(user_id=1, limit=999)
    defaulted_results = get_recent_canonical_foods(user_id=1, limit=0)

    assert len(results) == 25
    assert len(defaulted_results) == 10
    serialized = str(results).lower()
    assert "source_payload_json" not in serialized
    assert "raw_source_record_id" not in serialized
    assert "private" not in serialized
    assert "raw source payload" not in serialized
