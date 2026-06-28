from __future__ import annotations

import json

from models.daily_coach_narrative_models import (
    DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED,
    DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED,
    DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED,
)
from models.daily_coach_synthesis_models import DailyCoachSynthesis
from models.daily_coach_value_narrative_models import CandidateDailyCoachValueNarrative
from models.daily_next_action_models import DailyNextAction
from services.daily_coach_narrative_context_service import (
    build_daily_coach_narrative_context_from_action,
)
from services.daily_coach_narrative_validation_service import (
    parse_daily_coach_narrative_candidate,
    validate_daily_coach_narrative_candidate,
    validate_daily_coach_value_narrative_candidate,
)


def _context():
    action = DailyNextAction(
        action_id="log_food",
        title="Log a meal or snack",
        summary="Add today's food intake so nutrition guidance has enough data.",
        reason="Today's nutrition state is limited until more food data is logged.",
        priority=3,
        workflow_target="nutrition_quick_log",
        severity="info",
        evidence={
            "scenario": "data_quality_limited",
            "recovery_checkin_present": True,
            "nutrition_logging_completeness": "likely_incomplete",
            "nutrition_confidence": "Limited",
            "workout_available": False,
            "report_guidance_available": False,
        },
    )
    return build_daily_coach_narrative_context_from_action(
        user_id=105,
        action=action,
        context_date="2026-06-19",
    )


def _valid_payload(context):
    return {
        "coach_note": (
            "Log a meal or snack so today's nutrition guidance has enough "
            "information to work from."
        ),
        "key_takeaway": "Today's nutrition state is limited until more food data is logged.",
        "recommended_focus": context.approved_focus,
        "confidence_language": "Keep this limited until more food data is logged.",
        "used_approved_facts": [
            f"Daily next action: {context.next_action_title}",
            f"Daily next action reason: {context.next_action_reason}",
        ],
        "avoided_claims": [
            "No food, exercise, target, recovery, or medical claim was invented."
        ],
    }


def test_parse_daily_coach_narrative_candidate_accepts_exact_schema_json():
    context = _context()

    result = parse_daily_coach_narrative_candidate(json.dumps(_valid_payload(context)))

    assert result.parse_status == DAILY_COACH_NARRATIVE_PARSE_STATUS_SUCCESS
    assert result.candidate is not None
    assert result.candidate.recommended_focus == context.approved_focus


def test_parse_rejects_markdown_or_prose_wrapped_json():
    context = _context()

    result = parse_daily_coach_narrative_candidate(
        "```json\n" + json.dumps(_valid_payload(context)) + "\n```"
    )

    assert result.parse_status == DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED
    assert "single JSON object" in (result.error or "")


def test_parse_rejects_missing_or_extra_keys():
    context = _context()
    payload = _valid_payload(context)
    payload["type"] = "object"
    payload.pop("avoided_claims")

    result = parse_daily_coach_narrative_candidate(json.dumps(payload))

    assert result.parse_status == DAILY_COACH_NARRATIVE_PARSE_STATUS_FAILED
    assert "Schema keys invalid" in (result.error or "")


def test_validation_approves_grounded_candidate():
    context = _context()
    parsed = parse_daily_coach_narrative_candidate(json.dumps(_valid_payload(context)))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED
    )
    assert validation.validation_errors == []


def test_validation_rejects_changed_recommended_focus():
    context = _context()
    payload = _valid_payload(context)
    payload["recommended_focus"] = "Review today's workout"
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any("recommended_focus" in error for error in validation.validation_errors)


def test_validation_rejects_unapproved_fact():
    context = _context()
    payload = _valid_payload(context)
    payload["used_approved_facts"] = ["A fact the backend did not approve"]
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any("unapproved fact" in error for error in validation.validation_errors)


def test_validation_rejects_invented_food_target_and_number():
    context = _context()
    payload = _valid_payload(context)
    payload["coach_note"] = (
        "Log a meal or snack, then eat 200g chicken breast to hit a calorie target."
    )
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any("Forbidden claim" in error for error in validation.validation_errors)
    assert any("Invented numeric" in error for error in validation.validation_errors)


def test_validation_rejects_raw_debug_provider_metadata():
    context = _context()
    payload = _valid_payload(context)
    payload["confidence_language"] = "The raw provider payload says this is valid."
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any("metadata" in error for error in validation.validation_errors)


def test_validation_rejects_qwen25_style_meta_process_language():
    context = _context()
    payload = _valid_payload(context)
    payload["coach_note"] = (
        "Use the exact approved focus Log a meal or snack because the "
        "backend-approved facts support it."
    )
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any(
        "Meta/internal process language" in error
        for error in validation.validation_errors
    )


def test_validation_reports_meta_language_field_name():
    context = _context()
    payload = _valid_payload(context)
    payload["coach_note"] = "The backend-approved facts support logging food today."
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any(
        "coach_note:" in error and "backend-approved" in error
        for error in validation.validation_errors
    )


def test_validation_rejects_internal_architecture_language_in_user_copy():
    context = _context()
    payload = _valid_payload(context)
    payload["key_takeaway"] = (
        "Based on the provided context, the validator requires this workflow target."
    )
    payload["confidence_language"] = "As instructed, keep the JSON output compact."
    payload["avoided_claims"] = [
        "No provider output should mention the deterministic fallback."
    ]
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    joined_errors = " ".join(validation.validation_errors)
    assert "key_takeaway:" in joined_errors
    assert "confidence_language:" in joined_errors
    assert "provided context" in joined_errors
    assert "workflow target" in joined_errors
    assert "json" in joined_errors.lower()


def test_validation_allows_normal_qwen3_style_coach_copy():
    context = _context()
    payload = _valid_payload(context)
    payload["coach_note"] = (
        "Log your meal or snack to improve nutrition tracking accuracy."
    )
    payload["key_takeaway"] = (
        "Today's nutrition state is limited until more food data is logged."
    )
    payload["confidence_language"] = "Keep this limited until more food data is logged."
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED
    )
    assert validation.validation_errors == []


def test_validation_allows_audit_language_in_avoided_claims_only():
    context = _context()
    payload = _valid_payload(context)
    payload["avoided_claims"] = [
        "No backend-approved facts, provider output, or deterministic fallback "
        "language is displayed."
    ]
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED
    )
    assert validation.validation_errors == []


def test_validation_allows_exact_nutrition_confidence_fact_but_rejects_paraphrase():
    context = _context()
    exact_fact = "Nutrition confidence: Limited"
    assert exact_fact in context.approved_facts

    exact_payload = _valid_payload(context)
    exact_payload["used_approved_facts"] = [
        f"Daily next action: {context.next_action_title}",
        exact_fact,
    ]
    exact_parsed = parse_daily_coach_narrative_candidate(json.dumps(exact_payload))
    exact_validation = validate_daily_coach_narrative_candidate(
        exact_parsed.candidate,
        context=context,
    )
    assert (
        exact_validation.validation_status
        == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_APPROVED
    )

    paraphrased_payload = _valid_payload(context)
    paraphrased_payload["used_approved_facts"] = [
        f"Daily next action: {context.next_action_title}",
        "Nutritional confidence: Limited",
    ]
    paraphrased_parsed = parse_daily_coach_narrative_candidate(
        json.dumps(paraphrased_payload)
    )
    paraphrased_validation = validate_daily_coach_narrative_candidate(
        paraphrased_parsed.candidate,
        context=context,
    )
    assert (
        paraphrased_validation.validation_status
        == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any(
        "unapproved fact: Nutritional confidence: Limited" in error
        for error in paraphrased_validation.validation_errors
    )

    typo_payload = _valid_payload(context)
    typo_payload["used_approved_facts"] = [
        f"Daily next action: {context.next_action_title}",
        "Nut,rition confidence: Limited",
    ]
    typo_parsed = parse_daily_coach_narrative_candidate(json.dumps(typo_payload))
    typo_validation = validate_daily_coach_narrative_candidate(
        typo_parsed.candidate,
        context=context,
    )
    assert (
        typo_validation.validation_status
        == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any(
        "unapproved fact: Nut,rition confidence: Limited" in error
        for error in typo_validation.validation_errors
    )


def test_validation_rejects_changed_workflow_target_reference():
    context = _context()
    payload = _valid_payload(context)
    payload["coach_note"] = "Log a meal or snack before moving over to workout_preview."
    parsed = parse_daily_coach_narrative_candidate(json.dumps(payload))

    validation = validate_daily_coach_narrative_candidate(
        parsed.candidate,
        context=context,
    )

    assert (
        validation.validation_status == DAILY_COACH_NARRATIVE_VALIDATION_STATUS_REJECTED
    )
    assert any("workflow target" in error for error in validation.validation_errors)


def _value_synthesis() -> DailyCoachSynthesis:
    return DailyCoachSynthesis(
        user_id=102,
        synthesis_date="2026-06-05",
        scenario="aligned_managed",
        confidence="High",
        today_summary="Today supports planned training with nutrition follow-through.",
        recovery_signal="Readiness is high and fatigue risk is low.",
        training_signal="Planned strength work is available.",
        workout_guidance="Keep RIR 2-4.",
        execution_context="Planned strength work is available.",
        logging_focus="Calories and protein are below target.",
        plan_fit_note="No plan fit issue is present.",
        recommended_focus="Train as planned and close the protein gap.",
        reason_codes=["unit_test"],
        limitations=[],
    )


def _value_context_for_plainspoken_validation() -> dict:
    return {
        "approved_recovery": {
            "readiness_level": "High",
            "fatigue_risk": "Low",
        },
        "food_action_context": {
            "available": True,
            "primary_gap": "protein",
            "friendly_food_options": [
                {
                    "friendly_name": "canned tuna",
                    "canonical_name": "Tuna, Canned in Water",
                    "macro_reason": "protein",
                    "claim_keys": {
                        "friendly_name": "nutrition.food_suggestion.1.friendly_name",
                        "canonical_name": "nutrition.food_suggestion.1.display_name",
                    },
                }
            ],
        },
        "food_suggestion_copy_context": {
            "suggestions": [
                {
                    "friendly_name": "canned tuna",
                    "canonical_name": "Tuna, Canned in Water",
                    "macro_reason": "protein",
                    "claim_keys": {
                        "friendly_name": "nutrition.food_suggestion.1.friendly_name",
                        "canonical_name": "nutrition.food_suggestion.1.display_name",
                    },
                }
            ]
        },
        "approved_value_claims": [
            {
                "key": "recovery.readiness_level",
                "label": "readiness",
                "value": "High",
                "aliases": ["readiness is High"],
                "display_allowed": True,
            },
            {
                "key": "recovery.fatigue_risk",
                "label": "fatigue risk",
                "value": "Low",
                "aliases": ["fatigue risk is Low"],
                "display_allowed": True,
            },
            {
                "key": "nutrition.calories.status",
                "label": "calories status",
                "value": "below_target",
                "aliases": ["calories are below target"],
                "display_allowed": True,
            },
            {
                "key": "nutrition.protein.status",
                "label": "protein status",
                "value": "below_target",
                "aliases": ["protein is below target", "protein is still short"],
                "display_allowed": True,
            },
            {
                "key": "nutrition.food_suggestion.1.friendly_name",
                "label": "friendly food suggestion",
                "value": "canned tuna",
                "aliases": ["canned tuna"],
                "display_allowed": True,
            },
            {
                "key": "training.rir_range",
                "label": "RIR range",
                "value": "2-4",
                "aliases": ["RIR 2-4", "couple reps in reserve"],
                "display_allowed": True,
            },
        ],
    }


def _plainspoken_candidate(**overrides) -> CandidateDailyCoachValueNarrative:
    payload = {
        "headline": "Clean Strength + Simple Protein",
        "summary": "You can train as planned today, but do not turn it into a max-effort test.",
        "nutrition_note": "Calories and protein are below target. Add canned tuna if you still need more protein.",
        "training_note": "Prioritize clean reps, keep a couple reps in reserve, and stop before the set turns into a grind.",
        "recovery_note": "Recovery looks good enough to train as planned today.",
        "priority_action": "Do the planned workout, log what you actually eat, then add canned tuna if protein is still short.",
        "confidence": "High",
        "reason_codes": ["unit_test"],
        "quoted_values_used": [
            "recovery.readiness_level",
            "recovery.fatigue_risk",
            "nutrition.calories.status",
            "nutrition.protein.status",
            "nutrition.food_suggestion.1.friendly_name",
            "training.rir_range",
        ],
    }
    payload.update(overrides)
    return CandidateDailyCoachValueNarrative(**payload)


def test_value_narrative_validation_rejects_plainspoken_rejected_phrases():
    candidate = _plainspoken_candidate(
        summary="The win is clean work plus one simple food move.",
        nutrition_note="Use an easy protein bump if it fits your meals.",
    )

    errors = validate_daily_coach_value_narrative_candidate(
        candidate,
        synthesis=_value_synthesis(),
        value_context=_value_context_for_plainspoken_validation(),
    )

    joined = " ".join(errors)
    assert "food move" in joined
    assert "clean work" in joined
    assert "protein bump" in joined


def test_value_narrative_validation_allows_plainspoken_food_action():
    errors = validate_daily_coach_value_narrative_candidate(
        _plainspoken_candidate(),
        synthesis=_value_synthesis(),
        value_context=_value_context_for_plainspoken_validation(),
    )

    assert errors == []


def test_value_narrative_validation_rejects_unbacked_timing_or_pairing():
    candidate = _plainspoken_candidate(
        nutrition_note="Add canned tuna after training with rice if you still need more protein."
    )

    errors = validate_daily_coach_value_narrative_candidate(
        candidate,
        synthesis=_value_synthesis(),
        value_context=_value_context_for_plainspoken_validation(),
    )

    joined = " ".join(errors)
    assert "timing" in joined
    assert "pairings" in joined
