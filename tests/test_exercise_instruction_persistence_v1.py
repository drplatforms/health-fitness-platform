from dataclasses import fields
from pathlib import Path

import pytest

import database
from models.exercise_catalog_models import ExerciseInstruction
from services.exercise_catalog_service import (
    clear_exercise_catalog_cache,
    ensure_exercise_catalog_tables,
    get_exercise_catalog,
    get_exercise_instruction,
    seed_exercise_catalog,
    upsert_exercise_instruction,
)


@pytest.fixture(autouse=True)
def pytest_owned_database(tmp_path, monkeypatch):
    test_db = tmp_path / "fitness_ai_instruction_test.db"
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert test_db.resolve() != canonical_db.resolve()

    monkeypatch.setattr(database, "DB_PATH", test_db)
    clear_exercise_catalog_cache()
    yield test_db
    clear_exercise_catalog_cache()


def _seed_catalog():
    database.initialize_database()
    seed_exercise_catalog()
    return get_exercise_catalog()


def _instruction(catalog_exercise_id: int, *, suffix: str = ""):
    return ExerciseInstruction(
        catalog_exercise_id=catalog_exercise_id,
        overview=f"A controlled strength movement{suffix}.",
        setup_steps=["Set the bench.", "Plant both feet.", "Set the bench."],
        execution_steps=["Lower under control.", "Press to the start position."],
        form_cues=["Keep the wrists stacked.", "Maintain full-foot pressure."],
        common_mistakes=["Rushing the lowering phase.", "Lifting the heels."],
        safety_notes=["Use a load you can control.", "Stop if pain is sharp."],
    )


def _catalog_id(entries, index: int = 0) -> int:
    catalog_exercise_id = entries[index].id
    assert catalog_exercise_id is not None
    return catalog_exercise_id


def test_instruction_contract_contains_only_catalog_identity_and_instruction_fields():
    assert [field.name for field in fields(ExerciseInstruction)] == [
        "catalog_exercise_id",
        "overview",
        "setup_steps",
        "execution_steps",
        "form_cues",
        "common_mistakes",
        "safety_notes",
    ]


def test_instruction_table_uses_catalog_exercise_id_as_sole_identity():
    entries = _seed_catalog()
    catalog_exercise_id = _catalog_id(entries)
    upsert_exercise_instruction(_instruction(catalog_exercise_id))

    conn = database.get_connection()
    columns = {
        row["name"]: row
        for row in conn.execute(
            "PRAGMA table_info(exercise_catalog_instructions)"
        ).fetchall()
    }
    foreign_keys = conn.execute(
        "PRAGMA foreign_key_list(exercise_catalog_instructions)"
    ).fetchall()
    persisted_ids = conn.execute(
        "SELECT exercise_id FROM exercise_catalog_instructions"
    ).fetchall()
    conn.close()

    assert "id" not in columns
    assert columns["exercise_id"]["pk"] == 1
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["table"] == "exercise_catalog_exercises"
    assert foreign_keys[0]["from"] == "exercise_id"
    assert foreign_keys[0]["to"] == "id"
    assert [row["exercise_id"] for row in persisted_ids] == [catalog_exercise_id]


def test_complete_instruction_round_trips_ordered_lists_without_content_loss():
    entries = _seed_catalog()
    instruction = _instruction(_catalog_id(entries))

    persisted = upsert_exercise_instruction(instruction)
    loaded = get_exercise_instruction(instruction.catalog_exercise_id)

    assert persisted == instruction
    assert loaded == instruction
    assert loaded.setup_steps == [
        "Set the bench.",
        "Plant both feet.",
        "Set the bench.",
    ]


def test_upsert_replaces_same_exercise_instruction_without_duplicate_row():
    entries = _seed_catalog()
    catalog_exercise_id = _catalog_id(entries)
    upsert_exercise_instruction(_instruction(catalog_exercise_id))

    replacement = ExerciseInstruction(
        catalog_exercise_id=catalog_exercise_id,
        overview="Replacement overview.",
        setup_steps=["Replacement setup."],
        execution_steps=["Replacement execution."],
        form_cues=["Replacement cue."],
        common_mistakes=["Replacement mistake."],
        safety_notes=["Replacement safety note."],
    )
    upsert_exercise_instruction(replacement)

    conn = database.get_connection()
    row_count = conn.execute(
        "SELECT COUNT(*) AS count FROM exercise_catalog_instructions"
    ).fetchone()["count"]
    conn.close()

    assert row_count == 1
    assert get_exercise_instruction(catalog_exercise_id) == replacement


def test_multiple_exercises_have_independent_instruction_records():
    entries = _seed_catalog()
    first = _instruction(_catalog_id(entries, 0), suffix=" for the first exercise")
    second = _instruction(_catalog_id(entries, 1), suffix=" for the second exercise")

    upsert_exercise_instruction(first)
    upsert_exercise_instruction(second)

    assert get_exercise_instruction(first.catalog_exercise_id) == first
    assert get_exercise_instruction(second.catalog_exercise_id) == second


def test_catalog_exercise_without_instruction_returns_explicit_absence():
    entries = _seed_catalog()

    assert get_exercise_instruction(_catalog_id(entries)) is None


def test_nonexistent_catalog_exercise_cannot_receive_instruction():
    entries = _seed_catalog()
    nonexistent_id = max(entry.id or 0 for entry in entries) + 1_000

    with pytest.raises(
        ValueError, match=f"Catalog exercise {nonexistent_id} does not exist"
    ):
        upsert_exercise_instruction(_instruction(nonexistent_id))

    conn = database.get_connection()
    row_count = conn.execute(
        "SELECT COUNT(*) AS count FROM exercise_catalog_instructions"
    ).fetchone()["count"]
    conn.close()
    assert row_count == 0


def test_empty_instruction_lists_round_trip_safely():
    entries = _seed_catalog()
    instruction = ExerciseInstruction(
        catalog_exercise_id=_catalog_id(entries),
        overview="Overview without list details yet.",
        setup_steps=[],
        execution_steps=[],
        form_cues=[],
        common_mistakes=[],
        safety_notes=[],
    )

    upsert_exercise_instruction(instruction)

    assert get_exercise_instruction(instruction.catalog_exercise_id) == instruction


def test_existing_catalog_seeding_remains_deterministic_and_preserves_instruction():
    entries = _seed_catalog()
    catalog_exercise_id = _catalog_id(entries)
    instruction = _instruction(catalog_exercise_id)
    upsert_exercise_instruction(instruction)
    first_catalog = [
        (
            entry.id,
            entry.name,
            entry.exercise_type,
            entry.movement_pattern,
            entry.primary_muscle_groups,
            entry.equipment_required,
            entry.difficulty,
        )
        for entry in entries
    ]

    seed_exercise_catalog()
    second_catalog = [
        (
            entry.id,
            entry.name,
            entry.exercise_type,
            entry.movement_pattern,
            entry.primary_muscle_groups,
            entry.equipment_required,
            entry.difficulty,
        )
        for entry in get_exercise_catalog()
    ]

    assert second_catalog == first_catalog
    assert get_exercise_instruction(catalog_exercise_id) == instruction


def test_instruction_persistence_does_not_change_existing_catalog_records():
    entries = _seed_catalog()
    conn = database.get_connection()
    before = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM exercise_catalog_exercises ORDER BY id"
        ).fetchall()
    ]
    conn.close()

    upsert_exercise_instruction(_instruction(_catalog_id(entries)))

    conn = database.get_connection()
    after = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM exercise_catalog_exercises ORDER BY id"
        ).fetchall()
    ]
    conn.close()
    assert after == before


def test_existing_database_gains_empty_instruction_table_additively():
    database.initialize_database()
    conn = database.get_connection()
    conn.execute(
        """
        CREATE TABLE exercise_catalog_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            exercise_type TEXT NOT NULL,
            movement_pattern TEXT NOT NULL,
            primary_muscle_groups_json TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT INTO exercise_catalog_exercises (
            name,
            exercise_type,
            movement_pattern,
            primary_muscle_groups_json,
            difficulty
        )
        VALUES ('Existing Exercise', 'strength', 'push', '["chest"]', 'beginner')
        """
    )
    conn.commit()
    conn.close()

    ensure_exercise_catalog_tables()

    conn = database.get_connection()
    instruction_table = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'exercise_catalog_instructions'
        """
    ).fetchone()
    exercise = conn.execute(
        "SELECT id, name FROM exercise_catalog_exercises"
    ).fetchone()
    instruction_count = conn.execute(
        "SELECT COUNT(*) AS count FROM exercise_catalog_instructions"
    ).fetchone()["count"]
    conn.close()

    assert instruction_table["name"] == "exercise_catalog_instructions"
    assert dict(exercise) == {"id": 1, "name": "Existing Exercise"}
    assert instruction_count == 0


def test_instruction_tests_are_bound_to_pytest_owned_database(
    pytest_owned_database,
):
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"

    assert Path(database.DB_PATH).resolve() == pytest_owned_database.resolve()
    assert Path(database.DB_PATH).resolve() != canonical_db.resolve()
