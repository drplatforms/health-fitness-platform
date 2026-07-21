from __future__ import annotations

from typing import Any

from database import get_connection
from services.food_normalization_service import (
    curate_canonical_display_name,
    ensure_food_normalization_tables,
    get_canonical_food,
)

AVAILABLE_INGREDIENTS_TABLE_NAME = "user_available_ingredients"


class AvailableIngredientError(ValueError):
    pass


class AvailableIngredientNotFoundError(AvailableIngredientError):
    pass


def ensure_available_ingredient_schema() -> None:
    ensure_food_normalization_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {AVAILABLE_INGREDIENTS_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            canonical_food_id INTEGER NOT NULL,
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, canonical_food_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id)
        )
        """
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_user_available_ingredients_user_food
        ON {AVAILABLE_INGREDIENTS_TABLE_NAME}(user_id, canonical_food_id)
        """
    )
    conn.commit()
    conn.close()


def list_available_ingredients(*, user_id: int) -> list[dict[str, Any]]:
    ensure_available_ingredient_schema()
    _assert_user_exists(user_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            available.canonical_food_id,
            available.added_at,
            food.display_name,
            food.food_type
        FROM {AVAILABLE_INGREDIENTS_TABLE_NAME} AS available
        JOIN canonical_foods AS food
          ON food.id = available.canonical_food_id
        WHERE available.user_id = ?
          AND food.active = 1
        ORDER BY food.display_name COLLATE NOCASE, food.id
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_public_available_ingredient(row) for row in rows]


def add_available_ingredient(
    *,
    user_id: int,
    canonical_food_id: int,
) -> dict[str, Any]:
    ensure_available_ingredient_schema()
    _assert_user_exists(user_id)
    food_id = _validated_canonical_food_id(canonical_food_id)
    food = get_canonical_food(food_id)
    if food is None or not food.active:
        raise AvailableIngredientNotFoundError("Canonical food not found.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT OR IGNORE INTO {AVAILABLE_INGREDIENTS_TABLE_NAME} (
            user_id, canonical_food_id
        ) VALUES (?, ?)
        """,
        (user_id, food_id),
    )
    cursor.execute(
        f"""
        SELECT added_at
        FROM {AVAILABLE_INGREDIENTS_TABLE_NAME}
        WHERE user_id = ? AND canonical_food_id = ?
        """,
        (user_id, food_id),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return {
        "canonical_food_id": food.id,
        "display_name": curate_canonical_display_name(
            food.display_name,
            food.food_type,
        ),
        "food_type": food.food_type,
        "added_at": str(row["added_at"]),
    }


def remove_available_ingredient(
    *,
    user_id: int,
    canonical_food_id: int,
) -> bool:
    ensure_available_ingredient_schema()
    _assert_user_exists(user_id)
    food_id = _validated_canonical_food_id(canonical_food_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        DELETE FROM {AVAILABLE_INGREDIENTS_TABLE_NAME}
        WHERE user_id = ? AND canonical_food_id = ?
        """,
        (user_id, food_id),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def _public_available_ingredient(row: Any) -> dict[str, Any]:
    return {
        "canonical_food_id": int(row["canonical_food_id"]),
        "display_name": curate_canonical_display_name(
            str(row["display_name"]),
            str(row["food_type"]),
        ),
        "food_type": str(row["food_type"]),
        "added_at": str(row["added_at"]),
    }


def _assert_user_exists(user_id: int) -> None:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise AvailableIngredientNotFoundError("User not found.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    if not exists:
        raise AvailableIngredientNotFoundError("User not found.")


def _validated_canonical_food_id(canonical_food_id: int) -> int:
    if (
        isinstance(canonical_food_id, bool)
        or not isinstance(canonical_food_id, int)
        or canonical_food_id <= 0
    ):
        raise AvailableIngredientError("canonical_food_id must be a positive integer.")
    return canonical_food_id
