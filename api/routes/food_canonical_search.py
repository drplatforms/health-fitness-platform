from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.available_ingredient_starter_service import (
    list_available_ingredient_starter_groups,
)
from services.food_normalization_service import (
    browse_canonical_foods,
    curate_canonical_display_name,
    ensure_starter_canonical_foods_seeded,
    get_canonical_food,
    get_nutrients_for_canonical_food,
    get_raw_food_source_record,
    get_source_links_for_canonical_food,
    search_canonical_foods,
)
from services.nutrition_serving_unit_service import (
    get_active_serving_units_for_canonical_food,
    seed_canonical_food_serving_units,
)
from services.user_canonical_food_name_service import (
    UserCanonicalFoodNameNotFoundError,
    browse_user_canonical_foods,
    get_user_canonical_food_names,
    search_user_canonical_foods,
)

router = APIRouter()

_CANONICAL_SEARCH_MIN_QUERY_LENGTH = 2
_CANONICAL_SEARCH_DEFAULT_LIMIT = 20
_CANONICAL_SEARCH_MAX_LIMIT = 25
_CANONICAL_BROWSE_SCOPES = {"all", "catalog", "added"}

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


def _normalize_nutrient_name(name: str) -> str:
    return " ".join(name.strip().lower().replace("_", " ").split())


def _bounded_limit(limit: int) -> int:
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be at least 1.")
    return min(limit, _CANONICAL_SEARCH_MAX_LIMIT)


def _build_nutrient_summary(canonical_food_id: int) -> dict[str, float]:
    summary: dict[str, float] = {}
    for nutrient in get_nutrients_for_canonical_food(canonical_food_id):
        summary_key = _NUTRIENT_SUMMARY_KEYS.get(
            _normalize_nutrient_name(nutrient.nutrient_name)
        )
        if summary_key is not None:
            summary[summary_key] = nutrient.amount_per_100g
    return summary


def _build_source_links(canonical_food_id: int) -> list[dict[str, str | int | None]]:
    public_links: list[dict[str, str | int | None]] = []
    for link in get_source_links_for_canonical_food(canonical_food_id):
        raw_record = get_raw_food_source_record(link.raw_food_source_record_id)
        if raw_record is None:
            continue
        public_links.append(
            {
                "relationship_type": link.relationship_type,
                "source_name": raw_record.source_name,
                "source_record_id": raw_record.source_record_id,
                "raw_description": raw_record.raw_description,
                "brand_name": raw_record.brand_name,
                "food_category": raw_record.food_category,
                "source_url": raw_record.source_url,
                "license": raw_record.license,
            }
        )
    return public_links


def _build_source_summary(canonical_food_id: int) -> dict[str, str] | None:
    for link in get_source_links_for_canonical_food(canonical_food_id):
        raw_record = get_raw_food_source_record(link.raw_food_source_record_id)
        if raw_record is None:
            continue
        return {
            "source_name": raw_record.source_name,
            "source_record_id": raw_record.source_record_id,
        }
    return None


def _serving_unit_to_public_dict(serving_unit, *, is_default: bool = False) -> dict:
    return {
        "id": serving_unit.id,
        "serving_unit_id": serving_unit.id,
        "display_label": serving_unit.display_name,
        "display_name": serving_unit.display_name,
        "unit_name": serving_unit.unit_name,
        "unit_quantity": serving_unit.unit_quantity,
        "grams_per_unit": serving_unit.grams_default,
        "grams_default": serving_unit.grams_default,
        "grams_min": serving_unit.grams_min,
        "grams_max": serving_unit.grams_max,
        "confidence": serving_unit.confidence,
        "is_default": is_default,
        "amount_source": "serving_unit_estimate",
        "source": serving_unit.source,
        "source_notes": serving_unit.source_note,
        "sort_order": serving_unit.sort_order,
    }


def _get_public_active_canonical_food(canonical_food_id: int):
    canonical_food = get_canonical_food(canonical_food_id)
    if canonical_food is None or not canonical_food.active:
        raise HTTPException(status_code=404, detail="Canonical food not found.")
    return canonical_food


def _canonical_search_result_to_public_dict(
    result,
    *,
    include_source_links: bool,
    custom_display_name: str | None = None,
) -> dict:
    food = result.canonical_food
    original_food = get_canonical_food(food.id)
    original_display_name = (
        curate_canonical_display_name(
            original_food.display_name, original_food.food_type
        )
        if original_food is not None
        else food.display_name
    )
    payload = {
        "canonical_food_id": food.id,
        "display_name": custom_display_name
        or curate_canonical_display_name(food.display_name, food.food_type),
        "food_type": food.food_type,
        "default_unit": food.default_unit,
        "default_grams": food.default_grams,
        "search_priority": food.search_priority,
        "matched_on": result.matched_on,
        "aliases": list(result.aliases),
        "original_display_name": original_display_name,
        "custom_display_name": custom_display_name,
    }

    nutrient_summary = _build_nutrient_summary(food.id)
    if nutrient_summary:
        payload["nutrient_summary"] = nutrient_summary

    source_summary = _build_source_summary(food.id)
    if source_summary is not None:
        payload["source"] = source_summary

    if include_source_links:
        payload["source_links"] = _build_source_links(food.id)

    return payload


@router.get("/foods/canonical/search")
def canonical_food_search_endpoint(
    q: str = Query(default=""),
    limit: int = Query(default=_CANONICAL_SEARCH_DEFAULT_LIMIT),
    include_inactive: bool = False,
    include_source_links: bool = False,
    user_id: int | None = None,
):
    """Return public-safe canonical food search results for user-facing food picks."""

    query = q.strip()
    if not query:
        return {
            "success": True,
            "query": "",
            "results": [],
        }

    if len(query) < _CANONICAL_SEARCH_MIN_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="q must be at least 2 characters for canonical food search.",
        )

    ensure_starter_canonical_foods_seeded()
    try:
        results = (
            search_user_canonical_foods(
                query,
                user_id=user_id,
                limit=_bounded_limit(limit),
                include_inactive=include_inactive,
            )
            if user_id is not None
            else search_canonical_foods(
                query,
                limit=_bounded_limit(limit),
                include_inactive=include_inactive,
            )
        )
    except UserCanonicalFoodNameNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    custom_names = (
        get_user_canonical_food_names(
            user_id=user_id,
            canonical_food_ids=[result.canonical_food.id for result in results],
        )
        if user_id is not None
        else {}
    )

    return {
        "success": True,
        "query": query,
        "results": [
            _canonical_search_result_to_public_dict(
                result,
                include_source_links=include_source_links,
                custom_display_name=custom_names.get(result.canonical_food.id),
            )
            for result in results
        ],
    }


@router.get("/foods/canonical/browse")
def canonical_food_browse_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_CANONICAL_SEARCH_DEFAULT_LIMIT),
    scope: str = Query(default="all"),
    q: str = Query(default="", max_length=120),
    start_letter: str = Query(default="", max_length=1),
    user_id: int | None = None,
):
    """Return one bounded, stable page of active foods for catalog discovery."""

    normalized_scope = scope.strip().lower()
    if normalized_scope not in _CANONICAL_BROWSE_SCOPES:
        raise HTTPException(
            status_code=400,
            detail="scope must be one of: all, catalog, added.",
        )
    normalized_start_letter = start_letter.strip().upper()
    if normalized_start_letter and not normalized_start_letter.isascii():
        raise HTTPException(status_code=400, detail="start_letter must be A-Z.")
    if normalized_start_letter and not normalized_start_letter.isalpha():
        raise HTTPException(status_code=400, detail="start_letter must be A-Z.")

    ensure_starter_canonical_foods_seeded()
    page_limit = _bounded_limit(limit)
    try:
        results = (
            browse_user_canonical_foods(
                user_id=user_id,
                offset=offset,
                limit=page_limit + 1,
                catalog_scope=normalized_scope,
                query=q,
                start_letter=normalized_start_letter,
            )
            if user_id is not None
            else browse_canonical_foods(
                offset=offset,
                limit=page_limit + 1,
                catalog_scope=normalized_scope,
                query=q,
                start_letter=normalized_start_letter,
            )
        )
    except UserCanonicalFoodNameNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    page_results = results[:page_limit]
    custom_names = (
        get_user_canonical_food_names(
            user_id=user_id,
            canonical_food_ids=[result.canonical_food.id for result in page_results],
        )
        if user_id is not None
        else {}
    )
    has_more = len(results) > page_limit
    return {
        "success": True,
        "scope": normalized_scope,
        "query": q.strip(),
        "start_letter": normalized_start_letter,
        "offset": offset,
        "next_offset": offset + page_limit if has_more else None,
        "has_more": has_more,
        "results": [
            _canonical_search_result_to_public_dict(
                result,
                include_source_links=False,
                custom_display_name=custom_names.get(result.canonical_food.id),
            )
            for result in page_results
        ],
    }


@router.get("/foods/canonical/available-ingredient-starters")
def available_ingredient_starter_groups_endpoint(user_id: int | None = None):
    groups = list_available_ingredient_starter_groups()
    if user_id is not None:
        items = [item for group in groups for item in group["items"]]
        custom_names = get_user_canonical_food_names(
            user_id=user_id,
            canonical_food_ids=[item["canonical_food_id"] for item in items],
        )
        for group in groups:
            for item in group["items"]:
                custom_name = custom_names.get(item["canonical_food_id"])
                if custom_name is not None:
                    item["display_name"] = custom_name
    return {
        "success": True,
        "groups": groups,
    }


@router.get("/foods/canonical/{canonical_food_id}/serving-units")
def canonical_food_serving_units_endpoint(canonical_food_id: int):
    """Return public-safe active serving units for a canonical food."""

    ensure_starter_canonical_foods_seeded()
    seed_canonical_food_serving_units()

    canonical_food = _get_public_active_canonical_food(canonical_food_id)
    serving_units = get_active_serving_units_for_canonical_food(canonical_food.id)

    return {
        "success": True,
        "canonical_food_id": canonical_food.id,
        "display_name": canonical_food.display_name,
        "serving_units": [
            _serving_unit_to_public_dict(
                serving_unit,
                is_default=index == 0,
            )
            for index, serving_unit in enumerate(serving_units)
        ],
    }
