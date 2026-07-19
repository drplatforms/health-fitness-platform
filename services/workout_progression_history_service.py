from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean
from typing import Any

from database import get_connection

DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_HISTORY_LIMIT = 5
SOURCE_TABLES = [
    "workout_plan_instances",
    "planned_workout_exercises",
    "workout_execution_sessions",
    "workout_execution_set_actuals",
]


@dataclass(frozen=True)
class WorkoutExerciseRecentSession:
    workout_plan_instance_id: int
    workout_execution_session_id: int
    performed_at: str | None
    completed_set_count: int
    planned_set_count: int
    summary: str


@dataclass(frozen=True)
class WorkoutExerciseBestSet:
    performed_at: str | None
    actual_reps: int | None
    actual_weight: float | None
    actual_rir: int | None
    summary: str


@dataclass(frozen=True)
class WorkoutExerciseHistorySummary:
    exercise_name: str
    has_history: bool
    completed_session_count: int
    last_performed_at: str | None
    last_session_summary: str | None
    recent_best_set: WorkoutExerciseBestSet | None
    logging_quality: str
    message: str


@dataclass(frozen=True)
class ExerciseProgressionSession:
    workout_plan_instance_id: int
    workout_execution_session_id: int
    performed_at: str | None
    planned_exercise_id: int
    planned_set_count: int
    effective_exercise_name: str
    effective_catalog_exercise_id: int | None
    actual_rows: list[dict[str, Any]]


def build_workout_progression_history(
    user_id: int,
    planned_exercises: Iterable[str | dict[str, Any]],
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    limit: int = DEFAULT_HISTORY_LIMIT,
) -> list[WorkoutExerciseHistorySummary]:
    """Build bounded, read-only exercise history for a planned workout."""

    exercise_names = _unique_names(_exercise_name(item) for item in planned_exercises)
    return [
        build_exercise_history_summary(
            user_id=user_id,
            exercise_name_or_id=name,
            lookback_days=lookback_days,
            limit=limit,
        )
        for name in exercise_names
    ]


def build_exercise_history_summary(
    user_id: int,
    exercise_name_or_id: str,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    limit: int = DEFAULT_HISTORY_LIMIT,
) -> WorkoutExerciseHistorySummary:
    """Summarize recent completed planned-workout history for one exercise."""

    exercise_name = str(exercise_name_or_id or "").strip()
    if not exercise_name:
        return _empty_summary("Unknown exercise")

    sessions = load_completed_exercise_progression_sessions(
        user_id=user_id,
        exercise_name=exercise_name,
        lookback_days=lookback_days,
        limit=limit,
    )
    if not sessions:
        return _empty_summary(exercise_name)

    recent_sessions = [_summarize_recent_session(session) for session in sessions]
    best_set = _best_set(sessions)
    logging_quality = _logging_quality(sessions)
    message = _message(logging_quality)
    last_session = recent_sessions[0]

    return WorkoutExerciseHistorySummary(
        exercise_name=exercise_name,
        has_history=True,
        completed_session_count=len(sessions),
        last_performed_at=last_session.performed_at,
        last_session_summary=last_session.summary,
        recent_best_set=best_set,
        logging_quality=logging_quality,
        message=message,
    )


def load_completed_exercise_progression_sessions(
    *,
    user_id: int,
    exercise_name: str,
    catalog_exercise_id: int | None = None,
    lookback_days: int,
    limit: int,
) -> list[ExerciseProgressionSession]:
    """Load ordered, substitution-aware completed-session evidence.

    This is an internal service boundary shared by the read-only history summary
    and the advisory progression engine. Public history response shapes remain
    unchanged.
    """

    normalized_target = _normalize_name(exercise_name)
    if not normalized_target and catalog_exercise_id is None:
        return []

    return _load_completed_progression_sessions(
        user_id=user_id,
        lookback_days=lookback_days,
        limit=max(1, int(limit)),
        normalized_target=normalized_target,
        catalog_exercise_id=catalog_exercise_id,
    )


def load_completed_user_progression_sessions(
    *,
    user_id: int,
    lookback_days: int,
) -> list[ExerciseProgressionSession]:
    """Load all effective exercise exposures from completed planned workouts."""

    return _load_completed_progression_sessions(
        user_id=user_id,
        lookback_days=lookback_days,
        limit=None,
        normalized_target=None,
        catalog_exercise_id=None,
    )


def _load_completed_progression_sessions(
    *,
    user_id: int,
    lookback_days: int,
    limit: int | None,
    normalized_target: str | None,
    catalog_exercise_id: int | None,
) -> list[ExerciseProgressionSession]:
    """Load shared substitution-aware completed-session evidence."""

    conn = get_connection()
    cursor = conn.cursor()
    if not _required_tables_exist(cursor):
        conn.close()
        return []

    cutoff = (date.today() - timedelta(days=max(1, int(lookback_days)))).isoformat()
    wpi_columns = _column_names(cursor, "workout_plan_instances")
    pwe_columns = _column_names(cursor, "planned_workout_exercises")
    planned_catalog_expr = (
        "pwe.catalog_exercise_id" if "catalog_exercise_id" in pwe_columns else "NULL"
    )
    planned_measurement_expr = (
        "COALESCE(pwe.measurement_type, 'reps')"
        if "measurement_type" in pwe_columns
        else "'reps'"
    )
    plan_completed_at = "wpi.completed_at" if "completed_at" in wpi_columns else "NULL"
    performed_at_expr = f"COALESCE(wes.completed_at, {plan_completed_at}, wpi.selected_at, wpi.created_at)"
    rows = cursor.execute(
        f"""
        SELECT wpi.id AS workout_plan_instance_id,
               wes.id AS workout_execution_session_id,
               {performed_at_expr} AS performed_at,
               pwe.id AS planned_exercise_id,
               pwe.name AS planned_exercise_name,
               pwe.sets AS planned_set_count,
               {planned_measurement_expr} AS planned_measurement_type,
               {planned_catalog_expr} AS planned_catalog_exercise_id
        FROM workout_plan_instances AS wpi
        JOIN workout_execution_sessions AS wes
          ON wes.workout_plan_instance_id = wpi.id
        JOIN planned_workout_exercises AS pwe
          ON pwe.workout_plan_instance_id = wpi.id
        WHERE wpi.user_id = ?
          AND wpi.status = 'completed'
          AND wes.status = 'completed'
          AND date({performed_at_expr}) >= date(?)
        ORDER BY performed_at DESC, wpi.id DESC, pwe.exercise_order ASC
        """,
        (user_id, cutoff),
    ).fetchall()

    substitution_table_exists = _table_exists(
        cursor, "workout_plan_exercise_substitutions"
    )
    matches: list[ExerciseProgressionSession] = []
    for row in rows:
        if row["planned_measurement_type"] != "reps":
            continue
        planned_name = str(row["planned_exercise_name"] or "")
        replacement_name: str | None = None
        replacement_catalog_exercise_id: int | None = None
        if substitution_table_exists:
            substitution = cursor.execute(
                """
                SELECT replacement_exercise_name,
                       replacement_catalog_exercise_id
                FROM workout_plan_exercise_substitutions
                WHERE workout_plan_instance_id = ?
                  AND planned_workout_exercise_id = ?
                  AND status = 'active'
                ORDER BY updated_at DESC,
                         id DESC
                LIMIT 1
                """,
                (
                    int(row["workout_plan_instance_id"]),
                    int(row["planned_exercise_id"]),
                ),
            ).fetchone()
            if substitution is not None:
                replacement_name = (
                    str(substitution["replacement_exercise_name"] or "").strip() or None
                )
                replacement_catalog_exercise_id = _nullable_int(
                    substitution["replacement_catalog_exercise_id"]
                )

        effective_name = replacement_name or planned_name
        effective_catalog_exercise_id = (
            replacement_catalog_exercise_id
            if replacement_name is not None
            else _nullable_int(row["planned_catalog_exercise_id"])
        )
        if normalized_target is not None or catalog_exercise_id is not None:
            if (
                catalog_exercise_id is not None
                and effective_catalog_exercise_id is not None
            ):
                identity_matches = effective_catalog_exercise_id == int(
                    catalog_exercise_id
                )
            else:
                identity_matches = _normalize_name(effective_name) == normalized_target
            if not identity_matches:
                continue

        actual_rows = cursor.execute(
            """
            SELECT id,
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
                   created_at
            FROM workout_execution_set_actuals
            WHERE workout_execution_session_id = ?
              AND (
                planned_workout_exercise_id = ?
                OR substitution_for_planned_exercise_id = ?
                OR LOWER(TRIM(exercise_name)) = LOWER(TRIM(?))
                OR LOWER(TRIM(exercise_name)) = LOWER(TRIM(?))
              )
            ORDER BY set_number ASC, id ASC
            """,
            (
                int(row["workout_execution_session_id"]),
                int(row["planned_exercise_id"]),
                int(row["planned_exercise_id"]),
                planned_name,
                effective_name,
            ),
        ).fetchall()
        matches.append(
            ExerciseProgressionSession(
                workout_plan_instance_id=int(row["workout_plan_instance_id"]),
                workout_execution_session_id=int(row["workout_execution_session_id"]),
                performed_at=_date_part(row["performed_at"]),
                planned_exercise_id=int(row["planned_exercise_id"]),
                planned_set_count=_safe_int(row["planned_set_count"]),
                effective_exercise_name=effective_name,
                effective_catalog_exercise_id=effective_catalog_exercise_id,
                actual_rows=[dict(actual) for actual in actual_rows],
            )
        )
        if limit is not None and len(matches) >= limit:
            break

    conn.close()
    return matches


def summarize_exercise_progression_session(
    session: ExerciseProgressionSession,
) -> WorkoutExerciseRecentSession:
    """Return the existing deterministic compact session summary."""

    return _summarize_recent_session(session)


def select_recent_best_set(
    sessions: list[ExerciseProgressionSession],
) -> WorkoutExerciseBestSet | None:
    """Apply the existing public recent-best-set semantics to loaded evidence."""

    return _best_set(sessions)


def classify_exercise_history_logging_quality(
    sessions: list[ExerciseProgressionSession],
) -> str:
    """Classify exercise-history completeness without changing its semantics."""

    return _logging_quality(sessions)


def completed_exercise_actual_rows(
    session: ExerciseProgressionSession,
) -> list[dict[str, Any]]:
    """Return completed, non-skipped rows for factual descriptive analytics."""

    return _completed_rows(session.actual_rows)


def _summarize_recent_session(
    session: ExerciseProgressionSession,
) -> WorkoutExerciseRecentSession:
    completed_rows = _completed_rows(session.actual_rows)
    return WorkoutExerciseRecentSession(
        workout_plan_instance_id=session.workout_plan_instance_id,
        workout_execution_session_id=session.workout_execution_session_id,
        performed_at=session.performed_at,
        completed_set_count=len(completed_rows),
        planned_set_count=session.planned_set_count,
        summary=_session_summary(completed_rows),
    )


def _best_set(
    sessions: list[ExerciseProgressionSession],
) -> WorkoutExerciseBestSet | None:
    completed = [
        (session, row)
        for session in sessions
        for row in _completed_rows(session.actual_rows)
        if row.get("actual_reps") is not None
    ]
    if not completed:
        return None
    session, row = max(
        completed,
        key=lambda item: (
            _safe_int(item[1].get("actual_reps")),
            _safe_float(item[1].get("actual_weight")) or 0.0,
            item[0].performed_at or "",
        ),
    )
    return WorkoutExerciseBestSet(
        performed_at=session.performed_at,
        actual_reps=_nullable_int(row.get("actual_reps")),
        actual_weight=_nullable_float(row.get("actual_weight")),
        actual_rir=_nullable_int(row.get("actual_rir")),
        summary=_set_summary(row),
    )


def _session_summary(completed_rows: list[dict[str, Any]]) -> str:
    if not completed_rows:
        return "No completed sets logged last time."

    set_count = len(completed_rows)
    reps_values = [_nullable_int(row.get("actual_reps")) for row in completed_rows]
    reps_values = [value for value in reps_values if value is not None]
    if reps_values:
        if min(reps_values) == max(reps_values):
            rep_part = f"{set_count}x{reps_values[0]}"
        else:
            rep_part = f"{set_count} sets x {min(reps_values)}-{max(reps_values)} reps"
    else:
        rep_part = f"{set_count} completed sets"

    details = [rep_part]
    weight_part = _weight_summary(completed_rows)
    if weight_part:
        details.append(weight_part)
    rir_part = _rir_summary(completed_rows)
    if rir_part:
        details.append(rir_part)
    return ", ".join(details)


def _set_summary(row: dict[str, Any]) -> str:
    pieces = []
    reps = _nullable_int(row.get("actual_reps"))
    weight = _nullable_float(row.get("actual_weight"))
    rir = _nullable_int(row.get("actual_rir"))
    if reps is not None:
        pieces.append(f"{reps} reps")
    if weight is not None:
        pieces.append(f"@ {_format_number(weight)} lb")
    if rir is not None:
        pieces.append(f"RIR {rir}")
    return " ".join(pieces) if pieces else "Completed set"


def _weight_summary(rows: list[dict[str, Any]]) -> str | None:
    weights = [_nullable_float(row.get("actual_weight")) for row in rows]
    weights = [weight for weight in weights if weight is not None]
    if not weights:
        return None
    if min(weights) == max(weights):
        return f"@ {_format_number(weights[0])} lb"
    return f"@ {_format_number(round(mean(weights), 1))} lb avg"


def _rir_summary(rows: list[dict[str, Any]]) -> str | None:
    rirs = [_nullable_int(row.get("actual_rir")) for row in rows]
    rirs = [rir for rir in rirs if rir is not None]
    if not rirs:
        return None
    if min(rirs) == max(rirs):
        return f"RIR {rirs[0]}"
    return f"avg RIR {_format_number(round(mean(rirs), 1))}"


def _logging_quality(sessions: list[ExerciseProgressionSession]) -> str:
    planned = sum(session.planned_set_count for session in sessions)
    rows = [row for session in sessions for row in session.actual_rows]
    completed = _completed_rows(rows)
    if planned <= 0:
        return "limited"
    if not completed:
        return "limited"
    missing_sets = planned - len(completed)
    missing_reps = sum(1 for row in completed if row.get("actual_reps") is None)
    missing_rir = sum(1 for row in completed if row.get("actual_rir") is None)
    if missing_sets > 0 or missing_reps or missing_rir:
        return "incomplete"
    return "complete"


def _message(logging_quality: str) -> str:
    if logging_quality in {"limited", "incomplete"}:
        return "Recent history is limited because prior set logging is incomplete."
    return "Recent completed workout history is available."


def _empty_summary(exercise_name: str) -> WorkoutExerciseHistorySummary:
    return WorkoutExerciseHistorySummary(
        exercise_name=exercise_name,
        has_history=False,
        completed_session_count=0,
        last_performed_at=None,
        last_session_summary=None,
        recent_best_set=None,
        logging_quality="none",
        message="No recent history for this exercise yet.",
    )


def _completed_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if _is_truthy(row.get("completed")) and not _is_truthy(row.get("skipped"))
    ]


def _exercise_name(item: str | dict[str, Any]) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or item.get("exercise_name") or "").strip()
    return str(item or "").strip()


def _unique_names(values: Iterable[str]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for value in values:
        name = str(value or "").strip()
        normalized = _normalize_name(name)
        if not name or normalized in seen:
            continue
        names.append(name)
        seen.add(normalized)
    return names


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _required_tables_exist(cursor: Any) -> bool:
    rows = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    return set(SOURCE_TABLES).issubset({str(row["name"]) for row in rows})


def _table_exists(cursor: Any, table_name: str) -> bool:
    return (
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        is not None
    )


def _column_names(cursor: Any, table_name: str) -> set[str]:
    rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _date_part(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)[:10]


def _is_truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _nullable_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _nullable_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _format_number(value: float | int) -> str:
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.1f}"
