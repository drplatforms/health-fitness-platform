from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict
from datetime import UTC, datetime

from database import get_connection
from models.temporary_workout_limitation_models import (
    TemporaryWorkoutLimitation,
    WorkoutLimitationConflict,
)
from services.exercise_catalog_service import (
    find_catalog_entry_by_name,
    get_exercise_catalog,
    get_exercise_catalog_entry_by_id,
)

ALLOWED_AFFECTED_REGIONS = {
    "neck",
    "shoulder",
    "elbow",
    "wrist_hand",
    "upper_back",
    "lower_back",
    "hip",
    "knee",
    "ankle_foot",
}
MAX_AFFECTED_REGIONS = len(ALLOWED_AFFECTED_REGIONS)
MAX_RESTRICTED_MOVEMENT_PATTERNS = 20
MAX_EXCLUDED_CATALOG_EXERCISES = 50


class TemporaryWorkoutLimitationValidationError(ValueError):
    pass


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _unique(values: Iterable) -> list:
    return list(dict.fromkeys(values))


def _decode_list(raw_value: str | None) -> list:
    if not raw_value:
        return []
    try:
        value = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TemporaryWorkoutLimitationValidationError(
            "expires_at must be a valid ISO-8601 timestamp."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_active(
    limitation: TemporaryWorkoutLimitation, now: datetime | None = None
) -> bool:
    expires_at = _parse_timestamp(limitation.expires_at)
    if expires_at is None:
        return True
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return expires_at > current.astimezone(UTC)


def ensure_temporary_workout_limitation_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_temporary_workout_limitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            affected_regions_json TEXT NOT NULL,
            restricted_movement_patterns_json TEXT NOT NULL,
            excluded_catalog_exercise_ids_json TEXT NOT NULL,
            expires_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


def _row_to_limitation(row) -> TemporaryWorkoutLimitation:
    return TemporaryWorkoutLimitation(
        user_id=int(row["user_id"]),
        affected_regions=[
            _normalize_token(str(value))
            for value in _decode_list(row["affected_regions_json"])
        ],
        restricted_movement_patterns=[
            _normalize_token(str(value))
            for value in _decode_list(row["restricted_movement_patterns_json"])
        ],
        excluded_catalog_exercise_ids=[
            int(value)
            for value in _decode_list(row["excluded_catalog_exercise_ids_json"])
            if isinstance(value, int) and not isinstance(value, bool)
        ],
        expires_at=row["expires_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_temporary_workout_limitation(
    user_id: int,
) -> TemporaryWorkoutLimitation | None:
    ensure_temporary_workout_limitation_table()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user_temporary_workout_limitations WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_limitation(row) if row is not None else None


def get_active_temporary_workout_limitation(
    user_id: int,
    *,
    now: datetime | None = None,
) -> TemporaryWorkoutLimitation | None:
    limitation = get_temporary_workout_limitation(user_id)
    if limitation is None or not _is_active(limitation, now=now):
        return None
    return limitation


def _supported_movement_patterns() -> set[str]:
    return {
        _normalize_token(entry.movement_pattern)
        for entry in get_exercise_catalog()
        if entry.movement_pattern
    }


def save_temporary_workout_limitation(
    user_id: int,
    *,
    affected_regions: list[str] | None = None,
    restricted_movement_patterns: list[str] | None = None,
    excluded_catalog_exercise_ids: list[int] | None = None,
    expires_at: str | None = None,
    now: datetime | None = None,
) -> TemporaryWorkoutLimitation:
    regions = _unique(
        _normalize_token(str(value))
        for value in (affected_regions or [])
        if str(value).strip()
    )
    movements = _unique(
        _normalize_token(str(value))
        for value in (restricted_movement_patterns or [])
        if str(value).strip()
    )
    catalog_ids = _unique(excluded_catalog_exercise_ids or [])

    if len(regions) > MAX_AFFECTED_REGIONS or set(regions) - ALLOWED_AFFECTED_REGIONS:
        raise TemporaryWorkoutLimitationValidationError(
            "affected_regions contains an unsupported value."
        )
    if len(movements) > MAX_RESTRICTED_MOVEMENT_PATTERNS:
        raise TemporaryWorkoutLimitationValidationError(
            "restricted_movement_patterns exceeds the supported limit."
        )
    unsupported_movements = set(movements) - _supported_movement_patterns()
    if unsupported_movements:
        raise TemporaryWorkoutLimitationValidationError(
            "restricted_movement_patterns contains an unsupported catalog movement."
        )
    if len(catalog_ids) > MAX_EXCLUDED_CATALOG_EXERCISES:
        raise TemporaryWorkoutLimitationValidationError(
            "excluded_catalog_exercise_ids exceeds the supported limit."
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 1
        for value in catalog_ids
    ):
        raise TemporaryWorkoutLimitationValidationError(
            "excluded_catalog_exercise_ids must contain positive integer IDs."
        )
    missing_ids = [
        catalog_id
        for catalog_id in catalog_ids
        if get_exercise_catalog_entry_by_id(catalog_id) is None
    ]
    if missing_ids:
        raise TemporaryWorkoutLimitationValidationError(
            "excluded_catalog_exercise_ids contains an unknown catalog exercise."
        )
    if not movements and not catalog_ids:
        raise TemporaryWorkoutLimitationValidationError(
            "Select at least one movement pattern or catalog exercise to avoid."
        )

    normalized_expires_at = None
    if expires_at:
        parsed_expires_at = _parse_timestamp(expires_at)
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        if parsed_expires_at is None or parsed_expires_at <= current.astimezone(UTC):
            raise TemporaryWorkoutLimitationValidationError(
                "expires_at must be in the future."
            )
        normalized_expires_at = parsed_expires_at.isoformat().replace("+00:00", "Z")

    ensure_temporary_workout_limitation_table()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_temporary_workout_limitations (
            user_id,
            affected_regions_json,
            restricted_movement_patterns_json,
            excluded_catalog_exercise_ids_json,
            expires_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            affected_regions_json = excluded.affected_regions_json,
            restricted_movement_patterns_json = excluded.restricted_movement_patterns_json,
            excluded_catalog_exercise_ids_json = excluded.excluded_catalog_exercise_ids_json,
            expires_at = excluded.expires_at,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            json.dumps(regions),
            json.dumps(movements),
            json.dumps(catalog_ids),
            normalized_expires_at,
        ),
    )
    conn.commit()
    conn.close()

    limitation = get_temporary_workout_limitation(user_id)
    if limitation is None:
        raise RuntimeError("Failed to save temporary workout limitation.")
    return limitation


def clear_temporary_workout_limitation(user_id: int) -> bool:
    ensure_temporary_workout_limitation_table()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_temporary_workout_limitations WHERE user_id = ?",
        (user_id,),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def limitation_conflicts_for_exercises(
    limitation: TemporaryWorkoutLimitation | None,
    exercises: Iterable,
) -> list[WorkoutLimitationConflict]:
    if limitation is None:
        return []
    restricted_movements = set(limitation.restricted_movement_patterns)
    excluded_ids = set(limitation.excluded_catalog_exercise_ids)
    conflicts: list[WorkoutLimitationConflict] = []

    for exercise in exercises:
        name = str(getattr(exercise, "name", "")).strip()
        catalog_id = getattr(exercise, "catalog_exercise_id", None)
        planned_exercise_id = getattr(exercise, "id", None)
        entry = (
            get_exercise_catalog_entry_by_id(catalog_id)
            if catalog_id is not None
            else find_catalog_entry_by_name(name)
        )
        movement_pattern = entry.movement_pattern if entry is not None else None
        effective_catalog_id = entry.id if entry is not None else catalog_id

        if effective_catalog_id in excluded_ids:
            conflicts.append(
                WorkoutLimitationConflict(
                    planned_exercise_id=planned_exercise_id,
                    exercise_name=name,
                    conflict_type="excluded_catalog_exercise",
                    movement_pattern=movement_pattern,
                )
            )
        elif movement_pattern in restricted_movements:
            conflicts.append(
                WorkoutLimitationConflict(
                    planned_exercise_id=planned_exercise_id,
                    exercise_name=name,
                    conflict_type="restricted_movement_pattern",
                    movement_pattern=movement_pattern,
                )
            )
    return conflicts


def get_current_plan_limitation_conflicts(
    user_id: int,
) -> list[WorkoutLimitationConflict]:
    limitation = get_active_temporary_workout_limitation(user_id)
    if limitation is None:
        return []
    try:
        from services.workout_daily_state_service import resolve_workout_daily_state

        daily_state = resolve_workout_daily_state(user_id)
        plan_instance_id = daily_state.selected_plan_id or daily_state.active_plan_id
        if daily_state.state not in {"selected_today", "active_today"}:
            return []
        if plan_instance_id is None:
            return []
    except Exception:
        return []

    return get_plan_limitation_conflicts(user_id, plan_instance_id)


def get_plan_limitation_conflicts(
    user_id: int,
    plan_instance_id: int,
) -> list[WorkoutLimitationConflict]:
    limitation = get_active_temporary_workout_limitation(user_id)
    if limitation is None:
        return []
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                pwe.id,
                COALESCE(sub.replacement_exercise_name, pwe.name) AS name,
                COALESCE(
                    sub.replacement_catalog_exercise_id,
                    pwe.catalog_exercise_id
                ) AS catalog_exercise_id
            FROM planned_workout_exercises pwe
            LEFT JOIN workout_plan_exercise_substitutions sub
              ON sub.planned_workout_exercise_id = pwe.id
             AND sub.workout_plan_instance_id = pwe.workout_plan_instance_id
             AND sub.status = 'active'
            WHERE pwe.workout_plan_instance_id = ?
            ORDER BY pwe.exercise_order
            """,
            (plan_instance_id,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    class ExerciseRow:
        def __init__(self, row):
            self.id = int(row["id"])
            self.name = str(row["name"])
            self.catalog_exercise_id = row["catalog_exercise_id"]

    return limitation_conflicts_for_exercises(
        limitation,
        [ExerciseRow(row) for row in rows],
    )


def temporary_workout_limitation_response(user_id: int) -> dict:
    limitation = get_active_temporary_workout_limitation(user_id)
    return {
        "success": True,
        "user_id": user_id,
        "active": limitation is not None,
        "limitation": asdict(limitation) if limitation is not None else None,
        "current_plan_conflicts": [
            asdict(conflict)
            for conflict in get_current_plan_limitation_conflicts(user_id)
        ],
    }
