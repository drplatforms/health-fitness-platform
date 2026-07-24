"""Build deterministic 24-week QA histories for users 106-108.

The command is deliberately conservative:

* ``--database`` must point at an existing, initialized database.
* the default mode is a read-only dry run;
* apply requires exact user-id confirmation;
* existing rows are replaced only after marker-based ownership proof; and
* all database writes happen on one connection in one transaction.

This module does not initialize schemas, seed reference catalogs, call an LLM,
or change production analytics/coaching behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

SEED_VERSION = "realistic_longitudinal_qa_v2"
SEED_MARKER = f"[{SEED_VERSION}]"
LEGACY_QA106_NAME = "Performance Studio Demo"
LEGACY_QA106_SCENARIO = "workout_performance_studio_qa_v1"
HISTORY_START = date(2026, 2, 5)
HISTORY_END = date(2026, 7, 23)
QA_USER_IDS = (106, 107, 108)
REQUIRED_CONFIRMATION = ",".join(str(user_id) for user_id in QA_USER_IDS)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DATABASE_PATH = (REPOSITORY_ROOT / "fitness_ai.db").resolve()
MANIFEST_FINALIZATION_EXIT_CODE = 3

LEGACY_QA106_END_DATE = date(2026, 7, 20)
LEGACY_QA106_SESSION_DAY_OFFSETS = (
    176,
    167,
    159,
    151,
    143,
    136,
    128,
    119,
    112,
    104,
    96,
    88,
    81,
    73,
    66,
    58,
    50,
    43,
    35,
    28,
    20,
    13,
    6,
    0,
)
LEGACY_QA106_BENCH_LOADS = (
    40.0,
    45.0,
    45.0,
    50.0,
    50.0,
    55.0,
    55.0,
    55.0,
    55.0,
    55.0,
    45.0,
    45.0,
    55.0,
    55.0,
    60.0,
    60.0,
    60.0,
    60.0,
    60.0,
    60.0,
    50.0,
    50.0,
    60.0,
    65.0,
)
LEGACY_QA106_BENCH_RIRS = (
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    3,
    3,
    None,
    2,
    3,
    2,
    1,
    1,
    4,
    4,
    3,
    2,
)

FailureHook = Callable[[str], None]

REQUIRED_SCHEMA: dict[str, set[str]] = {
    "users": {
        "id",
        "name",
        "gender",
        "age",
        "height_cm",
        "starting_weight",
        "goal_weight",
        "primary_goal",
        "activity_level",
        "created_at",
    },
    "daily_checkins": {
        "id",
        "user_id",
        "checkin_date",
        "body_weight",
        "sleep_hours",
        "sleep_quality",
        "energy_level",
        "soreness_level",
        "stress_level",
        "training_motivation",
        "pain_concern",
        "pain_area",
        "mood",
        "notes",
        "created_at",
    },
    "foods": {"id", "name"},
    "nutrients": {"id", "name", "unit"},
    "food_nutrients": {"food_id", "nutrient_id", "amount_per_100g"},
    "food_entries": {
        "id",
        "user_id",
        "food_id",
        "canonical_food_id",
        "food_name_snapshot",
        "grams",
        "meal_type",
        "notes",
        "calories",
        "protein_g",
        "carbs_g",
        "fat_g",
        "entry_date",
        "created_at",
    },
    "canonical_foods": {"id", "display_name", "active"},
    "canonical_food_nutrients": {
        "canonical_food_id",
        "nutrient_name",
        "nutrient_unit",
        "amount_per_100g",
    },
    "exercises": {"id", "name"},
    "exercise_catalog_exercises": {"id", "name"},
    "exercise_catalog_prescription_measurements": {
        "exercise_id",
        "default_measurement_type",
        "allowed_measurement_types_json",
    },
    "user_equipment_profiles": {
        "id",
        "user_id",
        "training_environment",
        "available_equipment_json",
        "unavailable_equipment_json",
        "created_at",
        "updated_at",
    },
    "workout_sessions": {
        "id",
        "user_id",
        "workout_date",
        "workout_name",
        "duration_minutes",
        "notes",
        "created_at",
    },
    "workout_sets": {
        "id",
        "workout_session_id",
        "exercise_id",
        "set_number",
        "reps",
        "weight",
        "rir",
        "created_at",
    },
    "workout_plan_instances": {
        "id",
        "user_id",
        "status",
        "scenario",
        "confidence",
        "title",
        "approved_workout_plan_json",
        "selected_at",
        "completed_at",
        "created_at",
        "updated_at",
    },
    "planned_workout_exercises": {
        "id",
        "workout_plan_instance_id",
        "exercise_order",
        "name",
        "sets",
        "measurement_type",
        "reps_min",
        "reps_max",
        "target_duration_seconds",
        "target_distance_meters",
        "rir_min",
        "rir_max",
        "notes",
        "equipment_required_json",
        "catalog_exercise_id",
        "created_at",
    },
    "workout_execution_sessions": {
        "id",
        "workout_plan_instance_id",
        "user_id",
        "status",
        "workout_session_id",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    },
    "workout_execution_set_actuals": {
        "id",
        "workout_execution_session_id",
        "planned_workout_exercise_id",
        "workout_session_id",
        "workout_set_id",
        "exercise_name",
        "set_number",
        "planned_reps_min",
        "planned_reps_max",
        "measurement_type",
        "planned_duration_seconds",
        "planned_distance_meters",
        "planned_rir_min",
        "planned_rir_max",
        "actual_reps",
        "actual_duration_seconds",
        "actual_distance_meters",
        "actual_weight",
        "actual_rir",
        "completed",
        "skipped",
        "notes",
        "created_at",
        "updated_at",
    },
}

ALLOWED_DIRECT_V2_TABLES = {
    "daily_checkins",
    "food_entries",
    "user_equipment_profiles",
    "workout_execution_sessions",
    "workout_plan_instances",
    "workout_sessions",
}
ALLOWED_DIRECT_LEGACY_QA106_TABLES = {
    "workout_execution_sessions",
    "workout_plan_instances",
}
ALLOWED_INDIRECT_RELATIONS = {
    (
        "planned_workout_exercises",
        "workout_plan_instance_id",
        "workout_plan_instances",
    ),
    (
        "workout_execution_sessions",
        "workout_plan_instance_id",
        "workout_plan_instances",
    ),
    (
        "workout_execution_sessions",
        "workout_session_id",
        "workout_sessions",
    ),
    (
        "workout_execution_set_actuals",
        "workout_execution_session_id",
        "workout_execution_sessions",
    ),
    (
        "workout_execution_set_actuals",
        "planned_workout_exercise_id",
        "planned_workout_exercises",
    ),
    (
        "workout_execution_set_actuals",
        "substitution_for_planned_exercise_id",
        "planned_workout_exercises",
    ),
    (
        "workout_execution_set_actuals",
        "workout_session_id",
        "workout_sessions",
    ),
    ("workout_execution_set_actuals", "workout_set_id", "workout_sets"),
    ("workout_sets", "workout_session_id", "workout_sessions"),
}
GLOBAL_REFERENCE_PARENT_TABLES = {
    "canonical_foods",
    "exercise_catalog_exercises",
    "exercises",
    "foods",
    "nutrients",
}

CANONICAL_FOOD_NAMES = (
    "Chicken Breast, Cooked, Skinless",
    "Greek Yogurt, Plain",
    "White Rice, Cooked",
    "Oats, Dry",
    "Banana",
    "Broccoli, Cooked",
    "Olive Oil",
    "Egg, Large",
)
MACRO_NUTRIENTS = ("Calories", "Protein", "Carbohydrate", "Fat")


@dataclass(frozen=True)
class Persona:
    user_id: int
    name: str
    latest_activity: date
    gender: str
    age: int
    height_cm: float
    starting_weight: float
    final_weight: float
    goal_weight: float
    primary_goal: str
    activity_level: str
    training_environment: str
    available_equipment: tuple[str, ...]
    unavailable_equipment: tuple[str, ...]
    intended_activities_per_week: int
    intended_weekdays: tuple[int, ...]
    story: str

    @property
    def scenario(self) -> str:
        return f"{SEED_VERSION}:qa{self.user_id}"


PERSONAS = (
    Persona(
        user_id=106,
        name="QA106 — Consistent Strength",
        latest_activity=date(2026, 7, 22),
        gender="Male",
        age=36,
        height_cm=178.0,
        starting_weight=182.0,
        final_weight=184.2,
        goal_weight=188.0,
        primary_goal="strength_progression",
        activity_level="moderate",
        training_environment="home_gym",
        available_equipment=(
            "adjustable_bench",
            "barbell",
            "bodyweight",
            "dumbbell",
            "exercise_ball",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
            "treadmill",
        ),
        unavailable_equipment=("cable", "machine", "rope_cable_attachment"),
        intended_activities_per_week=4,
        intended_weekdays=(0, 2, 4, 6),
        story=(
            "High but imperfect strength adherence with a plateau, temporary "
            "fatigue, a reduced-load deload, and a gradual rebound."
        ),
    ),
    Persona(
        user_id=107,
        name="QA107 — Interrupted Progress",
        latest_activity=date(2026, 7, 19),
        gender="Female",
        age=34,
        height_cm=168.0,
        starting_weight=176.0,
        final_weight=175.1,
        goal_weight=170.0,
        primary_goal="strength_and_recomposition",
        activity_level="light",
        training_environment="limited_equipment",
        available_equipment=(
            "adjustable_bench",
            "bodyweight",
            "dumbbell",
            "pull_up_bar",
            "resistance_band",
        ),
        unavailable_equipment=(
            "barbell",
            "bike",
            "cable",
            "machine",
            "plates",
            "rack",
            "treadmill",
        ),
        intended_activities_per_week=3,
        intended_weekdays=(1, 3, 6),
        story=(
            "Irregular strength attendance, a three-week interruption, momentum "
            "loss, and a cautious return with moderate evidence quality."
        ),
    ),
    Persona(
        user_id=108,
        name="QA108 — Mixed Modality",
        latest_activity=date(2026, 7, 23),
        gender="Non-binary",
        age=32,
        height_cm=173.0,
        starting_weight=168.0,
        final_weight=169.0,
        goal_weight=170.0,
        primary_goal="maintenance_and_performance",
        activity_level="active",
        training_environment="home_gym",
        available_equipment=(
            "adjustable_bench",
            "barbell",
            "bodyweight",
            "dumbbell",
            "exercise_ball",
            "plates",
            "pull_up_bar",
            "rack",
            "resistance_band",
            "treadmill",
        ),
        unavailable_equipment=("cable", "machine", "rope_cable_attachment"),
        intended_activities_per_week=5,
        intended_weekdays=(0, 1, 3, 4, 6),
        story=(
            "Strength, bodyweight, timed, distance, carry, and cardio work with "
            "fatigue accumulation, deliberate reduction, and resumed progress."
        ),
    ),
)
PERSONA_BY_ID = {persona.user_id: persona for persona in PERSONAS}

PHASE_WINDOWS: dict[int, tuple[tuple[str, date, date], ...]] = {
    106: (
        ("foundation", HISTORY_START, date(2026, 3, 1)),
        ("progression", date(2026, 3, 2), date(2026, 5, 3)),
        ("plateau_and_fatigue", date(2026, 5, 4), date(2026, 6, 7)),
        ("deload", date(2026, 6, 8), date(2026, 6, 21)),
        ("rebound", date(2026, 6, 22), HISTORY_END),
    ),
    107: (
        ("early_improvement", HISTORY_START, date(2026, 3, 22)),
        ("plateau", date(2026, 3, 23), date(2026, 5, 3)),
        ("interruption", date(2026, 5, 4), date(2026, 5, 24)),
        ("momentum_loss", date(2026, 5, 25), date(2026, 6, 14)),
        ("gradual_return", date(2026, 6, 15), HISTORY_END),
    ),
    108: (
        ("mixed_foundation", HISTORY_START, date(2026, 3, 15)),
        ("mixed_build", date(2026, 3, 16), date(2026, 5, 17)),
        ("fatigue_accumulation", date(2026, 5, 18), date(2026, 6, 7)),
        ("deliberate_reduction", date(2026, 6, 8), date(2026, 6, 21)),
        ("resumed_progress", date(2026, 6, 22), HISTORY_END),
    ),
}

CHECKPOINTS: dict[int, dict[str, str]] = {
    106: {
        "fatigue_recovery_limited": "2026-06-14",
        "deload_transition": "2026-06-21",
        "final_rebound": "2026-07-23",
    },
    107: {
        "interruption_start": "2026-05-04",
        "interruption_end": "2026-05-24",
        "renewed_activity": "2026-07-23",
    },
    108: {
        "fatigue_accumulation": "2026-06-07",
        "deliberate_reduction": "2026-06-14",
        "resumed_progress": "2026-07-23",
    },
}

EXERCISE_EQUIPMENT: dict[str, tuple[str, ...]] = {
    "Dumbbell Bench Press": ("dumbbell", "adjustable_bench"),
    "Goblet Squat": ("dumbbell",),
    "Romanian Deadlift": ("dumbbell",),
    "One-Arm Dumbbell Row": ("dumbbell", "adjustable_bench"),
    "Pull-Up": ("bodyweight", "pull_up_bar"),
    "Plank": ("bodyweight",),
    "Farmer Carry": ("dumbbell",),
    "Treadmill Walk": ("treadmill",),
}
EXERCISE_MODALITIES: dict[str, str] = {
    "Dumbbell Bench Press": "externally_weighted",
    "Goblet Squat": "externally_weighted",
    "Romanian Deadlift": "externally_weighted",
    "One-Arm Dumbbell Row": "externally_weighted",
    "Pull-Up": "bodyweight",
    "Plank": "timed",
    "Farmer Carry": "carry",
    "Treadmill Walk": "cardio",
}


@dataclass(frozen=True)
class ActualSet:
    set_number: int
    actual_reps: int | None = None
    actual_duration_seconds: int | None = None
    actual_distance_meters: float | None = None
    actual_weight: float | None = None
    actual_rir: int | None = None
    completed: bool = True
    skipped: bool = False


@dataclass(frozen=True)
class LegacyExerciseExpectation:
    name: str
    measurement_type: str
    planned_sets: int
    reps_min: int | None
    reps_max: int | None
    target_duration_seconds: int | None
    target_distance_meters: float | None
    equipment: tuple[str, ...]
    actuals: tuple[ActualSet, ...]


@dataclass(frozen=True)
class ExerciseLog:
    name: str
    measurement_type: str
    planned_sets: int
    reps_min: int | None
    reps_max: int | None
    target_duration_seconds: int | None
    target_distance_meters: float | None
    rir_min: int | None
    rir_max: int | None
    actuals: tuple[ActualSet, ...]


@dataclass(frozen=True)
class WorkoutLog:
    user_id: int
    workout_date: date
    title: str
    duration_minutes: int
    phase: str
    exercises: tuple[ExerciseLog, ...]
    partial_kind: str | None


@dataclass(frozen=True)
class RecoveryLog:
    user_id: int
    checkin_date: date
    body_weight: float | None
    sleep_hours: float
    sleep_quality: int
    energy_level: int
    soreness_level: int
    stress_level: int
    training_motivation: int
    mood: str
    phase: str


@dataclass(frozen=True)
class NutritionLog:
    user_id: int
    entry_date: date
    food_name: str
    grams: float
    meal_type: str
    completeness: str
    entry_index: int


@dataclass(frozen=True)
class SeedDataset:
    workouts: tuple[WorkoutLog, ...]
    recovery: tuple[RecoveryLog, ...]
    nutrition: tuple[NutritionLog, ...]
    intended_workout_counts: dict[int, int]


@dataclass(frozen=True)
class CanonicalFoodReference:
    canonical_food_id: int
    legacy_food_id: int
    display_name: str
    nutrients_per_100g: dict[str, float]


@dataclass(frozen=True)
class ResolvedReferences:
    catalog_exercise_ids: dict[str, int]
    legacy_exercise_ids: dict[str, int]
    canonical_foods: dict[str, CanonicalFoodReference]


@dataclass(frozen=True)
class OwnershipPlan:
    create_user_ids: tuple[int, ...]
    replace_user_ids: tuple[int, ...]
    migrate_legacy_106: bool

    @property
    def proposed_operation(self) -> str:
        parts: list[str] = []
        if self.create_user_ids:
            parts.append(
                "create " + ",".join(str(user_id) for user_id in self.create_user_ids)
            )
        if self.replace_user_ids:
            parts.append(
                "replace-owned "
                + ",".join(str(user_id) for user_id in self.replace_user_ids)
            )
        if self.migrate_legacy_106:
            parts.append("migrate recognized legacy 106")
        return "; ".join(parts) or "validate existing owned rows"


@dataclass(frozen=True)
class SeedRunResult:
    database_path: Path
    mode: str
    proposed_operation: str
    manifest: dict[str, Any]
    manifest_path: Path | None
    canonical_database: bool
    canonical_apply_authorized: bool
    database_committed: bool


@dataclass(frozen=True)
class StagedManifest:
    staged_path: Path
    final_path: Path


class ManifestFinalizationError(RuntimeError):
    """Report a committed database whose staged manifest was not published."""

    exit_code = MANIFEST_FINALIZATION_EXIT_CODE
    database_committed = True

    def __init__(
        self,
        *,
        staged_path: Path,
        final_path: Path,
        cause: OSError,
    ) -> None:
        self.staged_path = staged_path
        self.final_path = final_path
        self.cause = cause
        super().__init__(
            "DATABASE COMMITTED; MANIFEST FINALIZATION FAILED: "
            f"staged={staged_path}; final={final_path}; error={cause}"
        )


def _daterange(start: date, end: date) -> Iterable[date]:
    for day_offset in range((end - start).days + 1):
        yield start + timedelta(days=day_offset)


def _timestamp(day: date, hour: int, minute: int = 0) -> str:
    return datetime.combine(
        day,
        time(hour=hour, minute=minute),
        tzinfo=UTC,
    ).isoformat()


def _phase_for(user_id: int, target_date: date) -> str:
    for phase, start, end in PHASE_WINDOWS[user_id]:
        if start <= target_date <= end:
            return phase
    raise ValueError(f"No phase is defined for user {user_id} on {target_date}.")


def _week_index(day: date) -> int:
    return max(0, (day - HISTORY_START).days // 7)


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _strength_load(
    user_id: int,
    day: date,
    *,
    exercise_offset: float = 0.0,
) -> float:
    week = _week_index(day)
    phase = _phase_for(user_id, day)
    if user_id == 106:
        if phase == "foundation":
            load = 40.0 + min(10.0, (week // 2) * 5.0)
        elif phase == "progression":
            load = 50.0 + min(15.0, ((week - 4) // 2) * 5.0)
        elif phase == "plateau_and_fatigue":
            load = 65.0
        elif phase == "deload":
            load = 50.0 if week % 2 == 0 else 52.5
        else:
            rebound = (55.0, 60.0, 62.5, 65.0, 67.5)
            load = rebound[min(len(rebound) - 1, max(0, week - 19))]
    elif user_id == 107:
        if phase == "early_improvement":
            load = (35.0, 40.0, 45.0, 45.0, 50.0, 50.0, 50.0)[min(6, week)]
        elif phase == "plateau":
            load = 50.0
        elif phase == "momentum_loss":
            load = 42.5 if week % 2 == 0 else 45.0
        elif phase == "gradual_return":
            return_steps = (42.5, 45.0, 45.0, 47.5, 50.0, 50.0)
            load = return_steps[min(len(return_steps) - 1, max(0, week - 18))]
        else:
            load = 42.5
    else:
        if phase == "mixed_foundation":
            load = 35.0 + min(10.0, (week // 2) * 5.0)
        elif phase == "mixed_build":
            load = 45.0 + min(15.0, ((week - 5) // 2) * 5.0)
        elif phase == "fatigue_accumulation":
            load = 60.0
        elif phase == "deliberate_reduction":
            load = 47.5
        else:
            resumed = (50.0, 52.5, 55.0, 57.5, 60.0)
            load = resumed[min(len(resumed) - 1, max(0, week - 19))]
    return round(load + exercise_offset, 1)


def _rir_for(user_id: int, day: date, workout_index: int, set_index: int) -> int:
    phase = _phase_for(user_id, day)
    if phase in {"plateau_and_fatigue", "fatigue_accumulation"}:
        values = (1, 1, 2)
    elif phase in {"deload", "deliberate_reduction"}:
        values = (4, 3, 4)
    elif phase in {"momentum_loss", "gradual_return"}:
        values = (3, 2, 3)
    else:
        values = (3, 2, 2)
    return values[(workout_index + set_index) % len(values)]


def _reps_exercise(
    *,
    user_id: int,
    day: date,
    workout_index: int,
    name: str,
    load: float | None,
    reps: int,
    planned_sets: int = 3,
    reps_min: int | None = None,
    reps_max: int | None = None,
) -> ExerciseLog:
    resolved_min = reps_min if reps_min is not None else max(1, reps - 2)
    resolved_max = reps_max if reps_max is not None else reps
    actuals: list[ActualSet] = []
    for set_index in range(planned_sets):
        actual_rir: int | None = _rir_for(user_id, day, workout_index, set_index)
        if (workout_index * 3 + set_index + user_id) % 17 == 0:
            actual_rir = None
        actuals.append(
            ActualSet(
                set_number=set_index + 1,
                actual_reps=max(1, reps - (1 if set_index == planned_sets - 1 else 0)),
                actual_weight=load,
                actual_rir=actual_rir,
            )
        )
    return ExerciseLog(
        name=name,
        measurement_type="reps",
        planned_sets=planned_sets,
        reps_min=resolved_min,
        reps_max=resolved_max,
        target_duration_seconds=None,
        target_distance_meters=None,
        rir_min=1,
        rir_max=4,
        actuals=tuple(actuals),
    )


def _duration_exercise(
    *,
    name: str,
    target_seconds: int,
    planned_sets: int,
) -> ExerciseLog:
    actuals = tuple(
        ActualSet(
            set_number=set_index + 1,
            actual_duration_seconds=target_seconds + (set_index % 2) * 5,
        )
        for set_index in range(planned_sets)
    )
    return ExerciseLog(
        name=name,
        measurement_type="duration",
        planned_sets=planned_sets,
        reps_min=None,
        reps_max=None,
        target_duration_seconds=target_seconds,
        target_distance_meters=None,
        rir_min=None,
        rir_max=None,
        actuals=actuals,
    )


def _distance_exercise(
    *,
    name: str,
    target_meters: float,
    load: float | None,
    planned_sets: int,
) -> ExerciseLog:
    actuals = tuple(
        ActualSet(
            set_number=set_index + 1,
            actual_distance_meters=target_meters + (5.0 if set_index == 2 else 0.0),
            actual_weight=load,
        )
        for set_index in range(planned_sets)
    )
    return ExerciseLog(
        name=name,
        measurement_type="distance",
        planned_sets=planned_sets,
        reps_min=None,
        reps_max=None,
        target_duration_seconds=None,
        target_distance_meters=target_meters,
        rir_min=None,
        rir_max=None,
        actuals=actuals,
    )


def _partial_kind(user_id: int, workout_index: int) -> str | None:
    cadence = {106: 13, 107: 5, 108: 11}[user_id]
    value = workout_index % cadence
    if value == 2:
        return "explicit_skip"
    if value == cadence - 2:
        return "unlogged_set"
    return None


def _apply_partial(
    exercises: tuple[ExerciseLog, ...],
    partial_kind: str | None,
) -> tuple[ExerciseLog, ...]:
    if partial_kind is None or not exercises:
        return exercises
    last = exercises[-1]
    if not last.actuals:
        return exercises
    if partial_kind == "explicit_skip":
        kept_count = 0 if len(last.actuals) == 1 else max(1, len(last.actuals) - 2)
        kept = list(last.actuals[:kept_count])
        skipped_number = min(last.planned_sets, len(kept) + 1)
        kept.append(
            ActualSet(
                set_number=skipped_number,
                completed=False,
                skipped=True,
            )
        )
        replacement = replace(last, actuals=tuple(kept))
    else:
        replacement = replace(last, actuals=last.actuals[:-1])
    return (*exercises[:-1], replacement)


def _qa106_workout(
    day: date, workout_index: int
) -> tuple[str, int, tuple[ExerciseLog, ...]]:
    phase = _phase_for(106, day)
    planned_sets = 2 if phase == "deload" else 3
    anchor_load = _strength_load(106, day)
    if day.weekday() == 0:
        title = "Upper Strength Practice"
        exercises = (
            _reps_exercise(
                user_id=106,
                day=day,
                workout_index=workout_index,
                name="Dumbbell Bench Press",
                load=anchor_load,
                reps=10,
                planned_sets=planned_sets,
            ),
            _reps_exercise(
                user_id=106,
                day=day,
                workout_index=workout_index,
                name="One-Arm Dumbbell Row",
                load=_strength_load(106, day, exercise_offset=10.0),
                reps=10,
                planned_sets=planned_sets,
            ),
        )
    elif day.weekday() == 2:
        title = "Lower Strength Practice"
        exercises = (
            _reps_exercise(
                user_id=106,
                day=day,
                workout_index=workout_index,
                name="Goblet Squat",
                load=_strength_load(106, day, exercise_offset=5.0),
                reps=10,
                planned_sets=planned_sets,
            ),
            _reps_exercise(
                user_id=106,
                day=day,
                workout_index=workout_index,
                name="Romanian Deadlift",
                load=_strength_load(106, day, exercise_offset=20.0),
                reps=9,
                planned_sets=planned_sets,
            ),
        )
    elif day.weekday() == 4:
        title = "Upper Strength Progression"
        pull_up_reps = min(10, 6 + _week_index(day) // 6)
        exercises = (
            _reps_exercise(
                user_id=106,
                day=day,
                workout_index=workout_index,
                name="Dumbbell Bench Press",
                load=anchor_load,
                reps=9,
                planned_sets=planned_sets,
            ),
            _reps_exercise(
                user_id=106,
                day=day,
                workout_index=workout_index,
                name="Pull-Up",
                load=None,
                reps=pull_up_reps,
                planned_sets=planned_sets,
                reps_min=max(1, pull_up_reps - 2),
                reps_max=pull_up_reps,
            ),
        )
    else:
        title = "Posterior Strength and Core"
        plank_seconds = 35 if phase == "deload" else 45 + min(15, _week_index(day))
        exercises = (
            _reps_exercise(
                user_id=106,
                day=day,
                workout_index=workout_index,
                name="Romanian Deadlift",
                load=_strength_load(106, day, exercise_offset=20.0),
                reps=8,
                planned_sets=planned_sets,
            ),
            _duration_exercise(
                name="Plank",
                target_seconds=(plank_seconds // 5) * 5,
                planned_sets=planned_sets,
            ),
        )
    return title, 50 if planned_sets == 3 else 40, exercises


def _qa107_workout(
    day: date, workout_index: int
) -> tuple[str, int, tuple[ExerciseLog, ...]]:
    anchor_load = _strength_load(107, day)
    if day.weekday() == 1:
        title = "Upper Strength Return"
        exercises = (
            _reps_exercise(
                user_id=107,
                day=day,
                workout_index=workout_index,
                name="Dumbbell Bench Press",
                load=anchor_load,
                reps=9,
            ),
            _reps_exercise(
                user_id=107,
                day=day,
                workout_index=workout_index,
                name="One-Arm Dumbbell Row",
                load=anchor_load + 10.0,
                reps=10,
            ),
        )
    elif day.weekday() == 3:
        title = "Lower Strength Return"
        exercises = (
            _reps_exercise(
                user_id=107,
                day=day,
                workout_index=workout_index,
                name="Goblet Squat",
                load=anchor_load + 5.0,
                reps=10,
            ),
            _reps_exercise(
                user_id=107,
                day=day,
                workout_index=workout_index,
                name="Romanian Deadlift",
                load=anchor_load + 20.0,
                reps=8,
            ),
        )
    else:
        title = "Manageable Full Body Practice"
        exercises = (
            _reps_exercise(
                user_id=107,
                day=day,
                workout_index=workout_index,
                name="Dumbbell Bench Press",
                load=anchor_load,
                reps=8,
            ),
            _reps_exercise(
                user_id=107,
                day=day,
                workout_index=workout_index,
                name="Pull-Up",
                load=None,
                reps=min(8, 4 + _week_index(day) // 8),
                reps_min=3,
                reps_max=8,
            ),
        )
    return title, 45, exercises


def _qa108_workout(
    day: date, workout_index: int
) -> tuple[str, int, tuple[ExerciseLog, ...]]:
    week = _week_index(day)
    phase = _phase_for(108, day)
    reduction = phase == "deliberate_reduction"
    if day.weekday() == 0:
        title = "Mixed Strength A"
        exercises = (
            _reps_exercise(
                user_id=108,
                day=day,
                workout_index=workout_index,
                name="Dumbbell Bench Press",
                load=_strength_load(108, day),
                reps=10,
                planned_sets=2 if reduction else 3,
            ),
            _reps_exercise(
                user_id=108,
                day=day,
                workout_index=workout_index,
                name="Goblet Squat",
                load=_strength_load(108, day, exercise_offset=10.0),
                reps=10,
                planned_sets=2 if reduction else 3,
            ),
        )
        duration = 50
    elif day.weekday() == 1:
        title = "Steady Conditioning"
        if reduction:
            seconds = 900
        else:
            seconds = min(1800, 900 + (week // 2) * 60)
        exercises = (
            _duration_exercise(
                name="Treadmill Walk",
                target_seconds=seconds,
                planned_sets=1,
            ),
        )
        duration = max(20, seconds // 60 + 5)
    elif day.weekday() == 3:
        title = "Bodyweight and Core"
        pull_up_reps = 6 if reduction else min(11, 5 + week // 4)
        plank_seconds = 35 if reduction else min(75, 35 + (week // 2) * 5)
        exercises = (
            _reps_exercise(
                user_id=108,
                day=day,
                workout_index=workout_index,
                name="Pull-Up",
                load=None,
                reps=pull_up_reps,
                reps_min=max(1, pull_up_reps - 2),
                reps_max=pull_up_reps,
            ),
            _duration_exercise(
                name="Plank",
                target_seconds=plank_seconds,
                planned_sets=3,
            ),
        )
        duration = 35
    elif day.weekday() == 4:
        title = "Loaded Carry Conditioning"
        distance_meters = 25.0 if reduction else min(45.0, 20.0 + (week // 4) * 5.0)
        carry_load = 40.0 if reduction else min(60.0, 35.0 + (week // 4) * 5.0)
        exercises = (
            _distance_exercise(
                name="Farmer Carry",
                target_meters=distance_meters,
                load=carry_load,
                planned_sets=3,
            ),
        )
        duration = 30
    else:
        title = "Mixed Strength B"
        exercises = (
            _reps_exercise(
                user_id=108,
                day=day,
                workout_index=workout_index,
                name="Romanian Deadlift",
                load=_strength_load(108, day, exercise_offset=20.0),
                reps=8,
                planned_sets=2 if reduction else 3,
            ),
            _reps_exercise(
                user_id=108,
                day=day,
                workout_index=workout_index,
                name="One-Arm Dumbbell Row",
                load=_strength_load(108, day, exercise_offset=10.0),
                reps=10,
                planned_sets=2 if reduction else 3,
            ),
        )
        duration = 50
    return title, duration, exercises


def _should_omit_workout(
    persona: Persona,
    day: date,
    candidate_index: int,
) -> bool:
    if day == persona.latest_activity:
        return False
    phase = _phase_for(persona.user_id, day)
    if persona.user_id == 106:
        return candidate_index % 13 == 4 or (
            phase == "plateau_and_fatigue" and candidate_index % 9 == 6
        )
    if persona.user_id == 107:
        if phase == "interruption":
            return True
        return candidate_index % 4 == 1 or candidate_index % 11 == 7
    return candidate_index % 19 == 8 or (
        phase == "fatigue_accumulation" and candidate_index % 13 == 4
    )


def _build_workouts() -> tuple[tuple[WorkoutLog, ...], dict[int, int]]:
    workouts: list[WorkoutLog] = []
    intended_counts: dict[int, int] = {}
    builders = {106: _qa106_workout, 107: _qa107_workout, 108: _qa108_workout}
    for persona in PERSONAS:
        candidates = [
            day
            for day in _daterange(HISTORY_START, persona.latest_activity)
            if day.weekday() in persona.intended_weekdays
        ]
        intended_counts[persona.user_id] = len(candidates)
        recorded_index = 0
        for candidate_index, day in enumerate(candidates):
            if _should_omit_workout(persona, day, candidate_index):
                continue
            title, duration_minutes, exercises = builders[persona.user_id](
                day,
                recorded_index,
            )
            partial_kind = _partial_kind(persona.user_id, recorded_index)
            workouts.append(
                WorkoutLog(
                    user_id=persona.user_id,
                    workout_date=day,
                    title=title,
                    duration_minutes=duration_minutes,
                    phase=_phase_for(persona.user_id, day),
                    exercises=_apply_partial(exercises, partial_kind),
                    partial_kind=partial_kind,
                )
            )
            recorded_index += 1
    return tuple(workouts), intended_counts


def _should_seed_recovery(persona: Persona, day: date, day_index: int) -> bool:
    if day == persona.latest_activity:
        return True
    phase = _phase_for(persona.user_id, day)
    if persona.user_id == 106:
        return day.weekday() != 1 and day_index % 17 != 5
    if persona.user_id == 107:
        if phase == "interruption":
            return day.weekday() in {2, 6}
        return day.weekday() in {0, 2, 4, 6} and day_index % 11 != 3
    return day.weekday() != 2 and day_index % 23 != 6


def _recovery_base(persona: Persona, day: date) -> tuple[float, int, int]:
    phase = _phase_for(persona.user_id, day)
    if persona.user_id == 106:
        values = {
            "foundation": (7.3, 7, 3),
            "progression": (7.1, 7, 4),
            "plateau_and_fatigue": (6.2, 5, 6),
            "rebound": (7.5, 8, 3),
        }
        if phase == "deload" and day <= date(2026, 6, 14):
            return 5.9, 4, 7
        if phase == "deload":
            return 7.2, 7, 4
        return values[phase]
    if persona.user_id == 107:
        values = {
            "early_improvement": (6.8, 6, 4),
            "plateau": (6.4, 5, 5),
            "interruption": (6.0, 5, 5),
            "momentum_loss": (6.3, 5, 5),
            "gradual_return": (6.9, 6, 4),
        }
        return values[phase]
    values = {
        "mixed_foundation": (7.2, 7, 3),
        "mixed_build": (7.0, 7, 4),
        "fatigue_accumulation": (6.1, 5, 6),
        "deliberate_reduction": (7.2, 7, 4),
        "resumed_progress": (7.5, 8, 3),
    }
    return values[phase]


def _weight_for(persona: Persona, day: date, weigh_in_index: int) -> float:
    total_days = max(1, (persona.latest_activity - HISTORY_START).days)
    progress = (day - HISTORY_START).days / total_days
    noise = (-0.2, 0.1, 0.3, -0.1, 0.2, 0.0, -0.3)[weigh_in_index % 7]
    return round(
        persona.starting_weight
        + (persona.final_weight - persona.starting_weight) * progress
        + noise,
        1,
    )


def _build_recovery() -> tuple[RecoveryLog, ...]:
    rows: list[RecoveryLog] = []
    for persona in PERSONAS:
        inserted_index = 0
        weigh_in_index = 0
        for day_index, day in enumerate(
            _daterange(HISTORY_START, persona.latest_activity)
        ):
            if not _should_seed_recovery(persona, day, day_index):
                continue
            base_sleep, base_energy, base_soreness = _recovery_base(persona, day)
            sleep_variation = (-0.2, 0.1, 0.0, 0.3, -0.1)[
                (day_index + persona.user_id) % 5
            ]
            energy_variation = (-1, 0, 1, 0, 0, -1)[day_index % 6]
            soreness_variation = (0, 1, 0, -1, 0, 1, 0)[day_index % 7]
            body_weight: float | None = None
            if inserted_index % 3 == 0 or day == persona.latest_activity:
                body_weight = _weight_for(persona, day, weigh_in_index)
                weigh_in_index += 1
            energy = _clamp_int(base_energy + energy_variation, 1, 10)
            soreness = _clamp_int(base_soreness + soreness_variation, 1, 10)
            sleep_quality = _clamp_int(round((base_sleep + sleep_variation) / 2), 1, 5)
            stress_level = _clamp_int(
                2 + (1 if energy <= 5 else 0) + (day_index % 9 == 0),
                1,
                5,
            )
            motivation = _clamp_int(
                4 - (1 if soreness >= 6 else 0) + (day_index % 10 == 0),
                1,
                5,
            )
            mood = "steady"
            if energy <= 5:
                mood = "tired"
            elif energy >= 8:
                mood = "energized"
            rows.append(
                RecoveryLog(
                    user_id=persona.user_id,
                    checkin_date=day,
                    body_weight=body_weight,
                    sleep_hours=round(base_sleep + sleep_variation, 1),
                    sleep_quality=sleep_quality,
                    energy_level=energy,
                    soreness_level=soreness,
                    stress_level=stress_level,
                    training_motivation=motivation,
                    mood=mood,
                    phase=_phase_for(persona.user_id, day),
                )
            )
            inserted_index += 1
    return tuple(rows)


NutritionMenu = tuple[tuple[str, float, str], ...]

COMPLETE_MENUS: dict[int, tuple[NutritionMenu, ...]] = {
    106: (
        (
            ("Oats, Dry", 100.0, "breakfast"),
            ("Egg, Large", 180.0, "breakfast"),
            ("Banana", 160.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 320.0, "lunch"),
            ("White Rice, Cooked", 650.0, "lunch"),
            ("Broccoli, Cooked", 240.0, "dinner"),
            ("Olive Oil", 25.0, "dinner"),
            ("Greek Yogurt, Plain", 350.0, "snack"),
        ),
        (
            ("Oats, Dry", 115.0, "breakfast"),
            ("Banana", 180.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 380.0, "lunch"),
            ("White Rice, Cooked", 720.0, "lunch"),
            ("Broccoli, Cooked", 220.0, "dinner"),
            ("Olive Oil", 30.0, "dinner"),
            ("Greek Yogurt, Plain", 450.0, "snack"),
        ),
        (
            ("Oats, Dry", 110.0, "breakfast"),
            ("Egg, Large", 220.0, "breakfast"),
            ("Banana", 150.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 350.0, "lunch"),
            ("White Rice, Cooked", 700.0, "lunch"),
            ("Broccoli, Cooked", 250.0, "dinner"),
            ("Olive Oil", 30.0, "dinner"),
        ),
        (
            ("Oats, Dry", 120.0, "breakfast"),
            ("Egg, Large", 200.0, "breakfast"),
            ("Chicken Breast, Cooked, Skinless", 360.0, "lunch"),
            ("White Rice, Cooked", 740.0, "lunch"),
            ("Broccoli, Cooked", 230.0, "dinner"),
            ("Olive Oil", 28.0, "dinner"),
            ("Greek Yogurt, Plain", 400.0, "snack"),
        ),
        (
            ("Oats, Dry", 105.0, "breakfast"),
            ("Egg, Large", 190.0, "breakfast"),
            ("Banana", 200.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 340.0, "lunch"),
            ("White Rice, Cooked", 680.0, "lunch"),
            ("Olive Oil", 27.0, "dinner"),
            ("Greek Yogurt, Plain", 420.0, "snack"),
        ),
        (
            ("Oats, Dry", 95.0, "breakfast"),
            ("Egg, Large", 170.0, "breakfast"),
            ("Banana", 140.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 300.0, "lunch"),
            ("White Rice, Cooked", 620.0, "lunch"),
            ("Broccoli, Cooked", 260.0, "dinner"),
            ("Olive Oil", 24.0, "dinner"),
            ("Greek Yogurt, Plain", 380.0, "snack"),
        ),
    ),
    107: (
        (
            ("Oats, Dry", 75.0, "breakfast"),
            ("Egg, Large", 150.0, "breakfast"),
            ("Banana", 120.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 240.0, "lunch"),
            ("White Rice, Cooked", 400.0, "lunch"),
            ("Broccoli, Cooked", 180.0, "dinner"),
            ("Olive Oil", 18.0, "dinner"),
            ("Greek Yogurt, Plain", 250.0, "snack"),
        ),
        (
            ("Oats, Dry", 90.0, "breakfast"),
            ("Banana", 180.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 280.0, "lunch"),
            ("White Rice, Cooked", 500.0, "lunch"),
            ("Broccoli, Cooked", 200.0, "dinner"),
            ("Olive Oil", 22.0, "dinner"),
            ("Greek Yogurt, Plain", 350.0, "snack"),
        ),
        (
            ("Oats, Dry", 80.0, "breakfast"),
            ("Egg, Large", 180.0, "breakfast"),
            ("Banana", 140.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 260.0, "lunch"),
            ("White Rice, Cooked", 450.0, "lunch"),
            ("Broccoli, Cooked", 160.0, "dinner"),
            ("Olive Oil", 20.0, "dinner"),
        ),
        (
            ("Oats, Dry", 100.0, "breakfast"),
            ("Egg, Large", 180.0, "breakfast"),
            ("Banana", 180.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 300.0, "lunch"),
            ("White Rice, Cooked", 550.0, "lunch"),
            ("Broccoli, Cooked", 220.0, "dinner"),
            ("Olive Oil", 24.0, "dinner"),
            ("Greek Yogurt, Plain", 300.0, "snack"),
        ),
    ),
    108: (
        (
            ("Oats, Dry", 95.0, "breakfast"),
            ("Egg, Large", 180.0, "breakfast"),
            ("Banana", 200.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 300.0, "lunch"),
            ("White Rice, Cooked", 600.0, "lunch"),
            ("Broccoli, Cooked", 220.0, "dinner"),
            ("Olive Oil", 22.0, "dinner"),
            ("Greek Yogurt, Plain", 350.0, "snack"),
        ),
        (
            ("Oats, Dry", 110.0, "breakfast"),
            ("Banana", 220.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 340.0, "lunch"),
            ("White Rice, Cooked", 700.0, "lunch"),
            ("Broccoli, Cooked", 250.0, "dinner"),
            ("Olive Oil", 26.0, "dinner"),
            ("Greek Yogurt, Plain", 450.0, "snack"),
        ),
        (
            ("Oats, Dry", 105.0, "breakfast"),
            ("Egg, Large", 220.0, "breakfast"),
            ("Banana", 200.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 320.0, "lunch"),
            ("White Rice, Cooked", 680.0, "lunch"),
            ("Broccoli, Cooked", 240.0, "dinner"),
            ("Olive Oil", 25.0, "dinner"),
        ),
        (
            ("Oats, Dry", 115.0, "breakfast"),
            ("Egg, Large", 200.0, "breakfast"),
            ("Chicken Breast, Cooked, Skinless", 350.0, "lunch"),
            ("White Rice, Cooked", 720.0, "lunch"),
            ("Broccoli, Cooked", 260.0, "dinner"),
            ("Olive Oil", 28.0, "dinner"),
            ("Greek Yogurt, Plain", 400.0, "snack"),
        ),
        (
            ("Oats, Dry", 100.0, "breakfast"),
            ("Egg, Large", 190.0, "breakfast"),
            ("Banana", 240.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 330.0, "lunch"),
            ("White Rice, Cooked", 740.0, "lunch"),
            ("Olive Oil", 25.0, "dinner"),
            ("Greek Yogurt, Plain", 380.0, "snack"),
        ),
        (
            ("Oats, Dry", 90.0, "breakfast"),
            ("Egg, Large", 170.0, "breakfast"),
            ("Banana", 180.0, "snack"),
            ("Chicken Breast, Cooked, Skinless", 290.0, "lunch"),
            ("White Rice, Cooked", 620.0, "lunch"),
            ("Broccoli, Cooked", 200.0, "dinner"),
            ("Olive Oil", 23.0, "dinner"),
            ("Greek Yogurt, Plain", 330.0, "snack"),
        ),
    ),
}

PARTIAL_MENUS: dict[int, tuple[NutritionMenu, ...]] = {
    106: (
        (("Greek Yogurt, Plain", 250.0, "snack"),),
        (("Oats, Dry", 80.0, "breakfast"),),
        (("Chicken Breast, Cooked, Skinless", 150.0, "lunch"),),
    ),
    107: (
        (("Banana", 120.0, "snack"),),
        (("Greek Yogurt, Plain", 180.0, "snack"),),
        (("White Rice, Cooked", 180.0, "lunch"),),
        (("Egg, Large", 100.0, "breakfast"),),
    ),
    108: (
        (("Banana", 150.0, "snack"),),
        (("Greek Yogurt, Plain", 220.0, "snack"),),
        (("Oats, Dry", 70.0, "breakfast"),),
    ),
}


def _nutrition_completeness(
    persona: Persona,
    day: date,
    day_index: int,
) -> str:
    if day == persona.latest_activity:
        return "complete"
    phase = _phase_for(persona.user_id, day)
    if persona.user_id == 106:
        if day.weekday() not in {0, 1, 2, 4, 5}:
            return "none"
        return "partial" if day_index % 17 == 6 else "complete"
    if persona.user_id == 107:
        if phase == "interruption":
            return "partial" if day.weekday() == 6 else "none"
        if day.weekday() not in {1, 3, 6}:
            return "none"
        return "partial" if day_index % 3 == 0 else "complete"
    if day.weekday() == 2:
        return "none"
    return "partial" if day_index % 19 == 5 else "complete"


def _nutrition_scale(
    persona: Persona,
    *,
    phase: str,
    is_training_day: bool,
) -> float:
    if persona.user_id == 106:
        if phase == "deload":
            return 0.94
        if phase == "rebound" and is_training_day:
            return 1.06
        return 1.04 if is_training_day else 0.96
    if persona.user_id == 107:
        if phase == "interruption":
            return 0.88
        if phase == "momentum_loss":
            return 0.92 if is_training_day else 0.88
        return 1.03 if is_training_day else 0.94
    if phase == "deliberate_reduction":
        return 0.94
    return 1.08 if is_training_day else 0.94


def _scaled_menu(
    menu: NutritionMenu,
    *,
    scale: float,
) -> NutritionMenu:
    scaled: list[tuple[str, float, str]] = []
    for food_name, grams, meal_type in menu:
        portion_increment = 1.0 if food_name == "Olive Oil" else 5.0
        scaled_grams = round((grams * scale) / portion_increment) * portion_increment
        scaled.append((food_name, float(scaled_grams), meal_type))
    return tuple(scaled)


def _build_nutrition(
    workouts: tuple[WorkoutLog, ...],
) -> tuple[NutritionLog, ...]:
    entries: list[NutritionLog] = []
    workout_dates = {
        persona.user_id: {
            workout.workout_date
            for workout in workouts
            if workout.user_id == persona.user_id
        }
        for persona in PERSONAS
    }
    for persona in PERSONAS:
        for day_index, day in enumerate(
            _daterange(HISTORY_START, persona.latest_activity)
        ):
            completeness = _nutrition_completeness(persona, day, day_index)
            if completeness == "none":
                continue
            phase = _phase_for(persona.user_id, day)
            is_training_day = day in workout_dates[persona.user_id]
            if completeness == "complete":
                templates = COMPLETE_MENUS[persona.user_id]
                template_index = (
                    day_index + day.weekday() * 2 + persona.user_id
                ) % len(templates)
                scale = _nutrition_scale(
                    persona,
                    phase=phase,
                    is_training_day=is_training_day,
                )
                menu = _scaled_menu(
                    templates[template_index],
                    scale=scale,
                )
            else:
                templates = PARTIAL_MENUS[persona.user_id]
                menu = templates[(day_index + persona.user_id) % len(templates)]
            for entry_index, (food_name, grams, meal_type) in enumerate(menu):
                entries.append(
                    NutritionLog(
                        user_id=persona.user_id,
                        entry_date=day,
                        food_name=food_name,
                        grams=grams,
                        meal_type=meal_type,
                        completeness=completeness,
                        entry_index=entry_index,
                    )
                )
    return tuple(entries)


def build_seed_dataset() -> SeedDataset:
    workouts, intended_counts = _build_workouts()
    return SeedDataset(
        workouts=workouts,
        recovery=_build_recovery(),
        nutrition=_build_nutrition(workouts),
        intended_workout_counts=intended_counts,
    )


def _workouts_for(dataset: SeedDataset, user_id: int) -> list[WorkoutLog]:
    return [workout for workout in dataset.workouts if workout.user_id == user_id]


def _recovery_for(dataset: SeedDataset, user_id: int) -> list[RecoveryLog]:
    return [row for row in dataset.recovery if row.user_id == user_id]


def _nutrition_for(dataset: SeedDataset, user_id: int) -> list[NutritionLog]:
    return [row for row in dataset.nutrition if row.user_id == user_id]


def _expected_counts(dataset: SeedDataset, user_id: int) -> dict[str, int]:
    workouts = _workouts_for(dataset, user_id)
    recovery = _recovery_for(dataset, user_id)
    nutrition = _nutrition_for(dataset, user_id)
    planned_exercises = sum(len(workout.exercises) for workout in workouts)
    actuals = sum(
        len(exercise.actuals) for workout in workouts for exercise in workout.exercises
    )
    legacy_sets = sum(
        1
        for workout in workouts
        for exercise in workout.exercises
        for actual in exercise.actuals
        if (
            exercise.measurement_type == "reps"
            and actual.completed
            and not actual.skipped
            and actual.actual_reps is not None
        )
    )
    return {
        "daily_checkins": len(recovery),
        "food_entries": len(nutrition),
        "user_equipment_profiles": 1,
        "workout_plan_instances": len(workouts),
        "workout_execution_sessions": len(workouts),
        "workout_sessions": len(workouts),
        "planned_workout_exercises": planned_exercises,
        "workout_execution_set_actuals": actuals,
        "workout_sets": legacy_sets,
    }


def _exercise_patterns(workouts: list[WorkoutLog]) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    names = sorted(
        {exercise.name for workout in workouts for exercise in workout.exercises}
    )
    for name in names:
        matching = [
            (workout, exercise)
            for workout in workouts
            for exercise in workout.exercises
            if exercise.name == name
        ]
        metrics: list[float] = []
        loads: list[float] = []
        for _workout, exercise in matching:
            for actual in exercise.actuals:
                if (
                    exercise.measurement_type == "reps"
                    and actual.actual_reps is not None
                ):
                    metrics.append(float(actual.actual_reps))
                elif (
                    exercise.measurement_type == "duration"
                    and actual.actual_duration_seconds is not None
                ):
                    metrics.append(float(actual.actual_duration_seconds))
                elif (
                    exercise.measurement_type == "distance"
                    and actual.actual_distance_meters is not None
                ):
                    metrics.append(float(actual.actual_distance_meters))
                if actual.actual_weight is not None:
                    loads.append(float(actual.actual_weight))
        patterns.append(
            {
                "exercise_name": name,
                "modality": EXERCISE_MODALITIES[name],
                "measurement_type": matching[0][1].measurement_type,
                "session_count": len(matching),
                "metric_min": min(metrics) if metrics else None,
                "metric_max": max(metrics) if metrics else None,
                "load_min_lb": min(loads) if loads else None,
                "load_max_lb": max(loads) if loads else None,
            }
        )
    return patterns


def _persona_manifest(dataset: SeedDataset, persona: Persona) -> dict[str, Any]:
    workouts = _workouts_for(dataset, persona.user_id)
    recovery = _recovery_for(dataset, persona.user_id)
    nutrition = _nutrition_for(dataset, persona.user_id)
    nutrition_days = sorted({row.entry_date for row in nutrition})
    complete_days = {
        row.entry_date for row in nutrition if row.completeness == "complete"
    }
    partial_days = {
        row.entry_date for row in nutrition if row.completeness == "partial"
    }
    total_history_days = (persona.latest_activity - HISTORY_START).days + 1
    weigh_ins = [row.body_weight for row in recovery if row.body_weight is not None]
    counts = _expected_counts(dataset, persona.user_id)
    intended = dataset.intended_workout_counts[persona.user_id]
    recorded = len(workouts)
    missing_rir = sum(
        1
        for workout in workouts
        for exercise in workout.exercises
        for actual in exercise.actuals
        if (
            exercise.measurement_type == "reps"
            and actual.completed
            and actual.actual_rir is None
        )
    )
    skipped_sets = sum(
        1
        for workout in workouts
        for exercise in workout.exercises
        for actual in exercise.actuals
        if actual.skipped
    )
    complete_menu_signatures = {
        tuple(
            (
                row.food_name,
                row.grams,
                row.meal_type,
            )
            for row in sorted(
                (
                    entry
                    for entry in nutrition
                    if entry.entry_date == complete_day
                    and entry.completeness == "complete"
                ),
                key=lambda entry: entry.entry_index,
            )
        )
        for complete_day in complete_days
    }
    return {
        "id": persona.user_id,
        "name": persona.name,
        "marker": persona.scenario,
        "story": persona.story,
        "profile": {
            "gender": persona.gender,
            "age": persona.age,
            "height_cm": persona.height_cm,
            "starting_weight_lb": persona.starting_weight,
            "goal_weight_lb": persona.goal_weight,
            "primary_goal": persona.primary_goal,
            "activity_level": persona.activity_level,
        },
        "equipment": {
            "training_environment": persona.training_environment,
            "available": list(persona.available_equipment),
            "unavailable": list(persona.unavailable_equipment),
        },
        "history_start": HISTORY_START.isoformat(),
        "history_end": HISTORY_END.isoformat(),
        "latest_activity": persona.latest_activity.isoformat(),
        "row_counts": counts,
        "training": {
            "intended_activities_per_week": persona.intended_activities_per_week,
            "intended_session_count": intended,
            "recorded_session_count": recorded,
            "adherence_percent": round(recorded / intended * 100, 1),
            "partial_session_count": sum(
                1 for workout in workouts if workout.partial_kind is not None
            ),
            "explicit_skipped_set_count": skipped_sets,
            "missing_rir_count": missing_rir,
            "dual_persistence": {
                "planned_execution_workouts": recorded,
                "legacy_workout_sessions": counts["workout_sessions"],
                "legacy_reps_sets": counts["workout_sets"],
            },
            "exercise_patterns": _exercise_patterns(workouts),
        },
        "recovery": {
            "checkin_days": len(recovery),
            "omitted_days": total_history_days - len(recovery),
            "all_inserted_rows_have_numeric_sleep_energy_soreness": True,
        },
        "nutrition": {
            "logged_days": len(nutrition_days),
            "complete_days": len(complete_days),
            "partial_days": len(partial_days),
            "no_log_days": total_history_days - len(nutrition_days),
            "complete_menu_signature_count": len(complete_menu_signatures),
            "canonical_food_names": list(CANONICAL_FOOD_NAMES),
            "snapshot_nutrients": list(MACRO_NUTRIENTS),
        },
        "weight": {
            "weigh_in_count": len(weigh_ins),
            "first_weight_lb": weigh_ins[0] if weigh_ins else None,
            "last_weight_lb": weigh_ins[-1] if weigh_ins else None,
            "broad_trend": (
                "modest_gain"
                if persona.final_weight > persona.starting_weight + 0.5
                else "stable_to_gentle_loss"
            ),
        },
        "phase_windows": [
            {
                "phase": phase,
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
            for phase, start, end in PHASE_WINDOWS[persona.user_id]
        ],
        "checkpoints": CHECKPOINTS[persona.user_id],
        "expected_evidence": {
            106: [
                "repeated anchor loads before deload",
                "temporary recovery limitation near deload",
                "reduced load and volume followed by rebound",
            ],
            107: [
                "irregular attendance from the beginning",
                "three-week absent-record interruption",
                "renewed activity with incomplete logging evidence",
            ],
            108: [
                "weighted and bodyweight progression",
                "duration, distance, carry, and cardio history",
                "fatigue reduction followed by resumed progress",
            ],
        }[persona.user_id],
    }


def build_seed_manifest(dataset: SeedDataset) -> dict[str, Any]:
    return {
        "version": SEED_VERSION,
        "history_start": HISTORY_START.isoformat(),
        "history_end": HISTORY_END.isoformat(),
        "elapsed_days": (HISTORY_END - HISTORY_START).days,
        "personas": [_persona_manifest(dataset, persona) for persona in PERSONAS],
    }


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _table_names(conn: sqlite3.Connection) -> list[str]:
    return [
        str(row[0])
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
    ]


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    quoted = _quote_identifier(table_name)
    return {
        str(row[1]) for row in conn.execute(f"PRAGMA table_info({quoted})").fetchall()
    }


def _verify_schema(conn: sqlite3.Connection) -> None:
    table_names = set(_table_names(conn))
    missing_tables = sorted(set(REQUIRED_SCHEMA) - table_names)
    if missing_tables:
        raise RuntimeError(
            "Database is missing required tables: " + ", ".join(missing_tables)
        )
    problems: list[str] = []
    for table_name, required_columns in REQUIRED_SCHEMA.items():
        missing_columns = sorted(required_columns - _table_columns(conn, table_name))
        if missing_columns:
            problems.append(f"{table_name}({', '.join(missing_columns)})")
    if problems:
        raise RuntimeError(
            "Database is missing required columns: " + "; ".join(problems)
        )


def _decode_measurements(raw_value: str) -> set[str]:
    try:
        value = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError) as exc:
        raise RuntimeError("Exercise measurement metadata is malformed.") from exc
    if not isinstance(value, list):
        raise RuntimeError("Exercise measurement metadata must be a JSON list.")
    return {str(item) for item in value}


def _resolve_references(
    conn: sqlite3.Connection,
    dataset: SeedDataset,
) -> ResolvedReferences:
    required_measurements: dict[str, set[str]] = {}
    for workout in dataset.workouts:
        for exercise in workout.exercises:
            required_measurements.setdefault(exercise.name, set()).add(
                exercise.measurement_type
            )

    catalog_ids: dict[str, int] = {}
    for exercise_name, measurements in sorted(required_measurements.items()):
        row = conn.execute(
            """
            SELECT catalog.id,
                   measurement.default_measurement_type,
                   measurement.allowed_measurement_types_json
            FROM exercise_catalog_exercises AS catalog
            JOIN exercise_catalog_prescription_measurements AS measurement
              ON measurement.exercise_id = catalog.id
            WHERE catalog.name = ?
            """,
            (exercise_name,),
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"Missing required catalog exercise or measurement: {exercise_name}"
            )
        allowed = _decode_measurements(str(row["allowed_measurement_types_json"]))
        unsupported = sorted(measurements - allowed)
        if unsupported:
            raise RuntimeError(
                f"{exercise_name} does not allow measurement types: "
                + ", ".join(unsupported)
            )
        catalog_ids[exercise_name] = int(row["id"])

    legacy_reps_names = sorted(
        {
            exercise.name
            for workout in dataset.workouts
            for exercise in workout.exercises
            if exercise.measurement_type == "reps"
        }
    )
    legacy_ids: dict[str, int] = {}
    for exercise_name in legacy_reps_names:
        row = conn.execute(
            "SELECT id FROM exercises WHERE name = ?",
            (exercise_name,),
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"Missing legacy exercise required for dual persistence: {exercise_name}"
            )
        legacy_ids[exercise_name] = int(row["id"])

    food_references: dict[str, CanonicalFoodReference] = {}
    for display_name in CANONICAL_FOOD_NAMES:
        food_row = conn.execute(
            """
            SELECT canonical.id AS canonical_food_id,
                   legacy.id AS legacy_food_id
            FROM canonical_foods AS canonical
            LEFT JOIN foods AS legacy
              ON legacy.name = 'Canonical: ' || canonical.display_name
            WHERE canonical.display_name = ?
              AND canonical.active = 1
            """,
            (display_name,),
        ).fetchone()
        if food_row is None:
            raise RuntimeError(
                f"Missing active required canonical food: {display_name}"
            )
        if food_row["legacy_food_id"] is None:
            raise RuntimeError(
                "Missing current canonical logging mirror for "
                f"{display_name!r}; log/synchronize reference data before seeding."
            )
        nutrient_rows = conn.execute(
            """
            SELECT nutrient_name, nutrient_unit, amount_per_100g
            FROM canonical_food_nutrients
            WHERE canonical_food_id = ?
            """,
            (int(food_row["canonical_food_id"]),),
        ).fetchall()
        nutrient_map = {
            str(row["nutrient_name"]): float(row["amount_per_100g"])
            for row in nutrient_rows
        }
        missing_nutrients = sorted(set(MACRO_NUTRIENTS) - nutrient_map.keys())
        if missing_nutrients:
            raise RuntimeError(
                f"Canonical food {display_name!r} is missing nutrient snapshots: "
                + ", ".join(missing_nutrients)
            )
        legacy_nutrients = {
            str(row["name"])
            for row in conn.execute(
                """
                SELECT nutrients.name
                FROM food_nutrients
                JOIN nutrients ON nutrients.id = food_nutrients.nutrient_id
                WHERE food_nutrients.food_id = ?
                """,
                (int(food_row["legacy_food_id"]),),
            ).fetchall()
        }
        required_legacy = {"Calories", "Protein", "Carbohydrates", "Fat"}
        if not required_legacy.issubset(legacy_nutrients):
            raise RuntimeError(
                f"Legacy nutrient mirror for {display_name!r} is incomplete."
            )
        food_references[display_name] = CanonicalFoodReference(
            canonical_food_id=int(food_row["canonical_food_id"]),
            legacy_food_id=int(food_row["legacy_food_id"]),
            display_name=display_name,
            nutrients_per_100g={
                nutrient: nutrient_map[nutrient] for nutrient in MACRO_NUTRIENTS
            },
        )

    return ResolvedReferences(
        catalog_exercise_ids=catalog_ids,
        legacy_exercise_ids=legacy_ids,
        canonical_foods=food_references,
    )


def _direct_user_attachment_counts(
    conn: sqlite3.Connection,
    user_id: int,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table_name in _table_names(conn):
        if "user_id" not in _table_columns(conn, table_name):
            continue
        quoted = _quote_identifier(table_name)
        count = int(
            conn.execute(
                f"SELECT COUNT(*) FROM {quoted} WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]
        )
        if count:
            counts[table_name] = count
    return counts


def _owned_ids(
    conn: sqlite3.Connection,
    user_id: int,
) -> dict[str, set[int]]:
    ids: dict[str, set[int]] = {"users": {user_id}}
    direct_tables = (
        "daily_checkins",
        "food_entries",
        "user_equipment_profiles",
        "workout_execution_sessions",
        "workout_plan_instances",
        "workout_sessions",
    )
    for table_name in direct_tables:
        if table_name not in _table_names(conn):
            continue
        quoted = _quote_identifier(table_name)
        ids[table_name] = {
            int(row[0])
            for row in conn.execute(
                f"SELECT id FROM {quoted} WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        }
    plan_ids = ids.get("workout_plan_instances", set())
    session_ids = ids.get("workout_sessions", set())
    execution_ids = ids.get("workout_execution_sessions", set())
    if plan_ids:
        placeholders = ",".join("?" for _ in plan_ids)
        ids["planned_workout_exercises"] = {
            int(row[0])
            for row in conn.execute(
                "SELECT id FROM planned_workout_exercises "
                f"WHERE workout_plan_instance_id IN ({placeholders})",
                tuple(sorted(plan_ids)),
            ).fetchall()
        }
    if session_ids:
        placeholders = ",".join("?" for _ in session_ids)
        ids["workout_sets"] = {
            int(row[0])
            for row in conn.execute(
                "SELECT id FROM workout_sets "
                f"WHERE workout_session_id IN ({placeholders})",
                tuple(sorted(session_ids)),
            ).fetchall()
        }
    if execution_ids:
        placeholders = ",".join("?" for _ in execution_ids)
        ids["workout_execution_set_actuals"] = {
            int(row[0])
            for row in conn.execute(
                "SELECT id FROM workout_execution_set_actuals "
                f"WHERE workout_execution_session_id IN ({placeholders})",
                tuple(sorted(execution_ids)),
            ).fetchall()
        }
    return ids


def _foreign_key_relations(
    conn: sqlite3.Connection,
    table_name: str,
) -> list[tuple[str, str]]:
    quoted = _quote_identifier(table_name)
    return [
        (str(row[3]), str(row[2]))
        for row in conn.execute(f"PRAGMA foreign_key_list({quoted})").fetchall()
    ]


def _assert_owned_graph(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    allowed_direct_tables: set[str],
) -> dict[str, set[int]]:
    owned = _owned_ids(conn, user_id)
    problems: list[str] = []

    for table_name, row_ids in owned.items():
        if table_name == "users" or not row_ids:
            continue
        columns = _table_columns(conn, table_name)
        if "id" not in columns:
            problems.append(f"{table_name} has no stable id ownership shape")
            continue
        placeholders = ",".join("?" for _ in row_ids)
        rows = conn.execute(
            f"SELECT * FROM {_quote_identifier(table_name)} "
            f"WHERE id IN ({placeholders})",
            tuple(sorted(row_ids)),
        ).fetchall()
        foreign_keys = _foreign_key_relations(conn, table_name)
        for row in rows:
            row_id = int(row["id"])
            if "user_id" in columns and int(row["user_id"]) != user_id:
                problems.append(
                    "cross-user attachment: "
                    f"{table_name} id {row_id} has user_id {row['user_id']}, "
                    f"expected {user_id}"
                )
            for child_column, parent_table in foreign_keys:
                value = row[child_column]
                if value is None:
                    continue
                if parent_table == "users":
                    if int(value) != user_id:
                        problems.append(
                            "cross-user attachment: "
                            f"{table_name} id {row_id} links "
                            f"{child_column}={value}, expected user {user_id}"
                        )
                    continue
                if parent_table in owned:
                    if int(value) not in owned[parent_table]:
                        problems.append(
                            "cross-user attachment: "
                            f"{table_name} id {row_id} links {child_column}={value} "
                            f"outside user {user_id} owned {parent_table}"
                        )
                    continue
                if parent_table in GLOBAL_REFERENCE_PARENT_TABLES:
                    continue
                problems.append(
                    "unrecognized ownership foreign key: "
                    f"{table_name} id {row_id} links "
                    f"{child_column}->{parent_table}"
                )

    for child_table in _table_names(conn):
        child_columns = _table_columns(conn, child_table)
        child_quoted = _quote_identifier(child_table)
        for child_column, parent_table in _foreign_key_relations(
            conn,
            child_table,
        ):
            parent_ids = owned.get(parent_table, set())
            if not parent_ids or child_column not in child_columns:
                continue
            placeholders = ",".join("?" for _ in parent_ids)
            attached_rows = conn.execute(
                f"SELECT * FROM {child_quoted} "
                f"WHERE {_quote_identifier(child_column)} "
                f"IN ({placeholders})",
                tuple(sorted(parent_ids)),
            ).fetchall()
            if not attached_rows:
                continue
            relation = (child_table, child_column, parent_table)
            relation_allowed = (
                parent_table == "users" and child_table in allowed_direct_tables
            ) or relation in ALLOWED_INDIRECT_RELATIONS
            if not relation_allowed:
                problems.append(
                    "unrecognized indirect attachment: "
                    f"{child_table}.{child_column}->{parent_table} "
                    f"({len(attached_rows)} rows)"
                )
                continue
            if "id" not in child_columns:
                problems.append(
                    "unknown relation shape: "
                    f"{child_table}.{child_column}->{parent_table} has no id"
                )
                continue
            child_owned_ids = owned.get(child_table, set())
            for row in attached_rows:
                row_id = int(row["id"])
                if row_id not in child_owned_ids:
                    row_user_id = row["user_id"] if "user_id" in child_columns else None
                    problems.append(
                        "cross-user attachment: "
                        f"{child_table} id {row_id} "
                        f"(user_id={row_user_id}) references user {user_id} "
                        f"owned {parent_table} through {child_column}"
                    )
                elif "user_id" in child_columns and int(row["user_id"]) != user_id:
                    problems.append(
                        "cross-user attachment: "
                        f"{child_table} id {row_id} has user_id "
                        f"{row['user_id']}, expected {user_id}"
                    )
    if problems:
        raise RuntimeError(
            f"User {user_id} ownership graph validation failed: "
            + "; ".join(sorted(set(problems)))
        )
    return owned


def _assert_marker_count(
    conn: sqlite3.Connection,
    *,
    sql: str,
    params: Sequence[Any],
    expected: int,
    label: str,
) -> None:
    count = int(conn.execute(sql, tuple(params)).fetchone()[0])
    if count != expected:
        raise RuntimeError(
            f"Ownership proof failed for {label}: expected {expected}, found {count}."
        )


def _assert_v2_owned(
    conn: sqlite3.Connection,
    dataset: SeedDataset,
    user_id: int,
) -> None:
    persona = PERSONA_BY_ID[user_id]
    counts = _expected_counts(dataset, user_id)
    direct = _direct_user_attachment_counts(conn, user_id)
    unknown_direct = sorted(set(direct) - ALLOWED_DIRECT_V2_TABLES)
    if unknown_direct:
        raise RuntimeError(
            f"User {user_id} has unrecognized direct attachments: "
            + ", ".join(unknown_direct)
        )
    owned = _assert_owned_graph(
        conn,
        user_id,
        allowed_direct_tables=ALLOWED_DIRECT_V2_TABLES,
    )
    for table_name in ALLOWED_DIRECT_V2_TABLES:
        actual_count = direct.get(table_name, 0)
        expected_count = counts[table_name]
        if actual_count != expected_count:
            raise RuntimeError(
                f"User {user_id} {table_name} count does not prove v2 ownership "
                f"(expected {expected_count}, found {actual_count})."
            )
    user_row = conn.execute(
        """
        SELECT name,
               gender,
               age,
               height_cm,
               starting_weight,
               goal_weight,
               primary_goal,
               activity_level
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    expected_profile = (
        persona.name,
        persona.gender,
        persona.age,
        persona.height_cm,
        persona.starting_weight,
        persona.goal_weight,
        persona.primary_goal,
        persona.activity_level,
    )
    if user_row is None or tuple(user_row) != expected_profile:
        raise RuntimeError(f"User {user_id} profile does not prove v2 ownership.")

    marker_like = SEED_MARKER + "%"
    _assert_marker_count(
        conn,
        sql="SELECT COUNT(*) FROM daily_checkins WHERE user_id = ? AND notes LIKE ?",
        params=(user_id, marker_like),
        expected=counts["daily_checkins"],
        label=f"user {user_id} recovery rows",
    )
    _assert_marker_count(
        conn,
        sql="SELECT COUNT(*) FROM food_entries WHERE user_id = ? AND notes LIKE ?",
        params=(user_id, marker_like),
        expected=counts["food_entries"],
        label=f"user {user_id} nutrition rows",
    )
    _assert_marker_count(
        conn,
        sql="SELECT COUNT(*) FROM workout_sessions WHERE user_id = ? AND notes LIKE ?",
        params=(user_id, marker_like),
        expected=counts["workout_sessions"],
        label=f"user {user_id} legacy workout sessions",
    )
    _assert_marker_count(
        conn,
        sql="SELECT COUNT(*) FROM workout_plan_instances "
        "WHERE user_id = ? AND scenario = ?",
        params=(user_id, persona.scenario),
        expected=counts["workout_plan_instances"],
        label=f"user {user_id} plan marker",
    )
    _assert_marker_count(
        conn,
        sql="""
            SELECT COUNT(*)
            FROM workout_execution_sessions AS execution
            JOIN workout_plan_instances AS plan
              ON plan.id = execution.workout_plan_instance_id
            WHERE execution.user_id = ?
              AND plan.scenario = ?
        """,
        params=(user_id, persona.scenario),
        expected=counts["workout_execution_sessions"],
        label=f"user {user_id} execution marker",
    )
    for table_name in (
        "planned_workout_exercises",
        "workout_execution_set_actuals",
        "workout_sets",
    ):
        actual_count = len(owned.get(table_name, set()))
        if actual_count != counts[table_name]:
            raise RuntimeError(
                f"User {user_id} {table_name} count does not prove v2 ownership "
                f"(expected {counts[table_name]}, found {actual_count})."
            )


def _legacy_bench_expectation(session_index: int) -> LegacyExerciseExpectation:
    completed_sets = 2 if session_index == 8 else 3
    actual_reps = (10, 9, 8)[:completed_sets]
    load = LEGACY_QA106_BENCH_LOADS[session_index]
    rir = LEGACY_QA106_BENCH_RIRS[session_index]
    return LegacyExerciseExpectation(
        name="Dumbbell Bench Press",
        measurement_type="reps",
        planned_sets=3,
        reps_min=8,
        reps_max=10,
        target_duration_seconds=None,
        target_distance_meters=None,
        equipment=("dumbbell", "adjustable_bench"),
        actuals=tuple(
            ActualSet(
                set_number=set_index + 1,
                actual_reps=reps,
                actual_weight=load,
                actual_rir=rir,
            )
            for set_index, reps in enumerate(actual_reps)
        ),
    )


def _legacy_conditioning_expectation(
    session_index: int,
) -> LegacyExerciseExpectation:
    occurrence = session_index // 4
    variant = session_index % 4
    if variant == 0:
        reps = 6 + occurrence
        return LegacyExerciseExpectation(
            name="Pull-Up",
            measurement_type="reps",
            planned_sets=3,
            reps_min=5,
            reps_max=10,
            target_duration_seconds=None,
            target_distance_meters=None,
            equipment=("bodyweight",),
            actuals=tuple(
                ActualSet(
                    set_number=set_index + 1,
                    actual_reps=actual_reps,
                    actual_rir=actual_rir,
                )
                for set_index, (actual_reps, actual_rir) in enumerate(
                    (
                        (reps, 3),
                        (max(1, reps - 1), 2),
                        (max(1, reps - 2), 2),
                    )
                )
            ),
        )
    if variant == 1:
        duration = 35 + occurrence * 5
        return LegacyExerciseExpectation(
            name="Plank",
            measurement_type="duration",
            planned_sets=3,
            reps_min=None,
            reps_max=None,
            target_duration_seconds=duration,
            target_distance_meters=None,
            equipment=("bodyweight", "exercise_mat"),
            actuals=tuple(
                ActualSet(
                    set_number=set_index + 1,
                    actual_duration_seconds=actual_duration,
                )
                for set_index, actual_duration in enumerate(
                    (duration, duration + 5, duration)
                )
            ),
        )
    if variant == 2:
        distance = 20.0 + occurrence * 5.0
        load = 40.0 + occurrence * 5.0
        return LegacyExerciseExpectation(
            name="Farmer Carry",
            measurement_type="distance",
            planned_sets=3,
            reps_min=None,
            reps_max=None,
            target_duration_seconds=None,
            target_distance_meters=distance,
            equipment=("dumbbell",),
            actuals=tuple(
                ActualSet(
                    set_number=set_index + 1,
                    actual_distance_meters=actual_distance,
                    actual_weight=load,
                )
                for set_index, actual_distance in enumerate(
                    (distance, distance, distance + 5.0)
                )
            ),
        )

    distance = 800.0 + occurrence * 100.0
    return LegacyExerciseExpectation(
        name="Treadmill Walk",
        measurement_type="distance",
        planned_sets=1,
        reps_min=None,
        reps_max=None,
        target_duration_seconds=None,
        target_distance_meters=distance,
        equipment=("treadmill",),
        actuals=(
            ActualSet(
                set_number=1,
                actual_distance_meters=distance,
            ),
        ),
    )


def _legacy_workout_title(conditioning_name: str) -> str:
    if conditioning_name in {"Pull-Up", "Plank"}:
        return "Upper Body Strength"
    return "Strength and Conditioning"


def _legacy_signature_error(detail: str) -> RuntimeError:
    return RuntimeError("Legacy QA106 exact fixture signature mismatch: " + detail)


def _assert_legacy_qa106_owned(conn: sqlite3.Connection) -> None:
    user_row = conn.execute(
        """
        SELECT name,
               gender,
               age,
               height_cm,
               starting_weight,
               goal_weight,
               primary_goal,
               activity_level
        FROM users
        WHERE id = 106
        """
    ).fetchone()
    expected_profile = (
        LEGACY_QA106_NAME,
        None,
        36,
        None,
        182.0,
        None,
        "Build strength and conditioning",
        "moderate",
    )
    if user_row is None or tuple(user_row) != expected_profile:
        raise _legacy_signature_error("user profile differs from the v1 seed.")

    direct = _direct_user_attachment_counts(conn, 106)
    expected_direct = {
        "workout_execution_sessions": 24,
        "workout_plan_instances": 24,
    }
    if direct != expected_direct:
        raise _legacy_signature_error(
            f"direct attachment counts differ: expected {expected_direct}, "
            f"found {direct}."
        )

    owned = _assert_owned_graph(
        conn,
        106,
        allowed_direct_tables=ALLOWED_DIRECT_LEGACY_QA106_TABLES,
    )
    expected_indirect_counts = {
        "planned_workout_exercises": 48,
        "workout_execution_set_actuals": 131,
        "workout_sessions": 0,
        "workout_sets": 0,
    }
    for table_name, expected_count in expected_indirect_counts.items():
        actual_count = len(owned.get(table_name, set()))
        if actual_count != expected_count:
            raise _legacy_signature_error(
                f"{table_name} count differs: expected {expected_count}, "
                f"found {actual_count}."
            )

    required_exercise_names = {
        "Dumbbell Bench Press",
        "Pull-Up",
        "Plank",
        "Farmer Carry",
        "Treadmill Walk",
    }
    placeholders = ",".join("?" for _ in required_exercise_names)
    catalog_rows = conn.execute(
        """
        SELECT id, name
        FROM exercise_catalog_exercises
        WHERE name IN ("""
        + placeholders
        + ")",
        tuple(sorted(required_exercise_names)),
    ).fetchall()
    catalog_ids = {str(row["name"]): int(row["id"]) for row in catalog_rows}
    if set(catalog_ids) != required_exercise_names:
        raise _legacy_signature_error(
            "required catalog exercise identities are unavailable."
        )

    plan_rows = conn.execute(
        """
        SELECT id,
               status,
               scenario,
               confidence,
               title,
               approved_workout_plan_json,
               selected_at,
               completed_at,
               created_at,
               updated_at
        FROM workout_plan_instances
        WHERE user_id = 106
        ORDER BY selected_at, id
        """
    ).fetchall()
    if len(plan_rows) != len(LEGACY_QA106_SESSION_DAY_OFFSETS):
        raise _legacy_signature_error("plan count is not exactly 24.")

    for session_index, (plan_row, day_offset) in enumerate(
        zip(
            plan_rows,
            LEGACY_QA106_SESSION_DAY_OFFSETS,
            strict=True,
        )
    ):
        session_date = LEGACY_QA106_END_DATE - timedelta(days=day_offset)
        timestamp = _timestamp(session_date, 18)
        exercises = (
            _legacy_bench_expectation(session_index),
            _legacy_conditioning_expectation(session_index),
        )
        title = _legacy_workout_title(exercises[1].name)
        expected_plan_values = (
            "completed",
            LEGACY_QA106_SCENARIO,
            "High",
            title,
            timestamp,
            timestamp,
            timestamp,
            timestamp,
        )
        actual_plan_values = (
            plan_row["status"],
            plan_row["scenario"],
            plan_row["confidence"],
            plan_row["title"],
            plan_row["selected_at"],
            plan_row["completed_at"],
            plan_row["created_at"],
            plan_row["updated_at"],
        )
        if actual_plan_values != expected_plan_values:
            raise _legacy_signature_error(
                f"plan {session_index + 1} identity/date/status differs."
            )

        expected_approved_plan = {
            "title": title,
            "duration_minutes": 50,
            "confidence": "High",
            "exercises": [
                {
                    "exercise_name": exercise.name,
                    "catalog_exercise_id": catalog_ids[exercise.name],
                    "sets": exercise.planned_sets,
                    "measurement_type": exercise.measurement_type,
                }
                for exercise in exercises
            ],
        }
        try:
            approved_plan = json.loads(plan_row["approved_workout_plan_json"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise _legacy_signature_error(
                f"plan {session_index + 1} approved JSON is invalid."
            ) from exc
        if approved_plan != expected_approved_plan:
            raise _legacy_signature_error(
                f"plan {session_index + 1} approved snapshot differs."
            )

        planned_rows = conn.execute(
            """
            SELECT id,
                   exercise_order,
                   name,
                   sets,
                   measurement_type,
                   reps_min,
                   reps_max,
                   target_duration_seconds,
                   target_distance_meters,
                   rir_min,
                   rir_max,
                   notes,
                   equipment_required_json,
                   catalog_exercise_id,
                   created_at
            FROM planned_workout_exercises
            WHERE workout_plan_instance_id = ?
            ORDER BY exercise_order, id
            """,
            (int(plan_row["id"]),),
        ).fetchall()
        if len(planned_rows) != 2:
            raise _legacy_signature_error(
                f"plan {session_index + 1} does not have exactly two exercises."
            )

        execution_rows = conn.execute(
            """
            SELECT id,
                   user_id,
                   status,
                   workout_session_id,
                   started_at,
                   completed_at,
                   created_at,
                   updated_at
            FROM workout_execution_sessions
            WHERE workout_plan_instance_id = ?
            ORDER BY id
            """,
            (int(plan_row["id"]),),
        ).fetchall()
        if len(execution_rows) != 1:
            raise _legacy_signature_error(
                f"plan {session_index + 1} does not have exactly one execution."
            )
        execution_row = execution_rows[0]
        execution_values = (
            int(execution_row["user_id"]),
            execution_row["status"],
            execution_row["workout_session_id"],
            execution_row["started_at"],
            execution_row["completed_at"],
            execution_row["created_at"],
            execution_row["updated_at"],
        )
        expected_execution_values = (
            106,
            "completed",
            None,
            timestamp,
            timestamp,
            timestamp,
            timestamp,
        )
        if execution_values != expected_execution_values:
            raise _legacy_signature_error(
                f"execution {session_index + 1} linkage/status differs."
            )

        for exercise_order, (planned_row, exercise) in enumerate(
            zip(planned_rows, exercises, strict=True),
            start=1,
        ):
            try:
                equipment = tuple(json.loads(planned_row["equipment_required_json"]))
            except (TypeError, json.JSONDecodeError) as exc:
                raise _legacy_signature_error(
                    f"plan {session_index + 1} exercise "
                    f"{exercise_order} equipment JSON is invalid."
                ) from exc
            planned_values = (
                int(planned_row["exercise_order"]),
                planned_row["name"],
                int(planned_row["sets"]),
                planned_row["measurement_type"],
                planned_row["reps_min"],
                planned_row["reps_max"],
                planned_row["target_duration_seconds"],
                planned_row["target_distance_meters"],
                planned_row["rir_min"],
                planned_row["rir_max"],
                planned_row["notes"],
                equipment,
                int(planned_row["catalog_exercise_id"]),
                planned_row["created_at"],
            )
            expected_planned_values = (
                exercise_order,
                exercise.name,
                exercise.planned_sets,
                exercise.measurement_type,
                exercise.reps_min,
                exercise.reps_max,
                exercise.target_duration_seconds,
                exercise.target_distance_meters,
                1 if exercise.measurement_type == "reps" else None,
                3 if exercise.measurement_type == "reps" else None,
                "Use controlled form and record each completed set.",
                exercise.equipment,
                catalog_ids[exercise.name],
                timestamp,
            )
            if planned_values != expected_planned_values:
                raise _legacy_signature_error(
                    f"plan {session_index + 1} exercise {exercise_order} differs."
                )

            actual_rows = conn.execute(
                """
                SELECT workout_execution_session_id,
                       planned_workout_exercise_id,
                       workout_session_id,
                       workout_set_id,
                       substitution_for_planned_exercise_id,
                       exercise_name,
                       set_number,
                       planned_reps_min,
                       planned_reps_max,
                       measurement_type,
                       planned_duration_seconds,
                       planned_distance_meters,
                       planned_rir_min,
                       planned_rir_max,
                       actual_reps,
                       actual_duration_seconds,
                       actual_distance_meters,
                       actual_weight,
                       actual_rir,
                       completed,
                       skipped,
                       notes,
                       created_at,
                       updated_at
                FROM workout_execution_set_actuals
                WHERE workout_execution_session_id = ?
                  AND planned_workout_exercise_id = ?
                ORDER BY set_number, id
                """,
                (
                    int(execution_row["id"]),
                    int(planned_row["id"]),
                ),
            ).fetchall()
            if len(actual_rows) != len(exercise.actuals):
                raise _legacy_signature_error(
                    f"plan {session_index + 1} exercise {exercise_order} "
                    "actual-set count differs."
                )
            for actual_row, expected_actual in zip(
                actual_rows,
                exercise.actuals,
                strict=True,
            ):
                actual_values = (
                    int(actual_row["workout_execution_session_id"]),
                    int(actual_row["planned_workout_exercise_id"]),
                    actual_row["workout_session_id"],
                    actual_row["workout_set_id"],
                    actual_row["substitution_for_planned_exercise_id"],
                    actual_row["exercise_name"],
                    int(actual_row["set_number"]),
                    actual_row["planned_reps_min"],
                    actual_row["planned_reps_max"],
                    actual_row["measurement_type"],
                    actual_row["planned_duration_seconds"],
                    actual_row["planned_distance_meters"],
                    actual_row["planned_rir_min"],
                    actual_row["planned_rir_max"],
                    actual_row["actual_reps"],
                    actual_row["actual_duration_seconds"],
                    actual_row["actual_distance_meters"],
                    actual_row["actual_weight"],
                    actual_row["actual_rir"],
                    int(actual_row["completed"]),
                    int(actual_row["skipped"]),
                    actual_row["notes"],
                    actual_row["created_at"],
                    actual_row["updated_at"],
                )
                expected_actual_values = (
                    int(execution_row["id"]),
                    int(planned_row["id"]),
                    None,
                    None,
                    None,
                    exercise.name,
                    expected_actual.set_number,
                    exercise.reps_min,
                    exercise.reps_max,
                    exercise.measurement_type,
                    exercise.target_duration_seconds,
                    exercise.target_distance_meters,
                    1 if exercise.measurement_type == "reps" else None,
                    3 if exercise.measurement_type == "reps" else None,
                    expected_actual.actual_reps,
                    expected_actual.actual_duration_seconds,
                    expected_actual.actual_distance_meters,
                    expected_actual.actual_weight,
                    expected_actual.actual_rir,
                    1,
                    0,
                    "Recorded during the completed workout.",
                    timestamp,
                    timestamp,
                )
                if actual_values != expected_actual_values:
                    raise _legacy_signature_error(
                        f"plan {session_index + 1} exercise {exercise_order} "
                        f"set {expected_actual.set_number} differs."
                    )


def _preflight_ownership(
    conn: sqlite3.Connection,
    dataset: SeedDataset,
    *,
    target_user_ids: Sequence[int],
    replace_owned: bool,
    migrate_legacy_106: bool,
) -> OwnershipPlan:
    target_ids = tuple(target_user_ids)
    expected_names = {user_id: PERSONA_BY_ID[user_id].name for user_id in target_ids}
    name_rows = conn.execute(
        "SELECT id, name FROM users WHERE lower(name) IN ("
        + ",".join("lower(?)" for _ in expected_names)
        + ")",
        tuple(expected_names.values()),
    ).fetchall()
    for row in name_rows:
        row_id = int(row["id"])
        matching_id = next(
            user_id
            for user_id, expected_name in expected_names.items()
            if str(row["name"]).casefold() == expected_name.casefold()
        )
        if row_id != matching_id:
            raise RuntimeError(
                f"Case-insensitive name collision: {row['name']!r} belongs to "
                f"user {row_id}, not {matching_id}."
            )

    create_ids: list[int] = []
    replace_ids: list[int] = []
    legacy_migration = False
    for user_id in target_ids:
        row = conn.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            create_ids.append(user_id)
            continue
        actual_name = str(row["name"])
        expected_name = expected_names[user_id]
        if actual_name.casefold() == expected_name.casefold():
            if not replace_owned:
                raise RuntimeError(
                    f"User {user_id} already exists; pass --replace-owned only "
                    "after accepting marker-based replacement."
                )
            _assert_v2_owned(conn, dataset, user_id)
            replace_ids.append(user_id)
            continue
        if user_id == 106 and actual_name == LEGACY_QA106_NAME:
            if not migrate_legacy_106:
                raise RuntimeError(
                    "Possible legacy QA106 identity found; pass "
                    "--migrate-legacy-106 to permit exact-signature validation "
                    "and replacement."
                )
            _assert_legacy_qa106_owned(conn)
            legacy_migration = True
            continue
        raise RuntimeError(
            f"User id {user_id} is owned by unrecognized name {actual_name!r}."
        )
    return OwnershipPlan(
        create_user_ids=tuple(create_ids),
        replace_user_ids=tuple(replace_ids),
        migrate_legacy_106=legacy_migration,
    )


def _clear_user_rows(
    conn: sqlite3.Connection,
    user_ids: Sequence[int],
) -> None:
    if not user_ids:
        return
    placeholders = ",".join("?" for _ in user_ids)
    params = tuple(user_ids)
    conn.execute(
        """
        DELETE FROM workout_execution_set_actuals
        WHERE workout_execution_session_id IN (
            SELECT id
            FROM workout_execution_sessions
            WHERE user_id IN ("""
        + placeholders
        + "))",
        params,
    )
    conn.execute(
        """
        DELETE FROM workout_execution_sessions
        WHERE user_id IN ("""
        + placeholders
        + ")",
        params,
    )
    conn.execute(
        """
        DELETE FROM planned_workout_exercises
        WHERE workout_plan_instance_id IN (
            SELECT id
            FROM workout_plan_instances
            WHERE user_id IN ("""
        + placeholders
        + "))",
        params,
    )
    conn.execute(
        "DELETE FROM workout_plan_instances WHERE user_id IN (" + placeholders + ")",
        params,
    )
    conn.execute(
        """
        DELETE FROM workout_sets
        WHERE workout_session_id IN (
            SELECT id
            FROM workout_sessions
            WHERE user_id IN ("""
        + placeholders
        + "))",
        params,
    )
    conn.execute(
        "DELETE FROM workout_sessions WHERE user_id IN (" + placeholders + ")",
        params,
    )
    conn.execute(
        "DELETE FROM food_entries WHERE user_id IN (" + placeholders + ")",
        params,
    )
    conn.execute(
        "DELETE FROM daily_checkins WHERE user_id IN (" + placeholders + ")",
        params,
    )
    conn.execute(
        "DELETE FROM user_equipment_profiles WHERE user_id IN (" + placeholders + ")",
        params,
    )
    conn.execute(
        "DELETE FROM users WHERE id IN (" + placeholders + ")",
        params,
    )


def _insert_user_and_equipment(
    conn: sqlite3.Connection,
    persona: Persona,
) -> None:
    created_at = _timestamp(HISTORY_START, 6)
    conn.execute(
        """
        INSERT INTO users (
            id,
            name,
            gender,
            age,
            height_cm,
            starting_weight,
            goal_weight,
            primary_goal,
            activity_level,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            persona.user_id,
            persona.name,
            persona.gender,
            persona.age,
            persona.height_cm,
            persona.starting_weight,
            persona.goal_weight,
            persona.primary_goal,
            persona.activity_level,
            created_at,
        ),
    )
    conn.execute(
        """
        INSERT INTO user_equipment_profiles (
            user_id,
            training_environment,
            available_equipment_json,
            unavailable_equipment_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            persona.user_id,
            persona.training_environment,
            json.dumps(persona.available_equipment),
            json.dumps(persona.unavailable_equipment),
            created_at,
            created_at,
        ),
    )


def _insert_recovery(
    conn: sqlite3.Connection,
    rows: Sequence[RecoveryLog],
) -> None:
    for row in rows:
        conn.execute(
            """
            INSERT INTO daily_checkins (
                user_id,
                checkin_date,
                body_weight,
                sleep_hours,
                sleep_quality,
                energy_level,
                soreness_level,
                stress_level,
                training_motivation,
                pain_concern,
                pain_area,
                mood,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'none', NULL, ?, ?, ?)
            """,
            (
                row.user_id,
                row.checkin_date.isoformat(),
                row.body_weight,
                row.sleep_hours,
                row.sleep_quality,
                row.energy_level,
                row.soreness_level,
                row.stress_level,
                row.training_motivation,
                row.mood,
                f"{SEED_MARKER} recovery check-in; phase={row.phase}.",
                _timestamp(row.checkin_date, 7, row.user_id % 60),
            ),
        )


def _snapshot_for_grams(
    reference: CanonicalFoodReference,
    grams: float,
) -> dict[str, float]:
    factor = grams / 100.0
    return {
        nutrient: round(reference.nutrients_per_100g[nutrient] * factor, 3)
        for nutrient in MACRO_NUTRIENTS
    }


def _insert_nutrition(
    conn: sqlite3.Connection,
    rows: Sequence[NutritionLog],
    references: ResolvedReferences,
) -> None:
    meal_hours = {"breakfast": 8, "lunch": 13, "snack": 16, "dinner": 19}
    for row in rows:
        reference = references.canonical_foods[row.food_name]
        snapshot = _snapshot_for_grams(reference, row.grams)
        conn.execute(
            """
            INSERT INTO food_entries (
                user_id,
                food_id,
                canonical_food_id,
                food_name_snapshot,
                grams,
                meal_type,
                notes,
                calories,
                protein_g,
                carbs_g,
                fat_g,
                entry_date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.user_id,
                reference.legacy_food_id,
                reference.canonical_food_id,
                reference.display_name,
                row.grams,
                row.meal_type,
                (f"{SEED_MARKER} canonical nutrient snapshot; day={row.completeness}."),
                snapshot["Calories"],
                snapshot["Protein"],
                snapshot["Carbohydrate"],
                snapshot["Fat"],
                row.entry_date.isoformat(),
                _timestamp(
                    row.entry_date,
                    meal_hours[row.meal_type],
                    row.entry_index,
                ),
            ),
        )


def _approved_plan(
    workout: WorkoutLog,
    references: ResolvedReferences,
) -> dict[str, Any]:
    return {
        "title": workout.title,
        "session_focus": "Complete the planned work with controlled effort.",
        "duration_minutes": workout.duration_minutes,
        "confidence": "Moderate" if workout.user_id == 107 else "High",
        "scenario": PERSONA_BY_ID[workout.user_id].scenario,
        "warmup": "Use easy movement and gradual practice sets.",
        "cooldown": "Finish with easy breathing and light mobility.",
        "progression_guidance": (
            "Review completed load, reps, and effort before the next progression."
        ),
        "rationale": "The session matches the current training phase and equipment.",
        "exercises": [
            {
                "name": exercise.name,
                "catalog_exercise_id": references.catalog_exercise_ids[exercise.name],
                "sets": exercise.planned_sets,
                "measurement_type": exercise.measurement_type,
                "reps_min": exercise.reps_min,
                "reps_max": exercise.reps_max,
                "target_duration_seconds": exercise.target_duration_seconds,
                "target_distance_meters": exercise.target_distance_meters,
                "rir_min": exercise.rir_min,
                "rir_max": exercise.rir_max,
                "notes": "Use controlled form and record completed work.",
                "equipment_required": list(EXERCISE_EQUIPMENT[exercise.name]),
            }
            for exercise in workout.exercises
        ],
    }


def _insert_workout(
    conn: sqlite3.Connection,
    workout: WorkoutLog,
    references: ResolvedReferences,
    workout_index: int,
) -> None:
    persona = PERSONA_BY_ID[workout.user_id]
    timestamp = _timestamp(
        workout.workout_date,
        18,
        workout_index % 50,
    )
    approved_plan = _approved_plan(workout, references)
    plan_cursor = conn.execute(
        """
        INSERT INTO workout_plan_instances (
            user_id,
            status,
            scenario,
            confidence,
            title,
            approved_workout_plan_json,
            selected_at,
            completed_at,
            created_at,
            updated_at
        )
        VALUES (?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            workout.user_id,
            persona.scenario,
            "Moderate" if workout.user_id == 107 else "High",
            workout.title,
            json.dumps(approved_plan, sort_keys=True),
            timestamp,
            timestamp,
            timestamp,
            timestamp,
        ),
    )
    plan_id = int(plan_cursor.lastrowid)

    planned_ids: list[int] = []
    for exercise_order, exercise in enumerate(workout.exercises, start=1):
        planned_cursor = conn.execute(
            """
            INSERT INTO planned_workout_exercises (
                workout_plan_instance_id,
                exercise_order,
                name,
                sets,
                measurement_type,
                reps_min,
                reps_max,
                target_duration_seconds,
                target_distance_meters,
                rir_min,
                rir_max,
                notes,
                equipment_required_json,
                catalog_exercise_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                exercise_order,
                exercise.name,
                exercise.planned_sets,
                exercise.measurement_type,
                exercise.reps_min,
                exercise.reps_max,
                exercise.target_duration_seconds,
                exercise.target_distance_meters,
                exercise.rir_min,
                exercise.rir_max,
                f"{SEED_MARKER} planned exercise.",
                json.dumps(EXERCISE_EQUIPMENT[exercise.name]),
                references.catalog_exercise_ids[exercise.name],
                timestamp,
            ),
        )
        planned_ids.append(int(planned_cursor.lastrowid))

    legacy_cursor = conn.execute(
        """
        INSERT INTO workout_sessions (
            user_id,
            workout_date,
            workout_name,
            duration_minutes,
            notes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            workout.user_id,
            workout.workout_date.isoformat(),
            workout.title,
            workout.duration_minutes,
            (
                f"{SEED_MARKER} linked completed planned execution; "
                f"phase={workout.phase}."
            ),
            timestamp,
        ),
    )
    workout_session_id = int(legacy_cursor.lastrowid)
    execution_cursor = conn.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id,
            user_id,
            status,
            workout_session_id,
            started_at,
            completed_at,
            created_at,
            updated_at
        )
        VALUES (?, ?, 'completed', ?, ?, ?, ?, ?)
        """,
        (
            plan_id,
            workout.user_id,
            workout_session_id,
            timestamp,
            timestamp,
            timestamp,
            timestamp,
        ),
    )
    execution_id = int(execution_cursor.lastrowid)

    for planned_id, exercise in zip(
        planned_ids,
        workout.exercises,
        strict=True,
    ):
        for actual in exercise.actuals:
            workout_set_id: int | None = None
            if (
                exercise.measurement_type == "reps"
                and actual.completed
                and not actual.skipped
                and actual.actual_reps is not None
            ):
                set_cursor = conn.execute(
                    """
                    INSERT INTO workout_sets (
                        workout_session_id,
                        exercise_id,
                        set_number,
                        reps,
                        weight,
                        rir,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workout_session_id,
                        references.legacy_exercise_ids[exercise.name],
                        actual.set_number,
                        actual.actual_reps,
                        actual.actual_weight,
                        actual.actual_rir,
                        timestamp,
                    ),
                )
                workout_set_id = int(set_cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO workout_execution_set_actuals (
                    workout_execution_session_id,
                    planned_workout_exercise_id,
                    workout_session_id,
                    workout_set_id,
                    exercise_name,
                    set_number,
                    planned_reps_min,
                    planned_reps_max,
                    measurement_type,
                    planned_duration_seconds,
                    planned_distance_meters,
                    planned_rir_min,
                    planned_rir_max,
                    actual_reps,
                    actual_duration_seconds,
                    actual_distance_meters,
                    actual_weight,
                    actual_rir,
                    completed,
                    skipped,
                    notes,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    execution_id,
                    planned_id,
                    workout_session_id,
                    workout_set_id,
                    exercise.name,
                    actual.set_number,
                    exercise.reps_min,
                    exercise.reps_max,
                    exercise.measurement_type,
                    exercise.target_duration_seconds,
                    exercise.target_distance_meters,
                    exercise.rir_min,
                    exercise.rir_max,
                    actual.actual_reps,
                    actual.actual_duration_seconds,
                    actual.actual_distance_meters,
                    actual.actual_weight,
                    actual.actual_rir,
                    1 if actual.completed else 0,
                    1 if actual.skipped else 0,
                    f"{SEED_MARKER} recorded execution actual.",
                    timestamp,
                    timestamp,
                ),
            )


def _insert_dataset(
    conn: sqlite3.Connection,
    dataset: SeedDataset,
    references: ResolvedReferences,
    *,
    target_user_ids: Sequence[int],
    failure_hook: FailureHook | None,
) -> None:
    target_set = set(target_user_ids)
    for persona in PERSONAS:
        if persona.user_id not in target_set:
            continue
        _insert_user_and_equipment(conn, persona)
        if failure_hook is not None:
            failure_hook(f"after_user_{persona.user_id}")
        _insert_recovery(conn, _recovery_for(dataset, persona.user_id))
        _insert_nutrition(
            conn,
            _nutrition_for(dataset, persona.user_id),
            references,
        )
        for workout_index, workout in enumerate(
            _workouts_for(dataset, persona.user_id)
        ):
            _insert_workout(
                conn,
                workout,
                references,
                workout_index,
            )
        if failure_hook is not None:
            failure_hook(f"after_persona_{persona.user_id}")


def _open_read_only(database_path: Path) -> sqlite3.Connection:
    uri = database_path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _open_read_write(database_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    enabled = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    if enabled != 1:
        conn.close()
        raise RuntimeError("SQLite foreign keys could not be enabled.")
    return conn


def _parse_confirmation(raw_value: str | None) -> tuple[int, ...] | None:
    if raw_value is None:
        return None
    if raw_value != REQUIRED_CONFIRMATION:
        raise ValueError(f"--confirm-user-ids must be exactly {REQUIRED_CONFIRMATION}.")
    return QA_USER_IDS


def _validate_database_path(database_path: str | Path) -> Path:
    resolved = Path(database_path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Database path does not exist: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"Database path is not a file: {resolved}")
    return resolved


def _resolved_canonical_database_path(
    override: str | Path | None = None,
) -> Path:
    if override is None:
        return CANONICAL_DATABASE_PATH
    return Path(override).expanduser().resolve()


def _paths_refer_to_same_file(left: Path, right: Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except OSError:
        return left.resolve() == right.resolve()


def _validate_canonical_apply(
    *,
    database_path: Path,
    apply: bool,
    allow_canonical_database: bool,
    confirm_canonical_path: str | None,
    canonical_database_path: Path,
) -> tuple[bool, bool]:
    is_canonical = _paths_refer_to_same_file(
        database_path,
        canonical_database_path,
    )
    if not apply or not is_canonical:
        return is_canonical, False

    exact_path = str(canonical_database_path)
    if not allow_canonical_database or confirm_canonical_path is None:
        raise ValueError(
            "Apply to the canonical database requires both "
            "--allow-canonical-database and "
            f"--confirm-canonical-path {exact_path!r}."
        )
    if confirm_canonical_path != exact_path:
        raise ValueError(
            "--confirm-canonical-path must exactly match the resolved canonical "
            f"database path: {exact_path}"
        )
    return True, True


def _validate_end_date(end_date: date) -> None:
    if end_date != HISTORY_END:
        raise ValueError(
            f"{SEED_VERSION} requires --end-date {HISTORY_END.isoformat()}."
        )


def _manifest_with_run(
    *,
    seed_manifest: dict[str, Any],
    database_path: Path,
    mode: str,
    legacy_migrated: bool,
) -> dict[str, Any]:
    generated_at = (
        datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    return {
        "seed": seed_manifest,
        "run": {
            "database_path": str(database_path),
            "generated_at": generated_at,
            "mode": mode,
            "legacy_qa106_migrated": legacy_migrated,
        },
    }


def _resolve_manifest_path(manifest_path: str | Path) -> Path:
    resolved = Path(manifest_path).expanduser().resolve()
    if resolved.exists() and resolved.is_dir():
        raise ValueError(f"Manifest path is a directory: {resolved}")
    if not resolved.parent.exists():
        raise FileNotFoundError(
            f"Manifest parent directory must already exist: {resolved.parent}"
        )
    if not resolved.parent.is_dir():
        raise ValueError(f"Manifest parent path is not a directory: {resolved.parent}")
    return resolved


def _stage_manifest(
    manifest_path: str | Path,
    manifest: dict[str, Any],
) -> StagedManifest:
    final_path = _resolve_manifest_path(manifest_path)
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    descriptor, staged_name = tempfile.mkstemp(
        dir=final_path.parent,
        prefix=f".{final_path.name}.",
        suffix=".staged",
        text=True,
    )
    staged_path = Path(staged_name)
    try:
        with os.fdopen(
            descriptor,
            mode="w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        staged_path.unlink(missing_ok=True)
        raise
    return StagedManifest(
        staged_path=staged_path,
        final_path=final_path,
    )


def _remove_staged_manifest(staged: StagedManifest | None) -> None:
    if staged is not None:
        staged.staged_path.unlink(missing_ok=True)


def _publish_staged_manifest(
    staged: StagedManifest | None,
    *,
    database_committed: bool,
) -> Path | None:
    if staged is None:
        return None
    try:
        os.replace(staged.staged_path, staged.final_path)
    except OSError as exc:
        if database_committed:
            raise ManifestFinalizationError(
                staged_path=staged.staged_path,
                final_path=staged.final_path,
                cause=exc,
            ) from exc
        _remove_staged_manifest(staged)
        raise RuntimeError(
            "Manifest finalization failed before any database mutation: "
            f"{staged.final_path}"
        ) from exc
    return staged.final_path


def run_realistic_longitudinal_qa_seed_v2(
    *,
    database_path: str | Path,
    apply: bool = False,
    confirm_user_ids: str | None = None,
    allow_canonical_database: bool = False,
    confirm_canonical_path: str | None = None,
    replace_owned: bool = False,
    migrate_legacy_106: bool = False,
    manifest_path: str | Path | None = None,
    end_date: date = HISTORY_END,
    _failure_hook: FailureHook | None = None,
    _canonical_database_path: str | Path | None = None,
) -> SeedRunResult:
    """Validate or apply the v2 fixture without initializing reference data."""

    _validate_end_date(end_date)
    resolved_database = _validate_database_path(database_path)
    confirmation = _parse_confirmation(confirm_user_ids)
    if apply and confirmation != QA_USER_IDS:
        raise ValueError(
            f"Apply requires --confirm-user-ids {REQUIRED_CONFIRMATION} exactly."
        )
    resolved_canonical = _resolved_canonical_database_path(_canonical_database_path)
    canonical_database, canonical_apply_authorized = _validate_canonical_apply(
        database_path=resolved_database,
        apply=apply,
        allow_canonical_database=allow_canonical_database,
        confirm_canonical_path=confirm_canonical_path,
        canonical_database_path=resolved_canonical,
    )

    dataset = build_seed_dataset()
    seed_manifest = build_seed_manifest(dataset)
    mode = "apply" if apply else "dry_run"
    read_conn = _open_read_only(resolved_database)
    try:
        _verify_schema(read_conn)
        _resolve_references(read_conn, dataset)
        ownership = _preflight_ownership(
            read_conn,
            dataset,
            target_user_ids=QA_USER_IDS,
            replace_owned=replace_owned,
            migrate_legacy_106=migrate_legacy_106,
        )
    finally:
        read_conn.close()

    manifest = _manifest_with_run(
        seed_manifest=seed_manifest,
        database_path=resolved_database,
        mode=mode,
        legacy_migrated=apply and ownership.migrate_legacy_106,
    )
    staged_manifest = (
        _stage_manifest(manifest_path, manifest) if manifest_path is not None else None
    )

    if not apply:
        published_manifest = _publish_staged_manifest(
            staged_manifest,
            database_committed=False,
        )
        return SeedRunResult(
            database_path=resolved_database,
            mode=mode,
            proposed_operation=ownership.proposed_operation,
            manifest=manifest,
            manifest_path=published_manifest,
            canonical_database=canonical_database,
            canonical_apply_authorized=False,
            database_committed=False,
        )

    write_conn: sqlite3.Connection | None = None
    database_committed = False
    try:
        write_conn = _open_read_write(resolved_database)
        write_conn.execute("BEGIN IMMEDIATE")
        _verify_schema(write_conn)
        references = _resolve_references(write_conn, dataset)
        transaction_ownership = _preflight_ownership(
            write_conn,
            dataset,
            target_user_ids=QA_USER_IDS,
            replace_owned=replace_owned,
            migrate_legacy_106=migrate_legacy_106,
        )
        if transaction_ownership != ownership:
            raise RuntimeError(
                "Ownership state changed between read-only preflight and "
                "the write transaction."
            )
        _clear_user_rows(write_conn, QA_USER_IDS)
        if _failure_hook is not None:
            _failure_hook("after_clear")
        _insert_dataset(
            write_conn,
            dataset,
            references,
            target_user_ids=QA_USER_IDS,
            failure_hook=_failure_hook,
        )
        for user_id in QA_USER_IDS:
            _assert_v2_owned(write_conn, dataset, user_id)
        write_conn.commit()
        database_committed = True
    except Exception:
        if write_conn is not None:
            write_conn.rollback()
        _remove_staged_manifest(staged_manifest)
        raise
    finally:
        if write_conn is not None:
            write_conn.close()

    published_manifest = _publish_staged_manifest(
        staged_manifest,
        database_committed=database_committed,
    )
    return SeedRunResult(
        database_path=resolved_database,
        mode=mode,
        proposed_operation=ownership.proposed_operation,
        manifest=manifest,
        manifest_path=published_manifest,
        canonical_database=canonical_database,
        canonical_apply_authorized=canonical_apply_authorized,
        database_committed=database_committed,
    )


def seed_qa106_compatibility_in_connection(
    conn: sqlite3.Connection,
    *,
    end_date: date = HISTORY_END,
) -> dict[str, int | str]:
    """Replace recognized QA106 history with the canonical v2 persona.

    The caller owns transaction boundaries and must prepare reference catalogs.
    This is the narrow compatibility hook used by the legacy Performance Studio
    script; it never touches users 107 or 108.
    """

    _validate_end_date(end_date)
    conn.row_factory = sqlite3.Row
    dataset = build_seed_dataset()
    _verify_schema(conn)
    references = _resolve_references(conn, dataset)
    row = conn.execute("SELECT name FROM users WHERE id = 106").fetchone()
    if row is not None:
        name = str(row["name"])
        if name.casefold() == PERSONA_BY_ID[106].name.casefold():
            _assert_v2_owned(conn, dataset, 106)
        elif name == LEGACY_QA106_NAME:
            _assert_legacy_qa106_owned(conn)
        else:
            raise RuntimeError(f"User id 106 is owned by unrecognized name {name!r}.")
    name_collision = conn.execute(
        "SELECT id FROM users WHERE lower(name) = lower(?) AND id <> 106",
        (PERSONA_BY_ID[106].name,),
    ).fetchone()
    if name_collision is not None:
        raise RuntimeError(
            f"QA106 name is already assigned to user {int(name_collision['id'])}."
        )
    _clear_user_rows(conn, (106,))
    _insert_dataset(
        conn,
        dataset,
        references,
        target_user_ids=(106,),
        failure_hook=None,
    )
    _assert_v2_owned(conn, dataset, 106)
    counts = _expected_counts(dataset, 106)
    workouts = _workouts_for(dataset, 106)
    return {
        "user_id": 106,
        "completed_workout_count": counts["workout_plan_instances"],
        "actual_set_count": counts["workout_execution_set_actuals"],
        "first_session_date": workouts[0].workout_date.isoformat(),
        "last_session_date": workouts[-1].workout_date.isoformat(),
    }


def _parse_date(raw_value: str) -> date:
    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format.") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, help="Existing SQLite database.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the seed. Omit for a read-only dry run.",
    )
    parser.add_argument(
        "--confirm-user-ids",
        help=f"Exact apply confirmation: {REQUIRED_CONFIRMATION}",
    )
    parser.add_argument(
        "--allow-canonical-database",
        action="store_true",
        help=(
            "Acknowledge that apply targets the repository's canonical "
            "fitness_ai.db. This is insufficient without --confirm-canonical-path."
        ),
    )
    parser.add_argument(
        "--confirm-canonical-path",
        help=(
            "Exact resolved canonical path acknowledgment required in addition "
            "to --allow-canonical-database."
        ),
    )
    parser.add_argument(
        "--replace-owned",
        action="store_true",
        help="Replace only rows proven to be owned by this v2 seed.",
    )
    parser.add_argument(
        "--migrate-legacy-106",
        action="store_true",
        help="Permit migration of fully recognized legacy Performance Studio user 106.",
    )
    parser.add_argument("--manifest", help="Optional JSON manifest output path.")
    parser.add_argument(
        "--end-date",
        type=_parse_date,
        default=HISTORY_END,
        help=f"Fixed v2 end date; must be {HISTORY_END.isoformat()}.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    cli_database = _validate_database_path(args.database)
    _is_canonical, canonical_apply_authorized = _validate_canonical_apply(
        database_path=cli_database,
        apply=args.apply,
        allow_canonical_database=args.allow_canonical_database,
        confirm_canonical_path=args.confirm_canonical_path,
        canonical_database_path=_resolved_canonical_database_path(),
    )
    if canonical_apply_authorized:
        print(
            "WARNING: CANONICAL DATABASE APPLY AUTHORIZED: "
            f"{_resolved_canonical_database_path()}",
            file=sys.stderr,
        )
    try:
        result = run_realistic_longitudinal_qa_seed_v2(
            database_path=cli_database,
            apply=args.apply,
            confirm_user_ids=args.confirm_user_ids,
            allow_canonical_database=args.allow_canonical_database,
            confirm_canonical_path=args.confirm_canonical_path,
            replace_owned=args.replace_owned,
            migrate_legacy_106=args.migrate_legacy_106,
            manifest_path=args.manifest,
            end_date=args.end_date,
        )
    except ManifestFinalizationError as exc:
        print(str(exc), file=sys.stderr)
        print(
            "The staged manifest was preserved for recovery. "
            "Do not rerun or roll back the committed database automatically.",
            file=sys.stderr,
        )
        return exc.exit_code
    print(f"Database: {result.database_path}")
    print(f"Mode: {result.mode}")
    print(f"Proposed operation: {result.proposed_operation}")
    for persona in result.manifest["seed"]["personas"]:
        counts = persona["row_counts"]
        print(
            f"- user {persona['id']}: "
            f"workouts={counts['workout_plan_instances']} "
            f"actuals={counts['workout_execution_set_actuals']} "
            f"recovery={counts['daily_checkins']} "
            f"nutrition={counts['food_entries']}"
        )
    if result.manifest_path is not None:
        print(f"Manifest: {result.manifest_path}")
    if result.mode == "dry_run":
        print("Dry run complete; database writes: 0.")
    else:
        print("Apply complete; transaction committed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
