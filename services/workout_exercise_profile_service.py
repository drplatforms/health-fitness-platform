from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from database import get_connection
from services.exercise_catalog_service import get_exercise_catalog

MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE = 24
FAMILIARITY_STATES = frozenset({"unfamiliar", "learning", "familiar"})
PREFERENCE_STATES = frozenset({"favorite", "disliked"})


class WorkoutExerciseProfileError(Exception):
    """Base error for explicit user-owned exercise profiles."""


class WorkoutExerciseProfileValidationError(WorkoutExerciseProfileError):
    """Raised when an exercise-profile request is invalid."""


class WorkoutExerciseProfileNotFoundError(WorkoutExerciseProfileError):
    """Raised when a requested user or catalog exercise does not exist."""


@dataclass(frozen=True)
class WorkoutExerciseProfile:
    profile_id: int
    catalog_exercise_id: int
    familiarity_state: str | None
    preference_state: str | None
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class WorkoutExerciseProfileResolution:
    requested_catalog_exercise_id: int
    profile: WorkoutExerciseProfile | None


def ensure_workout_exercise_profile_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_exercise_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        catalog_exercise_id INTEGER NOT NULL,
        familiarity_state TEXT,
        preference_state TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(user_id, catalog_exercise_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (catalog_exercise_id) REFERENCES exercise_catalog_exercises(id),
        CHECK (
            familiarity_state IS NULL
            OR familiarity_state IN ('unfamiliar', 'learning', 'familiar')
        ),
        CHECK (
            preference_state IS NULL
            OR preference_state IN ('favorite', 'disliked')
        )
    )
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_workout_exercise_profiles_user_preference
    ON workout_exercise_profiles(user_id, preference_state)
    """)
    conn.commit()
    conn.close()


def resolve_workout_exercise_profiles(
    user_id: int,
    catalog_exercise_ids: Iterable[int],
) -> list[WorkoutExerciseProfileResolution]:
    requested_ids = _validate_catalog_id_batch(catalog_exercise_ids)
    _validate_catalog_ids_exist(requested_ids)
    ensure_workout_exercise_profile_table()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        _validate_user(cursor, user_id)
        placeholders = ",".join("?" for _ in requested_ids)
        rows = cursor.execute(
            f"""
            SELECT *
            FROM workout_exercise_profiles
            WHERE user_id = ?
              AND catalog_exercise_id IN ({placeholders})
            """,
            (int(user_id), *requested_ids),
        ).fetchall()
        profiles_by_catalog_id = {
            int(row["catalog_exercise_id"]): _profile_from_row(row) for row in rows
        }
        return [
            WorkoutExerciseProfileResolution(
                requested_catalog_exercise_id=catalog_exercise_id,
                profile=profiles_by_catalog_id.get(catalog_exercise_id),
            )
            for catalog_exercise_id in requested_ids
        ]
    finally:
        conn.close()


def save_workout_exercise_profile(
    user_id: int,
    *,
    catalog_exercise_id: int,
    familiarity_state: str | None,
    preference_state: str | None,
) -> WorkoutExerciseProfile | None:
    catalog_id = _validate_catalog_exercise_id(catalog_exercise_id)
    familiarity = _validate_optional_state(
        familiarity_state,
        allowed=FAMILIARITY_STATES,
        field_name="familiarity_state",
    )
    preference = _validate_optional_state(
        preference_state,
        allowed=PREFERENCE_STATES,
        field_name="preference_state",
    )
    _validate_catalog_ids_exist([catalog_id])
    ensure_workout_exercise_profile_table()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        _validate_user(cursor, user_id)
        if familiarity is None and preference is None:
            cursor.execute(
                """
                DELETE FROM workout_exercise_profiles
                WHERE user_id = ? AND catalog_exercise_id = ?
                """,
                (int(user_id), catalog_id),
            )
            conn.commit()
            return None

        cursor.execute(
            """
            INSERT INTO workout_exercise_profiles (
                user_id,
                catalog_exercise_id,
                familiarity_state,
                preference_state
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, catalog_exercise_id) DO UPDATE SET
                familiarity_state = excluded.familiarity_state,
                preference_state = excluded.preference_state,
                updated_at = CURRENT_TIMESTAMP
            """,
            (int(user_id), catalog_id, familiarity, preference),
        )
        conn.commit()
        row = cursor.execute(
            """
            SELECT * FROM workout_exercise_profiles
            WHERE user_id = ? AND catalog_exercise_id = ?
            """,
            (int(user_id), catalog_id),
        ).fetchone()
        if row is None:
            raise WorkoutExerciseProfileNotFoundError(
                "Exercise profile could not be loaded after saving."
            )
        return _profile_from_row(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_workout_exercise_profile(
    user_id: int,
    catalog_exercise_id: int,
) -> bool:
    catalog_id = _validate_catalog_exercise_id(catalog_exercise_id)
    _validate_catalog_ids_exist([catalog_id])
    ensure_workout_exercise_profile_table()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        _validate_user(cursor, user_id)
        cursor.execute(
            """
            DELETE FROM workout_exercise_profiles
            WHERE user_id = ? AND catalog_exercise_id = ?
            """,
            (int(user_id), catalog_id),
        )
        deleted = cursor.rowcount == 1
        conn.commit()
        return deleted
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_workout_exercise_preference_map(user_id: int) -> dict[int, str]:
    """Read one user's explicit preferences without initializing schema.

    Workout generation and substitution use this read-only seam so a missing
    profile table preserves legacy deterministic behavior and cannot cause an
    additive migration during unrelated validation.
    """

    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError):
        return {}
    if parsed_user_id <= 0:
        return {}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        table_exists = cursor.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'workout_exercise_profiles'
            """
        ).fetchone()
        if table_exists is None:
            return {}
        rows = cursor.execute(
            """
            SELECT catalog_exercise_id, preference_state
            FROM workout_exercise_profiles
            WHERE user_id = ? AND preference_state IS NOT NULL
            """,
            (parsed_user_id,),
        ).fetchall()
        return {
            int(row["catalog_exercise_id"]): str(row["preference_state"])
            for row in rows
            if row["preference_state"] in PREFERENCE_STATES
        }
    finally:
        conn.close()


def _validate_catalog_id_batch(catalog_exercise_ids: Iterable[int]) -> list[int]:
    requested = list(catalog_exercise_ids)
    if not requested:
        raise WorkoutExerciseProfileValidationError(
            "At least one catalog exercise ID is required."
        )
    if len(requested) > MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE:
        raise WorkoutExerciseProfileValidationError(
            "Exercise-profile batches are limited to "
            f"{MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE} exercises."
        )

    unique_ids: list[int] = []
    seen: set[int] = set()
    for value in requested:
        catalog_id = _validate_catalog_exercise_id(value)
        if catalog_id in seen:
            continue
        seen.add(catalog_id)
        unique_ids.append(catalog_id)
    return unique_ids


def _validate_catalog_exercise_id(value: Any) -> int:
    if isinstance(value, bool):
        raise WorkoutExerciseProfileValidationError(
            "catalog_exercise_id must be a positive integer."
        )
    try:
        catalog_id = int(value)
    except (TypeError, ValueError) as exc:
        raise WorkoutExerciseProfileValidationError(
            "catalog_exercise_id must be a positive integer."
        ) from exc
    if catalog_id <= 0:
        raise WorkoutExerciseProfileValidationError(
            "catalog_exercise_id must be a positive integer."
        )
    return catalog_id


def _validate_catalog_ids_exist(catalog_exercise_ids: list[int]) -> None:
    existing_ids = {
        int(entry.id)
        for entry in get_exercise_catalog()
        if entry.id is not None and int(entry.id) in catalog_exercise_ids
    }
    missing_ids = [
        catalog_id
        for catalog_id in catalog_exercise_ids
        if catalog_id not in existing_ids
    ]
    if missing_ids:
        raise WorkoutExerciseProfileNotFoundError(
            f"Catalog exercise {missing_ids[0]} was not found."
        )


def _validate_optional_state(
    value: str | None,
    *,
    allowed: frozenset[str],
    field_name: str,
) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if not normalized:
        return None
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise WorkoutExerciseProfileValidationError(
            f"{field_name} must be one of: {allowed_values}, or unset."
        )
    return normalized


def _validate_user(cursor: Any, user_id: int) -> None:
    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise WorkoutExerciseProfileValidationError(
            "user_id must be a positive integer."
        ) from exc
    if parsed_user_id <= 0:
        raise WorkoutExerciseProfileValidationError(
            "user_id must be a positive integer."
        )
    if (
        cursor.execute("SELECT 1 FROM users WHERE id = ?", (parsed_user_id,)).fetchone()
        is None
    ):
        raise WorkoutExerciseProfileNotFoundError("User was not found.")


def _profile_from_row(row: Any) -> WorkoutExerciseProfile:
    return WorkoutExerciseProfile(
        profile_id=int(row["id"]),
        catalog_exercise_id=int(row["catalog_exercise_id"]),
        familiarity_state=_nullable_str(row["familiarity_state"]),
        preference_state=_nullable_str(row["preference_state"]),
        created_at=_nullable_str(row["created_at"]),
        updated_at=_nullable_str(row["updated_at"]),
    )


def _nullable_str(value: Any) -> str | None:
    return None if value is None else str(value)
