from dataclasses import asdict

from fastapi import APIRouter

from services.user_state_service import build_user_health_state
from services.workout_plan_persistence_service import select_current_workout_plan
from services.workout_plan_service import (
    build_approved_workout_plan,
    build_workout_context,
    render_approved_workout_plan,
)

router = APIRouter()


@router.get("/workout-plans/preview/{user_id}")
def workout_plan_preview(user_id: int):
    health_state = build_user_health_state(user_id)
    context = build_workout_context(health_state)
    approved_plan = build_approved_workout_plan(health_state)

    return {
        "success": True,
        "user_id": user_id,
        "scenario": approved_plan.scenario,
        "confidence": approved_plan.confidence,
        "training_constraints": asdict(context.training_constraints),
        "workout_constraints": asdict(context.workout_constraints),
        "approved_workout_plan": asdict(approved_plan),
        "rendered_workout_plan": render_approved_workout_plan(approved_plan),
    }


@router.post("/workout-plans/{user_id}/select")
def select_workout_plan(user_id: int):
    selected = select_current_workout_plan(user_id)
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
