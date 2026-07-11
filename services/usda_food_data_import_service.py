from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import database
from database import get_connection
from models.usda_food_data_models import UsdaFoodImportRow, UsdaFoodImportSummary
from services.food_normalization_service import ensure_food_normalization_tables

USDA_SOURCE_NAME = "USDA FoodData Central"
USDA_LICENSE = "Public Domain"
USDA_DOWNLOAD_URL = "https://fdc.nal.usda.gov/download-datasets/"

REQUIRED_COLUMNS = {
    "fdc_id",
    "description",
    "data_type",
    "calories_per_100g",
    "protein_g_per_100g",
    "carbs_g_per_100g",
    "fat_g_per_100g",
}

FDC_REQUIRED_FILES = {
    "food": "food.csv",
    "food_nutrient": "food_nutrient.csv",
    "nutrient": "nutrient.csv",
}

FDC_FOOD_REQUIRED_COLUMNS = {
    "fdc_id",
    "description",
    "data_type",
}

FDC_FOOD_NUTRIENT_REQUIRED_COLUMNS = {
    "fdc_id",
    "nutrient_id",
    "amount",
}

FDC_NUTRIENT_REQUIRED_COLUMNS = {
    "id",
    "name",
}

FDC_FOOD_CATEGORY_REQUIRED_COLUMNS = {
    "id",
    "description",
}

FDC_SURVEY_FNDDS_REQUIRED_COLUMNS = {
    "fdc_id",
    "food_code",
    "wweia_category_number",
}

FDC_WWEIA_CATEGORY_CODE_COLUMNS = (
    "wweia_food_category_code",
    "wweia_food_category",
)

FDC_WWEIA_CATEGORY_DESCRIPTION_COLUMN = "wweia_food_category_description"

MACRO_FIELD_BY_KEY = {
    "calories": "calories_per_100g",
    "protein": "protein_g_per_100g",
    "carbs": "carbs_g_per_100g",
    "fat": "fat_g_per_100g",
}

GENERIC_FDC_DATA_TYPES = (
    "foundation_food",
    "sr_legacy_food",
    "survey_fndds_food",
)

DEFAULT_FDC_INCLUDE_DATA_TYPES = GENERIC_FDC_DATA_TYPES

FDC_DATA_TYPE_ALIASES = {
    "foundation_food": "foundation_food",
    "foundation_foods": "foundation_food",
    "sr_legacy": "sr_legacy_food",
    "sr_legacy_food": "sr_legacy_food",
    "survey_fndds": "survey_fndds_food",
    "survey_fndds_food": "survey_fndds_food",
    "survey_foods_fndds": "survey_fndds_food",
    "fndds": "survey_fndds_food",
    "branded": "branded_food",
    "branded_food": "branded_food",
    "experimental": "experimental_food",
    "experimental_food": "experimental_food",
}


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _optional_text(value: object) -> str | None:
    normalized = _normalize_text(value)
    return normalized or None


def _required_text(value: object, field_name: str, row_number: int) -> str:
    text = _normalize_text(value)
    if not text:
        raise ValueError(f"Row {row_number}: {field_name} is required.")
    return text


def _required_float(value: object, field_name: str, row_number: int) -> float:
    text = _normalize_text(value)
    if not text:
        raise ValueError(f"Row {row_number}: {field_name} is required.")
    try:
        parsed = float(text)
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: {field_name} must be numeric.") from exc
    if parsed < 0:
        raise ValueError(f"Row {row_number}: {field_name} must be non-negative.")
    return parsed


def _required_numeric_float(value: object, field_name: str, row_number: int) -> float:
    text = _normalize_text(value)
    if not text:
        raise ValueError(f"Row {row_number}: {field_name} is required.")
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: {field_name} must be numeric.") from exc


def _optional_float(value: object, field_name: str, row_number: int) -> float | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: {field_name} must be numeric.") from exc
    if parsed < 0:
        raise ValueError(f"Row {row_number}: {field_name} must be non-negative.")
    return parsed


def _required_int(value: object, field_name: str, row_number: int) -> int:
    text = _normalize_text(value)
    if not text:
        raise ValueError(f"Row {row_number}: {field_name} is required.")
    try:
        parsed = int(text)
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: {field_name} must be an integer.") from exc
    if parsed <= 0:
        raise ValueError(f"Row {row_number}: {field_name} must be positive.")
    return parsed


def _load_csv_rows(input_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("USDA input is missing a header row.")
        rows = [dict(row) for row in reader]
    return list(reader.fieldnames), rows


def _validate_required_columns(
    fieldnames: list[str],
    required_columns: set[str],
    input_label: str,
) -> None:
    missing = sorted(required_columns - set(fieldnames))
    if missing:
        raise ValueError(
            f"{input_label} is missing required columns: " + ", ".join(missing) + "."
        )


def _build_import_batch(input_path: Path, import_batch: str | None) -> str:
    if import_batch and import_batch.strip():
        return import_batch.strip()
    return input_path.stem


def _resolve_limit(limit: int | None) -> int | None:
    if limit is None:
        return None
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")
    return limit


def normalize_fdc_data_type_key(value: object) -> str:
    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        _normalize_text(value).casefold(),
    ).strip("_")
    return FDC_DATA_TYPE_ALIASES.get(normalized, normalized)


def _resolve_include_data_types(
    include_data_types: list[str] | tuple[str, ...] | None,
) -> tuple[str, ...]:
    if include_data_types is None:
        return DEFAULT_FDC_INCLUDE_DATA_TYPES

    normalized_data_types = tuple(
        normalized
        for value in include_data_types
        if (normalized := normalize_fdc_data_type_key(value))
    )
    if not normalized_data_types:
        raise ValueError("include_data_types must contain at least one data type.")
    return normalized_data_types


def _parse_row(raw_row: dict[str, str], row_number: int) -> UsdaFoodImportRow:
    description = _normalize_text(raw_row.get("description"))
    data_type = _normalize_text(raw_row.get("data_type"))
    if not description:
        raise ValueError(f"Row {row_number}: description is required.")
    if not data_type:
        raise ValueError(f"Row {row_number}: data_type is required.")

    return UsdaFoodImportRow(
        fdc_id=_required_int(raw_row.get("fdc_id"), "fdc_id", row_number),
        description=description,
        data_type=data_type,
        calories_per_100g=_required_float(
            raw_row.get("calories_per_100g"),
            "calories_per_100g",
            row_number,
        ),
        protein_g_per_100g=_required_float(
            raw_row.get("protein_g_per_100g"),
            "protein_g_per_100g",
            row_number,
        ),
        carbs_g_per_100g=_required_float(
            raw_row.get("carbs_g_per_100g"),
            "carbs_g_per_100g",
            row_number,
        ),
        fat_g_per_100g=_required_float(
            raw_row.get("fat_g_per_100g"),
            "fat_g_per_100g",
            row_number,
        ),
        brand_owner=_optional_text(raw_row.get("brand_owner")),
        gtin_upc=_optional_text(raw_row.get("gtin_upc")),
        serving_size=_optional_float(
            raw_row.get("serving_size"),
            "serving_size",
            row_number,
        ),
        serving_size_unit=_optional_text(raw_row.get("serving_size_unit")),
        food_category=_optional_text(raw_row.get("food_category")),
    )


def _first_non_empty(*values: object) -> str | None:
    for value in values:
        normalized = _optional_text(value)
        if normalized:
            return normalized
    return None


def _resolve_fdc_paths(fdc_dir: Path) -> dict[str, Path]:
    if not fdc_dir.exists() or not fdc_dir.is_dir():
        raise ValueError(f"USDA FDC directory not found: {fdc_dir}")

    resolved_paths: dict[str, Path] = {}
    missing_files: list[str] = []
    for key, filename in FDC_REQUIRED_FILES.items():
        path = fdc_dir / filename
        if not path.exists():
            missing_files.append(filename)
        else:
            resolved_paths[key] = path

    if missing_files:
        raise ValueError(
            "USDA FDC directory is missing required files: "
            + ", ".join(sorted(missing_files))
            + "."
        )

    branded_path = fdc_dir / "branded_food.csv"
    if branded_path.exists():
        resolved_paths["branded_food"] = branded_path

    food_category_path = fdc_dir / "food_category.csv"
    if food_category_path.exists():
        resolved_paths["food_category"] = food_category_path

    survey_fndds_path = fdc_dir / "survey_fndds_food.csv"
    if survey_fndds_path.exists():
        resolved_paths["survey_fndds_food"] = survey_fndds_path

    wweia_category_path = fdc_dir / "wweia_food_category.csv"
    if wweia_category_path.exists():
        resolved_paths["wweia_food_category"] = wweia_category_path

    return resolved_paths


def _normalize_nutrient_name(value: object) -> str:
    return _normalize_text(value).casefold()


def _macro_key_for_nutrient(raw_row: dict[str, str]) -> str | None:
    nutrient_name = _normalize_nutrient_name(raw_row.get("name"))
    unit_name = _normalize_nutrient_name(raw_row.get("unit_name"))

    if nutrient_name == "energy" and unit_name == "kcal":
        return "calories"
    if nutrient_name == "protein":
        return "protein"
    if nutrient_name == "carbohydrate, by difference":
        return "carbs"
    if nutrient_name == "total lipid (fat)":
        return "fat"
    return None


def _load_macro_nutrient_ids(nutrient_path: Path) -> dict[int, str]:
    fieldnames, raw_rows = _load_csv_rows(nutrient_path)
    _validate_required_columns(
        fieldnames,
        FDC_NUTRIENT_REQUIRED_COLUMNS,
        "USDA nutrient.csv",
    )

    macro_ids: dict[int, str] = {}
    matched_macro_keys: set[str] = set()
    for row_number, raw_row in enumerate(raw_rows, start=2):
        macro_key = _macro_key_for_nutrient(raw_row)
        if not macro_key:
            continue
        nutrient_id = _required_int(raw_row.get("id"), "id", row_number)
        _register_macro_nutrient_identifier(
            macro_ids,
            nutrient_id,
            macro_key,
            "id",
            row_number,
        )
        nutrient_nbr = _optional_text(raw_row.get("nutrient_nbr"))
        if nutrient_nbr is not None:
            _register_macro_nutrient_identifier(
                macro_ids,
                _required_int(nutrient_nbr, "nutrient_nbr", row_number),
                macro_key,
                "nutrient_nbr",
                row_number,
            )
        matched_macro_keys.add(macro_key)

    missing_macros = sorted(set(MACRO_FIELD_BY_KEY) - matched_macro_keys)
    if missing_macros:
        raise ValueError(
            "USDA nutrient.csv is missing macro nutrient definitions for: "
            + ", ".join(missing_macros)
            + "."
        )

    return macro_ids


def _register_macro_nutrient_identifier(
    macro_ids: dict[int, str],
    nutrient_identifier: int,
    macro_key: str,
    field_name: str,
    row_number: int,
) -> None:
    existing_macro_key = macro_ids.get(nutrient_identifier)
    if existing_macro_key is not None and existing_macro_key != macro_key:
        raise ValueError(
            f"Row {row_number}: {field_name} {nutrient_identifier} maps to both "
            f"{existing_macro_key} and {macro_key}."
        )
    macro_ids[nutrient_identifier] = macro_key


def _load_branded_food_rows(
    branded_food_path: Path | None,
    *,
    selected_fdc_ids: set[int],
) -> dict[int, dict[str, str]]:
    if branded_food_path is None:
        return {}

    rows_by_fdc_id: dict[int, dict[str, str]] = {}
    with branded_food_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("USDA branded_food.csv is missing a header row.")
        _validate_required_columns(
            list(reader.fieldnames),
            {"fdc_id"},
            "USDA branded_food.csv",
        )
        for row_number, raw_row in enumerate(reader, start=2):
            fdc_id = _required_int(raw_row.get("fdc_id"), "fdc_id", row_number)
            if fdc_id not in selected_fdc_ids:
                continue
            if fdc_id in rows_by_fdc_id:
                raise ValueError(
                    f"Row {row_number}: duplicate fdc_id {fdc_id} found in "
                    "branded_food.csv."
                )
            rows_by_fdc_id[fdc_id] = dict(raw_row)
    return rows_by_fdc_id


def _load_food_category_rows(food_category_path: Path | None) -> dict[int, str]:
    if food_category_path is None:
        return {}

    fieldnames, raw_rows = _load_csv_rows(food_category_path)
    _validate_required_columns(
        fieldnames,
        FDC_FOOD_CATEGORY_REQUIRED_COLUMNS,
        "USDA food_category.csv",
    )

    category_by_id: dict[int, str] = {}
    for row_number, raw_row in enumerate(raw_rows, start=2):
        category_id = _required_int(raw_row.get("id"), "id", row_number)
        description = _normalize_text(raw_row.get("description"))
        if not description:
            raise ValueError(f"Row {row_number}: description is required.")
        category_by_id[category_id] = description
    return category_by_id


def _load_wweia_category_rows(
    wweia_category_path: Path | None,
) -> dict[str, dict[str, str]]:
    if wweia_category_path is None:
        return {}

    fieldnames, raw_rows = _load_csv_rows(wweia_category_path)
    _validate_required_columns(
        fieldnames,
        {FDC_WWEIA_CATEGORY_DESCRIPTION_COLUMN},
        "USDA wweia_food_category.csv",
    )
    if not any(column in fieldnames for column in FDC_WWEIA_CATEGORY_CODE_COLUMNS):
        accepted_columns = ", ".join(FDC_WWEIA_CATEGORY_CODE_COLUMNS)
        raise ValueError(
            "USDA wweia_food_category.csv is missing a WWEIA category code "
            f"column. Expected one of: {accepted_columns}."
        )

    category_by_code: dict[str, dict[str, str]] = {}
    for row_number, raw_row in enumerate(raw_rows, start=2):
        code = _resolve_wweia_category_code(raw_row, row_number)
        description = _required_text(
            raw_row.get(FDC_WWEIA_CATEGORY_DESCRIPTION_COLUMN),
            FDC_WWEIA_CATEGORY_DESCRIPTION_COLUMN,
            row_number,
        )
        if code in category_by_code:
            raise ValueError(f"Row {row_number}: duplicate WWEIA category code {code}.")
        category_by_code[code] = {
            "wweia_food_category_code": code,
            "wweia_food_category_description": description,
        }
    return category_by_code


def _resolve_wweia_category_code(raw_row: dict[str, str], row_number: int) -> str:
    documented_code = _optional_text(raw_row.get("wweia_food_category_code"))
    current_release_code = _optional_text(raw_row.get("wweia_food_category"))

    if (
        documented_code
        and current_release_code
        and documented_code != current_release_code
    ):
        raise ValueError(
            f"Row {row_number}: conflicting WWEIA category code values for "
            "wweia_food_category_code and wweia_food_category."
        )

    return _required_text(
        documented_code or current_release_code,
        "wweia_food_category_code",
        row_number,
    )


def _load_survey_fndds_rows(
    survey_fndds_path: Path | None,
    *,
    selected_fdc_ids: set[int],
    category_by_code: dict[str, dict[str, str]],
) -> dict[int, dict[str, str]]:
    if survey_fndds_path is None:
        return {}

    survey_by_fdc_id: dict[int, dict[str, str]] = {}
    with survey_fndds_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("USDA survey_fndds_food.csv is missing a header row.")
        _validate_required_columns(
            list(reader.fieldnames),
            FDC_SURVEY_FNDDS_REQUIRED_COLUMNS,
            "USDA survey_fndds_food.csv",
        )
        for row_number, raw_row in enumerate(reader, start=2):
            fdc_id = _required_int(raw_row.get("fdc_id"), "fdc_id", row_number)
            if fdc_id not in selected_fdc_ids:
                continue
            if fdc_id in survey_by_fdc_id:
                raise ValueError(
                    f"Row {row_number}: duplicate fdc_id {fdc_id} found in "
                    "survey_fndds_food.csv."
                )

            food_code = _required_text(
                raw_row.get("food_code"), "food_code", row_number
            )
            category_number = _required_text(
                raw_row.get("wweia_category_number"),
                "wweia_category_number",
                row_number,
            )
            category = category_by_code.get(category_number, {})
            survey_by_fdc_id[fdc_id] = {
                "food_code": food_code,
                "wweia_category_number": category_number,
                **category,
            }
    return survey_by_fdc_id


def _build_food_row_index(
    raw_rows: list[dict[str, str]],
    *,
    limit: int | None,
) -> list[tuple[int, int, dict[str, str]]]:
    indexed_rows: list[tuple[int, int, dict[str, str]]] = []
    seen_fdc_ids: set[int] = set()
    selected_rows = raw_rows[:limit] if limit is not None else raw_rows
    for row_number, raw_row in enumerate(selected_rows, start=2):
        fdc_id = _required_int(raw_row.get("fdc_id"), "fdc_id", row_number)
        if fdc_id in seen_fdc_ids:
            raise ValueError(
                f"Row {row_number}: duplicate fdc_id {fdc_id} found in input."
            )
        seen_fdc_ids.add(fdc_id)
        indexed_rows.append((row_number, fdc_id, raw_row))
    return indexed_rows


def _stream_fdc_food_row_index(
    food_path: Path,
    *,
    include_data_types: tuple[str, ...],
    limit: int | None,
) -> list[tuple[int, int, str, dict[str, str]]]:
    indexed_rows: list[tuple[int, int, str, dict[str, str]]] = []
    seen_fdc_ids: set[int] = set()
    included_data_type_keys = set(include_data_types)

    with food_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("USDA food.csv is missing a header row.")
        _validate_required_columns(
            list(reader.fieldnames),
            FDC_FOOD_REQUIRED_COLUMNS,
            "USDA food.csv",
        )

        for row_number, raw_row in enumerate(reader, start=2):
            data_type_key = normalize_fdc_data_type_key(raw_row.get("data_type"))
            if data_type_key not in included_data_type_keys:
                continue

            fdc_id = _required_int(raw_row.get("fdc_id"), "fdc_id", row_number)
            if fdc_id in seen_fdc_ids:
                raise ValueError(
                    f"Row {row_number}: duplicate fdc_id {fdc_id} found in input."
                )

            seen_fdc_ids.add(fdc_id)
            indexed_rows.append((row_number, fdc_id, data_type_key, dict(raw_row)))
            if limit is not None and len(indexed_rows) >= limit:
                break

    return indexed_rows


def _load_macro_amounts_by_fdc_id(
    food_nutrient_path: Path,
    *,
    selected_fdc_ids: set[int],
    macro_nutrient_ids: dict[int, str],
) -> dict[int, dict[str, float]]:
    amounts_by_fdc_id: dict[int, dict[str, float]] = defaultdict(dict)
    with food_nutrient_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("USDA food_nutrient.csv is missing a header row.")
        _validate_required_columns(
            list(reader.fieldnames),
            FDC_FOOD_NUTRIENT_REQUIRED_COLUMNS,
            "USDA food_nutrient.csv",
        )
        for row_number, raw_row in enumerate(reader, start=2):
            fdc_id = _required_int(raw_row.get("fdc_id"), "fdc_id", row_number)
            if fdc_id not in selected_fdc_ids:
                continue
            nutrient_id = _required_int(
                raw_row.get("nutrient_id"), "nutrient_id", row_number
            )
            macro_key = macro_nutrient_ids.get(nutrient_id)
            if not macro_key:
                continue
            amount = _required_numeric_float(
                raw_row.get("amount"), "amount", row_number
            )
            if amount < 0:
                continue
            existing_amount = amounts_by_fdc_id[fdc_id].get(macro_key)
            if existing_amount is None:
                amounts_by_fdc_id[fdc_id][macro_key] = amount
            else:
                amounts_by_fdc_id[fdc_id][macro_key] = existing_amount + amount

    return dict(amounts_by_fdc_id)


def _parse_fdc_directory_row(
    raw_food_row: dict[str, str],
    normalized_data_type: str,
    branded_row: dict[str, str] | None,
    category_by_id: dict[int, str],
    survey_fndds_row: dict[str, str] | None,
    macro_amounts: dict[str, float],
    row_number: int,
) -> UsdaFoodImportRow:
    description = _normalize_text(raw_food_row.get("description"))
    source_data_type = _normalize_text(raw_food_row.get("data_type"))
    if not description:
        raise ValueError(f"Row {row_number}: description is required.")
    if not source_data_type:
        raise ValueError(f"Row {row_number}: data_type is required.")

    branded_values = branded_row or {}
    survey_values = survey_fndds_row or {}
    category_from_id = None
    category_id_text = _normalize_text(raw_food_row.get("food_category_id"))
    if normalized_data_type != "survey_fndds_food" and category_id_text:
        category_id = _required_int(
            raw_food_row.get("food_category_id"),
            "food_category_id",
            row_number,
        )
        category_from_id = category_by_id.get(category_id)

    return UsdaFoodImportRow(
        fdc_id=_required_int(raw_food_row.get("fdc_id"), "fdc_id", row_number),
        description=description,
        data_type=normalized_data_type,
        calories_per_100g=macro_amounts.get("calories"),
        protein_g_per_100g=macro_amounts.get("protein"),
        carbs_g_per_100g=macro_amounts.get("carbs"),
        fat_g_per_100g=macro_amounts.get("fat"),
        brand_owner=_first_non_empty(
            branded_values.get("brand_owner"),
            raw_food_row.get("brand_owner"),
        ),
        gtin_upc=_first_non_empty(
            branded_values.get("gtin_upc"),
            raw_food_row.get("gtin_upc"),
        ),
        serving_size=_optional_float(
            branded_values.get("serving_size", raw_food_row.get("serving_size")),
            "serving_size",
            row_number,
        ),
        serving_size_unit=_first_non_empty(
            branded_values.get("serving_size_unit"),
            raw_food_row.get("serving_size_unit"),
        ),
        food_category=_first_non_empty(
            survey_values.get("wweia_food_category_description")
            if normalized_data_type == "survey_fndds_food"
            else category_from_id,
            None
            if normalized_data_type == "survey_fndds_food"
            else raw_food_row.get("food_category"),
            None
            if normalized_data_type == "survey_fndds_food"
            else branded_values.get("food_category"),
            None
            if normalized_data_type == "survey_fndds_food"
            else branded_values.get("branded_food_category"),
        ),
        source_data_type=source_data_type,
        source_payload_metadata={
            key: value
            for key, value in survey_values.items()
            if key
            in {
                "food_code",
                "wweia_category_number",
                "wweia_food_category_code",
                "wweia_food_category_description",
            }
        },
    )


def _build_source_payload(
    row: UsdaFoodImportRow, import_batch: str
) -> dict[str, object]:
    payload: dict[str, object] = {
        "fdc_id": row.fdc_id,
        "description": row.description,
        "data_type": row.data_type,
        "brand_owner": row.brand_owner,
        "gtin_upc": row.gtin_upc,
        "serving_size": row.serving_size,
        "serving_size_unit": row.serving_size_unit,
        "food_category": row.food_category,
        "calories_per_100g": row.calories_per_100g,
        "protein_g_per_100g": row.protein_g_per_100g,
        "carbs_g_per_100g": row.carbs_g_per_100g,
        "fat_g_per_100g": row.fat_g_per_100g,
        "import_batch": import_batch,
    }
    if row.source_data_type is not None:
        payload["source_data_type"] = row.source_data_type
        payload["normalized_data_type"] = row.data_type
    payload.update(row.source_payload_metadata)
    return payload


def _upsert_import_rows(
    rows: list[UsdaFoodImportRow],
    *,
    import_batch: str,
    source_name: str,
    source_path: Path,
) -> UsdaFoodImportSummary:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    inserted_count = 0
    updated_count = 0

    try:
        for row in rows:
            cursor.execute(
                """
                SELECT id
                FROM raw_food_source_records
                WHERE source_name = ? AND source_record_id = ?
                """,
                (source_name, str(row.fdc_id)),
            )
            existing = cursor.fetchone() is not None

            cursor.execute(
                """
                INSERT INTO raw_food_source_records (
                    source_name,
                    source_record_id,
                    raw_description,
                    brand_name,
                    food_category,
                    data_type,
                    gtin_upc,
                    serving_size,
                    serving_size_unit,
                    calories_per_100g,
                    protein_g_per_100g,
                    carbs_g_per_100g,
                    fat_g_per_100g,
                    import_batch,
                    source_payload_json,
                    license,
                    source_url,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(source_name, source_record_id) DO UPDATE SET
                    raw_description = excluded.raw_description,
                    brand_name = excluded.brand_name,
                    food_category = excluded.food_category,
                    data_type = excluded.data_type,
                    gtin_upc = excluded.gtin_upc,
                    serving_size = excluded.serving_size,
                    serving_size_unit = excluded.serving_size_unit,
                    calories_per_100g = excluded.calories_per_100g,
                    protein_g_per_100g = excluded.protein_g_per_100g,
                    carbs_g_per_100g = excluded.carbs_g_per_100g,
                    fat_g_per_100g = excluded.fat_g_per_100g,
                    import_batch = excluded.import_batch,
                    source_payload_json = excluded.source_payload_json,
                    license = excluded.license,
                    source_url = excluded.source_url,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    source_name,
                    str(row.fdc_id),
                    row.description,
                    row.brand_owner,
                    row.food_category,
                    row.data_type,
                    row.gtin_upc,
                    row.serving_size,
                    row.serving_size_unit,
                    row.calories_per_100g,
                    row.protein_g_per_100g,
                    row.carbs_g_per_100g,
                    row.fat_g_per_100g,
                    import_batch,
                    json.dumps(
                        _build_source_payload(row, import_batch), sort_keys=True
                    ),
                    USDA_LICENSE,
                    f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{row.fdc_id}",
                ),
            )

            if existing:
                updated_count += 1
            else:
                inserted_count += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return UsdaFoodImportSummary(
        input_path=str(source_path),
        database_path=str(database.DB_PATH),
        source_name=source_name,
        import_batch=import_batch,
        total_rows=len(rows),
        inserted_count=inserted_count,
        updated_count=updated_count,
        processed_count_by_data_type=dict(
            sorted(Counter(row.data_type for row in rows).items())
        ),
    )


def import_usda_food_csv(
    input_path: str | Path,
    *,
    import_batch: str | None = None,
    source_name: str = USDA_SOURCE_NAME,
    limit: int | None = None,
) -> UsdaFoodImportSummary:
    source_path = Path(input_path)
    if not source_path.exists():
        raise ValueError(f"USDA input file not found: {source_path}")

    fieldnames, raw_rows = _load_csv_rows(source_path)
    _validate_required_columns(fieldnames, REQUIRED_COLUMNS, "USDA input")

    parsed_rows: list[UsdaFoodImportRow] = []
    indexed_rows = _build_food_row_index(raw_rows, limit=_resolve_limit(limit))
    for row_number, _, raw_row in indexed_rows:
        parsed_rows.append(_parse_row(raw_row, row_number))

    resolved_batch = _build_import_batch(source_path, import_batch)
    return _upsert_import_rows(
        parsed_rows,
        import_batch=resolved_batch,
        source_name=source_name,
        source_path=source_path,
    )


def import_usda_food_fdc_directory(
    fdc_dir: str | Path,
    *,
    import_batch: str | None = None,
    source_name: str = USDA_SOURCE_NAME,
    limit: int | None = None,
    include_data_types: list[str] | tuple[str, ...] | None = None,
) -> UsdaFoodImportSummary:
    source_dir = Path(fdc_dir)
    resolved_paths = _resolve_fdc_paths(source_dir)
    resolved_limit = _resolve_limit(limit)
    resolved_include_data_types = _resolve_include_data_types(include_data_types)

    indexed_food_rows = _stream_fdc_food_row_index(
        resolved_paths["food"],
        include_data_types=resolved_include_data_types,
        limit=resolved_limit,
    )
    selected_fdc_ids = {fdc_id for _, fdc_id, _, _ in indexed_food_rows}
    macro_nutrient_ids = _load_macro_nutrient_ids(resolved_paths["nutrient"])
    macro_amounts_by_fdc_id = _load_macro_amounts_by_fdc_id(
        resolved_paths["food_nutrient"],
        selected_fdc_ids=selected_fdc_ids,
        macro_nutrient_ids=macro_nutrient_ids,
    )
    branded_rows = (
        _load_branded_food_rows(
            resolved_paths.get("branded_food"),
            selected_fdc_ids=selected_fdc_ids,
        )
        if "branded_food" in resolved_include_data_types
        else {}
    )
    category_by_id = _load_food_category_rows(resolved_paths.get("food_category"))
    selected_fndds_ids = {
        fdc_id
        for _, fdc_id, data_type, _ in indexed_food_rows
        if data_type == "survey_fndds_food"
    }
    if selected_fndds_ids and resolved_paths.get("survey_fndds_food") is not None:
        wweia_category_by_code = _load_wweia_category_rows(
            resolved_paths.get("wweia_food_category")
        )
        survey_fndds_rows = _load_survey_fndds_rows(
            resolved_paths.get("survey_fndds_food"),
            selected_fdc_ids=selected_fndds_ids,
            category_by_code=wweia_category_by_code,
        )
    else:
        survey_fndds_rows = {}

    parsed_rows = [
        _parse_fdc_directory_row(
            raw_food_row,
            normalized_data_type,
            branded_rows.get(fdc_id),
            category_by_id,
            survey_fndds_rows.get(fdc_id),
            macro_amounts_by_fdc_id.get(fdc_id, {}),
            row_number,
        )
        for row_number, fdc_id, normalized_data_type, raw_food_row in indexed_food_rows
    ]

    resolved_batch = _build_import_batch(source_dir, import_batch)
    return _upsert_import_rows(
        parsed_rows,
        import_batch=resolved_batch,
        source_name=source_name,
        source_path=source_dir,
    )
