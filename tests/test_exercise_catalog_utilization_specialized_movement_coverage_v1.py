from pathlib import Path

import database
from tools.exercise_catalog_utilization_diagnostic import (
    DEFAULT_HOME_GYM_EQUIPMENT,
    collect_catalog_utilization_diagnostic,
)

TARGET_REACHABLE_EXERCISE_MINIMUM = 60
TARGET_NOT_IN_CANDIDATE_MAXIMUM = 25
TARGET_MOVEMENT_PATTERNS = {
    "squat",
    "lunge",
    "horizontal_push",
    "horizontal_pull",
    "core_anti_extension",
}
TARGET_SPECIALIZED_SELECTIONS = {
    "Reverse Lunge",
    "Split Squat",
    "Dumbbell Split Squat",
    "Dumbbell Reverse Lunge",
    "Dumbbell RDL",
    "Glute Bridge",
    "Hip Thrust",
    "Dead Bug",
    "Side Plank",
    "Bird Dog",
    "Band Face Pull",
    "Band Pull-Apart",
    "Band-Assisted Pull-Up",
    "Cable Crunch",
    "Farmer Carry",
    "Hanging Leg Raise",
    "Hanging Oblique Knee Raise",
    "Treadmill Walk",
    "Bike Intervals",
    "Waiter Carry",
}
TARGET_CANDIDATE_OPTIONS = {
    "Reverse Lunge",
    "Dumbbell Split Squat",
    "Dumbbell RDL",
    "Dead Bug",
    "Side Plank",
    "Bird Dog",
    "Band-Assisted Pull-Up",
}


def _collect_report(tmp_path, monkeypatch) -> dict:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    return collect_catalog_utilization_diagnostic(
        variation_count=12,
        available_equipment=list(DEFAULT_HOME_GYM_EQUIPMENT),
    )


def _selected_exercise_names(report: dict) -> set[str]:
    return {
        name
        for plan in report["generated_plan_sweep"]
        for name in plan["exercise_names"]
    }


def _candidate_option_names(report: dict) -> set[str]:
    names: set[str] = set()
    for record in report["slot_selection_records"]:
        names.update(record["top_candidate_names_before_scoring"])
        names.update(record["top_candidate_names_after_scoring"])
        names.update(
            candidate["name"] for candidate in record["excluded_candidate_examples"]
        )
    return names


def _diagnostic_failure_message(report: dict) -> str:
    reachability = report["generation_reachability_summary"]
    selected_names = sorted(_selected_exercise_names(report))
    candidate_names = _candidate_option_names(report)
    missing_patterns = sorted(
        TARGET_MOVEMENT_PATTERNS
        - set(report["dominance_summary"]["selected_by_movement_pattern"])
    )
    missing_candidate_options = sorted(TARGET_CANDIDATE_OPTIONS - candidate_names)
    selected_specialized = sorted(TARGET_SPECIALIZED_SELECTIONS & set(selected_names))

    return "\n".join(
        [
            "catalog utilization diagnostic did not meet v1 coverage gate",
            f"total_unique_selected_exercises={reachability['total_unique_selected_exercises']}",
            f"target_unique_selected_exercises>={TARGET_REACHABLE_EXERCISE_MINIMUM}",
            "total_equipment_eligible_not_in_candidate_options="
            f"{reachability['total_equipment_eligible_not_in_candidate_options']}",
            "target_equipment_eligible_not_in_candidate_options<="
            f"{TARGET_NOT_IN_CANDIDATE_MAXIMUM}",
            "selected_by_movement_pattern="
            f"{report['dominance_summary']['selected_by_movement_pattern']}",
            f"missing_target_movement_patterns={missing_patterns}",
            f"selected_specialized_targets={selected_specialized}",
            f"missing_target_candidate_options={missing_candidate_options}",
            f"selected_exercise_names={selected_names}",
            f"diagnostic_findings={report['diagnostic_findings']}",
        ]
    )


def test_catalog_reachability_breadth_exceeds_current_narrow_sweep(
    tmp_path, monkeypatch
):
    report = _collect_report(tmp_path, monkeypatch)
    reachability = report["generation_reachability_summary"]
    selected_patterns = set(report["dominance_summary"]["selected_by_movement_pattern"])

    failures = []
    if (
        reachability["total_unique_selected_exercises"]
        < TARGET_REACHABLE_EXERCISE_MINIMUM
    ):
        failures.append("too_few_unique_selected_exercises")
    if (
        reachability["total_equipment_eligible_not_in_candidate_options"]
        > TARGET_NOT_IN_CANDIDATE_MAXIMUM
    ):
        failures.append("too_many_equipment_eligible_exercises_never_in_candidates")
    missing_patterns = TARGET_MOVEMENT_PATTERNS - selected_patterns
    if missing_patterns:
        failures.append("missing_supported_movement_patterns")

    assert failures == [], _diagnostic_failure_message(report)


def test_specialized_movements_are_reachable_and_selected_when_equipment_matches(
    tmp_path, monkeypatch
):
    report = _collect_report(tmp_path, monkeypatch)
    selected_names = _selected_exercise_names(report)
    candidate_names = _candidate_option_names(report)

    selected_specialized_targets = TARGET_SPECIALIZED_SELECTIONS & selected_names
    missing_candidate_options = TARGET_CANDIDATE_OPTIONS - candidate_names

    assert len(selected_specialized_targets) >= 3, _diagnostic_failure_message(report)
    assert missing_candidate_options == set(), _diagnostic_failure_message(report)
