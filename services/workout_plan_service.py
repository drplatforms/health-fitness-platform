from dataclasses import asdict

from models.user_state_models import UserHealthState
from models.workout_constraint_models import WorkoutConstraints
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutPlan,
    CandidateWorkoutExercise,
    CandidateWorkoutPlan,
    WorkoutContext,
)
from services.coaching_decision_service import build_coaching_decision
from services.exercise_catalog_service import find_catalog_entry_by_name
from services.training_constraint_service import build_training_constraints
from services.workout_constraint_service import build_workout_constraints

_INTERNAL_DEBUG_TERMS = [
    "guardrail",
    "guardrails",
    "validation",
    "validator",
    "fallback",
    "deterministic",
    "backend",
    "schema",
    "source of truth",
    "reason code",
    "reason codes",
    "debug",
    "internal",
    "candidateworkoutplan",
    "approvedworkoutplan",
    "workoutcontext",
    "trainingconstraints",
    "workoutconstraints",
    "coachingdecision",
    "data_quality_limited",
    "aligned_managed",
    "recovery_limited",
    "nutrition_training_mismatch",
    "improving_after_deload",
]

_RECOVERY_LIMITED_FORBIDDEN_TERMS = [
    "max effort",
    "max-effort",
    "all-out",
    "to failure",
]

_ALIGNED_MANAGED_FORBIDDEN_TERMS = [
    "deload",
    "reduce intensity",
    "reduce training",
    "cut volume",
    "back off",
]

_DATA_QUALITY_FORBIDDEN_TERMS = [
    "overtraining",
    "stalled progress",
    "stalled weight loss",
    "stalled fat loss",
    "likely caused",
    "likely causing",
    "likely contribute",
]


def _normalize_equipment(equipment: str) -> str:
    return equipment.strip().lower().replace(" ", "_")


def _text_blob(plan: CandidateWorkoutPlan) -> str:
    exercise_text = " ".join(
        f"{exercise.name} {exercise.notes}" for exercise in plan.exercises
    )
    return " ".join(
        [
            plan.title,
            plan.session_focus,
            plan.warmup,
            plan.cooldown,
            plan.progression_guidance,
            plan.rationale,
            exercise_text,
        ]
    ).lower()


def build_workout_context(health_state: UserHealthState) -> WorkoutContext:
    coaching_decision = build_coaching_decision(health_state)
    training_constraints = build_training_constraints(health_state, coaching_decision)
    workout_constraints = build_workout_constraints(health_state)

    return WorkoutContext(
        user_id=health_state.user_id,
        scenario=coaching_decision.scenario,
        primary_goal=health_state.primary_goal,
        training_load=health_state.training_state.training_load,
        recovery_demand=health_state.training_state.recovery_demand,
        avg_rir=health_state.training_state.avg_rir,
        workout_count=health_state.training_state.workout_count,
        training_constraints=training_constraints,
        workout_constraints=workout_constraints,
        confidence=coaching_decision.confidence,
        reason_codes=list(
            dict.fromkeys(
                coaching_decision.reason_codes
                + training_constraints.reason_codes
                + workout_constraints.reason_codes
            )
        ),
    )


def _equipment_allowed(
    equipment_required: list[str], workout_constraints: WorkoutConstraints
) -> bool:
    if not equipment_required:
        return True

    required = {_normalize_equipment(item) for item in equipment_required}
    available = {
        _normalize_equipment(item) for item in workout_constraints.available_equipment
    }
    unavailable = {
        _normalize_equipment(item) for item in workout_constraints.unavailable_equipment
    }

    if required & unavailable:
        return False

    if available and not required.issubset(available):
        return False

    return True


def _catalog_equipment_for_option(
    name: str,
    fallback_equipment_required: list[str],
) -> tuple[str, list[str]]:
    catalog_entry = find_catalog_entry_by_name(name)
    if catalog_entry is None:
        return name, [
            _normalize_equipment(item) for item in fallback_equipment_required
        ]

    return (
        catalog_entry.name,
        [_normalize_equipment(item) for item in catalog_entry.equipment_required],
    )


def _normalize_exercise_name(name: str) -> str:
    return name.strip().lower().replace("-", " ").replace("_", " ")


def _recent_exercise_names(workout_constraints: WorkoutConstraints) -> set[str]:
    return {
        _normalize_exercise_name(name)
        for name in workout_constraints.recent_exercises
        if name
    }


def _recent_movement_patterns(workout_constraints: WorkoutConstraints) -> set[str]:
    patterns: set[str] = set()
    for name in workout_constraints.recent_exercises:
        catalog_entry = find_catalog_entry_by_name(name)
        if catalog_entry is not None:
            patterns.add(catalog_entry.movement_pattern)
    return patterns


def _is_home_gym_like(workout_constraints: WorkoutConstraints) -> bool:
    available = {
        _normalize_equipment(item) for item in workout_constraints.available_equipment
    }
    return bool(
        available
        & {
            "barbell",
            "cable",
            "dumbbell",
            "ez_bar",
            "pull_up_bar",
            "resistance_band",
        }
    )


def _difficulty_score(
    difficulty: str | None, workout_constraints: WorkoutConstraints
) -> int:
    normalized = (difficulty or "intermediate").strip().lower()
    if workout_constraints.confidence == "Low":
        return {"beginner": 12, "intermediate": 2, "advanced": -18}.get(normalized, 0)

    return {"beginner": 2, "intermediate": 12, "advanced": 4}.get(normalized, 0)


def _option_score(
    name: str,
    equipment_required: list[str],
    workout_constraints: WorkoutConstraints,
    option_index: int,
    recent_names: set[str],
    recent_patterns: set[str],
) -> int:
    catalog_entry = find_catalog_entry_by_name(name)
    catalog_name, normalized_equipment = _catalog_equipment_for_option(
        name, equipment_required
    )
    score = 1000 - option_index

    if _normalize_exercise_name(catalog_name) in recent_names:
        score -= 450

    if catalog_entry is not None:
        if catalog_entry.movement_pattern in recent_patterns:
            score -= 45
        score += _difficulty_score(catalog_entry.difficulty, workout_constraints)

    equipment = set(normalized_equipment)
    if "machine" in equipment:
        score -= 90

    if _is_home_gym_like(workout_constraints):
        score += 12 * len(
            equipment
            & {
                "barbell",
                "cable",
                "dumbbell",
                "ez_bar",
                "pull_up_bar",
                "resistance_band",
                "rope_cable_attachment",
            }
        )
        if equipment == {"bodyweight"}:
            score -= 8

    return score


def _select_exercise(
    workout_constraints: WorkoutConstraints,
    options: list[tuple[str, list[str]]],
) -> tuple[str, list[str]]:
    allowed_options: list[tuple[int, str, list[str]]] = []
    recent_names = _recent_exercise_names(workout_constraints)
    recent_patterns = _recent_movement_patterns(workout_constraints)

    for index, (name, equipment_required) in enumerate(options):
        catalog_name, catalog_equipment_required = _catalog_equipment_for_option(
            name,
            equipment_required,
        )
        if _equipment_allowed(catalog_equipment_required, workout_constraints):
            allowed_options.append(
                (
                    _option_score(
                        name,
                        equipment_required,
                        workout_constraints,
                        index,
                        recent_names,
                        recent_patterns,
                    ),
                    catalog_name,
                    catalog_equipment_required,
                )
            )

    if allowed_options:
        _, name, equipment_required = max(allowed_options, key=lambda item: item[0])
        return name, equipment_required

    name, equipment_required = options[-1]
    return _catalog_equipment_for_option(name, equipment_required)


def _prefer_alternate_template(context: WorkoutContext) -> bool:
    recent_patterns = _recent_movement_patterns(context.workout_constraints)
    return bool(
        {"hinge", "vertical_push", "vertical_pull"}.issubset(recent_patterns)
        or {"squat", "horizontal_push", "horizontal_pull"}.issubset(recent_patterns)
    )


def _exercise(
    name: str,
    sets: int,
    reps_min: int,
    reps_max: int,
    rir_min: int,
    rir_max: int,
    notes: str,
    equipment_required: list[str],
) -> CandidateWorkoutExercise:
    return CandidateWorkoutExercise(
        name=name,
        sets=sets,
        reps_min=reps_min,
        reps_max=reps_max,
        rir_min=rir_min,
        rir_max=rir_max,
        notes=notes,
        equipment_required=[_normalize_equipment(item) for item in equipment_required],
    )


def _exercise_from_options(
    context: WorkoutContext,
    options: list[tuple[str, list[str]]],
    sets: int,
    reps_min: int,
    reps_max: int,
    rir_min: int,
    rir_max: int,
    notes: str,
) -> CandidateWorkoutExercise:
    name, equipment_required = _select_exercise(context.workout_constraints, options)
    return _exercise(
        name,
        sets,
        reps_min,
        reps_max,
        rir_min,
        rir_max,
        notes,
        equipment_required,
    )


def generate_candidate_workout_plan(context: WorkoutContext) -> CandidateWorkoutPlan:
    constraints = context.training_constraints
    rir_min = constraints.recommended_rir_min or 2
    rir_max = constraints.recommended_rir_max or 4

    if context.scenario == "recovery_limited":
        return CandidateWorkoutPlan(
            title="Recovery-Aware Strength Session",
            session_focus="Maintain movement quality while reducing recovery cost.",
            duration_minutes=40,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Goblet Squat", ["dumbbell"]),
                        ("Dumbbell Split Squat", ["dumbbell"]),
                        ("Stability Ball Wall Squat", ["exercise_ball"]),
                        ("Reverse Lunge", ["bodyweight"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                        ("Leg Press", ["machine"]),
                    ],
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Use a controlled tempo and stop with reps in reserve.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Dumbbell Floor Press", ["dumbbell"]),
                        ("Dumbbell Bench Press", ["dumbbell"]),
                        ("Band Resisted Push-Up", ["bodyweight", "resistance_band"]),
                        ("Push-Up", ["bodyweight"]),
                        ("Machine Chest Press", ["machine"]),
                    ],
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Keep effort moderate and avoid grinding reps.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Band Row", ["resistance_band"]),
                        ("Cable Row", ["cable"]),
                        ("One-Arm Dumbbell Row", ["dumbbell"]),
                        ("Chest-Supported Row", ["dumbbell"]),
                        ("Inverted Row", ["bodyweight"]),
                        ("Machine Row", ["machine"]),
                    ],
                    3,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Prioritize smooth reps and steady breathing.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Bird Dog", ["bodyweight"]),
                        ("Band Face Pull", ["resistance_band"]),
                        ("Stability Ball Dead Bug", ["exercise_ball"]),
                        ("Dead Bug", ["bodyweight"]),
                        ("Bike Recovery Ride", ["bike"]),
                        ("Farmer Carry", ["dumbbell"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep this easy and restorative; it should feel light.",
                ),
            ],
            warmup="Start with 5-8 minutes of easy cardio and light ramp-up sets.",
            cooldown="Finish with easy walking and relaxed mobility work.",
            progression_guidance=constraints.low_rir_guidance,
            rationale=(
                "Recovery markers suggest the session should preserve consistency "
                "without adding aggressive training stress."
            ),
            confidence=context.confidence,
        )

    if context.scenario == "nutrition_training_mismatch":
        return CandidateWorkoutPlan(
            title="Controlled Strength Practice",
            session_focus="Train productively while nutrition support is reviewed.",
            duration_minutes=45,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Dumbbell RDL", ["dumbbell"]),
                        ("Cable Pull-Through", ["cable", "rope_cable_attachment"]),
                        ("Stability Ball Hamstring Curl", ["exercise_ball"]),
                        ("Goblet Squat", ["dumbbell"]),
                        ("Reverse Lunge", ["bodyweight"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                        ("Leg Press", ["machine"]),
                    ],
                    3,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep the final reps controlled and repeatable.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Incline Dumbbell Press", ["dumbbell"]),
                        ("Dumbbell Floor Press", ["dumbbell"]),
                        ("Single-Arm Cable Press", ["cable"]),
                        ("Push-Up", ["bodyweight"]),
                        ("Machine Chest Press", ["machine"]),
                    ],
                    3,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use a load that allows consistent technique.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Cable Lat Pulldown", ["cable"]),
                        ("Band Lat Pulldown", ["resistance_band"]),
                        ("Cable Row", ["cable"]),
                        ("Dumbbell Row", ["dumbbell"]),
                        ("Inverted Row", ["bodyweight"]),
                    ],
                    3,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Stop before form breaks down.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Cable Woodchop", ["cable"]),
                        ("Band Pallof Press", ["resistance_band"]),
                        ("Dead Bug", ["bodyweight"]),
                        ("Band Face Pull", ["resistance_band"]),
                        ("Bike Steady State", ["bike"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    (
                        "Keep the accessory work low-to-moderate while nutrition "
                        "support is clarified."
                    ),
                ),
            ],
            warmup="Use progressive warm-up sets before the first two movements.",
            cooldown="Log performance, effort, and post-workout energy.",
            progression_guidance=constraints.progression_guidance,
            rationale=(
                "Training can continue, but progression should stay controlled "
                "while nutrition support is clarified."
            ),
            confidence=context.confidence,
        )

    if context.scenario == "improving_after_deload":
        return CandidateWorkoutPlan(
            title="Controlled Progression Session",
            session_focus="Build on the improving trend without ramping too quickly.",
            duration_minutes=50,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Romanian Deadlift", ["barbell"]),
                        ("Barbell Squat", ["barbell"]),
                        ("Dumbbell Split Squat", ["dumbbell"]),
                        ("Dumbbell Single-Leg RDL", ["dumbbell"]),
                        ("Goblet Squat", ["dumbbell"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                        ("Leg Press", ["machine"]),
                    ],
                    3,
                    5,
                    8,
                    rir_min,
                    rir_max,
                    "Use a conservative load and leave room to progress next session.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Overhead Press", ["barbell"]),
                        ("Dumbbell Shoulder Press", ["dumbbell"]),
                        ("Dumbbell Bench Press", ["dumbbell"]),
                        ("Barbell Bench Press", ["barbell"]),
                        ("Dumbbell Floor Press", ["dumbbell"]),
                        ("Push-Up", ["bodyweight"]),
                    ],
                    3,
                    6,
                    8,
                    rir_min,
                    rir_max,
                    "Keep speed consistent across sets.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Pull-Up", ["pull_up_bar"]),
                        ("Cable Lat Pulldown", ["cable"]),
                        ("Cable High Row", ["cable"]),
                        ("Cable Row", ["cable"]),
                        ("Barbell Row", ["barbell"]),
                        ("Dumbbell Row", ["dumbbell"]),
                        ("Band Row", ["resistance_band"]),
                        ("Inverted Row", ["bodyweight"]),
                    ],
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Keep reps crisp and avoid forcing load jumps.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Farmer Carry", ["dumbbell"]),
                        ("Suitcase Carry", ["dumbbell"]),
                        ("Cable Pallof Press", ["cable"]),
                        ("Cable Woodchop", ["cable"]),
                        ("EZ-Bar Curl", ["ez_bar"]),
                        ("Stability Ball Rollout", ["exercise_ball"]),
                        ("Dead Bug", ["bodyweight"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use controlled accessory work and avoid turning it into a ramp-up test.",
                ),
            ],
            warmup="Ramp gradually and keep early sets easy.",
            cooldown="Record soreness, energy, and performance after training.",
            progression_guidance=constraints.progression_guidance,
            rationale=(
                "Recent improvement supports training, but the next step should be "
                "gradual rather than a fast return to frequent high-effort work."
            ),
            confidence=context.confidence,
        )

    if context.scenario == "data_quality_limited":
        return CandidateWorkoutPlan(
            title="Manageable Baseline Session",
            session_focus="Keep training simple while logging quality improves.",
            duration_minutes=35,
            exercises=[
                _exercise_from_options(
                    context,
                    [
                        ("Goblet Squat", ["dumbbell"]),
                        ("Leg Press", ["machine"]),
                        ("Bodyweight Squat", ["bodyweight"]),
                    ],
                    2,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Choose a comfortable load and focus on repeatable movement.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Push-Up", ["bodyweight"]),
                        ("Dumbbell Shoulder Press", ["dumbbell"]),
                        ("Machine Chest Press", ["machine"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use a variation that feels controlled today.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Cable Row", ["cable"]),
                        ("Dumbbell Row", ["dumbbell"]),
                        ("Machine Row", ["machine"]),
                        ("Inverted Row", ["bodyweight"]),
                    ],
                    2,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Keep effort manageable and log how the session feels.",
                ),
                _exercise_from_options(
                    context,
                    [
                        ("Dead Bug", ["bodyweight"]),
                        ("Treadmill Walk", ["treadmill"]),
                        ("Bike Steady State", ["bike"]),
                        ("Band Pull-Apart", ["resistance_band"]),
                    ],
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep this simple and manageable so the session is easy to log consistently.",
                ),
            ],
            warmup="Start with easy movement and one light practice set per exercise.",
            cooldown="Log exercise, sets, reps, load, RIR, soreness, and energy.",
            progression_guidance=constraints.progression_guidance,
            rationale=(
                "Data quality limits confidence, so the session should establish a "
                "clear baseline before stronger training conclusions are made."
            ),
            confidence=context.confidence,
        )

    alternate_template = _prefer_alternate_template(context)
    lower_body_options = (
        [
            ("Romanian Deadlift", ["barbell"]),
            ("Dumbbell Single-Leg RDL", ["dumbbell"]),
            ("Front Squat", ["barbell"]),
            ("Goblet Squat", ["dumbbell"]),
            ("Stability Ball Wall Squat", ["exercise_ball"]),
            ("Bodyweight Squat", ["bodyweight"]),
            ("Leg Press", ["machine"]),
        ]
        if alternate_template
        else [
            ("Romanian Deadlift", ["barbell"]),
            ("Dumbbell Single-Leg RDL", ["dumbbell"]),
            ("Cable Pull-Through", ["cable", "rope_cable_attachment"]),
            ("Barbell Squat", ["barbell"]),
            ("Goblet Squat", ["dumbbell"]),
            ("Bodyweight Squat", ["bodyweight"]),
            ("Leg Press", ["machine"]),
        ]
    )
    push_options = (
        [
            ("Barbell Bench Press", ["barbell"]),
            ("Dumbbell Bench Press", ["dumbbell"]),
            ("Dumbbell Floor Press", ["dumbbell"]),
            ("Single-Arm Cable Press", ["cable"]),
            ("Push-Up", ["bodyweight"]),
        ]
        if alternate_template
        else [
            ("Overhead Press", ["barbell"]),
            ("Dumbbell Shoulder Press", ["dumbbell"]),
            ("Arnold Press", ["dumbbell"]),
            ("Barbell Bench Press", ["barbell"]),
            ("Push-Up", ["bodyweight"]),
        ]
    )
    pull_options = (
        [
            ("Cable Row", ["cable"]),
            ("Barbell Row", ["barbell"]),
            ("One-Arm Dumbbell Row", ["dumbbell", "adjustable_bench"]),
            ("Dumbbell Row", ["dumbbell"]),
            ("Band Row", ["resistance_band"]),
            ("Inverted Row", ["bodyweight"]),
        ]
        if alternate_template
        else [
            ("Pull-Up", ["pull_up_bar"]),
            ("Chin-Up", ["pull_up_bar"]),
            ("Cable Lat Pulldown", ["cable"]),
            ("Band Lat Pulldown", ["resistance_band"]),
            ("Cable Row", ["cable"]),
            ("Inverted Row", ["bodyweight"]),
        ]
    )
    accessory_options = (
        [
            ("Cable Woodchop", ["cable"]),
            ("Cable Pallof Press", ["cable"]),
            ("EZ-Bar Curl", ["ez_bar"]),
            ("Dumbbell Lateral Raise", ["dumbbell"]),
            ("Dead Bug", ["bodyweight"]),
        ]
        if alternate_template
        else [
            ("Farmer Carry", ["dumbbell"]),
            ("Suitcase Carry", ["dumbbell"]),
            ("Stability Ball Rollout", ["exercise_ball"]),
            ("Rope Face Pull", ["cable", "rope_cable_attachment"]),
            ("Dead Bug", ["bodyweight"]),
        ]
    )

    return CandidateWorkoutPlan(
        title="Gradual Progression Strength Session",
        session_focus="Maintain consistency and progress gradually.",
        duration_minutes=50,
        exercises=[
            _exercise_from_options(
                context,
                lower_body_options,
                3,
                5,
                8,
                rir_min,
                rir_max,
                "Add load only if the previous session felt stable.",
            ),
            _exercise_from_options(
                context,
                push_options,
                3,
                6,
                8,
                rir_min,
                rir_max,
                "Keep one or more clean reps in reserve on working sets.",
            ),
            _exercise_from_options(
                context,
                pull_options,
                3,
                8,
                10,
                rir_min,
                rir_max,
                "Progress gradually while recovery markers remain stable.",
            ),
            _exercise_from_options(
                context,
                accessory_options,
                2,
                8,
                12,
                rir_min,
                rir_max,
                "Use accessory work to round out the session without forcing progression.",
            ),
        ],
        warmup="Use 5-10 minutes of easy movement and progressive ramp-up sets.",
        cooldown="Log performance and recovery markers after the session.",
        progression_guidance=constraints.progression_guidance,
        rationale=(
            "Recovery, training, and available context support a normal gradual "
            "progression session."
        ),
        confidence=context.confidence,
    )


def validate_candidate_workout_plan(
    candidate: CandidateWorkoutPlan,
    context: WorkoutContext,
) -> list[str]:
    violations: list[str] = []

    if not candidate.exercises:
        violations.append("Workout plan must include at least one exercise.")

    training_constraints = context.training_constraints
    workout_constraints = context.workout_constraints
    for exercise in candidate.exercises:
        if exercise.sets < 1 or exercise.sets > 6:
            violations.append(f"Invalid set count for {exercise.name}.")

        if exercise.reps_min < 1 or exercise.reps_max < exercise.reps_min:
            violations.append(f"Invalid rep range for {exercise.name}.")

        if (
            exercise.rir_min < 0
            or exercise.rir_max > 5
            or exercise.rir_max < exercise.rir_min
        ):
            violations.append(f"Invalid RIR range for {exercise.name}.")

        if training_constraints.recommended_rir_min is not None:
            if exercise.rir_min < training_constraints.recommended_rir_min:
                violations.append(
                    f"{exercise.name} uses lower RIR than current constraints allow."
                )

        if training_constraints.recommended_rir_max is not None:
            if exercise.rir_max > training_constraints.recommended_rir_max:
                violations.append(
                    f"{exercise.name} uses higher RIR than current constraints allow."
                )

        if not _equipment_allowed(exercise.equipment_required, workout_constraints):
            violations.append(
                f"{exercise.name} requires equipment outside current workout constraints."
            )

    text = _text_blob(candidate)

    for term in _INTERNAL_DEBUG_TERMS:
        if term in text:
            violations.append("Workout plan contains internal/debug language.")
            break

    if context.scenario == "recovery_limited":
        for term in _RECOVERY_LIMITED_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Recovery-limited workout plans must avoid max-effort language."
                )
                break

    if context.scenario == "aligned_managed":
        for term in _ALIGNED_MANAGED_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Aligned workout plans must avoid unnecessary intervention framing."
                )
                break

    if context.scenario == "data_quality_limited":
        for term in _DATA_QUALITY_FORBIDDEN_TERMS:
            if term in text:
                violations.append(
                    "Data-quality-limited workout plans must avoid "
                    "overconfident claims."
                )
                break

    return violations


def approve_candidate_workout_plan(
    candidate: CandidateWorkoutPlan,
    context: WorkoutContext,
) -> ApprovedWorkoutPlan:
    violations = validate_candidate_workout_plan(candidate, context)
    if violations:
        raise ValueError(
            "CandidateWorkoutPlan failed validation: " + "; ".join(violations)
        )

    return ApprovedWorkoutPlan(
        title=candidate.title,
        session_focus=candidate.session_focus,
        duration_minutes=candidate.duration_minutes,
        exercises=[
            ApprovedWorkoutExercise(
                name=exercise.name,
                sets=exercise.sets,
                reps_min=exercise.reps_min,
                reps_max=exercise.reps_max,
                rir_min=exercise.rir_min,
                rir_max=exercise.rir_max,
                notes=exercise.notes,
                equipment_required=exercise.equipment_required,
            )
            for exercise in candidate.exercises
        ],
        warmup=candidate.warmup,
        cooldown=candidate.cooldown,
        progression_guidance=candidate.progression_guidance,
        rationale=candidate.rationale,
        confidence=candidate.confidence,
        scenario=context.scenario,
        reason_codes=context.reason_codes,
    )


def build_approved_workout_plan(health_state: UserHealthState) -> ApprovedWorkoutPlan:
    context = build_workout_context(health_state)
    candidate = generate_candidate_workout_plan(context)
    return approve_candidate_workout_plan(candidate, context)


def render_approved_workout_plan(plan: ApprovedWorkoutPlan) -> str:
    lines = [
        "**Workout Plan Preview**",
        "",
        f"**Title:** {plan.title}",
        f"**Focus:** {plan.session_focus}",
        f"**Duration:** About {plan.duration_minutes} minutes",
        "",
        "**Warmup:** " + plan.warmup,
        "",
        "**Exercises:**",
    ]

    for exercise in plan.exercises:
        lines.append(
            "- "
            f"{exercise.name}: {exercise.sets} sets x "
            f"{exercise.reps_min}-{exercise.reps_max} reps, "
            f"RIR {exercise.rir_min}-{exercise.rir_max}. "
            f"{exercise.notes}"
        )

    lines.extend(
        [
            "",
            "**Progression Guidance:** " + plan.progression_guidance,
            "",
            "**Cooldown:** " + plan.cooldown,
            "",
            "**Why:** " + plan.rationale,
            "",
            "**Confidence:** " + plan.confidence,
        ]
    )

    return "\n".join(lines)


def approved_workout_plan_to_dict(plan: ApprovedWorkoutPlan) -> dict:
    return asdict(plan)
