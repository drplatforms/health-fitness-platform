# ruff: noqa: E402
"""Promote a deterministic starter set from existing raw food source records."""

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
from services.food_normalization_service import ensure_food_normalization_tables
from services.food_starter_set_definitions import STARTER_FOOD_CATEGORIES
from services.food_starter_set_service import promote_canonical_food_starter_set


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Promote high-confidence everyday canonical foods from existing raw "
            "food source records."
        )
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Required SQLite path override for a local review database.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the starter-set report without promoting canonical foods.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of starter definitions to process.",
    )
    parser.add_argument(
        "--include-categories",
        default=None,
        help=(
            "Optional comma-separated categories to process. Known categories: "
            + ", ".join(STARTER_FOOD_CATEGORIES)
            + "."
        ),
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional path for a JSON promotion report.",
    )
    return parser


def _parse_categories(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    categories = tuple(
        category.strip() for category in value.split(",") if category.strip()
    )
    return categories or None


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

    report = promote_canonical_food_starter_set(
        dry_run=args.dry_run,
        limit=args.limit,
        include_categories=_parse_categories(args.include_categories),
    )
    payload = report.to_dict()
    _write_report(args.report_path, payload)

    summary = payload["summary"]
    print("Canonical food starter-set promotion complete.")
    print(f"Database: {database.DB_PATH}")
    print(f"Dry run: {report.dry_run}")
    print(f"Definitions processed: {report.processed_count}")
    print(
        "Summary: "
        f"matched={summary['matched']}, "
        f"already_promoted={summary['already_promoted']}, "
        f"skipped_missing={summary['skipped_missing']}, "
        f"skipped_ambiguous={summary['skipped_ambiguous']}, "
        f"skipped_raw_only={summary['skipped_raw_only']}"
    )
    if args.report_path:
        print(f"Report: {Path(args.report_path).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
