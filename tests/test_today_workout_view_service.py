from __future__ import annotations

from types import SimpleNamespace

from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutPlan,
    PlannedWorkoutExercise,
    WorkoutExecutionSession,
    WorkoutPlanExerciseSubstitution,
    WorkoutPlanInstance,
)
from services.today_workout_view_service import build_today_workout_response


def _health_state(user_id: int = 102) -> UserHealthState:
    return UserHealthState(
        user_id=user_id,
        user_name="QA User",
        primary_goal="strength_and_recomposition",
        recovery_state=UserRecoveryState(
            avg_sleep=7.5,
            avg_energy=8.0,
            avg_soreness=2.0,
            weight_change=0.0,
            recovery_score=90,
            fatigue_risk="Low",
            readiness_level="High",
            sleep_trend="Stable",
            weight_trend="Stable",
        ),
        nutrition_state=UserNutritionState(
            nutrition_summary="Nutrition data is available.",
            has_nutrition_data=True,
            calories=2200.0,
            protein_grams=160.0,
            carbohydrate_grams=220.0,
            fat_grams=70.0,
            protein_status="Logged",
            calorie_status="Logged",
            recovery_nutrition_status="Logged",
        ),
        training_state=UserTrainingState(
            workout_summary="Workout context is available.",
            has_workout_data=True,
            workout_count=3,
            adherence_level="Moderate",
            training_trend="Stable",
            total_volume_load=12000.0,
            avg_rir=2.0,
            training_load="Moderate",
            recovery_demand="Normal",
        ),
        system_stress_level="Managed",
        nutrition_training_alignment="Aligned",
        coordinator_focus="aligned_managed",
        latest_body_weight=190.0,
        activity_level="moderate",
    )


def _approved_plan() -> ApprovedWorkoutPlan:
    return ApprovedWorkoutPlan(
        title="Upper Body Strength",
        session_focus="Upper body strength",
        duration_minutes=45,
        exercises=[
            ApprovedWorkoutExercise(
                name="Incline Dumbbell Press",
                sets=3,
                reps_min=8,
                reps_max=10,
                rir_min=2,
                rir_max=4,
                notes="Controlled reps.",
                equipment_required=["dumbbell", "bench"],
            )
        ],
        warmup="Warm up",
        cooldown="Cooldown",
        progression_guidance="Progress gradually",
        rationale="It fits today",
        confidence="Moderate",
        scenario="aligned_managed",
    )


def test_service_returns_current_execution_state_when_present(monkeypatch) -> None:
    approved_plan = _approved_plan()
    execution_state = {
        "workout_plan_instance": WorkoutPlanInstance(
            id=321,
            user_id=102,
            status="selected",
            scenario="aligned_managed",
            confidence="Moderate",
            title=approved_plan.title,
            approved_workout_plan=approved_plan,
            selected_at="2026-07-05T07:15:00",
            created_at="2026-07-05T07:15:00",
            updated_at="2026-07-05T07:15:00",
        ),
        "execution_session": WorkoutExecutionSession(
            id=55,
            workout_plan_instance_id=321,
            user_id=102,
            status="started",
            workout_session_id=None,
            started_at="2026-07-05T07:20:00",
            created_at="2026-07-05T07:20:00",
            updated_at="2026-07-05T07:20:00",
        ),
        "planned_exercises": [
            PlannedWorkoutExercise(
                id=777,
                workout_plan_instance_id=321,
                exercise_order=1,
                name="Incline Dumbbell Press",
                sets=3,
                reps_min=8,
                reps_max=10,
                rir_min=2,
                rir_max=4,
                notes="Controlled reps.",
                equipment_required=["dumbbell", "bench"],
            )
        ],
        "actual_sets": [],
        "active_substitutions": [
            WorkoutPlanExerciseSubstitution(
                id=1,
                workout_plan_instance_id=321,
                workout_execution_session_id=55,
                planned_workout_exercise_id=777,
                original_exercise_name="Incline Dumbbell Press",
                replacement_exercise_name="Machine Chest Press",
                replacement_catalog_exercise_id=90,
                original_movement_pattern="push",
                replacement_movement_pattern="push",
                substitution_reason="equipment_limit",
                status="active",
            )
        ],
        "approved_workout_plan": approved_plan,
    }

    monkeypatch.setattr(
        "services.today_workout_view_service.resolve_workout_daily_state",
        lambda user_id, target_date=None: SimpleNamespace(
            state="selected_today",
            stale_state_detected=False,
            user_safe_message=None,
        ),
    )
    monkeypatch.setattr(
        "services.today_workout_view_service.get_current_day_execution_state",
        lambda user_id, target_date=None: execution_state,
    )

    response = build_today_workout_response(102, "2026-07-05")

    assert response.status == "selected"
    assert response.source == "current_execution_state"
    assert response.workout_id == "plan_321"
    assert response.exercises[0].exercise_id == "planned_777"
    assert response.exercises[0].substitution_notes == (
        "Substitute with Machine Chest Press (equipment limit)."
    )


def test_service_returns_generated_preview_when_no_current_state(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.today_workout_view_service.resolve_workout_daily_state",
        lambda user_id, target_date=None: SimpleNamespace(
            state="no_workout_today",
            stale_state_detected=False,
            user_safe_message=None,
        ),
    )
    monkeypatch.setattr(
        "services.today_workout_view_service.get_current_day_execution_state",
        lambda user_id, target_date=None: None,
    )
    monkeypatch.setattr(
        "services.today_workout_view_service.build_user_health_state",
        lambda user_id: _health_state(user_id),
    )
    monkeypatch.setattr(
        "services.today_workout_view_service.build_approved_workout_plan",
        lambda health_state: _approved_plan(),
    )

    response = build_today_workout_response(102, "2026-07-05")

    assert response.status == "preview"
    assert response.source == "deterministic_generation"
    assert response.workout_id == "generated_102_2026-07-05"
    assert response.exercises[0].name == "Incline Dumbbell Press"
    assert response.limitations == [
        "This workout is a generated preview and is not yet selected in the workout lifecycle."
    ]


def test_service_returns_honest_empty_state_when_generation_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.today_workout_view_service.resolve_workout_daily_state",
        lambda user_id, target_date=None: SimpleNamespace(
            state="no_workout_today",
            stale_state_detected=True,
            user_safe_message="An unfinished workout from a previous day was cleared so you can start fresh today.",
        ),
    )
    monkeypatch.setattr(
        "services.today_workout_view_service.get_current_day_execution_state",
        lambda user_id, target_date=None: None,
    )
    monkeypatch.setattr(
        "services.today_workout_view_service.build_user_health_state",
        lambda user_id: _health_state(user_id),
    )
    monkeypatch.setattr(
        "services.today_workout_view_service.build_approved_workout_plan",
        lambda health_state: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = build_today_workout_response(102, "2026-07-05")

    assert response.status == "not_available"
    assert response.source == "none"
    assert response.exercises == []
    assert response.data_gaps == [
        "No planned workout was found or generated for today."
    ]
    assert response.limitations == [
        "An unfinished workout from a previous day was cleared so you can start fresh today."
    ]
