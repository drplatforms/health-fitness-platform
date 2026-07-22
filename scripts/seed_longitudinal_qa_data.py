"""Seed deterministic year-long longitudinal QA data for users 101-105.

Run from the project root:
    python scripts/seed_longitudinal_qa_data.py

The seed is official, deterministic for a given end date, and safe to rerun. It
clears and reseeds only QA-owned per-user rows for users 101-105. It does not
modify user 1, non-QA users, canonical foods, exercise catalog rows, or global
reference data.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
from scripts.longitudinal_qa_scenario_manifest import phase_id_for  # noqa: E402
from services.exercise_catalog_service import seed_exercise_catalog  # noqa: E402
from services.food_normalization_service import (  # noqa: E402
    ensure_starter_canonical_foods_seeded,
)
from services.workout_exercise_memory_service import (  # noqa: E402
    build_workout_exercise_memory_identity_key,
    ensure_workout_exercise_memory_table,
    normalize_workout_exercise_memory_name,
)
from services.workout_plan_persistence_service import (  # noqa: E402
    ensure_workout_plan_persistence_tables,
)

SEED_MARKER = "longitudinal_qa_seed_v1"
QA_USER_IDS = (101, 102, 103, 104, 105)
DEFAULT_END_DATE = date.today()
DEFAULT_DAY_COUNT = 365
RECOVERY_DETERIORATION_OFFSET_DAYS = 14
TRAINING_PROGRESSION_OFFSET_DAYS = 41

PRODUCT_WORKOUT_TITLES = (
    "Recovery-Aware Strength Session",
    "Gradual Progression Strength Session",
    "Controlled Strength Practice",
    "Controlled Progression Session",
    "Manageable Baseline Session",
)

HOME_GYM_EQUIPMENT = [
    "bodyweight",
    "dumbbell",
    "adjustable_bench",
    "barbell",
    "ez_bar",
    "rack",
    "plates",
    "pull_up_bar",
    "resistance_band",
    "cable",
    "treadmill",
    "bike",
]

FORBIDDEN_PRODUCT_CONTEXT_TERMS = (
    "QA",
    "Seeded",
    "Test",
    "Placeholder",
    "Dummy",
    "Synthetic",
)

CANONICAL_FOOD_NAMES = (
    "Chicken Breast, Cooked, Skinless",
    "Turkey Breast, Cooked",
    "Tuna, Canned in Water",
    "Greek Yogurt, Plain",
    "Whey Protein Powder, Generic",
    "White Rice, Cooked",
    "Brown Rice, Cooked",
    "Oats, Dry",
    "Banana",
    "Blueberries",
    "Broccoli, Cooked",
    "Olive Oil",
    "Almonds",
    "Egg, Large",
)


@dataclass(frozen=True)
class LongitudinalQAUser:
    user_id: int
    name: str
    scenario: str
    gender: str | None
    age: int | None
    height_cm: float | None
    starting_weight: float | None
    goal_weight: float | None
    primary_goal: str | None
    activity_level: str | None
    training_environment: str
    training_days_per_week: int


@dataclass(frozen=True)
class SeededLongitudinalQAUser:
    user_id: int
    scenario: str
    recovery_checkins: int
    nutrition_days: int
    nutrition_entries: int
    completed_workouts: int
    actual_sets: int


QA_USERS = (
    LongitudinalQAUser(
        user_id=101,
        name="Recovery Limited Scenario User",
        scenario="recovery_limited",
        gender="Male",
        age=36,
        height_cm=177.0,
        starting_weight=190.0,
        goal_weight=180.0,
        primary_goal="strength_and_recomposition",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=3,
    ),
    LongitudinalQAUser(
        user_id=102,
        name="Aligned Managed Scenario User",
        scenario="aligned_managed",
        gender="Male",
        age=35,
        height_cm=177.0,
        starting_weight=178.0,
        goal_weight=178.0,
        primary_goal="strength_progression",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=4,
    ),
    LongitudinalQAUser(
        user_id=103,
        name="Fat Loss to Maintenance Scenario User",
        scenario="nutrition_training_mismatch",
        gender="Male",
        age=34,
        height_cm=178.0,
        starting_weight=185.0,
        goal_weight=174.0,
        primary_goal="maintenance_and_performance",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=3,
    ),
    LongitudinalQAUser(
        user_id=104,
        name="Strength Plateau Deload Rebound Scenario User",
        scenario="improving_after_deload",
        gender="Male",
        age=37,
        height_cm=176.0,
        starting_weight=188.0,
        goal_weight=184.0,
        primary_goal="strength_progression",
        activity_level="moderate",
        training_environment="home_gym",
        training_days_per_week=3,
    ),
    LongitudinalQAUser(
        user_id=105,
        name="Data Quality Limited Scenario User",
        scenario="data_quality_limited",
        gender=None,
        age=None,
        height_cm=None,
        starting_weight=200.0,
        goal_weight=185.0,
        primary_goal="fat_loss",
        activity_level=None,
        training_environment="limited_equipment",
        training_days_per_week=2,
    ),
)

BASE_PLAN_EXERCISES = (
    {
        "name": "Dumbbell Bench Press",
        "sets": 3,
        "reps_min": 8,
        "reps_max": 10,
        "rir_min": 2,
        "rir_max": 3,
        "equipment_required": ["dumbbell", "adjustable_bench"],
    },
    {
        "name": "Romanian Deadlift",
        "sets": 3,
        "reps_min": 8,
        "reps_max": 10,
        "rir_min": 2,
        "rir_max": 3,
        "equipment_required": ["barbell"],
    },
    {
        "name": "Barbell Row",
        "sets": 3,
        "reps_min": 8,
        "reps_max": 10,
        "rir_min": 2,
        "rir_max": 3,
        "equipment_required": ["barbell"],
    },
    {
        "name": "Cable Crunch",
        "sets": 2,
        "reps_min": 12,
        "reps_max": 15,
        "rir_min": 2,
        "rir_max": 4,
        "equipment_required": ["cable"],
    },
)


def _parse_date(raw_value: str) -> date:
    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format.") from exc


def _iso(day: date) -> str:
    return day.isoformat()


def _timestamp(day: date, hour: int = 8, minute: int = 0) -> str:
    return (
        datetime.combine(day, datetime.min.time())
        .replace(hour=hour, minute=minute)
        .isoformat(sep=" ")
    )


def _date_series(*, end_date: date, day_count: int) -> list[date]:
    start_date = end_date - timedelta(days=day_count - 1)
    return [start_date + timedelta(days=index) for index in range(day_count)]


def longitudinal_insight_qa_dates(end_date: date) -> dict[str, date]:
    """Return stable smoke-test anchors for the date-relative story arcs."""

    return {
        "recovery_deterioration": end_date
        - timedelta(days=RECOVERY_DETERIORATION_OFFSET_DAYS),
        "recovery_rebound": end_date,
        "training_progression": end_date
        - timedelta(days=TRAINING_PROGRESSION_OFFSET_DAYS),
        "training_rising_effort": end_date,
        "sparse_data_control": end_date,
        "strength_progression_phase": end_date - timedelta(days=240),
        "strength_plateau_phase": end_date - timedelta(days=165),
        "strength_deload_phase": end_date - timedelta(days=100),
        "fat_loss_phase": end_date - timedelta(days=190),
        "fat_loss_maintenance": end_date,
        "variable_schedule_disruption": end_date - timedelta(days=270),
        "variable_schedule_return": end_date,
    }


def _placeholders(values: tuple[int, ...]) -> str:
    return ",".join("?" for _ in values)


def _legacy_nutrient_name(nutrient_name: str) -> str:
    normalized = " ".join(nutrient_name.strip().lower().replace("_", " ").split())
    return {
        "calorie": "Calories",
        "calories": "Calories",
        "energy": "Calories",
        "protein": "Protein",
        "carbohydrate": "Carbohydrates",
        "carbohydrates": "Carbohydrates",
        "carbs": "Carbohydrates",
        "total carbohydrate": "Carbohydrates",
        "fat": "Fat",
        "total fat": "Fat",
        "fiber": "Fiber",
        "sugar": "Sugar",
        "sodium": "Sodium",
        "potassium": "Potassium",
        "magnesium": "Magnesium",
        "calcium": "Calcium",
        "iron": "Iron",
        "vitamin c": "Vitamin C",
        "vitamin d": "Vitamin D",
        "vitamin b12": "Vitamin B12",
        "zinc": "Zinc",
    }.get(normalized, nutrient_name.strip())


def _ensure_legacy_nutrient(cursor, nutrient_name: str, unit: str) -> int:
    legacy_name = _legacy_nutrient_name(nutrient_name)
    cursor.execute(
        "INSERT OR IGNORE INTO nutrients (name, unit) VALUES (?, ?)",
        (legacy_name, unit),
    )
    cursor.execute("SELECT id FROM nutrients WHERE name = ?", (legacy_name,))
    return int(cursor.fetchone()["id"])


def _ensure_legacy_foods_from_canonical(cursor) -> dict[str, int]:
    cursor.execute(
        f"""
        SELECT id, display_name
        FROM canonical_foods
        WHERE display_name IN ({",".join("?" for _ in CANONICAL_FOOD_NAMES)})
          AND active = 1
        """,
        CANONICAL_FOOD_NAMES,
    )
    canonical_rows = cursor.fetchall()
    if len(canonical_rows) < len(CANONICAL_FOOD_NAMES):
        found = {row["display_name"] for row in canonical_rows}
        missing = sorted(set(CANONICAL_FOOD_NAMES) - found)
        raise RuntimeError(f"Missing starter canonical foods: {missing}")

    legacy_food_ids: dict[str, int] = {}
    for row in canonical_rows:
        display_name = row["display_name"]
        legacy_name = f"Canonical: {display_name}"
        cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (legacy_name,))
        cursor.execute("SELECT id FROM foods WHERE name = ?", (legacy_name,))
        legacy_food_id = int(cursor.fetchone()["id"])
        legacy_food_ids[display_name] = legacy_food_id

        cursor.execute(
            "DELETE FROM food_nutrients WHERE food_id = ?", (legacy_food_id,)
        )
        cursor.execute(
            """
            SELECT nutrient_name, nutrient_unit, amount_per_100g
            FROM canonical_food_nutrients
            WHERE canonical_food_id = ?
            """,
            (int(row["id"]),),
        )
        for nutrient_row in cursor.fetchall():
            nutrient_id = _ensure_legacy_nutrient(
                cursor,
                nutrient_row["nutrient_name"],
                nutrient_row["nutrient_unit"],
            )
            cursor.execute(
                """
                INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
                VALUES (?, ?, ?)
                """,
                (legacy_food_id, nutrient_id, float(nutrient_row["amount_per_100g"])),
            )

    return legacy_food_ids


def _clear_existing_qa_user_data(cursor) -> None:
    placeholders = _placeholders(QA_USER_IDS)

    cursor.execute(
        f"DELETE FROM workout_exercise_memories WHERE user_id IN ({placeholders})",
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_plan_exercise_substitutions
        WHERE workout_plan_instance_id IN (
            SELECT id FROM workout_plan_instances WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_execution_set_actuals
        WHERE workout_execution_session_id IN (
            SELECT id FROM workout_execution_sessions WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_execution_sessions
        WHERE user_id IN ({placeholders})
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM planned_workout_exercises
        WHERE workout_plan_instance_id IN (
            SELECT id FROM workout_plan_instances WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"DELETE FROM workout_plan_instances WHERE user_id IN ({placeholders})",
        QA_USER_IDS,
    )
    cursor.execute(
        f"""
        DELETE FROM workout_sets
        WHERE workout_session_id IN (
            SELECT id FROM workout_sessions WHERE user_id IN ({placeholders})
        )
        """,
        QA_USER_IDS,
    )
    cursor.execute(
        f"DELETE FROM workout_sessions WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM food_entries WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM daily_checkins WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM recovery_reports WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM health_reports WHERE user_id IN ({placeholders})", QA_USER_IDS
    )
    cursor.execute(
        f"DELETE FROM user_equipment_profiles WHERE user_id IN ({placeholders})",
        QA_USER_IDS,
    )


def _seed_workout_exercise_memories(cursor) -> None:
    fixtures = (
        (
            102,
            "Dumbbell Bench Press",
            True,
            "Bench notch 3. Keep the dumbbells just inside the rack uprights.",
        ),
        (
            102,
            "One-Arm Dumbbell Row",
            True,
            "Brace on the flat bench and start with the right side.",
        ),
        (
            103,
            "Cable Crunch",
            False,
            "Use the rope attachment and kneel one pad back from the stack.",
        ),
    )
    for user_id, exercise_name, catalog_backed, memory_text in fixtures:
        catalog_exercise_id = None
        if catalog_backed:
            row = cursor.execute(
                "SELECT id FROM exercise_catalog_exercises WHERE name = ?",
                (exercise_name,),
            ).fetchone()
            if row is None:
                raise RuntimeError(
                    f"Missing catalog exercise required by QA memory seed: {exercise_name}"
                )
            catalog_exercise_id = int(row["id"])
        cursor.execute(
            """
            INSERT INTO workout_exercise_memories (
                user_id,
                identity_key,
                catalog_exercise_id,
                exercise_name,
                normalized_exercise_name,
                memory_text
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                build_workout_exercise_memory_identity_key(
                    catalog_exercise_id,
                    exercise_name,
                ),
                catalog_exercise_id,
                exercise_name,
                normalize_workout_exercise_memory_name(exercise_name),
                memory_text,
            ),
        )


def _seed_users(cursor) -> None:
    for user in QA_USERS:
        cursor.execute(
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
                activity_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                gender = excluded.gender,
                age = excluded.age,
                height_cm = excluded.height_cm,
                starting_weight = excluded.starting_weight,
                goal_weight = excluded.goal_weight,
                primary_goal = excluded.primary_goal,
                activity_level = excluded.activity_level
            """,
            (
                user.user_id,
                user.name,
                user.gender,
                user.age,
                user.height_cm,
                user.starting_weight,
                user.goal_weight,
                user.primary_goal,
                user.activity_level,
            ),
        )
        cursor.execute(
            """
            INSERT INTO user_equipment_profiles (
                user_id,
                training_environment,
                available_equipment_json,
                unavailable_equipment_json,
                updated_at
            )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                training_environment = excluded.training_environment,
                available_equipment_json = excluded.available_equipment_json,
                unavailable_equipment_json = excluded.unavailable_equipment_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user.user_id,
                user.training_environment,
                json.dumps(HOME_GYM_EQUIPMENT),
                json.dumps(
                    ["machine"] if user.user_id != 105 else ["machine", "cable"]
                ),
            ),
        )


def _recovery_values(
    user: LongitudinalQAUser, index: int, total_days: int
) -> tuple[float, int, int, str]:
    days_remaining = total_days - 1 - index
    phase = phase_id_for(user.user_id, days_remaining)
    if user.scenario == "recovery_limited":
        phase_values = {
            "stable_start": (7.3, 7, 3),
            "schedule_disruption": (5.9, 5, 6),
            "attempted_return": (6.6, 6, 5),
            "recurring_stress": (5.6, 4, 7),
            "missed_training": (6.1, 5, 6),
        }
        if phase == "recovery_swings":
            sleep, energy, soreness = (
                (5.8, 4, 7) if (index // 7) % 2 == 0 else (7.2, 7, 4)
            )
        elif phase == "productive_return" and days_remaining <= 6:
            sleep, energy, soreness = 6.8, 6, 6
        elif phase == "productive_return" and days_remaining <= 13:
            sleep, energy, soreness = 5.8, 5, 7
        elif phase == "productive_return":
            sleep, energy, soreness = 6.5, 6, 6
        else:
            sleep, energy, soreness = phase_values.get(phase, (6.0, 5, 6))
        sleep += ((index % 5) - 2) * 0.08
        energy = max(1, min(10, energy + (-1 if index % 6 == 0 else 0)))
        soreness = max(1, min(10, soreness + (1 if index % 8 == 0 else 0)))
        note = "Variable schedule and sleep keep recovery relevant during a measured return."
    elif user.scenario == "aligned_managed":
        sleep = 7.6 + ((index % 5) * 0.12)
        energy = [8, 8, 9, 8, 7][index % 5]
        soreness = [2, 3, 2, 2, 3][index % 5]
        note = "Stable recovery inputs support managed training decisions."
    elif user.scenario == "nutrition_training_mismatch":
        phase_values = {
            "baseline": (7.0, 6, 4),
            "logging_consistency": (7.2, 7, 4),
            "fat_loss": (7.1, 6, 5),
            "harder_training": (6.5, 5, 6),
            "logging_disruption": (6.2, 5, 6),
            "maintenance_recovery": (7.6, 8, 3),
        }
        sleep, energy, soreness = phase_values.get(phase, (7.0, 6, 5))
        sleep += ((index % 5) - 2) * 0.06
        energy = max(1, min(10, energy + (1 if index % 9 == 0 else 0)))
        soreness = max(1, min(10, soreness + (1 if index % 11 == 0 else 0)))
        note = "Recovery follows the fat-loss, harder-training, and maintenance phases."
    elif user.scenario == "improving_after_deload":
        story_phase = phase or _recovery_story_phase(index, total_days)
        if story_phase == "healthy_baseline":
            sleep, energy, soreness = 7.8, 8, 2
            note = "Recovery inputs are healthy before the short deterioration phase."
        elif story_phase in {"recovery_decline", "brief_fatigue", "deterioration"}:
            sleep, energy, soreness = 5.8, 4, 7
            note = "Sleep, energy, and soreness are worsening during a hard recovery phase."
        elif story_phase == "recovery_rebound":
            sleep, energy, soreness = 8.0, 8, 2
            note = "Recovery inputs have rebounded after the short deterioration phase."
        elif story_phase == "deload":
            sleep, energy, soreness = 7.3, 7, 3
            note = (
                "Recovery is improving while training demand is deliberately reduced."
            )
        elif story_phase == "plateau":
            sleep, energy, soreness = 6.9, 6, 5
            note = "Recovery is usable but less robust while strength progress stalls."
        elif story_phase in {"progression", "foundation", "rebound"}:
            sleep, energy, soreness = 7.5, 7, 3
            note = "Recovery supports consistent strength training in this phase."
        else:
            progress = index / max(total_days - 1, 1)
            sleep = 6.0 + (1.7 * progress) + ((index % 3) * 0.05)
            energy = min(8, 4 + round(progress * 4))
            soreness = max(2, 8 - round(progress * 6))
            note = "Recovery inputs gradually improve before the focused QA story arc."
    else:
        sleep = [6.0, 6.8, 5.7, 7.1, 6.4][index % 5]
        energy = [5, 6, 4, 7, 5][index % 5]
        soreness = [3, 6, 4, 7, 5][index % 5]
        note = "Inputs are inconsistent, so confidence should stay limited."

    if user.scenario == "improving_after_deload":
        sleep += ((index % 5) - 2) * 0.05

    return round(sleep, 1), int(energy), int(soreness), note


def _recovery_story_phase(index: int, total_days: int) -> str | None:
    days_remaining = total_days - 1 - index
    if 21 <= days_remaining <= 27:
        return "healthy_baseline"
    if 7 <= days_remaining <= 20:
        return "deterioration"
    if 0 <= days_remaining <= 6:
        return "rebound"
    return None


def _weight_for(user: LongitudinalQAUser, index: int, total_days: int) -> float | None:
    if user.starting_weight is None:
        return None

    progress = index / max(total_days - 1, 1)
    days_remaining = total_days - 1 - index
    phase = phase_id_for(user.user_id, days_remaining)
    story_index = max(0, 364 - days_remaining)
    if user.scenario == "aligned_managed":
        delta = ((index % 10) - 5) * 0.03
    elif user.scenario == "improving_after_deload":
        delta = -1.2 * progress + ((index % 9) - 4) * 0.04
    elif user.scenario == "nutrition_training_mismatch":
        if phase is None:
            delta = 0.0
        elif phase == "baseline":
            delta = -0.4 * min(1.0, (story_index / 60))
        elif phase == "logging_consistency":
            delta = -0.4 - (story_index - 60) * 0.015
        elif phase == "fat_loss":
            delta = -1.3 - (story_index - 121) * 0.065
        elif phase == "harder_training":
            delta = -7.2 - (story_index - 212) * 0.025
        elif phase == "logging_disruption":
            delta = -8.7 - (story_index - 273) * 0.01
        else:
            delta = -9.0 + ((index % 8) - 4) * 0.05
        delta += ((index % 7) - 3) * 0.04
    elif user.scenario == "data_quality_limited":
        delta = -1.0 * progress if index % 3 != 0 else 0.4
    else:
        delta = 0.6 * progress + ((index % 9) - 4) * 0.04

    return round(user.starting_weight + delta, 1)


def _seed_recovery(cursor, user: LongitudinalQAUser, days: list[date]) -> int:
    inserted = 0
    for index, day in enumerate(days):
        days_remaining = len(days) - 1 - index
        if user.scenario == "data_quality_limited":
            if days_remaining < 28 and days_remaining != 0:
                continue
            if days_remaining >= 28 and index % 3 == 0:
                continue
        if user.scenario == "nutrition_training_mismatch" and index % 9 == 0:
            continue
        phase = phase_id_for(user.user_id, days_remaining)
        if user.scenario == "recovery_limited":
            if phase in {"schedule_disruption", "recurring_stress"} and index % 5 == 0:
                continue
            if phase == "missed_training" and index % 4 == 0:
                continue

        sleep, energy, soreness, note = _recovery_values(user, index, len(days))
        if user.scenario == "recovery_limited":
            strained = phase in {
                "schedule_disruption",
                "recurring_stress",
                "missed_training",
            } or (phase == "recovery_swings" and (index // 7) % 2 == 0)
            sleep_quality = 2 if strained else 3
            stress_level = 5 if strained else 3
            training_motivation = 2 if strained else 4
            pain_concern = "mild" if index % 8 == 0 else "none"
            pain_area = "knee" if pain_concern == "mild" else None
        elif user.scenario == "aligned_managed":
            sleep_quality = 4
            stress_level = 2
            training_motivation = 4
            pain_concern = "none"
            pain_area = None
        elif user.scenario == "nutrition_training_mismatch":
            strained = phase in {"harder_training", "logging_disruption"}
            sleep_quality = 3 if strained else 4
            stress_level = 4 if strained else 2
            training_motivation = 3 if strained else 4
            pain_concern = "none"
            pain_area = None
        elif user.scenario == "improving_after_deload":
            story_phase = phase or _recovery_story_phase(index, len(days))
            if story_phase in {"recovery_decline", "brief_fatigue", "deterioration"}:
                sleep_quality, stress_level, training_motivation = 2, 5, 2
            elif story_phase in {"healthy_baseline", "rebound", "recovery_rebound"}:
                sleep_quality, stress_level, training_motivation = 4, 2, 4
            else:
                progress = index / max(len(days) - 1, 1)
                sleep_quality = min(5, 2 + round(progress * 3))
                stress_level = max(2, 5 - round(progress * 3))
                training_motivation = min(5, 2 + round(progress * 3))
            progress = index / max(len(days) - 1, 1)
            pain_concern = "mild" if progress < 0.25 and index % 7 == 0 else "none"
            pain_area = "lower_back" if pain_concern == "mild" else None
        else:
            sleep_quality = None if index % 2 == 0 else 3
            stress_level = None if index % 3 == 0 else 4
            training_motivation = None if index % 4 == 0 else 3
            pain_concern = None if index % 5 == 0 else "none"
            pain_area = None
        cursor.execute(
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.user_id,
                _iso(day),
                _weight_for(user, index, len(days)),
                sleep,
                sleep_quality,
                energy,
                soreness,
                stress_level,
                training_motivation,
                pain_concern,
                pain_area,
                "steady" if user.scenario != "data_quality_limited" else "variable",
                note,
                _timestamp(day, hour=7),
            ),
        )
        inserted += 1
    return inserted


def _nutrition_food_plan(
    user: LongitudinalQAUser, index: int, total_days: int
) -> list[tuple[str, float]]:
    days_remaining = total_days - 1 - index
    phase = phase_id_for(user.user_id, days_remaining)
    if user.scenario == "aligned_managed":
        return [
            ("Oats, Dry", 80 + (index % 3) * 5),
            ("Chicken Breast, Cooked, Skinless", 180),
            ("White Rice, Cooked", 260),
            ("Greek Yogurt, Plain", 220),
            ("Olive Oil", 12),
            ("Blueberries", 100),
        ]
    if user.scenario == "recovery_limited":
        if phase in {"schedule_disruption", "recurring_stress", "missed_training"}:
            if index % 3 == 0:
                return [("Greek Yogurt, Plain", 180)]
            return [
                ("Chicken Breast, Cooked, Skinless", 150),
                ("Brown Rice, Cooked", 150),
            ]
        if phase == "recovery_swings" and (index // 7) % 2 == 0:
            return [("Egg, Large", 110), ("Banana", 100)]
        return [
            ("Chicken Breast, Cooked, Skinless", 155 + (index % 3) * 5),
            ("Brown Rice, Cooked", 160 + (index % 4) * 10),
            ("Banana", 120),
            ("Greek Yogurt, Plain", 160),
            ("Olive Oil", 10),
        ]
    if user.scenario == "nutrition_training_mismatch":
        if phase == "baseline":
            if index % 3 == 0:
                return [("Tuna, Canned in Water", 120)]
            return [("Turkey Breast, Cooked", 130), ("White Rice, Cooked", 140)]
        if phase == "logging_disruption":
            if index % 2 == 0:
                return [("Greek Yogurt, Plain", 180)]
            return [("Turkey Breast, Cooked", 140), ("Banana", 100)]
        rice_grams = 170
        if phase == "fat_loss":
            rice_grams = 145 + (index % 3) * 10
        elif phase == "harder_training":
            rice_grams = 220 + (index % 4) * 10
        elif phase == "maintenance_recovery":
            rice_grams = 240 + (index % 3) * 10
        return [
            ("Oats, Dry", 60 + (index % 3) * 5),
            ("Turkey Breast, Cooked", 155 + (index % 2) * 10),
            ("White Rice, Cooked", rice_grams),
            ("Banana", 100),
            ("Greek Yogurt, Plain", 200),
            ("Olive Oil", 8 if phase == "fat_loss" else 12),
        ]
    if user.scenario == "improving_after_deload":
        if phase in {"recovery_decline", "brief_fatigue"} and index % 5 == 0:
            return [("Greek Yogurt, Plain", 180), ("Banana", 100)]
        rice_grams = 220
        if phase == "deload":
            rice_grams = 170
        elif phase in {"progression", "rebound", "recovery_rebound"}:
            rice_grams = 250
        return [
            ("Oats, Dry", 70 + (index % 3) * 5),
            ("Chicken Breast, Cooked, Skinless", 170 + (index % 2) * 10),
            ("Brown Rice, Cooked", rice_grams),
            ("Broccoli, Cooked", 130),
            ("Greek Yogurt, Plain", 180),
            ("Olive Oil", 10),
        ]
    if index % 5 in {0, 1}:
        return []
    if index % 4 == 0:
        return [("Almonds", 45)]
    return [("Egg, Large", 110), ("Banana", 90)]


def _should_seed_nutrition(
    user: LongitudinalQAUser, index: int, total_days: int
) -> bool:
    days_remaining = total_days - 1 - index
    phase = phase_id_for(user.user_id, days_remaining)
    if user.scenario == "aligned_managed":
        return index % 12 != 0
    if user.scenario == "recovery_limited":
        if phase in {"schedule_disruption", "recurring_stress", "missed_training"}:
            return index % 3 != 0
        return index % 8 != 0
    if user.scenario == "nutrition_training_mismatch":
        if phase == "baseline":
            return index % 3 != 0
        if phase == "logging_disruption":
            return index % 2 == 0
        return index % 10 != 0
    if user.scenario == "improving_after_deload":
        if phase in {"recovery_decline", "brief_fatigue"}:
            return index % 5 != 0
        return index % 12 != 0
    if days_remaining < 28:
        return days_remaining == 0
    return index % 3 == 0 or index % 7 == 0


def _seed_nutrition(
    cursor,
    user: LongitudinalQAUser,
    days: list[date],
    food_ids: dict[str, int],
) -> tuple[int, int]:
    nutrition_days = 0
    nutrition_entries = 0
    for index, day in enumerate(days):
        if not _should_seed_nutrition(user, index, len(days)):
            continue
        entries = _nutrition_food_plan(user, index, len(days))
        if not entries:
            continue
        nutrition_days += 1
        for food_name, grams in entries:
            cursor.execute(
                """
                INSERT INTO food_entries (user_id, food_id, grams, entry_date, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user.user_id,
                    food_ids[food_name],
                    float(grams),
                    _iso(day),
                    _timestamp(day, hour=12, minute=index % 50),
                ),
            )
            nutrition_entries += 1
    return nutrition_days, nutrition_entries


def _workout_days(user: LongitudinalQAUser, days: list[date]) -> list[date]:
    selected: list[date] = []
    weekday_map = {
        2: {1, 4},
        3: {0, 2, 5},
        4: {0, 2, 4, 6},
    }
    target_weekdays = weekday_map[user.training_days_per_week]
    for index, day in enumerate(days):
        if day.weekday() not in target_weekdays:
            continue
        days_remaining = (days[-1] - day).days
        phase = phase_id_for(user.user_id, days_remaining)
        if user.scenario == "data_quality_limited" and index % 5 == 0:
            continue
        if user.scenario == "recovery_limited":
            if phase in {"schedule_disruption", "recurring_stress"} and index % 3 == 0:
                continue
            if phase == "missed_training" and index % 2 == 0:
                continue
        if (
            user.scenario == "nutrition_training_mismatch"
            and phase == "logging_disruption"
            and index % 4 == 0
        ):
            continue
        if (
            user.scenario == "improving_after_deload"
            and phase == "deload"
            and day.weekday() == 5
        ):
            continue
        selected.append(day)
    return selected


def _plan_exercises_for(
    user: LongitudinalQAUser, workout_index: int, *, days_remaining: int
) -> list[dict[str, Any]]:
    exercises = [dict(exercise) for exercise in BASE_PLAN_EXERCISES]
    phase = phase_id_for(user.user_id, days_remaining)
    if user.scenario == "recovery_limited":
        for exercise in exercises:
            exercise["rir_min"] = 2
            exercise["rir_max"] = 4
    elif user.scenario == "nutrition_training_mismatch":
        for exercise in exercises:
            exercise["rir_min"] = 1 if phase == "harder_training" else 2
            exercise["rir_max"] = 3 if phase == "harder_training" else 4
    elif user.scenario == "improving_after_deload":
        for exercise in exercises:
            if phase == "deload":
                exercise["sets"] = max(2, exercise["sets"] - 1)
                exercise["rir_min"] = 3
                exercise["rir_max"] = 5
            elif phase in {"plateau", "recovery_decline", "brief_fatigue"}:
                exercise["rir_min"] = 1
                exercise["rir_max"] = 3
    elif user.scenario == "data_quality_limited":
        exercises = exercises[:3]
        for exercise in exercises:
            exercise["sets"] = 2
            exercise["rir_min"] = 2
            exercise["rir_max"] = 5
    return exercises


def _workout_title_for(
    user: LongitudinalQAUser, workout_index: int, *, days_remaining: int
) -> str:
    phase = phase_id_for(user.user_id, days_remaining)
    if user.scenario == "recovery_limited":
        titles = (
            "Recovery-Aware Strength Session",
            "Manageable Baseline Session",
            "Controlled Strength Practice",
        )
    elif user.scenario == "aligned_managed":
        titles = (
            "Gradual Progression Strength Session",
            "Controlled Progression Session",
            "Manageable Baseline Session",
        )
    elif user.scenario == "nutrition_training_mismatch":
        titles = (
            "Controlled Strength Practice",
            "Gradual Progression Strength Session",
            "Manageable Baseline Session",
        )
    elif user.scenario == "improving_after_deload":
        if phase == "deload":
            return "Recovery-Aware Strength Session"
        titles = (
            "Controlled Progression Session",
            "Recovery-Aware Strength Session",
            "Gradual Progression Strength Session",
        )
    else:
        titles = ("Manageable Baseline Session", "Controlled Strength Practice")
    return titles[workout_index % len(titles)]


def _approved_plan_payload(
    *,
    title: str,
    scenario: str,
    exercises: list[dict[str, Any]],
    duration_minutes: int,
) -> dict[str, Any]:
    return {
        "title": title,
        "session_focus": "Strength practice with controlled execution and logged effort.",
        "duration_minutes": duration_minutes,
        "exercises": [
            {
                "name": exercise["name"],
                "sets": exercise["sets"],
                "reps_min": exercise["reps_min"],
                "reps_max": exercise["reps_max"],
                "rir_min": exercise["rir_min"],
                "rir_max": exercise["rir_max"],
                "notes": "Use controlled reps and stop within the planned effort range.",
                "equipment_required": exercise["equipment_required"],
            }
            for exercise in exercises
        ],
        "warmup": "Ramp up gradually with easy movement and lighter sets.",
        "cooldown": "Finish with easy breathing and light mobility.",
        "progression_guidance": "Adjust only after reviewing logged load, reps, and RIR.",
        "rationale": "This session keeps training decisions tied to logged execution data.",
        "confidence": "Moderate" if scenario != "data_quality_limited" else "Limited",
        "scenario": scenario,
        "reason_codes": ["longitudinal_data_foundation"],
    }


def _legacy_exercise_ids(cursor) -> dict[str, int]:
    cursor.execute("SELECT id, name FROM exercises")
    return {row["name"]: int(row["id"]) for row in cursor.fetchall()}


def _actual_rir_for(
    user: LongitudinalQAUser,
    workout_index: int,
    set_index: int,
    *,
    days_remaining: int,
) -> int | None:
    phase = phase_id_for(user.user_id, days_remaining)
    if user.scenario == "recovery_limited":
        if phase in {"stable_start", "attempted_return", "productive_return"}:
            return [2, 3, 2][(workout_index + set_index) % 3]
        return [1, 1, 0, 2][(workout_index + set_index) % 4]
    if user.scenario == "aligned_managed":
        if days_remaining <= 1:
            return 1
        if days_remaining <= 7:
            return 3
        return 2
    if user.scenario == "nutrition_training_mismatch":
        if phase == "maintenance_recovery":
            return [2, 3, 2][(workout_index + set_index) % 3]
        if phase == "harder_training":
            return [1, 1, 2, 0][(workout_index + set_index) % 4]
        return [1, 2, 1, 2][(workout_index + set_index) % 4]
    if user.scenario == "improving_after_deload":
        if phase in {"recovery_decline", "brief_fatigue"}:
            return 1
        if phase == "deload":
            return [4, 3, 4][set_index % 3]
        if phase == "recovery_rebound":
            return [3, 3, 2][set_index % 3]
        return [2, 3, 2][set_index % 3]
    if days_remaining <= 28:
        return None
    if (workout_index + set_index) % 5 == 0:
        return None
    return [3, 4, 2][set_index % 3]


def _actual_weight_for(
    user: LongitudinalQAUser,
    exercise_index: int,
    workout_index: int,
    *,
    days_remaining: int,
) -> float:
    base = {
        "recovery_limited": 40.0,
        "aligned_managed": 55.0,
        "nutrition_training_mismatch": 50.0,
        "improving_after_deload": 45.0,
        "data_quality_limited": 30.0,
    }[user.scenario]
    phase = phase_id_for(user.user_id, days_remaining)
    story_index = max(0, 364 - days_remaining)
    if user.scenario == "aligned_managed":
        progression = 10.0 if days_remaining <= 43 else min(workout_index * 0.12, 5.0)
    elif user.scenario == "improving_after_deload":
        if phase is None:
            progression = 0.0
        elif phase == "foundation":
            progression = (story_index // 28) * 2.5
        elif phase == "progression":
            progression = 5.0 + ((story_index - 60) // 21) * 2.5
        elif phase in {"plateau", "recovery_decline"}:
            progression = 17.5
        elif phase == "deload":
            progression = 7.5
        else:
            progression = 20.0 + min(5.0, max(0, story_index - 273) * 0.05)
    elif user.scenario == "nutrition_training_mismatch":
        if phase == "harder_training":
            progression = 7.5
        elif phase == "maintenance_recovery":
            progression = 10.0
        else:
            progression = min(7.5, story_index * 0.035)
    elif user.scenario == "recovery_limited":
        phase_adjustment = {
            "stable_start": 2.5,
            "schedule_disruption": 0.0,
            "attempted_return": 3.0,
            "recurring_stress": 1.0,
            "missed_training": -1.0,
            "recovery_swings": 2.0,
            "productive_return": 4.0,
        }
        progression = phase_adjustment.get(phase, 0.0)
    else:
        progression = workout_index * (
            0.12 if user.scenario != "data_quality_limited" else 0.04
        )
    return round(base + (exercise_index * 12.5) + progression, 1)


def _seed_workouts(
    cursor, user: LongitudinalQAUser, days: list[date]
) -> tuple[int, int]:
    exercise_ids = _legacy_exercise_ids(cursor)
    completed_workouts = 0
    actual_sets = 0

    for workout_index, day in enumerate(_workout_days(user, days)):
        days_remaining = (days[-1] - day).days
        exercises = _plan_exercises_for(
            user,
            workout_index,
            days_remaining=days_remaining,
        )
        title = _workout_title_for(
            user,
            workout_index,
            days_remaining=days_remaining,
        )
        duration = 45 if user.scenario == "data_quality_limited" else 55
        timestamp = _timestamp(day, hour=18, minute=workout_index % 50)
        approved_plan = _approved_plan_payload(
            title=title,
            scenario=user.scenario,
            exercises=exercises,
            duration_minutes=duration,
        )

        cursor.execute(
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
                user.user_id,
                user.scenario,
                approved_plan["confidence"],
                title,
                json.dumps(approved_plan, sort_keys=True),
                timestamp,
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        plan_instance_id = int(cursor.lastrowid)

        planned_ids: list[int] = []
        for exercise_order, exercise in enumerate(exercises, start=1):
            cursor.execute(
                """
                INSERT INTO planned_workout_exercises (
                    workout_plan_instance_id,
                    exercise_order,
                    name,
                    sets,
                    reps_min,
                    reps_max,
                    rir_min,
                    rir_max,
                    notes,
                    equipment_required_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_instance_id,
                    exercise_order,
                    exercise["name"],
                    exercise["sets"],
                    exercise["reps_min"],
                    exercise["reps_max"],
                    exercise["rir_min"],
                    exercise["rir_max"],
                    "Use controlled reps and log load, reps, and RIR.",
                    json.dumps(exercise["equipment_required"]),
                    timestamp,
                ),
            )
            planned_ids.append(int(cursor.lastrowid))

        cursor.execute(
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
                user.user_id,
                _iso(day),
                title,
                duration,
                "Planned execution row for longitudinal data foundation.",
                timestamp,
            ),
        )
        workout_session_id = int(cursor.lastrowid)

        cursor.execute(
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
                plan_instance_id,
                user.user_id,
                workout_session_id,
                timestamp,
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        execution_session_id = int(cursor.lastrowid)

        for exercise_index, exercise in enumerate(exercises, start=1):
            planned_id = planned_ids[exercise_index - 1]
            skipped_exercise = (
                user.scenario == "data_quality_limited"
                and (workout_index + exercise_index) % 4 == 0
            )
            logged_sets = exercise["sets"]
            if user.scenario == "data_quality_limited" and exercise_index == len(
                exercises
            ):
                logged_sets = max(1, exercise["sets"] - 1)
            if (
                user.scenario == "recovery_limited"
                and (workout_index + exercise_index) % 9 == 0
            ):
                logged_sets = max(1, exercise["sets"] - 1)

            for set_number in range(1, logged_sets + 1):
                actual_rir = _actual_rir_for(
                    user,
                    workout_index,
                    set_number,
                    days_remaining=days_remaining,
                )
                completed = not skipped_exercise
                actual_reps = None if skipped_exercise else exercise["reps_max"]
                actual_weight = (
                    None
                    if skipped_exercise
                    else _actual_weight_for(
                        user,
                        exercise_index,
                        workout_index,
                        days_remaining=days_remaining,
                    )
                )
                if (
                    user.scenario == "nutrition_training_mismatch"
                    and phase_id_for(user.user_id, days_remaining) == "harder_training"
                    and set_number == logged_sets
                    and exercise_index % 2 == 0
                ):
                    actual_reps = exercise["reps_min"] - 1
                if user.scenario == "data_quality_limited" and actual_rir is None:
                    actual_reps = exercise["reps_max"] if not skipped_exercise else None
                    completed = not skipped_exercise

                cursor.execute(
                    """
                    INSERT INTO workout_execution_set_actuals (
                        workout_execution_session_id,
                        planned_workout_exercise_id,
                        workout_session_id,
                        exercise_name,
                        set_number,
                        planned_reps_min,
                        planned_reps_max,
                        planned_rir_min,
                        planned_rir_max,
                        actual_reps,
                        actual_weight,
                        actual_rir,
                        completed,
                        skipped,
                        notes,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        execution_session_id,
                        planned_id,
                        workout_session_id,
                        exercise["name"],
                        set_number,
                        exercise["reps_min"],
                        exercise["reps_max"],
                        exercise["rir_min"],
                        exercise["rir_max"],
                        actual_reps,
                        actual_weight,
                        actual_rir,
                        1 if completed else 0,
                        1 if skipped_exercise else 0,
                        "Actual set row from longitudinal data foundation.",
                        timestamp,
                        timestamp,
                    ),
                )
                actual_sets += 1

                legacy_exercise_id = exercise_ids.get(exercise["name"])
                if (
                    legacy_exercise_id is not None
                    and completed
                    and actual_reps is not None
                ):
                    cursor.execute(
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
                            legacy_exercise_id,
                            set_number,
                            actual_reps,
                            actual_weight,
                            actual_rir,
                            timestamp,
                        ),
                    )

        completed_workouts += 1

    return completed_workouts, actual_sets


def seed_longitudinal_qa_data(
    *,
    end_date: date = DEFAULT_END_DATE,
    day_count: int = DEFAULT_DAY_COUNT,
) -> list[SeededLongitudinalQAUser]:
    """Seed users 101-105 with deterministic longitudinal QA data."""

    if day_count < 365:
        raise ValueError("day_count must be at least 365 for longitudinal QA data.")

    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    ensure_workout_exercise_memory_table()
    ensure_starter_canonical_foods_seeded()
    seed_exercise_catalog()

    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        _clear_existing_qa_user_data(cursor)
        _seed_users(cursor)
        _seed_workout_exercise_memories(cursor)
        food_ids = _ensure_legacy_foods_from_canonical(cursor)
        days = _date_series(end_date=end_date, day_count=day_count)

        seeded: list[SeededLongitudinalQAUser] = []
        for user in QA_USERS:
            recovery_count = _seed_recovery(cursor, user, days)
            nutrition_days, nutrition_entries = _seed_nutrition(
                cursor,
                user,
                days,
                food_ids,
            )
            completed_workouts, actual_sets = _seed_workouts(cursor, user, days)
            seeded.append(
                SeededLongitudinalQAUser(
                    user_id=user.user_id,
                    scenario=user.scenario,
                    recovery_checkins=recovery_count,
                    nutrition_days=nutrition_days,
                    nutrition_entries=nutrition_entries,
                    completed_workouts=completed_workouts,
                    actual_sets=actual_sets,
                )
            )

        conn.commit()
        return seeded
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--end-date",
        type=_parse_date,
        default=DEFAULT_END_DATE,
        help="Inclusive seed end date in YYYY-MM-DD format; defaults to today.",
    )
    parser.add_argument(
        "--day-count",
        type=int,
        default=DEFAULT_DAY_COUNT,
        help="Number of days to seed ending at --end-date.",
    )
    args = parser.parse_args()

    seeded = seed_longitudinal_qa_data(
        end_date=args.end_date,
        day_count=args.day_count,
    )
    print("Seeded longitudinal QA data:")
    for item in seeded:
        print(
            "- "
            f"user_id={item.user_id} "
            f"scenario={item.scenario} "
            f"recovery_checkins={item.recovery_checkins} "
            f"nutrition_days={item.nutrition_days} "
            f"nutrition_entries={item.nutrition_entries} "
            f"completed_workouts={item.completed_workouts} "
            f"actual_sets={item.actual_sets}"
        )
    print("Historical insight smoke anchors:")
    smoke_user_ids = {
        "recovery_deterioration": 104,
        "recovery_rebound": 104,
        "training_progression": 102,
        "training_rising_effort": 102,
        "sparse_data_control": 105,
        "strength_progression_phase": 104,
        "strength_plateau_phase": 104,
        "strength_deload_phase": 104,
        "fat_loss_phase": 103,
        "fat_loss_maintenance": 103,
        "variable_schedule_disruption": 101,
        "variable_schedule_return": 101,
    }
    for label, as_of_date in longitudinal_insight_qa_dates(args.end_date).items():
        user_id = smoke_user_ids[label]
        print(
            f"- {label}: GET /insights/longitudinal/{user_id}"
            f"?as_of_date={as_of_date.isoformat()}&max_insights=10"
        )


if __name__ == "__main__":
    main()
