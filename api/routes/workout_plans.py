from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.exercise_substitution_service import (
    apply_substitution,
    get_substitution_candidate_dicts,
)
from services.post_workout_review_service import (
    build_configured_post_workout_review_summary_with_metadata,
    build_post_workout_review_context,
)
from services.recovery_intelligence_v2_service import (
    build_recovery_intelligence_v2,
)
from services.user_state_service import build_user_health_state
from services.weekly_training_plan_service import (
    WeeklyTrainingPlanConflictError,
    WeeklyTrainingPlanNotFoundError,
    WeeklyTrainingPlanProtectedDateError,
    WeeklyTrainingPlanValidationError,
    create_weekly_training_plan,
    get_weekly_training_plan,
    resolve_weekly_training_context,
    update_weekly_training_plan,
)
from services.workout_daily_state_service import (
    get_current_day_execution_state,
    resolve_workout_daily_state,
)
from services.workout_plan_persistence_service import (
    WorkoutPlanInvalidStatusError,
    WorkoutPlanNotFoundError,
    WorkoutPlanValidationError,
    approved_workout_plan_from_payload,
    build_planned_vs_actual_summary,
    complete_workout_plan,
    delete_actual_set,
    get_execution_state,
    get_workout_plan_history,
    log_actual_set,
    select_approved_workout_plan,
    select_current_workout_plan,
    start_selected_workout_plan,
    update_actual_set,
)
from services.workout_plan_service import (
    build_approved_workout_plan,
    build_approved_workout_plan_for_context,
    build_configured_approved_workout_plan_with_metadata,
    build_configured_workout_explanation_with_metadata,
    build_workout_context,
    render_approved_workout_plan,
)
from services.workout_progression_decision_service import (
    CurrentExercisePrescription,
    build_workout_progression_decisions,
)
from services.workout_progression_history_service import (
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_LOOKBACK_DAYS,
    build_workout_progression_history,
)

router = APIRouter()


class ActualSetPayload(BaseModel):
    planned_workout_exercise_id: int | None = None
    exercise_name: str | None = None
    set_number: int | None = None
    actual_reps: int | None = None
    actual_weight: float | None = None
    actual_rir: int | None = None
    completed: bool = True
    skipped: bool = False
    substitution_for_planned_exercise_id: int | None = None
    notes: str | None = None


class ActualSetUpdatePayload(BaseModel):
    planned_workout_exercise_id: int | None = None
    exercise_name: str | None = None
    set_number: int | None = None
    actual_reps: int | None = None
    actual_weight: float | None = None
    actual_rir: int | None = None
    completed: bool | None = None
    skipped: bool | None = None
    substitution_for_planned_exercise_id: int | None = None
    notes: str | None = None


class ExerciseSubstitutionPayload(BaseModel):
    replacement_catalog_exercise_id: int
    substitution_reason: str | None = "user_selected"


class WorkoutPlanSelectionPayload(BaseModel):
    approved_workout_plan: dict


class WorkoutProgressionHistoryPayload(BaseModel):
    exercise_names: list[str]
    lookback_days: int = DEFAULT_LOOKBACK_DAYS
    limit: int = DEFAULT_HISTORY_LIMIT


class WorkoutProgressionDecisionExercisePayload(BaseModel):
    exercise_name: str = Field(min_length=1)
    catalog_exercise_id: int | None = None
    sets: int = Field(ge=1)
    reps_min: int = Field(ge=0)
    reps_max: int = Field(ge=0)
    rir_min: int = Field(ge=0)
    rir_max: int = Field(ge=0)


class WorkoutProgressionDecisionPayload(BaseModel):
    target_date: date
    exercises: list[WorkoutProgressionDecisionExercisePayload] = Field(min_length=1)


class WeeklyTrainingPlanCreatePayload(BaseModel):
    week_start_date: date
    training_weekdays: list[int]
    default_workout_size_preference: str = "standard"
    current_date: date | None = None


class WeeklyTrainingPlanUpdatePayload(BaseModel):
    training_weekdays: list[int]
    default_workout_size_preference: str
    current_date: date


def _raise_weekly_training_plan_http_error(exc: Exception) -> None:
    if isinstance(exc, WeeklyTrainingPlanNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, WeeklyTrainingPlanConflictError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, WeeklyTrainingPlanProtectedDateError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, WeeklyTrainingPlanValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


@router.get("/weekly-training-plans/{user_id}")
def weekly_training_plan(
    user_id: int,
    week_start_date: str,
    current_date: str | None = None,
):
    try:
        plan = get_weekly_training_plan(
            user_id,
            week_start_date,
            current_date=current_date,
        )
    except WeeklyTrainingPlanValidationError as exc:
        _raise_weekly_training_plan_http_error(exc)
    return {
        "success": True,
        "user_id": user_id,
        "week_start_date": week_start_date,
        "plan": asdict(plan) if plan else None,
    }


@router.post("/weekly-training-plans/{user_id}")
def create_weekly_training_plan_route(
    user_id: int,
    payload: WeeklyTrainingPlanCreatePayload,
):
    try:
        plan = create_weekly_training_plan(
            user_id,
            payload.week_start_date,
            payload.training_weekdays,
            payload.default_workout_size_preference,
            current_date=payload.current_date,
        )
    except (
        WeeklyTrainingPlanConflictError,
        WeeklyTrainingPlanNotFoundError,
        WeeklyTrainingPlanValidationError,
    ) as exc:
        _raise_weekly_training_plan_http_error(exc)
    return {"success": True, "user_id": user_id, "plan": asdict(plan)}


@router.patch("/weekly-training-plans/{user_id}/{weekly_plan_id}")
def update_weekly_training_plan_route(
    user_id: int,
    weekly_plan_id: int,
    payload: WeeklyTrainingPlanUpdatePayload,
):
    try:
        plan = update_weekly_training_plan(
            user_id,
            weekly_plan_id,
            payload.training_weekdays,
            payload.default_workout_size_preference,
            current_date=payload.current_date,
        )
    except (
        WeeklyTrainingPlanNotFoundError,
        WeeklyTrainingPlanProtectedDateError,
        WeeklyTrainingPlanValidationError,
    ) as exc:
        _raise_weekly_training_plan_http_error(exc)
    return {"success": True, "user_id": user_id, "plan": asdict(plan)}


@router.get("/workout-plans/current/{user_id}")
def current_workout_plan_state(user_id: int, target_date: str | None = None):
    daily_state = resolve_workout_daily_state(user_id, target_date=target_date)
    execution_state = get_current_day_execution_state(user_id, target_date=target_date)
    weekly_training_context = (
        resolve_weekly_training_context(
            user_id,
            target_date,
            current_date=target_date,
        )
        if target_date
        else {
            "has_weekly_plan": False,
            "weekly_plan_id": None,
            "weekly_plan_day_id": None,
            "day_type": None,
            "session_type": None,
            "session_title": None,
            "session_focus": None,
            "session_directive": None,
            "default_workout_size_preference": None,
            "derived_status": None,
            "is_override": False,
        }
    )

    current_execution_state = None
    if execution_state is not None:
        current_execution_state = {
            "workout_plan_instance": asdict(execution_state["workout_plan_instance"]),
            "execution_session": asdict(execution_state["execution_session"]),
            "planned_exercises": [
                asdict(exercise) for exercise in execution_state["planned_exercises"]
            ],
            "actual_sets": [
                asdict(actual_set) for actual_set in execution_state["actual_sets"]
            ],
            "active_substitutions": [
                asdict(substitution)
                for substitution in execution_state.get("active_substitutions", [])
            ],
            "approved_workout_plan": asdict(execution_state["approved_workout_plan"]),
        }

    response = {
        "success": True,
        "user_id": user_id,
        "workout_daily_state": asdict(daily_state),
        "current_execution_state": current_execution_state,
    }
    if target_date:
        response["weekly_training_context"] = weekly_training_context
    return response


@router.post("/workout-plans/{user_id}/progression-history")
def workout_progression_history(
    user_id: int,
    payload: WorkoutProgressionHistoryPayload,
):
    histories = build_workout_progression_history(
        user_id=user_id,
        planned_exercises=payload.exercise_names,
        lookback_days=payload.lookback_days,
        limit=payload.limit,
    )

    return {
        "success": True,
        "user_id": user_id,
        "lookback_days": payload.lookback_days,
        "exercise_histories": [asdict(history) for history in histories],
    }


@router.post("/workout-plans/{user_id}/progression-decisions")
def workout_progression_decisions(
    user_id: int,
    payload: WorkoutProgressionDecisionPayload,
):
    target_date = payload.target_date.isoformat()
    recovery = build_recovery_intelligence_v2(user_id, target_date)
    decisions = build_workout_progression_decisions(
        user_id=user_id,
        current_exercises=[
            CurrentExercisePrescription(
                exercise_name=exercise.exercise_name.strip(),
                catalog_exercise_id=exercise.catalog_exercise_id,
                sets=exercise.sets,
                reps_min=exercise.reps_min,
                reps_max=exercise.reps_max,
                rir_min=exercise.rir_min,
                rir_max=exercise.rir_max,
            )
            for exercise in payload.exercises
        ],
        recovery=recovery,
    )

    return {
        "success": True,
        "user_id": user_id,
        "target_date": target_date,
        "progression_decisions": [asdict(decision) for decision in decisions],
    }


@router.get("/workout-plans/history/{user_id}")
def workout_plan_history(user_id: int):
    history_items = get_workout_plan_history(user_id)

    return {
        "success": True,
        "user_id": user_id,
        "workout_plan_instances": [
            {
                "workout_plan_instance": asdict(item["workout_plan_instance"]),
                "execution_session": (
                    asdict(item["execution_session"])
                    if item["execution_session"] is not None
                    else None
                ),
                "approved_workout_title": item["approved_workout_title"],
                "approved_workout_session_focus": item[
                    "approved_workout_session_focus"
                ],
                "planned_vs_actual_summary": (
                    asdict(item["planned_vs_actual_summary"])
                    if item["planned_vs_actual_summary"] is not None
                    else None
                ),
            }
            for item in history_items
        ],
    }


@router.get("/workout-plans/preview/{user_id}")
def workout_plan_preview(
    user_id: int,
    workout_size_preference: str | None = None,
    requested_target_count: int | None = None,
    preview_variation_index: int = 0,
    target_date: str | None = None,
    train_anyway: bool = False,
):
    weekly_training_context = (
        resolve_weekly_training_context(
            user_id,
            target_date,
            current_date=target_date,
            is_override=train_anyway,
        )
        if target_date
        else {
            "has_weekly_plan": False,
            "weekly_plan_id": None,
            "weekly_plan_day_id": None,
            "day_type": None,
            "session_type": None,
            "session_title": None,
            "session_focus": None,
            "session_directive": None,
            "default_workout_size_preference": None,
            "derived_status": None,
            "is_override": train_anyway,
        }
    )
    if (
        weekly_training_context["has_weekly_plan"]
        and weekly_training_context["day_type"] == "rest"
        and not train_anyway
    ):
        return {
            "success": True,
            "user_id": user_id,
            "target_date": target_date,
            "rest_day": True,
            "weekly_training_context": weekly_training_context,
            "approved_workout_plan": None,
            "rendered_workout_plan": None,
            "workout_exercise_count": None,
        }
    effective_size = workout_size_preference
    if effective_size is None:
        weekly_size = weekly_training_context.get("default_workout_size_preference")
        effective_size = "full" if weekly_size == "extended" else weekly_size
    health_state = build_user_health_state(user_id)
    context = build_workout_context(
        health_state,
        workout_size_preference=effective_size,
        requested_target_count=requested_target_count,
        preview_variation_index=preview_variation_index,
        weekly_training_context=weekly_training_context,
    )
    approved_plan = build_approved_workout_plan_for_context(context)

    response = {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "training_constraints": asdict(context.training_constraints),
        "workout_constraints": asdict(context.workout_constraints),
        "workout_exercise_count": {
            "requested_size": context.workout_size_preference,
            "requested_count": context.requested_exercise_count,
            "final_count": len(approved_plan.exercises),
            "final_target_count": context.final_target_exercise_count,
            "reason": context.exercise_count_reason,
            "user_safe_reason": approved_plan.exercise_count_user_reason,
        },
        "approved_workout_plan": asdict(approved_plan),
        "rendered_workout_plan": render_approved_workout_plan(approved_plan),
    }
    if target_date:
        response.update(
            {
                "target_date": target_date,
                "rest_day": False,
                "weekly_training_context": weekly_training_context,
            }
        )
    return response


@router.get("/workout-plans/preview/{user_id}/debug")
def workout_plan_preview_debug(
    user_id: int,
    workout_size_preference: str = "standard",
    requested_target_count: int | None = None,
    preview_variation_index: int = 0,
):
    health_state = build_user_health_state(user_id)
    context = build_workout_context(
        health_state,
        workout_size_preference=workout_size_preference,
        requested_target_count=requested_target_count,
        preview_variation_index=preview_variation_index,
    )
    result = build_configured_approved_workout_plan_with_metadata(
        health_state,
        workout_size_preference=workout_size_preference,
        requested_target_count=requested_target_count,
        preview_variation_index=preview_variation_index,
    )
    approved_plan = result.approved_workout_plan

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "training_constraints": asdict(context.training_constraints),
        "workout_constraints": asdict(context.workout_constraints),
        "workout_exercise_count": {
            "requested_size": context.workout_size_preference,
            "requested_count": context.requested_exercise_count,
            "final_count": len(approved_plan.exercises),
            "final_target_count": context.final_target_exercise_count,
            "reason": context.exercise_count_reason,
            "user_safe_reason": approved_plan.exercise_count_user_reason,
        },
        "approved_workout_plan": asdict(approved_plan),
        "rendered_workout_plan": render_approved_workout_plan(approved_plan),
        "runtime_metadata": asdict(result.runtime_metadata),
    }


@router.get("/workout-plans/preview/{user_id}/explanation")
def workout_plan_explanation(user_id: int):
    health_state = build_user_health_state(user_id)
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)
    explanation_result = build_configured_workout_explanation_with_metadata(
        approved_plan,
        context,
    )

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "approved_workout_explanation": asdict(
            explanation_result.approved_workout_explanation
        ),
    }


@router.get("/workout-plans/preview/{user_id}/explanation/debug")
def workout_plan_explanation_debug(user_id: int):
    health_state = build_user_health_state(user_id)
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)
    explanation_result = build_configured_workout_explanation_with_metadata(
        approved_plan,
        context,
    )

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "approved_workout_plan": asdict(approved_plan),
        "approved_workout_explanation": asdict(
            explanation_result.approved_workout_explanation
        ),
        "explanation_runtime_metadata": asdict(explanation_result.runtime_metadata),
    }


@router.get("/workout-executions/{execution_id}/post-workout-summary")
def workout_execution_post_workout_summary(execution_id: int):
    try:
        review_context = build_post_workout_review_context(execution_id)
        review_result = build_configured_post_workout_review_summary_with_metadata(
            execution_id
        )
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkoutPlanInvalidStatusError, WorkoutPlanValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": review_context.user_id,
        "execution_id": review_context.execution_id,
        "plan_instance_id": review_context.plan_instance_id,
        "approved_post_workout_review_summary": asdict(
            review_result.approved_post_workout_review_summary
        ),
    }


@router.get("/workout-executions/{execution_id}/post-workout-summary/debug")
def workout_execution_post_workout_summary_debug(execution_id: int):
    try:
        review_context = build_post_workout_review_context(execution_id)
        review_result = build_configured_post_workout_review_summary_with_metadata(
            execution_id
        )
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkoutPlanInvalidStatusError, WorkoutPlanValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "user_id": review_context.user_id,
        "execution_id": review_context.execution_id,
        "plan_instance_id": review_context.plan_instance_id,
        "approved_workout_plan": asdict(review_context.approved_workout_plan),
        "planned_vs_actual_summary": asdict(review_context.planned_vs_actual_summary),
        "approved_post_workout_review_summary": asdict(
            review_result.approved_post_workout_review_summary
        ),
        "post_workout_review_runtime_metadata": asdict(review_result.runtime_metadata),
    }


@router.post("/workout-plans/{user_id}/select")
def select_workout_plan(
    user_id: int,
    workout_size_preference: str = "standard",
    requested_target_count: int | None = None,
):
    selected = select_current_workout_plan(
        user_id,
        workout_size_preference=workout_size_preference,
        requested_target_count=requested_target_count,
    )
    workout_plan_instance = selected["workout_plan_instance"]
    execution_session = selected["execution_session"]
    approved_plan = selected["approved_workout_plan"]

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "workout_plan_instance": asdict(workout_plan_instance),
        "planned_exercises": [
            asdict(exercise) for exercise in selected["planned_exercises"]
        ],
        "execution_session": asdict(execution_session),
        "approved_workout_plan": asdict(approved_plan),
    }


@router.post("/workout-plans/{user_id}/select-preview")
def select_workout_plan_preview(
    user_id: int,
    payload: WorkoutPlanSelectionPayload,
):
    try:
        approved_plan = approved_workout_plan_from_payload(
            payload.approved_workout_plan
        )
        selected = select_approved_workout_plan(user_id, approved_plan)
    except WorkoutPlanValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workout_plan_instance = selected["workout_plan_instance"]
    execution_session = selected["execution_session"]

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "workout_plan_instance": asdict(workout_plan_instance),
        "planned_exercises": [
            asdict(exercise) for exercise in selected["planned_exercises"]
        ],
        "execution_session": asdict(execution_session),
        "approved_workout_plan": asdict(approved_plan),
    }


@router.post("/workout-plans/{plan_instance_id}/start")
def start_workout_plan(plan_instance_id: int):
    try:
        started = start_selected_workout_plan(plan_instance_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanInvalidStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workout_plan_instance = started["workout_plan_instance"]
    execution_session = started["execution_session"]
    approved_plan = started["approved_workout_plan"]

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "user_id": workout_plan_instance.user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "workout_plan_instance": asdict(workout_plan_instance),
        "planned_exercises": [
            asdict(exercise) for exercise in started["planned_exercises"]
        ],
        "execution_session": asdict(execution_session),
        "approved_workout_plan": asdict(approved_plan),
    }


@router.get(
    "/workout-plans/{plan_instance_id}/planned-exercises/"
    "{planned_exercise_id}/substitution-candidates"
)
def workout_plan_substitution_candidates(
    plan_instance_id: int,
    planned_exercise_id: int,
):
    try:
        candidates = get_substitution_candidate_dicts(
            plan_instance_id,
            planned_exercise_id,
        )
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "planned_workout_exercise_id": planned_exercise_id,
        "substitution_candidates": candidates,
    }


@router.post(
    "/workout-plans/{plan_instance_id}/planned-exercises/"
    "{planned_exercise_id}/substitute"
)
def substitute_workout_plan_exercise(
    plan_instance_id: int,
    planned_exercise_id: int,
    payload: ExerciseSubstitutionPayload,
):
    try:
        result = apply_substitution(
            plan_instance_id=plan_instance_id,
            planned_exercise_id=planned_exercise_id,
            replacement_catalog_exercise_id=payload.replacement_catalog_exercise_id,
            substitution_reason=payload.substitution_reason,
        )
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkoutPlanInvalidStatusError, WorkoutPlanValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "planned_workout_exercise_id": planned_exercise_id,
        "planned_workout_exercise": asdict(result["planned_workout_exercise"]),
        "active_substitution": asdict(result["active_substitution"]),
        "previous_active_substitution_replaced": result[
            "previous_active_substitution_replaced"
        ],
        "selected_candidate": asdict(result["selected_candidate"]),
        "workout_plan_instance": asdict(result["workout_plan_instance"]),
    }


@router.get("/workout-plans/{plan_instance_id}/execution")
def workout_plan_execution_state(plan_instance_id: int):
    try:
        execution_state = get_execution_state(plan_instance_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanInvalidStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workout_plan_instance = execution_state["workout_plan_instance"]
    approved_plan = execution_state["approved_workout_plan"]

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "user_id": workout_plan_instance.user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "workout_plan_instance": asdict(workout_plan_instance),
        "execution_session": asdict(execution_state["execution_session"]),
        "planned_exercises": [
            asdict(exercise) for exercise in execution_state["planned_exercises"]
        ],
        "actual_sets": [
            asdict(actual_set) for actual_set in execution_state["actual_sets"]
        ],
        "active_substitutions": [
            asdict(substitution)
            for substitution in execution_state.get("active_substitutions", [])
        ],
        "approved_workout_plan": asdict(approved_plan),
    }


@router.post("/workout-plans/{plan_instance_id}/actual-sets")
def create_workout_plan_actual_set(
    plan_instance_id: int,
    payload: ActualSetPayload,
):
    try:
        result = log_actual_set(
            plan_instance_id,
            payload.model_dump(exclude_none=True),
        )
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkoutPlanInvalidStatusError, WorkoutPlanValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    execution_state = result["execution_state"]

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "actual_set": asdict(result["actual_set"]),
        "workout_plan_instance": asdict(execution_state["workout_plan_instance"]),
        "execution_session": asdict(execution_state["execution_session"]),
        "actual_sets": [
            asdict(actual_set) for actual_set in execution_state["actual_sets"]
        ],
    }


@router.patch("/workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}")
def update_workout_plan_actual_set(
    plan_instance_id: int,
    actual_set_id: int,
    payload: ActualSetUpdatePayload,
):
    try:
        result = update_actual_set(
            plan_instance_id,
            actual_set_id,
            payload.model_dump(exclude_unset=True),
        )
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkoutPlanInvalidStatusError, WorkoutPlanValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "actual_set": asdict(result["actual_set"]),
        "workout_plan_instance": asdict(result["workout_plan_instance"]),
        "execution_session": asdict(result["execution_session"]),
        "planned_vs_actual_summary": asdict(result["planned_vs_actual_summary"]),
    }


@router.delete("/workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}")
def delete_workout_plan_actual_set(
    plan_instance_id: int,
    actual_set_id: int,
):
    try:
        result = delete_actual_set(plan_instance_id, actual_set_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (WorkoutPlanInvalidStatusError, WorkoutPlanValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "workout_plan_instance": asdict(result["workout_plan_instance"]),
        "execution_session": asdict(result["execution_session"]),
        "actual_sets": [asdict(actual_set) for actual_set in result["actual_sets"]],
        "planned_vs_actual_summary": asdict(result["planned_vs_actual_summary"]),
    }


@router.get("/workout-plans/{plan_instance_id}/planned-vs-actual")
def workout_plan_planned_vs_actual(plan_instance_id: int):
    try:
        execution_state = get_execution_state(plan_instance_id)
        workout_plan_instance = execution_state["workout_plan_instance"]
        if workout_plan_instance.status not in {"started", "in_progress", "completed"}:
            raise WorkoutPlanInvalidStatusError(
                "Planned-vs-actual summary is available for started, "
                "in-progress, or completed workout plans. "
                f"Plan {plan_instance_id} is currently "
                f"{workout_plan_instance.status}."
            )
        summary = build_planned_vs_actual_summary(plan_instance_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanInvalidStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "workout_plan_instance": asdict(workout_plan_instance),
        "execution_session": asdict(execution_state["execution_session"]),
        "planned_vs_actual_summary": asdict(summary),
        "planned_exercises": [
            asdict(exercise) for exercise in execution_state["planned_exercises"]
        ],
        "actual_sets": [
            asdict(actual_set) for actual_set in execution_state["actual_sets"]
        ],
    }


@router.post("/workout-plans/{plan_instance_id}/complete")
def complete_workout_plan_execution(plan_instance_id: int):
    try:
        result = complete_workout_plan(plan_instance_id)
    except WorkoutPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WorkoutPlanInvalidStatusError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "workout_plan_instance_id": plan_instance_id,
        "workout_plan_instance": asdict(result["workout_plan_instance"]),
        "execution_session": asdict(result["execution_session"]),
        "planned_vs_actual_summary": asdict(result["planned_vs_actual_summary"]),
    }
