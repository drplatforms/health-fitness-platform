# ruff: noqa: E402
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database
from database import initialize_database
from services.food_canonical_manifest_promotion_service import (
    execute_manifest,
    report_json,
    require_external_database_path,
)
from services.food_normalization_service import ensure_food_normalization_tables


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute a verified canonical-food manifest."
    )
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--manifest-path", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-item-count", type=int, required=True)
    parser.add_argument("--report-path", required=True)
    args = parser.parse_args()
    database.DB_PATH = require_external_database_path(args.db_path)
    initialize_database()
    ensure_food_normalization_tables()
    report = execute_manifest(
        args.manifest_path,
        expected_sha256=args.expected_sha256,
        expected_item_count=args.expected_item_count,
    )
    Path(args.report_path).write_text(report_json(report), encoding="utf-8")
    print(f"Manifest promotion complete: {report['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
