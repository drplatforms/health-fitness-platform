from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, timedelta

import pytest

import database
from services.workout_exercise_history_analytics_service import (
    build_workout_exercise_history_analytics,
)
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "history_analytics_test.db")
    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        [
            (1, "History Analytics User", 180.0),
            (2, "Other History User", 175.0),
        ],
    )
    conn.commit()
    conn.close()


def _timestamp(days_ago: int) -> str:
    return f"{(date.today() - timedelta(days=days_ago)).isoformat()}T18:00:00"


def _insert_plan(
    *,
    user_id: int = 1,
    days_ago: int = 1,
    exercise_name: str = "Bench Press",
    catalog_exercise_id: int | None = None,
    planned_sets: int = 3,
    actual_reps: list[int | None] | None = None,
    actual_weights: list[float | None] | None = None,
    actual_rirs: list[int | None] | None = None,
    completed_flags: list[int] | None = None,
    skipped_flags: list[int] | None = None,
    plan_status: str = "completed",
    execution_status: str = "completed",
    notes: str = "Private analytics fixture note.",
) -> tuple[int, int, int]:
    actual_reps = actual_reps if actual_reps is not None else [10] * planned_sets
    actual_weights = (
        actual_weights if actual_weights is not None else [40.0] * len(actual_reps)
    )
    actual_rirs = actual_rirs if actual_rirs is not None else [2] * len(actual_reps)
    completed_flags = completed_flags or [1] * len(actual_reps)
    skipped_flags = skipped_flags or [0] * len(actual_reps)
    completed_at = _timestamp(days_ago)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id, status, scenario, confidence, title,
            approved_workout_plan_json, selected_at, completed_at
        )
        VALUES (?, ?, 'analytics_test', 'High', 'History Session', ?, ?, ?)
        """,
        (
            user_id,
            plan_status,
            json.dumps({"title": "History Session"}),
            completed_at,
            completed_at if plan_status == "completed" else None,
        ),
    )
    plan_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO planned_workout_exercises (
            workout_plan_instance_id, exercise_order, name, sets, reps_min,
            reps_max, rir_min, rir_max, notes, equipment_required_json,
            catalog_exercise_id
        )
        VALUES (?, 1, ?, ?, 8, 12, 1, 3, '', '[]', ?)
        """,
        (plan_id, exercise_name, planned_sets, catalog_exercise_id),
    )
    planned_id = int(cursor.lastrowid)
    cursor.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id, user_id, status, started_at, completed_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            plan_id,
            user_id,
            execution_status,
            completed_at,
            completed_at if execution_status == "completed" else None,
        ),
    )
    execution_id = int(cursor.lastrowid)
    for index, reps in enumerate(actual_reps):
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
                execution_id,
                planned_id,
                exercise_name,
                index + 1,
                reps,
                actual_weights[index] if index < len(actual_weights) else None,
                actual_rirs[index] if index < len(actual_rirs) else None,
                completed_flags[index] if index < len(completed_flags) else 1,
                skipped_flags[index] if index < len(skipped_flags) else 0,
                notes,
            ),
        )
    conn.commit()
    conn.close()
    return plan_id, execution_id, planned_id


def test_no_completed_history_returns_one_safe_empty_contract(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    analytics = build_workout_exercise_history_analytics(user_id=1)

    assert analytics.overview.has_history is False
    assert analytics.overview.completed_workout_count == 0
    assert analytics.overview.completed_set_count == 0
    assert analytics.overview.distinct_effective_exercise_count == 0
    assert analytics.overview.most_recent_completed_workout_date is None
    assert analytics.exercises == []


def test_counts_only_completed_user_scoped_history_inside_lookback(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(days_ago=2)
    _insert_plan(user_id=2, days_ago=1, exercise_name="Squat")
    _insert_plan(days_ago=200, exercise_name="Barbell Row")
    _insert_plan(
        days_ago=1,
        exercise_name="Romanian Deadlift",
        plan_status="in_progress",
        execution_status="in_progress",
    )

    analytics = build_workout_exercise_history_analytics(
        user_id=1,
        lookback_days=180,
    )

    assert analytics.overview.completed_workout_count == 1
    assert analytics.overview.completed_set_count == 3
    assert analytics.overview.distinct_effective_exercise_count == 1
    assert [item.exercise_name for item in analytics.exercises] == ["Bench Press"]


def test_recent_sessions_expose_only_completed_non_skipped_set_performance(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(
        actual_reps=[12, 9, 8],
        actual_weights=[45.0, 45.0, 45.0],
        actual_rirs=[2, 1, 0],
        completed_flags=[1, 1, 0],
        skipped_flags=[0, 1, 0],
    )

    exercise = build_workout_exercise_history_analytics(user_id=1).exercises[0]

    assert exercise.recent_sessions[0].completed_set_count == 1
    assert [asdict(item) for item in exercise.recent_sessions[0].completed_sets] == [
        {
            "set_number": 1,
            "actual_reps": 12,
            "actual_weight": 45.0,
            "actual_rir": 2,
        }
    ]


def test_progression_recommendation_reuses_engine_and_stays_user_scoped(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(
        user_id=1,
        actual_reps=[10, 10, 10],
        actual_weights=[45.0, 45.0, 45.0],
        actual_rirs=[2, 2, 2],
    )
    _insert_plan(
        user_id=2,
        actual_reps=[12, 12, 12],
        actual_weights=[45.0, 45.0, 45.0],
        actual_rirs=[2, 2, 2],
    )

    recommendation = (
        build_workout_exercise_history_analytics(user_id=1)
        .exercises[0]
        .progression_recommendation
    )

    assert recommendation.decision == "increase_reps"
    assert recommendation.headline == "Increase reps"
    assert recommendation.target_guidance == "45 lb × 8–12"
    assert recommendation.evidence_session_count == 1


def test_exercises_are_recent_first_and_response_limits_do_not_change_overview(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(days_ago=5, exercise_name="Bench Press", actual_reps=[9, 9, 9])
    _insert_plan(
        days_ago=1,
        exercise_name="Dumbbell Row",
        planned_sets=2,
        actual_reps=[10, 10],
    )

    analytics = build_workout_exercise_history_analytics(
        user_id=1,
        exercise_limit=1,
        session_limit=1,
    )

    assert analytics.overview.completed_workout_count == 2
    assert analytics.overview.completed_set_count == 5
    assert analytics.overview.distinct_effective_exercise_count == 2
    assert analytics.overview.most_recent_completed_workout_date == _timestamp(1)[:10]
    assert len(analytics.exercises) == 1
    assert analytics.exercises[0].exercise_name == "Dumbbell Row"
    assert len(analytics.exercises[0].recent_sessions) == 1


def test_substitution_identity_and_name_aliases_merge_into_replacement(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(days_ago=8, exercise_name="Dumbbell Row")
    plan_id, execution_id, planned_id = _insert_plan(
        days_ago=1,
        exercise_name="Bench Press",
    )
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workout_plan_exercise_substitutions (
            workout_plan_instance_id, workout_execution_session_id,
            planned_workout_exercise_id, original_exercise_name,
            replacement_exercise_name, replacement_catalog_exercise_id,
            original_movement_pattern, replacement_movement_pattern,
            substitution_reason, status
        )
        VALUES (?, ?, ?, 'Bench Press', 'Dumbbell Row', 55, 'push', 'pull',
                'user_selected', 'active')
        """,
        (plan_id, execution_id, planned_id),
    )
    cursor.execute(
        """
        UPDATE workout_execution_set_actuals
        SET exercise_name = 'Dumbbell Row',
            planned_workout_exercise_id = NULL,
            substitution_for_planned_exercise_id = ?
        WHERE workout_execution_session_id = ?
        """,
        (planned_id, execution_id),
    )
    conn.commit()
    conn.close()

    analytics = build_workout_exercise_history_analytics(user_id=1)

    assert analytics.overview.distinct_effective_exercise_count == 1
    assert len(analytics.exercises) == 1
    exercise = analytics.exercises[0]
    assert exercise.catalog_exercise_id == 55
    assert exercise.exercise_name == "Dumbbell Row"
    assert exercise.completed_session_count == 2


def test_catalog_identity_survives_newer_untagged_name_alias(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(
        days_ago=8,
        exercise_name="Dumbbell Row",
        catalog_exercise_id=55,
    )
    _insert_plan(days_ago=1, exercise_name="Dumbbell Row")

    analytics = build_workout_exercise_history_analytics(user_id=1)

    assert analytics.overview.distinct_effective_exercise_count == 1
    assert len(analytics.exercises) == 1
    exercise = analytics.exercises[0]
    assert exercise.completed_session_count == 2
    assert exercise.catalog_exercise_id == 55


@pytest.mark.parametrize(
    ("older_weight", "latest_weight", "expected_status", "expected_change"),
    [
        (40.0, 50.0, "higher_recently", 10.0),
        (40.0, 40.0, "steady", 0.0),
        (50.0, 40.0, "lower_recently", 10.0),
    ],
)
def test_recent_working_load_trend_uses_only_comparable_sessions(
    tmp_path,
    monkeypatch,
    older_weight,
    latest_weight,
    expected_status,
    expected_change,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(days_ago=8, actual_weights=[older_weight] * 3)
    _insert_plan(days_ago=1, actual_weights=[latest_weight] * 3)

    exercise = build_workout_exercise_history_analytics(user_id=1).exercises[0]

    trend = exercise.recent_working_load_trend
    assert trend.status == expected_status
    assert trend.latest_comparable_working_weight == latest_weight
    assert trend.comparison_working_weight == older_weight
    assert trend.absolute_change_lb == expected_change
    assert trend.qualifying_session_count == 2


def test_incomplete_or_inconsistent_logging_does_not_fabricate_a_trend(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(days_ago=8, actual_weights=[40.0, 45.0, 40.0])
    _insert_plan(days_ago=1, actual_rirs=[None, None], actual_reps=[10, 10])

    exercise = build_workout_exercise_history_analytics(user_id=1).exercises[0]

    assert exercise.logging_quality == "incomplete"
    assert exercise.limitation is not None
    assert exercise.recent_working_load_trend.status == "insufficient_data"
    assert exercise.recent_working_load_trend.absolute_change_lb is None
    assert exercise.recent_sessions[0].average_actual_rir is None


def test_public_contract_excludes_raw_rows_notes_and_internal_ids(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(notes="Private note must remain internal.")

    payload = asdict(build_workout_exercise_history_analytics(user_id=1))
    serialized = json.dumps(payload).lower()

    assert "private note" not in serialized
    assert "actual_rows" not in serialized
    assert "workout_plan_instance_id" not in serialized
    assert "workout_execution_session_id" not in serialized
    assert "planned_exercise_id" not in serialized
    assert "why_this_recommendation" not in serialized
    assert "reason_codes" not in serialized
