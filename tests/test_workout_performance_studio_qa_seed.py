from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date

import database
from scripts.seed_workout_performance_studio_qa import (
    PERFORMANCE_STUDIO_SCENARIO,
    PERFORMANCE_STUDIO_USER_ID,
    seed_workout_performance_studio_qa,
)
from services.workout_exercise_history_analytics_service import (
    build_workout_exercise_history_analytics,
    build_workout_exercise_history_session_detail,
)


def test_performance_studio_seed_is_isolated_idempotent_and_analytics_ready(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "workout_performance_studio_qa.db",
    )
    target_date = date(2026, 7, 20)

    first = seed_workout_performance_studio_qa(end_date=target_date)
    conn = database.get_connection()
    conn.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id,
            status,
            scenario,
            confidence,
            title,
            approved_workout_plan_json
        )
        VALUES (?, 'draft', 'personal_plan', 'Moderate', 'Keep me', '{}')
        """,
        (PERFORMANCE_STUDIO_USER_ID,),
    )
    conn.commit()
    conn.close()

    second = seed_workout_performance_studio_qa(end_date=target_date)

    assert first == second
    assert second.completed_workout_count == 24
    assert second.actual_set_count == 131
    assert second.first_session_date == "2026-01-25"
    assert second.last_session_date == "2026-07-20"

    conn = database.get_connection()
    marker_plan_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM workout_plan_instances
        WHERE user_id = ? AND scenario = ?
        """,
        (PERFORMANCE_STUDIO_USER_ID, PERFORMANCE_STUDIO_SCENARIO),
    ).fetchone()[0]
    untouched_plan_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM workout_plan_instances
        WHERE user_id = ? AND scenario = 'personal_plan'
        """,
        (PERFORMANCE_STUDIO_USER_ID,),
    ).fetchone()[0]
    conn.close()
    assert marker_plan_count == 24
    assert untouched_plan_count == 1

    analytics = build_workout_exercise_history_analytics(
        user_id=PERFORMANCE_STUDIO_USER_ID,
        lookback_days=365,
        exercise_limit=12,
        session_limit=400,
        end_date=target_date.isoformat(),
        include_set_details=False,
    )
    by_name = {exercise.exercise_name: exercise for exercise in analytics.exercises}

    assert {
        name: by_name[name].modality
        for name in (
            "Dumbbell Bench Press",
            "Pull-Up",
            "Plank",
            "Farmer Carry",
            "Treadmill Walk",
        )
    } == {
        "Dumbbell Bench Press": "externally_weighted",
        "Pull-Up": "bodyweight",
        "Plank": "timed",
        "Farmer Carry": "carry",
        "Treadmill Walk": "cardio",
    }

    bench = by_name["Dumbbell Bench Press"]
    assert bench.completed_session_count == 24
    assert len(bench.recent_sessions) == 24
    assert bench.logging_quality == "incomplete"
    missing_effort_sessions = [
        session
        for session in bench.recent_sessions
        if session.average_actual_rir is None
    ]
    assert missing_effort_sessions
    assert all(
        session.performance_metric is not None for session in missing_effort_sessions
    )
    assert any(session.completed_set_count == 2 for session in bench.recent_sessions)
    assert all(not session.has_set_details for session in bench.recent_sessions)
    assert all(not session.recorded_sets for session in bench.recent_sessions)
    assert all(not session.completed_sets for session in bench.recent_sessions)

    phase_codes = {phase.code for phase in bench.historical_phase_segments}
    assert {"progression", "plateau", "deload", "rebound"} <= phase_codes
    assert all(
        phase.start_date < phase.end_date for phase in bench.historical_phase_segments
    )
    assert all(
        earlier.end_date <= later.start_date
        for earlier, later in zip(
            bench.historical_phase_segments,
            bench.historical_phase_segments[1:],
            strict=False,
        )
    )
    assert bench.current_trend is not None

    selected_session = bench.recent_sessions[0]
    detail = build_workout_exercise_history_session_detail(
        user_id=PERFORMANCE_STUDIO_USER_ID,
        session_key=selected_session.session_key,
        lookback_days=365,
        end_date=target_date.isoformat(),
    )
    assert detail is not None
    assert detail.has_set_details is True
    assert len(detail.recorded_sets) == 3
    assert len(detail.completed_sets) == 3

    public_payload = json.dumps(asdict(analytics), sort_keys=True)
    assert PERFORMANCE_STUDIO_SCENARIO not in public_payload
    assert "intended_story" not in public_payload
