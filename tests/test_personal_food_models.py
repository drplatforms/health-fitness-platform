from __future__ import annotations

import sqlite3

import pytest

import database
from models.personal_food_models import PersonalFoodRevisionInput
from services.personal_food_service import create_personal_food


@pytest.fixture
def personal_food_db(tmp_path, monkeypatch):
    db_path = tmp_path / "personal_food_models.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def test_personal_food_schema_initializes_idempotently(personal_food_db) -> None:
    database.initialize_database()
    conn = sqlite3.connect(personal_food_db)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(food_entries)").fetchall()
    }
    foreign_keys = {
        (row[3], row[2], row[4])
        for row in conn.execute("PRAGMA foreign_key_list(food_entries)").fetchall()
    }
    conn.close()
    assert {"personal_foods", "personal_food_revisions"} <= tables
    assert {
        "personal_food_id",
        "personal_food_revision_id",
        "food_name_snapshot",
    } <= columns
    assert {
        ("personal_food_id", "personal_foods", "id"),
        ("personal_food_revision_id", "personal_food_revisions", "id"),
    } <= foreign_keys


def test_existing_database_upgrade_adds_personal_food_provenance_foreign_keys(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "pre_milestone.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            gender TEXT,
            age INTEGER,
            height_cm REAL,
            starting_weight REAL,
            goal_weight REAL,
            primary_goal TEXT,
            activity_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            canonical_food_id INTEGER,
            grams REAL NOT NULL,
            meal_type TEXT,
            notes TEXT,
            calories REAL,
            protein_g REAL,
            carbs_g REAL,
            fat_g REAL,
            entry_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (food_id) REFERENCES foods(id)
        );
        INSERT INTO users (id, name) VALUES (77, 'Existing User');
        INSERT INTO foods (id, name) VALUES (88, 'Existing Food');
        INSERT INTO food_entries (
            id, user_id, food_id, grams, meal_type, calories, entry_date
        ) VALUES (99, 77, 88, 125, 'lunch', 250, '2026-07-01');
        """
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    database.initialize_database()

    conn = sqlite3.connect(db_path)
    existing_row = conn.execute(
        """
        SELECT id, user_id, food_id, grams, meal_type, calories, entry_date
        FROM food_entries
        WHERE id = 99
        """
    ).fetchone()
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(food_entries)").fetchall()
    }
    foreign_keys = {
        (row[3], row[2], row[4])
        for row in conn.execute("PRAGMA foreign_key_list(food_entries)").fetchall()
    }
    conn.close()

    assert existing_row == (99, 77, 88, 125, "lunch", 250, "2026-07-01")
    assert {
        "personal_food_id",
        "personal_food_revision_id",
        "food_name_snapshot",
    } <= columns
    assert {
        ("personal_food_id", "personal_foods", "id"),
        ("personal_food_revision_id", "personal_food_revisions", "id"),
    } <= foreign_keys


def test_revision_public_contract_hides_internal_legacy_identity(
    personal_food_db,
) -> None:
    food = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="Package Bread",
            input_basis="per_100g",
            calories=240,
        ),
    )
    payload = food.to_public_dict()
    assert "normalized_name" not in payload
    assert "legacy_food_id" not in payload["current_revision"]
    assert "legacy_food_id" not in str(payload)


def test_database_constraints_reject_negative_revision_nutrients(
    personal_food_db,
) -> None:
    food = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="Constraint Food",
            input_basis="per_100g",
            protein_g=0,
        ),
    )
    conn = sqlite3.connect(personal_food_db)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE personal_food_revisions SET protein_g_per_100g = -1 WHERE id = ?",
            (food.current_revision_id,),
        )
    conn.rollback()
    conn.close()
