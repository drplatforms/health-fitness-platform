"""Seed one isolated, deterministic Performance Studio demo history."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

import database
from services.exercise_catalog_service import seed_exercise_catalog
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)

PERFORMANCE_STUDIO_USER_ID = 106
PERFORMANCE_STUDIO_USER_NAME = "Performance Studio Demo"
PERFORMANCE_STUDIO_SCENARIO = "workout_performance_studio_qa_v1"
DEFAULT_END_DATE = date(2026, 7, 20)

_SESSION_DAY_OFFSETS = (
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
_BENCH_LOADS = (
    40.0,
    42.5,
    45.0,
    47.5,
    50.0,
    52.5,
    52.5,
    52.5,
    52.5,
    52.5,
    45.0,
    45.0,
    52.5,
    55.0,
    57.5,
    60.0,
    60.0,
    60.0,
    60.0,
    60.0,
    52.5,
    52.5,
    60.0,
    62.5,
)
_BENCH_RIRS = (
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


@dataclass(frozen=True)
class SeededPerformanceStudioQA:
    user_id: int
    completed_workout_count: int
    actual_set_count: int
    first_session_date: str
    last_session_date: str


@dataclass(frozen=True)
class _ExerciseLog:
    name: str
    measurement_type: str
    planned_sets: int
    reps_min: int | None
    reps_max: int | None
    target_duration_seconds: int | None
    target_distance_meters: float | None
    equipment: tuple[str, ...]
    actual_reps: tuple[int | None, ...]
    actual_durations: tuple[int | None, ...]
    actual_distances: tuple[float | None, ...]
    actual_weights: tuple[float | None, ...]
    actual_rirs: tuple[int | None, ...]


def seed_workout_performance_studio_qa(
    *,
    end_date: date = DEFAULT_END_DATE,
) -> SeededPerformanceStudioQA:
    """Replace only the marker-owned Performance Studio demo history."""

    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    seed_exercise_catalog()

    conn = database.get_connection()
    try:
        with conn:
            _ensure_demo_user(conn)
            _clear_marker_owned_history(conn)
            catalog_ids = _catalog_ids(conn)
            actual_set_count = 0
            for session_index, day_offset in enumerate(_SESSION_DAY_OFFSETS):
                session_date = end_date - timedelta(days=day_offset)
                actual_set_count += _insert_completed_workout(
                    conn,
                    catalog_ids=catalog_ids,
                    session_index=session_index,
                    session_date=session_date,
                )
    finally:
        conn.close()

    return SeededPerformanceStudioQA(
        user_id=PERFORMANCE_STUDIO_USER_ID,
        completed_workout_count=len(_SESSION_DAY_OFFSETS),
        actual_set_count=actual_set_count,
        first_session_date=(
            end_date - timedelta(days=_SESSION_DAY_OFFSETS[0])
        ).isoformat(),
        last_session_date=end_date.isoformat(),
    )


def _ensure_demo_user(conn) -> None:
    existing_id = conn.execute(
        "SELECT name FROM users WHERE id = ?",
        (PERFORMANCE_STUDIO_USER_ID,),
    ).fetchone()
    if existing_id is not None and existing_id["name"] != PERFORMANCE_STUDIO_USER_NAME:
        raise RuntimeError(
            f"User id {PERFORMANCE_STUDIO_USER_ID} already belongs to another user."
        )

    existing_name = conn.execute(
        "SELECT id FROM users WHERE name = ?",
        (PERFORMANCE_STUDIO_USER_NAME,),
    ).fetchone()
    if (
        existing_name is not None
        and int(existing_name["id"]) != PERFORMANCE_STUDIO_USER_ID
    ):
        raise RuntimeError(
            f"User name {PERFORMANCE_STUDIO_USER_NAME!r} already has another id."
        )

    conn.execute(
        """
        INSERT OR IGNORE INTO users (
            id,
            name,
            age,
            starting_weight,
            primary_goal,
            activity_level
        )
        VALUES (?, ?, 36, 182.0, 'Build strength and conditioning', 'moderate')
        """,
        (PERFORMANCE_STUDIO_USER_ID, PERFORMANCE_STUDIO_USER_NAME),
    )


def _clear_marker_owned_history(conn) -> None:
    plan_rows = conn.execute(
        """
        SELECT id
        FROM workout_plan_instances
        WHERE user_id = ? AND scenario = ?
        """,
        (PERFORMANCE_STUDIO_USER_ID, PERFORMANCE_STUDIO_SCENARIO),
    ).fetchall()
    plan_ids = [int(row["id"]) for row in plan_rows]
    if not plan_ids:
        return

    placeholders = ",".join("?" for _ in plan_ids)
    execution_rows = conn.execute(
        f"""
        SELECT id
        FROM workout_execution_sessions
        WHERE workout_plan_instance_id IN ({placeholders})
        """,
        plan_ids,
    ).fetchall()
    execution_ids = [int(row["id"]) for row in execution_rows]
    if execution_ids:
        execution_placeholders = ",".join("?" for _ in execution_ids)
        conn.execute(
            f"""
            DELETE FROM workout_execution_set_actuals
            WHERE workout_execution_session_id IN ({execution_placeholders})
            """,
            execution_ids,
        )
    conn.execute(
        f"""
        DELETE FROM workout_execution_sessions
        WHERE workout_plan_instance_id IN ({placeholders})
        """,
        plan_ids,
    )
    conn.execute(
        f"""
        DELETE FROM planned_workout_exercises
        WHERE workout_plan_instance_id IN ({placeholders})
        """,
        plan_ids,
    )
    conn.execute(
        f"DELETE FROM workout_plan_instances WHERE id IN ({placeholders})",
        plan_ids,
    )


def _catalog_ids(conn) -> dict[str, int]:
    required_names = {
        "Dumbbell Bench Press",
        "Pull-Up",
        "Plank",
        "Farmer Carry",
        "Treadmill Walk",
    }
    placeholders = ",".join("?" for _ in required_names)
    rows = conn.execute(
        f"""
        SELECT id, name
        FROM exercise_catalog_exercises
        WHERE name IN ({placeholders})
        """,
        sorted(required_names),
    ).fetchall()
    catalog_ids = {str(row["name"]): int(row["id"]) for row in rows}
    missing = sorted(required_names - catalog_ids.keys())
    if missing:
        raise RuntimeError(f"Missing required catalog exercises: {', '.join(missing)}")
    return catalog_ids


def _insert_completed_workout(
    conn,
    *,
    catalog_ids: dict[str, int],
    session_index: int,
    session_date: date,
) -> int:
    timestamp = datetime.combine(
        session_date,
        time(hour=18),
        tzinfo=UTC,
    ).isoformat()
    exercises = (
        _bench_log(session_index),
        _rotating_conditioning_log(session_index),
    )
    title = _workout_title(exercises[1].name)
    approved_plan = {
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
    cursor = conn.execute(
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
        VALUES (?, 'completed', ?, 'High', ?, ?, ?, ?, ?, ?)
        """,
        (
            PERFORMANCE_STUDIO_USER_ID,
            PERFORMANCE_STUDIO_SCENARIO,
            title,
            json.dumps(approved_plan, sort_keys=True),
            timestamp,
            timestamp,
            timestamp,
            timestamp,
        ),
    )
    plan_id = int(cursor.lastrowid)

    planned_ids: list[int] = []
    for exercise_order, exercise in enumerate(exercises, start=1):
        planned = conn.execute(
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
                1 if exercise.measurement_type == "reps" else None,
                3 if exercise.measurement_type == "reps" else None,
                "Use controlled form and record each completed set.",
                json.dumps(exercise.equipment),
                catalog_ids[exercise.name],
                timestamp,
            ),
        )
        planned_ids.append(int(planned.lastrowid))

    execution = conn.execute(
        """
        INSERT INTO workout_execution_sessions (
            workout_plan_instance_id,
            user_id,
            status,
            started_at,
            completed_at,
            created_at,
            updated_at
        )
        VALUES (?, ?, 'completed', ?, ?, ?, ?)
        """,
        (
            plan_id,
            PERFORMANCE_STUDIO_USER_ID,
            timestamp,
            timestamp,
            timestamp,
            timestamp,
        ),
    )
    execution_id = int(execution.lastrowid)

    actual_count = 0
    for planned_id, exercise in zip(planned_ids, exercises, strict=True):
        for set_index in range(len(exercise.actual_reps)):
            conn.execute(
                """
                INSERT INTO workout_execution_set_actuals (
                    workout_execution_session_id,
                    planned_workout_exercise_id,
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
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    1, 0, ?, ?, ?
                )
                """,
                (
                    execution_id,
                    planned_id,
                    exercise.name,
                    set_index + 1,
                    exercise.reps_min,
                    exercise.reps_max,
                    exercise.measurement_type,
                    exercise.target_duration_seconds,
                    exercise.target_distance_meters,
                    1 if exercise.measurement_type == "reps" else None,
                    3 if exercise.measurement_type == "reps" else None,
                    exercise.actual_reps[set_index],
                    exercise.actual_durations[set_index],
                    exercise.actual_distances[set_index],
                    exercise.actual_weights[set_index],
                    exercise.actual_rirs[set_index],
                    "Recorded during the completed workout.",
                    timestamp,
                    timestamp,
                ),
            )
            actual_count += 1
    return actual_count


def _bench_log(session_index: int) -> _ExerciseLog:
    completed_sets = 2 if session_index == 8 else 3
    rir = _BENCH_RIRS[session_index]
    return _ExerciseLog(
        name="Dumbbell Bench Press",
        measurement_type="reps",
        planned_sets=3,
        reps_min=8,
        reps_max=10,
        target_duration_seconds=None,
        target_distance_meters=None,
        equipment=("dumbbell", "adjustable_bench"),
        actual_reps=(10, 9, 8)[:completed_sets],
        actual_durations=(None, None, None)[:completed_sets],
        actual_distances=(None, None, None)[:completed_sets],
        actual_weights=(_BENCH_LOADS[session_index],) * completed_sets,
        actual_rirs=(rir,) * completed_sets,
    )


def _rotating_conditioning_log(session_index: int) -> _ExerciseLog:
    occurrence = session_index // 4
    variant = session_index % 4
    if variant == 0:
        reps = 6 + occurrence
        return _ExerciseLog(
            name="Pull-Up",
            measurement_type="reps",
            planned_sets=3,
            reps_min=5,
            reps_max=10,
            target_duration_seconds=None,
            target_distance_meters=None,
            equipment=("bodyweight",),
            actual_reps=(reps, max(1, reps - 1), max(1, reps - 2)),
            actual_durations=(None, None, None),
            actual_distances=(None, None, None),
            actual_weights=(None, None, None),
            actual_rirs=(3, 2, 2),
        )
    if variant == 1:
        duration = 35 + occurrence * 5
        return _ExerciseLog(
            name="Plank",
            measurement_type="duration",
            planned_sets=3,
            reps_min=None,
            reps_max=None,
            target_duration_seconds=duration,
            target_distance_meters=None,
            equipment=("bodyweight", "exercise_mat"),
            actual_reps=(None, None, None),
            actual_durations=(duration, duration + 3, duration),
            actual_distances=(None, None, None),
            actual_weights=(None, None, None),
            actual_rirs=(None, None, None),
        )
    if variant == 2:
        distance = 20.0 + occurrence * 5.0
        weight = 40.0 + occurrence * 2.5
        return _ExerciseLog(
            name="Farmer Carry",
            measurement_type="distance",
            planned_sets=3,
            reps_min=None,
            reps_max=None,
            target_duration_seconds=None,
            target_distance_meters=distance,
            equipment=("dumbbell",),
            actual_reps=(None, None, None),
            actual_durations=(None, None, None),
            actual_distances=(distance, distance, distance + 5.0),
            actual_weights=(weight, weight, weight),
            actual_rirs=(None, None, None),
        )

    distance = 800.0 + occurrence * 120.0
    return _ExerciseLog(
        name="Treadmill Walk",
        measurement_type="distance",
        planned_sets=1,
        reps_min=None,
        reps_max=None,
        target_duration_seconds=None,
        target_distance_meters=distance,
        equipment=("treadmill",),
        actual_reps=(None,),
        actual_durations=(None,),
        actual_distances=(distance,),
        actual_weights=(None,),
        actual_rirs=(None,),
    )


def _workout_title(second_exercise_name: str) -> str:
    if second_exercise_name in {"Pull-Up", "Plank"}:
        return "Upper Body Strength"
    return "Strength and Conditioning"


if __name__ == "__main__":
    seeded = seed_workout_performance_studio_qa()
    print(
        f"Seeded {seeded.completed_workout_count} completed workouts for "
        f"{PERFORMANCE_STUDIO_USER_NAME} (user {seeded.user_id})."
    )
