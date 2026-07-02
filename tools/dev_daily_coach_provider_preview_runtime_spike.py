from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_provider_preview_payload_service import (  # noqa: E402
    build_daily_coach_provider_preview_raw_data_payload_for_user,
)
from services.daily_coach_provider_preview_runtime_service import (  # noqa: E402
    run_daily_coach_provider_preview_runtime_spike,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Developer-only Daily Coach provider preview runtime spike. "
            "Calls a local provider only when explicitly run from the terminal, "
            "prints raw model output, and does not persist anything."
        )
    )
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument(
        "--ollama-base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--print-payload", action="store_true")
    args = parser.parse_args(argv)

    payload = build_daily_coach_provider_preview_raw_data_payload_for_user(
        user_id=args.user_id,
        target_date=args.target_date,
    )
    if args.print_payload:
        print("=== RAW BACKEND PAYLOAD JSON ===")
        print(json.dumps(payload.to_dict(), indent=2, sort_keys=True))
        print()

    result = run_daily_coach_provider_preview_runtime_spike(
        payload=payload,
        model_name=args.model,
        timeout_seconds=args.timeout_seconds,
        ollama_base_url=args.ollama_base_url,
        temperature=args.temperature,
    )
    result_dict = result.to_dict()
    metadata = {
        key: value for key, value in result_dict.items() if key != "raw_model_output"
    }

    print("=== DAILY COACH PROVIDER PREVIEW RUNTIME SPIKE METADATA ===")
    print(json.dumps(metadata, indent=2, sort_keys=True))
    print()
    print("=== RAW MODEL OUTPUT ===")
    if result.raw_model_output:
        print(result.raw_model_output)
    else:
        print("<no model output>")
    return 0 if result.error_type is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
