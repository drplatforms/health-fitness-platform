from __future__ import annotations

from typing import Any, Literal

from database import get_connection
from services.food_normalization_service import (
    curate_canonical_display_name,
    ensure_food_normalization_tables,
    get_canonical_food,
    get_nutrients_for_canonical_food,
)
from services.personal_food_service import (
    PersonalFoodNotFoundError,
    get_personal_food,
)
from services.user_canonical_food_name_service import get_user_canonical_food_name

PINNED_FOODS_TABLE_NAME = "user_pinned_foods"
PinnedFoodType = Literal["canonical", "personal"]

_NUTRIENT_SUMMARY_KEYS = {
    "calories": "calories_per_100g",
    "calorie": "calories_per_100g",
    "energy": "calories_per_100g",
    "protein": "protein_g_per_100g",
    "carbohydrate": "carbohydrate_g_per_100g",
    "carbohydrates": "carbohydrate_g_per_100g",
    "carbs": "carbohydrate_g_per_100g",
    "total carbohydrate": "carbohydrate_g_per_100g",
    "fat": "fat_g_per_100g",
    "total fat": "fat_g_per_100g",
}


class PinnedFoodError(ValueError):
    pass


class PinnedFoodNotFoundError(PinnedFoodError):
    pass


def ensure_pinned_food_schema() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PINNED_FOODS_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_type TEXT NOT NULL CHECK (food_type IN ('canonical', 'personal')),
            food_id INTEGER NOT NULL CHECK (food_id > 0),
            pinned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, food_type, food_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_user_pinned_foods_user_order
        ON {PINNED_FOODS_TABLE_NAME}(user_id, id)
        """
    )
    conn.commit()
    conn.close()


def list_pinned_foods(*, user_id: int) -> list[dict[str, Any]]:
    ensure_food_normalization_tables()
    ensure_pinned_food_schema()
    _assert_user_exists(user_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT food_type, food_id, pinned_at
        FROM {PINNED_FOODS_TABLE_NAME}
        WHERE user_id = ?
        ORDER BY id
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    results: list[dict[str, Any]] = []
    for row in rows:
        item = _public_pinned_food(
            user_id=user_id,
            food_type=row["food_type"],
            food_id=int(row["food_id"]),
            pinned_at=str(row["pinned_at"]),
        )
        if item is not None:
            results.append(item)
    return results


def pin_food(
    *,
    user_id: int,
    food_type: str,
    food_id: int,
) -> dict[str, Any]:
    ensure_food_normalization_tables()
    ensure_pinned_food_schema()
    resolved_type, resolved_id = _validated_identity(food_type, food_id)
    _assert_user_exists(user_id)
    _assert_food_is_available(
        user_id=user_id,
        food_type=resolved_type,
        food_id=resolved_id,
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT OR IGNORE INTO {PINNED_FOODS_TABLE_NAME} (
            user_id, food_type, food_id
        ) VALUES (?, ?, ?)
        """,
        (user_id, resolved_type, resolved_id),
    )
    cursor.execute(
        f"""
        SELECT pinned_at
        FROM {PINNED_FOODS_TABLE_NAME}
        WHERE user_id = ? AND food_type = ? AND food_id = ?
        """,
        (user_id, resolved_type, resolved_id),
    )
    pinned_at = str(cursor.fetchone()["pinned_at"])
    conn.commit()
    conn.close()

    item = _public_pinned_food(
        user_id=user_id,
        food_type=resolved_type,
        food_id=resolved_id,
        pinned_at=pinned_at,
    )
    if item is None:
        raise PinnedFoodNotFoundError("Food not found.")
    return item


def unpin_food(*, user_id: int, food_type: str, food_id: int) -> bool:
    ensure_pinned_food_schema()
    resolved_type, resolved_id = _validated_identity(food_type, food_id)
    _assert_user_exists(user_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        DELETE FROM {PINNED_FOODS_TABLE_NAME}
        WHERE user_id = ? AND food_type = ? AND food_id = ?
        """,
        (user_id, resolved_type, resolved_id),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def _public_pinned_food(
    *,
    user_id: int,
    food_type: PinnedFoodType,
    food_id: int,
    pinned_at: str,
) -> dict[str, Any] | None:
    if food_type == "canonical":
        food = get_canonical_food(food_id)
        if food is None or not food.active:
            return None
        nutrient_summary: dict[str, float] = {}
        for nutrient in get_nutrients_for_canonical_food(food.id):
            normalized_name = " ".join(
                nutrient.nutrient_name.strip().lower().replace("_", " ").split()
            )
            summary_key = _NUTRIENT_SUMMARY_KEYS.get(normalized_name)
            if summary_key is not None:
                nutrient_summary[summary_key] = float(nutrient.amount_per_100g)
        custom_display_name = get_user_canonical_food_name(
            user_id=user_id, canonical_food_id=food.id
        )
        original_display_name = curate_canonical_display_name(
            food.display_name, food.food_type
        )
        return {
            "food_type": "canonical",
            "food_id": food.id,
            "canonical_food_id": food.id,
            "display_name": custom_display_name or original_display_name,
            "original_display_name": original_display_name,
            "custom_display_name": custom_display_name,
            "default_grams": food.default_grams,
            "pinned_at": pinned_at,
            **({"nutrient_summary": nutrient_summary} if nutrient_summary else {}),
        }

    try:
        food = get_personal_food(user_id=user_id, personal_food_id=food_id)
    except PersonalFoodNotFoundError:
        return None
    if not food.active:
        return None
    revision = food.current_revision
    nutrient_summary = {
        key: value
        for key, value in {
            "calories_per_100g": revision.calories_per_100g,
            "protein_g_per_100g": revision.protein_g_per_100g,
            "carbohydrate_g_per_100g": revision.carbs_g_per_100g,
            "fat_g_per_100g": revision.fat_g_per_100g,
        }.items()
        if value is not None
    }
    return {
        "food_type": "personal",
        "food_id": food.id,
        "personal_food_id": food.id,
        "display_name": food.display_name,
        "default_grams": revision.serving_grams,
        "serving_name": revision.serving_name,
        "serving_grams": revision.serving_grams,
        "pinned_at": pinned_at,
        **({"nutrient_summary": nutrient_summary} if nutrient_summary else {}),
    }


def _assert_food_is_available(
    *,
    user_id: int,
    food_type: PinnedFoodType,
    food_id: int,
) -> None:
    if food_type == "canonical":
        food = get_canonical_food(food_id)
        if food is None or not food.active:
            raise PinnedFoodNotFoundError("Canonical food not found.")
        return

    try:
        food = get_personal_food(user_id=user_id, personal_food_id=food_id)
    except PersonalFoodNotFoundError as exc:
        raise PinnedFoodNotFoundError("Personal food not found.") from exc
    if not food.active:
        raise PinnedFoodNotFoundError("Personal food not found.")


def _assert_user_exists(user_id: int) -> None:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise PinnedFoodNotFoundError("User not found.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    if not exists:
        raise PinnedFoodNotFoundError("User not found.")


def _validated_identity(food_type: str, food_id: int) -> tuple[PinnedFoodType, int]:
    if food_type not in {"canonical", "personal"}:
        raise PinnedFoodError("food_type must be canonical or personal.")
    if isinstance(food_id, bool) or not isinstance(food_id, int) or food_id <= 0:
        raise PinnedFoodError("food_id must be a positive integer.")
    return food_type, food_id
