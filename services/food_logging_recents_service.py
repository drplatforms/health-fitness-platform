from __future__ import annotations

from typing import Any

from database import get_connection
from services.nutrition_serving_unit_logging_service import (
    SERVING_UNIT_LOG_METADATA_TABLE_NAME,
    ensure_serving_unit_log_metadata_schema,
)
from services.pinned_food_service import (
    PINNED_FOODS_TABLE_NAME,
    ensure_pinned_food_schema,
)
from services.user_canonical_food_name_service import (
    USER_CANONICAL_FOOD_NAMES_TABLE_NAME,
    ensure_user_canonical_food_name_schema,
)

DEFAULT_RECENT_CANONICAL_FOODS_LIMIT = 10
MAX_RECENT_CANONICAL_FOODS_LIMIT = 25


def _bounded_limit(limit: int = DEFAULT_RECENT_CANONICAL_FOODS_LIMIT) -> int:
    try:
        resolved_limit = int(limit)
    except (TypeError, ValueError):
        return DEFAULT_RECENT_CANONICAL_FOODS_LIMIT

    if resolved_limit < 1:
        return DEFAULT_RECENT_CANONICAL_FOODS_LIMIT
    return min(resolved_limit, MAX_RECENT_CANONICAL_FOODS_LIMIT)


def _macro_summary_from_row(row: Any) -> dict[str, float]:
    summary: dict[str, float] = {}
    if row["calories"] is not None:
        summary["calories"] = float(row["calories"])
    if row["protein_g"] is not None:
        summary["protein_g"] = float(row["protein_g"])
    if row["carbs_g"] is not None:
        summary["carbohydrate_g"] = float(row["carbs_g"])
    if row["fat_g"] is not None:
        summary["fat_g"] = float(row["fat_g"])
    return summary


def _recent_food_from_row(row: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "canonical_food_id": int(row["canonical_food_id"]),
        "display_name": row["display_name"],
        "original_display_name": row["original_display_name"],
        "custom_display_name": row["custom_display_name"],
        "last_logged_at": row["last_logged_at"],
        "last_logged_date": row["last_logged_date"],
        "last_meal_type": row["last_meal_type"],
        "last_grams": float(row["last_grams"]),
        "usage_count": int(row["usage_count"]),
    }

    if row["last_serving_unit_id"] is not None:
        item["last_serving_unit_id"] = int(row["last_serving_unit_id"])
        item["last_serving_unit_label"] = row["last_serving_unit_label"]
        item["last_quantity"] = float(row["last_quantity"])

    nutrient_summary = _macro_summary_from_row(row)
    if nutrient_summary:
        item["nutrient_summary"] = nutrient_summary

    return item


def get_recent_canonical_foods(
    user_id: int,
    limit: int = DEFAULT_RECENT_CANONICAL_FOODS_LIMIT,
) -> list[dict[str, Any]]:
    """Return distinct recent canonical foods for a user.

    Recents are derived from canonical food log entries, not stored as a new
    user preference surface. Serving-unit fields are included only when the
    most recent log entry has approved serving-unit provenance metadata.
    """

    ensure_serving_unit_log_metadata_schema()
    ensure_pinned_food_schema()
    ensure_user_canonical_food_name_schema()
    resolved_limit = _bounded_limit(limit)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        WITH ranked_entries AS (
            SELECT
                food_entries.id AS entry_id,
                food_entries.canonical_food_id,
                COALESCE(user_names.display_name, canonical_foods.display_name)
                    AS display_name,
                canonical_foods.display_name AS original_display_name,
                user_names.display_name AS custom_display_name,
                food_entries.created_at AS last_logged_at,
                food_entries.entry_date AS last_logged_date,
                food_entries.meal_type AS last_meal_type,
                food_entries.grams AS last_grams,
                food_entries.calories,
                food_entries.protein_g,
                food_entries.carbs_g,
                food_entries.fat_g,
                serving_metadata.serving_unit_id AS last_serving_unit_id,
                serving_metadata.original_serving_display
                    AS last_serving_unit_label,
                serving_metadata.serving_quantity AS last_quantity,
                COUNT(*) OVER (
                    PARTITION BY food_entries.canonical_food_id
                ) AS usage_count,
                ROW_NUMBER() OVER (
                    PARTITION BY food_entries.canonical_food_id
                    ORDER BY food_entries.created_at DESC, food_entries.id DESC
                ) AS row_rank
            FROM food_entries
            JOIN canonical_foods
                ON canonical_foods.id = food_entries.canonical_food_id
            LEFT JOIN {SERVING_UNIT_LOG_METADATA_TABLE_NAME} AS serving_metadata
                ON serving_metadata.food_entry_id = food_entries.id
            LEFT JOIN {USER_CANONICAL_FOOD_NAMES_TABLE_NAME} AS user_names
                ON user_names.user_id = food_entries.user_id
               AND user_names.canonical_food_id = food_entries.canonical_food_id
            WHERE food_entries.user_id = ?
              AND food_entries.canonical_food_id IS NOT NULL
              AND canonical_foods.active = 1
              AND NOT EXISTS (
                  SELECT 1
                  FROM {PINNED_FOODS_TABLE_NAME} AS pinned_foods
                  WHERE pinned_foods.user_id = food_entries.user_id
                    AND pinned_foods.food_type = 'canonical'
                    AND pinned_foods.food_id = food_entries.canonical_food_id
              )
        )
        SELECT *
        FROM ranked_entries
        WHERE row_rank = 1
        ORDER BY last_logged_at DESC, entry_id DESC
        LIMIT ?
        """,
        (int(user_id), resolved_limit),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_recent_food_from_row(row) for row in rows]
