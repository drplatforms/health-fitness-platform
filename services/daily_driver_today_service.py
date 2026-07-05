from __future__ import annotations

from datetime import date

from models.daily_driver_contract_models import (
    DailyDriverCoachNote,
    DailyDriverNextAction,
    DailyDriverNutritionSummary,
    DailyDriverReadinessSummary,
    DailyDriverTodayResponse,
    DailyDriverWorkoutSummary,
)
from models.daily_next_action_models import (
    DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN,
    DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE,
    DAILY_NEXT_ACTION_LOG_FOOD,
    DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS,
    DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE,
    DAILY_NEXT_ACTION_REVIEW_WORKOUT,
)
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    TARGET_STATUS_ABOVE,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    TargetVsActualNutritionSummary,
)
from models.user_state_models import UserHealthState
from models.workout_plan_models import ApprovedWorkoutPlan
from services.daily_next_action_service import build_daily_next_action
from services.nutrition_target_vs_actual_service import (
    build_formula_derived_nutrition_targets,
    build_target_vs_actual_nutrition_summary,
)
from services.user_state_service import build_user_health_state
from services.workout_daily_state_service import resolve_workout_daily_state
from services.workout_plan_service import build_approved_workout_plan

_NO_LOGGING_STATES = {
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
}
_WORKOUT_STATUS_MAP = {
    "selected_today": "not_started",
    "active_today": "in_progress",
    "completed_today": "completed",
    "no_workout_today": "not_started",
    "expired_uncompleted_prior": "not_started",
}
_COMPLETE_LOGGING_STATES = {
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
}


def build_daily_driver_today_response(
    user_id: int,
    target_date: str | None = None,
) -> DailyDriverTodayResponse:
    action_date = target_date or date.today().isoformat()
    health_state = build_user_health_state(user_id)

    data_gaps: list[str] = []
    limitations: list[str] = []

    readiness = _build_readiness_summary(health_state, data_gaps)
    workout_plan, workout_summary = _build_workout_summary(
        user_id=user_id,
        target_date=action_date,
        health_state=health_state,
        data_gaps=data_gaps,
        limitations=limitations,
    )
    nutrition_summary = _build_nutrition_summary(
        user_id=user_id,
        target_date=action_date,
        health_state=health_state,
        data_gaps=data_gaps,
        limitations=limitations,
    )
    next_action = _build_next_action(
        user_id=user_id,
        target_date=action_date,
        workout_summary=workout_summary,
        workout_plan=workout_plan,
        nutrition_summary=nutrition_summary,
        data_gaps=data_gaps,
    )

    return DailyDriverTodayResponse(
        user_id=user_id,
        target_date=action_date,
        readiness=readiness,
        workout=workout_summary,
        nutrition=nutrition_summary,
        next_action=next_action,
        coach_note=DailyDriverCoachNote(enabled=False, text=None),
        data_gaps=_unique(data_gaps),
        limitations=_unique(limitations),
    )


def _build_readiness_summary(
    health_state: UserHealthState,
    data_gaps: list[str],
) -> DailyDriverReadinessSummary:
    recovery = health_state.recovery_state
    readiness_level = str(recovery.readiness_level or "Unknown")
    fatigue_risk = str(recovery.fatigue_risk or "Unknown")
    scenario = str(health_state.coordinator_focus or "unknown")

    if (
        readiness_level == "Unknown"
        or fatigue_risk == "Unknown"
        or recovery.recovery_score <= 0
    ):
        data_gaps.append("Recovery data is limited for this date.")
        return DailyDriverReadinessSummary(
            status="unknown",
            headline="Recovery data is limited",
            reason="Today's readiness is unclear until recovery check-in data is more complete.",
            confidence="unknown",
        )

    if (
        scenario == "recovery_limited"
        or readiness_level == "Poor"
        or fatigue_risk == "High"
    ):
        return DailyDriverReadinessSummary(
            status="recover",
            headline="Keep training controlled today",
            reason="Recovery signals suggest a lighter, lower-risk training stance today.",
            confidence="medium",
        )

    if readiness_level in {"Moderate", "Fair"} or fatigue_risk == "Moderate":
        return DailyDriverReadinessSummary(
            status="light",
            headline="Train with a controlled pace today",
            reason="Recovery signals support training, but the day should stay measured.",
            confidence="medium",
        )

    return DailyDriverReadinessSummary(
        status="ready",
        headline="Ready to train",
        reason="Recovery signals support normal training today.",
        confidence="high" if readiness_level == "High" else "medium",
    )


def _build_workout_summary(
    *,
    user_id: int,
    target_date: str,
    health_state: UserHealthState,
    data_gaps: list[str],
    limitations: list[str],
) -> tuple[ApprovedWorkoutPlan | None, DailyDriverWorkoutSummary]:
    workout_state = resolve_workout_daily_state(user_id, target_date=target_date)

    try:
        workout_plan = build_approved_workout_plan(health_state)
    except Exception:
        data_gaps.append("Today's workout plan is unavailable right now.")
        return None, DailyDriverWorkoutSummary(
            planned=False,
            workout_id=None,
            title="Workout plan unavailable",
            summary="No workout plan is available yet.",
            status="not_planned",
            first_action_label="Review today",
        )

    status = _WORKOUT_STATUS_MAP.get(workout_state.state, "unknown")
    workout_id = _resolve_workout_id(user_id, target_date, workout_state)
    if status == "in_progress":
        first_action_label = "Continue today's workout"
    elif status == "completed":
        first_action_label = "Log today's workout"
    else:
        first_action_label = "Start today's workout"

    if workout_state.stale_state_detected and workout_state.user_safe_message:
        limitations.append(workout_state.user_safe_message)

    return workout_plan, DailyDriverWorkoutSummary(
        planned=True,
        workout_id=workout_id,
        title=workout_plan.title,
        summary=f"{len(workout_plan.exercises)} exercises",
        status=status,
        first_action_label=first_action_label,
    )


def _build_nutrition_summary(
    *,
    user_id: int,
    target_date: str,
    health_state: UserHealthState,
    data_gaps: list[str],
    limitations: list[str],
) -> DailyDriverNutritionSummary:
    try:
        target_summary = build_target_vs_actual_nutrition_summary(
            user_id,
            target_date,
            health_state=health_state,
        )
        nutrition_targets, _approved_targets = build_formula_derived_nutrition_targets(
            health_state,
            calculation_date=target_date,
        )
    except Exception:
        data_gaps.append("Nutrition targets or logs are unavailable for this date.")
        return DailyDriverNutritionSummary(
            status="unknown",
            calorie_target=None,
            protein_target_g=None,
            calories_logged=None,
            protein_logged_g=None,
            today_mission="Review today's nutrition data.",
        )

    limitations.extend(target_summary.limitations[:2])
    status = _nutrition_status(target_summary)
    mission = _nutrition_mission(target_summary, status)

    calorie_target = _display_target(
        nutrition_targets.calorie_target_min,
        nutrition_targets.calorie_target_max,
    )
    protein_target = _display_target(
        nutrition_targets.protein_grams_min,
        nutrition_targets.protein_grams_max,
    )

    return DailyDriverNutritionSummary(
        status=status,
        calorie_target=calorie_target,
        protein_target_g=protein_target,
        calories_logged=_rounded_int(target_summary.nutrition_actuals.logged_calories),
        protein_logged_g=_rounded_int(target_summary.nutrition_actuals.logged_protein),
        today_mission=mission,
    )


def _build_next_action(
    *,
    user_id: int,
    target_date: str,
    workout_summary: DailyDriverWorkoutSummary,
    workout_plan: ApprovedWorkoutPlan | None,
    nutrition_summary: DailyDriverNutritionSummary,
    data_gaps: list[str],
) -> DailyDriverNextAction:
    if workout_summary.status == "in_progress":
        return DailyDriverNextAction(
            type="continue_workout",
            label="Continue today's workout",
            context=_first_exercise_context(workout_plan),
        )

    if workout_summary.status == "completed":
        if nutrition_summary.status in {"behind", "not_logged"}:
            return DailyDriverNextAction(
                type="log_meal",
                label="Log your next meal",
                context=nutrition_summary.today_mission,
            )
        return DailyDriverNextAction(
            type="done",
            label="Today's core actions are done",
            context="Workout is logged and the day has no urgent follow-up action.",
        )

    try:
        action = build_daily_next_action(user_id, target_date=target_date)
    except Exception:
        data_gaps.append("Next action was built from fallback-only data.")
        return DailyDriverNextAction(
            type="review_today",
            label="Review today",
            context="Some daily sections are limited, so start by reviewing today's available data.",
        )

    action_type = _map_next_action_type(action.action_id)
    if action_type == "start_workout":
        context = _first_exercise_context(workout_plan)
    else:
        context = action.reason.strip() or action.summary.strip()

    return DailyDriverNextAction(
        type=action_type,
        label=action.title.strip(),
        context=context,
    )


def _resolve_workout_id(user_id: int, target_date: str, workout_state) -> str:
    for candidate in (
        workout_state.active_plan_id,
        workout_state.selected_plan_id,
        workout_state.completed_workout_id,
    ):
        if candidate is not None:
            return f"plan_{candidate}"
    return f"generated_{user_id}_{target_date}"


def _display_target(
    min_value: int | float | None, max_value: int | float | None
) -> int | None:
    if min_value is None and max_value is None:
        return None
    if min_value is None:
        return int(round(max_value))
    if max_value is None:
        return int(round(min_value))
    return int(round((float(min_value) + float(max_value)) / 2.0))


def _rounded_int(value: float | None) -> int | None:
    if value is None:
        return None
    return int(round(value))


def _nutrition_status(summary: TargetVsActualNutritionSummary) -> str:
    if summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        return "not_logged"
    if summary.logging_completeness in _NO_LOGGING_STATES:
        return "behind"

    protein = summary.comparisons.get("protein")
    calories = summary.comparisons.get("calories")
    if (
        protein
        and protein.comparison_available
        and protein.target_status == TARGET_STATUS_BELOW
    ):
        return "behind"
    if (
        protein
        and protein.comparison_available
        and protein.target_status in {TARGET_STATUS_NEAR, TARGET_STATUS_ABOVE}
        and calories
        and calories.comparison_available
        and calories.target_status in {TARGET_STATUS_NEAR, TARGET_STATUS_ABOVE}
        and summary.logging_completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH
    ):
        return "complete"
    if summary.logging_completeness in _COMPLETE_LOGGING_STATES:
        return "on_track"
    return "unknown"


def _nutrition_mission(summary: TargetVsActualNutritionSummary, status: str) -> str:
    if status == "not_logged":
        return "Log your first meal so today's nutrition picture is usable."
    if status == "behind":
        protein = summary.comparisons.get("protein")
        if (
            protein
            and protein.comparison_available
            and protein.target_status == TARGET_STATUS_BELOW
        ):
            return "Get protein on track with your next meal."
        return "Log your next meal so today's totals are more reliable."
    if status == "complete":
        return "Keep logging clean and maintain today's nutrition plan."
    if status == "on_track":
        return "Stay consistent with the current nutrition pace."
    return "Review today's nutrition data."


def _map_next_action_type(action_id: str) -> str:
    mapping = {
        DAILY_NEXT_ACTION_COMPLETE_RECOVERY_CHECKIN: "review_recovery",
        DAILY_NEXT_ACTION_KEEP_TRAINING_CONSERVATIVE: "review_today",
        DAILY_NEXT_ACTION_LOG_FOOD: "log_meal",
        DAILY_NEXT_ACTION_REVIEW_NUTRITION_TARGETS: "review_today",
        DAILY_NEXT_ACTION_REVIEW_REPORT_GUIDANCE: "review_today",
        DAILY_NEXT_ACTION_REVIEW_WORKOUT: "start_workout",
    }
    return mapping.get(action_id, "unknown")


def _first_exercise_context(workout_plan: ApprovedWorkoutPlan | None) -> str:
    if workout_plan and workout_plan.exercises:
        return f"First exercise is {workout_plan.exercises[0].name}."
    return "Start with the first planned exercise."


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
