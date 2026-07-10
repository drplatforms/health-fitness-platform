from __future__ import annotations

import json

import database
from services.workout_progression_history_service import (
    build_exercise_history_summary,
    build_workout_progression_history,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        (1, "Progression User", 190.0),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        (2, "Other Progression User", 180.0),
    )
    conn.commit()
    conn.close()


def _insert_completed_plan(
    *,
    user_id: int = 1,
    completed_at: str = "2026-07-01T10:00:00",
    exercise_name: str = "Bench Press",
    sets: int = 3,
    actual_reps: list[int | None] | None = None,
    actual_weights: list[float | None] | None = None,
    actual_rirs: list[int | None] | None = None,
    completed_flags: list[int] | None = None,
    skipped_flags: list[int] | None = None,
    notes: str | None = "Private note should never be public.",
    status: str = "completed",
    execution_status: str = "completed",
) -> int:
    actual_reps = actual_reps if actual_reps is not None else [10] * sets
    actual_weights = (
        actual_weights if actual_weights is not None else [25.0] * len(actual_reps)
    )
    actual_rirs = actual_rirs if actual_rirs is not None else [2] * len(actual_reps)
    completed_flags = (
        completed_flags if completed_flags is not None else [1] * len(actual_reps)
    )
    skipped_flags = (
        skipped_flags if skipped_flags is not None else [0] * len(actual_reps)
    )

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id, status, scenario, confidence, title,
            approved_workout_plan_json, selected_at
        )
        VALUES (?, ?, 'unit_test', 'High', ?, ?, ?)
        """,
        (
            user_id,
            status,
            "Strength Day",
            json.dumps({"title": "Strength Day"}),
            completed_at,
        ),
    )
    plan_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO planned_workout_exercises (
            workout_plan_instance_id, exercise_order, name, sets, reps_min,
            reps_max, rir_min, rir_max, notes, equipment_required_json
        )
        VALUES (?, 1, ?, ?, 8, 12, 1, 3, '', '[]')
        """,
        (plan_id, exercise_name, sets),
    )
    planned_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id, user_id, status, completed_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            plan_id,
            user_id,
            execution_status,
            completed_at if execution_status == "completed" else None,
        ),
    )
    session_id = int(cursor.lastrowid)
    for index, reps in enumerate(actual_reps, start=1):
        cursor.execute(
            """
            INSERT INTO workout_execution_set_actuals (
                workout_execution_session_id, planned_workout_exercise_id,
                exercise_name, set_number, planned_reps_min, planned_reps_max,
                planned_rir_min, planned_rir_max, actual_reps, actual_weight,
                actual_rir, completed, skipped, notes
            )
            VALUES (?, ?, ?, ?, 8, 12, 1, 3, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                planned_id,
                exercise_name,
                index,
                reps,
                actual_weights[index - 1] if index - 1 < len(actual_weights) else None,
                actual_rirs[index - 1] if index - 1 < len(actual_rirs) else None,
                completed_flags[index - 1] if index - 1 < len(completed_flags) else 1,
                skipped_flags[index - 1] if index - 1 < len(skipped_flags) else 0,
                notes,
            ),
        )
    conn.commit()
    conn.close()
    return plan_id


def test_no_completed_workouts_returns_no_history(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_exercise_history_summary(1, "Bench Press")

    assert summary.has_history is False
    assert summary.completed_session_count == 0
    assert summary.message == "No recent history for this exercise yet."


def test_completed_prior_workout_returns_last_session_summary(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        exercise_name="Bench Press",
        actual_reps=[10, 10, 10],
        actual_weights=[25.0, 25.0, 25.0],
        actual_rirs=[2, 2, 2],
    )

    summary = build_exercise_history_summary(1, "Bench Press")

    assert summary.has_history is True
    assert summary.completed_session_count == 1
    assert summary.last_performed_at == "2026-07-01"
    assert summary.last_session_summary == "3x10, @ 25 lb, RIR 2"
    assert summary.logging_quality == "complete"


def test_multiple_prior_workouts_return_most_recent_session(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(completed_at="2026-06-20T10:00:00", actual_reps=[8, 8, 8])
    _insert_completed_plan(completed_at="2026-07-02T10:00:00", actual_reps=[11, 11, 11])

    summary = build_exercise_history_summary(1, "Bench Press")

    assert summary.completed_session_count == 2
    assert summary.last_performed_at == "2026-07-02"
    assert summary.last_session_summary.startswith("3x11")


def test_recent_best_set_is_calculated_safely(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        exercise_name="Dumbbell Row",
        actual_reps=[8, 12, 10],
        actual_weights=[40.0, 35.0, 45.0],
        actual_rirs=[3, 2, 2],
    )

    summary = build_exercise_history_summary(1, "Dumbbell Row")

    assert summary.recent_best_set is not None
    assert summary.recent_best_set.actual_reps == 12
    assert summary.recent_best_set.summary == "12 reps @ 35 lb RIR 2"


def test_incomplete_set_logging_returns_limited_quality(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        actual_reps=[10, None],
        actual_weights=[25.0, None],
        actual_rirs=[2, None],
        completed_flags=[1, 1],
        sets=3,
    )

    summary = build_exercise_history_summary(1, "Bench Press")

    assert summary.has_history is True
    assert summary.logging_quality == "incomplete"
    assert summary.message == (
        "Recent history is limited because prior set logging is incomplete."
    )


def test_different_user_data_is_not_included(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(user_id=2, exercise_name="Bench Press")

    summary = build_exercise_history_summary(1, "Bench Press")

    assert summary.has_history is False
    assert summary.completed_session_count == 0


def test_non_completed_plans_are_not_used(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(status="in_progress", execution_status="in_progress")

    summary = build_exercise_history_summary(1, "Bench Press")

    assert summary.has_history is False


def test_exercise_with_no_matching_history_does_not_crash(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(exercise_name="Bench Press")

    summary = build_exercise_history_summary(1, "Squat")

    assert summary.exercise_name == "Squat"
    assert summary.has_history is False


def test_response_is_bounded_by_limit_and_deduplicates_requested_names(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for day in range(1, 5):
        _insert_completed_plan(completed_at=f"2026-07-0{day}T10:00:00")

    histories = build_workout_progression_history(
        user_id=1,
        planned_exercises=["Bench Press", {"name": "Bench Press"}, "Squat"],
        limit=2,
    )

    assert [history.exercise_name for history in histories] == ["Bench Press", "Squat"]
    assert histories[0].completed_session_count == 2
    assert histories[0].last_performed_at == "2026-07-04"
