from __future__ import annotations

import sqlite3

import pytest

import database
from models.personal_food_models import PersonalFoodRevisionInput
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
)
from services.nutrition_service import add_canonical_food_entry
from services.nutrition_target_vs_actual_service import build_nutrition_actuals
from services.personal_food_logging_service import (
    PersonalFoodLogEntryNotFoundError,
    delete_personal_food_entry,
    get_daily_personal_food_logs,
    log_personal_food,
    update_personal_food_entry,
)
from services.personal_food_service import (
    PersonalFoodArchivedError,
    PersonalFoodNotFoundError,
    PersonalFoodValidationError,
    archive_personal_food,
    create_personal_food,
    revise_personal_food,
)


@pytest.fixture
def personal_food_db(tmp_path, monkeypatch):
    db_path = tmp_path / "personal_food_logging.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def _create_label_food(*, calories: float = 100, serving_grams: float = 50):
    return create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="My Frozen Meal",
            input_basis="nutrition_label",
            serving_name="1 tray",
            serving_grams=serving_grams,
            calories=calories,
            protein_g=10,
            carbs_g=None,
            fat_g=0,
        ),
    )


def test_grams_logging_uses_known_nutrients_only(personal_food_db) -> None:
    food = _create_label_food()
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=25,
        entry_date="2026-07-14",
        meal_type="lunch",
    )
    assert logged.grams == 25
    assert logged.serving_quantity is None
    assert logged.nutrient_summary == {
        "calories": 50,
        "protein_g": 5,
        "fat_g": 0,
    }


def test_default_serving_quantity_resolves_to_grams(personal_food_db) -> None:
    food = _create_label_food(serving_grams=40)
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        serving_quantity=2,
        entry_date="2026-07-14",
    )
    assert logged.grams == 80
    assert logged.serving_quantity == 2
    assert logged.nutrient_summary["calories"] == 200


def test_resolved_serving_underflow_is_rejected_without_food_entry(
    personal_food_db,
) -> None:
    food = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="Tiny Serving",
            input_basis="nutrition_label",
            serving_name="tiny serving",
            serving_grams=1e-300,
            calories=1e-300,
        ),
    )
    conn = sqlite3.connect(personal_food_db)
    before_count = conn.execute("SELECT COUNT(*) FROM food_entries").fetchone()[0]
    conn.close()

    with pytest.raises(PersonalFoodValidationError, match="resolved_grams"):
        log_personal_food(
            user_id=1,
            personal_food_id=food.id,
            serving_quantity=1e-300,
        )

    conn = sqlite3.connect(personal_food_db)
    after_count = conn.execute("SELECT COUNT(*) FROM food_entries").fetchone()[0]
    conn.close()
    assert after_count == before_count


def test_personal_food_logging_accepts_shared_5000_gram_ceiling(
    personal_food_db,
) -> None:
    food = _create_label_food()
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=5_000,
        entry_date="2026-07-14",
    )
    assert logged.grams == 5_000


@pytest.mark.parametrize(
    ("serving_grams", "log_kwargs"),
    (
        (50, {"grams": 5_000.001}),
        (50, {"grams": 5_001}),
        (5_001, {"serving_quantity": 1}),
    ),
)
def test_personal_food_logging_rejects_amounts_above_shared_ceiling_without_entry(
    personal_food_db,
    serving_grams,
    log_kwargs,
) -> None:
    food = _create_label_food(serving_grams=serving_grams)
    conn = sqlite3.connect(personal_food_db)
    before_count = conn.execute("SELECT COUNT(*) FROM food_entries").fetchone()[0]
    conn.close()

    with pytest.raises(PersonalFoodValidationError, match="too large"):
        log_personal_food(
            user_id=1,
            personal_food_id=food.id,
            entry_date="2026-07-14",
            **log_kwargs,
        )

    conn = sqlite3.connect(personal_food_db)
    after_count = conn.execute("SELECT COUNT(*) FROM food_entries").fetchone()[0]
    conn.close()
    assert after_count == before_count


@pytest.mark.parametrize(
    ("grams", "serving_quantity"),
    ((None, None), (10, 1), (0, None), (float("inf"), None), (1_000_000, None)),
)
def test_invalid_logging_amounts_are_rejected(
    personal_food_db,
    grams,
    serving_quantity,
) -> None:
    food = _create_label_food()
    with pytest.raises(PersonalFoodValidationError):
        log_personal_food(
            user_id=1,
            personal_food_id=food.id,
            grams=grams,
            serving_quantity=serving_quantity,
        )


def test_serving_logging_requires_default_serving(personal_food_db) -> None:
    food = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="No Serving Food",
            input_basis="per_100g",
            calories=100,
        ),
    )
    with pytest.raises(PersonalFoodValidationError, match="no default serving"):
        log_personal_food(
            user_id=1,
            personal_food_id=food.id,
            serving_quantity=1,
        )


def test_archived_and_cross_user_foods_cannot_be_logged(personal_food_db) -> None:
    food = _create_label_food()
    with pytest.raises(PersonalFoodNotFoundError):
        log_personal_food(user_id=2, personal_food_id=food.id, grams=10)
    archive_personal_food(user_id=1, personal_food_id=food.id)
    with pytest.raises(PersonalFoodArchivedError):
        log_personal_food(user_id=1, personal_food_id=food.id, grams=10)


@pytest.mark.parametrize("invalid_id", (True, 1.0, "1", 0, -1))
def test_direct_logging_rejects_invalid_personal_food_ids(
    personal_food_db,
    invalid_id,
) -> None:
    _create_label_food()
    with pytest.raises(PersonalFoodValidationError, match="positive integer"):
        log_personal_food(user_id=1, personal_food_id=invalid_id, grams=10)


@pytest.mark.parametrize("overflow_field", ("calories", "protein_g"))
def test_logging_overflow_rolls_back_without_food_entry(
    personal_food_db,
    overflow_field,
) -> None:
    nutrients = {"calories": None, "protein_g": None}
    nutrients[overflow_field] = 1e308
    food = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name=f"Snapshot Overflow {overflow_field}",
            input_basis="per_100g",
            calories=nutrients["calories"],
            protein_g=nutrients["protein_g"],
        ),
    )
    conn = sqlite3.connect(personal_food_db)
    before_count = conn.execute("SELECT COUNT(*) FROM food_entries").fetchone()[0]
    conn.close()

    with pytest.raises(PersonalFoodValidationError, match="finite non-negative"):
        log_personal_food(
            user_id=1,
            personal_food_id=food.id,
            grams=5_000,
        )

    conn = sqlite3.connect(personal_food_db)
    after_count = conn.execute("SELECT COUNT(*) FROM food_entries").fetchone()[0]
    conn.close()
    assert after_count == before_count


def test_high_finite_logging_snapshot_remains_supported(personal_food_db) -> None:
    food = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="High Finite Snapshot",
            input_basis="per_100g",
            calories=1e300,
        ),
    )
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=5_000,
    )
    assert logged.nutrient_summary["calories"] == pytest.approx(5e301)


def test_revision_history_and_target_actuals_remain_stable(personal_food_db) -> None:
    food = _create_label_food(calories=100)
    first = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        serving_quantity=1,
        entry_date="2026-07-14",
    )
    revised = revise_personal_food(
        user_id=1,
        personal_food_id=food.id,
        revision_input=PersonalFoodRevisionInput(
            display_name="Renamed Frozen Meal",
            input_basis="nutrition_label",
            serving_name="1 tray",
            serving_grams=50,
            calories=150,
            protein_g=12,
            carbs_g=None,
            fat_g=1,
        ),
    )
    second = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        serving_quantity=1,
        entry_date="2026-07-14",
    )
    assert first.personal_food_revision_id != second.personal_food_revision_id
    assert first.display_name == "My Frozen Meal"
    assert second.display_name == "Renamed Frozen Meal"
    assert first.nutrient_summary["calories"] == 100
    assert second.nutrient_summary["calories"] == 150
    assert revised.current_revision.revision_number == 2

    actuals = build_nutrition_actuals(1, "2026-07-14")
    assert actuals.logged_calories == 250
    conn = sqlite3.connect(personal_food_db)
    rows = conn.execute(
        """
        SELECT personal_food_revision_id, food_name_snapshot, calories
        FROM food_entries
        ORDER BY id
        """
    ).fetchall()
    assert rows == [
        (first.personal_food_revision_id, "My Frozen Meal", 100),
        (second.personal_food_revision_id, "Renamed Frozen Meal", 150),
    ]
    archive_personal_food(user_id=1, personal_food_id=food.id)
    assert build_nutrition_actuals(1, "2026-07-14").logged_calories == 250
    conn.close()


def test_personal_log_list_is_user_date_and_food_type_scoped(
    personal_food_db,
) -> None:
    food = _create_label_food()
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=25,
        entry_date="2026-07-14",
        meal_type="lunch",
    )
    log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=10,
        entry_date="2026-07-15",
    )
    canonical_food = create_canonical_food("Canonical Test Food", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 100)
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=canonical_food.id,
        grams=20,
        entry_date="2026-07-14",
    )

    entries = get_daily_personal_food_logs(
        user_id=1,
        entry_date="2026-07-14",
    )

    assert entries == [
        {
            "entry_id": logged.logged_food_entry_id,
            "food_type": "personal",
            "personal_food_id": food.id,
            "personal_food_revision_id": logged.personal_food_revision_id,
            "food_name": "My Frozen Meal",
            "grams": 25.0,
            "meal_type": "lunch",
            "calories": 50.0,
            "protein_g": 5.0,
            "carbs_g": None,
            "fat_g": 0.0,
            "serving_name": "1 tray",
            "serving_grams": 50.0,
        }
    ]
    assert "legacy_food_id" not in entries[0]
    assert (
        get_daily_personal_food_logs(
            user_id=2,
            entry_date="2026-07-14",
        )
        == []
    )


def test_personal_log_grams_update_uses_stored_revision(personal_food_db) -> None:
    food = _create_label_food(calories=100, serving_grams=50)
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=50,
        entry_date="2026-07-14",
    )
    revise_personal_food(
        user_id=1,
        personal_food_id=food.id,
        revision_input=PersonalFoodRevisionInput(
            display_name="Renamed Frozen Meal",
            input_basis="nutrition_label",
            serving_name="new tray",
            serving_grams=50,
            calories=250,
        ),
    )

    updated = update_personal_food_entry(
        user_id=1,
        entry_id=logged.logged_food_entry_id,
        grams=100,
        entry_date="2026-07-14",
    )

    assert updated["personal_food_revision_id"] == logged.personal_food_revision_id
    assert updated["food_name"] == "My Frozen Meal"
    assert updated["grams"] == 100
    assert updated["calories"] == 200


def test_personal_log_saved_serving_update_uses_stored_revision(
    personal_food_db,
) -> None:
    food = _create_label_food(calories=100, serving_grams=40)
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=20,
        entry_date="2026-07-14",
    )
    revise_personal_food(
        user_id=1,
        personal_food_id=food.id,
        revision_input=PersonalFoodRevisionInput(
            display_name="My Frozen Meal",
            input_basis="nutrition_label",
            serving_name="larger tray",
            serving_grams=100,
            calories=500,
        ),
    )

    updated = update_personal_food_entry(
        user_id=1,
        entry_id=logged.logged_food_entry_id,
        serving_quantity=2,
        entry_date="2026-07-14",
    )

    assert updated["grams"] == 80
    assert updated["calories"] == 200
    assert updated["serving_name"] == "1 tray"
    assert updated["serving_grams"] == 40


def test_personal_log_meal_only_update_preserves_amount_and_nutrients(
    personal_food_db,
) -> None:
    food = _create_label_food()
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=25,
        entry_date="2026-07-14",
    )

    updated = update_personal_food_entry(
        user_id=1,
        entry_id=logged.logged_food_entry_id,
        meal_type="Dinner",
        entry_date="2026-07-14",
    )

    assert updated["grams"] == 25
    assert updated["calories"] == 50
    assert updated["protein_g"] == 5
    assert updated["meal_type"] == "dinner"


def test_invalid_personal_log_update_rolls_back(personal_food_db) -> None:
    food = _create_label_food()
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=25,
        entry_date="2026-07-14",
        meal_type="lunch",
    )

    with pytest.raises(PersonalFoodValidationError):
        update_personal_food_entry(
            user_id=1,
            entry_id=logged.logged_food_entry_id,
            grams=5_001,
            meal_type="dinner",
            entry_date="2026-07-14",
        )

    entry = get_daily_personal_food_logs(
        user_id=1,
        entry_date="2026-07-14",
    )[0]
    assert entry["grams"] == 25
    assert entry["meal_type"] == "lunch"
    assert entry["calories"] == 50


def test_personal_log_update_rejects_cross_user_canonical_and_missing_entries(
    personal_food_db,
) -> None:
    food = _create_label_food()
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=25,
        entry_date="2026-07-14",
    )
    canonical_food = create_canonical_food("Canonical Update Guard", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 100)
    canonical = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=canonical_food.id,
        grams=20,
        entry_date="2026-07-14",
    )

    for user_id, entry_id in (
        (2, logged.logged_food_entry_id),
        (1, canonical["logged_food_entry_id"]),
        (1, 999_999),
    ):
        with pytest.raises(PersonalFoodLogEntryNotFoundError):
            update_personal_food_entry(
                user_id=user_id,
                entry_id=entry_id,
                grams=50,
            )


def test_personal_log_delete_enforces_owner_type_and_date(personal_food_db) -> None:
    food = _create_label_food()
    logged = log_personal_food(
        user_id=1,
        personal_food_id=food.id,
        grams=25,
        entry_date="2026-07-14",
    )
    canonical_food = create_canonical_food("Canonical Delete Guard", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 100)
    canonical = add_canonical_food_entry(
        user_id=1,
        canonical_food_id=canonical_food.id,
        grams=20,
        entry_date="2026-07-14",
    )

    with pytest.raises(PersonalFoodLogEntryNotFoundError):
        delete_personal_food_entry(
            user_id=2,
            entry_id=logged.logged_food_entry_id,
        )
    with pytest.raises(PersonalFoodLogEntryNotFoundError):
        delete_personal_food_entry(
            user_id=1,
            entry_id=canonical["logged_food_entry_id"],
        )
    with pytest.raises(PersonalFoodLogEntryNotFoundError):
        delete_personal_food_entry(
            user_id=1,
            entry_id=logged.logged_food_entry_id,
            entry_date="2026-07-15",
        )

    assert delete_personal_food_entry(
        user_id=1,
        entry_id=logged.logged_food_entry_id,
        entry_date="2026-07-14",
    ) == {"deleted": True, "entry_id": logged.logged_food_entry_id}
    assert (
        get_daily_personal_food_logs(
            user_id=1,
            entry_date="2026-07-14",
        )
        == []
    )
