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
