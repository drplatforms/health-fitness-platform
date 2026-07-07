from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    seed_starter_canonical_foods,
)
from services.nutrition_service import (
    add_food_entry,
    get_daily_canonical_food_logs,
    get_daily_canonical_food_macro_totals,
    get_daily_nutrition,
)
from services.nutrition_serving_unit_logging_service import (
    get_serving_unit_log_metadata_for_food_entry,
)
from services.nutrition_serving_unit_service import (
    get_active_serving_units_for_canonical_food,
    seed_canonical_food_serving_units,
)


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _client() -> TestClient:
    return TestClient(app)


def _create_legacy_food_entries_schema(db_path) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            grams REAL NOT NULL,
            entry_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO food_entries (user_id, food_id, grams, entry_date)
        VALUES (1, 1, 150, '2026-06-05')
        """
    )
    conn.commit()
    conn.close()


def _seed_chicken() -> int:
    seed_starter_canonical_foods()
    response = _client().get("/foods/canonical/search?q=chicken%20breast")
    assert response.status_code == 200
    return int(response.json()["results"][0]["canonical_food_id"])


def _serving_unit_id(canonical_food_id: int, display_name: str) -> int:
    seed_canonical_food_serving_units()
    serving_units = get_active_serving_units_for_canonical_food(canonical_food_id)
    for serving_unit in serving_units:
        if serving_unit.display_name == display_name:
            return serving_unit.id
    raise AssertionError(f"Missing serving unit: {display_name}")


def test_initialize_database_upgrades_legacy_food_entries_table_safely(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    _create_legacy_food_entries_schema(db_path)

    database.initialize_database()

    conn = database.get_connection()
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(food_entries)").fetchall()
    }
    row = conn.execute(
        """
        SELECT user_id, food_id, grams, entry_date
        FROM food_entries
        WHERE id = 1
        """
    ).fetchone()
    conn.close()

    assert {
        "canonical_food_id",
        "meal_type",
        "notes",
        "calories",
        "protein_g",
        "carbs_g",
        "fat_g",
    }.issubset(columns)
    assert row["user_id"] == 1
    assert row["food_id"] == 1
    assert row["grams"] == 150.0
    assert row["entry_date"] == "2026-06-05"


def test_canonical_logging_route_upgrades_legacy_food_entries_schema_on_app_startup(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    _create_legacy_food_entries_schema(db_path)

    with TestClient(app) as client:
        search_response = client.get("/foods/canonical/search?q=chicken%20breast")
        assert search_response.status_code == 200
        canonical_food_id = int(
            search_response.json()["results"][0]["canonical_food_id"]
        )

        response = client.post(
            "/nutrition/1/log-canonical",
            json={
                "canonical_food_id": canonical_food_id,
                "grams": 100,
                "entry_date": "2026-06-05",
            },
        )

    assert response.status_code == 200
    assert response.json()["canonical_food_id"] == canonical_food_id

    conn = database.get_connection()
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(food_entries)").fetchall()
    }
    logged_row = conn.execute(
        """
        SELECT canonical_food_id, calories, protein_g, carbs_g, fat_g
        FROM food_entries
        WHERE id = ?
        """,
        (response.json()["logged_food_entry_id"],),
    ).fetchone()
    conn.close()

    assert {
        "canonical_food_id",
        "meal_type",
        "notes",
        "calories",
        "protein_g",
        "carbs_g",
        "fat_g",
    }.issubset(columns)
    assert logged_row["canonical_food_id"] == canonical_food_id
    assert logged_row["calories"] == 165.0
    assert logged_row["protein_g"] == 31.0
    assert logged_row["carbs_g"] == 0.0
    assert logged_row["fat_g"] == 3.6


def test_canonical_food_can_be_logged_by_canonical_food_id(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 150,
            "entry_date": "2026-06-05",
            "meal_type": "lunch",
            "notes": "post-workout",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["logged_food_entry_id"] > 0
    assert payload["canonical_food_id"] == canonical_food_id
    assert payload["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert payload["grams"] == 150.0
    assert payload["logged_date"] == "2026-06-05"
    assert payload["meal_type"] == "lunch"
    assert payload["notes"] == "post-workout"
    assert payload["nutrient_summary"] == {
        "calories": 247.5,
        "protein_g": 46.5,
        "carbohydrate_g": 0.0,
        "fat_g": 5.4,
    }
    assert "source_payload_json" not in payload

    conn = database.get_connection()
    conn.row_factory = database.sqlite3.Row
    row = conn.execute(
        """
        SELECT canonical_food_id, grams, meal_type, notes, calories, protein_g, carbs_g, fat_g
        FROM food_entries
        WHERE id = ?
        """,
        (payload["logged_food_entry_id"],),
    ).fetchone()
    conn.close()

    assert row["canonical_food_id"] == canonical_food_id
    assert row["grams"] == 150.0
    assert row["meal_type"] == "lunch"
    assert row["notes"] == "post-workout"
    assert row["calories"] == 247.5
    assert row["protein_g"] == 46.5
    assert row["carbs_g"] == 0.0
    assert row["fat_g"] == 5.4


def test_canonical_food_can_be_logged_by_serving_unit(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()
    serving_unit_id = _serving_unit_id(
        canonical_food_id,
        "4 oz cooked chicken breast",
    )

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "serving_unit_id": serving_unit_id,
            "quantity": 1.5,
            "entry_date": "2026-06-05",
            "meal_type": "dinner",
            "notes": "serving unit path",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["logged_food_entry_id"] > 0
    assert payload["canonical_food_id"] == canonical_food_id
    assert payload["serving_unit_id"] == serving_unit_id
    assert payload["display_name"] == "Chicken Breast, Cooked, Skinless"
    assert payload["serving_quantity"] == 1.5
    assert payload["serving_display"] == "1.5 x 4 oz cooked chicken breast"
    assert payload["resolved_grams"] == 169.5
    assert payload["grams"] == 169.5
    assert payload["meal_type"] == "dinner"
    assert payload["notes"] == "serving unit path"
    assert payload["nutrient_summary"] == {
        "calories": 279.7,
        "protein_g": 52.5,
        "carbohydrate_g": 0.0,
        "fat_g": 6.1,
    }

    conn = database.get_connection()
    row = conn.execute(
        """
        SELECT canonical_food_id, grams, meal_type, notes, calories, protein_g, carbs_g, fat_g
        FROM food_entries
        WHERE id = ?
        """,
        (payload["logged_food_entry_id"],),
    ).fetchone()
    conn.close()

    assert row["canonical_food_id"] == canonical_food_id
    assert row["grams"] == 169.5
    assert row["meal_type"] == "dinner"
    assert row["notes"] == "serving unit path"
    assert row["calories"] == 279.7
    assert row["protein_g"] == 52.5
    assert row["carbs_g"] == 0.0
    assert row["fat_g"] == 6.1

    metadata = get_serving_unit_log_metadata_for_food_entry(
        payload["logged_food_entry_id"]
    )
    assert metadata is not None
    assert metadata.resolved_grams == 169.5

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["entry_count"] == 1
    assert actuals["logged_calories"] == 279.7
    assert actuals["logged_protein"] == 52.5
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 6.1


def test_canonical_logging_rejects_mixed_and_incomplete_serving_modes(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()
    serving_unit_id = _serving_unit_id(
        canonical_food_id,
        "100g cooked chicken breast",
    )

    mixed = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "serving_unit_id": serving_unit_id,
            "quantity": 1,
        },
    )
    missing_quantity = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "serving_unit_id": serving_unit_id,
        },
    )
    missing_mode = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": canonical_food_id},
    )

    assert mixed.status_code == 400
    assert mixed.json()["detail"] == (
        "Provide either grams or serving_unit_id with quantity, not both."
    )
    assert missing_quantity.status_code == 400
    assert missing_quantity.json()["detail"] == (
        "serving_unit_id and quantity are required for serving-unit logging."
    )
    assert missing_mode.status_code == 400
    assert missing_mode.json()["detail"] == (
        "Either grams or serving_unit_id with quantity is required."
    )


def test_canonical_logging_rejects_unreasonable_resolved_grams(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()
    serving_unit_id = _serving_unit_id(
        canonical_food_id,
        "100g cooked chicken breast",
    )

    grams_response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": canonical_food_id, "grams": 5000.1},
    )
    serving_response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "serving_unit_id": serving_unit_id,
            "quantity": 51,
        },
    )

    assert grams_response.status_code == 400
    assert grams_response.json()["detail"] == (
        "grams must be less than or equal to 5000."
    )
    assert serving_response.status_code == 400
    assert serving_response.json()["detail"] == (
        "grams must be less than or equal to 5000."
    )


def test_inactive_canonical_food_cannot_be_logged(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    inactive_food = create_canonical_food(
        "Inactive Canonical Food",
        "generic",
        active=False,
    )
    create_canonical_food_nutrient(inactive_food.id, "Calories", "kcal", 100)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": inactive_food.id, "grams": 100},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Canonical food is inactive."


def test_missing_canonical_food_returns_safe_404(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": 99999, "grams": 100},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Canonical food not found."


def test_raw_source_record_id_cannot_be_logged_as_the_user_facing_identifier(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"raw_food_source_record_id": 123, "grams": 100},
    )

    assert response.status_code == 422


def test_canonical_logging_requires_positive_grams(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": canonical_food_id, "grams": 0},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "grams must be greater than 0."


def test_invalid_canonical_logging_date_is_safe_400(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "06/05/2026",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "entry_date must use YYYY-MM-DD format."


def test_missing_canonical_nutrients_remain_missing_not_zero(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = create_canonical_food("Protein Only Test Food", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Protein", "g", 20)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food.id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["nutrient_summary"] == {"protein_g": 20.0}

    conn = database.get_connection()
    row = conn.execute(
        """
        SELECT calories, protein_g, carbs_g, fat_g
        FROM food_entries
        WHERE id = ?
        """,
        (response.json()["logged_food_entry_id"],),
    ).fetchone()
    conn.close()

    assert row["calories"] is None
    assert row["protein_g"] == 20.0
    assert row["carbs_g"] is None
    assert row["fat_g"] is None

    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")
    assert nutrition["Protein"]["amount"] == 20.0
    assert "Calories" not in nutrition
    assert "Carbohydrates" not in nutrition
    assert "Fat" not in nutrition

    totals = get_daily_canonical_food_macro_totals(user_id=1, entry_date="2026-06-05")
    assert totals == {
        "entry_count": 1,
        "calories": None,
        "protein_g": 20.0,
        "carbs_g": None,
        "fat_g": None,
    }


def test_explicit_zero_macro_values_remain_zero_in_logged_entry_and_rollup(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = create_canonical_food("Zero Macro Test Food", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 0)
    create_canonical_food_nutrient(canonical_food.id, "Protein", "g", 0)
    create_canonical_food_nutrient(canonical_food.id, "Carbohydrate", "g", 0)
    create_canonical_food_nutrient(canonical_food.id, "Fat", "g", 0)

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food.id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["nutrient_summary"] == {
        "calories": 0.0,
        "protein_g": 0.0,
        "carbohydrate_g": 0.0,
        "fat_g": 0.0,
    }

    totals = get_daily_canonical_food_macro_totals(user_id=1, entry_date="2026-06-05")
    assert totals == {
        "entry_count": 1,
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
    }


def test_canonical_logged_foods_create_usable_logged_actuals(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 200,
            "entry_date": "2026-06-05",
        },
    )
    assert response.status_code == 200

    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")
    assert nutrition["Calories"]["amount"] == 330.0
    assert nutrition["Protein"]["amount"] == 62.0
    assert nutrition["Carbohydrates"]["amount"] == 0.0
    assert nutrition["Fat"]["amount"] == 7.2


def test_target_vs_actual_reflects_canonical_logged_foods(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 200,
            "entry_date": "2026-06-05",
        },
    )
    assert response.status_code == 200

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")

    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["entry_count"] == 1
    assert actuals["logged_calories"] == 330.0
    assert actuals["logged_protein"] == 62.0
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 7.2

    totals = get_daily_canonical_food_macro_totals(user_id=1, entry_date="2026-06-05")
    assert totals == {
        "entry_count": 1,
        "calories": 330.0,
        "protein_g": 62.0,
        "carbs_g": 0.0,
        "fat_g": 7.2,
    }


def test_expanded_canonical_food_can_be_logged_and_counted(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()
    search_response = _client().get("/foods/canonical/search?q=tuna")
    assert search_response.status_code == 200
    tuna_id = search_response.json()["results"][0]["canonical_food_id"]

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": tuna_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Tuna, Canned in Water"
    assert response.json()["nutrient_summary"] == {
        "calories": 116.0,
        "protein_g": 25.5,
        "carbohydrate_g": 0.0,
        "fat_g": 0.8,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 116.0
    assert actuals["logged_protein"] == 25.5
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 0.8


def test_food_catalog_expansion_v1_new_canonical_food_can_be_logged(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()
    search_response = _client().get("/foods/canonical/search?q=skyr")
    assert search_response.status_code == 200
    skyr_id = search_response.json()["results"][0]["canonical_food_id"]

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": skyr_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Skyr, Plain Nonfat"
    assert response.json()["nutrient_summary"] == {
        "calories": 63.0,
        "protein_g": 11.0,
        "carbohydrate_g": 4.0,
        "fat_g": 0.2,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 63.0
    assert actuals["logged_protein"] == 11.0
    assert actuals["logged_carbs"] == 4.0
    assert actuals["logged_fat"] == 0.2


def test_existing_raw_source_nutrition_log_behavior_remains_stable(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES ('Legacy Rice')")
    cursor.execute("SELECT id FROM foods WHERE name = 'Legacy Rice'")
    food_id = cursor.fetchone()["id"]
    cursor.execute("SELECT id FROM nutrients WHERE name = 'Carbohydrates'")
    carbohydrate_id = cursor.fetchone()["id"]
    cursor.execute(
        """
        INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
        VALUES (?, ?, ?)
        """,
        (food_id, carbohydrate_id, 28.0),
    )
    conn.commit()
    conn.close()

    add_food_entry(user_id=1, food_id=food_id, grams=150, entry_date="2026-06-05")
    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")

    assert nutrition["Carbohydrates"]["amount"] == 42.0
    assert nutrition["Carbohydrates"]["unit"] == "g"


def test_canonical_logging_does_not_expose_raw_source_payloads(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food = create_canonical_food("Linked Canonical Food", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 100)
    create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="raw-private",
        raw_description="Verbose raw source record",
        source_payload={"private_payload": True},
    )

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={"canonical_food_id": canonical_food.id, "grams": 100},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "source_payload_json" not in payload
    assert "raw_description" not in payload


def test_daily_canonical_rollup_separates_users_and_dates(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    first = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    second = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 50,
            "entry_date": "2026-06-05",
        },
    )
    third = _client().post(
        "/nutrition/2/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    fourth = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-06",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert fourth.status_code == 200

    user_one_day_one = get_daily_canonical_food_macro_totals(
        user_id=1,
        entry_date="2026-06-05",
    )
    user_two_day_one = get_daily_canonical_food_macro_totals(
        user_id=2,
        entry_date="2026-06-05",
    )
    user_one_day_two = get_daily_canonical_food_macro_totals(
        user_id=1,
        entry_date="2026-06-06",
    )

    assert user_one_day_one == {
        "entry_count": 2,
        "calories": 247.5,
        "protein_g": 46.5,
        "carbs_g": 0.0,
        "fat_g": 5.4,
    }
    assert user_two_day_one == {
        "entry_count": 1,
        "calories": 165.0,
        "protein_g": 31.0,
        "carbs_g": 0.0,
        "fat_g": 3.6,
    }
    assert user_one_day_two == {
        "entry_count": 1,
        "calories": 165.0,
        "protein_g": 31.0,
        "carbs_g": 0.0,
        "fat_g": 3.6,
    }


def test_canonical_totals_endpoint_is_safe_and_returns_rollup(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    assert logged.status_code == 200

    response = _client().get("/nutrition/1/canonical-totals?date=2026-06-05")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "user_id": 1,
        "date": "2026-06-05",
        "totals": {
            "entry_count": 1,
            "calories": 165.0,
            "protein_g": 31.0,
            "carbs_g": 0.0,
            "fat_g": 3.6,
        },
    }


def test_canonical_logs_endpoint_returns_empty_list_for_empty_day(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/nutrition/1/canonical-logs?date=2026-06-05")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "user_id": 1,
        "date": "2026-06-05",
        "entries": [],
    }


def test_daily_canonical_logs_return_logged_entries_with_snapshots(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 150,
            "entry_date": "2026-06-05",
            "meal_type": "lunch",
        },
    )
    assert logged.status_code == 200

    response = _client().get("/nutrition/1/canonical-logs?date=2026-06-05")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["date"] == "2026-06-05"
    assert payload["entries"] == [
        {
            "entry_id": logged.json()["logged_food_entry_id"],
            "canonical_food_id": canonical_food_id,
            "food_name": "Chicken Breast, Cooked, Skinless",
            "grams": 150.0,
            "meal_type": "lunch",
            "calories": 247.5,
            "protein_g": 46.5,
            "carbs_g": 0.0,
            "fat_g": 5.4,
        }
    ]
    assert "source_payload_json" not in payload["entries"][0]
    assert "raw_description" not in payload["entries"][0]

    service_entries = get_daily_canonical_food_logs(
        user_id=1,
        entry_date="2026-06-05",
    )
    assert service_entries == payload["entries"]


def test_daily_canonical_logs_separate_users_and_dates(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()

    first = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
            "meal_type": "breakfast",
        },
    )
    second = _client().post(
        "/nutrition/2/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 200,
            "entry_date": "2026-06-05",
            "meal_type": "lunch",
        },
    )
    third = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 50,
            "entry_date": "2026-06-06",
            "meal_type": "snack",
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200

    user_one_day_one = _client().get("/nutrition/1/canonical-logs?date=2026-06-05")
    user_two_day_one = _client().get("/nutrition/2/canonical-logs?date=2026-06-05")
    user_one_day_two = _client().get("/nutrition/1/canonical-logs?date=2026-06-06")

    assert user_one_day_one.status_code == 200
    assert user_two_day_one.status_code == 200
    assert user_one_day_two.status_code == 200
    assert [entry["entry_id"] for entry in user_one_day_one.json()["entries"]] == [
        first.json()["logged_food_entry_id"]
    ]
    assert [entry["entry_id"] for entry in user_two_day_one.json()["entries"]] == [
        second.json()["logged_food_entry_id"]
    ]
    assert [entry["entry_id"] for entry in user_one_day_two.json()["entries"]] == [
        third.json()["logged_food_entry_id"]
    ]


def test_daily_canonical_logs_preserve_missing_and_zero_macro_snapshots(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    protein_food = create_canonical_food("Protein Only Test Food", "generic")
    create_canonical_food_nutrient(protein_food.id, "Protein", "g", 20)
    zero_food = create_canonical_food("Zero Macro Test Food", "generic")
    create_canonical_food_nutrient(zero_food.id, "Calories", "kcal", 0)
    create_canonical_food_nutrient(zero_food.id, "Protein", "g", 0)
    create_canonical_food_nutrient(zero_food.id, "Carbohydrate", "g", 0)
    create_canonical_food_nutrient(zero_food.id, "Fat", "g", 0)

    missing = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": protein_food.id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    zero = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": zero_food.id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    assert missing.status_code == 200
    assert zero.status_code == 200

    response = _client().get("/nutrition/1/canonical-logs?date=2026-06-05")

    assert response.status_code == 200
    entries = response.json()["entries"]
    assert entries[0]["calories"] is None
    assert entries[0]["protein_g"] == 20.0
    assert entries[0]["carbs_g"] is None
    assert entries[0]["fat_g"] is None
    assert entries[1]["calories"] == 0.0
    assert entries[1]["protein_g"] == 0.0
    assert entries[1]["carbs_g"] == 0.0
    assert entries[1]["fat_g"] == 0.0


def test_canonical_log_patch_updates_grams_meal_snapshots_and_totals(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()
    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
            "meal_type": "lunch",
        },
    )
    assert logged.status_code == 200
    entry_id = logged.json()["logged_food_entry_id"]

    response = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={
            "grams": 150,
            "meal_type": "snack",
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "user_id": 1,
        "entry": {
            "entry_id": entry_id,
            "canonical_food_id": canonical_food_id,
            "food_name": "Chicken Breast, Cooked, Skinless",
            "grams": 150.0,
            "meal_type": "snack",
            "calories": 247.5,
            "protein_g": 46.5,
            "carbs_g": 0.0,
            "fat_g": 5.4,
        },
    }

    entries_response = _client().get("/nutrition/1/canonical-logs?date=2026-06-05")
    assert entries_response.status_code == 200
    assert entries_response.json()["entries"] == [response.json()["entry"]]

    totals = get_daily_canonical_food_macro_totals(user_id=1, entry_date="2026-06-05")
    assert totals == {
        "entry_count": 1,
        "calories": 247.5,
        "protein_g": 46.5,
        "carbs_g": 0.0,
        "fat_g": 5.4,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 247.5
    assert actuals["logged_protein"] == 46.5
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 5.4

    conn = database.get_connection()
    canonical_row = conn.execute(
        """
        SELECT id, display_name
        FROM canonical_foods
        WHERE id = ?
        """,
        (canonical_food_id,),
    ).fetchone()
    conn.close()
    assert canonical_row["display_name"] == "Chicken Breast, Cooked, Skinless"


def test_canonical_log_patch_rejects_bad_grams_missing_and_wrong_user(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()
    logged = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
            "meal_type": "lunch",
        },
    )
    assert logged.status_code == 200
    entry_id = logged.json()["logged_food_entry_id"]

    bad_grams = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={"grams": 0, "meal_type": "snack", "entry_date": "2026-06-05"},
    )
    missing = _client().patch(
        "/nutrition/1/canonical-logs/999999",
        json={"grams": 150, "meal_type": "snack", "entry_date": "2026-06-05"},
    )
    wrong_user = _client().patch(
        f"/nutrition/2/canonical-logs/{entry_id}",
        json={"grams": 150, "meal_type": "snack", "entry_date": "2026-06-05"},
    )
    wrong_date = _client().patch(
        f"/nutrition/1/canonical-logs/{entry_id}",
        json={"grams": 150, "meal_type": "snack", "entry_date": "2026-06-06"},
    )

    assert bad_grams.status_code == 400
    assert bad_grams.json()["detail"] == "grams must be greater than 0."
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Canonical food log entry not found."
    assert wrong_user.status_code == 404
    assert wrong_user.json()["detail"] == "Canonical food log entry not found."
    assert wrong_date.status_code == 404
    assert wrong_date.json()["detail"] == "Canonical food log entry not found."

    entries_response = _client().get("/nutrition/1/canonical-logs?date=2026-06-05")
    assert entries_response.json()["entries"][0]["grams"] == 100.0
    assert entries_response.json()["entries"][0]["meal_type"] == "lunch"


def test_canonical_log_patch_preserves_missing_and_zero_macro_snapshots(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    protein_food = create_canonical_food("Protein Only Test Food", "generic")
    create_canonical_food_nutrient(protein_food.id, "Protein", "g", 20)
    zero_food = create_canonical_food("Zero Macro Test Food", "generic")
    create_canonical_food_nutrient(zero_food.id, "Calories", "kcal", 0)
    create_canonical_food_nutrient(zero_food.id, "Protein", "g", 0)
    create_canonical_food_nutrient(zero_food.id, "Carbohydrate", "g", 0)
    create_canonical_food_nutrient(zero_food.id, "Fat", "g", 0)

    missing = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": protein_food.id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    zero = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": zero_food.id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    assert missing.status_code == 200
    assert zero.status_code == 200

    updated_missing = _client().patch(
        f"/nutrition/1/canonical-logs/{missing.json()['logged_food_entry_id']}",
        json={"grams": 50, "meal_type": "other", "entry_date": "2026-06-05"},
    )
    updated_zero = _client().patch(
        f"/nutrition/1/canonical-logs/{zero.json()['logged_food_entry_id']}",
        json={"grams": 50, "meal_type": "other", "entry_date": "2026-06-05"},
    )

    assert updated_missing.status_code == 200
    assert updated_zero.status_code == 200
    assert updated_missing.json()["entry"]["calories"] is None
    assert updated_missing.json()["entry"]["protein_g"] == 10.0
    assert updated_missing.json()["entry"]["carbs_g"] is None
    assert updated_missing.json()["entry"]["fat_g"] is None
    assert updated_zero.json()["entry"]["calories"] == 0.0
    assert updated_zero.json()["entry"]["protein_g"] == 0.0
    assert updated_zero.json()["entry"]["carbs_g"] == 0.0
    assert updated_zero.json()["entry"]["fat_g"] == 0.0


def test_canonical_log_delete_removes_one_entry_and_protects_ownership(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    canonical_food_id = _seed_chicken()
    first = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
            "meal_type": "breakfast",
        },
    )
    second = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": canonical_food_id,
            "grams": 50,
            "entry_date": "2026-06-05",
            "meal_type": "snack",
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200
    first_entry_id = first.json()["logged_food_entry_id"]
    second_entry_id = second.json()["logged_food_entry_id"]

    wrong_user = _client().delete(
        f"/nutrition/2/canonical-logs/{first_entry_id}?date=2026-06-05"
    )
    missing = _client().delete("/nutrition/1/canonical-logs/999999?date=2026-06-05")
    deleted = _client().delete(
        f"/nutrition/1/canonical-logs/{first_entry_id}?date=2026-06-05"
    )

    assert wrong_user.status_code == 404
    assert wrong_user.json()["detail"] == "Canonical food log entry not found."
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Canonical food log entry not found."
    assert deleted.status_code == 200
    assert deleted.json() == {
        "success": True,
        "user_id": 1,
        "deleted": True,
        "entry_id": first_entry_id,
    }

    entries_response = _client().get("/nutrition/1/canonical-logs?date=2026-06-05")
    assert entries_response.status_code == 200
    entries = entries_response.json()["entries"]
    assert [entry["entry_id"] for entry in entries] == [second_entry_id]

    totals = get_daily_canonical_food_macro_totals(user_id=1, entry_date="2026-06-05")
    assert totals == {
        "entry_count": 1,
        "calories": 82.5,
        "protein_g": 15.5,
        "carbs_g": 0.0,
        "fat_g": 1.8,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 82.5
    assert actuals["logged_protein"] == 15.5
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 1.8

    conn = database.get_connection()
    canonical_count = conn.execute(
        "SELECT COUNT(*) AS count FROM canonical_foods WHERE id = ?",
        (canonical_food_id,),
    ).fetchone()["count"]
    conn.close()
    assert canonical_count == 1


def test_canonical_logs_endpoint_rejects_invalid_date(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/nutrition/1/canonical-logs?date=06/05/2026")

    assert response.status_code == 400
    assert response.json()["detail"] == "entry_date must use YYYY-MM-DD format."


def test_v3_daily_staple_canonical_food_can_be_logged(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()
    search_response = _client().get("/foods/canonical/search?q=ground%20turkey")
    assert search_response.status_code == 200
    turkey_id = search_response.json()["results"][0]["canonical_food_id"]

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": turkey_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Turkey, Ground 93/7"
    assert response.json()["nutrient_summary"] == {
        "calories": 150.0,
        "protein_g": 22.0,
        "carbohydrate_g": 0.0,
        "fat_g": 7.0,
    }

    target_response = _client().get("/nutrition/1/target-vs-actual?date=2026-06-05")
    assert target_response.status_code == 200
    actuals = target_response.json()["nutrition_actuals"]
    assert actuals["logged_calories"] == 150.0
    assert actuals["logged_protein"] == 22.0
    assert actuals["logged_carbs"] == 0.0
    assert actuals["logged_fat"] == 7.0
