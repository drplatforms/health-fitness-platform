from __future__ import annotations

import sqlite3

import pytest

import database
from models.personal_food_models import PersonalFoodRevisionInput
from models.saved_meal_models import SavedMealItemInput, SavedMealMutationInput
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
)
from services.nutrition_serving_unit_service import create_or_update_serving_unit
from services.personal_food_service import (
    archive_personal_food,
    create_personal_food,
)
from services.saved_meal_service import (
    SavedMealDuplicateNameError,
    SavedMealNotFoundError,
    SavedMealValidationError,
    archive_saved_meal,
    create_saved_meal,
    get_saved_meal,
    list_saved_meals,
    normalize_saved_meal_name,
    restore_saved_meal,
    update_saved_meal,
)


@pytest.fixture
def saved_meal_db(tmp_path, monkeypatch):
    db_path = tmp_path / "saved_meals.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    ensure_food_normalization_tables()
    return db_path


def _canonical_food(name: str = "Meal Builder Chicken", calories: float = 200):
    food = create_canonical_food(name, "generic")
    for nutrient_name, amount in (
        ("Calories", calories),
        ("Protein", 30),
        ("Carbohydrates", 5),
        ("Fat", 8),
    ):
        create_canonical_food_nutrient(food.id, nutrient_name, "g", amount)
    return food


def _personal_food(user_id: int = 1, name: str = "My Meal Sauce"):
    return create_personal_food(
        user_id=user_id,
        revision_input=PersonalFoodRevisionInput(
            display_name=name,
            input_basis="nutrition_label",
            serving_name="1 tbsp",
            serving_grams=15,
            calories=50,
            protein_g=1,
            carbs_g=4,
            fat_g=3,
        ),
    )


def _mutation(name: str, *items: SavedMealItemInput, meal_type: str | None = None):
    return SavedMealMutationInput(
        display_name=name,
        default_meal_type=meal_type,
        items=tuple(items),
    )


def test_saved_meal_schema_is_additive_and_idempotent(saved_meal_db) -> None:
    database.initialize_database()
    conn = sqlite3.connect(saved_meal_db)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    indexes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    }
    conn.close()
    assert {"saved_meals", "saved_meal_items"}.issubset(tables)
    assert "idx_saved_meals_user_active_name" in indexes
    assert "idx_saved_meal_items_meal_order" in indexes


def test_create_canonical_meal_persists_order_serving_and_dynamic_macros(
    saved_meal_db,
) -> None:
    chicken = _canonical_food()
    rice = _canonical_food("Meal Builder Rice", calories=130)
    serving, _ = create_or_update_serving_unit(
        canonical_food_id=chicken.id,
        unit_name="portion",
        unit_quantity=1,
        display_name="1 chicken portion",
        grams_default=120,
        confidence="High",
        active=True,
    )
    meal = create_saved_meal(
        user_id=1,
        mutation=_mutation(
            "Chicken Bowl",
            SavedMealItemInput(
                food_type="canonical",
                canonical_food_id=chicken.id,
                serving_unit_id=serving.id,
                serving_quantity=1.5,
            ),
            SavedMealItemInput(
                food_type="canonical", canonical_food_id=rice.id, grams=100
            ),
            meal_type="dinner",
        ),
    )
    assert meal.item_count == 2
    assert [item.item_order for item in meal.items] == [0, 1]
    assert meal.items[0].resolved_grams == 180
    assert meal.items[0].canonical_serving_unit_id == serving.id
    assert meal.items[0].serving_display_snapshot == "1.5 x 1 chicken portion"
    assert meal.calories == 490
    assert meal.protein_g == 84
    assert meal.validation_status == "valid"


def test_mixed_meal_is_owned_and_duplicate_name_is_normalized_per_user(
    saved_meal_db,
) -> None:
    chicken = _canonical_food()
    sauce = _personal_food()
    mutation = _mutation(
        " Protein   Bowl ",
        SavedMealItemInput(
            food_type="canonical", canonical_food_id=chicken.id, grams=100
        ),
        SavedMealItemInput(
            food_type="personal",
            personal_food_id=sauce.id,
            personal_serving_quantity=2,
        ),
    )
    meal = create_saved_meal(user_id=1, mutation=mutation)
    assert normalize_saved_meal_name(" protein bowl ") == "protein bowl"
    assert meal.items[1].resolved_grams == 30
    with pytest.raises(SavedMealDuplicateNameError):
        create_saved_meal(
            user_id=1,
            mutation=_mutation(
                "PROTEIN BOWL",
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=chicken.id,
                    grams=50,
                ),
            ),
        )
    other = create_saved_meal(
        user_id=2,
        mutation=_mutation(
            "Protein Bowl",
            SavedMealItemInput(
                food_type="canonical", canonical_food_id=chicken.id, grams=50
            ),
        ),
    )
    assert other.user_id == 2


def test_update_replaces_definition_and_supports_reorder_add_remove(
    saved_meal_db,
) -> None:
    chicken = _canonical_food()
    rice = _canonical_food("Meal Builder Rice")
    sauce = _personal_food()
    meal = create_saved_meal(
        user_id=1,
        mutation=_mutation(
            "Old Bowl",
            SavedMealItemInput(
                food_type="canonical", canonical_food_id=chicken.id, grams=100
            ),
            SavedMealItemInput(
                food_type="canonical", canonical_food_id=rice.id, grams=80
            ),
        ),
    )
    updated = update_saved_meal(
        user_id=1,
        saved_meal_id=meal.id,
        mutation=_mutation(
            "New Bowl",
            SavedMealItemInput(
                food_type="personal", personal_food_id=sauce.id, grams=25
            ),
            SavedMealItemInput(
                food_type="canonical", canonical_food_id=chicken.id, grams=150
            ),
            meal_type="lunch",
        ),
    )
    assert updated.display_name == "New Bowl"
    assert updated.default_meal_type == "lunch"
    assert [item.food_type for item in updated.items] == ["personal", "canonical"]
    assert [item.resolved_grams for item in updated.items] == [25, 150]
    assert all(item.canonical_food_id != rice.id for item in updated.items)


def test_archive_restore_listing_and_cross_user_operations_are_scoped(
    saved_meal_db,
) -> None:
    food = _canonical_food()
    meal = create_saved_meal(
        user_id=1,
        mutation=_mutation(
            "Scoped Meal",
            SavedMealItemInput(
                food_type="canonical", canonical_food_id=food.id, grams=100
            ),
        ),
    )
    with pytest.raises(SavedMealNotFoundError):
        get_saved_meal(user_id=2, saved_meal_id=meal.id)
    with pytest.raises(SavedMealNotFoundError):
        update_saved_meal(
            user_id=2,
            saved_meal_id=meal.id,
            mutation=_mutation(
                "Stolen",
                SavedMealItemInput(
                    food_type="canonical", canonical_food_id=food.id, grams=10
                ),
            ),
        )
    archived = archive_saved_meal(user_id=1, saved_meal_id=meal.id)
    assert archived.active is False
    assert list_saved_meals(user_id=1) == []
    assert [item.id for item in list_saved_meals(user_id=1, include_archived=True)] == [
        meal.id
    ]
    with pytest.raises(SavedMealNotFoundError):
        restore_saved_meal(user_id=2, saved_meal_id=meal.id)
    assert restore_saved_meal(user_id=1, saved_meal_id=meal.id).active is True


def test_cross_user_personal_food_and_invalid_amount_modes_are_rejected(
    saved_meal_db,
) -> None:
    personal = _personal_food(user_id=2)
    with pytest.raises(SavedMealValidationError, match="Personal food not found"):
        create_saved_meal(
            user_id=1,
            mutation=_mutation(
                "Wrong Owner",
                SavedMealItemInput(
                    food_type="personal", personal_food_id=personal.id, grams=20
                ),
            ),
        )
    food = _canonical_food()
    with pytest.raises(SavedMealValidationError, match="exactly one"):
        create_saved_meal(
            user_id=1,
            mutation=_mutation(
                "Bad Amount",
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=food.id,
                    grams=20,
                    serving_unit_id=1,
                    serving_quantity=1,
                ),
            ),
        )
    with pytest.raises(SavedMealValidationError, match="at least one"):
        create_saved_meal(user_id=1, mutation=_mutation("Empty Meal"))


def test_archived_component_keeps_meal_visible_and_marks_it_invalid(
    saved_meal_db,
) -> None:
    personal = _personal_food()
    meal = create_saved_meal(
        user_id=1,
        mutation=_mutation(
            "Personal Meal",
            SavedMealItemInput(
                food_type="personal", personal_food_id=personal.id, grams=30
            ),
        ),
    )
    archive_personal_food(user_id=1, personal_food_id=personal.id)
    refreshed = get_saved_meal(user_id=1, saved_meal_id=meal.id)
    assert refreshed.validation_status == "invalid"
    assert refreshed.invalid_item_count == 1
    assert refreshed.items[0].validation_reason == "Personal food is archived."
