from __future__ import annotations

import json

import pytest

import database
from services.workout_exercise_memory_service import (
    MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE,
    MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS,
    WorkoutExerciseMemoryConflictError,
    WorkoutExerciseMemoryNotFoundError,
    WorkoutExerciseMemoryValidationError,
    delete_workout_exercise_memory,
    ensure_workout_exercise_memory_table,
    resolve_workout_exercise_memories,
    save_workout_exercise_memory,
)
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)


def _seed_memory_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "workout_memory_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        [
            (1, "Memory User", 180.0),
            (2, "Other Memory User", 175.0),
        ],
    )
    conn.commit()
    conn.close()


def _resolve(
    user_id: int,
    exercise_name: str,
    catalog_exercise_id: int | None = None,
):
    return resolve_workout_exercise_memories(
        user_id,
        [
            {
                "catalog_exercise_id": catalog_exercise_id,
                "exercise_name": exercise_name,
            }
        ],
    )[0]


def _insert_raw_memory(
    *,
    user_id: int,
    identity_key: str,
    catalog_exercise_id: int | None,
    exercise_name: str,
    normalized_exercise_name: str,
    memory_text: str,
) -> int:
    ensure_workout_exercise_memory_table()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_exercise_memories (
            user_id, identity_key, catalog_exercise_id, exercise_name,
            normalized_exercise_name, memory_text
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            identity_key,
            catalog_exercise_id,
            exercise_name,
            normalized_exercise_name,
            memory_text,
        ),
    )
    memory_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return memory_id


def test_no_memory_returns_safe_no_memory_result(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)

    resolution = _resolve(1, "Dumbbell Row", 55)

    assert resolution.requested_catalog_exercise_id == 55
    assert resolution.requested_exercise_name == "Dumbbell Row"
    assert resolution.memory is None


def test_create_and_retrieve_catalog_backed_memory(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)

    created = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="  Rack 12.\nUse the rope attachment.  ",
    )
    resolution = _resolve(1, "Dumbbell Row", 55)

    assert created.catalog_exercise_id == 55
    assert created.memory_text == "Rack 12.\nUse the rope attachment."
    assert resolution.memory == created


def test_update_memory_preserves_one_current_row(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    created = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Rack 10.",
    )

    updated = save_workout_exercise_memory(
        1,
        memory_id=created.memory_id,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Rack 12.",
    )

    assert updated.memory_id == created.memory_id
    assert updated.memory_text == "Rack 12."
    conn = database.get_connection()
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM workout_exercise_memories WHERE user_id = 1"
    ).fetchone()["count"]
    conn.close()
    assert count == 1


def test_catalog_backed_memory_can_be_edited_through_a_name_alias(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    created = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Rack 10.",
    )
    resolution = _resolve(1, "Single-Arm Dumbbell Row", 55)

    updated = save_workout_exercise_memory(
        1,
        memory_id=resolution.memory.memory_id,
        catalog_exercise_id=55,
        exercise_name="Single-Arm Dumbbell Row",
        memory_text="Rack 12.",
    )

    assert resolution.memory.memory_id == created.memory_id
    assert updated.memory_id == created.memory_id
    assert updated.catalog_exercise_id == 55
    assert updated.exercise_name == "Single-Arm Dumbbell Row"
    assert updated.memory_text == "Rack 12."


def test_delete_memory_removes_only_selected_user_memory(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    first = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Rack 12.",
    )
    second = save_workout_exercise_memory(
        2,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Use straps.",
    )

    delete_workout_exercise_memory(1, first.memory_id)

    assert _resolve(1, "Dumbbell Row", 55).memory is None
    assert _resolve(2, "Dumbbell Row", 55).memory.memory_id == second.memory_id


def test_user_isolation_and_wrong_user_update_delete_are_safe(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    created = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="User one memory.",
    )

    assert _resolve(2, "Dumbbell Row", 55).memory is None
    with pytest.raises(WorkoutExerciseMemoryNotFoundError):
        save_workout_exercise_memory(
            2,
            memory_id=created.memory_id,
            catalog_exercise_id=55,
            exercise_name="Dumbbell Row",
            memory_text="Wrong user update.",
        )
    with pytest.raises(WorkoutExerciseMemoryNotFoundError):
        delete_workout_exercise_memory(2, created.memory_id)
    assert _resolve(1, "Dumbbell Row", 55).memory.memory_text == "User one memory."


@pytest.mark.parametrize("memory_text", ["", "   ", "\n\t"])
def test_empty_memory_text_is_rejected(tmp_path, monkeypatch, memory_text) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)

    with pytest.raises(WorkoutExerciseMemoryValidationError):
        save_workout_exercise_memory(
            1,
            catalog_exercise_id=55,
            exercise_name="Dumbbell Row",
            memory_text=memory_text,
        )


def test_over_limit_memory_text_is_rejected(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)

    with pytest.raises(WorkoutExerciseMemoryValidationError):
        save_workout_exercise_memory(
            1,
            catalog_exercise_id=55,
            exercise_name="Dumbbell Row",
            memory_text="x" * (MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS + 1),
        )


def test_batch_lookup_is_bounded_deduplicated_and_deterministic(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    saved = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Rack 12.",
    )

    resolutions = resolve_workout_exercise_memories(
        1,
        [
            {"catalog_exercise_id": 55, "exercise_name": "Dumbbell Row"},
            {"catalog_exercise_id": 55, "exercise_name": "Row alias"},
            {"catalog_exercise_id": None, "exercise_name": " Cable Crunch "},
            {"catalog_exercise_id": None, "exercise_name": "cable   crunch"},
        ],
    )

    assert len(resolutions) == 2
    assert resolutions[0].memory.memory_id == saved.memory_id
    assert resolutions[1].requested_exercise_name == "Cable Crunch"
    assert resolutions[1].memory is None

    oversized = [
        {"catalog_exercise_id": index + 1, "exercise_name": f"Exercise {index}"}
        for index in range(MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE + 1)
    ]
    with pytest.raises(WorkoutExerciseMemoryValidationError):
        resolve_workout_exercise_memories(1, oversized)


def test_exact_catalog_identity_wins_over_name_fallback(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    catalog = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Catalog memory.",
    )
    _insert_raw_memory(
        user_id=1,
        identity_key="name:dumbbell row",
        catalog_exercise_id=None,
        exercise_name="Dumbbell Row",
        normalized_exercise_name="dumbbell row",
        memory_text="Legacy name memory.",
    )

    resolution = _resolve(1, "Dumbbell Row", 55)

    assert resolution.memory.memory_id == catalog.memory_id
    assert resolution.memory.memory_text == "Catalog memory."


def test_catalog_lookup_can_use_compatible_name_only_fallback(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    legacy_id = _insert_raw_memory(
        user_id=1,
        identity_key="name:dumbbell row",
        catalog_exercise_id=None,
        exercise_name="Dumbbell Row",
        normalized_exercise_name="dumbbell row",
        memory_text="Legacy memory.",
    )

    resolution = _resolve(1, "  DUMBBELL   ROW ", 55)

    assert resolution.memory.memory_id == legacy_id
    assert resolution.memory.catalog_exercise_id is None


def test_catalog_lookup_does_not_use_ambiguous_name_only_fallback(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    _insert_raw_memory(
        user_id=1,
        identity_key="name:dumbbell row",
        catalog_exercise_id=None,
        exercise_name="Dumbbell Row",
        normalized_exercise_name="dumbbell row",
        memory_text="Legacy memory.",
    )
    _insert_raw_memory(
        user_id=1,
        identity_key="catalog:56",
        catalog_exercise_id=56,
        exercise_name="Dumbbell Row",
        normalized_exercise_name="dumbbell row",
        memory_text="Different catalog memory.",
    )

    assert _resolve(1, "Dumbbell Row", 55).memory is None


def test_name_only_lookup_prefers_exact_name_memory(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    name_id = _insert_raw_memory(
        user_id=1,
        identity_key="name:dumbbell row",
        catalog_exercise_id=None,
        exercise_name="Dumbbell Row",
        normalized_exercise_name="dumbbell row",
        memory_text="Exact name memory.",
    )
    save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Different Name",
        memory_text="Catalog memory.",
    )

    resolution = _resolve(1, "dumbbell   row")

    assert resolution.memory.memory_id == name_id


def test_name_only_lookup_resolves_exactly_one_same_name_catalog_memory(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    catalog = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Catalog memory.",
    )

    resolution = _resolve(1, "dumbbell row")

    assert resolution.memory.memory_id == catalog.memory_id


def test_ambiguous_same_name_catalog_memories_do_not_guess(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="First catalog memory.",
    )
    save_workout_exercise_memory(
        1,
        catalog_exercise_id=56,
        exercise_name="Dumbbell Row",
        memory_text="Second catalog memory.",
    )

    assert _resolve(1, "Dumbbell Row").memory is None


def test_safe_name_only_memory_promotion_uses_same_row(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    legacy = save_workout_exercise_memory(
        1,
        catalog_exercise_id=None,
        exercise_name="Dumbbell Row",
        memory_text="Legacy memory.",
    )

    promoted = save_workout_exercise_memory(
        1,
        memory_id=legacy.memory_id,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Catalog-backed memory.",
    )

    assert promoted.memory_id == legacy.memory_id
    assert promoted.catalog_exercise_id == 55
    assert _resolve(1, "Dumbbell Row", 55).memory == promoted


def test_ambiguous_selected_name_memory_is_not_promoted(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    name_id = _insert_raw_memory(
        user_id=1,
        identity_key="name:dumbbell row",
        catalog_exercise_id=None,
        exercise_name="Dumbbell Row",
        normalized_exercise_name="dumbbell row",
        memory_text="Legacy memory.",
    )
    _insert_raw_memory(
        user_id=1,
        identity_key="catalog:56",
        catalog_exercise_id=56,
        exercise_name="Dumbbell Row",
        normalized_exercise_name="dumbbell row",
        memory_text="Other catalog memory.",
    )

    with pytest.raises(WorkoutExerciseMemoryConflictError):
        save_workout_exercise_memory(
            1,
            memory_id=name_id,
            catalog_exercise_id=55,
            exercise_name="Dumbbell Row",
            memory_text="Unsafe promotion.",
        )


def test_table_ensure_is_idempotent(tmp_path, monkeypatch) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)

    ensure_workout_exercise_memory_table()
    ensure_workout_exercise_memory_table()

    conn = database.get_connection()
    table_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM sqlite_master
        WHERE type = 'table' AND name = 'workout_exercise_memories'
        """
    ).fetchone()["count"]
    conn.close()
    assert table_count == 1


def test_memory_operations_do_not_mutate_actual_set_notes_or_workout_history(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    ensure_workout_plan_persistence_tables()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id, status, scenario, confidence, title,
            approved_workout_plan_json, selected_at
        )
        VALUES (1, 'completed', 'memory_test', 'High', 'Strength', ?, '2026-07-01')
        """,
        (json.dumps({"title": "Strength"}),),
    )
    plan_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO planned_workout_exercises (
            workout_plan_instance_id, exercise_order, name, sets, reps_min,
            reps_max, rir_min, rir_max, notes, equipment_required_json
        )
        VALUES (?, 1, 'Dumbbell Row', 1, 8, 10, 2, 3, '', '[]')
        """,
        (plan_id,),
    )
    planned_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id, user_id, status, completed_at
        )
        VALUES (?, 1, 'completed', '2026-07-01')
        """,
        (plan_id,),
    )
    session_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO workout_execution_set_actuals (
            workout_execution_session_id, planned_workout_exercise_id,
            exercise_name, set_number, actual_reps, completed, notes
        )
        VALUES (?, ?, 'Dumbbell Row', 1, 10, 1, 'Keep elbows tucked.')
        """,
        (session_id, planned_id),
    )
    conn.commit()
    conn.close()

    memory = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="Rack 12.",
    )
    delete_workout_exercise_memory(1, memory.memory_id)

    conn = database.get_connection()
    actual_note = conn.execute(
        "SELECT notes FROM workout_execution_set_actuals WHERE id = 1"
    ).fetchone()["notes"]
    plan_count = conn.execute(
        "SELECT COUNT(*) AS count FROM workout_plan_instances WHERE user_id = 1"
    ).fetchone()["count"]
    conn.close()
    assert actual_note == "Keep elbows tucked."
    assert plan_count == 1
