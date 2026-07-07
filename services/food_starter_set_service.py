from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from database import get_connection
from models.food_normalization_models import RawFoodSourceRecord
from services.food_canonical_promotion_service import (
    DEFAULT_PROMOTABLE_DATA_TYPES,
    promote_raw_source_record_to_canonical,
)
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    normalize_food_name,
)
from services.food_starter_set_definitions import (
    STARTER_FOOD_DEFINITIONS,
    StarterFoodDefinition,
)
from services.usda_food_data_import_service import USDA_SOURCE_NAME

StarterSetStatus = Literal[
    "matched",
    "skipped_missing",
    "skipped_ambiguous",
    "skipped_raw_only",
    "already_promoted",
]

RAW_SOURCE_TERMS = {"raw", "uncooked"}


@dataclass(frozen=True)
class StarterFoodPromotionItem:
    display_name: str
    category: str
    status: StarterSetStatus
    raw_food_source_record_id: int | None = None
    source_name: str | None = None
    source_record_id: str | None = None
    raw_description: str | None = None
    canonical_food_id: int | None = None
    canonical_display_name: str | None = None
    reason: str | None = None
    aliases: tuple[str, ...] = ()
    nutrients_synced: tuple[str, ...] = ()


@dataclass(frozen=True)
class StarterSetPromotionReport:
    dry_run: bool
    definition_count: int
    processed_count: int
    matched: list[StarterFoodPromotionItem] = field(default_factory=list)
    skipped_missing: list[StarterFoodPromotionItem] = field(default_factory=list)
    skipped_ambiguous: list[StarterFoodPromotionItem] = field(default_factory=list)
    skipped_raw_only: list[StarterFoodPromotionItem] = field(default_factory=list)
    already_promoted: list[StarterFoodPromotionItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "dry_run": self.dry_run,
            "definition_count": self.definition_count,
            "processed_count": self.processed_count,
            "matched": [asdict(item) for item in self.matched],
            "skipped_missing": [asdict(item) for item in self.skipped_missing],
            "skipped_ambiguous": [asdict(item) for item in self.skipped_ambiguous],
            "skipped_raw_only": [asdict(item) for item in self.skipped_raw_only],
            "already_promoted": [asdict(item) for item in self.already_promoted],
            "summary": {
                "matched": len(self.matched),
                "skipped_missing": len(self.skipped_missing),
                "skipped_ambiguous": len(self.skipped_ambiguous),
                "skipped_raw_only": len(self.skipped_raw_only),
                "already_promoted": len(self.already_promoted),
            },
        }


@dataclass(frozen=True)
class _CandidateMatch:
    raw_record: RawFoodSourceRecord
    score: int
    matched_search_term: str
    unsafe_raw_source: bool


def _row_to_raw_food_source_record(row) -> RawFoodSourceRecord:
    return RawFoodSourceRecord(
        id=row["id"],
        source_name=row["source_name"],
        source_record_id=row["source_record_id"],
        raw_description=row["raw_description"],
        brand_name=row["brand_name"],
        food_category=row["food_category"],
        data_type=row["data_type"],
        gtin_upc=row["gtin_upc"],
        serving_size=row["serving_size"],
        serving_size_unit=row["serving_size_unit"],
        calories_per_100g=row["calories_per_100g"],
        protein_g_per_100g=row["protein_g_per_100g"],
        carbs_g_per_100g=row["carbs_g_per_100g"],
        fat_g_per_100g=row["fat_g_per_100g"],
        import_batch=row["import_batch"],
        source_payload_json=row["source_payload_json"],
        license=row["license"],
        source_url=row["source_url"],
        imported_at=row["imported_at"],
        updated_at=row["updated_at"],
    )


def _normalize_data_types(
    include_data_types: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if include_data_types is None:
        return DEFAULT_PROMOTABLE_DATA_TYPES
    normalized = tuple(
        value
        for raw_value in include_data_types
        if (value := " ".join(raw_value.strip().casefold().split()))
    )
    if not normalized:
        raise ValueError("include_data_types must contain at least one value.")
    return normalized


def _selected_definitions(
    *,
    include_categories: tuple[str, ...] | None,
    limit: int | None,
) -> list[StarterFoodDefinition]:
    normalized_categories = {
        category.strip().casefold()
        for category in include_categories or ()
        if category.strip()
    }
    definitions = [
        definition
        for definition in STARTER_FOOD_DEFINITIONS
        if not normalized_categories
        or definition.category.casefold() in normalized_categories
    ]
    if limit is not None:
        if limit <= 0:
            raise ValueError("limit must be a positive integer.")
        definitions = definitions[:limit]
    return definitions


def _tokens_for(value: str) -> set[str]:
    return set(normalize_food_name(value).split())


def _contains_all_tokens(normalized_description: str, search_term: str) -> bool:
    search_tokens = _tokens_for(search_term)
    description_tokens = set(normalized_description.split())
    return bool(search_tokens) and search_tokens.issubset(description_tokens)


def _contains_phrase_or_tokens(normalized_description: str, term: str) -> bool:
    normalized_term = normalize_food_name(term)
    if not normalized_term:
        return False
    return normalized_term in normalized_description or _contains_all_tokens(
        normalized_description, normalized_term
    )


def _has_macro_data(raw_record: RawFoodSourceRecord) -> bool:
    return any(
        value is not None
        for value in (
            raw_record.calories_per_100g,
            raw_record.protein_g_per_100g,
            raw_record.carbs_g_per_100g,
            raw_record.fat_g_per_100g,
        )
    )


def _macro_count(raw_record: RawFoodSourceRecord) -> int:
    return sum(
        value is not None
        for value in (
            raw_record.calories_per_100g,
            raw_record.protein_g_per_100g,
            raw_record.carbs_g_per_100g,
            raw_record.fat_g_per_100g,
        )
    )


def _is_unsafe_raw_source(
    raw_record: RawFoodSourceRecord,
    definition: StarterFoodDefinition,
) -> bool:
    if definition.raw_source_safe:
        return False
    normalized_description = normalize_food_name(raw_record.raw_description)
    return bool(RAW_SOURCE_TERMS.intersection(normalized_description.split()))


def _score_candidate(
    raw_record: RawFoodSourceRecord,
    definition: StarterFoodDefinition,
    *,
    matched_search_term: str,
) -> _CandidateMatch:
    normalized_description = normalize_food_name(raw_record.raw_description)
    score = 100
    score += 15 * _macro_count(raw_record)

    normalized_search_term = normalize_food_name(matched_search_term)
    if normalized_description == normalized_search_term:
        score += 80
    elif normalized_search_term in normalized_description:
        score += 40

    for prefer_term in definition.prefer_terms:
        if _contains_phrase_or_tokens(normalized_description, prefer_term):
            score += 20

    for avoid_term in definition.avoid_terms:
        if _contains_phrase_or_tokens(normalized_description, avoid_term):
            score -= 45

    unsafe_raw_source = _is_unsafe_raw_source(raw_record, definition)
    if unsafe_raw_source:
        score -= 200

    return _CandidateMatch(
        raw_record=raw_record,
        score=score,
        matched_search_term=matched_search_term,
        unsafe_raw_source=unsafe_raw_source,
    )


def _candidate_raw_records(
    *,
    source_name: str,
    include_data_types: tuple[str, ...],
) -> list[RawFoodSourceRecord]:
    ensure_food_normalization_tables()

    placeholders = ",".join("?" for _ in include_data_types)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM raw_food_source_records
        WHERE source_name = ?
          AND LOWER(COALESCE(data_type, '')) IN ({placeholders})
          AND (
              calories_per_100g IS NOT NULL
              OR protein_g_per_100g IS NOT NULL
              OR carbs_g_per_100g IS NOT NULL
              OR fat_g_per_100g IS NOT NULL
          )
        ORDER BY LOWER(raw_description), id
        """,
        (source_name, *include_data_types),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_raw_food_source_record(row) for row in rows]


def _existing_primary_canonical_food_id(raw_food_source_record_id: int) -> int | None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT canonical_food_id
        FROM food_source_links
        WHERE raw_food_source_record_id = ?
          AND relationship_type = 'primary'
        ORDER BY id
        LIMIT 1
        """,
        (raw_food_source_record_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return int(row["canonical_food_id"])


def _find_best_candidate(
    definition: StarterFoodDefinition,
    raw_records: list[RawFoodSourceRecord],
) -> tuple[StarterSetStatus, list[_CandidateMatch]]:
    candidate_matches: list[_CandidateMatch] = []
    raw_only_matches: list[_CandidateMatch] = []

    for raw_record in raw_records:
        normalized_description = normalize_food_name(raw_record.raw_description)
        if not _has_macro_data(raw_record):
            continue

        matched_search_term = next(
            (
                search_term
                for search_term in definition.search_terms
                if _contains_all_tokens(normalized_description, search_term)
            ),
            None,
        )
        if matched_search_term is None:
            continue

        candidate = _score_candidate(
            raw_record,
            definition,
            matched_search_term=matched_search_term,
        )
        if candidate.unsafe_raw_source:
            raw_only_matches.append(candidate)
            continue
        candidate_matches.append(candidate)

    if not candidate_matches:
        if raw_only_matches:
            return "skipped_raw_only", sorted(
                raw_only_matches,
                key=lambda item: (-item.score, item.raw_record.id),
            )
        return "skipped_missing", []

    ranked_matches = sorted(
        candidate_matches,
        key=lambda item: (-item.score, item.raw_record.id),
    )
    if len(ranked_matches) > 1 and ranked_matches[0].score == ranked_matches[1].score:
        tied_top_matches = [
            candidate
            for candidate in ranked_matches
            if candidate.score == ranked_matches[0].score
        ]
        return "skipped_ambiguous", tied_top_matches
    return "matched", [ranked_matches[0]]


def _item_for_candidate(
    definition: StarterFoodDefinition,
    status: StarterSetStatus,
    candidate: _CandidateMatch | None,
    *,
    canonical_food_id: int | None = None,
    canonical_display_name: str | None = None,
    reason: str | None = None,
    aliases: tuple[str, ...] = (),
    nutrients_synced: tuple[str, ...] = (),
) -> StarterFoodPromotionItem:
    raw_record = candidate.raw_record if candidate is not None else None
    return StarterFoodPromotionItem(
        display_name=definition.display_name,
        category=definition.category,
        status=status,
        raw_food_source_record_id=raw_record.id if raw_record is not None else None,
        source_name=raw_record.source_name if raw_record is not None else None,
        source_record_id=(
            raw_record.source_record_id if raw_record is not None else None
        ),
        raw_description=(
            raw_record.raw_description if raw_record is not None else None
        ),
        canonical_food_id=canonical_food_id,
        canonical_display_name=canonical_display_name,
        reason=reason,
        aliases=aliases,
        nutrients_synced=nutrients_synced,
    )


def promote_canonical_food_starter_set(
    *,
    dry_run: bool = False,
    limit: int | None = None,
    include_categories: tuple[str, ...] | None = None,
    source_name: str = USDA_SOURCE_NAME,
    include_data_types: tuple[str, ...] | None = None,
) -> StarterSetPromotionReport:
    """Promote high-confidence starter foods from existing raw source records."""

    ensure_food_normalization_tables()
    normalized_data_types = _normalize_data_types(include_data_types)
    definitions = _selected_definitions(
        include_categories=include_categories,
        limit=limit,
    )
    raw_records = _candidate_raw_records(
        source_name=source_name,
        include_data_types=normalized_data_types,
    )

    matched: list[StarterFoodPromotionItem] = []
    skipped_missing: list[StarterFoodPromotionItem] = []
    skipped_ambiguous: list[StarterFoodPromotionItem] = []
    skipped_raw_only: list[StarterFoodPromotionItem] = []
    already_promoted: list[StarterFoodPromotionItem] = []

    for definition in definitions:
        status, candidates = _find_best_candidate(definition, raw_records)
        candidate = candidates[0] if candidates else None

        if status == "skipped_missing":
            skipped_missing.append(
                _item_for_candidate(
                    definition,
                    "skipped_missing",
                    None,
                    reason="No existing source record matched all search terms.",
                )
            )
            continue

        if status == "skipped_raw_only":
            skipped_raw_only.append(
                _item_for_candidate(
                    definition,
                    "skipped_raw_only",
                    candidate,
                    reason=(
                        "Only raw/uncooked source candidates were available for "
                        "a meat/fowl/fish starter item."
                    ),
                )
            )
            continue

        if status == "skipped_ambiguous":
            skipped_ambiguous.append(
                _item_for_candidate(
                    definition,
                    "skipped_ambiguous",
                    candidate,
                    reason="Multiple source candidates tied for the top score.",
                )
            )
            continue

        if candidate is None:
            skipped_missing.append(
                _item_for_candidate(
                    definition,
                    "skipped_missing",
                    None,
                    reason="No existing source record matched.",
                )
            )
            continue

        existing_canonical_food_id = _existing_primary_canonical_food_id(
            candidate.raw_record.id
        )
        if existing_canonical_food_id is not None:
            already_promoted.append(
                _item_for_candidate(
                    definition,
                    "already_promoted",
                    candidate,
                    canonical_food_id=existing_canonical_food_id,
                    reason="Source record already has a primary canonical link.",
                )
            )
            continue

        if dry_run:
            matched.append(
                _item_for_candidate(
                    definition,
                    "matched",
                    candidate,
                    reason="Dry run: candidate would be promoted.",
                    aliases=definition.aliases,
                )
            )
            continue

        promotion = promote_raw_source_record_to_canonical(
            candidate.raw_record.id,
            canonical_name=definition.display_name,
            aliases=definition.aliases,
        )
        matched.append(
            _item_for_candidate(
                definition,
                "matched",
                candidate,
                canonical_food_id=promotion.canonical_food.id,
                canonical_display_name=promotion.canonical_food.display_name,
                reason="Promoted from starter-set candidate.",
                aliases=tuple(alias.alias for alias in promotion.aliases),
                nutrients_synced=tuple(
                    nutrient.nutrient_name for nutrient in promotion.nutrients
                ),
            )
        )

    return StarterSetPromotionReport(
        dry_run=dry_run,
        definition_count=len(STARTER_FOOD_DEFINITIONS),
        processed_count=len(definitions),
        matched=matched,
        skipped_missing=skipped_missing,
        skipped_ambiguous=skipped_ambiguous,
        skipped_raw_only=skipped_raw_only,
        already_promoted=already_promoted,
    )
