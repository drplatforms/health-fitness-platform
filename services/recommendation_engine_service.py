import json
from dataclasses import asdict

from models.recommendation_models import (
    ApprovedActionPlan,
    CandidateActionPlan,
    RecommendationContext,
)
from models.user_state_models import UserHealthState
from services.coaching_decision_service import build_coaching_decision
from services.nutrition_target_service import build_nutrition_targets
from services.training_constraint_service import build_training_constraints

_FORBIDDEN_RECOMMENDATION_PHRASES = [
    "high-rir (0-1)",
    "high rir (0-1)",
    "lower rir to 2-3",
    "sleep deprivation (5.3/10)",
    "likely from supplements",
    "over-supplementation likely",
    "supplementation artifacts",
    "0 kcal",
    "0 g protein",
    "0 g carbs",
    "0 g fat",
]


def build_recommendation_context(
    health_state: UserHealthState,
) -> RecommendationContext:
    coaching_decision = build_coaching_decision(health_state)
    nutrition_targets = build_nutrition_targets(health_state)
    training_constraints = build_training_constraints(health_state, coaching_decision)

    allowed_actions = [
        coaching_decision.training_action,
        coaching_decision.nutrition_action,
        coaching_decision.sleep_action,
        coaching_decision.monitoring_action,
        training_constraints.progression_guidance,
    ]
    forbidden_claims = [
        "Do not treat missing nutrition fields as zero intake.",
        "Do not assume supplements explain unusual micronutrient values.",
        "Do not describe RIR 0-1 as high RIR.",
        "Do not prescribe targets outside NutritionTargets v1 ranges.",
    ]

    return RecommendationContext(
        user_id=health_state.user_id,
        scenario=coaching_decision.scenario,
        primary_goal=health_state.primary_goal,
        body_weight_lb=nutrition_targets.body_weight_lb,
        nutrition_targets=nutrition_targets,
        training_constraints=training_constraints,
        coaching_decision=coaching_decision,
        allowed_actions=allowed_actions,
        forbidden_claims=forbidden_claims,
        confidence=coaching_decision.confidence,
        reason_codes=list(
            dict.fromkeys(
                coaching_decision.reason_codes
                + nutrition_targets.reason_codes
                + training_constraints.reason_codes
            )
        ),
    )


def recommendation_context_to_json(context: RecommendationContext) -> str:
    return json.dumps(asdict(context), indent=2)


def generate_candidate_action_plan_json(context: RecommendationContext) -> str:
    """Return structured JSON for the v1 recommendation vertical slice.

    This deterministic implementation is the local stand-in for the CrewAI JSON task.
    The schema and validator are the contract the future CrewAI task must satisfy.
    """
    decision = context.coaching_decision
    targets = context.nutrition_targets
    constraints = context.training_constraints

    if context.scenario == "aligned_managed":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=(
                "Maintain the current direction and progress gradually while recovery markers stay stable."
            ),
            workout_recommendation=constraints.progression_guidance,
            nutrition_action=(
                f"Keep nutrition logging consistent and use the current target ranges as a check-in point: "
                f"protein {targets.protein_grams_min}-{targets.protein_grams_max} g/day and "
                f"carbohydrates {targets.carbohydrate_grams_min}-{targets.carbohydrate_grams_max} g/day."
            ),
            rationale=(
                "Recovery, training load, and nutrition appear aligned enough to favor consistency over intervention."
            ),
            confidence=context.confidence,
        )
    elif context.scenario == "recovery_limited":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=decision.primary_focus,
            workout_recommendation=constraints.low_rir_guidance,
            nutrition_action=(
                "Review protein and carbohydrate support against training demand without assuming missing intake is zero."
            ),
            rationale=(
                "Sleep, soreness, energy, and training effort suggest recovery should lead the next recommendation."
            ),
            confidence=context.confidence,
        )
    elif context.scenario == "nutrition_training_mismatch":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=decision.primary_focus,
            workout_recommendation=constraints.progression_guidance,
            nutrition_action=(
                "Improve nutrition logging and compare protein and carbohydrate intake against the calculated target ranges."
            ),
            rationale=(
                "Training demand appears higher than confirmed nutrition support, but missing fields are unknown rather than zero."
            ),
            confidence=context.confidence,
        )
    elif context.scenario == "improving_after_deload":
        plan = CandidateActionPlan(
            daily_coaching_recommendation=(
                "Continue controlled progression while the recovery trend stabilizes."
            ),
            workout_recommendation=constraints.low_rir_guidance,
            nutrition_action=(
                "Keep nutrition logging consistent on training days and review support against training demand."
            ),
            rationale=(
                "The recent lower-stress period appears to be helping, so the next step is gradual progression."
            ),
            confidence=context.confidence,
        )
    else:
        plan = CandidateActionPlan(
            daily_coaching_recommendation=(
                "Improve logging completeness before making stronger nutrition or training changes."
            ),
            workout_recommendation=constraints.progression_guidance,
            nutrition_action=(
                "Verify food entries and unusual nutrient values; treat missing fields as unknown."
            ),
            rationale=(
                "Data quality limits confidence, so verification should come before stronger conclusions."
            ),
            confidence=context.confidence,
        )

    return json.dumps(asdict(plan))


def parse_candidate_action_plan(raw_json: str) -> CandidateActionPlan:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError("CandidateActionPlan must be valid JSON.") from exc

    required_fields = {
        "daily_coaching_recommendation",
        "workout_recommendation",
        "nutrition_action",
        "rationale",
        "confidence",
    }
    missing = required_fields - payload.keys()
    if missing:
        raise ValueError(f"CandidateActionPlan missing fields: {sorted(missing)}")

    return CandidateActionPlan(**{field: payload[field] for field in required_fields})


def validate_candidate_action_plan(
    candidate: CandidateActionPlan,
    context: RecommendationContext,
) -> list[str]:
    text = " ".join(
        [
            candidate.daily_coaching_recommendation,
            candidate.workout_recommendation,
            candidate.nutrition_action,
            candidate.rationale,
        ]
    ).lower()
    violations: list[str] = []

    for phrase in _FORBIDDEN_RECOMMENDATION_PHRASES:
        if phrase in text:
            violations.append(f"Forbidden recommendation phrase: {phrase}")

    if context.scenario == "recovery_limited":
        if "low_rir_high_effort_training" in context.reason_codes:
            if "rir 2-3" not in text or "rir 0-1" not in text:
                violations.append(
                    "Recovery-limited low-RIR recommendations must include RIR 2-3 guidance."
                )

    if context.scenario == "aligned_managed":
        intervention_terms = ["deload", "reduce intensity", "caloric deficit"]
        if any(term in text for term in intervention_terms):
            violations.append(
                "Aligned/managed recommendations should not use unnecessary intervention framing."
            )

    if context.scenario == "nutrition_training_mismatch":
        zero_intake_phrases = [
            "missing intake is zero",
            "missing fields are zero",
            "missing nutrition is zero",
        ]
        if any(phrase in text for phrase in zero_intake_phrases):
            violations.append("Missing nutrition must not be framed as zero intake.")

    if context.scenario == "data_quality_limited":
        if "verify" not in text and "logging" not in text:
            violations.append(
                "Data-quality-limited recommendations must emphasize verification or logging."
            )

    return violations


def approve_candidate_action_plan(
    candidate: CandidateActionPlan,
    context: RecommendationContext,
) -> ApprovedActionPlan:
    violations = validate_candidate_action_plan(candidate, context)
    if violations:
        raise ValueError("CandidateActionPlan rejected: " + "; ".join(violations))

    return ApprovedActionPlan(
        daily_coaching_recommendation=candidate.daily_coaching_recommendation,
        workout_recommendation=candidate.workout_recommendation,
        nutrition_action=candidate.nutrition_action,
        rationale=candidate.rationale,
        confidence=candidate.confidence,
        scenario=context.scenario,
        reason_codes=context.reason_codes,
    )


def render_approved_action_plan(plan: ApprovedActionPlan) -> str:
    return (
        "**Grounded Recommendation**\n\n"
        f"**Daily Coaching Recommendation:** {plan.daily_coaching_recommendation}\n\n"
        f"**Workout Recommendation:** {plan.workout_recommendation}\n\n"
        f"**Nutrition Action:** {plan.nutrition_action}\n\n"
        f"**Why:** {plan.rationale}\n\n"
        f"**Confidence:** {plan.confidence}"
    )


def build_approved_action_plan(health_state: UserHealthState) -> ApprovedActionPlan:
    context = build_recommendation_context(health_state)
    raw_json = generate_candidate_action_plan_json(context)
    candidate = parse_candidate_action_plan(raw_json)
    return approve_candidate_action_plan(candidate, context)
