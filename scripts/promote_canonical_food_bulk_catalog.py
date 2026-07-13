# ruff: noqa: E402
"""Bulk-promote safe USDA generic raw rows into canonical foods."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database
from database import initialize_database
from services.food_bulk_catalog_service import promote_canonical_food_bulk_catalog
from services.food_normalization_service import ensure_food_normalization_tables
from services.usda_food_data_import_service import USDA_SOURCE_NAME


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Promote safe, practical USDA generic raw source rows into "
            "canonical foods with dry-run and JSON reporting support."
        )
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Required SQLite path for the source and canonical catalog.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report candidates without mutating canonical tables.",
    )
    parser.add_argument(
        "--source-name",
        default=USDA_SOURCE_NAME,
        help="Raw source name to scan. Defaults to USDA FoodData Central.",
    )
    parser.add_argument(
        "--include-data-types",
        default=None,
        help="Optional comma-separated raw data_type values. Defaults to foundation_food.",
    )
    parser.add_argument(
        "--include-categories",
        default=None,
        help="Optional comma-separated food_category values to include.",
    )
    parser.add_argument(
        "--exclude-categories",
        default=None,
        help="Optional comma-separated food_category values to exclude.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of raw source rows to scan.",
    )
    parser.add_argument(
        "--max-promotions",
        type=int,
        default=None,
        help="Optional maximum number of candidates to promote or dry-run as promoted.",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional path for a JSON promotion report.",
    )
    return parser


def _parse_csv_option(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    parsed = tuple(item.strip() for item in value.split(",") if item.strip())
    return parsed or None


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
    database.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    initialize_database()
    ensure_food_normalization_tables()

    report = promote_canonical_food_bulk_catalog(
        dry_run=args.dry_run,
        source_name=args.source_name,
        include_data_types=_parse_csv_option(args.include_data_types),
        include_categories=_parse_csv_option(args.include_categories),
        exclude_categories=_parse_csv_option(args.exclude_categories),
        limit=args.limit,
        max_promotions=args.max_promotions,
    )
    payload = report.to_dict()
    _write_report(args.report_path, payload)
    summary = payload["summary"]

    print("Canonical food bulk catalog promotion complete.")
    print(f"Database: {database.DB_PATH}")
    print(f"Dry run: {report.dry_run}")
    print(f"Raw rows processed: {report.processed_count}")
    print(
        "Summary: "
        f"promoted={summary['promoted']}, "
        f"already_promoted={summary['already_promoted']}, "
        f"skipped_missing_macros={summary['skipped_missing_macros']}, "
        f"skipped_unsafe_raw={summary['skipped_unsafe_raw']}, "
        f"skipped_category={summary['skipped_category']}, "
        f"skipped_duplicate_name={summary['skipped_duplicate_name']}, "
        f"skipped_ambiguous={summary['skipped_ambiguous']}, "
        f"skipped_invalid={summary['skipped_invalid']}"
    )
    if args.report_path:
        print(f"Report: {Path(args.report_path).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
