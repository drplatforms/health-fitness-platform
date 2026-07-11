# ruff: noqa: E402
"""Inspect USDA raw source and FDC CSV coverage for catalog promotion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database
from services.food_catalog_inventory_service import (
    build_food_catalog_inventory_report,
)
from services.usda_food_data_import_service import GENERIC_FDC_DATA_TYPES


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect raw USDA source rows, canonical food counts, and optional "
            "FoodData Central CSV source coverage without mutating the database."
        )
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Required SQLite path to inspect.",
    )
    parser.add_argument(
        "--fdc-dir",
        default=None,
        help="Optional extracted FoodData Central CSV directory to inspect.",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional path for a JSON inventory report.",
    )
    parser.add_argument(
        "--include-data-types",
        default=None,
        help=(
            "Accepted for command-menu symmetry. Inventory reports all data types "
            "and does not filter database rows."
        ),
    )
    return parser


def _write_report(report_path: str | None, payload: dict[str, object]) -> None:
    if report_path is None:
        return
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    database.DB_PATH = Path(args.db_path).resolve()

    report = build_food_catalog_inventory_report(
        database_path=str(database.DB_PATH),
        fdc_dir=args.fdc_dir,
    )
    payload = report.to_dict()
    _write_report(args.report_path, payload)

    print("USDA food catalog source inventory complete.")
    print(f"Database: {database.DB_PATH}")
    print(f"Raw source rows: {report.macro_coverage['total']}")
    for data_type in GENERIC_FDC_DATA_TYPES:
        print(
            f"Raw rows [{data_type}]: {report.raw_count_by_data_type.get(data_type, 0)}"
        )
    print(f"Canonical foods: {report.canonical_food_count}")
    print(f"Canonical source links: {report.canonical_source_link_count}")
    if args.fdc_dir:
        print(f"FDC directory: {Path(args.fdc_dir).resolve()}")
        for data_type in GENERIC_FDC_DATA_TYPES:
            print(
                f"FDC rows [{data_type}]: "
                f"{report.fdc_food_count_by_data_type.get(data_type, 0)}"
            )
    for note in report.notes:
        print(f"Note: {note}")
    if args.report_path:
        print(f"Report: {Path(args.report_path).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
