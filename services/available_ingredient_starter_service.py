from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from database import get_connection
from services.food_normalization_service import (
    curate_canonical_display_name,
    ensure_starter_canonical_foods_seeded,
    normalize_food_name,
)


@dataclass(frozen=True)
class AvailableIngredientStarterGroupDefinition:
    key: str
    title: str
    search_terms: tuple[str, ...]


AVAILABLE_INGREDIENT_STARTER_GROUPS = (
    AvailableIngredientStarterGroupDefinition(
        key="proteins",
        title="Proteins",
        search_terms=(
            "chicken breast",
            "chicken thigh",
            "ground turkey",
            "sirloin steak",
            "canned tuna",
            "salmon",
            "egg",
            "shrimp",
        ),
    ),
    AvailableIngredientStarterGroupDefinition(
        key="grains_starches",
        title="Grains & starches",
        search_terms=(
            "white rice",
            "brown rice",
            "jasmine rice",
            "basmati rice",
            "pasta",
            "quinoa",
            "oats",
            "flour tortilla",
            "potato",
        ),
    ),
    AvailableIngredientStarterGroupDefinition(
        key="beans_legumes",
        title="Beans & legumes",
        search_terms=(
            "black beans",
            "pinto beans",
            "kidney beans",
            "chickpeas",
            "lentils",
            "cannellini beans",
            "black eyed peas",
        ),
    ),
    AvailableIngredientStarterGroupDefinition(
        key="dairy",
        title="Dairy",
        search_terms=(
            "greek yogurt",
            "cottage cheese",
            "2% milk",
            "whole milk",
            "cheddar cheese",
            "parmesan cheese",
            "sour cream",
        ),
    ),
    AvailableIngredientStarterGroupDefinition(
        key="produce",
        title="Produce",
        search_terms=(
            "broccoli",
            "onion",
            "tomato",
            "bell pepper",
            "carrots",
            "spinach",
            "banana",
            "strawberries",
            "blueberries",
            "avocado",
        ),
    ),
    AvailableIngredientStarterGroupDefinition(
        key="pantry_basics",
        title="Pantry basics",
        search_terms=(
            "olive oil",
            "all purpose flour",
            "cornstarch",
            "apple cider vinegar",
            "worcestershire sauce",
            "granulated sugar",
            "cocoa powder",
            "baking powder",
        ),
    ),
    AvailableIngredientStarterGroupDefinition(
        key="herbs_spices",
        title="Herbs & spices",
        search_terms=(
            "garlic",
            "ginger",
            "black pepper",
            "cayenne pepper",
            "paprika",
            "cumin",
            "basil",
            "rosemary",
            "thyme",
            "mint",
        ),
    ),
)


def list_available_ingredient_starter_groups() -> list[dict[str, Any]]:
    """Resolve curated setup choices to active canonical catalog identities."""

    ensure_starter_canonical_foods_seeded()
    normalized_terms = tuple(
        dict.fromkeys(
            normalize_food_name(term)
            for group in AVAILABLE_INGREDIENT_STARTER_GROUPS
            for term in group.search_terms
        )
    )
    placeholders = ",".join("?" for _ in normalized_terms)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            food.id,
            food.display_name,
            food.normalized_name,
            food.food_type,
            food.search_priority,
            alias.normalized_alias,
            alias.priority AS alias_priority
        FROM canonical_foods AS food
        LEFT JOIN canonical_food_aliases AS alias
          ON alias.canonical_food_id = food.id
        WHERE food.active = 1
          AND (
            food.normalized_name IN ({placeholders})
            OR alias.normalized_alias IN ({placeholders})
          )
        ORDER BY food.search_priority, food.id, alias.priority
        """,
        (*normalized_terms, *normalized_terms),
    )
    rows = cursor.fetchall()
    conn.close()

    best_by_term: dict[str, Any] = {}
    score_by_term: dict[str, tuple[int, int, int, int]] = {}
    for row in rows:
        for term in normalized_terms:
            is_name_match = row["normalized_name"] == term
            is_alias_match = row["normalized_alias"] == term
            if not is_name_match and not is_alias_match:
                continue
            score = (
                0 if is_name_match else 1,
                int(row["search_priority"]),
                int(row["alias_priority"] or 0),
                int(row["id"]),
            )
            if term not in score_by_term or score < score_by_term[term]:
                score_by_term[term] = score
                best_by_term[term] = row

    seen_food_ids: set[int] = set()
    groups: list[dict[str, Any]] = []
    for definition in AVAILABLE_INGREDIENT_STARTER_GROUPS:
        items: list[dict[str, Any]] = []
        for search_term in definition.search_terms:
            row = best_by_term.get(normalize_food_name(search_term))
            if row is None or int(row["id"]) in seen_food_ids:
                continue
            food_id = int(row["id"])
            seen_food_ids.add(food_id)
            items.append(
                {
                    "canonical_food_id": food_id,
                    "display_name": curate_canonical_display_name(
                        str(row["display_name"]),
                        str(row["food_type"]),
                    ),
                    "food_type": str(row["food_type"]),
                }
            )
        groups.append(
            {
                "key": definition.key,
                "title": definition.title,
                "items": items,
            }
        )
    return groups
