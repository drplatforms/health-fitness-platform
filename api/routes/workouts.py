# =====================================
# Imports
# =====================================

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Path

from api.models.workout_models import WorkoutRequest
from services.exercise_catalog_service import (
    get_exercise_catalog_dicts,
    get_exercise_catalog_entry_by_id,
    get_exercise_form_media,
    get_exercise_instruction,
)
from services.workout_service import (
    add_workout_set,
    create_workout_session,
    get_all_exercises,
    get_recent_workouts,
)

# =====================================
# Router Initialization
# =====================================

router = APIRouter()


# =====================================
# Recent Workouts Endpoint
# =====================================


@router.get("/workouts/{user_id}")
def recent_workouts(user_id: int):
    workouts = get_recent_workouts(user_id)

    return {"success": True, "workouts": workouts}


# =====================================
# Get Exercises Endpoint
# =====================================


@router.get("/exercises")
def get_exercises():
    exercises = get_all_exercises()

    return {
        "success": True,
        "exercises": exercises,
    }


# =====================================
# Exercise Catalog Endpoint
# =====================================


@router.get("/exercise-catalog")
def exercise_catalog():
    exercises = get_exercise_catalog_dicts()

    return {
        "success": True,
        "exercises": exercises,
    }


# =====================================
# Exercise Instruction Endpoint
# =====================================


@router.get("/exercise-catalog/{catalog_exercise_id}/instruction")
def exercise_instruction(
    catalog_exercise_id: int = Path(gt=0),
):
    exercise = get_exercise_catalog_entry_by_id(catalog_exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")

    instruction = get_exercise_instruction(catalog_exercise_id)
    if instruction is None:
        raise HTTPException(
            status_code=404,
            detail="Exercise instruction not found",
        )

    return {
        "success": True,
        "exercise": asdict(exercise),
        "instruction": asdict(instruction),
        "form_media": [
            asdict(asset) for asset in get_exercise_form_media(catalog_exercise_id)
        ],
    }


# =====================================
# Create Workout Endpoint
# =====================================


@router.post("/workouts/create")
def create_workout(payload: WorkoutRequest):
    session_id = create_workout_session(
        user_id=payload.user_id,
        workout_name=payload.workout_name,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
    )

    for set_data in payload.sets:
        add_workout_set(
            workout_session_id=session_id,
            exercise_id=set_data.exercise_id,
            set_number=set_data.set_number,
            reps=set_data.reps,
            weight=set_data.weight,
            rir=set_data.rir,
        )

    return {"success": True, "session_id": session_id}
