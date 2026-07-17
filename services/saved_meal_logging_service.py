from __future__ import annotations

import math
import sqlite3
from typing import Any

from database import get_connection
from models.food_normalization_models import CanonicalFoodNutrient
from services.nutrition_service import (
    _get_or_create_legacy_food_id_with_cursor,
    _normalize_meal_type,
    _nutrient_summary_for_logged_grams,
    _resolve_entry_date,
    _sync_legacy_food_nutrients_with_cursor,
)
from services.nutrition_serving_unit_logging_service import (
    SERVING_UNIT_AMOUNT_SOURCE,
    SERVING_UNIT_LOG_METADATA_TABLE_NAME,
    ensure_serving_unit_log_metadata_schema,
)
from services.personal_food_logging_service import _nutrient_summary
from services.personal_food_service import _assert_user_exists
from services.saved_meal_service import (
    SavedMealArchivedError,
    SavedMealValidationError,
    _fetch_owned_meal_row,
    _positive_id,
)


def log_saved_meal(
    *,
    user_id: int,
    saved_meal_id: int,
    entry_date: str | None,
    meal_type: str | None = None,
) -> dict[str, Any]:
    saved_meal_id = _positive_id(saved_meal_id, "saved_meal_id")
    try:
        resolved_date = _resolve_entry_date(entry_date)
    except ValueError as exc:
        raise SavedMealValidationError(str(exc)) from exc

    ensure_serving_unit_log_metadata_schema()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        meal_row = _fetch_owned_meal_row(
            cursor,
            user_id=user_id,
            saved_meal_id=saved_meal_id,
        )
        if not bool(meal_row["active"]):
            raise SavedMealArchivedError("Archived saved meals cannot be logged.")
        try:
            resolved_meal_type = _normalize_meal_type(
                meal_type if meal_type is not None else meal_row["default_meal_type"]
            )
        except ValueError as exc:
            raise SavedMealValidationError(str(exc)) from exc
        if resolved_meal_type is None:
            raise SavedMealValidationError(
                "meal_type is required when the saved meal has no default."
            )

        cursor.execute(
            """
            SELECT * FROM saved_meal_items
            WHERE saved_meal_id = ?
            ORDER BY item_order, id
            """,
            (saved_meal_id,),
        )
        item_rows = cursor.fetchall()
        if not item_rows:
            raise SavedMealValidationError(
                "A saved meal must contain at least one item."
            )

        prepared_items = [
            _prepare_item(cursor, user_id=user_id, item_row=row) for row in item_rows
        ]
        logged_entries = [
            _insert_prepared_entry(
                cursor,
                user_id=user_id,
                prepared=item,
                entry_date=resolved_date,
                meal_type=resolved_meal_type,
                meal_name=str(meal_row["display_name"]),
            )
            for item in prepared_items
        ]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "saved_meal_id": int(saved_meal_id),
        "meal_name": str(meal_row["display_name"]),
        "entry_date": resolved_date,
        "meal_type": resolved_meal_type,
        "logged_item_count": len(logged_entries),
        "logged_entries": logged_entries,
        "aggregate_logged_macros": {
            key: _complete_macro_total(logged_entries, key)
            for key in ("calories", "protein_g", "carbs_g", "fat_g")
        },
    }


def _prepare_item(
    cursor: sqlite3.Cursor, *, user_id: int, item_row: sqlite3.Row
) -> dict[str, Any]:
    grams = float(item_row["resolved_grams"])
    if not math.isfinite(grams) or not 0 < grams <= 5_000:
        raise SavedMealValidationError(
            f"Meal item {int(item_row['item_order']) + 1} has invalid saved grams."
        )

    if item_row["food_type"] == "canonical":
        return _prepare_canonical_item(cursor, item_row=item_row, grams=grams)
    return _prepare_personal_item(
        cursor,
        user_id=user_id,
        item_row=item_row,
        grams=grams,
    )


def _prepare_canonical_item(
    cursor: sqlite3.Cursor, *, item_row: sqlite3.Row, grams: float
) -> dict[str, Any]:
    canonical_food_id = int(item_row["canonical_food_id"])
    cursor.execute(
        "SELECT display_name, active FROM canonical_foods WHERE id = ?",
        (canonical_food_id,),
    )
    food_row = cursor.fetchone()
    if food_row is None:
        raise SavedMealValidationError("A canonical meal item no longer exists.")
    if not bool(food_row["active"]):
        raise SavedMealValidationError(
            f"{food_row['display_name']} is inactive and cannot be logged."
        )
    cursor.execute(
        """
        SELECT * FROM canonical_food_nutrients
        WHERE canonical_food_id = ?
        ORDER BY id
        """,
        (canonical_food_id,),
    )
    nutrient_rows = cursor.fetchall()
    if not nutrient_rows:
        raise SavedMealValidationError(
            f"{food_row['display_name']} has no usable nutrition for logging."
        )
    nutrients = [
        CanonicalFoodNutrient(
            id=int(row["id"]),
            canonical_food_id=canonical_food_id,
            nutrient_name=str(row["nutrient_name"]),
            nutrient_unit=str(row["nutrient_unit"]),
            amount_per_100g=float(row["amount_per_100g"]),
            source_policy=str(row["source_policy"]),
            confidence=str(row["confidence"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in nutrient_rows
    ]
    serving_metadata = _current_serving_metadata(
        cursor,
        item_row=item_row,
        canonical_food_id=canonical_food_id,
        grams=grams,
    )
    nutrient_summary = _nutrient_summary_for_logged_grams(
        nutrients,
        grams,
        precision=1 if serving_metadata else 3,
    )
    return {
        "food_type": "canonical",
        "canonical_food_id": canonical_food_id,
        "personal_food_id": None,
        "personal_food_revision_id": None,
        "legacy_food_id": None,
        "display_name": str(food_row["display_name"]),
        "grams": grams,
        "nutrients": nutrients,
        "nutrient_summary": {
            "calories": nutrient_summary.get("calories"),
            "protein_g": nutrient_summary.get("protein_g"),
            "carbs_g": nutrient_summary.get("carbohydrate_g"),
            "fat_g": nutrient_summary.get("fat_g"),
        },
        "serving_metadata": serving_metadata,
    }


def _prepare_personal_item(
    cursor: sqlite3.Cursor,
    *,
    user_id: int,
    item_row: sqlite3.Row,
    grams: float,
) -> dict[str, Any]:
    personal_food_id = int(item_row["personal_food_id"])
    cursor.execute(
        """
        SELECT pf.active, pr.*
        FROM personal_foods AS pf
        JOIN personal_food_revisions AS pr ON pr.id = pf.current_revision_id
        WHERE pf.id = ? AND pf.user_id = ?
        """,
        (personal_food_id, user_id),
    )
    revision = cursor.fetchone()
    if revision is None:
        raise SavedMealValidationError("A personal meal item is unavailable.")
    if not bool(revision["active"]):
        raise SavedMealValidationError(
            f"{revision['display_name_snapshot']} is archived and cannot be logged."
        )
    try:
        nutrient_summary = _nutrient_summary(revision, grams)
    except ValueError as exc:
        raise SavedMealValidationError(str(exc)) from exc
    return {
        "food_type": "personal",
        "canonical_food_id": None,
        "personal_food_id": personal_food_id,
        "personal_food_revision_id": int(revision["id"]),
        "legacy_food_id": int(revision["legacy_food_id"]),
        "display_name": str(revision["display_name_snapshot"]),
        "grams": grams,
        "nutrients": None,
        "nutrient_summary": {
            "calories": nutrient_summary.get("calories"),
            "protein_g": nutrient_summary.get("protein_g"),
            "carbs_g": nutrient_summary.get("carbs_g"),
            "fat_g": nutrient_summary.get("fat_g"),
        },
        "serving_metadata": None,
    }


def _current_serving_metadata(
    cursor: sqlite3.Cursor,
    *,
    item_row: sqlite3.Row,
    canonical_food_id: int,
    grams: float,
) -> dict[str, Any] | None:
    serving_unit_id = item_row["canonical_serving_unit_id"]
    serving_quantity = item_row["serving_quantity"]
    if serving_unit_id is None or serving_quantity is None:
        return None
    cursor.execute(
        """
        SELECT * FROM canonical_food_serving_units
        WHERE id = ? AND canonical_food_id = ? AND active = 1
        """,
        (serving_unit_id, canonical_food_id),
    )
    serving_row = cursor.fetchone()
    if serving_row is None:
        return None
    quantity = float(serving_quantity)
    current_grams = round(float(serving_row["grams_default"]) * quantity, 4)
    if not math.isclose(current_grams, grams, rel_tol=0, abs_tol=0.0001):
        return None
    return {
        "serving_unit_id": int(serving_unit_id),
        "serving_quantity": quantity,
        "resolved_grams": grams,
        "grams_min": _scaled_optional(serving_row["grams_min"], quantity),
        "grams_max": _scaled_optional(serving_row["grams_max"], quantity),
        "serving_unit_confidence": str(serving_row["confidence"]),
        "amount_source": SERVING_UNIT_AMOUNT_SOURCE,
        "original_serving_display": (
            item_row["serving_display_snapshot"]
            or f"{quantity:g} x {serving_row['display_name']}"
        ),
        "source": serving_row["source"],
        "source_notes": serving_row["source_note"],
    }


def _insert_prepared_entry(
    cursor: sqlite3.Cursor,
    *,
    user_id: int,
    prepared: dict[str, Any],
    entry_date: str,
    meal_type: str,
    meal_name: str,
) -> dict[str, Any]:
    if prepared["food_type"] == "canonical":
        legacy_food_id = _get_or_create_legacy_food_id_with_cursor(
            cursor, f"Canonical: {prepared['display_name']}"
        )
        _sync_legacy_food_nutrients_with_cursor(
            cursor,
            legacy_food_id,
            prepared["nutrients"],
        )
    else:
        legacy_food_id = int(prepared["legacy_food_id"])

    macros = prepared["nutrient_summary"]
    cursor.execute(
        """
        INSERT INTO food_entries (
            user_id, food_id, canonical_food_id, personal_food_id,
            personal_food_revision_id, food_name_snapshot, grams,
            meal_type, notes, calories, protein_g, carbs_g, fat_g, entry_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            legacy_food_id,
            prepared["canonical_food_id"],
            prepared["personal_food_id"],
            prepared["personal_food_revision_id"],
            prepared["display_name"] if prepared["food_type"] == "personal" else None,
            prepared["grams"],
            meal_type,
            f"Logged from saved meal: {meal_name}",
            macros["calories"],
            macros["protein_g"],
            macros["carbs_g"],
            macros["fat_g"],
            entry_date,
        ),
    )
    entry_id = int(cursor.lastrowid)
    metadata = prepared["serving_metadata"]
    if metadata is not None:
        cursor.execute(
            f"""
            INSERT INTO {SERVING_UNIT_LOG_METADATA_TABLE_NAME} (
                food_entry_id, user_id, canonical_food_id, serving_unit_id,
                serving_quantity, resolved_grams, grams_min, grams_max,
                serving_unit_confidence, amount_source, original_serving_display,
                source, source_notes, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                entry_id,
                user_id,
                prepared["canonical_food_id"],
                metadata["serving_unit_id"],
                metadata["serving_quantity"],
                metadata["resolved_grams"],
                metadata["grams_min"],
                metadata["grams_max"],
                metadata["serving_unit_confidence"],
                metadata["amount_source"],
                metadata["original_serving_display"],
                metadata["source"],
                metadata["source_notes"],
            ),
        )
    return {
        "entry_id": entry_id,
        "food_type": prepared["food_type"],
        "canonical_food_id": prepared["canonical_food_id"],
        "personal_food_id": prepared["personal_food_id"],
        "personal_food_revision_id": prepared["personal_food_revision_id"],
        "display_name": prepared["display_name"],
        "grams": prepared["grams"],
        **macros,
    }


def _complete_macro_total(entries: list[dict[str, Any]], key: str) -> float | None:
    values = [entry[key] for entry in entries]
    if any(value is None for value in values):
        return None
    return round(sum(float(value) for value in values), 3)


def _scaled_optional(value: Any, quantity: float) -> float | None:
    return None if value is None else round(float(value) * quantity, 4)
