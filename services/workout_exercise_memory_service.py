from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from database import get_connection

MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS = 500
MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE = 24
MAX_WORKOUT_EXERCISE_NAME_CHARACTERS = 200


class WorkoutExerciseMemoryError(Exception):
    """Base error for explicit user-owned exercise memories."""


class WorkoutExerciseMemoryValidationError(WorkoutExerciseMemoryError):
    """Raised when an exercise-memory request is invalid."""


class WorkoutExerciseMemoryNotFoundError(WorkoutExerciseMemoryError):
    """Raised when a user-owned exercise memory cannot be found."""


class WorkoutExerciseMemoryConflictError(WorkoutExerciseMemoryError):
    """Raised when a requested identity promotion is not safe."""


@dataclass(frozen=True)
class WorkoutExerciseMemory:
    memory_id: int
    catalog_exercise_id: int | None
    exercise_name: str
    memory_text: str
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class WorkoutExerciseMemoryResolution:
    requested_catalog_exercise_id: int | None
    requested_exercise_name: str
    memory: WorkoutExerciseMemory | None


def normalize_workout_exercise_memory_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def build_workout_exercise_memory_identity_key(
    catalog_exercise_id: int | None,
    exercise_name: str,
) -> str:
    catalog_id, _, normalized_name = _validate_exercise_identity(
        catalog_exercise_id,
        exercise_name,
    )
    if catalog_id is not None:
        return f"catalog:{catalog_id}"
    return f"name:{normalized_name}"


def ensure_workout_exercise_memory_table() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_exercise_memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        identity_key TEXT NOT NULL,
        catalog_exercise_id INTEGER,
        exercise_name TEXT NOT NULL,
        normalized_exercise_name TEXT NOT NULL,
        memory_text TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(user_id, identity_key),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_workout_exercise_memories_user_name
    ON workout_exercise_memories(user_id, normalized_exercise_name)
    """)
    conn.commit()
    conn.close()


def resolve_workout_exercise_memories(
    user_id: int,
    exercises: Iterable[dict[str, Any]],
) -> list[WorkoutExerciseMemoryResolution]:
    requested_exercises = list(exercises)
    if not requested_exercises:
        raise WorkoutExerciseMemoryValidationError("At least one exercise is required.")
    if len(requested_exercises) > MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE:
        raise WorkoutExerciseMemoryValidationError(
            "Exercise-memory batches are limited to "
            f"{MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE} exercises."
        )

    unique_requests: list[tuple[int | None, str, str]] = []
    seen: set[str] = set()
    for exercise in requested_exercises:
        catalog_id, exercise_name, normalized_name = _validate_exercise_identity(
            exercise.get("catalog_exercise_id"),
            exercise.get("exercise_name"),
        )
        identity_key = (
            f"catalog:{catalog_id}"
            if catalog_id is not None
            else f"name:{normalized_name}"
        )
        if identity_key in seen:
            continue
        seen.add(identity_key)
        unique_requests.append((catalog_id, exercise_name, normalized_name))

    ensure_workout_exercise_memory_table()
    conn = get_connection()
    cursor = conn.cursor()
    _validate_user(cursor, user_id)
    resolutions = [
        WorkoutExerciseMemoryResolution(
            requested_catalog_exercise_id=catalog_id,
            requested_exercise_name=exercise_name,
            memory=_resolve_memory(
                cursor,
                user_id=user_id,
                catalog_exercise_id=catalog_id,
                normalized_exercise_name=normalized_name,
            ),
        )
        for catalog_id, exercise_name, normalized_name in unique_requests
    ]
    conn.close()
    return resolutions


def save_workout_exercise_memory(
    user_id: int,
    *,
    catalog_exercise_id: int | None,
    exercise_name: str,
    memory_text: str,
    memory_id: int | None = None,
) -> WorkoutExerciseMemory:
    catalog_id, cleaned_name, normalized_name = _validate_exercise_identity(
        catalog_exercise_id,
        exercise_name,
    )
    cleaned_memory_text = str(memory_text or "").strip()
    if not cleaned_memory_text:
        raise WorkoutExerciseMemoryValidationError("Memory text is required.")
    if len(cleaned_memory_text) > MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS:
        raise WorkoutExerciseMemoryValidationError(
            "Memory text must be "
            f"{MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS} characters or fewer."
        )
    if memory_id is not None and int(memory_id) <= 0:
        raise WorkoutExerciseMemoryValidationError(
            "memory_id must be a positive integer."
        )

    ensure_workout_exercise_memory_table()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _validate_user(cursor, user_id)
        selected_row = None
        if memory_id is not None:
            selected_row = cursor.execute(
                "SELECT * FROM workout_exercise_memories WHERE id = ?",
                (int(memory_id),),
            ).fetchone()
            if selected_row is None or int(selected_row["user_id"]) != int(user_id):
                raise WorkoutExerciseMemoryNotFoundError(
                    "Exercise memory was not found for this user."
                )
            _validate_selected_memory_identity(
                selected_row,
                catalog_exercise_id=catalog_id,
                normalized_exercise_name=normalized_name,
            )

        target_row = selected_row or _select_save_target(
            cursor,
            user_id=user_id,
            catalog_exercise_id=catalog_id,
            normalized_exercise_name=normalized_name,
        )
        identity_key = (
            f"catalog:{catalog_id}"
            if catalog_id is not None
            else f"name:{normalized_name}"
        )

        if target_row is None:
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
                    int(user_id),
                    identity_key,
                    catalog_id,
                    cleaned_name,
                    normalized_name,
                    cleaned_memory_text,
                ),
            )
            saved_id = int(cursor.lastrowid)
        else:
            saved_id = int(target_row["id"])
            target_catalog_id = _nullable_int(target_row["catalog_exercise_id"])
            next_catalog_id = target_catalog_id
            next_identity_key = str(target_row["identity_key"])
            if catalog_id is not None:
                if target_catalog_id is None:
                    if not _name_only_promotion_is_safe(
                        cursor,
                        user_id=user_id,
                        catalog_exercise_id=catalog_id,
                        normalized_exercise_name=normalized_name,
                        excluded_memory_id=saved_id,
                    ):
                        raise WorkoutExerciseMemoryConflictError(
                            "That name-only memory cannot be promoted because the "
                            "exercise name is ambiguous."
                        )
                    next_catalog_id = catalog_id
                    next_identity_key = identity_key
                elif target_catalog_id != catalog_id:
                    raise WorkoutExerciseMemoryConflictError(
                        "The selected memory belongs to a different catalog exercise."
                    )

            cursor.execute(
                """
                UPDATE workout_exercise_memories
                SET identity_key = ?,
                    catalog_exercise_id = ?,
                    exercise_name = ?,
                    normalized_exercise_name = ?,
                    memory_text = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    next_identity_key,
                    next_catalog_id,
                    cleaned_name,
                    normalized_name,
                    cleaned_memory_text,
                    saved_id,
                    int(user_id),
                ),
            )

        conn.commit()
        saved_row = cursor.execute(
            "SELECT * FROM workout_exercise_memories WHERE id = ? AND user_id = ?",
            (saved_id, int(user_id)),
        ).fetchone()
        if saved_row is None:
            raise WorkoutExerciseMemoryNotFoundError(
                "Exercise memory could not be loaded after saving."
            )
        return _memory_from_row(saved_row)
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise WorkoutExerciseMemoryConflictError(
            "An exercise memory already exists for that identity."
        ) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_workout_exercise_memory(user_id: int, memory_id: int) -> None:
    if int(memory_id) <= 0:
        raise WorkoutExerciseMemoryValidationError(
            "memory_id must be a positive integer."
        )

    ensure_workout_exercise_memory_table()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _validate_user(cursor, user_id)
        cursor.execute(
            "DELETE FROM workout_exercise_memories WHERE id = ? AND user_id = ?",
            (int(memory_id), int(user_id)),
        )
        if cursor.rowcount != 1:
            raise WorkoutExerciseMemoryNotFoundError(
                "Exercise memory was not found for this user."
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _validate_exercise_identity(
    catalog_exercise_id: Any,
    exercise_name: Any,
) -> tuple[int | None, str, str]:
    cleaned_name = str(exercise_name or "").strip()
    normalized_name = normalize_workout_exercise_memory_name(cleaned_name)
    if not normalized_name:
        raise WorkoutExerciseMemoryValidationError("Exercise name is required.")
    if len(cleaned_name) > MAX_WORKOUT_EXERCISE_NAME_CHARACTERS:
        raise WorkoutExerciseMemoryValidationError(
            "Exercise name must be "
            f"{MAX_WORKOUT_EXERCISE_NAME_CHARACTERS} characters or fewer."
        )

    catalog_id = None
    if catalog_exercise_id is not None:
        try:
            catalog_id = int(catalog_exercise_id)
        except (TypeError, ValueError) as exc:
            raise WorkoutExerciseMemoryValidationError(
                "catalog_exercise_id must be a positive integer."
            ) from exc
        if catalog_id <= 0:
            raise WorkoutExerciseMemoryValidationError(
                "catalog_exercise_id must be a positive integer."
            )
    return catalog_id, cleaned_name, normalized_name


def _validate_user(cursor: Any, user_id: int) -> None:
    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise WorkoutExerciseMemoryValidationError(
            "user_id must be a positive integer."
        ) from exc
    if parsed_user_id <= 0:
        raise WorkoutExerciseMemoryValidationError(
            "user_id must be a positive integer."
        )
    if (
        cursor.execute("SELECT 1 FROM users WHERE id = ?", (parsed_user_id,)).fetchone()
        is None
    ):
        raise WorkoutExerciseMemoryNotFoundError("User was not found.")


def _resolve_memory(
    cursor: Any,
    *,
    user_id: int,
    catalog_exercise_id: int | None,
    normalized_exercise_name: str,
) -> WorkoutExerciseMemory | None:
    if catalog_exercise_id is not None:
        row = cursor.execute(
            """
            SELECT *
            FROM workout_exercise_memories
            WHERE user_id = ? AND identity_key = ?
            """,
            (int(user_id), f"catalog:{catalog_exercise_id}"),
        ).fetchone()
        if row is not None:
            return _memory_from_row(row)
        row = cursor.execute(
            """
            SELECT *
            FROM workout_exercise_memories
            WHERE user_id = ? AND identity_key = ?
            """,
            (int(user_id), f"name:{normalized_exercise_name}"),
        ).fetchone()
        if row is not None and _name_only_promotion_is_safe(
            cursor,
            user_id=user_id,
            catalog_exercise_id=catalog_exercise_id,
            normalized_exercise_name=normalized_exercise_name,
            excluded_memory_id=int(row["id"]),
        ):
            return _memory_from_row(row)
        return None

    name_row = cursor.execute(
        """
        SELECT *
        FROM workout_exercise_memories
        WHERE user_id = ? AND identity_key = ?
        """,
        (int(user_id), f"name:{normalized_exercise_name}"),
    ).fetchone()
    if name_row is not None:
        return _memory_from_row(name_row)

    catalog_rows = cursor.execute(
        """
        SELECT *
        FROM workout_exercise_memories
        WHERE user_id = ?
          AND normalized_exercise_name = ?
          AND catalog_exercise_id IS NOT NULL
        ORDER BY id ASC
        """,
        (int(user_id), normalized_exercise_name),
    ).fetchall()
    if len(catalog_rows) == 1:
        return _memory_from_row(catalog_rows[0])
    return None


def _select_save_target(
    cursor: Any,
    *,
    user_id: int,
    catalog_exercise_id: int | None,
    normalized_exercise_name: str,
) -> Any | None:
    if catalog_exercise_id is not None:
        exact_catalog = cursor.execute(
            """
            SELECT * FROM workout_exercise_memories
            WHERE user_id = ? AND identity_key = ?
            """,
            (int(user_id), f"catalog:{catalog_exercise_id}"),
        ).fetchone()
        if exact_catalog is not None:
            return exact_catalog
        name_row = cursor.execute(
            """
            SELECT * FROM workout_exercise_memories
            WHERE user_id = ? AND identity_key = ?
            """,
            (int(user_id), f"name:{normalized_exercise_name}"),
        ).fetchone()
        if name_row is not None and _name_only_promotion_is_safe(
            cursor,
            user_id=user_id,
            catalog_exercise_id=catalog_exercise_id,
            normalized_exercise_name=normalized_exercise_name,
            excluded_memory_id=int(name_row["id"]),
        ):
            return name_row
        return None

    exact_name = cursor.execute(
        """
        SELECT * FROM workout_exercise_memories
        WHERE user_id = ? AND identity_key = ?
        """,
        (int(user_id), f"name:{normalized_exercise_name}"),
    ).fetchone()
    if exact_name is not None:
        return exact_name
    catalog_rows = cursor.execute(
        """
        SELECT * FROM workout_exercise_memories
        WHERE user_id = ?
          AND normalized_exercise_name = ?
          AND catalog_exercise_id IS NOT NULL
        ORDER BY id ASC
        """,
        (int(user_id), normalized_exercise_name),
    ).fetchall()
    return catalog_rows[0] if len(catalog_rows) == 1 else None


def _validate_selected_memory_identity(
    row: Any,
    *,
    catalog_exercise_id: int | None,
    normalized_exercise_name: str,
) -> None:
    stored_catalog_id = _nullable_int(row["catalog_exercise_id"])
    if stored_catalog_id is not None and catalog_exercise_id is not None:
        if stored_catalog_id != catalog_exercise_id:
            raise WorkoutExerciseMemoryConflictError(
                "The selected memory belongs to a different catalog exercise."
            )
        return

    if str(row["normalized_exercise_name"]) != normalized_exercise_name:
        raise WorkoutExerciseMemoryConflictError(
            "The selected memory belongs to a different exercise name."
        )


def _name_only_promotion_is_safe(
    cursor: Any,
    *,
    user_id: int,
    catalog_exercise_id: int,
    normalized_exercise_name: str,
    excluded_memory_id: int,
) -> bool:
    rows = cursor.execute(
        """
        SELECT catalog_exercise_id
        FROM workout_exercise_memories
        WHERE user_id = ?
          AND normalized_exercise_name = ?
          AND id != ?
          AND catalog_exercise_id IS NOT NULL
        """,
        (int(user_id), normalized_exercise_name, int(excluded_memory_id)),
    ).fetchall()
    return all(int(row["catalog_exercise_id"]) == catalog_exercise_id for row in rows)


def _memory_from_row(row: Any) -> WorkoutExerciseMemory:
    return WorkoutExerciseMemory(
        memory_id=int(row["id"]),
        catalog_exercise_id=_nullable_int(row["catalog_exercise_id"]),
        exercise_name=str(row["exercise_name"]),
        memory_text=str(row["memory_text"]),
        created_at=_nullable_str(row["created_at"]),
        updated_at=_nullable_str(row["updated_at"]),
    )


def _nullable_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _nullable_str(value: Any) -> str | None:
    return None if value is None else str(value)
