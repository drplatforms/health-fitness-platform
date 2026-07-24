from __future__ import annotations

import json
from dataclasses import asdict

import database
from scripts.seed_realistic_longitudinal_qa_v2 import (
    HISTORY_END,
    PERSONA_BY_ID,
)
from scripts.seed_workout_performance_studio_qa import (
    PERFORMANCE_STUDIO_SCENARIO,
    PERFORMANCE_STUDIO_USER_ID,
    seed_workout_performance_studio_qa,
)
from services.workout_exercise_history_analytics_service import (
    build_workout_exercise_history_analytics,
    build_workout_exercise_history_session_detail,
)


def test_performance_studio_compatibility_delegates_to_canonical_qa106(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "workout_performance_studio_qa.db",
    )

    first = seed_workout_performance_studio_qa()
    second = seed_workout_performance_studio_qa()

    assert first == second
    assert second.completed_workout_count == 87
    assert second.actual_set_count == 494
    assert second.first_session_date == "2026-02-06"
    assert second.last_session_date == "2026-07-22"

    conn = database.get_connection()
    user = conn.execute(
        "SELECT name FROM users WHERE id = ?",
        (PERFORMANCE_STUDIO_USER_ID,),
    ).fetchone()
    v2_plan_count = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM workout_plan_instances
            WHERE user_id = ? AND scenario = ?
            """,
            (PERFORMANCE_STUDIO_USER_ID, PERSONA_BY_ID[106].scenario),
        ).fetchone()[0]
    )
    legacy_plan_count = int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM workout_plan_instances
            WHERE user_id = ? AND scenario = ?
            """,
            (PERFORMANCE_STUDIO_USER_ID, PERFORMANCE_STUDIO_SCENARIO),
        ).fetchone()[0]
    )
    conn.close()
    assert user["name"] == PERSONA_BY_ID[106].name
    assert v2_plan_count == 87
    assert legacy_plan_count == 0

    analytics = build_workout_exercise_history_analytics(
        user_id=PERFORMANCE_STUDIO_USER_ID,
        lookback_days=365,
        exercise_limit=12,
        session_limit=400,
        end_date=HISTORY_END.isoformat(),
        include_set_details=False,
    )
    by_name = {exercise.exercise_name: exercise for exercise in analytics.exercises}

    assert {
        name: by_name[name].modality
        for name in (
            "Dumbbell Bench Press",
            "Pull-Up",
            "Plank",
        )
    } == {
        "Dumbbell Bench Press": "externally_weighted",
        "Pull-Up": "bodyweight",
        "Plank": "timed",
    }

    bench = by_name["Dumbbell Bench Press"]
    assert bench.completed_session_count >= 35
    assert bench.logging_quality == "incomplete"
    assert any(session.average_actual_rir is None for session in bench.recent_sessions)
    assert any(session.completed_set_count < 3 for session in bench.recent_sessions)
    bench_loads = [
        session.performance_metric.value
        for session in reversed(bench.recent_sessions)
        if session.performance_metric is not None
    ]
    adjacent_loads = list(zip(bench_loads, bench_loads[1:], strict=False))
    assert all(load % 2.5 == 0 for load in bench_loads)
    assert any(current == previous for previous, current in adjacent_loads)
    assert any(current < previous for previous, current in adjacent_loads)
    assert any(current > previous for previous, current in adjacent_loads)

    phase_codes = {phase.code for phase in bench.historical_phase_segments}
    assert {"plateau", "deload", "rebound"} <= phase_codes

    selected_session = next(
        session for session in bench.recent_sessions if session.completed_set_count == 3
    )
    detail = build_workout_exercise_history_session_detail(
        user_id=PERFORMANCE_STUDIO_USER_ID,
        session_key=selected_session.session_key,
        lookback_days=365,
        end_date=HISTORY_END.isoformat(),
    )
    assert detail is not None
    assert detail.has_set_details is True
    assert len(detail.recorded_sets) == 3

    public_payload = json.dumps(asdict(analytics), sort_keys=True)
    assert PERFORMANCE_STUDIO_SCENARIO not in public_payload
    assert "intended_story" not in public_payload
