from __future__ import annotations

import csv
import json
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


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _optional_text(value: object) -> str | None:
    normalized = _normalize_text(value)
    return normalized or None


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


def _validate_required_columns(fieldnames: list[str]) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(fieldnames))
    if missing:
        raise ValueError(
            "USDA input is missing required columns: " + ", ".join(missing) + "."
        )


def _build_import_batch(input_path: Path, import_batch: str | None) -> str:
    if import_batch and import_batch.strip():
        return import_batch.strip()
    return input_path.stem


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


def _build_source_payload(
    row: UsdaFoodImportRow, import_batch: str
) -> dict[str, object]:
    return {
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


def import_usda_food_csv(
    input_path: str | Path,
    *,
    import_batch: str | None = None,
    source_name: str = USDA_SOURCE_NAME,
) -> UsdaFoodImportSummary:
    source_path = Path(input_path)
    if not source_path.exists():
        raise ValueError(f"USDA input file not found: {source_path}")

    fieldnames, raw_rows = _load_csv_rows(source_path)
    _validate_required_columns(fieldnames)

    parsed_rows: list[UsdaFoodImportRow] = []
    seen_fdc_ids: set[int] = set()
    for row_number, raw_row in enumerate(raw_rows, start=2):
        parsed = _parse_row(raw_row, row_number)
        if parsed.fdc_id in seen_fdc_ids:
            raise ValueError(
                f"Row {row_number}: duplicate fdc_id {parsed.fdc_id} found in input."
            )
        seen_fdc_ids.add(parsed.fdc_id)
        parsed_rows.append(parsed)

    resolved_batch = _build_import_batch(source_path, import_batch)
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    inserted_count = 0
    updated_count = 0

    for row in parsed_rows:
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
                resolved_batch,
                json.dumps(_build_source_payload(row, resolved_batch), sort_keys=True),
                USDA_LICENSE,
                f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{row.fdc_id}",
            ),
        )

        if existing:
            updated_count += 1
        else:
            inserted_count += 1

    conn.commit()
    conn.close()

    return UsdaFoodImportSummary(
        input_path=str(source_path),
        database_path=str(database.DB_PATH),
        source_name=source_name,
        import_batch=resolved_batch,
        total_rows=len(parsed_rows),
        inserted_count=inserted_count,
        updated_count=updated_count,
    )
