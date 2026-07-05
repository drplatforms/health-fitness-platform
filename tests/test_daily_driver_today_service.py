from __future__ import annotations

from pathlib import Path

import database
from models.daily_next_action_models import DailyNextAction
from models.nutrition_target_models import NutritionTargets
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_NO_LOGS,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    NutritionActuals,
    NutritionLoggingSummary,
    NutritionTargetComparison,
    TargetVsActualNutritionSummary,
)
from models.user_state_models import (
    UserHealthState,
    UserNutritionState,
    UserRecoveryState,
    UserTrainingState,
)
from models.workout_plan_models import ApprovedWorkoutExercise, ApprovedWorkoutPlan
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.daily_driver_today_service import build_daily_driver_today_response


def _health_state(
    *,
    user_id: int = 102,
    readiness_level: str = "High",
    fatigue_risk: str = "Low",
    recovery_score: int = 90,
    coordinator_focus: str = "aligned_managed",
) -> UserHealthState:
    return UserHealthState(
        user_id=user_id,
        user_name="QA User",
        primary_goal="strength_and_recomposition",
        recovery_state=UserRecoveryState(
            avg_sleep=7.5 if readiness_level != "Unknown" else "Unknown",
            avg_energy=8.0 if readiness_level != "Unknown" else "Unknown",
            avg_soreness=2.0 if readiness_level != "Unknown" else "Unknown",
            weight_change=0.0 if readiness_level != "Unknown" else "Unknown",
            recovery_score=recovery_score,
            fatigue_risk=fatigue_risk,
            readiness_level=readiness_level,
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
        coordinator_focus=coordinator_focus,
        latest_body_weight=190.0,
        activity_level="moderate",
    )


def _nutrition_summary(
    *,
    completeness: str = LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    protein_status: str = TARGET_STATUS_NEAR,
    calorie_status: str = TARGET_STATUS_NEAR,
) -> TargetVsActualNutritionSummary:
    actuals = NutritionActuals(
        user_id=102,
        logging_date="2026-07-04",
        logging_window="calendar_day",
        logged_calories=(
            2200.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None
        ),
        logged_protein=160.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None,
        logged_carbs=220.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None,
        logged_fat=70.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None,
        logged_meal_count=3 if completeness != LOGGING_COMPLETENESS_NO_LOGS else 0,
        entry_count=3 if completeness != LOGGING_COMPLETENESS_NO_LOGS else 0,
        source_count=3 if completeness != LOGGING_COMPLETENESS_NO_LOGS else 0,
        reason_codes=["unit_test_actuals"],
    )
    logging_summary = NutritionLoggingSummary(
        user_id=102,
        logging_date="2026-07-04",
        logging_completeness=completeness,
        confidence=(
            "High" if completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH else "Low"
        ),
        logged_meal_count=actuals.logged_meal_count,
        entry_count=actuals.entry_count,
        reason_codes=["unit_test_logging"],
        limitations=(
            []
            if completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH
            else ["Logging is limited."]
        ),
    )
    comparisons = {
        "calories": NutritionTargetComparison(
            nutrient="calories",
            actual=2200.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None,
            target_min=2100.0,
            target_max=2300.0,
            delta_min=100.0,
            delta_max=-100.0,
            percent_of_target=100.0,
            target_status=calorie_status,
            comparison_available=completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
            confidence=logging_summary.confidence,
            reason_codes=["calories"],
            limitations=[],
        ),
        "protein": NutritionTargetComparison(
            nutrient="protein",
            actual=160.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None,
            target_min=150.0,
            target_max=180.0,
            delta_min=10.0,
            delta_max=-20.0,
            percent_of_target=97.0,
            target_status=protein_status,
            comparison_available=completeness != LOGGING_COMPLETENESS_NO_LOGS,
            confidence=logging_summary.confidence,
            reason_codes=["protein"],
            limitations=[],
        ),
        "carbs": NutritionTargetComparison(
            nutrient="carbs",
            actual=220.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None,
            target_min=200.0,
            target_max=250.0,
            delta_min=20.0,
            delta_max=-30.0,
            percent_of_target=98.0,
            target_status=TARGET_STATUS_NEAR,
            comparison_available=completeness != LOGGING_COMPLETENESS_NO_LOGS,
            confidence=logging_summary.confidence,
            reason_codes=["carbs"],
            limitations=[],
        ),
        "fat": NutritionTargetComparison(
            nutrient="fat",
            actual=70.0 if completeness != LOGGING_COMPLETENESS_NO_LOGS else None,
            target_min=60.0,
            target_max=80.0,
            delta_min=10.0,
            delta_max=-10.0,
            percent_of_target=100.0,
            target_status=TARGET_STATUS_NEAR,
            comparison_available=completeness != LOGGING_COMPLETENESS_NO_LOGS,
            confidence=logging_summary.confidence,
            reason_codes=["fat"],
            limitations=[],
        ),
    }
    return TargetVsActualNutritionSummary(
        user_id=102,
        date="2026-07-04",
        nutrition_actuals=actuals,
        logging_summary=logging_summary,
        comparisons=comparisons,
        logging_completeness=completeness,
        confidence=logging_summary.confidence,
        reason_codes=["unit_test_summary"],
        limitations=list(logging_summary.limitations),
    )


def _nutrition_targets() -> tuple[NutritionTargets, object]:
    return (
        NutritionTargets(
            body_weight_lb=190.0,
            calorie_target_min=2200,
            calorie_target_max=2400,
            protein_grams_min=170,
            protein_grams_max=190,
            carbohydrate_grams_min=200,
            carbohydrate_grams_max=260,
            fat_grams_min=60,
            fat_grams_max=80,
            confidence="High",
            allow_calorie_targets=True,
            allow_protein_targets=True,
            allow_carbohydrate_targets=True,
            allow_fat_targets=True,
            nutrition_display_message="Targets are available.",
            reason_codes=["unit_test_targets"],
        ),
        object(),
    )


def _workout_plan() -> ApprovedWorkoutPlan:
    return ApprovedWorkoutPlan(
        title="Upper Body Strength",
        session_focus="Build strength",
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
                equipment_required=["dumbbell"],
            )
        ],
        warmup="Warm up",
        cooldown="Cooldown",
        progression_guidance="Progress gradually",
        rationale="It fits today",
        confidence="Moderate",
        scenario="aligned_managed",
    )


def test_service_returns_contract_sections(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_user_health_state",
        lambda user_id: _health_state(user_id=user_id),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_target_vs_actual_nutrition_summary",
        lambda user_id, target_date, health_state=None: _nutrition_summary(),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_formula_derived_nutrition_targets",
        lambda health_state, calculation_date=None: _nutrition_targets(),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_approved_workout_plan",
        lambda health_state: _workout_plan(),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.resolve_workout_daily_state",
        lambda user_id, target_date=None: type(
            "State",
            (),
            {
                "state": "selected_today",
                "selected_plan_id": 321,
                "active_plan_id": None,
                "completed_workout_id": None,
                "stale_state_detected": False,
                "user_safe_message": None,
            },
        )(),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_daily_next_action",
        lambda user_id, target_date=None: DailyNextAction(
            action_id="review_workout",
            title="Start today's workout",
            summary="Review the approved workout.",
            reason="Workout context is ready.",
            priority=4,
            workflow_target="workout_preview",
            severity="success",
            evidence={},
        ),
    )

    response = build_daily_driver_today_response(102, "2026-07-04")
    payload = response.to_dict()

    assert payload["contract_version"] == "daily_driver_today_v0"
    assert payload["user_id"] == 102
    assert payload["target_date"] == "2026-07-04"
    assert payload["readiness"]["status"] == "ready"
    assert payload["workout"]["title"] == "Upper Body Strength"
    assert payload["nutrition"]["status"] == "complete"
    assert payload["next_action"]["type"] == "start_workout"
    assert payload["coach_note"] == {"enabled": False, "text": None}
    payload_text = str(payload).lower()
    assert "provider_output" not in payload_text
    assert "source_services" not in payload_text


def test_service_produces_safe_fallback_when_data_is_sparse(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_user_health_state",
        lambda user_id: _health_state(
            user_id=user_id,
            readiness_level="Unknown",
            fatigue_risk="Unknown",
            recovery_score=0,
            coordinator_focus="data_quality_limited",
        ),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_target_vs_actual_nutrition_summary",
        lambda user_id, target_date, health_state=None: _nutrition_summary(
            completeness=LOGGING_COMPLETENESS_NO_LOGS,
            protein_status=TARGET_STATUS_BELOW,
        ),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_formula_derived_nutrition_targets",
        lambda health_state, calculation_date=None: _nutrition_targets(),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_approved_workout_plan",
        lambda health_state: _workout_plan(),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.resolve_workout_daily_state",
        lambda user_id, target_date=None: type(
            "State",
            (),
            {
                "state": "no_workout_today",
                "selected_plan_id": None,
                "active_plan_id": None,
                "completed_workout_id": None,
                "stale_state_detected": False,
                "user_safe_message": None,
            },
        )(),
    )
    monkeypatch.setattr(
        "services.daily_driver_today_service.build_daily_next_action",
        lambda user_id, target_date=None: DailyNextAction(
            action_id="complete_recovery_checkin",
            title="Complete recovery check-in",
            summary="Update recovery first.",
            reason="Recovery data is limited.",
            priority=1,
            workflow_target="today_recovery_checkin",
            severity="info",
            evidence={},
        ),
    )

    response = build_daily_driver_today_response(102, "2026-07-04")

    assert response.readiness.status == "unknown"
    assert response.nutrition.status == "not_logged"
    assert response.next_action.type == "review_recovery"
    assert response.data_gaps


def test_service_uses_route_safe_seeded_data_without_provider_calls(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    seed_qa_scenarios()

    response = build_daily_driver_today_response(102, "2026-06-20")
    payload = response.to_dict()

    assert payload["contract_version"] == "daily_driver_today_v0"
    assert payload["next_action"]["label"]
    assert payload["readiness"]["status"] in {"ready", "light", "recover", "unknown"}
    assert payload["coach_note"]["enabled"] is False
    assert "OpenAI" not in str(payload)
    assert "Ollama" not in str(payload)
    assert "CrewAI" not in str(payload)
