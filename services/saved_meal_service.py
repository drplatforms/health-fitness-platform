from __future__ import annotations

import math
import sqlite3
from typing import Any

from database import get_connection
from models.saved_meal_models import (
    SavedMeal,
    SavedMealItem,
    SavedMealItemInput,
    SavedMealMutationInput,
)
from services.nutrition_service import MAX_CANONICAL_LOG_GRAMS, _normalize_meal_type
from services.personal_food_service import _assert_user_exists

ALLOWED_FOOD_TYPES = {"canonical", "personal"}
MAX_SAVED_MEALS_PER_USER = 500
MAX_SAVED_MEAL_ITEMS = 50


class SavedMealError(ValueError):
    """Base class for public-safe saved-meal failures."""


class SavedMealValidationError(SavedMealError):
    """Raised when a saved-meal definition is invalid."""


class SavedMealNotFoundError(SavedMealError):
    """Raised when a user-owned saved meal does not exist."""


class SavedMealDuplicateNameError(SavedMealError):
    """Raised when a user already owns the normalized meal name."""


class SavedMealArchivedError(SavedMealError):
    """Raised when an archived saved meal is used for logging."""


def normalize_saved_meal_name(value: str) -> str:
    display_name = _required_display_name(value)
    return display_name.casefold()


def create_saved_meal(*, user_id: int, mutation: SavedMealMutationInput) -> SavedMeal:
    display_name, normalized_name, meal_type, items = _normalize_mutation(mutation)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        cursor.execute(
            "SELECT COUNT(*) AS count FROM saved_meals WHERE user_id = ?",
            (user_id,),
        )
        if int(cursor.fetchone()["count"]) >= MAX_SAVED_MEALS_PER_USER:
            raise SavedMealValidationError("Saved meal limit reached.")
        cursor.execute(
            """
            INSERT INTO saved_meals (
                user_id, display_name, normalized_name, default_meal_type
            )
            VALUES (?, ?, ?, ?)
            """,
            (user_id, display_name, normalized_name, meal_type),
        )
        saved_meal_id = int(cursor.lastrowid)
        _replace_saved_meal_items(
            cursor,
            user_id=user_id,
            saved_meal_id=saved_meal_id,
            items=items,
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if "saved_meals.user_id, saved_meals.normalized_name" in str(exc):
            raise SavedMealDuplicateNameError(
                "A saved meal with this name already exists."
            ) from exc
        raise SavedMealValidationError("Saved meal could not be persisted.") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return get_saved_meal(user_id=user_id, saved_meal_id=saved_meal_id)


def update_saved_meal(
    *, user_id: int, saved_meal_id: int, mutation: SavedMealMutationInput
) -> SavedMeal:
    saved_meal_id = _positive_id(saved_meal_id, "saved_meal_id")
    display_name, normalized_name, meal_type, items = _normalize_mutation(mutation)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        _fetch_owned_meal_row(cursor, user_id=user_id, saved_meal_id=saved_meal_id)
        cursor.execute(
            """
            UPDATE saved_meals
            SET display_name = ?, normalized_name = ?, default_meal_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (display_name, normalized_name, meal_type, saved_meal_id, user_id),
        )
        _replace_saved_meal_items(
            cursor,
            user_id=user_id,
            saved_meal_id=saved_meal_id,
            items=items,
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if "saved_meals.user_id, saved_meals.normalized_name" in str(exc):
            raise SavedMealDuplicateNameError(
                "A saved meal with this name already exists."
            ) from exc
        raise SavedMealValidationError("Saved meal could not be persisted.") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return get_saved_meal(user_id=user_id, saved_meal_id=saved_meal_id)


def get_saved_meal(*, user_id: int, saved_meal_id: int) -> SavedMeal:
    saved_meal_id = _positive_id(saved_meal_id, "saved_meal_id")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _assert_user_exists(cursor, user_id)
        row = _fetch_owned_meal_row(
            cursor, user_id=user_id, saved_meal_id=saved_meal_id
        )
        return _build_saved_meal(cursor, row)
    finally:
        conn.close()


def list_saved_meals(
    *, user_id: int, include_archived: bool = False, limit: int = 100
) -> list[SavedMeal]:
    limit = _validated_limit(limit)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _assert_user_exists(cursor, user_id)
        active_clause = "" if include_archived else "AND active = 1"
        cursor.execute(
            f"""
            SELECT * FROM saved_meals
            WHERE user_id = ? {active_clause}
            ORDER BY active DESC, normalized_name, id
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [_build_saved_meal(cursor, row) for row in cursor.fetchall()]
    finally:
        conn.close()


def archive_saved_meal(*, user_id: int, saved_meal_id: int) -> SavedMeal:
    return _set_saved_meal_active(
        user_id=user_id, saved_meal_id=saved_meal_id, active=False
    )


def restore_saved_meal(*, user_id: int, saved_meal_id: int) -> SavedMeal:
    return _set_saved_meal_active(
        user_id=user_id, saved_meal_id=saved_meal_id, active=True
    )


def _set_saved_meal_active(
    *, user_id: int, saved_meal_id: int, active: bool
) -> SavedMeal:
    saved_meal_id = _positive_id(saved_meal_id, "saved_meal_id")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        _fetch_owned_meal_row(cursor, user_id=user_id, saved_meal_id=saved_meal_id)
        cursor.execute(
            """
            UPDATE saved_meals
            SET active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (1 if active else 0, saved_meal_id, user_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return get_saved_meal(user_id=user_id, saved_meal_id=saved_meal_id)


def _normalize_mutation(
    mutation: SavedMealMutationInput,
) -> tuple[str, str, str | None, tuple[SavedMealItemInput, ...]]:
    display_name = _required_display_name(mutation.display_name)
    normalized_name = display_name.casefold()
    try:
        meal_type = _normalize_meal_type(mutation.default_meal_type)
    except ValueError as exc:
        raise SavedMealValidationError(str(exc)) from exc
    items = tuple(mutation.items)
    if not items:
        raise SavedMealValidationError("A saved meal must contain at least one item.")
    if len(items) > MAX_SAVED_MEAL_ITEMS:
        raise SavedMealValidationError(
            f"A saved meal may contain at most {MAX_SAVED_MEAL_ITEMS} items."
        )
    return display_name, normalized_name, meal_type, items


def _replace_saved_meal_items(
    cursor: sqlite3.Cursor,
    *,
    user_id: int,
    saved_meal_id: int,
    items: tuple[SavedMealItemInput, ...],
) -> None:
    resolved_items = [
        _resolve_item_input(cursor, user_id=user_id, item=item) for item in items
    ]
    cursor.execute(
        "DELETE FROM saved_meal_items WHERE saved_meal_id = ?", (saved_meal_id,)
    )
    for item_order, item in enumerate(resolved_items):
        cursor.execute(
            """
            INSERT INTO saved_meal_items (
                saved_meal_id, item_order, food_type,
                canonical_food_id, personal_food_id, resolved_grams,
                canonical_serving_unit_id, serving_quantity,
                serving_display_snapshot, amount_source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                saved_meal_id,
                item_order,
                item["food_type"],
                item["canonical_food_id"],
                item["personal_food_id"],
                item["resolved_grams"],
                item["canonical_serving_unit_id"],
                item["serving_quantity"],
                item["serving_display_snapshot"],
                item["amount_source"],
            ),
        )


def _resolve_item_input(
    cursor: sqlite3.Cursor, *, user_id: int, item: SavedMealItemInput
) -> dict[str, Any]:
    food_type = str(item.food_type).strip().lower()
    if food_type not in ALLOWED_FOOD_TYPES:
        raise SavedMealValidationError("food_type must be canonical or personal.")
    canonical_food_id = (
        _positive_id(item.canonical_food_id, "canonical_food_id")
        if item.canonical_food_id is not None
        else None
    )
    personal_food_id = (
        _positive_id(item.personal_food_id, "personal_food_id")
        if item.personal_food_id is not None
        else None
    )
    if food_type == "canonical" and (
        canonical_food_id is None or personal_food_id is not None
    ):
        raise SavedMealValidationError(
            "Canonical items require canonical_food_id only."
        )
    if food_type == "personal" and (
        personal_food_id is None or canonical_food_id is not None
    ):
        raise SavedMealValidationError("Personal items require personal_food_id only.")

    amount_modes = sum(
        (
            item.grams is not None,
            item.serving_unit_id is not None or item.serving_quantity is not None,
            item.personal_serving_quantity is not None,
        )
    )
    if amount_modes != 1:
        raise SavedMealValidationError(
            "Provide exactly one item amount mode: grams, canonical serving, or personal serving."
        )

    if food_type == "canonical":
        cursor.execute(
            "SELECT display_name, active FROM canonical_foods WHERE id = ?",
            (canonical_food_id,),
        )
        food_row = cursor.fetchone()
        if food_row is None:
            raise SavedMealValidationError("Canonical food not found.")
        if not bool(food_row["active"]):
            raise SavedMealValidationError("Inactive canonical food cannot be added.")
    else:
        cursor.execute(
            """
            SELECT pf.active, pr.serving_name, pr.serving_grams
            FROM personal_foods AS pf
            JOIN personal_food_revisions AS pr ON pr.id = pf.current_revision_id
            WHERE pf.id = ? AND pf.user_id = ?
            """,
            (personal_food_id, user_id),
        )
        food_row = cursor.fetchone()
        if food_row is None:
            raise SavedMealValidationError("Personal food not found.")
        if not bool(food_row["active"]):
            raise SavedMealValidationError("Archived personal food cannot be added.")

    serving_unit_id: int | None = None
    serving_quantity: float | None = None
    serving_display: str | None = None
    if item.grams is not None:
        resolved_grams = _positive_amount(item.grams, "grams")
        amount_source = "grams"
    elif item.personal_serving_quantity is not None:
        if food_type != "personal":
            raise SavedMealValidationError(
                "personal_serving_quantity requires a personal food."
            )
        serving_quantity = _positive_amount(
            item.personal_serving_quantity,
            "personal_serving_quantity",
            maximum=1_000,
        )
        serving_grams = food_row["serving_grams"]
        if serving_grams is None:
            raise SavedMealValidationError(
                "This personal food has no default serving size."
            )
        resolved_grams = _positive_amount(
            float(serving_grams) * serving_quantity, "resolved_grams"
        )
        serving_name = str(food_row["serving_name"] or "serving")
        serving_display = f"{_compact_number(serving_quantity)} x {serving_name}"
        amount_source = "personal_serving"
    else:
        if food_type != "canonical":
            raise SavedMealValidationError(
                "Canonical serving units require a canonical food."
            )
        if item.serving_unit_id is None or item.serving_quantity is None:
            raise SavedMealValidationError(
                "serving_unit_id and serving_quantity are both required."
            )
        serving_unit_id = _positive_id(item.serving_unit_id, "serving_unit_id")
        serving_quantity = _positive_amount(
            item.serving_quantity, "serving_quantity", maximum=1_000
        )
        cursor.execute(
            """
            SELECT canonical_food_id, display_name, grams_default, active
            FROM canonical_food_serving_units
            WHERE id = ?
            """,
            (serving_unit_id,),
        )
        serving_row = cursor.fetchone()
        if serving_row is None:
            raise SavedMealValidationError("Serving unit not found.")
        if not bool(serving_row["active"]):
            raise SavedMealValidationError("Inactive serving unit cannot be used.")
        if int(serving_row["canonical_food_id"]) != canonical_food_id:
            raise SavedMealValidationError(
                "Serving unit does not belong to the canonical food."
            )
        resolved_grams = _positive_amount(
            float(serving_row["grams_default"]) * serving_quantity,
            "resolved_grams",
        )
        serving_display = (
            f"{_compact_number(serving_quantity)} x {serving_row['display_name']}"
        )
        amount_source = "canonical_serving"

    return {
        "food_type": food_type,
        "canonical_food_id": canonical_food_id,
        "personal_food_id": personal_food_id,
        "resolved_grams": round(resolved_grams, 4),
        "canonical_serving_unit_id": serving_unit_id,
        "serving_quantity": serving_quantity,
        "serving_display_snapshot": serving_display,
        "amount_source": amount_source,
    }


def _build_saved_meal(cursor: sqlite3.Cursor, meal_row: sqlite3.Row) -> SavedMeal:
    cursor.execute(
        """
        SELECT * FROM saved_meal_items
        WHERE saved_meal_id = ?
        ORDER BY item_order, id
        """,
        (meal_row["id"],),
    )
    items = tuple(
        _build_saved_meal_item(cursor, meal_row, item_row)
        for item_row in cursor.fetchall()
    )
    invalid_item_count = sum(item.validation_status != "valid" for item in items)
    validation_status = (
        "empty" if not items else "invalid" if invalid_item_count else "valid"
    )
    return SavedMeal(
        id=int(meal_row["id"]),
        user_id=int(meal_row["user_id"]),
        display_name=str(meal_row["display_name"]),
        default_meal_type=meal_row["default_meal_type"],
        active=bool(meal_row["active"]),
        created_at=str(meal_row["created_at"]),
        updated_at=str(meal_row["updated_at"]),
        items=items,
        calories=_complete_total(items, "calories"),
        protein_g=_complete_total(items, "protein_g"),
        carbs_g=_complete_total(items, "carbs_g"),
        fat_g=_complete_total(items, "fat_g"),
        validation_status=validation_status,
        invalid_item_count=invalid_item_count,
    )


def _build_saved_meal_item(
    cursor: sqlite3.Cursor, meal_row: sqlite3.Row, item_row: sqlite3.Row
) -> SavedMealItem:
    grams = float(item_row["resolved_grams"])
    validation_reason: str | None = None
    nutrient_values: dict[str, float | None]
    if item_row["food_type"] == "canonical":
        cursor.execute(
            "SELECT display_name, active FROM canonical_foods WHERE id = ?",
            (item_row["canonical_food_id"],),
        )
        food_row = cursor.fetchone()
        if food_row is None:
            display_name = "Unavailable canonical food"
            active = False
            validation_reason = "Canonical food no longer exists."
            nutrient_values = _empty_macros()
        else:
            display_name = str(food_row["display_name"])
            active = bool(food_row["active"])
            if not active:
                validation_reason = "Canonical food is inactive."
            cursor.execute(
                """
                SELECT nutrient_name, amount_per_100g
                FROM canonical_food_nutrients
                WHERE canonical_food_id = ?
                """,
                (item_row["canonical_food_id"],),
            )
            nutrient_values = _canonical_macros(cursor.fetchall(), grams)
            if not any(value is not None for value in nutrient_values.values()):
                validation_reason = validation_reason or (
                    "Canonical food has no usable nutrition."
                )
    else:
        cursor.execute(
            """
            SELECT pf.display_name, pf.active, pf.user_id,
                   pr.calories_per_100g, pr.protein_g_per_100g,
                   pr.carbs_g_per_100g, pr.fat_g_per_100g
            FROM personal_foods AS pf
            LEFT JOIN personal_food_revisions AS pr ON pr.id = pf.current_revision_id
            WHERE pf.id = ?
            """,
            (item_row["personal_food_id"],),
        )
        food_row = cursor.fetchone()
        if food_row is None or int(food_row["user_id"]) != int(meal_row["user_id"]):
            display_name = "Unavailable personal food"
            active = False
            validation_reason = "Personal food is unavailable."
            nutrient_values = _empty_macros()
        else:
            display_name = str(food_row["display_name"])
            active = bool(food_row["active"])
            if not active:
                validation_reason = "Personal food is archived."
            nutrient_values = {
                "calories": _scaled(food_row["calories_per_100g"], grams),
                "protein_g": _scaled(food_row["protein_g_per_100g"], grams),
                "carbs_g": _scaled(food_row["carbs_g_per_100g"], grams),
                "fat_g": _scaled(food_row["fat_g_per_100g"], grams),
            }

    return SavedMealItem(
        id=int(item_row["id"]),
        item_order=int(item_row["item_order"]),
        food_type=item_row["food_type"],
        canonical_food_id=item_row["canonical_food_id"],
        personal_food_id=item_row["personal_food_id"],
        display_name=display_name,
        active=active,
        resolved_grams=grams,
        canonical_serving_unit_id=item_row["canonical_serving_unit_id"],
        serving_quantity=_optional_float(item_row["serving_quantity"]),
        serving_display_snapshot=item_row["serving_display_snapshot"],
        amount_source=str(item_row["amount_source"]),
        validation_status="invalid" if validation_reason else "valid",
        validation_reason=validation_reason,
        calories=nutrient_values["calories"],
        protein_g=nutrient_values["protein_g"],
        carbs_g=nutrient_values["carbs_g"],
        fat_g=nutrient_values["fat_g"],
    )


def _canonical_macros(rows: list[sqlite3.Row], grams: float) -> dict[str, float | None]:
    aliases = {
        "calorie": "calories",
        "calories": "calories",
        "energy": "calories",
        "protein": "protein_g",
        "carbohydrate": "carbs_g",
        "carbohydrates": "carbs_g",
        "carbs": "carbs_g",
        "total carbohydrate": "carbs_g",
        "fat": "fat_g",
        "total fat": "fat_g",
    }
    result = _empty_macros()
    for row in rows:
        key = aliases.get(str(row["nutrient_name"]).strip().lower())
        if key is not None:
            result[key] = round(float(row["amount_per_100g"]) * grams / 100, 3)
    return result


def _complete_total(items: tuple[SavedMealItem, ...], field_name: str) -> float | None:
    values = [getattr(item, field_name) for item in items]
    if not values or any(value is None for value in values):
        return None
    return round(sum(float(value) for value in values), 3)


def _fetch_owned_meal_row(
    cursor: sqlite3.Cursor, *, user_id: int, saved_meal_id: int
) -> sqlite3.Row:
    cursor.execute(
        "SELECT * FROM saved_meals WHERE id = ? AND user_id = ?",
        (saved_meal_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        raise SavedMealNotFoundError("Saved meal not found.")
    return row


def _required_display_name(value: str) -> str:
    if not isinstance(value, str):
        raise SavedMealValidationError("display_name is required.")
    display_name = " ".join(value.strip().split())
    if not display_name:
        raise SavedMealValidationError("display_name is required.")
    if len(display_name) > 120:
        raise SavedMealValidationError("display_name must be 120 characters or fewer.")
    return display_name


def _positive_id(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SavedMealValidationError(f"{field_name} must be a positive integer.")
    return value


def _positive_amount(
    value: Any, field_name: str, *, maximum: float = MAX_CANONICAL_LOG_GRAMS
) -> float:
    if isinstance(value, bool):
        raise SavedMealValidationError(f"{field_name} must be a positive number.")
    try:
        amount = float(value)
    except (TypeError, ValueError) as exc:
        raise SavedMealValidationError(
            f"{field_name} must be a positive number."
        ) from exc
    if not math.isfinite(amount) or amount <= 0:
        raise SavedMealValidationError(f"{field_name} must be greater than 0.")
    if amount > maximum:
        raise SavedMealValidationError(
            f"{field_name} must be less than or equal to {maximum:g}."
        )
    return amount


def _validated_limit(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 500:
        raise SavedMealValidationError("limit must be between 1 and 500.")
    return value


def _scaled(value: Any, grams: float) -> float | None:
    return None if value is None else round(float(value) * grams / 100, 3)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _empty_macros() -> dict[str, float | None]:
    return {"calories": None, "protein_g": None, "carbs_g": None, "fat_g": None}


def _compact_number(value: float) -> str:
    return f"{value:g}"
