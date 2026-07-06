# ruff: noqa: E402
"""Promote one USDA raw food source record into the canonical food tables."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database
from database import initialize_database
from services.food_canonical_promotion_service import (
    promote_raw_source_record_to_canonical,
)
from services.food_normalization_service import ensure_food_normalization_tables


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Promote one USDA raw food source record into the canonical food tables."
        )
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Required SQLite path override for a scratch or review database.",
    )
    parser.add_argument(
        "--source-record-id",
        required=True,
        type=int,
        help="Internal raw_food_source_records.id value to promote.",
    )
    parser.add_argument(
        "--canonical-name",
        default=None,
        help="Optional canonical display name override. Defaults to raw_description.",
    )
    parser.add_argument(
        "--alias",
        action="append",
        default=None,
        help="Optional alias to add. Repeat for multiple aliases.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    database.DB_PATH = Path(args.db_path).resolve()
    database.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    initialize_database()
    ensure_food_normalization_tables()

    result = promote_raw_source_record_to_canonical(
        args.source_record_id,
        canonical_name=args.canonical_name,
        aliases=args.alias,
    )

    print("Raw USDA source promotion complete.")
    print(f"Database: {database.DB_PATH}")
    print(f"Raw source record id: {result.raw_source_record.id}")
    print(f"USDA source_record_id: {result.source_identity.source_record_id}")
    print(f"Canonical food id: {result.canonical_food.id}")
    print(f"Canonical display name: {result.canonical_food.display_name}")
    print(f"Canonical food type: {result.canonical_food.food_type}")
    print(f"Aliases stored: {len(result.aliases)}")
    print(f"Macro nutrients stored: {len(result.nutrients)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
