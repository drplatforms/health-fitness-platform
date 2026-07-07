from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import WorkoutContext
from services.exercise_catalog_service import get_exercise_catalog

CATALOG_SLOT_FAMILY_PATTERNS: dict[str, set[str]] = {
    "lower_primary": {"squat", "lunge", "hinge"},
    "squat_lunge": {"squat", "lunge"},
    "hinge": {"hinge"},
    "push_primary": {"horizontal_push", "vertical_push"},
    "pull_primary": {"horizontal_pull", "vertical_pull"},
    "core": {"core_anti_extension", "core_anti_rotation"},
    "carry": {"carry"},
    "arms": {"arms_biceps", "arms_triceps"},
    "accessory": {
        "arms_biceps",
        "arms_triceps",
        "carry",
        "core_anti_extension",
        "core_anti_rotation",
        "horizontal_pull",
        "vertical_push",
    },
    "shoulder_upper_back": {
        "arms_biceps",
        "arms_triceps",
        "horizontal_pull",
        "vertical_push",
    },
    "conditioning_finish": {
        "carry",
        "conditioning",
        "core_anti_extension",
        "horizontal_pull",
    },
}

SUPPORTED_ROTATION_PATTERNS = set().union(*CATALOG_SLOT_FAMILY_PATTERNS.values())

_ACCESSORY_NAME_HINTS = {
    "curl",
    "extension",
    "pressdown",
    "skull crusher",
    "lateral raise",
    "front raise",
    "rear delt",
    "face pull",
    "pull-apart",
    "pull apart",
    "external rotation",
    "shrug",
    "carry",
    "march",
    "pallof",
    "woodchop",
    "dead bug",
    "plank",
    "rollout",
    "bird dog",
    "calf raise",
}

_LOW_STRESS_CONDITIONING_HINTS = {
    "walk",
    "steady state",
    "easy",
    "spin",
    "cadence",
    "carry",
    "march",
    "calf raise",
    "plank",
    "dead bug",
}


def _normalize_token(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_name(value: str) -> str:
    return " ".join(str(value).strip().lower().replace("-", " ").split())


def _normalize_equipment(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(_normalize_token(value) for value in values if value))


def _equipment_allowed(
    equipment_required: list[str], workout_constraints: WorkoutConstraints
) -> bool:
    required = set(_normalize_equipment(equipment_required))
    available = set(_normalize_equipment(workout_constraints.available_equipment))
    unavailable = set(_normalize_equipment(workout_constraints.unavailable_equipment))

    if required & unavailable:
        return False
    if available and not required.issubset(available):
        return False
    return True


def _blocked_movement_patterns(workout_constraints: WorkoutConstraints) -> set[str]:
    blocked = {
        _normalize_token(value)
        for value in (
            workout_constraints.avoid_movements
            + workout_constraints.movement_restrictions
        )
        if str(value).strip()
    }
    expanded = set(blocked)
    if "core" in blocked:
        expanded.update({"core_anti_extension", "core_anti_rotation"})
    if "push" in blocked:
        expanded.update({"horizontal_push", "vertical_push"})
    if "pull" in blocked:
        expanded.update({"horizontal_pull", "vertical_pull"})
    if "lower" in blocked:
        expanded.update({"squat", "lunge", "hinge"})
    return expanded


def is_catalog_entry_generator_eligible(entry: Any) -> bool:
    pattern = _normalize_token(entry.movement_pattern)
    exercise_type = _normalize_token(entry.exercise_type)
    return bool(
        entry.name
        and exercise_type
        and pattern in SUPPORTED_ROTATION_PATTERNS
        and exercise_type != "mobility"
        and entry.equipment_required
    )


def _entry_matches_family(entry: Any, slot_family: str) -> bool:
    pattern = _normalize_token(entry.movement_pattern)
    family_patterns = CATALOG_SLOT_FAMILY_PATTERNS.get(slot_family, set())
    if pattern not in family_patterns:
        return False

    normalized_name = _normalize_name(entry.name)
    if slot_family == "pull_primary" and (
        "internal rotation" in normalized_name or "external rotation" in normalized_name
    ):
        return False

    if slot_family in {"accessory", "shoulder_upper_back"}:
        if pattern in {
            "arms_biceps",
            "arms_triceps",
            "carry",
            "core_anti_extension",
            "core_anti_rotation",
        }:
            return True
        return any(hint in normalized_name for hint in _ACCESSORY_NAME_HINTS)

    if slot_family == "conditioning_finish":
        if pattern != "conditioning":
            return True
        return any(hint in normalized_name for hint in _LOW_STRESS_CONDITIONING_HINTS)

    return True


def _entry_allowed_for_context(entry: Any, context: WorkoutContext) -> bool:
    pattern = _normalize_token(entry.movement_pattern)
    difficulty = _normalize_token(entry.difficulty or "intermediate")
    if pattern in _blocked_movement_patterns(context.workout_constraints):
        return False
    if not _equipment_allowed(entry.equipment_required, context.workout_constraints):
        return False
    if context.scenario == "recovery_limited" and difficulty == "advanced":
        return False
    return True


def _dedupe_options(
    options: Iterable[tuple[str, list[str]]],
) -> list[tuple[str, list[str]]]:
    deduped: list[tuple[str, list[str]]] = []
    seen_names: set[str] = set()
    for name, equipment_required in options:
        normalized_name = _normalize_name(name)
        if not normalized_name or normalized_name in seen_names:
            continue
        seen_names.add(normalized_name)
        deduped.append((name, _normalize_equipment(equipment_required)))
    return deduped


def build_catalog_slot_options(
    context: WorkoutContext,
    anchor_options: Iterable[tuple[str, list[str]]],
    slot_family: str,
) -> list[tuple[str, list[str]]]:
    """Expand anchored deterministic options with safe catalog slot candidates."""

    catalog_options = [
        (entry.name, list(entry.equipment_required))
        for entry in get_exercise_catalog()
        if is_catalog_entry_generator_eligible(entry)
        and _entry_matches_family(entry, slot_family)
        and _entry_allowed_for_context(entry, context)
    ]
    return _dedupe_options([*anchor_options, *catalog_options])
