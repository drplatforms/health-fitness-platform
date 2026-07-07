from pathlib import Path

import database
from models.training_constraint_models import TrainingConstraints
from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import WorkoutContext
from services import workout_plan_service as workout_plans
from services.exercise_catalog_service import find_catalog_entry_by_name
from tools.exercise_catalog_utilization_diagnostic import (
    DEFAULT_HOME_GYM_EQUIPMENT,
    collect_catalog_utilization_diagnostic,
)

TARGET_UNIQUE_SELECTED_MINIMUM = 120
TARGET_NOT_IN_CANDIDATE_MAXIMUM = 25
REQUIRED_MOVEMENT_PATTERNS = {
    "arms_biceps",
    "arms_triceps",
    "carry",
    "conditioning",
    "core_anti_extension",
    "core_anti_rotation",
    "vertical_pull",
}
EXPECTED_COUNTS_BY_SIZE = {
    "quick": 4,
    "standard": 5,
    "full": 7,
}


def _collect_report(tmp_path, monkeypatch) -> dict:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    return collect_catalog_utilization_diagnostic(
        variation_count=25,
        available_equipment=list(DEFAULT_HOME_GYM_EQUIPMENT),
    )


def _selected_exercise_names(report: dict) -> set[str]:
    return {
        name
        for plan in report["generated_plan_sweep"]
        for name in plan["exercise_names"]
    }


def _training_constraints() -> TrainingConstraints:
    return TrainingConstraints(
        recommended_rir_min=2,
        recommended_rir_max=4,
        low_rir_guidance="Keep most working sets controlled.",
        progression_guidance="Progress gradually when recovery is stable.",
        recovery_constraint="normal",
        confidence="Moderate",
        reason_codes=["exercise_rotation_coverage_v0"],
    )


def _workout_constraints(**overrides) -> WorkoutConstraints:
    values = {
        "available_equipment": list(DEFAULT_HOME_GYM_EQUIPMENT),
        "unavailable_equipment": ["machine"],
        "confidence": "Moderate",
        "reason_codes": ["exercise_rotation_coverage_v0"],
    }
    values.update(overrides)
    return WorkoutConstraints(**values)


def _context(workout_constraints: WorkoutConstraints) -> WorkoutContext:
    return WorkoutContext(
        user_id=102,
        scenario="aligned_managed",
        primary_goal="strength_and_recomposition",
        training_load="moderate",
        recovery_demand="normal",
        avg_rir=2.5,
        workout_count=4,
        training_constraints=_training_constraints(),
        workout_constraints=workout_constraints,
        confidence="Moderate",
        reason_codes=["exercise_rotation_coverage_v0"],
        workout_size_preference="full",
        requested_exercise_count=7,
        final_target_exercise_count=7,
        exercise_count_reason="diagnostic_full",
        exercise_count_user_reason="Diagnostic full sweep.",
        preview_variation_index=4,
    )


def test_home_gym_sweep_selects_broad_catalog_and_required_families(
    tmp_path, monkeypatch
):
    report = _collect_report(tmp_path, monkeypatch)
    reachability = report["generation_reachability_summary"]
    selected_patterns = set(report["dominance_summary"]["selected_by_movement_pattern"])

    assert (
        reachability["total_unique_selected_exercises"]
        >= TARGET_UNIQUE_SELECTED_MINIMUM
    ), report["diagnostic_findings"]
    assert (
        reachability["total_equipment_eligible_not_in_candidate_options"]
        <= TARGET_NOT_IN_CANDIDATE_MAXIMUM
    ), report["diagnostic_findings"]
    assert REQUIRED_MOVEMENT_PATTERNS.issubset(selected_patterns)
    assert "mobility" not in report["dominance_summary"]["selected_by_exercise_type"]


def test_selected_exercises_are_catalog_backed_and_equipment_safe(
    tmp_path, monkeypatch
):
    report = _collect_report(tmp_path, monkeypatch)
    available_equipment = set(DEFAULT_HOME_GYM_EQUIPMENT)

    for name in _selected_exercise_names(report):
        entry = find_catalog_entry_by_name(name)
        assert entry is not None, name
        assert "machine" not in entry.equipment_required
        assert set(entry.equipment_required).issubset(available_equipment)


def test_generated_sweep_preserves_size_and_same_workout_uniqueness(
    tmp_path, monkeypatch
):
    report = _collect_report(tmp_path, monkeypatch)

    for plan in report["generated_plan_sweep"]:
        names = plan["exercise_names"]
        rotation_groups = [
            workout_plans._exercise_rotation_group(name)  # noqa: SLF001
            for name in names
        ]
        assert len(names) == EXPECTED_COUNTS_BY_SIZE[plan["size"]]
        assert len(names) == len(set(names))
        assert len(rotation_groups) == len(set(rotation_groups))


def test_movement_restrictions_apply_to_anchored_and_catalog_options(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()
    context = _context(
        _workout_constraints(
            avoid_movements=["hinge", "vertical_push"],
            movement_restrictions=["core"],
        )
    )

    plan = workout_plans.generate_candidate_workout_plan(context)
    selected_patterns = {
        find_catalog_entry_by_name(exercise.name).movement_pattern
        for exercise in plan.exercises
    }

    assert "hinge" not in selected_patterns
    assert "vertical_push" not in selected_patterns
    assert "core_anti_extension" not in selected_patterns
    assert "core_anti_rotation" not in selected_patterns
