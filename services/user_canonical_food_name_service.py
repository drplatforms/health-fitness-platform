from __future__ import annotations

from dataclasses import replace
from typing import Any

from database import get_connection
from models.food_normalization_models import CanonicalFoodSearchResult
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    get_aliases_for_canonical_food,
    get_canonical_food,
    normalize_food_name,
    search_canonical_foods,
)

USER_CANONICAL_FOOD_NAMES_TABLE_NAME = "user_canonical_food_names"
MAX_CUSTOM_DISPLAY_NAME_LENGTH = 120


class UserCanonicalFoodNameError(ValueError):
    pass


class UserCanonicalFoodNameNotFoundError(UserCanonicalFoodNameError):
    pass


def ensure_user_canonical_food_name_schema() -> None:
    ensure_food_normalization_tables()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {USER_CANONICAL_FOOD_NAMES_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            canonical_food_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, canonical_food_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id)
        )
        """
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_user_canonical_food_names_search
        ON {USER_CANONICAL_FOOD_NAMES_TABLE_NAME}(user_id, normalized_name)
        """
    )
    conn.commit()
    conn.close()


def set_user_canonical_food_name(
    *, user_id: int, canonical_food_id: int, display_name: str
) -> dict[str, Any]:
    ensure_user_canonical_food_name_schema()
    _assert_user_exists(user_id)
    food = _active_canonical_food(canonical_food_id)
    resolved_name = _validated_display_name(display_name)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT INTO {USER_CANONICAL_FOOD_NAMES_TABLE_NAME} (
            user_id, canonical_food_id, display_name, normalized_name
        ) VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, canonical_food_id) DO UPDATE SET
            display_name = excluded.display_name,
            normalized_name = excluded.normalized_name,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, food.id, resolved_name, normalize_food_name(resolved_name)),
    )
    conn.commit()
    conn.close()
    return _public_name(food.id, food.display_name, resolved_name)


def remove_user_canonical_food_name(*, user_id: int, canonical_food_id: int) -> bool:
    ensure_user_canonical_food_name_schema()
    _assert_user_exists(user_id)
    _active_canonical_food(canonical_food_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        DELETE FROM {USER_CANONICAL_FOOD_NAMES_TABLE_NAME}
        WHERE user_id = ? AND canonical_food_id = ?
        """,
        (user_id, canonical_food_id),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_user_canonical_food_name(*, user_id: int, canonical_food_id: int) -> str | None:
    ensure_user_canonical_food_name_schema()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT display_name
        FROM {USER_CANONICAL_FOOD_NAMES_TABLE_NAME}
        WHERE user_id = ? AND canonical_food_id = ?
        """,
        (user_id, canonical_food_id),
    )
    row = cursor.fetchone()
    conn.close()
    return str(row["display_name"]) if row is not None else None


def get_user_canonical_food_names(
    *, user_id: int, canonical_food_ids: list[int]
) -> dict[int, str]:
    ensure_user_canonical_food_name_schema()
    resolved_ids = list(dict.fromkeys(int(food_id) for food_id in canonical_food_ids))
    if not resolved_ids:
        return {}
    placeholders = ",".join("?" for _ in resolved_ids)
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT canonical_food_id, display_name
        FROM {USER_CANONICAL_FOOD_NAMES_TABLE_NAME}
        WHERE user_id = ? AND canonical_food_id IN ({placeholders})
        """,
        (user_id, *resolved_ids),
    ).fetchall()
    conn.close()
    return {int(row["canonical_food_id"]): str(row["display_name"]) for row in rows}


def browse_user_canonical_foods(
    *,
    user_id: int,
    offset: int = 0,
    limit: int = 20,
    catalog_scope: str = "all",
    query: str = "",
    start_letter: str = "",
) -> list[CanonicalFoodSearchResult]:
    """Browse active foods ordered and filtered by the user's visible names."""

    ensure_user_canonical_food_name_schema()
    _assert_user_exists(user_id)
    clauses = ["foods.active = 1"]
    params: list[Any] = [user_id]
    if catalog_scope == "catalog":
        clauses.append("foods.food_type != 'branded'")
    elif catalog_scope == "added":
        clauses.append("foods.food_type = 'branded'")
    normalized_query = normalize_food_name(query)
    if normalized_query:
        clauses.append("(foods.normalized_name LIKE ? OR names.normalized_name LIKE ?)")
        like_query = f"%{normalized_query}%"
        params.extend((like_query, like_query))
    if start_letter:
        clauses.append(
            "COALESCE(names.display_name, foods.display_name) " "COLLATE NOCASE >= ?"
        )
        params.append(start_letter)
    params.extend((max(1, int(limit)), max(0, int(offset))))

    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT foods.id,
               COALESCE(names.display_name, foods.display_name) AS browse_name
        FROM canonical_foods AS foods
        LEFT JOIN {USER_CANONICAL_FOOD_NAMES_TABLE_NAME} AS names
          ON names.canonical_food_id = foods.id AND names.user_id = ?
        WHERE {' AND '.join(clauses)}
        ORDER BY browse_name COLLATE NOCASE, foods.id
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()
    conn.close()

    results: list[CanonicalFoodSearchResult] = []
    for row in rows:
        food = get_canonical_food(int(row["id"]))
        if food is None:
            continue
        visible_name = str(row["browse_name"])
        results.append(
            CanonicalFoodSearchResult(
                canonical_food=replace(food, display_name=visible_name),
                matched_on="browse",
                matched_value=visible_name,
                rank_score=food.search_priority,
                aliases=[],
            )
        )
    return results


def search_user_canonical_foods(
    search_term: str,
    *,
    user_id: int,
    limit: int = 20,
    include_inactive: bool = False,
) -> list[CanonicalFoodSearchResult]:
    ensure_user_canonical_food_name_schema()
    _assert_user_exists(user_id)
    normalized_query = normalize_food_name(search_term)
    if not normalized_query:
        return []

    resolved_limit = max(1, int(limit))
    base_results = search_canonical_foods(
        search_term,
        limit=resolved_limit,
        include_inactive=include_inactive,
    )
    custom_matches = _custom_name_matches(
        user_id=user_id,
        normalized_query=normalized_query,
        limit=resolved_limit,
        include_inactive=include_inactive,
    )

    candidates = [*custom_matches, *base_results]
    custom_names = get_user_canonical_food_names(
        user_id=user_id,
        canonical_food_ids=[result.canonical_food.id for result in candidates],
    )
    merged: list[CanonicalFoodSearchResult] = []
    seen_ids: set[int] = set()
    for result in candidates:
        food_id = result.canonical_food.id
        if food_id in seen_ids:
            continue
        custom_name = custom_names.get(food_id)
        if custom_name is not None:
            result = replace(
                result,
                canonical_food=replace(result.canonical_food, display_name=custom_name),
            )
        merged.append(result)
        seen_ids.add(food_id)
        if len(merged) >= resolved_limit:
            break
    return merged


def _custom_name_matches(
    *,
    user_id: int,
    normalized_query: str,
    limit: int,
    include_inactive: bool,
) -> list[CanonicalFoodSearchResult]:
    like_query = f"%{normalized_query}%"
    prefix_query = f"{normalized_query}%"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT names.canonical_food_id, names.display_name,
               CASE
                   WHEN names.normalized_name = ? THEN 0
                   WHEN names.normalized_name LIKE ? THEN 10
                   ELSE 30
               END + foods.search_priority AS rank_score
        FROM {USER_CANONICAL_FOOD_NAMES_TABLE_NAME} AS names
        JOIN canonical_foods AS foods ON foods.id = names.canonical_food_id
        WHERE names.user_id = ?
          AND (? = 1 OR foods.active = 1)
          AND names.normalized_name LIKE ?
        ORDER BY rank_score, names.display_name COLLATE NOCASE
        LIMIT ?
        """,
        (
            normalized_query,
            prefix_query,
            user_id,
            1 if include_inactive else 0,
            like_query,
            limit,
        ),
    )
    rows = cursor.fetchall()
    conn.close()

    results: list[CanonicalFoodSearchResult] = []
    for row in rows:
        food = get_canonical_food(int(row["canonical_food_id"]))
        if food is None:
            continue
        results.append(
            CanonicalFoodSearchResult(
                canonical_food=replace(food, display_name=str(row["display_name"])),
                matched_on="custom_display_name",
                matched_value=str(row["display_name"]),
                rank_score=int(row["rank_score"]),
                aliases=[
                    alias.alias for alias in get_aliases_for_canonical_food(food.id)
                ],
            )
        )
    return results


def _public_name(
    canonical_food_id: int, original_display_name: str, custom_display_name: str
) -> dict[str, Any]:
    return {
        "canonical_food_id": canonical_food_id,
        "display_name": custom_display_name,
        "custom_display_name": custom_display_name,
        "original_display_name": original_display_name,
    }


def _validated_display_name(display_name: str) -> str:
    if not isinstance(display_name, str):
        raise UserCanonicalFoodNameError("display_name must be text.")
    resolved = " ".join(display_name.strip().split())
    if not resolved:
        raise UserCanonicalFoodNameError("display_name is required.")
    if len(resolved) > MAX_CUSTOM_DISPLAY_NAME_LENGTH:
        raise UserCanonicalFoodNameError(
            f"display_name must be {MAX_CUSTOM_DISPLAY_NAME_LENGTH} characters or fewer."
        )
    return resolved


def _assert_user_exists(user_id: int) -> None:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise UserCanonicalFoodNameNotFoundError("User not found.")
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row is None:
        raise UserCanonicalFoodNameNotFoundError("User not found.")


def _active_canonical_food(canonical_food_id: int):
    if (
        isinstance(canonical_food_id, bool)
        or not isinstance(canonical_food_id, int)
        or canonical_food_id <= 0
    ):
        raise UserCanonicalFoodNameError(
            "canonical_food_id must be a positive integer."
        )
    food = get_canonical_food(canonical_food_id)
    if food is None or not food.active:
        raise UserCanonicalFoodNameNotFoundError("Canonical food not found.")
    return food
