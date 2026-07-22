from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from database import get_connection
from models.meal_idea_models import MealIdeaGenerationRequest, MealIdeasResult

MAX_MEAL_IDEA_GENERATION_SETS_PER_USER = 5


class MealIdeaHistoryError(ValueError):
    """Base class for public-safe meal-idea history failures."""


class MealIdeaHistoryValidationError(MealIdeaHistoryError):
    """Raised when a history operation receives invalid input."""


class MealIdeaHistoryUserNotFoundError(MealIdeaHistoryError):
    """Raised when history is requested for an unknown user."""


class MealIdeaHistoryPersistenceError(MealIdeaHistoryError):
    """Raised when a stored history snapshot cannot be read safely."""


@dataclass(frozen=True)
class MealIdeaGenerationSet:
    id: int
    user_id: int
    created_at: str
    request: dict[str, Any]
    result: dict[str, Any]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "request": dict(self.request),
            "result": dict(self.result),
        }


def persist_successful_generation(
    *,
    user_id: int,
    selected_model: str,
    request: MealIdeaGenerationRequest,
    result: MealIdeasResult,
) -> MealIdeaGenerationSet:
    """Persist one grounded successful generation and retain only the newest five."""

    user_id = _positive_user_id(user_id)
    model = _required_model(selected_model)
    if result.provider != request.provider:
        raise MealIdeaHistoryValidationError(
            "Generation request and result providers must match."
        )
    if not result.ideas or result.telemetry is None:
        raise MealIdeaHistoryValidationError(
            "Only successful grounded meal-idea generations can be persisted."
        )

    request_payload = {
        "provider": request.provider,
        "model": model,
        "creative_steering": request.creative_steering,
        "meal_type": request.meal_type,
        "intent": request.intent,
    }
    result_payload = result.to_public_dict()
    request_json = _encode_payload(request_payload)
    result_json = _encode_payload(result_payload)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        cursor.execute(
            """
            INSERT INTO meal_idea_generation_sets (
                user_id, request_json, result_json
            )
            VALUES (?, ?, ?)
            """,
            (user_id, request_json, result_json),
        )
        generation_set_id = int(cursor.lastrowid)
        cursor.execute(
            """
            DELETE FROM meal_idea_generation_sets
            WHERE user_id = ?
              AND id NOT IN (
                  SELECT id
                  FROM meal_idea_generation_sets
                  WHERE user_id = ?
                  ORDER BY id DESC
                  LIMIT ?
              )
            """,
            (
                user_id,
                user_id,
                MAX_MEAL_IDEA_GENERATION_SETS_PER_USER,
            ),
        )
        row = cursor.execute(
            "SELECT * FROM meal_idea_generation_sets WHERE id = ? AND user_id = ?",
            (generation_set_id, user_id),
        ).fetchone()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if row is None:  # pragma: no cover - guarded by the transaction above
        raise MealIdeaHistoryPersistenceError(
            "Meal-idea generation history could not be persisted."
        )
    return _generation_set_from_row(row)


def list_generation_sets(
    *, user_id: int, limit: int = MAX_MEAL_IDEA_GENERATION_SETS_PER_USER
) -> list[MealIdeaGenerationSet]:
    user_id = _positive_user_id(user_id)
    limit = _validated_limit(limit)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _assert_user_exists(cursor, user_id)
        rows = cursor.execute(
            """
            SELECT *
            FROM meal_idea_generation_sets
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [_generation_set_from_row(row) for row in rows]


def _generation_set_from_row(row: sqlite3.Row) -> MealIdeaGenerationSet:
    return MealIdeaGenerationSet(
        id=int(row["id"]),
        user_id=int(row["user_id"]),
        created_at=str(row["created_at"]),
        request=_decode_payload(row["request_json"]),
        result=_decode_payload(row["result_json"]),
    )


def _assert_user_exists(cursor: sqlite3.Cursor, user_id: int) -> None:
    row = cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise MealIdeaHistoryUserNotFoundError("User not found.")


def _encode_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _decode_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        raise MealIdeaHistoryPersistenceError(
            "Stored meal-idea generation history is invalid."
        )
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise MealIdeaHistoryPersistenceError(
            "Stored meal-idea generation history is invalid."
        ) from exc
    if not isinstance(payload, dict):
        raise MealIdeaHistoryPersistenceError(
            "Stored meal-idea generation history is invalid."
        )
    return payload


def _positive_user_id(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise MealIdeaHistoryValidationError("user_id must be a positive integer.")
    return value


def _required_model(value: Any) -> str:
    if not isinstance(value, str):
        raise MealIdeaHistoryValidationError("model must be text.")
    model = value.strip()
    if not model or len(model) > 200:
        raise MealIdeaHistoryValidationError(
            "model must be between 1 and 200 characters."
        )
    return model


def _validated_limit(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= MAX_MEAL_IDEA_GENERATION_SETS_PER_USER
    ):
        raise MealIdeaHistoryValidationError(
            f"limit must be between 1 and {MAX_MEAL_IDEA_GENERATION_SETS_PER_USER}."
        )
    return value
