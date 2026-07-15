from __future__ import annotations

import math
from datetime import date
from typing import Any

from database import get_connection
from models.personal_food_models import PersonalFoodLogResult
from services.nutrition_service import MAX_CANONICAL_LOG_GRAMS
from services.personal_food_service import (
    PersonalFoodArchivedError,
    PersonalFoodNotFoundError,
    PersonalFoodValidationError,
    _assert_user_exists,
    _validate_personal_food_id,
)

MAX_PERSONAL_FOOD_LOG_GRAMS = MAX_CANONICAL_LOG_GRAMS
MAX_PERSONAL_FOOD_SERVING_QUANTITY = 1_000.0


class PersonalFoodLogEntryNotFoundError(PersonalFoodNotFoundError):
    """Raised when a user-owned personal-food log entry does not exist."""


def log_personal_food(
    *,
    user_id: int,
    personal_food_id: int,
    grams: float | None = None,
    serving_quantity: float | None = None,
    entry_date: str | None = None,
    meal_type: str | None = None,
    notes: str | None = None,
) -> PersonalFoodLogResult:
    personal_food_id = _validate_personal_food_id(personal_food_id)
    has_grams = grams is not None
    has_serving_quantity = serving_quantity is not None
    if has_grams == has_serving_quantity:
        raise PersonalFoodValidationError(
            "Provide exactly one of grams or serving_quantity."
        )
    resolved_date = _resolve_entry_date(entry_date)
    resolved_meal_type = _optional_text(meal_type, "meal_type")
    resolved_notes = _optional_text(notes, "notes")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        cursor.execute(
            """
            SELECT
                personal_foods.id AS personal_food_id,
                personal_foods.display_name,
                personal_foods.active,
                personal_food_revisions.*
            FROM personal_foods
            JOIN personal_food_revisions
                ON personal_food_revisions.id = personal_foods.current_revision_id
            WHERE personal_foods.id = ?
              AND personal_foods.user_id = ?
            """,
            (personal_food_id, user_id),
        )
        revision = cursor.fetchone()
        if revision is None:
            raise PersonalFoodNotFoundError("Personal food not found.")
        if not bool(revision["active"]):
            raise PersonalFoodArchivedError("Archived personal food cannot be logged.")

        resolved_serving_quantity: float | None = None
        if has_grams:
            resolved_grams = _positive_amount(
                grams,
                "grams",
                maximum=MAX_PERSONAL_FOOD_LOG_GRAMS,
            )
        else:
            resolved_serving_quantity = _positive_amount(
                serving_quantity,
                "serving_quantity",
                maximum=MAX_PERSONAL_FOOD_SERVING_QUANTITY,
            )
            serving_grams = revision["serving_grams"]
            if serving_grams is None:
                raise PersonalFoodValidationError(
                    "This personal food has no default serving size."
                )
            resolved_grams = _positive_amount(
                float(serving_grams) * resolved_serving_quantity,
                "resolved_grams",
                maximum=MAX_PERSONAL_FOOD_LOG_GRAMS,
            )

        nutrient_summary = _nutrient_summary(revision, resolved_grams)
        cursor.execute(
            """
            INSERT INTO food_entries (
                user_id,
                food_id,
                canonical_food_id,
                personal_food_id,
                personal_food_revision_id,
                food_name_snapshot,
                grams,
                meal_type,
                notes,
                calories,
                protein_g,
                carbs_g,
                fat_g,
                entry_date
            )
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                int(revision["legacy_food_id"]),
                personal_food_id,
                int(revision["id"]),
                str(revision["display_name_snapshot"]),
                resolved_grams,
                resolved_meal_type,
                resolved_notes,
                nutrient_summary.get("calories"),
                nutrient_summary.get("protein_g"),
                nutrient_summary.get("carbs_g"),
                nutrient_summary.get("fat_g"),
                resolved_date,
            ),
        )
        entry_id = int(cursor.lastrowid)
        conn.commit()
        return PersonalFoodLogResult(
            logged_food_entry_id=entry_id,
            personal_food_id=personal_food_id,
            personal_food_revision_id=int(revision["id"]),
            display_name=str(revision["display_name_snapshot"]),
            grams=resolved_grams,
            serving_quantity=resolved_serving_quantity,
            logged_date=resolved_date,
            meal_type=resolved_meal_type,
            nutrient_summary=nutrient_summary,
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_daily_personal_food_logs(
    *,
    user_id: int,
    entry_date: str,
) -> list[dict[str, Any]]:
    resolved_date = _resolve_entry_date(entry_date)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _assert_user_exists(cursor, user_id)
        cursor.execute(
            """
            SELECT
                food_entries.id AS entry_id,
                food_entries.personal_food_id,
                food_entries.personal_food_revision_id,
                food_entries.food_name_snapshot AS food_name,
                food_entries.grams,
                food_entries.meal_type,
                food_entries.calories,
                food_entries.protein_g,
                food_entries.carbs_g,
                food_entries.fat_g,
                personal_food_revisions.serving_name,
                personal_food_revisions.serving_grams
            FROM food_entries
            JOIN personal_food_revisions
                ON personal_food_revisions.id =
                    food_entries.personal_food_revision_id
            WHERE food_entries.user_id = ?
              AND food_entries.entry_date = ?
              AND food_entries.canonical_food_id IS NULL
              AND food_entries.personal_food_id IS NOT NULL
              AND food_entries.personal_food_revision_id IS NOT NULL
            ORDER BY food_entries.created_at, food_entries.id
            """,
            (user_id, resolved_date),
        )
        return [_personal_food_log_entry_response(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_personal_food_entry(
    *,
    user_id: int,
    entry_id: int,
    grams: float | None = None,
    serving_quantity: float | None = None,
    meal_type: str | None = None,
    entry_date: str | None = None,
) -> dict[str, Any]:
    entry_id = _validate_entry_id(entry_id)
    has_grams = grams is not None
    has_serving_quantity = serving_quantity is not None
    if has_grams and has_serving_quantity:
        raise PersonalFoodValidationError(
            "Provide either grams or serving_quantity, not both."
        )
    if not has_grams and not has_serving_quantity and meal_type is None:
        raise PersonalFoodValidationError(
            "grams, serving_quantity, or meal_type is required."
        )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        existing_entry = _fetch_owned_personal_food_entry(
            cursor,
            user_id=user_id,
            entry_id=entry_id,
            entry_date=entry_date,
        )
        resolved_meal_type = (
            _normalize_meal_type(meal_type)
            if meal_type is not None
            else existing_entry["meal_type"]
        )
        if has_grams:
            resolved_grams = _positive_amount(
                grams,
                "grams",
                maximum=MAX_PERSONAL_FOOD_LOG_GRAMS,
            )
        elif has_serving_quantity:
            resolved_quantity = _positive_amount(
                serving_quantity,
                "serving_quantity",
                maximum=MAX_PERSONAL_FOOD_SERVING_QUANTITY,
            )
            serving_grams = existing_entry["serving_grams"]
            if serving_grams is None:
                raise PersonalFoodValidationError(
                    "This logged revision has no saved serving size."
                )
            resolved_grams = _positive_amount(
                float(serving_grams) * resolved_quantity,
                "resolved_grams",
                maximum=MAX_PERSONAL_FOOD_LOG_GRAMS,
            )
        else:
            resolved_grams = float(existing_entry["grams"])

        nutrient_summary = _nutrient_summary(existing_entry, resolved_grams)
        cursor.execute(
            """
            UPDATE food_entries
            SET
                grams = ?,
                meal_type = ?,
                calories = ?,
                protein_g = ?,
                carbs_g = ?,
                fat_g = ?
            WHERE id = ?
              AND user_id = ?
              AND canonical_food_id IS NULL
              AND personal_food_id IS NOT NULL
              AND personal_food_revision_id IS NOT NULL
            """,
            (
                resolved_grams,
                resolved_meal_type,
                nutrient_summary.get("calories"),
                nutrient_summary.get("protein_g"),
                nutrient_summary.get("carbs_g"),
                nutrient_summary.get("fat_g"),
                entry_id,
                user_id,
            ),
        )
        updated_entry = _fetch_owned_personal_food_entry(
            cursor,
            user_id=user_id,
            entry_id=entry_id,
            entry_date=entry_date,
        )
        conn.commit()
        return _personal_food_log_entry_response(updated_entry)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_personal_food_entry(
    *,
    user_id: int,
    entry_id: int,
    entry_date: str | None = None,
) -> dict[str, Any]:
    entry_id = _validate_entry_id(entry_id)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        _fetch_owned_personal_food_entry(
            cursor,
            user_id=user_id,
            entry_id=entry_id,
            entry_date=entry_date,
        )
        cursor.execute(
            """
            DELETE FROM food_entries
            WHERE id = ?
              AND user_id = ?
              AND canonical_food_id IS NULL
              AND personal_food_id IS NOT NULL
              AND personal_food_revision_id IS NOT NULL
            """,
            (entry_id, user_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"deleted": True, "entry_id": entry_id}


def _fetch_owned_personal_food_entry(
    cursor,
    *,
    user_id: int,
    entry_id: int,
    entry_date: str | None = None,
):
    params: list[Any] = [entry_id, user_id]
    date_clause = ""
    if entry_date is not None:
        date_clause = "AND food_entries.entry_date = ?"
        params.append(_resolve_entry_date(entry_date))

    cursor.execute(
        f"""
        SELECT
            food_entries.id AS entry_id,
            food_entries.personal_food_id,
            food_entries.personal_food_revision_id,
            food_entries.food_name_snapshot AS food_name,
            food_entries.grams,
            food_entries.meal_type,
            food_entries.calories,
            food_entries.protein_g,
            food_entries.carbs_g,
            food_entries.fat_g,
            personal_food_revisions.serving_name,
            personal_food_revisions.serving_grams,
            personal_food_revisions.calories_per_100g,
            personal_food_revisions.protein_g_per_100g,
            personal_food_revisions.carbs_g_per_100g,
            personal_food_revisions.fat_g_per_100g
        FROM food_entries
        JOIN personal_food_revisions
            ON personal_food_revisions.id = food_entries.personal_food_revision_id
        WHERE food_entries.id = ?
          AND food_entries.user_id = ?
          AND food_entries.canonical_food_id IS NULL
          AND food_entries.personal_food_id IS NOT NULL
          AND food_entries.personal_food_revision_id IS NOT NULL
          {date_clause}
        """,
        tuple(params),
    )
    row = cursor.fetchone()
    if row is None:
        raise PersonalFoodLogEntryNotFoundError("Personal food log entry not found.")
    return row


def _personal_food_log_entry_response(row) -> dict[str, Any]:
    return {
        "entry_id": int(row["entry_id"]),
        "food_type": "personal",
        "personal_food_id": int(row["personal_food_id"]),
        "personal_food_revision_id": int(row["personal_food_revision_id"]),
        "food_name": str(row["food_name"]),
        "grams": float(row["grams"]),
        "meal_type": row["meal_type"],
        "calories": _optional_float(row["calories"]),
        "protein_g": _optional_float(row["protein_g"]),
        "carbs_g": _optional_float(row["carbs_g"]),
        "fat_g": _optional_float(row["fat_g"]),
        "serving_name": row["serving_name"],
        "serving_grams": _optional_float(row["serving_grams"]),
    }


def _nutrient_summary(revision: Any, grams: float) -> dict[str, float]:
    summary: dict[str, float] = {}
    for response_key, column_name in (
        ("calories", "calories_per_100g"),
        ("protein_g", "protein_g_per_100g"),
        ("carbs_g", "carbs_g_per_100g"),
        ("fat_g", "fat_g_per_100g"),
    ):
        amount_per_100g = revision[column_name]
        if amount_per_100g is not None:
            snapshot = float(amount_per_100g) * grams / 100.0
            if not math.isfinite(snapshot) or snapshot < 0:
                raise PersonalFoodValidationError(
                    f"{response_key} could not be logged as a finite non-negative value."
                )
            summary[response_key] = round(snapshot, 3)
    return summary


def _positive_amount(value: Any, field_name: str, *, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise PersonalFoodValidationError(f"{field_name} must be a number.")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise PersonalFoodValidationError(
            f"{field_name} must be a finite number greater than zero."
        )
    if number > maximum:
        raise PersonalFoodValidationError(f"{field_name} is too large.")
    return number


def _validate_entry_id(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PersonalFoodValidationError("entry_id must be a positive integer.")
    return value


def _resolve_entry_date(value: str | None) -> str:
    if value is None:
        return date.today().isoformat()
    if not isinstance(value, str):
        raise PersonalFoodValidationError("entry_date must use YYYY-MM-DD format.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise PersonalFoodValidationError(
            "entry_date must use YYYY-MM-DD format."
        ) from exc


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PersonalFoodValidationError(f"{field_name} must be text.")
    normalized = " ".join(value.strip().split())
    if not normalized:
        return None
    if len(normalized) > 1_000:
        raise PersonalFoodValidationError(f"{field_name} is too long.")
    return normalized


def _normalize_meal_type(value: Any) -> str | None:
    normalized = _optional_text(value, "meal_type")
    if normalized is None:
        return None
    normalized = normalized.lower().replace(" ", "_")
    if normalized not in {"breakfast", "lunch", "dinner", "snack", "other"}:
        raise PersonalFoodValidationError(
            "meal_type must be breakfast, lunch, dinner, snack, or other."
        )
    return normalized


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
