from __future__ import annotations

import math
import sqlite3
from collections.abc import Mapping
from typing import Any

from database import get_connection
from models.personal_food_models import (
    PersonalFood,
    PersonalFoodRevision,
    PersonalFoodRevisionInput,
)

_INPUT_BASES = {"nutrition_label", "per_100g"}
_NUTRIENT_NAMES = {
    "calories": "Calories",
    "protein_g": "Protein",
    "carbs_g": "Carbohydrates",
    "fat_g": "Fat",
}


class PersonalFoodError(ValueError):
    pass


class PersonalFoodValidationError(PersonalFoodError):
    pass


class PersonalFoodUserNotFoundError(PersonalFoodError):
    pass


class PersonalFoodNotFoundError(PersonalFoodError):
    pass


class PersonalFoodDuplicateNameError(PersonalFoodError):
    pass


class PersonalFoodArchivedError(PersonalFoodError):
    pass


def normalize_personal_food_name(value: str) -> str:
    if not isinstance(value, str):
        raise PersonalFoodValidationError("display_name must be text.")
    normalized = " ".join(value.strip().casefold().split())
    if not normalized:
        raise PersonalFoodValidationError("display_name is required.")
    return normalized


def create_personal_food(
    *,
    user_id: int,
    revision_input: PersonalFoodRevisionInput,
) -> PersonalFood:
    display_name = _required_display_name(revision_input.display_name)
    normalized_name = normalize_personal_food_name(display_name)
    brand_name = _optional_text(revision_input.brand_name)
    normalized_nutrients = _normalize_revision_input(revision_input)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        cursor.execute(
            """
            INSERT INTO personal_foods (
                user_id,
                display_name,
                normalized_name,
                brand_name,
                active
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            (user_id, display_name, normalized_name, brand_name),
        )
        personal_food_id = int(cursor.lastrowid)
        revision_id = _insert_personal_food_revision(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
            revision_number=1,
            display_name=display_name,
            brand_name=brand_name,
            revision_input=revision_input,
            normalized_nutrients=normalized_nutrients,
        )
        cursor.execute(
            """
            UPDATE personal_foods
            SET current_revision_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (revision_id, personal_food_id),
        )
        personal_food = _fetch_personal_food(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
        conn.commit()
        return personal_food
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if "personal_foods.user_id, personal_foods.normalized_name" in str(exc):
            raise PersonalFoodDuplicateNameError(
                "A personal food with this name already exists."
            ) from exc
        raise PersonalFoodValidationError("Personal food could not be saved.") from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_personal_food(*, user_id: int, personal_food_id: int) -> PersonalFood:
    personal_food_id = _validate_personal_food_id(personal_food_id)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _assert_user_exists(cursor, user_id)
        return _fetch_personal_food(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
    finally:
        conn.close()


def list_personal_foods(
    *,
    user_id: int,
    include_archived: bool = False,
    limit: int = 50,
) -> list[PersonalFood]:
    resolved_limit = _validate_limit(limit)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _assert_user_exists(cursor, user_id)
        active_clause = "" if include_archived else "AND active = 1"
        cursor.execute(
            f"""
            SELECT id
            FROM personal_foods
            WHERE user_id = ?
              {active_clause}
            ORDER BY normalized_name, id
            LIMIT ?
            """,
            (user_id, resolved_limit),
        )
        return [
            _fetch_personal_food(
                cursor,
                user_id=user_id,
                personal_food_id=int(row["id"]),
            )
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()


def search_personal_foods(
    *,
    user_id: int,
    query: str,
    include_archived: bool = False,
    limit: int = 20,
) -> list[PersonalFood]:
    normalized_query = normalize_personal_food_name(query)
    resolved_limit = _validate_limit(limit)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _assert_user_exists(cursor, user_id)
        active_clause = "" if include_archived else "AND active = 1"
        cursor.execute(
            f"""
            SELECT id
            FROM personal_foods
            WHERE user_id = ?
              AND normalized_name LIKE ?
              {active_clause}
            ORDER BY
                CASE WHEN normalized_name = ? THEN 0 ELSE 1 END,
                normalized_name,
                id
            LIMIT ?
            """,
            (user_id, f"%{normalized_query}%", normalized_query, resolved_limit),
        )
        return [
            _fetch_personal_food(
                cursor,
                user_id=user_id,
                personal_food_id=int(row["id"]),
            )
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()


def revise_personal_food(
    *,
    user_id: int,
    personal_food_id: int,
    revision_input: PersonalFoodRevisionInput,
) -> PersonalFood:
    personal_food_id = _validate_personal_food_id(personal_food_id)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        identity = _fetch_owned_identity_row(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
        display_name = (
            _required_display_name(revision_input.display_name)
            if revision_input.display_name is not None
            else str(identity["display_name"])
        )
        brand_name = (
            _optional_text(revision_input.brand_name)
            if revision_input.brand_name is not None
            else identity["brand_name"]
        )
        normalized_name = normalize_personal_food_name(display_name)
        normalized_nutrients = _normalize_revision_input(revision_input)
        cursor.execute(
            """
            SELECT COALESCE(MAX(revision_number), 0) + 1 AS next_revision_number
            FROM personal_food_revisions
            WHERE personal_food_id = ?
            """,
            (personal_food_id,),
        )
        revision_number = int(cursor.fetchone()["next_revision_number"])
        revision_id = _insert_personal_food_revision(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
            revision_number=revision_number,
            display_name=display_name,
            brand_name=brand_name,
            revision_input=revision_input,
            normalized_nutrients=normalized_nutrients,
        )
        cursor.execute(
            """
            UPDATE personal_foods
            SET
                display_name = ?,
                normalized_name = ?,
                brand_name = ?,
                current_revision_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (
                display_name,
                normalized_name,
                brand_name,
                revision_id,
                personal_food_id,
                user_id,
            ),
        )
        personal_food = _fetch_personal_food(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
        conn.commit()
        return personal_food
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if "personal_foods.user_id, personal_foods.normalized_name" in str(exc):
            raise PersonalFoodDuplicateNameError(
                "A personal food with this name already exists."
            ) from exc
        raise PersonalFoodValidationError(
            "Personal food revision could not be saved."
        ) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def archive_personal_food(*, user_id: int, personal_food_id: int) -> PersonalFood:
    return _set_personal_food_active(
        user_id=user_id,
        personal_food_id=personal_food_id,
        active=False,
    )


def restore_personal_food(*, user_id: int, personal_food_id: int) -> PersonalFood:
    return _set_personal_food_active(
        user_id=user_id,
        personal_food_id=personal_food_id,
        active=True,
    )


def _set_personal_food_active(
    *,
    user_id: int,
    personal_food_id: int,
    active: bool,
) -> PersonalFood:
    personal_food_id = _validate_personal_food_id(personal_food_id)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        _assert_user_exists(cursor, user_id)
        _fetch_owned_identity_row(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
        cursor.execute(
            """
            UPDATE personal_foods
            SET active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (int(active), personal_food_id, user_id),
        )
        personal_food = _fetch_personal_food(
            cursor,
            user_id=user_id,
            personal_food_id=personal_food_id,
        )
        conn.commit()
        return personal_food
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _insert_personal_food_revision(
    cursor: sqlite3.Cursor,
    *,
    user_id: int,
    personal_food_id: int,
    revision_number: int,
    display_name: str,
    brand_name: str | None,
    revision_input: PersonalFoodRevisionInput,
    normalized_nutrients: Mapping[str, float | None],
) -> int:
    legacy_name = (
        f"Internal Personal Food:{user_id}:{personal_food_id}:r{revision_number}"
    )
    cursor.execute("INSERT INTO foods (name) VALUES (?)", (legacy_name,))
    legacy_food_id = int(cursor.lastrowid)
    _insert_legacy_nutrients(
        cursor,
        legacy_food_id=legacy_food_id,
        normalized_nutrients=normalized_nutrients,
    )
    cursor.execute(
        """
        INSERT INTO personal_food_revisions (
            personal_food_id,
            revision_number,
            display_name_snapshot,
            brand_name_snapshot,
            input_basis,
            serving_name,
            serving_grams,
            calories_per_100g,
            protein_g_per_100g,
            carbs_g_per_100g,
            fat_g_per_100g,
            entered_calories,
            entered_protein_g,
            entered_carbs_g,
            entered_fat_g,
            source_note,
            legacy_food_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            personal_food_id,
            revision_number,
            display_name,
            brand_name,
            revision_input.input_basis,
            _optional_text(revision_input.serving_name),
            _optional_positive_number(revision_input.serving_grams, "serving_grams"),
            normalized_nutrients["calories"],
            normalized_nutrients["protein_g"],
            normalized_nutrients["carbs_g"],
            normalized_nutrients["fat_g"],
            _optional_nutrient(revision_input.calories, "calories"),
            _optional_nutrient(revision_input.protein_g, "protein_g"),
            _optional_nutrient(revision_input.carbs_g, "carbs_g"),
            _optional_nutrient(revision_input.fat_g, "fat_g"),
            _optional_text(revision_input.source_note),
            legacy_food_id,
        ),
    )
    return int(cursor.lastrowid)


def _insert_legacy_nutrients(
    cursor: sqlite3.Cursor,
    *,
    legacy_food_id: int,
    normalized_nutrients: Mapping[str, float | None],
) -> None:
    for field_name, nutrient_name in _NUTRIENT_NAMES.items():
        amount = normalized_nutrients[field_name]
        if amount is None:
            continue
        cursor.execute("SELECT id FROM nutrients WHERE name = ?", (nutrient_name,))
        row = cursor.fetchone()
        if row is None:
            raise PersonalFoodValidationError(
                "Required nutrient reference data is unavailable."
            )
        cursor.execute(
            """
            INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
            VALUES (?, ?, ?)
            """,
            (legacy_food_id, int(row["id"]), amount),
        )


def _normalize_revision_input(
    revision_input: PersonalFoodRevisionInput,
) -> dict[str, float | None]:
    if revision_input.input_basis not in _INPUT_BASES:
        raise PersonalFoodValidationError("input_basis is not supported.")
    serving_grams = _optional_positive_number(
        revision_input.serving_grams,
        "serving_grams",
    )
    if revision_input.input_basis == "nutrition_label" and serving_grams is None:
        raise PersonalFoodValidationError(
            "serving_grams is required for nutrition-label input."
        )
    entered = {
        "calories": _optional_nutrient(revision_input.calories, "calories"),
        "protein_g": _optional_nutrient(revision_input.protein_g, "protein_g"),
        "carbs_g": _optional_nutrient(revision_input.carbs_g, "carbs_g"),
        "fat_g": _optional_nutrient(revision_input.fat_g, "fat_g"),
    }
    if all(value is None for value in entered.values()):
        raise PersonalFoodValidationError("At least one nutrition value is required.")
    if revision_input.input_basis == "per_100g":
        return entered
    assert serving_grams is not None
    normalized: dict[str, float | None] = {}
    for key, value in entered.items():
        if value is None:
            normalized[key] = None
            continue
        amount_per_100g = value / serving_grams * 100.0
        if not math.isfinite(amount_per_100g) or amount_per_100g < 0:
            raise PersonalFoodValidationError(
                f"{key} could not be normalized to a finite non-negative value."
            )
        normalized[key] = amount_per_100g
    return normalized


def _fetch_personal_food(
    cursor: sqlite3.Cursor,
    *,
    user_id: int,
    personal_food_id: int,
) -> PersonalFood:
    identity = _fetch_owned_identity_row(
        cursor,
        user_id=user_id,
        personal_food_id=personal_food_id,
    )
    current_revision_id = identity["current_revision_id"]
    if current_revision_id is None:
        raise PersonalFoodError("Personal food has no current revision.")
    cursor.execute(
        """
        SELECT *
        FROM personal_food_revisions
        WHERE personal_food_id = ?
        ORDER BY revision_number
        """,
        (personal_food_id,),
    )
    revisions = tuple(_revision_from_row(row) for row in cursor.fetchall())
    current_revision = next(
        (revision for revision in revisions if revision.id == current_revision_id),
        None,
    )
    if current_revision is None:
        raise PersonalFoodError("Personal food current revision is unavailable.")
    return PersonalFood(
        id=int(identity["id"]),
        user_id=int(identity["user_id"]),
        display_name=str(identity["display_name"]),
        normalized_name=str(identity["normalized_name"]),
        brand_name=identity["brand_name"],
        active=bool(identity["active"]),
        current_revision_id=int(current_revision_id),
        created_at=str(identity["created_at"]),
        updated_at=str(identity["updated_at"]),
        current_revision=current_revision,
        revisions=revisions,
    )


def _fetch_owned_identity_row(
    cursor: sqlite3.Cursor,
    *,
    user_id: int,
    personal_food_id: int,
) -> sqlite3.Row:
    cursor.execute(
        """
        SELECT *
        FROM personal_foods
        WHERE id = ? AND user_id = ?
        """,
        (personal_food_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        raise PersonalFoodNotFoundError("Personal food not found.")
    return row


def _revision_from_row(row: sqlite3.Row) -> PersonalFoodRevision:
    return PersonalFoodRevision(
        id=int(row["id"]),
        personal_food_id=int(row["personal_food_id"]),
        revision_number=int(row["revision_number"]),
        display_name_snapshot=str(row["display_name_snapshot"]),
        brand_name_snapshot=row["brand_name_snapshot"],
        input_basis=row["input_basis"],
        serving_name=row["serving_name"],
        serving_grams=_optional_float(row["serving_grams"]),
        calories_per_100g=_optional_float(row["calories_per_100g"]),
        protein_g_per_100g=_optional_float(row["protein_g_per_100g"]),
        carbs_g_per_100g=_optional_float(row["carbs_g_per_100g"]),
        fat_g_per_100g=_optional_float(row["fat_g_per_100g"]),
        entered_calories=_optional_float(row["entered_calories"]),
        entered_protein_g=_optional_float(row["entered_protein_g"]),
        entered_carbs_g=_optional_float(row["entered_carbs_g"]),
        entered_fat_g=_optional_float(row["entered_fat_g"]),
        source_note=row["source_note"],
        legacy_food_id=int(row["legacy_food_id"]),
        created_at=str(row["created_at"]),
    )


def _assert_user_exists(cursor: sqlite3.Cursor, user_id: int) -> None:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise PersonalFoodUserNotFoundError("User not found.")
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        raise PersonalFoodUserNotFoundError("User not found.")


def _validate_personal_food_id(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PersonalFoodValidationError(
            "personal_food_id must be a positive integer."
        )
    return value


def _required_display_name(value: str | None) -> str:
    if value is None:
        raise PersonalFoodValidationError("display_name is required.")
    display_name = " ".join(value.strip().split())
    if not display_name:
        raise PersonalFoodValidationError("display_name is required.")
    if len(display_name) > 200:
        raise PersonalFoodValidationError("display_name is too long.")
    return display_name


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PersonalFoodValidationError("Text metadata must be text.")
    normalized = " ".join(value.strip().split())
    if not normalized:
        return None
    if len(normalized) > 500:
        raise PersonalFoodValidationError("Text metadata is too long.")
    return normalized


def _optional_nutrient(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise PersonalFoodValidationError(f"{field_name} must be a number.")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise PersonalFoodValidationError(
            f"{field_name} must be a finite non-negative number."
        )
    return number


def _optional_positive_number(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    number = _optional_nutrient(value, field_name)
    if number is None or number <= 0:
        raise PersonalFoodValidationError(f"{field_name} must be greater than zero.")
    return number


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _validate_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise PersonalFoodValidationError("limit must be between 1 and 100.")
    return limit
