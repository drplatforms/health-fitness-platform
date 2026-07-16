from __future__ import annotations

from types import SimpleNamespace

import database
from services.exercise_catalog_service import (
    find_catalog_entry_by_name,
    seed_exercise_catalog,
)
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)
from services.workout_progression_decision_service import (
    CurrentExercisePrescription,
    build_exercise_progression_decision,
)
from tests.test_workout_progression_history_service import (
    _insert_completed_plan,
    _seed_test_db,
)


def _current(
    exercise_name: str = "Bench Press",
    catalog_exercise_id: int | None = None,
) -> CurrentExercisePrescription:
    return CurrentExercisePrescription(
        exercise_name=exercise_name,
        catalog_exercise_id=catalog_exercise_id,
        sets=3,
        reps_min=8,
        reps_max=12,
        rir_min=1,
        rir_max=3,
    )


def _recovery(
    readiness_classification: str = "unknown",
    fatigue_support: str = "unknown",
):
    return SimpleNamespace(
        readiness_classification=readiness_classification,
        fatigue_support=fatigue_support,
    )


def _decision(current: CurrentExercisePrescription | None = None, recovery=None):
    return build_exercise_progression_decision(
        user_id=1,
        current_exercise=current or _current(),
        recovery=recovery or _recovery(),
    )


def test_no_history_returns_insufficient_data(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    decision = _decision()

    assert decision.decision == "insufficient_data"
    assert decision.reason_codes[0] == "no_completed_history"
    assert decision.evidence_session_count == 0


def test_complete_within_range_session_progresses_reps_with_reference_weight(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        actual_reps=[10, 10, 10],
        actual_weights=[25.0, 25.0, 25.0],
        actual_rirs=[2, 2, 2],
    )

    decision = _decision()

    assert decision.decision == "progress_reps"
    assert decision.reference_weight == 25.0
    assert decision.headline == "Add reps"
    assert "Keep 25 lb" in decision.target_guidance


def test_first_top_range_session_requires_another_confirmation(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(actual_reps=[12, 12, 12], actual_rirs=[1, 1, 1])

    decision = _decision()

    assert decision.decision == "progress_reps"
    assert "latest_session_top_range_first_confirmation" in decision.reason_codes


def test_two_consecutive_top_range_sessions_increase_load(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        completed_at="2026-07-01T10:00:00",
        actual_reps=[12, 12, 12],
        actual_rirs=[1, 1, 1],
    )
    _insert_completed_plan(
        completed_at="2026-07-08T10:00:00",
        actual_reps=[12, 12, 12],
        actual_rirs=[2, 2, 2],
    )

    decision = _decision()

    assert decision.decision == "increase_load"
    assert decision.evidence_session_count == 2
    assert "next practical load" in decision.target_guidance


def test_limiting_recovery_brakes_upward_progression(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(actual_reps=[10, 10, 10], actual_rirs=[2, 2, 2])

    decision = _decision(recovery=_recovery(fatigue_support="limiting"))

    assert decision.decision == "hold"
    assert decision.recovery_brake_applied is True
    assert "recovery_limited_progression_brake" in decision.reason_codes


def test_non_limiting_recovery_does_not_brake_progression(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(actual_reps=[10, 10, 10], actual_rirs=[2, 2, 2])

    decision = _decision(
        recovery=_recovery(
            readiness_classification="mixed", fatigue_support="supportive"
        )
    )

    assert decision.decision == "progress_reps"
    assert decision.recovery_brake_applied is False


def test_one_meaningful_underperformance_session_holds(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(actual_reps=[6, 6, 8], actual_rirs=[0, 0, 2])

    decision = _decision()

    assert decision.decision == "hold"
    assert "latest_session_underperformed_once" in decision.reason_codes


def test_two_consecutive_underperformance_sessions_ease_back(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for completed_at in ("2026-07-01T10:00:00", "2026-07-08T10:00:00"):
        _insert_completed_plan(
            completed_at=completed_at,
            actual_reps=[6, 6, 8],
            actual_rirs=[0, 0, 2],
        )

    decision = _decision()

    assert decision.decision == "ease_back"
    assert "two_consecutive_underperformance_sessions" in decision.reason_codes


def test_latest_incomplete_session_blocks_older_positive_evidence(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        completed_at="2026-07-01T10:00:00",
        actual_reps=[12, 12, 12],
        actual_rirs=[2, 2, 2],
    )
    _insert_completed_plan(
        completed_at="2026-07-08T10:00:00",
        actual_reps=[12, None, 12],
        actual_rirs=[2, None, 2],
    )

    decision = _decision()

    assert decision.decision == "insufficient_data"
    assert decision.reason_codes[0] == "latest_history_incomplete"


def test_incomplete_second_session_prevents_two_session_rule_only(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        completed_at="2026-07-01T10:00:00",
        actual_reps=[12, None, 12],
        actual_rirs=[2, None, 2],
    )
    _insert_completed_plan(
        completed_at="2026-07-08T10:00:00",
        actual_reps=[12, 12, 12],
        actual_rirs=[2, 2, 2],
    )

    decision = _decision()

    assert decision.decision == "progress_reps"
    assert "latest_session_top_range_first_confirmation" in decision.reason_codes


def test_extra_sets_and_varied_weight_do_not_block_rep_progression(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        sets=3,
        actual_reps=[10, 10, 10, None],
        actual_weights=[20.0, 25.0, 20.0, None],
        actual_rirs=[2, 2, 2, None],
        completed_flags=[1, 1, 1, 0],
    )

    decision = _decision()

    assert decision.decision == "progress_reps"
    assert decision.reference_weight is None
    assert "Keep the load or resistance similar" in decision.target_guidance


def test_substitution_history_uses_replacement_identity_and_original_prescription(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    plan_id = _insert_completed_plan(
        exercise_name="Bench Press",
        actual_reps=[10, 10, 10],
        actual_rirs=[2, 2, 2],
    )
    seed_exercise_catalog()
    ensure_workout_plan_persistence_tables()
    replacement = find_catalog_entry_by_name("Dumbbell Row")
    assert replacement is not None
    assert replacement.id is not None

    conn = database.get_connection()
    cursor = conn.cursor()
    planned = cursor.execute(
        "SELECT id FROM planned_workout_exercises WHERE workout_plan_instance_id = ?",
        (plan_id,),
    ).fetchone()
    execution = cursor.execute(
        "SELECT id FROM workout_execution_sessions WHERE workout_plan_instance_id = ?",
        (plan_id,),
    ).fetchone()
    assert planned is not None
    assert execution is not None
    planned_id = int(planned["id"])
    cursor.execute(
        """
        INSERT INTO workout_plan_exercise_substitutions (
            workout_plan_instance_id, workout_execution_session_id,
            planned_workout_exercise_id, original_exercise_name,
            replacement_exercise_name, replacement_catalog_exercise_id,
            original_movement_pattern, replacement_movement_pattern,
            substitution_reason, status
        )
        VALUES (?, ?, ?, 'Bench Press', 'Dumbbell Row', ?, 'push', 'pull',
                'user_selected', 'active')
        """,
        (plan_id, int(execution["id"]), planned_id, replacement.id),
    )
    cursor.execute(
        """
        UPDATE workout_execution_set_actuals
        SET planned_workout_exercise_id = NULL,
            substitution_for_planned_exercise_id = ?,
            exercise_name = 'Dumbbell Row'
        WHERE workout_execution_session_id = ?
        """,
        (planned_id, int(execution["id"])),
    )
    conn.commit()
    conn.close()

    decision = _decision(_current("Dumbbell Row", replacement.id))

    assert decision.decision == "progress_reps"
    assert decision.exercise_name == "Dumbbell Row"
    assert decision.catalog_exercise_id == replacement.id


def test_inactive_substitution_does_not_replace_planned_exercise_identity(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    plan_id = _insert_completed_plan(
        exercise_name="Bench Press",
        actual_reps=[9, 9, 9],
        actual_rirs=[2, 2, 2],
    )
    seed_exercise_catalog()
    ensure_workout_plan_persistence_tables()
    replacement = find_catalog_entry_by_name("Dumbbell Row")
    assert replacement is not None
    assert replacement.id is not None

    conn = database.get_connection()
    cursor = conn.cursor()
    planned = cursor.execute(
        "SELECT id FROM planned_workout_exercises WHERE workout_plan_instance_id = ?",
        (plan_id,),
    ).fetchone()
    execution = cursor.execute(
        "SELECT id FROM workout_execution_sessions WHERE workout_plan_instance_id = ?",
        (plan_id,),
    ).fetchone()
    assert planned is not None
    assert execution is not None
    cursor.execute(
        """
        INSERT INTO workout_plan_exercise_substitutions (
            workout_plan_instance_id, workout_execution_session_id,
            planned_workout_exercise_id, original_exercise_name,
            replacement_exercise_name, replacement_catalog_exercise_id,
            original_movement_pattern, replacement_movement_pattern,
            substitution_reason, status
        )
        VALUES (?, ?, ?, 'Bench Press', 'Dumbbell Row', ?, 'push', 'pull',
                'user_selected', 'cancelled')
        """,
        (plan_id, int(execution["id"]), int(planned["id"]), replacement.id),
    )
    conn.commit()
    conn.close()

    decision = _decision(_current("Bench Press"))

    assert decision.decision == "progress_reps"
    assert decision.exercise_name == "Bench Press"
