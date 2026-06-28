from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_natural_draft_audit_service import (  # noqa: E402
    DEFAULT_NATURAL_DRAFT_AUDIT_OUTPUT_DIR,
    list_daily_coach_natural_draft_scenarios,
    run_daily_coach_natural_draft_audit_matrix,
    run_daily_coach_natural_draft_audit_scenario,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Daily Coach Natural Draft + Claim Audit."
    )
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--run-scenario", default=None)
    parser.add_argument("--run-matrix", action="store_true")
    parser.add_argument("--scenarios", nargs="+", default=[])
    parser.add_argument(
        "--provider",
        default="deterministic",
        choices=["deterministic", "direct_ollama", "openai"],
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--allow-live-provider", action="store_true")
    parser.add_argument("--output-dir", default=DEFAULT_NATURAL_DRAFT_AUDIT_OUTPUT_DIR)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.list_scenarios:
        for scenario in list_daily_coach_natural_draft_scenarios():
            focus = "; ".join(scenario["expected_evaluation_focus"])
            print(
                f"{scenario['scenario_id']}\tuser={scenario['user_id']}\tdate={scenario['target_date']}\t{focus}"
            )
        return 0

    if args.run_scenario:
        result = run_daily_coach_natural_draft_audit_scenario(
            scenario_id=args.run_scenario,
            provider=args.provider,
            model=args.model,
            allow_live_provider=args.allow_live_provider,
            output_dir=Path(args.output_dir),
        )
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        else:
            _print_result_summary([result], Path(args.output_dir))
        return 0

    if args.run_matrix:
        scenarios = args.scenarios or ["rich_nutrition_training_recovery"]
        results = run_daily_coach_natural_draft_audit_matrix(
            scenarios=scenarios,
            provider=args.provider,
            model=args.model,
            allow_live_provider=args.allow_live_provider,
            output_dir=Path(args.output_dir),
        )
        if args.json:
            print(
                json.dumps(
                    [result.to_dict() for result in results], indent=2, sort_keys=True
                )
            )
        else:
            _print_result_summary(results, Path(args.output_dir))
        return 0

    parser.error("Use --list-scenarios, --run-scenario, or --run-matrix.")
    return 2


def _print_result_summary(results, output_dir: Path) -> None:
    print(f"Natural Draft Audit rows: {len(results)}")
    print(f"Output dir: {output_dir}")
    for result in results:
        print(
            f"{result.scenario_id}\t{result.provider}\tfinal={result.final_source}\t"
            f"initial_audit={result.audit_result.passed}\trepair={result.repair_result.attempted}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
