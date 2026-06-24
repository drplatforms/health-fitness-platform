from __future__ import annotations

import argparse
import dataclasses
import importlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _to_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _to_jsonable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            return str(value)
    return value


def _parse_user_ids(value: str) -> tuple[int, ...]:
    ids: list[int] = []
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "--users must be a comma-separated list of integers."
            ) from exc
    if not ids:
        raise argparse.ArgumentTypeError("--users must include at least one user id.")
    return tuple(ids)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify QA seed data counts and date bounds outside Streamlit."
    )
    parser.add_argument("--db-path", default=None, help="Optional SQLite DB path.")
    parser.add_argument(
        "--users",
        type=_parse_user_ids,
        default=None,
        help="Comma-separated QA user ids. Defaults to 101,102,103,104,105.",
    )
    parser.add_argument(
        "--preset",
        default=None,
        choices=(
            "latest_seeded_week",
            "previous_seeded_week",
            "recent_14_days",
            "recent_28_days",
            "full_expected_seed_window",
        ),
        help="Optional built-in date range preset.",
    )
    parser.add_argument("--start-date", default="2026-06-08")
    parser.add_argument("--end-date", default="2026-06-14")
    parser.add_argument(
        "--full-bounds",
        action="store_true",
        help="Accepted for readability; global bounds are always included.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = importlib.import_module("services.qa_seed_data_verification_service")

    start_date = args.start_date
    end_date = args.end_date
    if args.preset:
        start_date, end_date = service.RANGE_PRESETS[args.preset]

    try:
        report = service.verify_qa_seed_data(
            db_path=args.db_path,
            user_ids=args.users,
            start_date=start_date,
            end_date=end_date,
        )
    except service.QASeedVerificationError as exc:
        print(f"QA Seed Data Verification input error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(_to_jsonable(report), indent=2, sort_keys=True))
    else:
        print(service.render_qa_seed_verification_report(report))

    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
