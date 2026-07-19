from __future__ import annotations

from datetime import date

from models.today_workout_view_models import (
    TodayWorkoutExerciseItem,
    TodayWorkoutResponse,
)
from models.workout_plan_models import ApprovedWorkoutPlan
from services.user_state_service import build_user_health_state
from services.workout_daily_state_service import (
    get_current_day_execution_state,
    resolve_workout_daily_state,
)
from services.workout_plan_service import build_approved_workout_plan

_STATUS_MAP = {
    "selected_today": "selected",
    "active_today": "in_progress",
    "completed_today": "completed",
}


def build_today_workout_response(
    user_id: int,
    target_date: str | None = None,
) -> TodayWorkoutResponse:
    action_date = target_date or date.today().isoformat()
    data_gaps: list[str] = []
    limitations: list[str] = []

    workout_state = resolve_workout_daily_state(user_id, target_date=action_date)
    if workout_state.stale_state_detected and workout_state.user_safe_message:
        limitations.append(workout_state.user_safe_message)

    execution_state = get_current_day_execution_state(user_id, target_date=action_date)
    if execution_state is not None:
        return _build_persisted_workout_response(
            user_id=user_id,
            target_date=action_date,
            execution_state=execution_state,
            workout_state=workout_state,
            data_gaps=data_gaps,
            limitations=limitations,
        )

    try:
        health_state = build_user_health_state(user_id)
        approved_plan = build_approved_workout_plan(health_state)
    except Exception:
        data_gaps.append("No planned workout was found or generated for today.")
        return TodayWorkoutResponse(
            user_id=user_id,
            target_date=action_date,
            status="not_available",
            title="No workout available",
            summary="No planned workout is available for this date.",
            source="none",
            workout_id=None,
            generated_at=None,
            estimated_duration_minutes=None,
            focus=None,
            equipment=[],
            exercises=[],
            data_gaps=_unique(data_gaps),
            limitations=_unique(limitations),
        )

    limitations.append(
        "This workout is a generated preview and is not yet selected in the workout lifecycle."
    )
    return _build_generated_workout_response(
        user_id=user_id,
        target_date=action_date,
        approved_plan=approved_plan,
        data_gaps=data_gaps,
        limitations=limitations,
    )


def _build_persisted_workout_response(
    *,
    user_id: int,
    target_date: str,
    execution_state: dict,
    workout_state,
    data_gaps: list[str],
    limitations: list[str],
) -> TodayWorkoutResponse:
    workout_plan_instance = execution_state["workout_plan_instance"]
    approved_plan = execution_state["approved_workout_plan"]
    planned_exercises = execution_state.get("planned_exercises", [])
    substitutions = execution_state.get("active_substitutions", [])

    substitution_by_planned_id = {
        substitution.planned_workout_exercise_id: substitution
        for substitution in substitutions
    }
    exercises = [
        TodayWorkoutExerciseItem(
            exercise_id=f"planned_{exercise.id}",
            name=exercise.name,
            order=exercise.exercise_order,
            section="Main Session",
            sets=exercise.sets,
            reps=(
                _format_rep_range(exercise.reps_min, exercise.reps_max)
                if exercise.measurement_type == "reps"
                else None
            ),
            weight=None,
            weight_unit=None,
            rest_seconds=None,
            tempo=None,
            notes=exercise.notes or None,
            substitution_notes=_substitution_note(
                substitution_by_planned_id.get(exercise.id)
            ),
            measurement_type=exercise.measurement_type,
            target_duration_seconds=exercise.target_duration_seconds,
            target_distance_meters=exercise.target_distance_meters,
        )
        for exercise in planned_exercises
    ]

    if not exercises:
        data_gaps.append("Planned exercise details are unavailable for this workout.")

    return TodayWorkoutResponse(
        user_id=user_id,
        target_date=target_date,
        status=_STATUS_MAP.get(workout_state.state, "selected"),
        title=approved_plan.title,
        summary=_build_summary(approved_plan, len(exercises)),
        source="current_execution_state",
        workout_id=f"plan_{workout_plan_instance.id}",
        generated_at=workout_plan_instance.selected_at
        or workout_plan_instance.created_at,
        estimated_duration_minutes=approved_plan.duration_minutes,
        focus=approved_plan.session_focus,
        equipment=_collect_equipment_from_persisted(execution_state),
        exercises=exercises,
        data_gaps=_unique(data_gaps),
        limitations=_unique(limitations),
    )


def _build_generated_workout_response(
    *,
    user_id: int,
    target_date: str,
    approved_plan: ApprovedWorkoutPlan,
    data_gaps: list[str],
    limitations: list[str],
) -> TodayWorkoutResponse:
    exercises = [
        TodayWorkoutExerciseItem(
            exercise_id=None,
            name=exercise.name,
            order=index,
            section="Main Session",
            sets=exercise.sets,
            reps=(
                _format_rep_range(exercise.reps_min, exercise.reps_max)
                if exercise.measurement_type == "reps"
                else None
            ),
            weight=None,
            weight_unit=None,
            rest_seconds=None,
            tempo=None,
            notes=exercise.notes or None,
            substitution_notes=None,
            measurement_type=exercise.measurement_type,
            target_duration_seconds=exercise.target_duration_seconds,
            target_distance_meters=exercise.target_distance_meters,
        )
        for index, exercise in enumerate(approved_plan.exercises, start=1)
    ]

    if not exercises:
        data_gaps.append("No exercises are available in the generated workout preview.")

    return TodayWorkoutResponse(
        user_id=user_id,
        target_date=target_date,
        status="preview",
        title=approved_plan.title,
        summary=_build_summary(approved_plan, len(exercises)),
        source="deterministic_generation",
        workout_id=f"generated_{user_id}_{target_date}",
        generated_at=None,
        estimated_duration_minutes=approved_plan.duration_minutes,
        focus=approved_plan.session_focus,
        equipment=_collect_equipment_from_plan(approved_plan),
        exercises=exercises,
        data_gaps=_unique(data_gaps),
        limitations=_unique(limitations),
    )


def _collect_equipment_from_persisted(execution_state: dict) -> list[str]:
    equipment: list[str] = []
    for exercise in execution_state.get("planned_exercises", []):
        for item in exercise.equipment_required:
            equipment.append(str(item))
    return _unique(equipment)


def _collect_equipment_from_plan(approved_plan: ApprovedWorkoutPlan) -> list[str]:
    equipment: list[str] = []
    for exercise in approved_plan.exercises:
        for item in exercise.equipment_required:
            equipment.append(str(item))
    return _unique(equipment)


def _build_summary(approved_plan: ApprovedWorkoutPlan, exercise_count: int) -> str:
    focus = approved_plan.session_focus.strip().rstrip(".")
    if focus:
        return f"{exercise_count} planned exercises focused on {focus.lower()}."
    return f"{exercise_count} planned exercises."


def _format_rep_range(reps_min: int | None, reps_max: int | None) -> str | None:
    if reps_min is None and reps_max is None:
        return None
    if reps_min is None:
        return str(reps_max)
    if reps_max is None or reps_min == reps_max:
        return str(reps_min)
    return f"{reps_min}-{reps_max}"


def _substitution_note(substitution) -> str | None:
    if substitution is None:
        return None
    return (
        f"Substitute with {substitution.replacement_exercise_name} "
        f"({substitution.substitution_reason.replace('_', ' ')})."
    )


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
