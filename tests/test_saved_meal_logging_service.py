from __future__ import annotations

import sqlite3

import pytest

import database
import services.saved_meal_logging_service as saved_meal_logging_service
from models.personal_food_models import PersonalFoodRevisionInput
from models.saved_meal_models import SavedMealItemInput, SavedMealMutationInput
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
)
from services.nutrition_serving_unit_logging_service import (
    get_serving_unit_log_metadata_for_food_entry,
)
from services.nutrition_serving_unit_service import create_or_update_serving_unit
from services.personal_food_service import (
    archive_personal_food,
    create_personal_food,
    revise_personal_food,
)
from services.saved_meal_logging_service import log_saved_meal
from services.saved_meal_service import (
    SavedMealArchivedError,
    SavedMealValidationError,
    archive_saved_meal,
    create_saved_meal,
)


@pytest.fixture
def saved_meal_db(tmp_path, monkeypatch):
    db_path = tmp_path / "saved_meal_logging.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    ensure_food_normalization_tables()
    return db_path


def _canonical_food():
    food = create_canonical_food("Transactional Chicken", "generic")
    for nutrient_name, amount in (
        ("Calories", 200),
        ("Protein", 30),
        ("Carbohydrates", 5),
        ("Fat", 8),
    ):
        create_canonical_food_nutrient(food.id, nutrient_name, "g", amount)
    return food


def _personal_food(calories: float = 100):
    return create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="Transactional Sauce",
            input_basis="nutrition_label",
            serving_name="1 scoop",
            serving_grams=20,
            calories=calories,
            protein_g=4,
            carbs_g=6,
            fat_g=2,
        ),
    )


def _mixed_meal(*, meal_type: str | None = "dinner"):
    canonical = _canonical_food()
    personal = _personal_food()
    meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Transactional Bowl",
            default_meal_type=meal_type,
            items=(
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=canonical.id,
                    grams=100,
                ),
                SavedMealItemInput(
                    food_type="personal",
                    personal_food_id=personal.id,
                    grams=20,
                ),
            ),
        ),
    )
    return meal, canonical, personal


def _entry_rows(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM food_entries ORDER BY id").fetchall()
    conn.close()
    return rows


def test_successful_mixed_log_creates_normal_entries_with_one_date_and_meal_type(
    saved_meal_db,
) -> None:
    meal, canonical, personal = _mixed_meal()
    result = log_saved_meal(
        user_id=1,
        saved_meal_id=meal.id,
        entry_date="2026-07-16",
    )
    assert result["logged_item_count"] == 2
    assert result["entry_date"] == "2026-07-16"
    assert result["meal_type"] == "dinner"
    assert result["aggregate_logged_macros"] == {
        "calories": 300,
        "protein_g": 34,
        "carbs_g": 11,
        "fat_g": 10,
    }
    rows = _entry_rows(saved_meal_db)
    assert len(rows) == 2
    assert rows[0]["canonical_food_id"] == canonical.id
    assert rows[0]["personal_food_id"] is None
    assert rows[1]["personal_food_id"] == personal.id
    assert rows[1]["personal_food_revision_id"] == personal.current_revision_id
    assert rows[1]["food_name_snapshot"] == "Transactional Sauce"
    assert {row["entry_date"] for row in rows} == {"2026-07-16"}
    assert {row["meal_type"] for row in rows} == {"dinner"}


def test_personal_revision_updates_future_logs_without_rewriting_history(
    saved_meal_db,
) -> None:
    meal, _, personal = _mixed_meal()
    first = log_saved_meal(user_id=1, saved_meal_id=meal.id, entry_date="2026-07-16")
    revised = revise_personal_food(
        user_id=1,
        personal_food_id=personal.id,
        revision_input=PersonalFoodRevisionInput(
            display_name="Revised Sauce",
            input_basis="nutrition_label",
            serving_name="1 scoop",
            serving_grams=20,
            calories=150,
            protein_g=6,
            carbs_g=7,
            fat_g=3,
        ),
    )
    second = log_saved_meal(user_id=1, saved_meal_id=meal.id, entry_date="2026-07-17")
    assert (
        first["logged_entries"][1]["personal_food_revision_id"]
        != revised.current_revision_id
    )
    assert (
        second["logged_entries"][1]["personal_food_revision_id"]
        == revised.current_revision_id
    )
    rows = _entry_rows(saved_meal_db)
    assert rows[1]["food_name_snapshot"] == "Transactional Sauce"
    assert rows[1]["calories"] == 100
    assert rows[3]["food_name_snapshot"] == "Revised Sauce"
    assert rows[3]["calories"] == 150


def test_invalid_component_prevalidation_inserts_zero_entries(saved_meal_db) -> None:
    meal, _, personal = _mixed_meal()
    archive_personal_food(user_id=1, personal_food_id=personal.id)
    with pytest.raises(SavedMealValidationError, match="archived"):
        log_saved_meal(
            user_id=1,
            saved_meal_id=meal.id,
            entry_date="2026-07-16",
        )
    assert _entry_rows(saved_meal_db) == []


def test_insert_failure_rolls_back_every_meal_item(
    saved_meal_db,
    monkeypatch,
) -> None:
    meal, _, _ = _mixed_meal()
    original = saved_meal_logging_service._insert_prepared_entry
    call_count = 0

    def fail_second(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("injected second-item failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        saved_meal_logging_service,
        "_insert_prepared_entry",
        fail_second,
    )
    with pytest.raises(RuntimeError, match="second-item"):
        log_saved_meal(
            user_id=1,
            saved_meal_id=meal.id,
            entry_date="2026-07-16",
        )
    assert _entry_rows(saved_meal_db) == []


def test_repeated_logging_creates_independent_entries_and_preserves_definition(
    saved_meal_db,
) -> None:
    meal, _, _ = _mixed_meal()
    first = log_saved_meal(user_id=1, saved_meal_id=meal.id, entry_date="2026-07-16")
    second = log_saved_meal(user_id=1, saved_meal_id=meal.id, entry_date="2026-07-17")
    assert len(_entry_rows(saved_meal_db)) == 4
    assert {entry["entry_id"] for entry in first["logged_entries"]}.isdisjoint(
        {entry["entry_id"] for entry in second["logged_entries"]}
    )
    assert meal.item_count == 2


def test_serving_metadata_is_preserved_only_when_current_conversion_matches_saved_grams(
    saved_meal_db,
) -> None:
    food = _canonical_food()
    serving, _ = create_or_update_serving_unit(
        canonical_food_id=food.id,
        unit_name="portion",
        unit_quantity=1,
        display_name="1 portion",
        grams_default=100,
        confidence="High",
        active=True,
    )
    meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Serving Meal",
            default_meal_type="lunch",
            items=(
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=food.id,
                    serving_unit_id=serving.id,
                    serving_quantity=1.5,
                ),
            ),
        ),
    )
    first = log_saved_meal(user_id=1, saved_meal_id=meal.id, entry_date="2026-07-16")
    first_entry_id = first["logged_entries"][0]["entry_id"]
    assert get_serving_unit_log_metadata_for_food_entry(first_entry_id) is not None

    create_or_update_serving_unit(
        canonical_food_id=food.id,
        unit_name="portion",
        unit_quantity=1,
        display_name="1 portion",
        grams_default=110,
        confidence="High",
        active=True,
    )
    second = log_saved_meal(user_id=1, saved_meal_id=meal.id, entry_date="2026-07-17")
    second_entry_id = second["logged_entries"][0]["entry_id"]
    assert second["logged_entries"][0]["grams"] == 150
    assert get_serving_unit_log_metadata_for_food_entry(second_entry_id) is None


def test_archived_meal_and_missing_meal_type_cannot_be_logged(saved_meal_db) -> None:
    meal, _, _ = _mixed_meal(meal_type=None)
    with pytest.raises(SavedMealValidationError, match="meal_type is required"):
        log_saved_meal(user_id=1, saved_meal_id=meal.id, entry_date="2026-07-16")
    archive_saved_meal(user_id=1, saved_meal_id=meal.id)
    with pytest.raises(SavedMealArchivedError):
        log_saved_meal(
            user_id=1,
            saved_meal_id=meal.id,
            entry_date="2026-07-16",
            meal_type="snack",
        )
    assert _entry_rows(saved_meal_db) == []
