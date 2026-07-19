from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from types import MappingProxyType

import database
from database import get_connection
from models.exercise_catalog_models import (
    EXERCISE_PRESCRIPTION_DISTANCE_UNITS,
    EXERCISE_PRESCRIPTION_LOAD_APPLICABILITIES,
    EXERCISE_PRESCRIPTION_MEASUREMENT_TYPES,
    EXERCISE_PRESCRIPTION_RIR_APPLICABILITIES,
    EXERCISE_PROTOCOL_SLUGS,
    ExerciseCatalogEntry,
    ExerciseFormMediaAsset,
    ExerciseInstruction,
    ExercisePrescriptionMeasurementMetadata,
    ExerciseProtocolMetadata,
    ExerciseProtocolTemplate,
    ExerciseTaxonomyMetadata,
)
from services import (
    exercise_form_media_seed_data,
    exercise_instruction_seed_data,
    exercise_prescription_measurement_seed_data,
    exercise_protocol_seed_data,
    exercise_taxonomy_seed_data,
)

_CATALOG_CACHE_BY_DB_PATH: dict[str, list[ExerciseCatalogEntry]] = {}


def clear_exercise_catalog_cache() -> None:
    """Clear the in-process exercise catalog cache.

    The catalog itself is deterministic and database-backed. Tests frequently
    monkeypatch database.DB_PATH, so the cache is keyed by the current DB path
    and can be cleared explicitly after reseeding.
    """

    _CATALOG_CACHE_BY_DB_PATH.clear()


def _exercise_catalog_cache_key() -> str:
    return str(database.DB_PATH)


CURATED_EXERCISE_CATALOG: list[ExerciseCatalogEntry] = [
    # Bodyweight
    ExerciseCatalogEntry(
        None,
        "Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bodyweight Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Reverse Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Plank",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Side Plank",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dead Bug",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Mountain Climber",
        "conditioning",
        "conditioning",
        ["core", "conditioning"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Inverted Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["bodyweight"],
        "intermediate",
    ),
    # Dumbbell / bench
    ExerciseCatalogEntry(
        None,
        "Dumbbell Bench Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Dumbbell Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Shoulder Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "One-Arm Dumbbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Chest-Supported Dumbbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Chest-Supported Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell RDL",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Goblet Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Reverse Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Lateral Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Farmer Carry",
        "conditioning",
        "carry",
        ["grip", "traps", "core"],
        ["dumbbell"],
        "beginner",
    ),
    # Barbell / rack / plates
    ExerciseCatalogEntry(
        None,
        "Barbell Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Back Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Front Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Bench Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Overhead Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Romanian Deadlift",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Conventional Deadlift",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["barbell", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Hip Thrust",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["barbell", "plates", "adjustable_bench"],
        "intermediate",
    ),
    # EZ bar
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["ez_bar", "plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Skull Crusher",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["ez_bar", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Close-Grip Press",
        "strength",
        "horizontal_push",
        ["triceps", "chest"],
        ["ez_bar", "plates", "adjustable_bench"],
        "intermediate",
    ),
    # Pull-up bar
    ExerciseCatalogEntry(
        None,
        "Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Chin-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band-Assisted Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar", "resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Hanging Knee Raise",
        "core",
        "core_anti_extension",
        ["core", "hip_flexors"],
        ["pull_up_bar"],
        "intermediate",
    ),
    # Bands
    ExerciseCatalogEntry(
        None,
        "Band Pull-Apart",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Face Pull",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Triceps Pressdown",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band External Rotation",
        "mobility",
        "horizontal_pull",
        ["rotator_cuff"],
        ["resistance_band"],
        "beginner",
    ),
    # Cable
    ExerciseCatalogEntry(
        None,
        "Cable Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Lat Pulldown",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Lat Pulldown",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Face Pull",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Triceps Pressdown",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None, "Cable Curl", "strength", "arms_biceps", ["biceps"], ["cable"], "beginner"
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Lateral Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Woodchop",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["cable"],
        "beginner",
    ),
    # Machines retained for commercial gym users only
    ExerciseCatalogEntry(
        None,
        "Leg Press",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["machine"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Machine Chest Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["machine"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Machine Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["machine"],
        "beginner",
    ),
    # Cardio
    ExerciseCatalogEntry(
        None,
        "Treadmill Walk",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Incline Walk",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Steady State",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "intermediate",
    ),
    # Expanded home-gym catalog
    ExerciseCatalogEntry(
        None,
        "Bear Crawl",
        "conditioning",
        "conditioning",
        ["core", "shoulders", "conditioning"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bird Dog",
        "core",
        "core_anti_rotation",
        ["core", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Hollow Body Hold",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Hollow Rock",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Superman Hold",
        "core",
        "hinge",
        ["lower_back", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Walking Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Lateral Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes", "adductors"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Wall Sit",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Standing Calf Raise",
        "strength",
        "conditioning",
        ["calves"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Single-Leg Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Pike Push-Up",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Close-Grip Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Tempo Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Decline Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bench Dip",
        "strength",
        "arms_triceps",
        ["triceps", "chest"],
        ["bodyweight", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Floor Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Fly",
        "strength",
        "horizontal_push",
        ["chest", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Dumbbell Fly",
        "strength",
        "horizontal_push",
        ["chest", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Pullover",
        "strength",
        "horizontal_pull",
        ["lats", "chest", "core"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Arnold Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Seated Dumbbell Shoulder Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Front Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Rear Delt Fly",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Chest-Supported Rear Delt Fly",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["dumbbell", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Shrug",
        "strength",
        "horizontal_pull",
        ["traps", "upper_back"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Upright Row",
        "strength",
        "vertical_push",
        ["shoulders", "traps"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Hammer Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Concentration Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Zottman Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Kickback",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["dumbbell", "adjustable_bench"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Skull Crusher",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Close-Grip Press",
        "strength",
        "horizontal_push",
        ["triceps", "chest"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Step-Up",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Lateral Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes", "adductors"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Bulgarian Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Sumo Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "adductors"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Front Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Single-Leg RDL",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "core"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Hip Thrust",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Suitcase Carry",
        "conditioning",
        "carry",
        ["grip", "core", "obliques"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Waiter Carry",
        "conditioning",
        "carry",
        ["shoulders", "core", "grip"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Front Rack Carry",
        "conditioning",
        "carry",
        ["core", "upper_back", "grip"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Calf Raise",
        "strength",
        "conditioning",
        ["calves"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Pause Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Box Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Reverse Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Good Morning",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "lower_back"],
        ["barbell", "rack", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Floor Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Close-Grip Bench Press",
        "strength",
        "horizontal_push",
        ["triceps", "chest", "shoulders"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Incline Barbell Bench Press",
        "strength",
        "horizontal_push",
        ["chest", "shoulders", "triceps"],
        ["barbell", "rack", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Push Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps", "quadriceps"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Pendlay Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps", "upper_back"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell High Pull",
        "strength",
        "horizontal_pull",
        ["upper_back", "traps", "shoulders"],
        ["barbell", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["barbell", "plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Rollout",
        "core",
        "core_anti_extension",
        ["core", "shoulders"],
        ["barbell", "plates"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Plate Front Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Plate Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Plate Pinch Carry",
        "conditioning",
        "carry",
        ["grip", "forearms", "core"],
        ["plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Reverse Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["ez_bar", "plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Preacher-Style Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["ez_bar", "plates", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Overhead Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["ez_bar", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Upright Row",
        "strength",
        "vertical_push",
        ["shoulders", "traps"],
        ["ez_bar", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Neutral-Grip Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Negative Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps"],
        ["pull_up_bar"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Scapular Pull-Up",
        "strength",
        "vertical_pull",
        ["lats", "lower_traps"],
        ["pull_up_bar"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Commando Pull-Up",
        "strength",
        "vertical_pull",
        ["back", "biceps", "core"],
        ["pull_up_bar"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Dead Hang",
        "mobility",
        "vertical_pull",
        ["grip", "shoulders"],
        ["pull_up_bar"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Hanging Leg Raise",
        "core",
        "core_anti_extension",
        ["core", "hip_flexors"],
        ["pull_up_bar"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Hanging Oblique Knee Raise",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Biceps Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Hammer Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Overhead Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Lateral Raise",
        "strength",
        "vertical_push",
        ["shoulders"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Shoulder Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Lat Pulldown",
        "strength",
        "vertical_pull",
        ["lats", "biceps"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Straight-Arm Pulldown",
        "strength",
        "vertical_pull",
        ["lats"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Pull-Through",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Good Morning",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "lower_back"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Resisted Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight", "resistance_band"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Pallof Press",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Woodchop",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Lateral Walk",
        "strength",
        "lunge",
        ["glutes", "hips"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Monster Walk",
        "strength",
        "lunge",
        ["glutes", "hips"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Glute Bridge",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["bodyweight", "resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Single-Arm Cable Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable High Row",
        "strength",
        "horizontal_pull",
        ["upper_back", "rear_delts", "biceps"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Reverse Fly",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Chest Fly",
        "strength",
        "horizontal_push",
        ["chest", "shoulders"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Single-Arm Cable Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "core"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Upright Row",
        "strength",
        "vertical_push",
        ["shoulders", "traps"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Y Raise",
        "strength",
        "vertical_push",
        ["shoulders", "lower_traps"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable External Rotation",
        "strength",
        "horizontal_pull",
        ["rotator_cuff", "shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Internal Rotation",
        "strength",
        "horizontal_pull",
        ["rotator_cuff", "shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Pull-Through",
        "strength",
        "hinge",
        ["glutes", "hamstrings"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Crunch",
        "core",
        "core_anti_extension",
        ["core"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Pallof Press",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Triceps Pressdown",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Overhead Triceps Extension",
        "strength",
        "arms_triceps",
        ["triceps"],
        ["cable", "rope_cable_attachment"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Hammer Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Face Pull",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Straight-Arm Cable Pulldown",
        "strength",
        "vertical_pull",
        ["lats"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Hamstring Curl",
        "strength",
        "hinge",
        ["hamstrings", "glutes"],
        ["exercise_ball"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Rollout",
        "core",
        "core_anti_extension",
        ["core", "shoulders"],
        ["exercise_ball"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Plank",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight", "exercise_ball"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Stir-the-Pot",
        "core",
        "core_anti_extension",
        ["core", "shoulders"],
        ["exercise_ball"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Wall Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["exercise_ball"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Stability Ball Dead Bug",
        "core",
        "core_anti_extension",
        ["core"],
        ["exercise_ball"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Easy Jog",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Hill Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Tempo Run",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Recovery Ride",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Tempo Ride",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Hill Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "intermediate",
    ),
]


EXERCISE_CATALOG_EXPANSION_V1: list[ExerciseCatalogEntry] = [
    # Exercise Catalog Expansion v1: curated home-gym variety and recovery options.
    ExerciseCatalogEntry(
        None,
        "Wall Push-Up",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Scapular Push-Up",
        "strength",
        "horizontal_push",
        ["serratus", "shoulders", "upper_back"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Plank Shoulder Tap",
        "core",
        "core_anti_rotation",
        ["core", "shoulders"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Reverse Crunch",
        "core",
        "core_anti_extension",
        ["core", "hip_flexors"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Heel Tap",
        "core",
        "core_anti_extension",
        ["core"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Side Plank Reach-Through",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["bodyweight"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Seated Knee Tuck",
        "core",
        "core_anti_extension",
        ["core", "hip_flexors"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Toe Walk",
        "conditioning",
        "conditioning",
        ["calves", "feet"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Heel Walk",
        "conditioning",
        "conditioning",
        ["tibialis", "feet"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Prone Y-T-W Raise",
        "mobility",
        "horizontal_pull",
        ["upper_back", "rear_delts", "rotator_cuff"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cat-Cow",
        "mobility",
        "mobility",
        ["spine", "core"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Quadruped T-Spine Rotation",
        "mobility",
        "mobility",
        ["thoracic_spine", "shoulders"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Half-Kneeling Hip Flexor Stretch",
        "mobility",
        "mobility",
        ["hip_flexors", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "90/90 Hip Switch",
        "mobility",
        "mobility",
        ["hips", "glutes"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Child's Pose Lat Stretch",
        "mobility",
        "mobility",
        ["lats", "shoulders"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Wall Slide",
        "mobility",
        "vertical_push",
        ["shoulders", "upper_back"],
        ["bodyweight"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Squeeze Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Low-Incline Dumbbell Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Tate Press",
        "strength",
        "arms_triceps",
        ["triceps", "chest"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Reverse Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Cross-Body Hammer Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Spider Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["dumbbell", "adjustable_bench"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Suitcase Deadlift",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "core"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Farmer March",
        "conditioning",
        "carry",
        ["grip", "core", "traps"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Suitcase March",
        "conditioning",
        "carry",
        ["grip", "core", "obliques"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Tempo Goblet Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes", "core"],
        ["dumbbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Heel-Elevated Goblet Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["dumbbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Offset Reverse Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes", "core"],
        ["dumbbell"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Skater Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["dumbbell"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Dumbbell Renegade Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps", "core"],
        ["dumbbell"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Shrug",
        "strength",
        "horizontal_pull",
        ["traps", "upper_back"],
        ["barbell", "plates"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Calf Raise",
        "strength",
        "squat",
        ["calves"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Rack Pull",
        "strength",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["barbell", "rack", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Hip Hinge Drill",
        "mobility",
        "hinge",
        ["hamstrings", "glutes", "back"],
        ["barbell"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Tall-Kneeling Press",
        "strength",
        "vertical_push",
        ["shoulders", "triceps", "core"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Barbell Reverse-Grip Row",
        "strength",
        "horizontal_pull",
        ["back", "biceps"],
        ["barbell", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Drag Curl",
        "strength",
        "arms_biceps",
        ["biceps"],
        ["ez_bar", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar Close-Grip Floor Press",
        "strength",
        "horizontal_push",
        ["triceps", "chest"],
        ["ez_bar", "plates"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "EZ-Bar JM Press",
        "strength",
        "arms_triceps",
        ["triceps", "chest"],
        ["ez_bar", "plates", "adjustable_bench"],
        "advanced",
    ),
    ExerciseCatalogEntry(
        None,
        "Pull-Up Bar Dead Hang",
        "mobility",
        "vertical_pull",
        ["grip", "lats", "shoulders"],
        ["pull_up_bar"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Pull-Up Flexed-Arm Hang",
        "strength",
        "vertical_pull",
        ["back", "biceps", "grip"],
        ["pull_up_bar"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Chest Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Squat",
        "strength",
        "squat",
        ["quadriceps", "glutes"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Split Squat",
        "strength",
        "lunge",
        ["quadriceps", "glutes"],
        ["resistance_band"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Romanian Deadlift",
        "strength",
        "hinge",
        ["hamstrings", "glutes"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Hamstring Curl",
        "strength",
        "hinge",
        ["hamstrings"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Dead Bug Pulldown",
        "core",
        "core_anti_extension",
        ["core", "lats"],
        ["bodyweight", "resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Anti-Rotation Hold",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Band Shoulder Dislocate",
        "mobility",
        "vertical_push",
        ["shoulders", "upper_back"],
        ["resistance_band"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Chest Press",
        "strength",
        "horizontal_push",
        ["chest", "triceps", "shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Rear Delt Row",
        "strength",
        "horizontal_pull",
        ["rear_delts", "upper_back"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable 90/90 External Rotation",
        "mobility",
        "horizontal_pull",
        ["rotator_cuff", "shoulders"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Lateral Lunge",
        "strength",
        "lunge",
        ["quadriceps", "glutes", "adductors"],
        ["cable"],
        "intermediate",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Romanian Deadlift",
        "strength",
        "hinge",
        ["hamstrings", "glutes"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Kickback",
        "strength",
        "hinge",
        ["glutes"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Cable Anti-Rotation Hold",
        "core",
        "core_anti_rotation",
        ["core", "obliques"],
        ["cable"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Rope Cable Curl",
        "strength",
        "arms_biceps",
        ["biceps", "forearms"],
        ["cable", "rope_cable_attachment"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Recovery Walk",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Treadmill Easy Intervals",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["treadmill"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Easy Spin",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "beginner",
    ),
    ExerciseCatalogEntry(
        None,
        "Bike Cadence Drill",
        "conditioning",
        "conditioning",
        ["conditioning"],
        ["bike"],
        "beginner",
    ),
]

CURATED_EXERCISE_CATALOG.extend(EXERCISE_CATALOG_EXPANSION_V1)


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_display_name(value: str) -> str:
    return " ".join(value.strip().replace("-", " ").split()).title()


def _normalize_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return list(
        dict.fromkeys(_normalize_token(str(value)) for value in values if value)
    )


def _encode_json_list(values: list[str]) -> str:
    return json.dumps(_normalize_list(values))


def _decode_json_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        decoded = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return _normalize_list([str(value) for value in decoded])


def _encode_instruction_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def _decode_instruction_list(raw_value: str, field_name: str) -> list[str]:
    try:
        decoded = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid persisted {field_name} instruction list") from exc
    if not isinstance(decoded, list) or any(
        not isinstance(value, str) for value in decoded
    ):
        raise ValueError(f"Invalid persisted {field_name} instruction list")
    return decoded


def _validate_catalog_exercise_id(catalog_exercise_id: int) -> None:
    if (
        isinstance(catalog_exercise_id, bool)
        or not isinstance(catalog_exercise_id, int)
        or catalog_exercise_id <= 0
    ):
        raise ValueError("catalog_exercise_id must be a positive integer")


def _validate_exercise_instruction(instruction: ExerciseInstruction) -> None:
    if not isinstance(instruction, ExerciseInstruction):
        raise TypeError("instruction must be an ExerciseInstruction")
    _validate_catalog_exercise_id(instruction.catalog_exercise_id)
    if not isinstance(instruction.overview, str):
        raise TypeError("overview must be a string")

    for field_name in (
        "setup_steps",
        "execution_steps",
        "form_cues",
        "common_mistakes",
        "safety_notes",
    ):
        values = getattr(instruction, field_name)
        if not isinstance(values, list) or any(
            not isinstance(value, str) for value in values
        ):
            raise TypeError(f"{field_name} must be a list of strings")


_FORM_MEDIA_PATH_PREFIX = "/exercise-media/free-exercise-db/"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_DIRECTORY = Path(__file__).resolve().parents[1] / "frontend" / "public"


def _validate_exercise_form_media_asset(asset: ExerciseFormMediaAsset) -> None:
    if not isinstance(asset, ExerciseFormMediaAsset):
        raise TypeError("asset must be an ExerciseFormMediaAsset")
    _validate_catalog_exercise_id(asset.catalog_exercise_id)
    if not asset.media_key.strip():
        raise ValueError("media_key is required")
    if asset.media_type != "static_image":
        raise ValueError("Only static_image form media is supported")
    if (
        not asset.asset_path.startswith(_FORM_MEDIA_PATH_PREFIX)
        or ".." in asset.asset_path
    ):
        raise ValueError("asset_path must be a local approved form-media path")
    if not asset.alt_text.strip():
        raise ValueError("alt_text is required")
    if not isinstance(asset.sort_order, int) or asset.sort_order < 1:
        raise ValueError("sort_order must be a positive integer")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (
            asset.source_name,
            asset.source_exercise_id,
            asset.source_url,
            asset.license_name,
            asset.license_url,
        )
    ):
        raise ValueError("complete media provenance is required")
    if not _SHA256_PATTERN.fullmatch(asset.asset_sha256):
        raise ValueError("asset_sha256 must be a lowercase SHA-256 digest")

    local_asset = _PUBLIC_DIRECTORY / asset.asset_path.lstrip("/")
    if not local_asset.is_file():
        raise ValueError(
            f"Approved local form-media asset is missing: {asset.asset_path}"
        )
    actual_hash = hashlib.sha256(local_asset.read_bytes()).hexdigest()
    if actual_hash != asset.asset_sha256:
        raise ValueError(
            f"Approved local form-media asset checksum mismatch: {asset.asset_path}"
        )


def ensure_exercise_catalog_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_catalog_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        exercise_type TEXT NOT NULL,
        movement_pattern TEXT NOT NULL,
        primary_muscle_groups_json TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_equipment_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id INTEGER NOT NULL,
        equipment TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(exercise_id, equipment),
        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog_exercises(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_catalog_instructions (
        exercise_id INTEGER PRIMARY KEY,
        overview TEXT NOT NULL,
        setup_steps_json TEXT NOT NULL,
        execution_steps_json TEXT NOT NULL,
        form_cues_json TEXT NOT NULL,
        common_mistakes_json TEXT NOT NULL,
        safety_notes_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog_exercises(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_catalog_form_media (
        exercise_id INTEGER NOT NULL,
        media_key TEXT NOT NULL,
        media_type TEXT NOT NULL,
        asset_path TEXT NOT NULL,
        alt_text TEXT NOT NULL,
        caption TEXT,
        sort_order INTEGER NOT NULL,
        source_name TEXT NOT NULL,
        source_exercise_id TEXT NOT NULL,
        source_url TEXT NOT NULL,
        license_name TEXT NOT NULL,
        license_url TEXT NOT NULL,
        asset_sha256 TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        PRIMARY KEY (exercise_id, media_key),
        UNIQUE (exercise_id, sort_order),
        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog_exercises(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_catalog_taxonomy (
        exercise_id INTEGER PRIMARY KEY,
        family_slug TEXT NOT NULL, base_movement_slug TEXT NOT NULL,
        visual_identity_slug TEXT NOT NULL, taxonomy_status TEXT NOT NULL,
        body_position TEXT, support_type TEXT, bench_angle TEXT, laterality TEXT,
        grip TEXT, stance TEXT, load_position TEXT, attachment TEXT,
        movement_direction TEXT, locomotion_mode TEXT, execution_mode TEXT,
        variant_extensions_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog_exercises(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_catalog_prescription_measurements (
        exercise_id INTEGER PRIMARY KEY,
        default_measurement_type TEXT NOT NULL,
        allowed_measurement_types_json TEXT NOT NULL,
        sets_applicable INTEGER NOT NULL,
        load_applicability TEXT NOT NULL,
        rir_applicability TEXT NOT NULL,
        distance_unit TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog_exercises(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_catalog_protocols (
        exercise_id INTEGER PRIMARY KEY,
        protocol_slug TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog_exercises(id)
    )
    """)

    conn.commit()
    conn.close()


def upsert_exercise_instruction(
    instruction: ExerciseInstruction,
) -> ExerciseInstruction:
    """Persist one structured instruction record for a stable catalog exercise ID."""

    _validate_exercise_instruction(instruction)
    ensure_exercise_catalog_tables()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        with conn:
            _upsert_exercise_instruction_row(cursor, instruction)
    finally:
        conn.close()

    return ExerciseInstruction(
        catalog_exercise_id=instruction.catalog_exercise_id,
        overview=instruction.overview,
        setup_steps=list(instruction.setup_steps),
        execution_steps=list(instruction.execution_steps),
        form_cues=list(instruction.form_cues),
        common_mistakes=list(instruction.common_mistakes),
        safety_notes=list(instruction.safety_notes),
    )


def _upsert_exercise_instruction_row(cursor, instruction: ExerciseInstruction) -> None:
    cursor.execute(
        "SELECT 1 FROM exercise_catalog_exercises WHERE id = ?",
        (instruction.catalog_exercise_id,),
    )
    if cursor.fetchone() is None:
        raise ValueError(
            f"Catalog exercise {instruction.catalog_exercise_id} does not exist"
        )

    cursor.execute(
        """
        INSERT INTO exercise_catalog_instructions (
            exercise_id,
            overview,
            setup_steps_json,
            execution_steps_json,
            form_cues_json,
            common_mistakes_json,
            safety_notes_json,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(exercise_id) DO UPDATE SET
            overview = excluded.overview,
            setup_steps_json = excluded.setup_steps_json,
            execution_steps_json = excluded.execution_steps_json,
            form_cues_json = excluded.form_cues_json,
            common_mistakes_json = excluded.common_mistakes_json,
            safety_notes_json = excluded.safety_notes_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            instruction.catalog_exercise_id,
            instruction.overview,
            _encode_instruction_list(instruction.setup_steps),
            _encode_instruction_list(instruction.execution_steps),
            _encode_instruction_list(instruction.form_cues),
            _encode_instruction_list(instruction.common_mistakes),
            _encode_instruction_list(instruction.safety_notes),
        ),
    )


def get_exercise_instruction(
    catalog_exercise_id: int,
) -> ExerciseInstruction | None:
    """Return persisted instructions by stable catalog identity, or explicit absence."""

    _validate_catalog_exercise_id(catalog_exercise_id)
    ensure_exercise_catalog_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            exercise_id,
            overview,
            setup_steps_json,
            execution_steps_json,
            form_cues_json,
            common_mistakes_json,
            safety_notes_json
        FROM exercise_catalog_instructions
        WHERE exercise_id = ?
        """,
        (catalog_exercise_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None

    return ExerciseInstruction(
        catalog_exercise_id=row["exercise_id"],
        overview=row["overview"],
        setup_steps=_decode_instruction_list(row["setup_steps_json"], "setup_steps"),
        execution_steps=_decode_instruction_list(
            row["execution_steps_json"], "execution_steps"
        ),
        form_cues=_decode_instruction_list(row["form_cues_json"], "form_cues"),
        common_mistakes=_decode_instruction_list(
            row["common_mistakes_json"], "common_mistakes"
        ),
        safety_notes=_decode_instruction_list(row["safety_notes_json"], "safety_notes"),
    )


def _upsert_exercise_form_media_row(cursor, asset: ExerciseFormMediaAsset) -> None:
    cursor.execute(
        "SELECT 1 FROM exercise_catalog_exercises WHERE id = ?",
        (asset.catalog_exercise_id,),
    )
    if cursor.fetchone() is None:
        raise ValueError(f"Catalog exercise {asset.catalog_exercise_id} does not exist")

    cursor.execute(
        """
        INSERT INTO exercise_catalog_form_media (
            exercise_id, media_key, media_type, asset_path, alt_text, caption,
            sort_order, source_name, source_exercise_id, source_url,
            license_name, license_url, asset_sha256, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(exercise_id, media_key) DO UPDATE SET
            media_type = excluded.media_type,
            asset_path = excluded.asset_path,
            alt_text = excluded.alt_text,
            caption = excluded.caption,
            sort_order = excluded.sort_order,
            source_name = excluded.source_name,
            source_exercise_id = excluded.source_exercise_id,
            source_url = excluded.source_url,
            license_name = excluded.license_name,
            license_url = excluded.license_url,
            asset_sha256 = excluded.asset_sha256,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            asset.catalog_exercise_id,
            asset.media_key,
            asset.media_type,
            asset.asset_path,
            asset.alt_text,
            asset.caption,
            asset.sort_order,
            asset.source_name,
            asset.source_exercise_id,
            asset.source_url,
            asset.license_name,
            asset.license_url,
            asset.asset_sha256,
        ),
    )


def get_exercise_form_media(
    catalog_exercise_id: int,
) -> list[ExerciseFormMediaAsset]:
    """Return ordered approved local media for one stable catalog identity."""

    _validate_catalog_exercise_id(catalog_exercise_id)
    ensure_exercise_catalog_tables()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                exercise_id, media_key, media_type, asset_path, alt_text, caption,
                sort_order, source_name, source_exercise_id, source_url,
                license_name, license_url, asset_sha256
            FROM exercise_catalog_form_media
            WHERE exercise_id = ?
            ORDER BY sort_order, media_key
            """,
            (catalog_exercise_id,),
        ).fetchall()
    finally:
        conn.close()

    return [
        ExerciseFormMediaAsset(
            catalog_exercise_id=row["exercise_id"],
            media_key=row["media_key"],
            media_type=row["media_type"],
            asset_path=row["asset_path"],
            alt_text=row["alt_text"],
            caption=row["caption"],
            sort_order=row["sort_order"],
            source_name=row["source_name"],
            source_exercise_id=row["source_exercise_id"],
            source_url=row["source_url"],
            license_name=row["license_name"],
            license_url=row["license_url"],
            asset_sha256=row["asset_sha256"],
        )
        for row in rows
    ]


_TAXONOMY_CONTROLLED_FIELDS = (
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
_TAXONOMY_CONTROLLED_VALUES = MappingProxyType(
    {
        "body_position": frozenset(
            {
                "chest_supported",
                "childs_pose",
                "half_kneeling",
                "plank",
                "prone",
                "quadruped",
                "seated",
                "standing",
                "tall_kneeling",
            }
        ),
        "support_type": frozenset({"bench", "floor", "machine", "thigh", "wall"}),
        "bench_angle": frozenset({"decline", "incline", "low_incline"}),
        "laterality": frozenset({"bilateral", "unilateral"}),
        "grip": frozenset(
            {
                "close",
                "hammer",
                "mixed",
                "neutral",
                "pinch",
                "pronated",
                "reverse",
                "supinated",
            }
        ),
        "stance": frozenset({"split", "sumo"}),
        "load_position": frozenset(
            {"front_rack", "goblet", "overhead", "sides", "suitcase"}
        ),
        "attachment": frozenset({"rope"}),
        "movement_direction": frozenset(
            {"cross_body", "high_diagonal", "horizontal", "rotation", "vertical"}
        ),
        "locomotion_mode": frozenset({"jog", "march", "run", "unspecified", "walk"}),
        "execution_mode": frozenset({"dynamic", "eccentric_only", "isometric"}),
    }
)
_ALLOWED_TAXONOMY_EXTENSION_KEYS = frozenset(
    {"grade", "range", "range_of_motion_variant", "lower_body_drive"}
)
_SUPPORTED_TAXONOMY_STATUSES = frozenset(
    {"reviewed", "alias_candidate", "review_required"}
)
_TAXONOMY_TOKEN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def _validate_taxonomy_seed() -> None:
    seeds = exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS
    names, catalog_names = (
        [seed.canonical_exercise_name for seed in seeds],
        [entry.name for entry in CURATED_EXERCISE_CATALOG],
    )
    if len(names) != len(set(names)) or set(names) != set(catalog_names):
        raise ValueError(
            "Exercise taxonomy seed must have exact unique canonical-name coverage"
        )
    for seed in seeds:
        tokens = (
            seed.family_slug,
            seed.base_movement_slug,
            seed.visual_identity_slug,
            *seed.variants.values(),
            *seed.variant_extensions.values(),
        )
        if not seed.visual_identity_slug.startswith("visual_") or any(
            not _TAXONOMY_TOKEN.fullmatch(value) for value in tokens
        ):
            raise ValueError("Taxonomy values must be strict normalized tokens")
        if seed.taxonomy_status not in _SUPPORTED_TAXONOMY_STATUSES:
            raise ValueError("Unsupported taxonomy status")
        if (
            set(seed.variants) - set(_TAXONOMY_CONTROLLED_FIELDS)
            or set(seed.variant_extensions) - _ALLOWED_TAXONOMY_EXTENSION_KEYS
        ):
            raise ValueError("Unsupported taxonomy variant field")
        if any(
            value not in _TAXONOMY_CONTROLLED_VALUES[key]
            for key, value in seed.variants.items()
        ):
            raise ValueError("Unsupported taxonomy controlled value")


def seed_exercise_taxonomy() -> list[ExerciseTaxonomyMetadata]:
    seed_exercise_catalog()
    _validate_taxonomy_seed()
    seeds = exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS
    conn = get_connection()
    try:
        ids = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM exercise_catalog_exercises")
        }
        if set(seed.canonical_exercise_name for seed in seeds) - set(ids):
            raise ValueError("Persisted exercise catalog is missing taxonomy targets")
        metadata = [
            ExerciseTaxonomyMetadata(
                ids[seed.canonical_exercise_name],
                seed.family_slug,
                seed.base_movement_slug,
                seed.visual_identity_slug,
                seed.taxonomy_status,
                variant_extensions=dict(seed.variant_extensions),
                **seed.variants,
            )
            for seed in seeds
        ]
        with conn:
            conn.execute("DELETE FROM exercise_catalog_taxonomy")
            conn.executemany(
                "INSERT INTO exercise_catalog_taxonomy (exercise_id,family_slug,base_movement_slug,visual_identity_slug,taxonomy_status,body_position,support_type,bench_angle,laterality,grip,stance,load_position,attachment,movement_direction,locomotion_mode,execution_mode,variant_extensions_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        item.catalog_exercise_id,
                        item.family_slug,
                        item.base_movement_slug,
                        item.visual_identity_slug,
                        item.taxonomy_status,
                        *[
                            getattr(item, field)
                            for field in _TAXONOMY_CONTROLLED_FIELDS
                        ],
                        json.dumps(item.variant_extensions, sort_keys=True),
                    )
                    for item in metadata
                ],
            )
    finally:
        conn.close()
    return metadata


def get_exercise_taxonomy(catalog_exercise_id: int) -> ExerciseTaxonomyMetadata | None:
    _validate_catalog_exercise_id(catalog_exercise_id)
    ensure_exercise_catalog_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM exercise_catalog_taxonomy WHERE exercise_id = ?",
            (catalog_exercise_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    try:
        extensions = json.loads(row["variant_extensions_json"])
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid persisted taxonomy variant extensions") from exc
    if not isinstance(extensions, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in extensions.items()
    ):
        raise ValueError("Invalid persisted taxonomy variant extensions")
    return ExerciseTaxonomyMetadata(
        row["exercise_id"],
        row["family_slug"],
        row["base_movement_slug"],
        row["visual_identity_slug"],
        row["taxonomy_status"],
        variant_extensions=extensions,
        **{field: row[field] for field in _TAXONOMY_CONTROLLED_FIELDS},
    )


def _validate_prescription_measurement_values(
    metadata: ExercisePrescriptionMeasurementMetadata,
) -> None:
    _validate_catalog_exercise_id(metadata.catalog_exercise_id)
    if metadata.default_measurement_type not in EXERCISE_PRESCRIPTION_MEASUREMENT_TYPES:
        raise ValueError("Unsupported default exercise prescription measurement type")
    if (
        not metadata.allowed_measurement_types
        or len(metadata.allowed_measurement_types)
        != len(set(metadata.allowed_measurement_types))
        or set(metadata.allowed_measurement_types)
        - EXERCISE_PRESCRIPTION_MEASUREMENT_TYPES
    ):
        raise ValueError("Unsupported allowed exercise prescription measurement types")
    if metadata.default_measurement_type not in metadata.allowed_measurement_types:
        raise ValueError("Default exercise prescription type must be allowed")
    if not isinstance(metadata.sets_applicable, bool):
        raise ValueError("Exercise prescription sets_applicable must be boolean")
    if metadata.load_applicability not in EXERCISE_PRESCRIPTION_LOAD_APPLICABILITIES:
        raise ValueError("Unsupported exercise prescription load applicability")
    if metadata.rir_applicability not in EXERCISE_PRESCRIPTION_RIR_APPLICABILITIES:
        raise ValueError("Unsupported exercise prescription RIR applicability")
    distance_enabled = "distance" in metadata.allowed_measurement_types
    if (
        distance_enabled
        and metadata.distance_unit not in EXERCISE_PRESCRIPTION_DISTANCE_UNITS
    ):
        raise ValueError("Distance-enabled exercise prescriptions must use meters")
    if not distance_enabled and metadata.distance_unit is not None:
        raise ValueError(
            "Non-distance exercise prescriptions cannot define a distance unit"
        )


def _validated_prescription_measurement_seed_metadata(
    ids_by_name: dict[str, int],
) -> list[ExercisePrescriptionMeasurementMetadata]:
    seeds = exercise_prescription_measurement_seed_data.EXERCISE_PRESCRIPTION_MEASUREMENT_SEEDS
    seed_names = [seed.canonical_exercise_name for seed in seeds]
    catalog_names = [entry.name for entry in CURATED_EXERCISE_CATALOG]
    if (
        len(seed_names) != 240
        or len(seed_names) != len(set(seed_names))
        or set(seed_names) != set(catalog_names)
    ):
        raise ValueError(
            "Exercise prescription measurement seed must have exact unique "
            "canonical-name coverage"
        )
    if set(seed_names) - set(ids_by_name):
        raise ValueError(
            "Persisted exercise catalog is missing prescription measurement targets"
        )

    metadata = [
        ExercisePrescriptionMeasurementMetadata(
            catalog_exercise_id=ids_by_name[seed.canonical_exercise_name],
            default_measurement_type=seed.default_measurement_type,
            allowed_measurement_types=seed.allowed_measurement_types,
            sets_applicable=seed.sets_applicable,
            load_applicability=seed.load_applicability,
            rir_applicability=seed.rir_applicability,
            distance_unit=seed.distance_unit,
        )
        for seed in seeds
    ]
    for item in metadata:
        _validate_prescription_measurement_values(item)

    default_counts = {
        measurement_type: sum(
            item.default_measurement_type == measurement_type for item in metadata
        )
        for measurement_type in EXERCISE_PRESCRIPTION_MEASUREMENT_TYPES
    }
    multi_mode_count = sum(len(item.allowed_measurement_types) > 1 for item in metadata)
    distance_enabled_count = sum(
        "distance" in item.allowed_measurement_types for item in metadata
    )
    if (
        default_counts != {"reps": 203, "duration": 29, "distance": 8}
        or multi_mode_count != 31
        or distance_enabled_count != 25
    ):
        raise ValueError("Exercise prescription measurement seed invariants failed")
    return metadata


def seed_exercise_prescription_measurements() -> (
    list[ExercisePrescriptionMeasurementMetadata]
):
    """Atomically replace the complete stable-ID measurement projection."""

    ensure_exercise_catalog_tables()
    conn = get_connection()
    try:
        ids_by_name = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM exercise_catalog_exercises")
        }
        metadata = _validated_prescription_measurement_seed_metadata(ids_by_name)
        with conn:
            conn.execute("DELETE FROM exercise_catalog_prescription_measurements")
            conn.executemany(
                """
                INSERT INTO exercise_catalog_prescription_measurements (
                    exercise_id,
                    default_measurement_type,
                    allowed_measurement_types_json,
                    sets_applicable,
                    load_applicability,
                    rir_applicability,
                    distance_unit,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [
                    (
                        item.catalog_exercise_id,
                        item.default_measurement_type,
                        json.dumps(item.allowed_measurement_types),
                        int(item.sets_applicable),
                        item.load_applicability,
                        item.rir_applicability,
                        item.distance_unit,
                    )
                    for item in metadata
                ],
            )
    finally:
        conn.close()
    return metadata


def get_exercise_prescription_measurement_metadata(
    catalog_exercise_id: int,
) -> ExercisePrescriptionMeasurementMetadata | None:
    """Return persisted measurement metadata for one stable catalog ID."""

    _validate_catalog_exercise_id(catalog_exercise_id)
    ensure_exercise_catalog_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM exercise_catalog_prescription_measurements
            WHERE exercise_id = ?
            """,
            (catalog_exercise_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    try:
        allowed_raw = json.loads(row["allowed_measurement_types_json"])
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Invalid persisted exercise prescription measurement types"
        ) from exc
    if not isinstance(allowed_raw, list) or any(
        not isinstance(value, str) for value in allowed_raw
    ):
        raise ValueError("Invalid persisted exercise prescription measurement types")
    if row["sets_applicable"] not in {0, 1}:
        raise ValueError("Invalid persisted exercise prescription sets applicability")
    metadata = ExercisePrescriptionMeasurementMetadata(
        catalog_exercise_id=row["exercise_id"],
        default_measurement_type=row["default_measurement_type"],
        allowed_measurement_types=tuple(allowed_raw),
        sets_applicable=bool(row["sets_applicable"]),
        load_applicability=row["load_applicability"],
        rir_applicability=row["rir_applicability"],
        distance_unit=row["distance_unit"],
    )
    _validate_prescription_measurement_values(metadata)
    return metadata


def _protocol_templates_by_slug() -> dict[str, ExerciseProtocolTemplate]:
    templates = exercise_protocol_seed_data.EXERCISE_PROTOCOL_TEMPLATES
    slugs = [template.protocol_slug for template in templates]
    if (
        len(templates) != 9
        or len(slugs) != len(set(slugs))
        or set(slugs) != EXERCISE_PROTOCOL_SLUGS
        or any(
            not template.display_name.strip() or not template.description.strip()
            for template in templates
        )
    ):
        raise ValueError("Exercise protocol template registry is invalid")
    return {
        template.protocol_slug: ExerciseProtocolTemplate(
            protocol_slug=template.protocol_slug,
            display_name=template.display_name,
            description=template.description,
        )
        for template in templates
    }


def get_exercise_protocol_template(
    protocol_slug: str,
) -> ExerciseProtocolTemplate | None:
    """Return one immutable repository-owned protocol template by its slug."""

    return _protocol_templates_by_slug().get(protocol_slug)


def _validated_protocol_seed_metadata(
    ids_by_name: dict[str, int],
) -> list[ExerciseProtocolMetadata]:
    templates = _protocol_templates_by_slug()
    seeds = exercise_protocol_seed_data.EXERCISE_PROTOCOL_SEEDS
    names = [seed.canonical_exercise_name for seed in seeds]
    if len(seeds) != 16 or len(names) != len(set(names)):
        raise ValueError("Exercise protocol seed must have exactly 16 unique names")
    if set(names) - {entry.name for entry in CURATED_EXERCISE_CATALOG}:
        raise ValueError("Exercise protocol seed references unknown catalog exercises")
    if set(names) - set(ids_by_name):
        raise ValueError("Persisted exercise catalog is missing protocol targets")
    if any(seed.protocol_slug not in templates for seed in seeds):
        raise ValueError("Exercise protocol seed references an unsupported protocol")

    metadata = [
        ExerciseProtocolMetadata(
            catalog_exercise_id=ids_by_name[seed.canonical_exercise_name],
            protocol_slug=seed.protocol_slug,
        )
        for seed in seeds
    ]
    expected_counts = {
        "tempo": 4,
        "intervals": 2,
        "easy": 2,
        "hill_intervals": 2,
        "recovery": 2,
        "steady_state": 1,
        "pause": 1,
        "easy_intervals": 1,
        "cadence_drill": 1,
    }
    actual_counts = {
        slug: sum(item.protocol_slug == slug for item in metadata)
        for slug in EXERCISE_PROTOCOL_SLUGS
    }
    if actual_counts != expected_counts:
        raise ValueError("Exercise protocol seed invariants failed")
    return metadata


def seed_exercise_protocols() -> list[ExerciseProtocolMetadata]:
    """Atomically replace the complete protocol projection by stable catalog ID."""

    ensure_exercise_catalog_tables()
    conn = get_connection()
    try:
        ids_by_name = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM exercise_catalog_exercises")
        }
        metadata = _validated_protocol_seed_metadata(ids_by_name)
        with conn:
            conn.execute("DELETE FROM exercise_catalog_protocols")
            conn.executemany(
                """
                INSERT INTO exercise_catalog_protocols (
                    exercise_id, protocol_slug, updated_at
                ) VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                [(item.catalog_exercise_id, item.protocol_slug) for item in metadata],
            )
    finally:
        conn.close()
    return metadata


def get_exercise_protocol_metadata(
    catalog_exercise_id: int,
) -> ExerciseProtocolMetadata | None:
    """Return protocol metadata by stable catalog ID, or explicit absence."""

    _validate_catalog_exercise_id(catalog_exercise_id)
    ensure_exercise_catalog_tables()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT exercise_id, protocol_slug
            FROM exercise_catalog_protocols
            WHERE exercise_id = ?
            """,
            (catalog_exercise_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    if get_exercise_protocol_template(row["protocol_slug"]) is None:
        raise ValueError("Invalid persisted exercise protocol slug")
    return ExerciseProtocolMetadata(
        catalog_exercise_id=row["exercise_id"], protocol_slug=row["protocol_slug"]
    )


def _entry_to_legacy_exercise_row(
    entry: ExerciseCatalogEntry,
) -> tuple[str, str, str, str]:
    return (
        entry.name,
        ", ".join(
            group.replace("_", " ").title() for group in entry.primary_muscle_groups
        ),
        entry.exercise_type.replace("_", " ").title(),
        ", ".join(
            equipment.replace("_", " ").title()
            for equipment in entry.equipment_required
        ),
    )


def seed_exercise_catalog() -> list[ExerciseCatalogEntry]:
    """Seed the local curated exercise catalog.

    This is intentionally deterministic and local. It also mirrors each entry
    into the existing exercises table so manual workout logging keeps using the
    same simple exercise list endpoint until a richer catalog API is added.
    """

    ensure_exercise_catalog_tables()
    conn = get_connection()
    cursor = conn.cursor()

    for entry in CURATED_EXERCISE_CATALOG:
        normalized_equipment = _normalize_list(entry.equipment_required)
        normalized_groups = _normalize_list(entry.primary_muscle_groups)

        cursor.execute(
            """
            INSERT INTO exercise_catalog_exercises (
                name,
                exercise_type,
                movement_pattern,
                primary_muscle_groups_json,
                difficulty,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                exercise_type = excluded.exercise_type,
                movement_pattern = excluded.movement_pattern,
                primary_muscle_groups_json = excluded.primary_muscle_groups_json,
                difficulty = excluded.difficulty,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                entry.name,
                _normalize_token(entry.exercise_type),
                _normalize_token(entry.movement_pattern),
                json.dumps(normalized_groups),
                _normalize_token(entry.difficulty),
            ),
        )

        cursor.execute(
            "SELECT id FROM exercise_catalog_exercises WHERE name = ?",
            (entry.name,),
        )
        exercise_id = cursor.fetchone()["id"]

        cursor.execute(
            """
            DELETE FROM exercise_equipment_requirements
            WHERE exercise_id = ?
            """,
            (exercise_id,),
        )

        for equipment in normalized_equipment:
            cursor.execute(
                """
                INSERT OR IGNORE INTO exercise_equipment_requirements (
                    exercise_id,
                    equipment
                )
                VALUES (?, ?)
                """,
                (exercise_id, equipment),
            )

        legacy_name, muscle_group, movement_type, equipment = (
            _entry_to_legacy_exercise_row(
                ExerciseCatalogEntry(
                    id=exercise_id,
                    name=entry.name,
                    exercise_type=entry.exercise_type,
                    movement_pattern=entry.movement_pattern,
                    primary_muscle_groups=normalized_groups,
                    equipment_required=normalized_equipment,
                    difficulty=entry.difficulty,
                )
            )
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO exercises (
                name,
                muscle_group,
                movement_type,
                equipment
            )
            VALUES (?, ?, ?, ?)
            """,
            (legacy_name, muscle_group, movement_type, equipment),
        )

    conn.commit()
    conn.close()
    _CATALOG_CACHE_BY_DB_PATH.pop(_exercise_catalog_cache_key(), None)
    return list(CURATED_EXERCISE_CATALOG)


def _validate_exercise_instruction_seed_coverage(
    catalog_names: list[str],
    seed_names: set[str],
) -> None:
    catalog_name_set = set(catalog_names)
    if len(catalog_name_set) != len(catalog_names):
        raise ValueError("Curated exercise catalog contains duplicate names")

    missing = sorted(catalog_name_set - seed_names)
    unknown = sorted(seed_names - catalog_name_set)
    if missing or unknown:
        details: list[str] = []
        if missing:
            details.append(f"missing seed exercises: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown seed exercises: {', '.join(unknown)}")
        raise ValueError(
            "Exercise instruction seed coverage mismatch; " + "; ".join(details)
        )


def seed_exercise_instructions() -> list[ExerciseInstruction]:
    """Atomically persist complete repository-owned instruction seed coverage."""

    seed_exercise_catalog()
    catalog_names = [entry.name for entry in CURATED_EXERCISE_CATALOG]
    instruction_seeds = exercise_instruction_seed_data.EXERCISE_INSTRUCTION_SEEDS
    _validate_exercise_instruction_seed_coverage(
        catalog_names,
        set(instruction_seeds),
    )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM exercise_catalog_exercises")
        persisted_ids_by_name = {row["name"]: row["id"] for row in cursor.fetchall()}
        unresolved = sorted(set(catalog_names) - set(persisted_ids_by_name))
        if unresolved:
            raise ValueError(
                "Persisted exercise catalog is missing seed targets: "
                + ", ".join(unresolved)
            )

        instructions = []
        for name in catalog_names:
            seed = instruction_seeds[name]
            instruction = ExerciseInstruction(
                catalog_exercise_id=persisted_ids_by_name[name],
                overview=seed.overview,
                setup_steps=list(seed.setup_steps),
                execution_steps=list(seed.execution_steps),
                form_cues=list(seed.form_cues),
                common_mistakes=list(seed.common_mistakes),
                safety_notes=list(seed.safety_notes),
            )
            _validate_exercise_instruction(instruction)
            instructions.append(instruction)

        with conn:
            for instruction in instructions:
                _upsert_exercise_instruction_row(cursor, instruction)
    finally:
        conn.close()

    return instructions


def _validated_exercise_form_media_seeds():
    """Validate the complete local manifest before opening its write transaction."""

    seeds = exercise_form_media_seed_data.EXERCISE_FORM_MEDIA_SEEDS
    catalog_names = {entry.name for entry in CURATED_EXERCISE_CATALOG}
    seed_names = {seed.canonical_exercise_name for seed in seeds}
    unknown_names = sorted(seed_names - catalog_names)
    if unknown_names:
        raise ValueError(
            "Form-media seed references unknown catalog exercises: "
            + ", ".join(unknown_names)
        )

    duplicate_keys: set[tuple[str, str]] = set()
    duplicate_orders: set[tuple[str, int]] = set()
    seen_keys: set[tuple[str, str]] = set()
    seen_orders: set[tuple[str, int]] = set()
    for seed in seeds:
        key = (seed.canonical_exercise_name, seed.media_key)
        order = (seed.canonical_exercise_name, seed.sort_order)
        if key in seen_keys:
            duplicate_keys.add(key)
        if order in seen_orders:
            duplicate_orders.add(order)
        seen_keys.add(key)
        seen_orders.add(order)
    if duplicate_keys or duplicate_orders:
        raise ValueError("Form-media seed contains duplicate media keys or ordering")
    return seeds, catalog_names, seed_names


def seed_exercise_form_media() -> list[ExerciseFormMediaAsset]:
    """Atomically replace local media without mutating catalog-owned projections."""

    seeds, catalog_names, seed_names = _validated_exercise_form_media_seeds()
    ensure_exercise_catalog_tables()

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name FROM exercise_catalog_exercises"
        ).fetchall()
        persisted_ids_by_name = {row["name"]: row["id"] for row in rows}
        missing_catalog = sorted(catalog_names - set(persisted_ids_by_name))
        if missing_catalog:
            raise ValueError(
                "Form-media seeding requires an established complete catalog: "
                + ", ".join(missing_catalog)
            )
        unresolved = sorted(seed_names - set(persisted_ids_by_name))
        if unresolved:
            raise ValueError(
                "Persisted exercise catalog is missing form-media targets: "
                + ", ".join(unresolved)
            )

        persisted_catalog_ids = set(persisted_ids_by_name.values())
        taxonomy_rows = conn.execute(
            "SELECT exercise_id, visual_identity_slug FROM exercise_catalog_taxonomy"
        ).fetchall()
        taxonomy_by_catalog_id = {
            row["exercise_id"]: row["visual_identity_slug"] for row in taxonomy_rows
        }
        missing_taxonomy_ids = persisted_catalog_ids - set(taxonomy_by_catalog_id)
        if missing_taxonomy_ids:
            raise ValueError(
                "Form-media seeding requires established taxonomy for every catalog exercise"
            )
        direct_visual_identities = {
            taxonomy_by_catalog_id[persisted_ids_by_name[name]] for name in seed_names
        }
        if len(direct_visual_identities) != 83:
            raise ValueError(
                "Form-media direct owners must map to exactly 83 unique visual identities"
            )

        assets = [
            ExerciseFormMediaAsset(
                catalog_exercise_id=persisted_ids_by_name[seed.canonical_exercise_name],
                media_key=seed.media_key,
                media_type="static_image",
                asset_path=seed.asset_path,
                alt_text=seed.alt_text,
                caption=seed.caption,
                sort_order=seed.sort_order,
                source_name=exercise_form_media_seed_data.SOURCE_NAME,
                source_exercise_id=seed.source_exercise_id,
                source_url=seed.source_url,
                license_name=exercise_form_media_seed_data.LICENSE_NAME,
                license_url=exercise_form_media_seed_data.LICENSE_URL,
                asset_sha256=seed.asset_sha256,
            )
            for seed in seeds
        ]
        for asset in assets:
            _validate_exercise_form_media_asset(asset)

        with conn:
            cursor = conn.cursor()
            # Form media is a repository-owned projection, not user-authored data.
            # Validate every candidate before this transaction, then replace the
            # complete projection so removed manifest entries cannot remain live.
            cursor.execute("DELETE FROM exercise_catalog_form_media")
            for asset in assets:
                _upsert_exercise_form_media_row(cursor, asset)
    finally:
        conn.close()

    return sorted(
        assets, key=lambda asset: (asset.catalog_exercise_id, asset.sort_order)
    )


def _row_to_catalog_entry(row, equipment_required: list[str]) -> ExerciseCatalogEntry:
    return ExerciseCatalogEntry(
        id=row["id"],
        name=row["name"],
        exercise_type=row["exercise_type"],
        movement_pattern=row["movement_pattern"],
        primary_muscle_groups=_decode_json_list(row["primary_muscle_groups_json"]),
        equipment_required=_normalize_list(equipment_required),
        difficulty=row["difficulty"],
    )


def get_exercise_catalog_entry_by_id(
    catalog_exercise_id: int,
) -> ExerciseCatalogEntry | None:
    """Return one catalog entry by its stable persisted ID, or explicit absence."""

    _validate_catalog_exercise_id(catalog_exercise_id)
    ensure_exercise_catalog_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM exercise_catalog_exercises
        WHERE id = ?
        """,
        (catalog_exercise_id,),
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None

    cursor.execute(
        """
        SELECT equipment
        FROM exercise_equipment_requirements
        WHERE exercise_id = ?
        ORDER BY equipment
        """,
        (catalog_exercise_id,),
    )
    equipment_required = [
        equipment_row["equipment"] for equipment_row in cursor.fetchall()
    ]
    conn.close()
    return _row_to_catalog_entry(row, equipment_required)


def get_exercise_catalog() -> list[ExerciseCatalogEntry]:
    cache_key = _exercise_catalog_cache_key()
    cached_entries = _CATALOG_CACHE_BY_DB_PATH.get(cache_key)
    if cached_entries is not None:
        return list(cached_entries)

    seed_exercise_catalog()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM exercise_catalog_exercises
    ORDER BY id
    """)
    rows = cursor.fetchall()

    entries: list[ExerciseCatalogEntry] = []
    for row in rows:
        cursor.execute(
            """
            SELECT equipment
            FROM exercise_equipment_requirements
            WHERE exercise_id = ?
            ORDER BY equipment
            """,
            (row["id"],),
        )
        equipment_rows = cursor.fetchall()
        entries.append(
            _row_to_catalog_entry(
                row,
                [equipment_row["equipment"] for equipment_row in equipment_rows],
            )
        )

    conn.close()
    _CATALOG_CACHE_BY_DB_PATH[cache_key] = entries
    return list(entries)


def get_exercise_catalog_dicts() -> list[dict]:
    return [asdict(entry) for entry in get_exercise_catalog()]


def _equipment_allowed(
    equipment_required: list[str],
    available_equipment: list[str],
    unavailable_equipment: list[str],
) -> bool:
    required = set(_normalize_list(equipment_required))
    available = set(_normalize_list(available_equipment))
    unavailable = set(_normalize_list(unavailable_equipment))

    if required & unavailable:
        return False

    if available and not required.issubset(available):
        return False

    return True


def filter_exercises_for_equipment(
    available_equipment: list[str],
    unavailable_equipment: list[str] | None = None,
    movement_patterns: list[str] | None = None,
) -> list[ExerciseCatalogEntry]:
    patterns = set(_normalize_list(movement_patterns))
    unavailable_equipment = unavailable_equipment or []

    matches: list[ExerciseCatalogEntry] = []
    for entry in get_exercise_catalog():
        if patterns and _normalize_token(entry.movement_pattern) not in patterns:
            continue

        if _equipment_allowed(
            entry.equipment_required,
            available_equipment,
            unavailable_equipment,
        ):
            matches.append(entry)

    return matches


def find_catalog_entry_by_name(name: str) -> ExerciseCatalogEntry | None:
    normalized_name = _normalize_display_name(name)
    for entry in get_exercise_catalog():
        if _normalize_display_name(entry.name) == normalized_name:
            return entry
    return None
