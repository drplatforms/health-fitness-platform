from dataclasses import asdict

from models.user_state_models import UserHealthState
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutPlan,
    CandidateWorkoutExercise,
    CandidateWorkoutPlan,
    WorkoutContext,
)
from services.coaching_decision_service import build_coaching_decision
from services.training_constraint_service import build_training_constraints

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

    return WorkoutContext(
        user_id=health_state.user_id,
        scenario=coaching_decision.scenario,
        primary_goal=health_state.primary_goal,
        training_load=health_state.training_state.training_load,
        recovery_demand=health_state.training_state.recovery_demand,
        avg_rir=health_state.training_state.avg_rir,
        workout_count=health_state.training_state.workout_count,
        training_constraints=training_constraints,
        confidence=coaching_decision.confidence,
        reason_codes=list(
            dict.fromkeys(
                coaching_decision.reason_codes + training_constraints.reason_codes
            )
        ),
    )


def _exercise(
    name: str,
    sets: int,
    reps_min: int,
    reps_max: int,
    rir_min: int,
    rir_max: int,
    notes: str,
) -> CandidateWorkoutExercise:
    return CandidateWorkoutExercise(
        name=name,
        sets=sets,
        reps_min=reps_min,
        reps_max=reps_max,
        rir_min=rir_min,
        rir_max=rir_max,
        notes=notes,
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
                _exercise(
                    "Goblet Squat",
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Use a controlled tempo and stop with reps in reserve.",
                ),
                _exercise(
                    "Dumbbell Bench Press",
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Keep effort moderate and avoid grinding reps.",
                ),
                _exercise(
                    "Chest-Supported Row",
                    3,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Prioritize smooth reps and steady breathing.",
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
                _exercise(
                    "Leg Press",
                    3,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Keep the final reps controlled and repeatable.",
                ),
                _exercise(
                    "Incline Dumbbell Press",
                    3,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use a load that allows consistent technique.",
                ),
                _exercise(
                    "Lat Pulldown",
                    3,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Stop before form breaks down.",
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
                _exercise(
                    "Barbell Squat",
                    3,
                    5,
                    8,
                    rir_min,
                    rir_max,
                    "Use a conservative load and leave room to progress next session.",
                ),
                _exercise(
                    "Barbell Bench Press",
                    3,
                    6,
                    8,
                    rir_min,
                    rir_max,
                    "Keep bar speed consistent across sets.",
                ),
                _exercise(
                    "Barbell Row",
                    3,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Keep reps crisp and avoid forcing load jumps.",
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
                _exercise(
                    "Goblet Squat",
                    2,
                    8,
                    10,
                    rir_min,
                    rir_max,
                    "Choose a comfortable load and focus on repeatable movement.",
                ),
                _exercise(
                    "Push-Up or Dumbbell Press",
                    2,
                    8,
                    12,
                    rir_min,
                    rir_max,
                    "Use a variation that feels controlled today.",
                ),
                _exercise(
                    "Cable Row or Dumbbell Row",
                    2,
                    10,
                    12,
                    rir_min,
                    rir_max,
                    "Keep effort manageable and log how the session feels.",
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

    return CandidateWorkoutPlan(
        title="Gradual Progression Strength Session",
        session_focus="Maintain consistency and progress gradually.",
        duration_minutes=50,
        exercises=[
            _exercise(
                "Barbell Squat",
                3,
                5,
                8,
                rir_min,
                rir_max,
                "Add load only if the previous session felt stable.",
            ),
            _exercise(
                "Barbell Bench Press",
                3,
                6,
                8,
                rir_min,
                rir_max,
                "Keep one or more clean reps in reserve on working sets.",
            ),
            _exercise(
                "Barbell Row",
                3,
                8,
                10,
                rir_min,
                rir_max,
                "Progress gradually while recovery markers remain stable.",
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

    constraints = context.training_constraints
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

        if constraints.recommended_rir_min is not None:
            if exercise.rir_min < constraints.recommended_rir_min:
                violations.append(
                    f"{exercise.name} uses lower RIR than current constraints allow."
                )

        if constraints.recommended_rir_max is not None:
            if exercise.rir_max > constraints.recommended_rir_max:
                violations.append(
                    f"{exercise.name} uses higher RIR than current constraints allow."
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
