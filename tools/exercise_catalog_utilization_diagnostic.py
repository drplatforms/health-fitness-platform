"""Developer diagnostic for deterministic workout catalog utilization.

This tool intentionally does not change workout-generation behavior. It traces
which hard-coded candidate pools are actually considered by the deterministic
workout planner, compares those pools with the active exercise catalog, and
summarizes selection dominance across a variation sweep.
"""

# ruff: noqa: E402, SLF001

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database
from models.training_constraint_models import TrainingConstraints
from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import WorkoutContext
from services import workout_plan_service as workout_plans
from services.exercise_catalog_service import (
    clear_exercise_catalog_cache,
    find_catalog_entry_by_name,
    get_exercise_catalog,
)
from services.workout_rotation_pool_service import (
    CATALOG_SLOT_FAMILY_PATTERNS,
    build_catalog_slot_options,
    is_catalog_entry_generator_eligible,
)

DEFAULT_HOME_GYM_EQUIPMENT = [
    "bodyweight",
    "dumbbell",
    "adjustable_bench",
    "barbell",
    "rack",
    "plates",
    "ez_bar",
    "pull_up_bar",
    "resistance_band",
    "cable",
    "rope_cable_attachment",
    "treadmill",
    "bike",
    "exercise_ball",
]

WORKOUT_SIZE_TARGETS = {
    "quick": 4,
    "standard": 5,
    "full": 7,
}

SPECIALIZED_PATTERNS = {
    "carry",
    "core_anti_extension",
    "core_anti_rotation",
    "lunge",
    "vertical_pull",
}

SPECIALIZED_NAME_TERMS = {
    "carry",
    "split squat",
    "reverse lunge",
    "walking lunge",
    "lateral lunge",
    "step-up",
    "step up",
    "hip thrust",
    "glute bridge",
    "hamstring curl",
    "calf raise",
    "rear delt",
    "face pull",
    "pull-apart",
    "pull apart",
    "dead bug",
    "bird dog",
    "side plank",
    "pallof",
}


def _normalize_token(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_name(value: str) -> str:
    return workout_plans._normalize_exercise_name(value)  # noqa: SLF001


def _training_constraints() -> TrainingConstraints:
    return TrainingConstraints(
        recommended_rir_min=2,
        recommended_rir_max=4,
        low_rir_guidance="Keep most working sets controlled.",
        progression_guidance="Progress gradually when recovery is stable.",
        recovery_constraint="normal",
        confidence="Moderate",
        reason_codes=["catalog_utilization_diagnostic"],
    )


def _workout_constraints(available_equipment: list[str]) -> WorkoutConstraints:
    return WorkoutConstraints(
        available_equipment=available_equipment,
        unavailable_equipment=["machine"],
        confidence="Moderate",
        reason_codes=["catalog_utilization_diagnostic"],
    )


def _context_for(
    size: str, variation_index: int, available_equipment: list[str]
) -> WorkoutContext:
    target_count = WORKOUT_SIZE_TARGETS[size]
    return WorkoutContext(
        user_id=102,
        scenario="aligned_managed",
        primary_goal="strength_and_recomposition",
        training_load="moderate",
        recovery_demand="normal",
        avg_rir=2.5,
        workout_count=4,
        training_constraints=_training_constraints(),
        workout_constraints=_workout_constraints(available_equipment),
        confidence="Moderate",
        reason_codes=["catalog_utilization_diagnostic"],
        workout_size_preference=size,
        requested_exercise_count=target_count,
        final_target_exercise_count=target_count,
        exercise_count_reason=f"diagnostic_{size}",
        exercise_count_user_reason=f"Diagnostic {size} sweep.",
        preview_variation_index=variation_index,
    )


def _equipment_allowed_for_entry(entry: Any, constraints: WorkoutConstraints) -> bool:
    equipment = [str(item) for item in entry.equipment_required]
    return workout_plans._equipment_allowed(equipment, constraints)  # noqa: SLF001


def _equipment_exclusion_reason(
    equipment_required: list[str], constraints: WorkoutConstraints
) -> str:
    required = {_normalize_token(item) for item in equipment_required}
    available = {_normalize_token(item) for item in constraints.available_equipment}
    unavailable = {_normalize_token(item) for item in constraints.unavailable_equipment}
    blocked = sorted(required & unavailable)
    missing = sorted(required - available) if available else []
    if blocked:
        return "blocked_unavailable_equipment:" + ",".join(blocked)
    if missing:
        return "missing_available_equipment:" + ",".join(missing)
    return "unknown_filter_reason"


def _is_specialized(entry: Any) -> bool:
    normalized_name = entry.name.lower()
    return entry.movement_pattern in SPECIALIZED_PATTERNS or any(
        term in normalized_name for term in SPECIALIZED_NAME_TERMS
    )


def _entry_payload(entry: Any) -> dict[str, Any]:
    return {
        "name": entry.name,
        "exercise_type": entry.exercise_type,
        "movement_pattern": entry.movement_pattern,
        "primary_muscle_groups": list(entry.primary_muscle_groups),
        "equipment_required": list(entry.equipment_required),
        "difficulty": entry.difficulty,
    }


@contextmanager
def _trace_selection_records(
    records: list[dict[str, Any]], size: str, variation_index: int
):
    original_select = workout_plans._select_exercise  # noqa: SLF001
    slot_counter = {"value": 0}

    def traced_select(
        workout_constraints: WorkoutConstraints,
        options: list[tuple[str, list[str]]],
        *,
        user_id: int | None = None,
        slot_key: str | None = None,
        preview_variation_index: int = 0,
        exercise_preference_by_catalog_id: dict[int, str] | None = None,
    ) -> tuple[str, list[str]]:
        slot_counter["value"] += 1
        resolved_slot_key = slot_key or workout_plans._selection_slot_key(options)  # noqa: SLF001
        recent_name_counts = workout_plans._recent_exercise_counts(  # noqa: SLF001
            workout_constraints
        )
        recent_pattern_counts = workout_plans._recent_movement_pattern_counts(  # noqa: SLF001
            workout_constraints
        )
        recent_modality_counts = workout_plans._recent_equipment_modality_counts(  # noqa: SLF001
            workout_constraints
        )
        most_recent_plan_names = workout_plans._most_recent_plan_names(  # noqa: SLF001
            workout_constraints
        )

        allowed_candidates: list[dict[str, Any]] = []
        excluded_candidates: list[dict[str, Any]] = []
        candidate_names_before_filters: list[str] = []
        for option_index, (name, equipment_required) in enumerate(options):
            catalog_name, catalog_equipment = (
                workout_plans._catalog_equipment_for_option(  # noqa: SLF001
                    name, equipment_required
                )
            )
            candidate_names_before_filters.append(catalog_name)
            if workout_plans._equipment_allowed(  # noqa: SLF001
                catalog_equipment, workout_constraints
            ):
                score = workout_plans._option_score(  # noqa: SLF001
                    name,
                    equipment_required,
                    workout_constraints,
                    option_index,
                    recent_name_counts,
                    recent_pattern_counts,
                    recent_modality_counts,
                    most_recent_plan_names,
                    exercise_preference_by_catalog_id or {},
                )
                entry = find_catalog_entry_by_name(catalog_name)
                allowed_candidates.append(
                    {
                        "name": catalog_name,
                        "movement_pattern": entry.movement_pattern if entry else None,
                        "equipment_required": catalog_equipment,
                        "score": score,
                        "source_option_index": option_index,
                    }
                )
            else:
                excluded_candidates.append(
                    {
                        "name": catalog_name,
                        "equipment_required": catalog_equipment,
                        "reason": _equipment_exclusion_reason(
                            catalog_equipment, workout_constraints
                        ),
                        "source_option_index": option_index,
                    }
                )

        selected_name, selected_equipment = original_select(
            workout_constraints,
            options,
            user_id=user_id,
            slot_key=slot_key,
            preview_variation_index=preview_variation_index,
            exercise_preference_by_catalog_id=exercise_preference_by_catalog_id,
        )
        selected_entry = find_catalog_entry_by_name(selected_name)
        ranked_candidates = sorted(
            allowed_candidates,
            key=lambda candidate: candidate["score"],
            reverse=True,
        )
        records.append(
            {
                "size": size,
                "variation_index": variation_index,
                "slot_index": slot_counter["value"],
                "slot_key": resolved_slot_key,
                "selected_exercise": selected_name,
                "selected_movement_pattern": (
                    selected_entry.movement_pattern if selected_entry else None
                ),
                "selected_equipment_required": selected_equipment,
                "candidate_count_before_filters": len(options),
                "candidate_count_after_filters": len(allowed_candidates),
                "candidate_names_before_filters": candidate_names_before_filters,
                "candidate_names_after_filters": [
                    candidate["name"] for candidate in allowed_candidates
                ],
                "top_candidate_names_before_scoring": [
                    option_name for option_name, _equipment in options[:10]
                ],
                "top_candidate_names_after_scoring": [
                    candidate["name"] for candidate in ranked_candidates[:10]
                ],
                "excluded_candidate_examples": excluded_candidates[:10],
                "selected_candidate_score": next(
                    (
                        candidate["score"]
                        for candidate in ranked_candidates
                        if candidate["name"] == selected_name
                    ),
                    None,
                ),
                "selected_candidate_rank_after_scoring": next(
                    (
                        index + 1
                        for index, candidate in enumerate(ranked_candidates)
                        if candidate["name"] == selected_name
                    ),
                    None,
                ),
            }
        )
        return selected_name, selected_equipment

    workout_plans._select_exercise = traced_select  # noqa: SLF001
    try:
        yield
    finally:
        workout_plans._select_exercise = original_select  # noqa: SLF001


def collect_catalog_utilization_diagnostic(
    *,
    sizes: list[str] | None = None,
    variation_count: int = 10,
    available_equipment: list[str] | None = None,
    initialize_db: bool = True,
) -> dict[str, Any]:
    """Collect catalog reachability diagnostics without changing generation logic."""

    sizes = sizes or ["quick", "standard", "full"]
    available_equipment = available_equipment or list(DEFAULT_HOME_GYM_EQUIPMENT)
    if initialize_db:
        database.initialize_database()
    clear_exercise_catalog_cache()

    catalog = get_exercise_catalog()
    context_constraints = _workout_constraints(available_equipment)
    equipment_eligible_catalog = [
        entry
        for entry in catalog
        if _equipment_allowed_for_entry(entry, context_constraints)
    ]
    generator_eligible_catalog = [
        entry
        for entry in equipment_eligible_catalog
        if is_catalog_entry_generator_eligible(entry)
    ]

    selection_records: list[dict[str, Any]] = []
    generated_plans: list[dict[str, Any]] = []
    selected_names_counter: Counter[str] = Counter()
    selected_pattern_counter: Counter[str] = Counter()
    selected_type_counter: Counter[str] = Counter()

    for size in sizes:
        for variation_index in range(variation_count):
            context = _context_for(size, variation_index, available_equipment)
            with _trace_selection_records(selection_records, size, variation_index):
                plan = workout_plans.generate_candidate_workout_plan(context)
            exercise_names = [exercise.name for exercise in plan.exercises]
            selected_names_counter.update(exercise_names)
            selected_pattern_counter.update(
                entry.movement_pattern
                for name in exercise_names
                if (entry := find_catalog_entry_by_name(name)) is not None
            )
            selected_type_counter.update(
                entry.exercise_type
                for name in exercise_names
                if (entry := find_catalog_entry_by_name(name)) is not None
            )
            generated_plans.append(
                {
                    "size": size,
                    "variation_index": variation_index,
                    "exercise_count": len(plan.exercises),
                    "exercise_names": exercise_names,
                }
            )

    selected_normalized_names = {
        _normalize_name(name) for name in selected_names_counter
    }
    candidate_option_names = {
        _normalize_name(candidate_name)
        for record in selection_records
        for candidate_name in record["candidate_names_before_filters"]
    }
    candidate_option_names.update(
        _normalize_name(candidate_name)
        for record in selection_records
        for candidate_name in record["candidate_names_after_filters"]
    )
    never_selected_entries = [
        entry
        for entry in equipment_eligible_catalog
        if _normalize_name(entry.name) not in selected_normalized_names
    ]
    not_in_generation_candidate_options = [
        entry
        for entry in equipment_eligible_catalog
        if _normalize_name(entry.name) not in candidate_option_names
    ]
    generator_eligible_never_selected = [
        entry
        for entry in generator_eligible_catalog
        if _normalize_name(entry.name) not in selected_normalized_names
    ]
    specialized_never_selected = [
        entry for entry in never_selected_entries if _is_specialized(entry)
    ]

    exclusion_reason_counts: Counter[str] = Counter(
        candidate["reason"]
        for record in selection_records
        for candidate in record["excluded_candidate_examples"]
    )
    not_selected_reason_counts: Counter[str] = Counter()
    for entry in generator_eligible_never_selected:
        if _normalize_name(entry.name) not in candidate_option_names:
            not_selected_reason_counts[
                "not_supported_by_current_generator_candidate_pools"
            ] += 1
        else:
            not_selected_reason_counts["candidate_not_selected_in_sweep"] += 1

    representative_context = _context_for("full", 0, available_equipment)
    slot_family_candidate_pool_sizes = {
        family: len(build_catalog_slot_options(representative_context, [], family))
        for family in sorted(CATALOG_SLOT_FAMILY_PATTERNS)
    }

    slot_pool_summary: dict[str, dict[str, Any]] = {}
    for record in selection_records:
        slot_key = f"{record['size']}:slot_{record['slot_index']}:{record['slot_key']}"
        summary = slot_pool_summary.setdefault(
            slot_key,
            {
                "size": record["size"],
                "slot_index": record["slot_index"],
                "slot_key": record["slot_key"],
                "observed_after_filter_counts": [],
                "selected_exercises": Counter(),
                "top_candidates_after_scoring": set(),
            },
        )
        summary["observed_after_filter_counts"].append(
            record["candidate_count_after_filters"]
        )
        summary["selected_exercises"].update([record["selected_exercise"]])
        summary["top_candidates_after_scoring"].update(
            record["top_candidate_names_after_scoring"]
        )

    serializable_slot_pool_summary = []
    for summary in slot_pool_summary.values():
        counts = summary["observed_after_filter_counts"]
        serializable_slot_pool_summary.append(
            {
                "size": summary["size"],
                "slot_index": summary["slot_index"],
                "slot_key": summary["slot_key"],
                "min_candidate_count_after_filters": min(counts),
                "max_candidate_count_after_filters": max(counts),
                "selected_exercises": dict(summary["selected_exercises"].most_common()),
                "top_candidates_after_scoring": sorted(
                    summary["top_candidates_after_scoring"]
                )[:20],
            }
        )

    by_size_reachable: dict[str, list[str]] = {}
    for size in sizes:
        names_for_size = sorted(
            {
                name
                for plan in generated_plans
                if plan["size"] == size
                for name in plan["exercise_names"]
            }
        )
        by_size_reachable[size] = names_for_size

    report = {
        "diagnostic_scope": {
            "sizes": sizes,
            "variation_count": variation_count,
            "available_equipment": available_equipment,
            "unavailable_equipment": context_constraints.unavailable_equipment,
        },
        "catalog_summary": {
            "total_active_exercises": len(catalog),
            "total_exercises_with_usable_metadata": sum(
                1
                for entry in catalog
                if entry.name and entry.exercise_type and entry.movement_pattern
            ),
            "total_equipment_eligible_exercises": len(equipment_eligible_catalog),
            "total_generator_eligible_exercises": len(generator_eligible_catalog),
            "total_by_movement_pattern": dict(
                Counter(entry.movement_pattern for entry in catalog).most_common()
            ),
            "equipment_eligible_by_movement_pattern": dict(
                Counter(
                    entry.movement_pattern for entry in equipment_eligible_catalog
                ).most_common()
            ),
            "total_by_equipment_type": dict(
                Counter(
                    equipment
                    for entry in catalog
                    for equipment in entry.equipment_required
                ).most_common()
            ),
            "specialized_or_accessory_movement_count": sum(
                1 for entry in catalog if _is_specialized(entry)
            ),
        },
        "generation_reachability_summary": {
            "total_unique_selected_exercises": len(selected_names_counter),
            "unique_selected_by_size": by_size_reachable,
            "total_equipment_eligible_never_selected": len(never_selected_entries),
            "equipment_eligible_never_selected_examples": [
                _entry_payload(entry) for entry in never_selected_entries[:40]
            ],
            "total_equipment_eligible_not_in_candidate_options": len(
                not_in_generation_candidate_options
            ),
            "total_generator_eligible_not_selected": len(
                generator_eligible_never_selected
            ),
            "equipment_eligible_not_in_candidate_options_examples": [
                _entry_payload(entry)
                for entry in not_in_generation_candidate_options[:40]
            ],
            "total_specialized_never_selected": len(specialized_never_selected),
            "specialized_never_selected_examples": [
                _entry_payload(entry) for entry in specialized_never_selected[:40]
            ],
        },
        "dominance_summary": {
            "most_frequently_selected_exercises": dict(
                selected_names_counter.most_common(20)
            ),
            "selected_by_movement_pattern": dict(
                selected_pattern_counter.most_common()
            ),
            "selected_by_exercise_type": dict(selected_type_counter.most_common()),
            "candidate_filter_exclusion_reason_counts": dict(
                exclusion_reason_counts.most_common()
            ),
            "not_selected_reason_counts": dict(
                not_selected_reason_counts.most_common()
            ),
        },
        "slot_family_candidate_pool_sizes": slot_family_candidate_pool_sizes,
        "candidate_pool_summary": serializable_slot_pool_summary,
        "generated_plan_sweep": generated_plans,
        "slot_selection_records": selection_records,
    }
    report["diagnostic_findings"] = _build_findings(report)
    return report


def _build_findings(report: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    reachability = report["generation_reachability_summary"]
    catalog_summary = report["catalog_summary"]
    eligible = catalog_summary["total_equipment_eligible_exercises"]
    selected = reachability["total_unique_selected_exercises"]
    if eligible:
        findings.append(
            f"Deterministic sweep selected {selected} of {eligible} equipment-eligible catalog exercises."
        )
    not_in_options = reachability["total_equipment_eligible_not_in_candidate_options"]
    if not_in_options:
        findings.append(
            f"{not_in_options} equipment-eligible catalog exercises were never present in traced generation candidate options."
        )
    generator_not_selected = reachability["total_generator_eligible_not_selected"]
    if generator_not_selected:
        findings.append(
            f"{generator_not_selected} generator-eligible catalog exercises were not selected in the sweep."
        )
    specialized_never = reachability["total_specialized_never_selected"]
    if specialized_never:
        findings.append(
            f"{specialized_never} specialized/accessory equipment-eligible exercises were never selected in the sweep."
        )
    frequent = report["dominance_summary"]["most_frequently_selected_exercises"]
    if frequent:
        top_name, top_count = next(iter(frequent.items()))
        findings.append(
            f"Most frequent selected exercise: {top_name} ({top_count} selections)."
        )
    narrow_slots = [
        item
        for item in report["candidate_pool_summary"]
        if item["min_candidate_count_after_filters"] <= 2
    ]
    if narrow_slots:
        findings.append(
            f"{len(narrow_slots)} traced slot pools had two or fewer valid candidates after filters."
        )
    return findings


def _print_text_report(report: dict[str, Any]) -> None:
    print("=" * 80)
    print("EXERCISE CATALOG UTILIZATION DIAGNOSTIC V1")
    print("=" * 80)
    for finding in report["diagnostic_findings"]:
        print(f"- {finding}")

    print("\nCATALOG SUMMARY")
    for key, value in report["catalog_summary"].items():
        print(f"{key}: {value}")

    print("\nREACHABILITY SUMMARY")
    reachability = report["generation_reachability_summary"]
    print(
        "total_unique_selected_exercises:",
        reachability["total_unique_selected_exercises"],
    )
    for size, names in reachability["unique_selected_by_size"].items():
        print(f"{size}: {len(names)} selected -> {names}")
    print(
        "total_equipment_eligible_never_selected:",
        reachability["total_equipment_eligible_never_selected"],
    )
    print(
        "total_equipment_eligible_not_in_candidate_options:",
        reachability["total_equipment_eligible_not_in_candidate_options"],
    )
    print(
        "total_generator_eligible_not_selected:",
        reachability["total_generator_eligible_not_selected"],
    )
    print(
        "total_specialized_never_selected:",
        reachability["total_specialized_never_selected"],
    )

    print("\nDOMINANCE SUMMARY")
    for name, count in report["dominance_summary"][
        "most_frequently_selected_exercises"
    ].items():
        print(f"{count:>3}  {name}")
    print(
        "selected_by_movement_pattern:",
        report["dominance_summary"]["selected_by_movement_pattern"],
    )
    print(
        "selected_by_exercise_type:",
        report["dominance_summary"]["selected_by_exercise_type"],
    )
    print(
        "not_selected_reason_counts:",
        report["dominance_summary"]["not_selected_reason_counts"],
    )

    print("\nSLOT-FAMILY CANDIDATE POOL SIZES")
    for family, count in report["slot_family_candidate_pool_sizes"].items():
        print(f"{family}: {count}")

    print("\nCANDIDATE POOL SUMMARY")
    for pool in report["candidate_pool_summary"]:
        print(
            f"{pool['size']} slot {pool['slot_index']} "
            f"candidates={pool['min_candidate_count_after_filters']}-"
            f"{pool['max_candidate_count_after_filters']} "
            f"selected={pool['selected_exercises']}"
        )

    print("\nEQUIPMENT-ELIGIBLE NOT-IN-CANDIDATE EXAMPLES")
    for entry in reachability["equipment_eligible_not_in_candidate_options_examples"][
        :25
    ]:
        print(
            f"- {entry['name']} | {entry['movement_pattern']} | "
            f"{entry['equipment_required']}"
        )

    print("\nSPECIALIZED NEVER-SELECTED EXAMPLES")
    for entry in reachability["specialized_never_selected_examples"][:25]:
        print(
            f"- {entry['name']} | {entry['movement_pattern']} | "
            f"{entry['equipment_required']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report deterministic workout exercise catalog utilization."
    )
    parser.add_argument("--variation-count", type=int, default=10)
    parser.add_argument(
        "--sizes",
        nargs="+",
        default=["quick", "standard", "full"],
        choices=sorted(WORKOUT_SIZE_TARGETS),
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for JSON output. Text output is always printed when format=text.",
    )
    args = parser.parse_args()

    report = collect_catalog_utilization_diagnostic(
        sizes=list(args.sizes),
        variation_count=args.variation_count,
    )
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
