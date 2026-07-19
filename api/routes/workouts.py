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
    get_exercise_protocol_metadata,
    get_exercise_protocol_template,
    get_exercise_taxonomy,
)
from services.exercise_visual_media_service import resolve_exercise_visual_media
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

    visual_media = resolve_exercise_visual_media(catalog_exercise_id)

    return {
        "success": True,
        "exercise": asdict(exercise),
        "instruction": asdict(instruction),
        # Retained for local-media response compatibility.  New consumers use
        # the provider-neutral normalized contract below.
        "form_media": [
            asdict(asset) for asset in get_exercise_form_media(catalog_exercise_id)
        ],
        "visual_media": [asdict(item) for item in visual_media.media],
        "visual_media_resolution": asdict(visual_media.resolution),
    }


@router.get("/exercise-catalog/{catalog_exercise_id}/taxonomy")
def exercise_taxonomy(catalog_exercise_id: int = Path(gt=0)):
    exercise = get_exercise_catalog_entry_by_id(catalog_exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    taxonomy = get_exercise_taxonomy(catalog_exercise_id)
    if taxonomy is None:
        raise HTTPException(status_code=404, detail="Exercise taxonomy not found")
    fields = (
        "body_position",
        "support_type",
        "bench_angle",
        "laterality",
        "grip",
        "stance",
        "load_position",
        "attachment",
        "movement_direction",
        "locomotion_mode",
        "execution_mode",
    )
    result = {
        "family": taxonomy.family_slug,
        "base_movement": taxonomy.base_movement_slug,
        "visual_identity": taxonomy.visual_identity_slug,
        "status": taxonomy.taxonomy_status,
        "variants": {
            field: getattr(taxonomy, field)
            for field in fields
            if getattr(taxonomy, field) is not None
        },
    }
    if taxonomy.variant_extensions:
        result["extensions"] = taxonomy.variant_extensions
    return {"success": True, "exercise": asdict(exercise), "taxonomy": result}


@router.get("/exercise-catalog/{catalog_exercise_id}/protocol")
def exercise_protocol(catalog_exercise_id: int = Path(gt=0)):
    exercise = get_exercise_catalog_entry_by_id(catalog_exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    metadata = get_exercise_protocol_metadata(catalog_exercise_id)
    protocol = (
        None
        if metadata is None
        else get_exercise_protocol_template(metadata.protocol_slug)
    )
    if metadata is not None and protocol is None:
        raise RuntimeError("Persisted exercise protocol template is unavailable")
    return {
        "success": True,
        "exercise": asdict(exercise),
        "protocol": None
        if protocol is None
        else {
            "slug": protocol.protocol_slug,
            "display_name": protocol.display_name,
            "description": protocol.description,
        },
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
