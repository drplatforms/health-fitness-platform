from __future__ import annotations

from collections.abc import Iterable

from database import get_connection
from models.food_normalization_models import (
    CanonicalFood,
    CanonicalFoodAlias,
    CanonicalFoodNutrient,
    CanonicalFoodSourceIdentity,
    FoodSourceLink,
    RawFoodSourceRecord,
    RawFoodSourceReviewItem,
    RawSourcePromotionResult,
)
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
    get_aliases_for_canonical_food,
    get_canonical_food,
    get_nutrients_for_canonical_food,
    get_raw_food_source_record,
    normalize_food_name,
)
from services.usda_food_data_import_service import USDA_SOURCE_NAME

DEFAULT_PROMOTABLE_DATA_TYPES = ("foundation_food",)
MACRO_NUTRIENT_FIELD_MAP = (
    ("Calories", "kcal", "calories_per_100g"),
    ("Protein", "g", "protein_g_per_100g"),
    ("Carbohydrate", "g", "carbs_g_per_100g"),
    ("Fat", "g", "fat_g_per_100g"),
)
ALLOWED_PROMOTION_RELATIONSHIP_TYPES = ("primary",)


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_data_type_values(
    include_data_types: Iterable[str] | None,
) -> tuple[str, ...]:
    if include_data_types is None:
        return DEFAULT_PROMOTABLE_DATA_TYPES

    normalized_values = tuple(
        normalized
        for value in include_data_types
        if (normalized := _normalize_text(value).casefold())
    )
    if not normalized_values:
        raise ValueError("include_data_types must contain at least one value.")
    return normalized_values


def _resolve_limit(limit: int) -> int:
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")
    return min(limit, 500)


def _row_to_review_item(row) -> RawFoodSourceReviewItem:
    return RawFoodSourceReviewItem(
        id=int(row["id"]),
        source_name=row["source_name"],
        source_record_id=row["source_record_id"],
        raw_description=row["raw_description"],
        data_type=row["data_type"],
        brand_name=row["brand_name"],
        food_category=row["food_category"],
        import_batch=row["import_batch"],
        calories_per_100g=row["calories_per_100g"],
        protein_g_per_100g=row["protein_g_per_100g"],
        carbs_g_per_100g=row["carbs_g_per_100g"],
        fat_g_per_100g=row["fat_g_per_100g"],
        has_macro_data=bool(row["has_macro_data"]),
    )


def _row_to_food_source_link(row) -> FoodSourceLink:
    return FoodSourceLink(
        id=int(row["id"]),
        canonical_food_id=int(row["canonical_food_id"]),
        raw_food_source_record_id=int(row["raw_food_source_record_id"]),
        relationship_type=row["relationship_type"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_source_identity(row) -> CanonicalFoodSourceIdentity:
    return CanonicalFoodSourceIdentity(
        canonical_food_id=int(row["canonical_food_id"]),
        raw_food_source_record_id=int(row["raw_food_source_record_id"]),
        source_name=row["source_name"],
        source_record_id=row["source_record_id"],
        raw_description=row["raw_description"],
        relationship_type=row["relationship_type"],
    )


def _resolve_promoted_food_type(raw_record: RawFoodSourceRecord) -> str:
    if _normalize_text(raw_record.data_type).casefold() == "branded":
        return "branded"
    return "generic"


def _find_canonical_food_by_name(
    display_name: str,
    food_type: str,
) -> CanonicalFood | None:
    ensure_food_normalization_tables()

    normalized_name = normalize_food_name(display_name)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id
        FROM canonical_foods
        WHERE normalized_name = ? AND food_type = ?
        """,
        (normalized_name, food_type),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return get_canonical_food(int(row["id"]))


def _get_existing_source_link_for_raw_record(
    raw_food_source_record_id: int,
) -> FoodSourceLink | None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM food_source_links
        WHERE raw_food_source_record_id = ?
          AND relationship_type IN ({placeholders})
        ORDER BY
            CASE relationship_type
                WHEN 'primary' THEN 1
                ELSE 2
            END,
            id
        LIMIT 1
        """.format(
            placeholders=",".join("?" for _ in ALLOWED_PROMOTION_RELATIONSHIP_TYPES)
        ),
        (raw_food_source_record_id, *ALLOWED_PROMOTION_RELATIONSHIP_TYPES),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_food_source_link(row)


def _get_source_identity(
    canonical_food_id: int,
    raw_food_source_record_id: int,
    relationship_type: str = "primary",
) -> CanonicalFoodSourceIdentity:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            food_source_links.canonical_food_id,
            food_source_links.raw_food_source_record_id,
            raw_food_source_records.source_name,
            raw_food_source_records.source_record_id,
            raw_food_source_records.raw_description,
            food_source_links.relationship_type
        FROM food_source_links
        JOIN raw_food_source_records
            ON raw_food_source_records.id = food_source_links.raw_food_source_record_id
        WHERE food_source_links.canonical_food_id = ?
          AND food_source_links.raw_food_source_record_id = ?
          AND food_source_links.relationship_type = ?
        """,
        (canonical_food_id, raw_food_source_record_id, relationship_type),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise ValueError(
            "Canonical source identity not found for the promoted raw source record."
        )

    return _row_to_source_identity(row)


def _update_canonical_food_display_name(
    canonical_food_id: int,
    display_name: str,
) -> CanonicalFood:
    ensure_food_normalization_tables()

    normalized_name = normalize_food_name(display_name)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT food_type
        FROM canonical_foods
        WHERE id = ?
        """,
        (canonical_food_id,),
    )
    existing_food_row = cursor.fetchone()
    if existing_food_row is None:
        conn.close()
        raise ValueError(f"Canonical food {canonical_food_id} was not found.")

    food_type = existing_food_row["food_type"]
    cursor.execute(
        """
        SELECT id
        FROM canonical_foods
        WHERE normalized_name = ?
          AND food_type = ?
          AND id != ?
        """,
        (normalized_name, food_type, canonical_food_id),
    )
    conflicting_row = cursor.fetchone()
    if conflicting_row is not None:
        conn.close()
        raise ValueError(
            "Cannot rename promoted canonical food because another canonical food "
            f"already uses '{display_name.strip()}' for food_type '{food_type}'."
        )

    cursor.execute(
        """
        UPDATE canonical_foods
        SET display_name = ?,
            normalized_name = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (display_name.strip(), normalized_name, canonical_food_id),
    )
    conn.commit()
    conn.close()

    updated_food = get_canonical_food(canonical_food_id)
    if updated_food is None:
        raise ValueError(
            f"Canonical food {canonical_food_id} was not found after update."
        )
    return updated_food


def _sync_macro_nutrients(
    canonical_food_id: int,
    raw_record: RawFoodSourceRecord,
) -> list[CanonicalFoodNutrient]:
    synced_nutrient_names: list[str] = []
    for nutrient_name, nutrient_unit, raw_field_name in MACRO_NUTRIENT_FIELD_MAP:
        amount = getattr(raw_record, raw_field_name)
        if amount is None:
            continue
        create_canonical_food_nutrient(
            canonical_food_id=canonical_food_id,
            nutrient_name=nutrient_name,
            nutrient_unit=nutrient_unit,
            amount_per_100g=amount,
            source_policy="direct_source",
            confidence="Moderate",
        )
        synced_nutrient_names.append(nutrient_name)

    conn = get_connection()
    cursor = conn.cursor()
    if synced_nutrient_names:
        placeholders = ",".join("?" for _ in synced_nutrient_names)
        cursor.execute(
            f"""
            DELETE FROM canonical_food_nutrients
            WHERE canonical_food_id = ?
              AND nutrient_name IN ('Calories', 'Protein', 'Carbohydrate', 'Fat')
              AND nutrient_name NOT IN ({placeholders})
            """,
            (canonical_food_id, *synced_nutrient_names),
        )
    else:
        cursor.execute(
            """
            DELETE FROM canonical_food_nutrients
            WHERE canonical_food_id = ?
              AND nutrient_name IN ('Calories', 'Protein', 'Carbohydrate', 'Fat')
            """,
            (canonical_food_id,),
        )
    conn.commit()
    conn.close()

    nutrients = get_nutrients_for_canonical_food(canonical_food_id)
    return [
        nutrient
        for nutrient in nutrients
        if nutrient.nutrient_name in {"Calories", "Protein", "Carbohydrate", "Fat"}
    ]


def _normalize_aliases(
    aliases: Iterable[str] | None,
    canonical_name: str,
) -> list[str]:
    if aliases is None:
        return []

    normalized_canonical_name = normalize_food_name(canonical_name)
    deduped_aliases: list[str] = []
    seen_aliases: set[str] = set()
    for alias in aliases:
        normalized_alias = normalize_food_name(alias)
        if not normalized_alias or normalized_alias == normalized_canonical_name:
            continue
        if normalized_alias in seen_aliases:
            continue
        seen_aliases.add(normalized_alias)
        deduped_aliases.append(_normalize_text(alias))
    return deduped_aliases


def list_promotable_raw_food_source_records(
    *,
    source_name: str = USDA_SOURCE_NAME,
    import_batch: str | None = None,
    description_query: str | None = None,
    include_data_types: Iterable[str] | None = None,
    require_macro_data: bool = False,
    limit: int = 50,
) -> list[RawFoodSourceReviewItem]:
    ensure_food_normalization_tables()

    normalized_data_types = _normalize_data_type_values(include_data_types)
    resolved_limit = _resolve_limit(limit)

    where_clauses = ["source_name = ?"]
    params: list[object] = [source_name.strip()]

    if import_batch is not None and import_batch.strip():
        where_clauses.append("import_batch = ?")
        params.append(import_batch.strip())

    if description_query is not None and description_query.strip():
        where_clauses.append("LOWER(raw_description) LIKE ?")
        params.append(f"%{description_query.strip().casefold()}%")

    placeholders = ",".join("?" for _ in normalized_data_types)
    where_clauses.append(f"LOWER(COALESCE(data_type, '')) IN ({placeholders})")
    params.extend(normalized_data_types)

    if require_macro_data:
        where_clauses.append(
            """
            (
                calories_per_100g IS NOT NULL
                OR protein_g_per_100g IS NOT NULL
                OR carbs_g_per_100g IS NOT NULL
                OR fat_g_per_100g IS NOT NULL
            )
            """
        )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            raw_food_source_records.*,
            CASE
                WHEN calories_per_100g IS NOT NULL
                  OR protein_g_per_100g IS NOT NULL
                  OR carbs_g_per_100g IS NOT NULL
                  OR fat_g_per_100g IS NOT NULL
                THEN 1
                ELSE 0
            END AS has_macro_data
        FROM raw_food_source_records
        WHERE {" AND ".join(where_clauses)}
        ORDER BY LOWER(raw_description), id
        LIMIT ?
        """,
        (*params, resolved_limit),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_review_item(row) for row in rows]


def promote_raw_source_record_to_canonical(
    raw_food_source_record_id: int,
    *,
    canonical_name: str | None = None,
    aliases: Iterable[str] | None = None,
) -> RawSourcePromotionResult:
    ensure_food_normalization_tables()

    raw_record = get_raw_food_source_record(raw_food_source_record_id)
    if raw_record is None:
        raise ValueError(
            f"Raw food source record {raw_food_source_record_id} was not found."
        )

    existing_source_link = _get_existing_source_link_for_raw_record(raw_record.id)
    promoted_food: CanonicalFood | None = None

    if existing_source_link is not None:
        promoted_food = get_canonical_food(existing_source_link.canonical_food_id)
        if promoted_food is None:
            raise ValueError(
                f"Canonical food {existing_source_link.canonical_food_id} linked to raw "
                f"record {raw_record.id} was not found."
            )
        if canonical_name and canonical_name.strip():
            promoted_food = _update_canonical_food_display_name(
                promoted_food.id,
                canonical_name,
            )
    else:
        resolved_name = (
            canonical_name.strip() if canonical_name else raw_record.raw_description
        )
        resolved_food_type = _resolve_promoted_food_type(raw_record)
        existing_named_food = _find_canonical_food_by_name(
            resolved_name,
            resolved_food_type,
        )
        if existing_named_food is not None:
            promoted_food = existing_named_food
        else:
            promoted_food = create_canonical_food(
                display_name=resolved_name,
                food_type=resolved_food_type,
                default_unit="grams",
                default_grams=100.0,
                search_priority=100,
                active=True,
                notes=(
                    "Promoted from raw food source record for curated canonical use."
                ),
            )

    if promoted_food is None:
        raise ValueError("Promotion failed to resolve a canonical food.")

    normalized_aliases = _normalize_aliases(
        aliases,
        promoted_food.display_name,
    )
    stored_aliases: list[CanonicalFoodAlias] = []
    for alias in normalized_aliases:
        stored_aliases.append(
            create_canonical_food_alias(
                canonical_food_id=promoted_food.id,
                alias=alias,
                priority=50,
            )
        )

    synced_nutrients = _sync_macro_nutrients(promoted_food.id, raw_record)

    if existing_source_link is None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO food_source_links (
                canonical_food_id,
                raw_food_source_record_id,
                relationship_type,
                updated_at
            )
            VALUES (?, ?, 'primary', CURRENT_TIMESTAMP)
            ON CONFLICT(
                canonical_food_id,
                raw_food_source_record_id,
                relationship_type
            ) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
            """,
            (promoted_food.id, raw_record.id),
        )
        conn.commit()
        conn.close()
        relationship_type = "primary"
    else:
        relationship_type = existing_source_link.relationship_type

    source_identity = _get_source_identity(
        promoted_food.id,
        raw_record.id,
        relationship_type=relationship_type,
    )

    return RawSourcePromotionResult(
        raw_source_record=raw_record,
        canonical_food=promoted_food,
        source_identity=source_identity,
        aliases=get_aliases_for_canonical_food(promoted_food.id),
        nutrients=synced_nutrients,
    )
