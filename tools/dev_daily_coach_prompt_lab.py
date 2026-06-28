from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.daily_coach_prompt_lab_service import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    list_daily_coach_prompt_lab_scenarios,
    list_daily_coach_prompt_lab_variants,
    run_daily_coach_prompt_lab_matrix,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Developer-only Daily Coach Prompt Lab / Voice Lab."
    )
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--list-variants", action="store_true")
    parser.add_argument("--run-matrix", action="store_true")
    parser.add_argument("--scenarios", nargs="+", default=[])
    parser.add_argument("--variants", nargs="+", default=[])
    parser.add_argument(
        "--provider",
        default="deterministic",
        choices=["deterministic", "direct_ollama", "openai"],
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-live-provider", action="store_true")
    parser.add_argument("--include-deterministic-baseline", action="store_true")
    parser.add_argument("--write-scoring-template", action="store_true", default=True)
    parser.add_argument(
        "--no-scoring-template", action="store_false", dest="write_scoring_template"
    )
    parser.add_argument(
        "--json", action="store_true", help="Print result rows as JSON."
    )
    args = parser.parse_args(argv)

    if args.list_scenarios:
        for scenario in list_daily_coach_prompt_lab_scenarios():
            focus = "; ".join(scenario.expected_evaluation_focus)
            print(
                f"{scenario.scenario_id}\tuser={scenario.user_id}\tdate={scenario.target_date}\t{focus}"
            )
        return 0

    if args.list_variants:
        for variant in list_daily_coach_prompt_lab_variants():
            print(f"{variant.variant_id}\t{variant.label}\t{variant.hypothesis}")
        return 0

    if not args.run_matrix:
        parser.error("Use --list-scenarios, --list-variants, or --run-matrix.")

    scenarios = args.scenarios or ["rich_nutrition_training_recovery"]
    variants = args.variants or ["current_v5_baseline"]
    rows = run_daily_coach_prompt_lab_matrix(
        scenarios=scenarios,
        variants=variants,
        provider=args.provider,
        model=args.model,
        allow_live_provider=args.allow_live_provider,
        include_deterministic_baseline=args.include_deterministic_baseline,
        write_scoring_template=args.write_scoring_template,
        output_dir=Path(args.output_dir),
    )
    if args.json:
        print(json.dumps([row.to_dict() for row in rows], indent=2, sort_keys=True))
    else:
        print(f"Prompt Lab rows: {len(rows)}")
        print(f"Output dir: {Path(args.output_dir)}")
        for row in rows:
            print(
                f"{row.scenario_id}\t{row.variant_id}\t{row.provider}\t"
                f"success={row.success}\tskipped={row.skipped}\t"
                f"validation={row.safety_summary.validation_status}\t"
                f"rejected={len(row.safety_summary.rejected_phrase_flags)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
