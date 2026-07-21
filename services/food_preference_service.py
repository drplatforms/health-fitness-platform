from __future__ import annotations

from typing import Any

from database import get_connection
from services.food_normalization_service import (
    curate_canonical_display_name,
    ensure_food_normalization_tables,
    get_canonical_food,
)
from services.user_canonical_food_name_service import (
    USER_CANONICAL_FOOD_NAMES_TABLE_NAME,
    ensure_user_canonical_food_name_schema,
)

FOOD_PREFERENCES_TABLE_NAME = "user_canonical_food_preferences"
FOOD_PREFERENCE_STATES = ("love", "like", "dislike", "never_suggest")


class FoodPreferenceError(ValueError):
    pass


class FoodPreferenceNotFoundError(FoodPreferenceError):
    pass


def ensure_food_preference_schema() -> None:
    ensure_food_normalization_tables()
    conn = get_connection()
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {FOOD_PREFERENCES_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            canonical_food_id INTEGER NOT NULL,
            preference TEXT NOT NULL CHECK (
                preference IN ('love', 'like', 'dislike', 'never_suggest')
            ),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, canonical_food_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id)
        )
        """
    )
    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_food_preferences_user_preference
        ON {FOOD_PREFERENCES_TABLE_NAME}(user_id, preference, canonical_food_id)
        """
    )
    conn.commit()
    conn.close()


def list_food_preferences(*, user_id: int) -> list[dict[str, Any]]:
    ensure_food_preference_schema()
    ensure_user_canonical_food_name_schema()
    _assert_user_exists(user_id)
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT preferences.canonical_food_id,
               preferences.preference,
               preferences.updated_at,
               foods.display_name AS original_display_name,
               names.display_name AS custom_display_name,
               foods.food_type,
               foods.default_unit,
               foods.default_grams,
               foods.search_priority
        FROM {FOOD_PREFERENCES_TABLE_NAME} AS preferences
        JOIN canonical_foods AS foods
          ON foods.id = preferences.canonical_food_id
        LEFT JOIN {USER_CANONICAL_FOOD_NAMES_TABLE_NAME} AS names
          ON names.user_id = preferences.user_id
         AND names.canonical_food_id = preferences.canonical_food_id
        WHERE preferences.user_id = ? AND foods.active = 1
        ORDER BY COALESCE(names.display_name, foods.display_name) COLLATE NOCASE,
                 foods.id
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [_public_preference(row) for row in rows]


def set_food_preference(
    *, user_id: int, canonical_food_id: int, preference: str
) -> dict[str, Any]:
    ensure_food_preference_schema()
    _assert_user_exists(user_id)
    food = _active_canonical_food(canonical_food_id)
    resolved_preference = _validated_preference(preference)
    if resolved_preference == "neutral":
        remove_food_preference(user_id=user_id, canonical_food_id=canonical_food_id)
        return _neutral_preference(food.id)

    conn = get_connection()
    conn.execute(
        f"""
        INSERT INTO {FOOD_PREFERENCES_TABLE_NAME} (
            user_id, canonical_food_id, preference
        ) VALUES (?, ?, ?)
        ON CONFLICT(user_id, canonical_food_id) DO UPDATE SET
            preference = excluded.preference,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, food.id, resolved_preference),
    )
    conn.commit()
    conn.close()
    return _preference_state(food.id, resolved_preference)


def remove_food_preference(*, user_id: int, canonical_food_id: int) -> bool:
    ensure_food_preference_schema()
    _assert_user_exists(user_id)
    _active_canonical_food(canonical_food_id)
    conn = get_connection()
    cursor = conn.execute(
        f"""
        DELETE FROM {FOOD_PREFERENCES_TABLE_NAME}
        WHERE user_id = ? AND canonical_food_id = ?
        """,
        (user_id, canonical_food_id),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def _public_preference(row: Any) -> dict[str, Any]:
    original_name = curate_canonical_display_name(
        str(row["original_display_name"]), str(row["food_type"])
    )
    custom_name = row["custom_display_name"]
    state = _preference_state(int(row["canonical_food_id"]), str(row["preference"]))
    return {
        **state,
        "display_name": str(custom_name) if custom_name is not None else original_name,
        "original_display_name": original_name,
        "custom_display_name": custom_name,
        "food_type": str(row["food_type"]),
        "default_unit": row["default_unit"],
        "default_grams": row["default_grams"],
        "search_priority": int(row["search_priority"]),
        "updated_at": str(row["updated_at"]),
    }


def _preference_state(canonical_food_id: int, preference: str) -> dict[str, Any]:
    return {
        "canonical_food_id": canonical_food_id,
        "preference": preference,
        "is_hard_exclusion": preference == "never_suggest",
    }


def _neutral_preference(canonical_food_id: int) -> dict[str, Any]:
    return _preference_state(canonical_food_id, "neutral")


def _validated_preference(preference: str) -> str:
    if not isinstance(preference, str):
        raise FoodPreferenceError("preference must be text.")
    resolved = preference.strip().lower()
    if resolved not in (*FOOD_PREFERENCE_STATES, "neutral"):
        raise FoodPreferenceError(
            "preference must be one of: love, like, neutral, dislike, never_suggest."
        )
    return resolved


def _assert_user_exists(user_id: int) -> None:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise FoodPreferenceNotFoundError("User not found.")
    conn = get_connection()
    exists = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if exists is None:
        raise FoodPreferenceNotFoundError("User not found.")


def _active_canonical_food(canonical_food_id: int):
    if (
        isinstance(canonical_food_id, bool)
        or not isinstance(canonical_food_id, int)
        or canonical_food_id <= 0
    ):
        raise FoodPreferenceError("canonical_food_id must be a positive integer.")
    food = get_canonical_food(canonical_food_id)
    if food is None or not food.active:
        raise FoodPreferenceNotFoundError("Canonical food not found.")
    return food
