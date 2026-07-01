from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_provider_preview_payload_service import (  # noqa: E402
    build_daily_coach_provider_preview_raw_data_payload_for_user,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Developer-only Daily Coach provider-preview raw data payload tool. "
            "Prints JSON to terminal and does not call providers or persist output."
        )
    )
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--target-date", default=None)
    args = parser.parse_args(argv)

    payload = build_daily_coach_provider_preview_raw_data_payload_for_user(
        user_id=args.user_id,
        target_date=args.target_date,
    )
    print(json.dumps(payload.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
