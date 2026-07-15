from __future__ import annotations

import sqlite3

import pytest

import database
import services.personal_food_service as personal_food_service
from models.personal_food_models import PersonalFoodRevisionInput
from services.personal_food_service import (
    PersonalFoodDuplicateNameError,
    PersonalFoodNotFoundError,
    PersonalFoodUserNotFoundError,
    PersonalFoodValidationError,
    archive_personal_food,
    create_personal_food,
    get_personal_food,
    list_personal_foods,
    normalize_personal_food_name,
    restore_personal_food,
    revise_personal_food,
    search_personal_foods,
)


@pytest.fixture
def personal_food_db(tmp_path, monkeypatch):
    db_path = tmp_path / "personal_food_service.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _label_input(
    *,
    display_name: str = "Dustin's Protein Powder",
    calories: float | None = 120,
    protein_g: float | None = 24,
    carbs_g: float | None = 3,
    fat_g: float | None = 2,
) -> PersonalFoodRevisionInput:
    return PersonalFoodRevisionInput(
        display_name=display_name,
        brand_name="Example Brand",
        input_basis="nutrition_label",
        serving_name="1 scoop",
        serving_grams=32,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        source_note="Copied from package label",
    )


def test_label_input_normalizes_per_100g_and_retains_entered_values(
    personal_food_db,
) -> None:
    food = create_personal_food(user_id=1, revision_input=_label_input())
    revision = food.current_revision
    assert revision.revision_number == 1
    assert revision.entered_calories == 120
    assert revision.entered_protein_g == 24
    assert revision.calories_per_100g == pytest.approx(375)
    assert revision.protein_g_per_100g == pytest.approx(75)
    assert food.normalized_name == "dustin's protein powder"


def test_per_100g_missing_values_stay_missing_and_zero_stays_zero(
    personal_food_db,
) -> None:
    food = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="Homemade Sauce",
            input_basis="per_100g",
            calories=0,
            protein_g=None,
        ),
    )
    revision = food.current_revision
    assert revision.calories_per_100g == 0
    assert revision.entered_calories == 0
    assert revision.protein_g_per_100g is None


@pytest.mark.parametrize("overflow_field", ("calories", "protein_g"))
def test_label_normalization_overflow_is_rejected_without_partial_rows(
    personal_food_db,
    overflow_field,
) -> None:
    conn = sqlite3.connect(personal_food_db)
    before_counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "personal_foods",
            "personal_food_revisions",
            "foods",
            "food_nutrients",
        )
    }
    conn.close()
    values = {"calories": None, "protein_g": None}
    values[overflow_field] = 1e308

    with pytest.raises(PersonalFoodValidationError, match="finite non-negative"):
        create_personal_food(
            user_id=1,
            revision_input=PersonalFoodRevisionInput(
                display_name=f"Overflow {overflow_field}",
                input_basis="nutrition_label",
                serving_grams=1e-300,
                calories=values["calories"],
                protein_g=values["protein_g"],
            ),
        )

    conn = sqlite3.connect(personal_food_db)
    after_counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in before_counts
    }
    internal_count = conn.execute(
        "SELECT COUNT(*) FROM foods WHERE name LIKE 'Internal Personal Food:%'"
    ).fetchone()[0]
    conn.close()
    assert after_counts == before_counts
    assert internal_count == 0


def test_name_normalization_and_duplicate_identity_are_user_scoped(
    personal_food_db,
) -> None:
    assert normalize_personal_food_name("  My   Bread ") == "my bread"
    create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="My Bread",
            input_basis="per_100g",
            calories=200,
        ),
    )
    with pytest.raises(PersonalFoodDuplicateNameError):
        create_personal_food(
            user_id=1,
            revision_input=PersonalFoodRevisionInput(
                display_name=" my   bread ",
                input_basis="per_100g",
                calories=210,
            ),
        )
    other_user_food = create_personal_food(
        user_id=2,
        revision_input=PersonalFoodRevisionInput(
            display_name="My Bread",
            input_basis="per_100g",
            calories=220,
        ),
    )
    assert other_user_food.user_id == 2


@pytest.mark.parametrize(
    "revision_input",
    (
        PersonalFoodRevisionInput(
            display_name=" ", input_basis="per_100g", calories=10
        ),
        PersonalFoodRevisionInput(display_name="No Nutrition", input_basis="per_100g"),
        PersonalFoodRevisionInput(
            display_name="Bad Basis", input_basis="unsupported", calories=10
        ),
        PersonalFoodRevisionInput(
            display_name="Bad Serving",
            input_basis="nutrition_label",
            serving_grams=0,
            calories=10,
        ),
        PersonalFoodRevisionInput(
            display_name="Negative", input_basis="per_100g", fat_g=-1
        ),
        PersonalFoodRevisionInput(
            display_name="NaN", input_basis="per_100g", calories=float("nan")
        ),
        PersonalFoodRevisionInput(
            display_name="Infinity",
            input_basis="per_100g",
            calories=float("inf"),
        ),
    ),
)
def test_invalid_personal_food_inputs_are_rejected(
    personal_food_db,
    revision_input,
) -> None:
    with pytest.raises(PersonalFoodValidationError):
        create_personal_food(user_id=1, revision_input=revision_input)


def test_invalid_user_is_rejected(personal_food_db) -> None:
    with pytest.raises(PersonalFoodUserNotFoundError):
        create_personal_food(user_id=999, revision_input=_label_input())


def test_search_is_owned_ranked_and_archived_hidden(personal_food_db) -> None:
    exact = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="Bread",
            input_basis="per_100g",
            calories=200,
        ),
    )
    create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="Whole Wheat Bread",
            input_basis="per_100g",
            calories=210,
        ),
    )
    create_personal_food(
        user_id=2,
        revision_input=PersonalFoodRevisionInput(
            display_name="Bread Secret",
            input_basis="per_100g",
            calories=220,
        ),
    )
    results = search_personal_foods(user_id=1, query="bread")
    assert [item.id for item in results][:1] == [exact.id]
    assert all(item.user_id == 1 for item in results)
    archive_personal_food(user_id=1, personal_food_id=exact.id)
    assert exact.id not in {
        item.id for item in search_personal_foods(user_id=1, query="bread")
    }
    assert exact.id in {
        item.id for item in list_personal_foods(user_id=1, include_archived=True)
    }
    restored = restore_personal_food(user_id=1, personal_food_id=exact.id)
    assert restored.active is True


def test_cross_user_read_revise_and_archive_are_rejected(personal_food_db) -> None:
    food = create_personal_food(user_id=1, revision_input=_label_input())
    with pytest.raises(PersonalFoodNotFoundError):
        get_personal_food(user_id=2, personal_food_id=food.id)
    with pytest.raises(PersonalFoodNotFoundError):
        revise_personal_food(
            user_id=2,
            personal_food_id=food.id,
            revision_input=_label_input(calories=130),
        )
    with pytest.raises(PersonalFoodNotFoundError):
        archive_personal_food(user_id=2, personal_food_id=food.id)


@pytest.mark.parametrize("invalid_id", (True, 1.0, "1", 0, -1))
def test_direct_get_rejects_invalid_personal_food_ids(
    personal_food_db,
    invalid_id,
) -> None:
    create_personal_food(user_id=1, revision_input=_label_input())
    with pytest.raises(PersonalFoodValidationError, match="positive integer"):
        get_personal_food(user_id=1, personal_food_id=invalid_id)


def test_boolean_id_does_not_resolve_to_food_one_across_owned_operations(
    personal_food_db,
) -> None:
    create_personal_food(user_id=1, revision_input=_label_input())
    operations = (
        lambda: get_personal_food(user_id=1, personal_food_id=True),
        lambda: revise_personal_food(
            user_id=1,
            personal_food_id=True,
            revision_input=_label_input(calories=130),
        ),
        lambda: archive_personal_food(user_id=1, personal_food_id=True),
        lambda: restore_personal_food(user_id=1, personal_food_id=True),
    )
    for operation in operations:
        with pytest.raises(PersonalFoodValidationError, match="positive integer"):
            operation()


def test_revision_is_immutable_and_current_revision_advances(
    personal_food_db,
) -> None:
    food = create_personal_food(user_id=1, revision_input=_label_input())
    original_revision = food.current_revision
    revised = revise_personal_food(
        user_id=1,
        personal_food_id=food.id,
        revision_input=_label_input(
            display_name="Renamed Protein Powder",
            calories=150,
        ),
    )
    assert revised.current_revision.revision_number == 2
    assert revised.current_revision_id != original_revision.id
    assert revised.revisions[0] == original_revision
    assert revised.revisions[0].entered_calories == 120
    assert revised.current_revision.entered_calories == 150


def test_failed_creation_rolls_back_all_partial_rows(
    personal_food_db,
    monkeypatch,
) -> None:
    def fail_nutrients(*args, **kwargs):
        raise RuntimeError("injected nutrient failure")

    monkeypatch.setattr(
        personal_food_service, "_insert_legacy_nutrients", fail_nutrients
    )
    with pytest.raises(RuntimeError, match="injected nutrient failure"):
        create_personal_food(user_id=1, revision_input=_label_input())
    conn = sqlite3.connect(personal_food_db)
    assert conn.execute("SELECT COUNT(*) FROM personal_foods").fetchone()[0] == 0
    assert (
        conn.execute("SELECT COUNT(*) FROM personal_food_revisions").fetchone()[0] == 0
    )
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM foods WHERE name LIKE 'Internal Personal Food:%'"
        ).fetchone()[0]
        == 0
    )
    conn.close()


def test_failed_revision_preserves_current_revision_and_rows(
    personal_food_db,
    monkeypatch,
) -> None:
    food = create_personal_food(user_id=1, revision_input=_label_input())

    def fail_nutrients(*args, **kwargs):
        raise RuntimeError("injected revision failure")

    monkeypatch.setattr(
        personal_food_service, "_insert_legacy_nutrients", fail_nutrients
    )
    with pytest.raises(RuntimeError, match="injected revision failure"):
        revise_personal_food(
            user_id=1,
            personal_food_id=food.id,
            revision_input=_label_input(calories=150),
        )
    unchanged = get_personal_food(user_id=1, personal_food_id=food.id)
    assert unchanged.current_revision_id == food.current_revision_id
    assert len(unchanged.revisions) == 1


def test_read_operations_do_not_change_schema(personal_food_db) -> None:
    create_personal_food(user_id=1, revision_input=_label_input())
    conn = sqlite3.connect(personal_food_db)
    before = conn.execute(
        "SELECT name, sql FROM sqlite_master ORDER BY name"
    ).fetchall()
    conn.close()
    list_personal_foods(user_id=1)
    search_personal_foods(user_id=1, query="protein")
    conn = sqlite3.connect(personal_food_db)
    after = conn.execute("SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()
    conn.close()
    assert after == before
