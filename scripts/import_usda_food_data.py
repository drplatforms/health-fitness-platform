# ruff: noqa: E402
"""Import USDA-like food source rows into the local raw food source table."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database
from database import initialize_database
from services.usda_food_data_import_service import (
    import_usda_food_csv,
    import_usda_food_fdc_directory,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import either a simple USDA-style CSV file or an extracted USDA "
            "FoodData Central CSV directory into raw_food_source_records."
        )
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        help="Path to a local USDA-style CSV.",
    )
    input_group.add_argument(
        "--fdc-dir",
        help=(
            "Path to an extracted USDA FoodData Central directory containing "
            "food.csv, food_nutrient.csv, and nutrient.csv."
        ),
    )
    parser.add_argument(
        "--import-batch",
        default=None,
        help="Optional batch label. Defaults to the input filename stem.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Optional SQLite path override for a scratch or test database.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional positive row limit, mainly for local smoke imports.",
    )
    parser.add_argument(
        "--include-data-types",
        default=None,
        help=(
            "Optional comma-separated USDA food.csv data_type values for --fdc-dir "
            "imports. Defaults to foundation_food, sr_legacy_food, and "
            "survey_fndds_food."
        ),
    )
    return parser


def _parse_include_data_types(value: str | None) -> list[str] | None:
    if value is None:
        return None

    parsed_values = [item.strip() for item in value.split(",") if item.strip()]
    if not parsed_values:
        raise ValueError("--include-data-types must contain at least one value.")
    return parsed_values


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.db_path:
        database.DB_PATH = Path(args.db_path).resolve()
        database.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    initialize_database()
    if args.fdc_dir:
        summary = import_usda_food_fdc_directory(
            args.fdc_dir,
            import_batch=args.import_batch,
            limit=args.limit,
            include_data_types=_parse_include_data_types(args.include_data_types),
        )
    else:
        summary = import_usda_food_csv(
            args.input,
            import_batch=args.import_batch,
            limit=args.limit,
        )

    print("USDA food import complete.")
    print(f"Database: {summary.database_path}")
    print(f"Input: {summary.input_path}")
    print(f"Source: {summary.source_name}")
    print(f"Import batch: {summary.import_batch}")
    print(f"Rows processed: {summary.total_rows}")
    print(f"Rows inserted: {summary.inserted_count}")
    print(f"Rows updated: {summary.updated_count}")
    for data_type, count in summary.processed_count_by_data_type.items():
        print(f"Rows processed [{data_type}]: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
