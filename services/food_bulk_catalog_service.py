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
    curate_canonical_display_name,
    ensure_food_normalization_tables,
    normalize_food_name,
)
from services.usda_food_data_import_service import USDA_SOURCE_NAME

BulkCatalogStatus = Literal[
    "promoted",
    "already_promoted",
    "skipped_missing_macros",
    "skipped_unsafe_raw",
    "skipped_category",
    "skipped_duplicate_name",
    "skipped_ambiguous",
    "skipped_invalid",
]

ALLOWED_BULK_CATEGORIES = {
    "Vegetables and Vegetable Products",
    "Fruits and Fruit Juices",
    "Dairy and Egg Products",
    "Legumes and Legume Products",
    "Cereal Grains and Pasta",
    "Nut and Seed Products",
    "Fats and Oils",
    "Baked Products",
    "Soups, Sauces, and Gravies",
    "Spices and Herbs",
    "Sweets",
    "Beverages",
    "Poultry Products",
    "Beef Products",
    "Pork Products",
    "Finfish and Shellfish Products",
    "Sausages and Luncheon Meats",
    "Restaurant Foods",
    "Lamb, Veal, and Game Products",
}

SR_LEGACY_ALLOWED_BULK_CATEGORIES = {
    "Fruits and Fruit Juices",
    "Vegetables and Vegetable Products",
    "Legumes and Legume Products",
    "Cereal Grains and Pasta",
    "Dairy and Egg Products",
    "Nut and Seed Products",
    "Spices and Herbs",
}

DATA_TYPE_PRECEDENCE = {
    "foundation_food": 0,
    "sr_legacy_food": 1,
    "survey_fndds_food": 2,
}

MEAT_FOWL_FISH_CATEGORIES = {
    "Poultry Products",
    "Beef Products",
    "Pork Products",
    "Finfish and Shellfish Products",
    "Sausages and Luncheon Meats",
    "Lamb, Veal, and Game Products",
}

UNSAFE_SOURCE_TERMS = {
    "agricultural acquisition",
    "laboratory",
    "market acquisition",
    "moisture control only",
    "sample",
    "sub sample",
    "sub-sample",
    "test",
}
RAW_TERMS = {"raw", "uncooked"}
SAFE_PREPARED_TERMS = {
    "baked",
    "braised",
    "broiled",
    "canned",
    "cooked",
    "drained",
    "fried",
    "grilled",
    "pan broiled",
    "pan fried",
    "prepared",
    "restaurant",
    "roasted",
    "stewed",
}

SR_LEGACY_COMMERCIAL_TERMS = {
    "bolthouse farms",
    "breakstone s",
    "cheez whiz",
    "daily greens",
    "kraft",
    "nasoya",
    "ocean spray",
    "reddi wip",
    "silk",
    "velveeta",
    "vitasoy",
    "zespri",
}
USDA_DISTRIBUTION_PROGRAM_PHRASE = "includes foods for usda s food distribution program"

FOUNDATION_DISPLAY_NAME_OVERRIDES = {
    "cheese cottage lowfat 2 milkfat": "Low-fat cottage cheese",
    "cottage cheese full fat large or small curd": "Full-fat cottage cheese",
    "grape juice purple with added vitamin c from concentrate shelf stable": "Purple grape juice",
    "grape juice white with added vitamin c from concentrate shelf stable": "White grape juice",
    "grapefruit juice red not fortified not from concentrate refrigerated": "Red grapefruit juice",
    "grapefruit juice white canned or bottled unsweetened": "White grapefruit juice",
    "juice pomegranate from concentrate shelf stable": "Pomegranate juice",
    "juice prune shelf stable": "Prune juice",
    "juice tart cherry from concentrate shelf stable": "Tart cherry juice",
    "mango ataulfo peeled raw": "Ataulfo mango",
    "mango tommy atkins peeled raw": "Tommy Atkins mango",
    "plantains overripe raw": "Overripe plantains",
    "plantains ripe raw": "Ripe plantains",
    "plantains underripe raw": "Underripe plantains",
    "blackeye pea canned sodium added drained and rinsed": "Canned black-eyed peas",
    "blackeye pea dry": "Dry black-eyed peas",
    "peanut butter creamy": "Creamy peanut butter",
    "peanut butter smooth style with salt": "Salted smooth peanut butter",
    "cabbage bok choy raw": "Bok choy",
    "cabbage green raw": "Green cabbage",
    "cabbage napa leaf destemmed raw": "Napa cabbage",
    "cabbage red raw": "Red cabbage",
    "kale frozen cooked boiled drained without salt": "Cooked frozen kale",
    "kale raw": "Raw kale",
    "kiwifruit kiwi green peeled raw": "Peeled kiwifruit",
    "onions red raw": "Red onions",
    "onions white raw": "White onions",
    "onions yellow raw": "Yellow onions",
    "potatoes gold without skin raw": "Gold potatoes",
    "potatoes red without skin raw": "Red potatoes",
    "potatoes russet without skin raw": "Russet potatoes",
    "tomatoes canned red ripe diced": "Diced canned tomatoes",
    "tomatoes crushed canned": "Crushed tomatoes",
    "tomatoes whole canned solids and liquids with salt added": "Whole canned tomatoes",
}

SR_LEGACY_MEATLESS_BASE_NAMES = {
    "bacon",
    "bacon bits",
    "frankfurter",
    "luncheon slices",
    "meatballs",
    "sandwich spread",
    "sausage",
}


@dataclass(frozen=True)
class BulkCatalogItem:
    status: BulkCatalogStatus
    raw_food_source_record_id: int
    source_name: str
    source_record_id: str
    raw_description: str
    data_type: str | None
    food_category: str | None
    canonical_display_name: str | None = None
    canonical_food_id: int | None = None
    reason: str | None = None
    aliases: tuple[str, ...] = ()
    nutrients_synced: tuple[str, ...] = ()


@dataclass(frozen=True)
class BulkCatalogPromotionReport:
    dry_run: bool
    processed_count: int
    promoted: list[BulkCatalogItem] = field(default_factory=list)
    already_promoted: list[BulkCatalogItem] = field(default_factory=list)
    skipped_missing_macros: list[BulkCatalogItem] = field(default_factory=list)
    skipped_unsafe_raw: list[BulkCatalogItem] = field(default_factory=list)
    skipped_category: list[BulkCatalogItem] = field(default_factory=list)
    skipped_duplicate_name: list[BulkCatalogItem] = field(default_factory=list)
    skipped_ambiguous: list[BulkCatalogItem] = field(default_factory=list)
    skipped_invalid: list[BulkCatalogItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "dry_run": self.dry_run,
            "processed_count": self.processed_count,
            "promoted": [asdict(item) for item in self.promoted],
            "already_promoted": [asdict(item) for item in self.already_promoted],
            "skipped_missing_macros": [
                asdict(item) for item in self.skipped_missing_macros
            ],
            "skipped_unsafe_raw": [asdict(item) for item in self.skipped_unsafe_raw],
            "skipped_category": [asdict(item) for item in self.skipped_category],
            "skipped_duplicate_name": [
                asdict(item) for item in self.skipped_duplicate_name
            ],
            "skipped_ambiguous": [asdict(item) for item in self.skipped_ambiguous],
            "skipped_invalid": [asdict(item) for item in self.skipped_invalid],
            "summary": {
                "promoted": len(self.promoted),
                "already_promoted": len(self.already_promoted),
                "skipped_missing_macros": len(self.skipped_missing_macros),
                "skipped_unsafe_raw": len(self.skipped_unsafe_raw),
                "skipped_category": len(self.skipped_category),
                "skipped_duplicate_name": len(self.skipped_duplicate_name),
                "skipped_ambiguous": len(self.skipped_ambiguous),
                "skipped_invalid": len(self.skipped_invalid),
            },
        }


@dataclass(frozen=True)
class _BulkCandidate:
    raw_record: RawFoodSourceRecord
    canonical_display_name: str
    aliases: tuple[str, ...]


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


def _normalize_categories(categories: tuple[str, ...] | None) -> set[str]:
    return {
        " ".join(category.strip().split()).casefold()
        for category in categories or ()
        if category.strip()
    }


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


def _load_raw_records(
    *,
    source_name: str,
    include_data_types: tuple[str, ...],
    limit: int | None,
) -> list[RawFoodSourceRecord]:
    ensure_food_normalization_tables()

    placeholders = ",".join("?" for _ in include_data_types)
    query = f"""
        SELECT *
        FROM raw_food_source_records
        WHERE source_name = ?
          AND LOWER(COALESCE(data_type, '')) IN ({placeholders})
        ORDER BY LOWER(COALESCE(food_category, '')), LOWER(raw_description), id
    """
    params: list[object] = [source_name, *include_data_types]
    if limit is not None:
        if limit <= 0:
            raise ValueError("limit must be a positive integer.")
        query += " LIMIT ?"
        params.append(limit)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_raw_food_source_record(row) for row in rows]


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


def _canonical_food_id_for_name(display_name: str) -> int | None:
    ensure_food_normalization_tables()

    normalized_name = normalize_food_name(display_name)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id
        FROM canonical_foods
        WHERE normalized_name = ?
          AND food_type = 'generic'
        ORDER BY id
        LIMIT 1
        """,
        (normalized_name,),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return int(row["id"])


def _has_any_normalized_term(normalized_description: str, terms: set[str]) -> bool:
    return any(term in normalized_description for term in terms)


def _has_normalized_phrase(normalized_description: str, phrase: str) -> bool:
    return f" {phrase} " in f" {normalized_description} "


def _has_raw_term(raw_record: RawFoodSourceRecord) -> bool:
    tokens = set(normalize_food_name(raw_record.raw_description).split())
    return bool(tokens.intersection(RAW_TERMS))


def _has_safe_prepared_term(raw_record: RawFoodSourceRecord) -> bool:
    normalized_description = normalize_food_name(raw_record.raw_description)
    return _has_any_normalized_term(normalized_description, SAFE_PREPARED_TERMS)


def _is_allowed_category(
    raw_record: RawFoodSourceRecord,
    *,
    include_categories: set[str],
    exclude_categories: set[str],
) -> bool:
    category = " ".join((raw_record.food_category or "").strip().split())
    normalized_category = category.casefold()
    if not normalized_category:
        return False
    if exclude_categories and normalized_category in exclude_categories:
        return False
    if include_categories and normalized_category not in include_categories:
        return False
    if raw_record.data_type == "survey_fndds_food":
        return False
    if raw_record.data_type == "sr_legacy_food":
        return category in SR_LEGACY_ALLOWED_BULK_CATEGORIES
    return category in ALLOWED_BULK_CATEGORIES


def _is_invalid_source_row(raw_record: RawFoodSourceRecord) -> bool:
    normalized_description = normalize_food_name(raw_record.raw_description)
    normalized_data_type = normalize_food_name(raw_record.data_type or "")
    if USDA_DISTRIBUTION_PROGRAM_PHRASE in normalized_description:
        return True
    return _has_any_normalized_term(
        f"{normalized_description} {normalized_data_type}",
        {normalize_food_name(term) for term in UNSAFE_SOURCE_TERMS},
    )


def _is_sr_legacy_commercial_row(raw_record: RawFoodSourceRecord) -> bool:
    if raw_record.data_type != "sr_legacy_food":
        return False

    raw_description = raw_record.raw_description
    normalized_description = normalize_food_name(raw_description)
    if USDA_DISTRIBUTION_PROGRAM_PHRASE in normalized_description:
        return True
    if any(symbol in raw_description for symbol in ("™", "®")):
        return True
    if any(
        _has_normalized_phrase(normalized_description, term)
        for term in SR_LEGACY_COMMERCIAL_TERMS
    ):
        return True

    leading_words = raw_description.split(",", 1)[0].split()
    uppercase_words = [
        word
        for word in leading_words
        if any(character.isalpha() for character in word) and word.isupper()
    ]
    return len(uppercase_words) >= 2


def _is_unsafe_raw_meat_fowl_fish(raw_record: RawFoodSourceRecord) -> bool:
    if raw_record.food_category not in MEAT_FOWL_FISH_CATEGORIES:
        return False
    if _has_raw_term(raw_record):
        return True
    return not _has_safe_prepared_term(raw_record)


def _title_case_words(value: str) -> str:
    return " ".join(word.capitalize() for word in value.split())


def _first_phrase(raw_description: str) -> str:
    return raw_description.split(",", 1)[0].strip()


def _description_parts(raw_description: str) -> list[str]:
    return [
        normalize_food_name(part)
        for part in raw_description.split(",")
        if normalize_food_name(part)
    ]


def _has_token(normalized_value: str, token: str) -> bool:
    return token in set(normalized_value.split())


def _has_all_tokens(normalized_value: str, tokens: set[str]) -> bool:
    value_tokens = set(normalized_value.split())
    return tokens.issubset(value_tokens)


def _display_words(value: str) -> str:
    return _title_case_words(normalize_food_name(value))


def _macro_profile(raw_record: RawFoodSourceRecord) -> tuple[float | None, ...]:
    return (
        raw_record.calories_per_100g,
        raw_record.protein_g_per_100g,
        raw_record.carbs_g_per_100g,
        raw_record.fat_g_per_100g,
    )


def _bulk_display_name(raw_record: RawFoodSourceRecord) -> str:
    normalized = normalize_food_name(raw_record.raw_description)
    tokens = set(normalized.split())
    parts = _description_parts(raw_record.raw_description)
    first_part = parts[0] if parts else ""

    if raw_record.data_type == "foundation_food":
        if override := FOUNDATION_DISPLAY_NAME_OVERRIDES.get(normalized):
            return override
    if raw_record.data_type == "sr_legacy_food" and "meatless" in tokens:
        if first_part in SR_LEGACY_MEATLESS_BASE_NAMES:
            return f"Meatless {first_part}"
    if (
        raw_record.data_type == "sr_legacy_food"
        and normalized == "vermicelli made from soy"
    ):
        return "Soy vermicelli"

    if "hummus" in tokens:
        return "Hummus"
    if "tomatoes" in tokens and "grape" in tokens:
        return "Grape tomatoes"
    if "milk" in tokens and ("2" in tokens or "reduced" in tokens):
        return "2% milk"
    if "egg" in tokens and "whole" in tokens:
        return "Egg"
    if first_part == "rice" and "red" in tokens:
        if "raw" in tokens and "dry" in tokens:
            return "Raw dry red rice"
        return "Red rice"
    if first_part == "chicken" and "drumstick" in tokens and "braised" in tokens:
        return "Braised chicken drumstick"
    if first_part == "pork" and "bacon" in tokens and "cooked" in tokens:
        return "Cooked bacon"
    if first_part == "cookies" and "oatmeal" in tokens and "raisins" in tokens:
        return "Oatmeal raisin cookies"
    if "chickpeas" in tokens:
        if "canned" in tokens:
            return "Canned chickpeas"
        if "dry" in tokens:
            return "Dry chickpeas"
    if first_part == "seeds" and "pumpkin" in tokens and "raw" in tokens:
        return "Raw pumpkin seeds"
    if first_part == "seeds" and "sunflower" in tokens:
        if "raw" in tokens:
            return "Raw sunflower seeds"
        if {"dry", "roasted", "salt"}.issubset(tokens):
            return "Salted dry roasted sunflower seeds"
    if "anchovies" in tokens:
        if "canned" in tokens:
            return "Canned anchovies"
        return "Anchovies"
    if first_part == "oil":
        if "coconut" in tokens:
            return "Coconut oil"
        if "olive" in tokens:
            return "Olive oil"
    if first_part == "flour":
        if "almond" in tokens:
            return "Almond flour"
        if "coconut" in tokens:
            return "Coconut flour"
        if _has_all_tokens(normalized, {"whole", "wheat"}):
            return "Whole wheat flour"
        if "bread" in tokens:
            return "Bread flour"
        if "rice" in tokens and "brown" in tokens:
            return "Brown rice flour"
        if "rice" in tokens:
            return "Rice flour"
    if first_part == "cheese":
        for cheese_type in (
            "cheddar",
            "mozzarella",
            "parmesan",
            "feta",
            "swiss",
            "colby",
            "ricotta",
            "cottage",
        ):
            if cheese_type in tokens:
                return f"{_display_words(cheese_type)} cheese"
    if first_part == "rice":
        for rice_type in ("brown", "white", "black", "wild"):
            if rice_type in tokens:
                return f"{_display_words(rice_type)} rice"
    if first_part in {"oats", "oat"}:
        if "rolled" in tokens:
            return "Rolled oats"
        if "steel" in tokens and "cut" in tokens:
            return "Steel cut oats"
    if first_part in {"tomato", "tomatoes"}:
        if "paste" in tokens:
            return "Tomato paste"
        if "puree" in tokens:
            return "Tomato puree"
        if "sauce" in tokens:
            return "Tomato sauce"
        if "roma" in tokens:
            return "Roma tomato"
    if first_part == "butter":
        if "salted" in tokens and "unsalted" not in tokens:
            return "Salted butter"
        if "unsalted" in tokens:
            return "Unsalted butter"
    if first_part == "cream":
        if "heavy" in tokens:
            return "Heavy cream"
        if "sour" in tokens:
            return "Sour cream"
    if first_part == "bread":
        if _has_token(normalized, "white"):
            return "White bread"
        if _has_all_tokens(normalized, {"whole", "wheat"}):
            return "Whole wheat bread"
    if "tuna" in tokens and ("canned" in tokens or "water" in tokens):
        return "Tuna"
    if "chicken" in tokens and "breast" in tokens:
        return "Chicken breast"
    if "turkey" in tokens and "ground" in tokens:
        return "Ground turkey"
    if "beef" in tokens and "ground" in tokens:
        return "Ground beef"

    curated = curate_canonical_display_name(raw_record.raw_description, "generic")
    if curated != raw_record.raw_description:
        return curated

    first_phrase = _first_phrase(raw_record.raw_description)
    if first_phrase:
        return _title_case_words(normalize_food_name(first_phrase))
    return raw_record.raw_description.strip()


def _aliases_for_candidate(
    raw_record: RawFoodSourceRecord,
    canonical_display_name: str,
) -> tuple[str, ...]:
    aliases = [
        raw_record.raw_description,
        _first_phrase(raw_record.raw_description),
        canonical_display_name,
    ]
    if canonical_display_name == "2% milk":
        aliases.extend(["reduced fat milk", "two percent milk"])
    if canonical_display_name == "Olive oil":
        aliases.append("extra virgin olive oil")
    if canonical_display_name == "Canned anchovies":
        aliases.append("anchovies")
    if canonical_display_name == "Tuna":
        aliases.extend(["canned tuna", "tuna in water"])

    normalized_canonical = normalize_food_name(canonical_display_name)
    seen: set[str] = set()
    deduped: list[str] = []
    for alias in aliases:
        normalized_alias = normalize_food_name(alias)
        if not normalized_alias or normalized_alias == normalized_canonical:
            continue
        if normalized_alias in seen:
            continue
        seen.add(normalized_alias)
        deduped.append(" ".join(alias.strip().split()))
    return tuple(deduped)


def _item(
    raw_record: RawFoodSourceRecord,
    status: BulkCatalogStatus,
    *,
    canonical_display_name: str | None = None,
    canonical_food_id: int | None = None,
    reason: str | None = None,
    aliases: tuple[str, ...] = (),
    nutrients_synced: tuple[str, ...] = (),
) -> BulkCatalogItem:
    return BulkCatalogItem(
        status=status,
        raw_food_source_record_id=raw_record.id,
        source_name=raw_record.source_name,
        source_record_id=raw_record.source_record_id,
        raw_description=raw_record.raw_description,
        data_type=raw_record.data_type,
        food_category=raw_record.food_category,
        canonical_display_name=canonical_display_name,
        canonical_food_id=canonical_food_id,
        reason=reason,
        aliases=aliases,
        nutrients_synced=nutrients_synced,
    )


def promote_canonical_food_bulk_catalog(
    *,
    dry_run: bool = False,
    source_name: str = USDA_SOURCE_NAME,
    include_data_types: tuple[str, ...] | None = None,
    include_categories: tuple[str, ...] | None = None,
    exclude_categories: tuple[str, ...] | None = None,
    limit: int | None = None,
    max_promotions: int | None = None,
) -> BulkCatalogPromotionReport:
    ensure_food_normalization_tables()
    if max_promotions is not None and max_promotions <= 0:
        raise ValueError("max_promotions must be a positive integer.")

    raw_records = _load_raw_records(
        source_name=source_name,
        include_data_types=_normalize_data_types(include_data_types),
        limit=limit,
    )
    normalized_include_categories = _normalize_categories(include_categories)
    normalized_exclude_categories = _normalize_categories(exclude_categories)

    already_promoted: list[BulkCatalogItem] = []
    skipped_missing_macros: list[BulkCatalogItem] = []
    skipped_unsafe_raw: list[BulkCatalogItem] = []
    skipped_category: list[BulkCatalogItem] = []
    skipped_duplicate_name: list[BulkCatalogItem] = []
    skipped_ambiguous: list[BulkCatalogItem] = []
    skipped_invalid: list[BulkCatalogItem] = []
    candidates_by_name: dict[str, list[_BulkCandidate]] = {}

    for raw_record in raw_records:
        if not _has_macro_data(raw_record):
            skipped_missing_macros.append(
                _item(
                    raw_record,
                    "skipped_missing_macros",
                    reason="Source row has no macro nutrient values.",
                )
            )
            continue

        if _is_invalid_source_row(raw_record) or _is_sr_legacy_commercial_row(
            raw_record
        ):
            skipped_invalid.append(
                _item(
                    raw_record,
                    "skipped_invalid",
                    reason=(
                        "SR Legacy row contains an evidenced manufacturer, product-line, "
                        "or USDA distribution-program signal."
                        if _is_sr_legacy_commercial_row(raw_record)
                        else "Source row looks like review/test/acquisition data."
                    ),
                )
            )
            continue

        if not _is_allowed_category(
            raw_record,
            include_categories=normalized_include_categories,
            exclude_categories=normalized_exclude_categories,
        ):
            skipped_category.append(
                _item(
                    raw_record,
                    "skipped_category",
                    reason="Source row category is not enabled for v0 bulk promotion.",
                )
            )
            continue

        if _is_unsafe_raw_meat_fowl_fish(raw_record):
            skipped_unsafe_raw.append(
                _item(
                    raw_record,
                    "skipped_unsafe_raw",
                    reason="Raw or not-clearly-prepared meat/fowl/fish row skipped.",
                )
            )
            continue

        existing_linked_id = _existing_primary_canonical_food_id(raw_record.id)
        canonical_display_name = _bulk_display_name(raw_record)
        if existing_linked_id is not None:
            already_promoted.append(
                _item(
                    raw_record,
                    "already_promoted",
                    canonical_display_name=canonical_display_name,
                    canonical_food_id=existing_linked_id,
                    reason="Source row already has a primary canonical link.",
                )
            )
            continue

        if (
            raw_record.data_type == "sr_legacy_food"
            and "meatless" in normalize_food_name(raw_record.raw_description).split()
            and "meatless" not in normalize_food_name(canonical_display_name).split()
        ):
            skipped_invalid.append(
                _item(
                    raw_record,
                    "skipped_invalid",
                    canonical_display_name=canonical_display_name,
                    reason=(
                        "SR Legacy meatless row could not retain a clear Meatless "
                        "display-name qualifier."
                    ),
                )
            )
            continue

        if not canonical_display_name.strip():
            skipped_invalid.append(
                _item(
                    raw_record,
                    "skipped_invalid",
                    reason="Curated canonical display name was empty.",
                )
            )
            continue

        existing_named_id = _canonical_food_id_for_name(canonical_display_name)
        if existing_named_id is not None:
            skipped_duplicate_name.append(
                _item(
                    raw_record,
                    "skipped_duplicate_name",
                    canonical_display_name=canonical_display_name,
                    canonical_food_id=existing_named_id,
                    reason=(
                        "Canonical display name already exists without a primary "
                        "source link for this raw row."
                    ),
                )
            )
            continue

        normalized_name = normalize_food_name(canonical_display_name)
        candidates_by_name.setdefault(normalized_name, []).append(
            _BulkCandidate(
                raw_record=raw_record,
                canonical_display_name=canonical_display_name,
                aliases=_aliases_for_candidate(raw_record, canonical_display_name),
            )
        )

    ready_candidates: list[_BulkCandidate] = []
    for normalized_name in sorted(candidates_by_name):
        same_name_candidates = candidates_by_name[normalized_name]
        highest_precedence = min(
            DATA_TYPE_PRECEDENCE.get(candidate.raw_record.data_type or "", 99)
            for candidate in same_name_candidates
        )
        winning_candidates = [
            candidate
            for candidate in same_name_candidates
            if DATA_TYPE_PRECEDENCE.get(candidate.raw_record.data_type or "", 99)
            == highest_precedence
        ]
        winning_data_type = winning_candidates[0].raw_record.data_type or "unknown"
        for candidate in same_name_candidates:
            if candidate not in winning_candidates:
                skipped_duplicate_name.append(
                    _item(
                        candidate.raw_record,
                        "skipped_duplicate_name",
                        canonical_display_name=candidate.canonical_display_name,
                        reason=(
                            "Lower-precedence source row skipped because "
                            f"{winning_data_type} is selected for this candidate name."
                        ),
                    )
                )

        if len(winning_candidates) == 1:
            ready_candidates.extend(winning_candidates)
            continue

        macro_profiles = {
            _macro_profile(candidate.raw_record) for candidate in winning_candidates
        }
        if len(macro_profiles) == 1:
            selected = min(
                winning_candidates,
                key=lambda candidate: (
                    candidate.raw_record.source_name.casefold(),
                    candidate.raw_record.data_type or "",
                    candidate.raw_record.source_record_id,
                    normalize_food_name(candidate.raw_record.raw_description),
                    candidate.raw_record.id,
                ),
            )
            ready_candidates.append(selected)
            for candidate in winning_candidates:
                if candidate == selected:
                    continue
                skipped_duplicate_name.append(
                    _item(
                        candidate.raw_record,
                        "skipped_duplicate_name",
                        canonical_display_name=candidate.canonical_display_name,
                        reason=(
                            "An identical-profile representative was selected for this "
                            "canonical display name."
                        ),
                    )
                )
            continue

        for candidate in winning_candidates:
            skipped_duplicate_name.append(
                _item(
                    candidate.raw_record,
                    "skipped_duplicate_name",
                    canonical_display_name=candidate.canonical_display_name,
                    reason=(
                        "Materially different source rows share this canonical display "
                        "name and no targeted unique name is available."
                    ),
                )
            )

    promoted: list[BulkCatalogItem] = []
    for candidate in sorted(
        ready_candidates,
        key=lambda candidate: (
            DATA_TYPE_PRECEDENCE.get(candidate.raw_record.data_type or "", 99),
            normalize_food_name(candidate.canonical_display_name),
            candidate.raw_record.source_name.casefold(),
            candidate.raw_record.source_record_id,
            normalize_food_name(candidate.raw_record.raw_description),
            candidate.raw_record.id,
        ),
    ):
        if max_promotions is not None and len(promoted) >= max_promotions:
            skipped_ambiguous.append(
                _item(
                    candidate.raw_record,
                    "skipped_ambiguous",
                    canonical_display_name=candidate.canonical_display_name,
                    reason="Promotion cap reached before this candidate.",
                )
            )
            continue

        if dry_run:
            promoted.append(
                _item(
                    candidate.raw_record,
                    "promoted",
                    canonical_display_name=candidate.canonical_display_name,
                    reason="Dry run: candidate would be promoted.",
                    aliases=candidate.aliases,
                )
            )
            continue

        promotion = promote_raw_source_record_to_canonical(
            candidate.raw_record.id,
            canonical_name=candidate.canonical_display_name,
            aliases=candidate.aliases,
        )
        promoted.append(
            _item(
                candidate.raw_record,
                "promoted",
                canonical_display_name=promotion.canonical_food.display_name,
                canonical_food_id=promotion.canonical_food.id,
                reason="Promoted from bulk catalog candidate.",
                aliases=tuple(alias.alias for alias in promotion.aliases),
                nutrients_synced=tuple(
                    nutrient.nutrient_name for nutrient in promotion.nutrients
                ),
            )
        )

    return BulkCatalogPromotionReport(
        dry_run=dry_run,
        processed_count=len(raw_records),
        promoted=promoted,
        already_promoted=already_promoted,
        skipped_missing_macros=skipped_missing_macros,
        skipped_unsafe_raw=skipped_unsafe_raw,
        skipped_category=skipped_category,
        skipped_duplicate_name=skipped_duplicate_name,
        skipped_ambiguous=skipped_ambiguous,
        skipped_invalid=skipped_invalid,
    )
