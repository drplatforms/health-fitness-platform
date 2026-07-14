from __future__ import annotations

import json
from dataclasses import fields, replace
from pathlib import Path
from typing import Any, cast

import pytest

import database
import services.cross_domain_coaching_preview_service as preview_service
from models.cross_domain_coaching_preview_models import (
    ApprovedActionCatalogItem,
    CrossDomainSelectableAction,
    ResolvedCoachingAction,
)
from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,
    ApprovedCoachFact,
    ApprovedFoodAction,
    ApprovedRecoveryInterpretation,
    ApprovedTrainingAction,
)
from services.cross_domain_coaching_evidence_service import (
    CROSS_DOMAIN_ASSESSMENT_CONTEXT_VERSION,
    build_cross_domain_assessment_context,
    build_cross_domain_coaching_evidence_packet,
)
from services.cross_domain_coaching_preview_service import (
    CROSS_DOMAIN_SEMANTIC_NARRATIVE_CONTEXT_VERSION,
    CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION,
    SpecialistAssessmentValidationError,
    audit_cross_domain_narrative_confidence_coherence,
    build_narrative_confidence_policy,
    build_narrative_provider_input,
    build_provider_safe_narrative_context,
    build_specialist_provider_input,
    build_specialist_response_schema,
    call_direct_ollama_preview,
    parse_cross_domain_specialist_assessment,
    parse_natural_coach_draft,
    resolve_cross_domain_coaching_brief,
    run_cross_domain_coaching_preview,
)
from tools.dev_cross_domain_coaching_synthesis_preview import (
    write_preview_artifacts,
)


def _brief(*, scenario: str = "recovery_limited") -> ApprovedCoachBrief:
    return ApprovedCoachBrief(
        brief_id=f"test:11:2026-07-13:{scenario}",
        user_id=11,
        date="2026-07-13",
        scenario=scenario,
        today_intent="Keep the day measured and grounded in logged work.",
        approved_facts=(
            ApprovedCoachFact(
                claim_key="recovery.readiness_level",
                claim_type="recovery_status",
                value="moderate",
                display_value="Moderate readiness",
            ),
            ApprovedCoachFact(
                claim_key="nutrition.protein.status",
                claim_type="nutrition_status",
                value="below target",
                display_value="Protein is below target",
            ),
            ApprovedCoachFact(
                claim_key="limitations.logging",
                claim_type="limitation_claim",
                value="logging is incomplete",
                display_value="logging is incomplete",
            ),
        ),
        approved_food_actions=(
            ApprovedFoodAction(
                food_claim_key="nutrition.food_suggestion.1.friendly_name",
                canonical_name="Tuna, Canned in Water",
                friendly_name="canned tuna",
                macro_reason="protein",
            ),
        ),
        approved_training_actions=(
            ApprovedTrainingAction(
                claim_keys=("training.rir_range",),
                instruction="Keep the planned session controlled.",
            ),
        ),
        approved_recovery_interpretations=(
            ApprovedRecoveryInterpretation(
                claim_keys=("recovery.readiness_level",),
                interpretation="Keep effort measured while readiness is moderate.",
            ),
        ),
        blocked_topics=("medical claims", "workout changes"),
        blocked_phrases=("force progression",),
        claim_registry={
            "recovery.readiness_level": {
                "value": "moderate",
                "display_value": "Moderate readiness",
                "user_facing_allowed": True,
                "confidence": "Moderate",
            },
            "nutrition.protein.status": {
                "value": "below target",
                "display_value": "Protein is below target",
                "user_facing_allowed": True,
                "confidence": "Moderate",
            },
            "nutrition.food_suggestion.1.friendly_name": {
                "value": "canned tuna",
                "display_value": "canned tuna",
                "user_facing_allowed": True,
                "confidence": "High",
            },
            "training.rir_range": {
                "value": "2-4",
                "display_value": "2-4",
                "user_facing_allowed": True,
                "confidence": "Moderate",
            },
        },
    )


def _payload() -> dict[str, object]:
    return {
        "user_id": 11,
        "target_date": "2026-07-13",
        "source_snapshot_version": "daily_coach_intelligence_snapshot_v1",
        "source_services": ["daily_coach_intelligence_snapshot_service"],
        "source_data": {
            "recovery_intelligence": {"readiness": "moderate", "confidence": "High"},
            "recovery_intelligence_v2": {"sleep_consistency": "steady"},
            "nutrition_trend_window": {"protein_status": "below target"},
            "workout_set_intelligence": {"completed_set_count": 3},
            "training_execution_summary": {"planned_set_count": 3},
            "foundation_layer_status": {"status": "available"},
            "data_completeness": {"nutrition": "partial"},
            "source_data_gaps": ["food logging is incomplete"],
            "reason_codes": ["recovery_limited"],
            "limitations": ["logging is incomplete"],
            "unapproved_section": {"secret": "must not become evidence"},
        },
        "source_data_gaps": ["food logging is incomplete"],
        "limitations": ["logging is incomplete"],
        "backend_truth_contract": {"backend_owns_facts": True},
    }


def _packet(*, scenario: str = "recovery_limited"):
    return build_cross_domain_coaching_evidence_packet(
        payload=_payload(),
        approved_brief=_brief(scenario=scenario),
        scenario=scenario,
    )


def _packet_for_brief(brief: ApprovedCoachBrief):
    return build_cross_domain_coaching_evidence_packet(
        payload=_payload(),
        approved_brief=brief,
        scenario=brief.scenario,
    )


def _legacy_prose_brief() -> ApprovedCoachBrief:
    brief = _brief()
    coach_summary = (
        "Recent recovery signals look supportive based on logged sleep, energy, and "
        "soreness."
    )
    return replace(
        brief,
        today_intent=(
            "Do the planned workout, log what you actually eat, then handle the "
            "protein gap with an approved food option."
        ),
        approved_interpretations=("Recovery looks good enough to train as planned.",),
        approved_facts=(
            *brief.approved_facts,
            ApprovedCoachFact(
                claim_key="recovery.coach_safe_summary",
                claim_type="recovery_status_claim",
                value=coach_summary,
                display_value=coach_summary,
            ),
        ),
        approved_training_actions=(
            replace(
                brief.approved_training_actions[0],
                instruction=(
                    "Train as planned, keep a couple reps in reserve, and stop before "
                    "the set turns into a grind."
                ),
                allowed_phrasings=(
                    "Use an approved food option if the matching nutrition gap is "
                    "still open.",
                ),
            ),
        ),
        approved_recovery_interpretations=(
            replace(
                brief.approved_recovery_interpretations[0],
                interpretation="Use canned tuna if the protein gap is still open.",
            ),
        ),
        claim_registry={
            **brief.claim_registry,
            "recovery.coach_safe_summary": {
                "value": coach_summary,
                "display_value": coach_summary,
                "user_facing_allowed": True,
                "confidence": "High",
            },
        },
    )


def _nested_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key for child in value.values() for key in _nested_keys(child)
        }
    if isinstance(value, list | tuple):
        return {key for child in value for key in _nested_keys(child)}
    return set()


def _assessment_context(packet, brief: ApprovedCoachBrief | None = None):
    return build_cross_domain_assessment_context(packet, brief or _brief())


def _rich_packet():
    payload = _payload()
    source_data = cast(dict[str, Any], payload["source_data"])
    source_data["recovery_intelligence"] = {
        "readiness": "moderate",
        "fatigue_risk": "low",
        "coach_safe_summary": (
            "Recent recovery signals look supportive based on logged sleep, energy, "
            "and soreness."
        ),
        "summary": (
            "Recent recovery indicators look supportive with usable check-in coverage."
        ),
        "primary_sleep": "steady",
        "primary_energy": "steady",
        "primary_soreness": "low",
        "coverage": "complete",
        "confidence": "High",
        "model_version": "recovery-model-metadata",
        "source_table": "recovery-source-table",
        "user_id": "internal-user-id",
        "target_date": "2026-07-13",
        "window": {"reason": "window-only-metadata"},
        "reason_codes": ["repeated-recovery-reason"],
    }
    source_data["nutrition_trend_window"] = {
        "logging_completeness": "partial",
        "logged_count": 4,
        "complete_count": 2,
        "no_log_count": 1,
        "overall_trend_confidence": "Moderate",
        "bodyweight_direction": "steady",
        "calibration_readiness": "ready",
        "logging_quality": "good",
        "summary": "Bodyweight trend is available but based on limited weigh-ins.",
        "trend_days": [
            {"date": "2026-07-01", "status": "no-log-trend-day-one"},
            {"date": "2026-07-02", "status": "no-log-trend-day-two"},
        ],
    }
    source_data["workout_set_intelligence"] = {
        "completed_set_count": 7,
        "exercise_indicators": [
            {
                "exercise_id": "exercise-id-not-for-provider",
                "title": "Workout title not for provider",
                "status": "per-exercise-detail-not-for-provider",
            }
        ],
        "session_summaries": [
            {
                "session_id": "session-id-not-for-provider",
                "summary": "per-session-detail-not-for-provider",
            }
        ],
    }
    source_data["training_execution_summary"] = {
        "completion_rate": 0.8,
        "effort_trend": "steady",
        "completed_execution_count": 5,
        "average_completion": 0.8,
        "planned_vs_actual_rir": "inside range",
        "sets_below_planned_reps": 1,
        "sets_inside_planned_reps": 3,
        "sets_above_planned_reps": 1,
        "incomplete_logging_count": 1,
        "confidence": "Moderate",
    }
    source_data["source_data_gaps"] = [
        "logging is incomplete",
        "logging is incomplete",
        "food logging is incomplete",
    ]
    source_data["limitations"] = [
        "logging is incomplete",
        "one material limitation",
    ]
    payload["limitations"] = ["logging is incomplete", "one material limitation"]
    payload["source_data_gaps"] = [
        "food logging is incomplete",
        "logging is incomplete",
    ]
    return build_cross_domain_coaching_evidence_packet(
        payload=payload,
        approved_brief=_brief(),
        scenario="recovery_limited",
    )


def _assessment_payload(
    packet,
    *,
    priority_order: list[str] | None = None,
    recovery_status: str = "supportive",
    recovery_vetoes: list[str] | None = None,
) -> dict[str, object]:
    action_keys_by_domain: dict[str, list[str]] = {
        "recovery": [],
        "nutrition": [],
        "training": [],
    }
    for action in packet.approved_action_catalog:
        if action.domain in action_keys_by_domain:
            action_keys_by_domain[action.domain].append(action.action_key)

    response: dict[str, object] = {
        "assessment_version": CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION,
        "cross_domain_tensions": [],
        "priority_order": priority_order or ["recovery", "nutrition", "training"],
    }
    for domain in ("recovery", "nutrition", "training"):
        facts = packet.domain_evidence[domain]
        response[domain] = {
            "status": recovery_status if domain == "recovery" else "supportive",
            "confidence": "Moderate",
            "observations": [
                {
                    "text": f"{domain.title()} has usable backend evidence.",
                    "evidence_ids": [facts[0].evidence_id],
                }
            ],
            "selected_action_keys": action_keys_by_domain[domain][:1],
            "veto_action_keys": (recovery_vetoes or []) if domain == "recovery" else [],
        }
    return response


def _run(
    packet,
    responses: list[str],
    *,
    brief: ApprovedCoachBrief | None = None,
    scenario: str = "recovery_limited",
    assessment_provider: str = "mock",
    assessment_model: str = "assessment-test-model",
    narrative_provider: str = "mock",
    narrative_model: str = "narrative-test-model",
):
    calls: list[tuple[str, str]] = []
    approved_brief = brief or _brief(scenario=scenario)

    def assessment_provider_callable(provider_input: str) -> str:
        calls.append(("assessment", provider_input))
        return responses[0]

    def narrative_provider_callable(provider_input: str) -> str:
        calls.append(("narrative", provider_input))
        return responses[1]

    result = run_cross_domain_coaching_preview(
        evidence_packet=packet,
        approved_brief=approved_brief,
        assessment_provider=assessment_provider,
        assessment_model=assessment_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        assessment_prompt="assessment prompt",
        narrative_prompt="narrative prompt",
        assessment_provider_callable=assessment_provider_callable,
        narrative_provider_callable=narrative_provider_callable,
    )
    return result, calls


def _valid_assessment_json(packet, **kwargs: object) -> str:
    return json.dumps(_assessment_payload(packet, **kwargs))


def _passing_narrative_json() -> str:
    return json.dumps(
        {
            "headline": "A measured day",
            "body": (
                "Work through what is planned with two to four reps left in reserve, "
                "then log how it went. Canned tuna can help with protein if that still "
                "needs attention."
            ),
        }
    )


def _narrative_input_with_provider_prose(packet) -> str:
    payload = _assessment_payload(packet)
    payload["recovery"]["observations"][0]["text"] = (
        "SPECIALIST OBSERVATION: recovery prose must not cross the call boundary."
    )
    payload["cross_domain_tensions"] = [
        {
            "domains": ["recovery", "training"],
            "summary": "SPECIALIST TENSION: prose must not cross the call boundary.",
            "evidence_ids": [
                packet.domain_evidence["recovery"][0].evidence_id,
                packet.domain_evidence["training"][0].evidence_id,
            ],
        }
    ]
    assessment = parse_cross_domain_specialist_assessment(json.dumps(payload), packet)
    resolved = resolve_cross_domain_coaching_brief(
        evidence_packet=packet,
        assessment=assessment,
    )
    confidence_policy = build_narrative_confidence_policy(
        evidence_packet=packet,
        resolved_brief=resolved,
    )
    semantic_context = build_provider_safe_narrative_context(
        approved_brief=_brief(),
        assessment_context=_assessment_context(packet),
        assessment=assessment,
        resolved_brief=resolved,
        confidence_policy=confidence_policy,
    )
    return build_narrative_provider_input(
        "narrative prompt",
        semantic_narrative_context=semantic_context,
    )


def _confidence_policy_case(
    *,
    primary_domain: str = "recovery",
    confidence: str = "Limited",
    limitations: tuple[str, ...] = ("recovery check-in coverage is limited",),
    source_data_gaps: tuple[str, ...] = ("recovery check-in coverage is limited",),
):
    packet = replace(
        _packet(),
        limitations=limitations,
        source_data_gaps=source_data_gaps,
        overall_confidence=confidence,
    )
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(packet), packet
    )
    resolved = replace(
        resolve_cross_domain_coaching_brief(
            evidence_packet=packet,
            assessment=assessment,
        ),
        primary_domain=primary_domain,
        confidence=confidence,
    )
    return (
        packet,
        resolved,
        build_narrative_confidence_policy(
            evidence_packet=packet,
            resolved_brief=resolved,
        ),
    )


def test_evidence_packet_is_deterministic_for_same_payload() -> None:
    assert _packet().to_dict() == _packet().to_dict()


def test_assessment_context_is_deterministic_and_preserves_full_packet() -> None:
    packet = _rich_packet()
    packet_before = packet.to_dict()
    assert (
        _assessment_context(packet).to_dict() == _assessment_context(packet).to_dict()
    )
    assert packet.to_dict() == packet_before


def test_assessment_context_ids_are_from_the_full_evidence_packet() -> None:
    packet = _rich_packet()
    full_ids = {
        fact.evidence_id for facts in packet.domain_evidence.values() for fact in facts
    }
    context_ids = {
        fact.evidence_id
        for facts in _assessment_context(packet).domain_evidence.values()
        for fact in facts
    }
    assert context_ids <= full_ids


def test_assessment_context_applies_domain_and_total_fact_caps() -> None:
    context = _assessment_context(_rich_packet())
    assert context.context_version == CROSS_DOMAIN_ASSESSMENT_CONTEXT_VERSION
    assert len(context.domain_evidence["recovery"]) <= 8
    assert len(context.domain_evidence["nutrition"]) <= 8
    assert len(context.domain_evidence["training"]) <= 10
    assert len(context.domain_evidence["shared/data-quality"]) <= 5
    assert sum(len(facts) for facts in context.domain_evidence.values()) <= 31


def test_assessment_context_excludes_recovery_metadata_and_window_facts() -> None:
    packet = _rich_packet()
    full_paths = {
        fact.evidence_id: fact.source_path
        for facts in packet.domain_evidence.values()
        for fact in facts
    }
    selected_paths = [
        full_paths[fact.evidence_id]
        for fact in _assessment_context(packet).domain_evidence["recovery"]
    ]
    assert not any(
        token in path
        for path in selected_paths
        for token in (
            "model_version",
            "source_table",
            "user_id",
            "target_date",
            "window",
        )
    )


def test_assessment_context_excludes_nutrition_trend_day_rows() -> None:
    packet = _rich_packet()
    full_paths = {
        fact.evidence_id: fact.source_path
        for fact in packet.domain_evidence["nutrition"]
    }
    selected_paths = [
        full_paths[fact.evidence_id]
        for fact in _assessment_context(packet).domain_evidence["nutrition"]
    ]
    assert not any("trend_days[" in path for path in selected_paths)


def test_assessment_context_excludes_training_detail_rows() -> None:
    packet = _rich_packet()
    full_paths = {
        fact.evidence_id: fact.source_path
        for fact in packet.domain_evidence["training"]
    }
    selected_paths = [
        full_paths[fact.evidence_id]
        for fact in _assessment_context(packet).domain_evidence["training"]
    ]
    assert not any("exercise_indicators" in path for path in selected_paths)
    assert not any("session_summaries" in path for path in selected_paths)


def test_assessment_context_deduplicates_display_values_deterministically() -> None:
    context = _assessment_context(_rich_packet())
    for facts in context.domain_evidence.values():
        values = [" ".join(fact.display_value.lower().split()) for fact in facts]
        assert len(values) == len(set(values))


def test_assessment_context_keeps_only_specialist_selectable_actions() -> None:
    packet = _packet()
    context = _assessment_context(packet)
    assert set(context.selectable_actions) == {"recovery", "nutrition", "training"}
    selectable_keys = {
        action.action_key
        for actions in context.selectable_actions.values()
        for action in actions
    }
    assert all(not key.startswith("limitation:") for key in selectable_keys)
    assert all(
        item.domain != "shared/data-quality" for item in packet.approved_action_catalog
    )


def test_selectable_action_support_uses_only_its_approved_claim_keys() -> None:
    packet = _packet()
    context = _assessment_context(packet)
    recovery_action = context.selectable_actions["recovery"][0]
    catalog_action = next(
        action
        for action in packet.approved_action_catalog
        if action.action_key == recovery_action.action_key
    )
    assert [claim.claim_key for claim in recovery_action.supporting_claims] == [
        "recovery.readiness_level"
    ]
    assert {claim.claim_key for claim in recovery_action.supporting_claims} <= set(
        catalog_action.source_claim_keys
    )


def test_selectable_action_support_comes_only_from_the_claim_registry() -> None:
    brief = replace(
        _brief(),
        claim_registry={
            "recovery.readiness_level": {
                "value": "high",
                "display_value": "High readiness",
                "user_facing_allowed": True,
                "confidence": "High",
            },
            "unrelated.claim": {
                "display_value": "Do not include",
                "user_facing_allowed": True,
                "confidence": "High",
            },
        },
    )
    action = _assessment_context(_packet(), brief).selectable_actions["recovery"][0]
    assert [claim.claim_key for claim in action.supporting_claims] == [
        "recovery.readiness_level"
    ]
    assert action.supporting_claims[0].value == "high"
    assert action.supporting_claims[0].display_value is None


def test_non_user_facing_or_missing_action_support_claims_are_skipped() -> None:
    brief = replace(
        _brief(),
        claim_registry={
            "recovery.readiness_level": {
                "display_value": "Do not include",
                "user_facing_allowed": False,
                "confidence": "High",
            }
        },
    )
    context = _assessment_context(_packet(), brief)
    assert context.selectable_actions["recovery"][0].supporting_claims == ()
    assert context.selectable_actions["nutrition"][0].supporting_claims == ()


def test_prose_bearing_action_support_claim_is_skipped() -> None:
    brief = replace(
        _brief(),
        approved_training_actions=(
            ApprovedTrainingAction(
                claim_keys=("training.rir_range", "training.instruction"),
                instruction="Legacy instruction is not provider data.",
            ),
        ),
        claim_registry={
            **_brief().claim_registry,
            "training.instruction": {
                "value": "Train as planned and stop before the set becomes a grind.",
                "display_value": (
                    "Train as planned and stop before the set becomes a grind."
                ),
                "user_facing_allowed": True,
                "confidence": "High",
            },
        },
    )
    packet = _packet_for_brief(brief)
    training_action = _assessment_context(packet, brief).selectable_actions["training"][
        0
    ]
    assert [claim.claim_key for claim in training_action.supporting_claims] == [
        "training.rir_range"
    ]


def test_assessment_context_keeps_material_limitations_separate_from_actions() -> None:
    context = _assessment_context(_rich_packet())
    assert {item.code for item in context.material_limitations} == {
        "logging_incomplete",
        "material_limitation_present",
    }
    assert {item.code for item in context.source_data_gaps} == {
        "logging_incomplete",
        "food_logging_incomplete",
    }
    assert len(context.material_limitations) <= 5
    assert len(context.source_data_gaps) <= 5
    assert all(
        not claim.claim_key.startswith("limitations.")
        for actions in context.selectable_actions.values()
        for action in actions
        for claim in action.supporting_claims
    )


def test_assessment_provider_input_contains_only_bounded_provider_safe_context() -> (
    None
):
    provider_input = build_specialist_provider_input(
        "assessment prompt",
        _assessment_context(_rich_packet()),
    )
    assert "CROSS-DOMAIN EVIDENCE PACKET" not in provider_input
    assert '"source_path"' not in provider_input
    assert "recovery-source-table" not in provider_input
    assert "internal-user-id" not in provider_input
    assert "exercise-id-not-for-provider" not in provider_input
    assert (
        "Recent recovery signals look supportive based on logged sleep, energy, and "
        "soreness."
    ) not in provider_input
    assert (
        "Recent recovery indicators look supportive with usable check-in coverage."
        not in provider_input
    )
    assert (
        "Bodyweight trend is available but based on limited weigh-ins."
        not in provider_input
    )
    assert "logging is incomplete" not in provider_input


def test_assessment_provider_input_has_complete_concrete_domain_examples() -> None:
    provider_input = build_specialist_provider_input(
        "assessment prompt",
        _assessment_context(_packet()),
    )
    response_text = provider_input.split(
        "=== REQUIRED JSON RESPONSE EXAMPLE ===\n", maxsplit=1
    )[1].split("\n\nReturn one JSON object only.", maxsplit=1)[0]
    response_example = json.loads(response_text)
    for domain in ("recovery", "nutrition", "training"):
        assert response_example[domain] == {
            "status": "supportive",
            "confidence": "Moderate",
            "observations": [],
            "selected_action_keys": [],
            "veto_action_keys": [],
        }
    assert "same shape as recovery" not in provider_input


def test_narrative_confidence_policy_is_deterministic() -> None:
    packet, resolved, policy = _confidence_policy_case()
    assert (
        policy.to_dict()
        == build_narrative_confidence_policy(
            evidence_packet=packet,
            resolved_brief=resolved,
        ).to_dict()
    )


def test_limited_or_low_confidence_preserves_structured_uncertainty() -> None:
    for confidence in ("Limited", "Low"):
        _, _, policy = _confidence_policy_case(confidence=confidence)
        assert policy.resolved_confidence == confidence
        assert {item.code for item in policy.material_limitations} == {
            "recovery_data_incomplete"
        }
        assert "limited_resolved_confidence" in policy.reason_codes
        assert set(policy.to_dict()) == {
            "resolved_confidence",
            "primary_domain",
            "material_limitations",
            "source_data_gaps_preserved",
            "forbidden_certainty_phrases",
            "reason_codes",
        }


def test_moderate_or_high_confidence_without_limitations_has_no_certainty_ban() -> None:
    for confidence in ("Moderate", "High"):
        _, _, policy = _confidence_policy_case(
            confidence=confidence,
            limitations=(),
            source_data_gaps=(),
        )
        assert policy.material_limitations == ()
        assert policy.forbidden_certainty_phrases == ()


def test_confidence_policy_preserves_limitations_for_each_primary_domain() -> None:
    cases = (
        ("recovery", ("recovery check-in coverage is limited",)),
        ("nutrition", ("nutrition logging is incomplete",)),
        ("training", ("workout logging is incomplete",)),
        ("shared/data-quality", ("some source data is incomplete",)),
    )
    for primary_domain, limitations in cases:
        _, _, policy = _confidence_policy_case(
            primary_domain=primary_domain,
            limitations=limitations,
            source_data_gaps=limitations,
        )
        assert policy.primary_domain == primary_domain
        assert policy.material_limitations


def test_narrative_provider_input_contains_structured_uncertainty_and_action_support() -> (
    None
):
    packet, resolved, policy = _confidence_policy_case()
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(packet), packet
    )
    semantic_context = build_provider_safe_narrative_context(
        approved_brief=_brief(),
        assessment_context=_assessment_context(packet),
        assessment=assessment,
        resolved_brief=resolved,
        confidence_policy=policy,
    )
    provider_input = build_narrative_provider_input(
        "narrative prompt",
        semantic_narrative_context=semantic_context,
    )
    assert '"context_version"' in provider_input
    assert '"resolved_decision"' in provider_input
    assert '"approved_facts"' in provider_input
    assert '"material_limitations"' in provider_input
    assert '"source_data_gaps"' in provider_input
    assert '"recovery.readiness_level"' in provider_input
    assert '"forbidden_certainty_phrases"' not in provider_input


def test_both_provider_inputs_exclude_legacy_prose_contract() -> None:
    brief = _legacy_prose_brief()
    packet = _packet_for_brief(brief)
    result, calls = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        brief=brief,
    )
    assert result.disposition == "APPROVED_PREVIEW"
    assert [kind for kind, _ in calls] == ["assessment", "narrative"]
    forbidden_keys = {
        "today_intent",
        "approved_interpretations",
        "approved_training_actions",
        "approved_recovery_interpretations",
        "instruction",
        "interpretation",
        "allowed_phrasings",
        "blocked_phrasings",
        "recommended_focus",
        "desired_coaching_move",
        "coach_safe_summary",
    }
    leaked_sentences = (
        "Recovery looks good enough to train as planned.",
        (
            "Train as planned, keep a couple reps in reserve, and stop before the set "
            "turns into a grind."
        ),
        "Use canned tuna if the protein gap is still open.",
        (
            "Do the planned workout, log what you actually eat, then handle the "
            "protein gap with an approved food option."
        ),
        ("Use an approved food option if the matching nutrition gap is still open."),
        (
            "Recent recovery signals look supportive based on logged sleep, energy, "
            "and soreness."
        ),
    )
    for _, provider_input in calls:
        assert all(f'"{key}"' not in provider_input for key in forbidden_keys)
        assert all(sentence not in provider_input for sentence in leaked_sentences)
    assert '"approved_coach_brief"' not in calls[1][1]


def test_semantic_narrative_context_is_bounded_and_keeps_approved_data() -> None:
    packet = _packet()
    result, calls = _run(
        packet, [_valid_assessment_json(packet), _passing_narrative_json()]
    )
    context = result.semantic_narrative_context
    assert context is not None
    assert context["context_version"] == CROSS_DOMAIN_SEMANTIC_NARRATIVE_CONTEXT_VERSION
    assert set(context["resolved_decision"]) == {
        "primary_domain",
        "primary_action",
        "supporting_actions",
        "suppressed_action_keys",
        "resolution_reason_codes",
    }
    facts = context["approved_facts"]
    assert len(facts["recovery"]) <= 6
    assert len(facts["nutrition"]) <= 8
    assert len(facts["training"]) <= 6
    assert "canned tuna" in calls[1][1]
    assert '"value": "2-4"' in calls[1][1]
    assert {
        "text",
        "copy",
        "sentence",
        "phrasing",
        "approved_coach_brief",
    }.isdisjoint(_nested_keys(context))


def test_narrative_prompt_preserves_provider_wording_freedom() -> None:
    prompt = Path("docs/provider_trials/cross_domain_narrative_prompt_v1.md").read_text(
        encoding="utf-8"
    )
    assert "Choose your own wording" in prompt
    assert "verbatim" not in prompt
    assert "Recent recovery check-in coverage" not in prompt


def test_confidence_coherence_accepts_different_natural_phrasings_without_qualifier() -> (
    None
):
    _, _, policy = _confidence_policy_case()
    for body in (
        "Keep today's plan measured and log how it goes.",
        "A steady session and a simple meal are enough today.",
    ):
        draft = parse_natural_coach_draft(
            json.dumps({"headline": "A measured read", "body": body}),
            provider="mock",
            model="test-model",
        )
        audit = audit_cross_domain_narrative_confidence_coherence(
            draft=draft,
            confidence_policy=policy,
        )
        assert audit.passed is True
        assert audit.findings == ()


def test_confidence_coherence_allows_irrelevant_domains_to_be_omitted() -> None:
    _, _, policy = _confidence_policy_case()
    draft = parse_natural_coach_draft(
        json.dumps({"headline": "A measured read", "body": "Keep the plan measured."}),
        provider="mock",
        model="test-model",
    )
    assert (
        audit_cross_domain_narrative_confidence_coherence(
            draft=draft,
            confidence_policy=policy,
        ).passed
        is True
    )


def test_confidence_coherence_rejects_certainty_escalation_but_not_strong_metrics() -> (
    None
):
    _, _, policy = _confidence_policy_case()
    violating_draft = parse_natural_coach_draft(
        json.dumps(
            {
                "headline": "A measured read",
                "body": "You are definitely ready today.",
            }
        ),
        provider="mock",
        model="test-model",
    )
    violating_audit = audit_cross_domain_narrative_confidence_coherence(
        draft=violating_draft,
        confidence_policy=policy,
    )
    assert violating_audit.certainty_violation_count == 1
    assert violating_audit.passed is False

    strong_metric_draft = parse_natural_coach_draft(
        json.dumps(
            {
                "headline": "A measured read",
                "body": "Recovery score is 100%.",
            }
        ),
        provider="mock",
        model="test-model",
    )
    assert (
        audit_cross_domain_narrative_confidence_coherence(
            draft=strong_metric_draft,
            confidence_policy=policy,
        ).passed
        is True
    )


def test_confidence_coherence_rejects_source_data_gap_denial() -> None:
    _, _, policy = _confidence_policy_case()
    draft = parse_natural_coach_draft(
        json.dumps(
            {
                "headline": "A measured read",
                "body": "All data is complete.",
            }
        ),
        provider="mock",
        model="test-model",
    )
    audit = audit_cross_domain_narrative_confidence_coherence(
        draft=draft,
        confidence_policy=policy,
    )
    assert "source_data_gap_denial:all data is complete" in audit.findings


def test_confidence_coherence_rejects_direct_material_limitation_denial() -> None:
    _, _, policy = _confidence_policy_case()
    draft = parse_natural_coach_draft(
        json.dumps(
            {
                "headline": "A measured read",
                "body": "There are no limitations today.",
            }
        ),
        provider="mock",
        model="test-model",
    )
    audit = audit_cross_domain_narrative_confidence_coherence(
        draft=draft,
        confidence_policy=policy,
    )
    assert "material_limitation_denial:no limitations" in audit.findings


def test_dynamic_assessment_schema_restricts_versions_status_and_confidence() -> None:
    schema = build_specialist_response_schema(_assessment_context(_packet()))
    properties = schema["properties"]
    assert properties["assessment_version"]["const"] == (
        CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION
    )
    recovery_properties = properties["recovery"]["properties"]
    assert recovery_properties["status"]["enum"] == sorted(
        {"supportive", "caution", "limiting", "unknown"}
    )
    assert recovery_properties["confidence"]["enum"] == [
        "Limited",
        "Low",
        "Moderate",
        "High",
    ]


def test_dynamic_assessment_schema_restricts_domain_action_and_evidence_ids() -> None:
    context = _assessment_context(_packet())
    schema = build_specialist_response_schema(context)
    for domain in ("recovery", "nutrition", "training"):
        domain_properties = schema["properties"][domain]["properties"]
        assert domain_properties["selected_action_keys"]["items"]["enum"] == [
            action.action_key for action in context.selectable_actions[domain]
        ]
        assert domain_properties["veto_action_keys"]["items"]["enum"] == [
            action.action_key for action in context.selectable_actions[domain]
        ]
        observation = domain_properties["observations"]["items"]
        assert observation["properties"]["evidence_ids"]["items"]["enum"] == [
            fact.evidence_id for fact in context.domain_evidence[domain]
        ]


def test_dynamic_assessment_schema_restricts_priorities_and_tension_evidence() -> None:
    context = _assessment_context(_packet())
    schema = build_specialist_response_schema(context)
    priority_order = schema["properties"]["priority_order"]
    assert priority_order["items"]["enum"] == ["recovery", "nutrition", "training"]
    assert priority_order["minItems"] == priority_order["maxItems"] == 3
    assert priority_order["uniqueItems"] is True
    tension = schema["properties"]["cross_domain_tensions"]
    assert tension["maxItems"] == 3
    expected_ids = [
        fact.evidence_id
        for domain in ("recovery", "nutrition", "training")
        for fact in context.domain_evidence[domain]
    ]
    assert (
        tension["items"]["properties"]["evidence_ids"]["items"]["enum"] == expected_ids
    )


def test_dynamic_schema_requires_empty_action_lists_without_domain_actions() -> None:
    packet = _packet()
    without_recovery_actions = replace(
        packet,
        approved_action_catalog=tuple(
            action
            for action in packet.approved_action_catalog
            if action.domain != "recovery"
        ),
    )
    schema = build_specialist_response_schema(
        _assessment_context(without_recovery_actions)
    )
    recovery_properties = schema["properties"]["recovery"]["properties"]
    assert recovery_properties["selected_action_keys"]["maxItems"] == 0
    assert recovery_properties["veto_action_keys"]["maxItems"] == 0


def test_only_authorized_source_sections_become_evidence() -> None:
    facts = [
        fact
        for domain_facts in _packet().domain_evidence.values()
        for fact in domain_facts
    ]
    assert facts
    assert all("unapproved_section" not in fact.source_path for fact in facts)
    assert all(fact.value != "must not become evidence" for fact in facts)


def test_provider_facing_action_models_have_no_prose_field() -> None:
    forbidden_fields = {"text", "copy", "sentence", "phrasing"}
    for model in (
        ApprovedActionCatalogItem,
        CrossDomainSelectableAction,
        ResolvedCoachingAction,
    ):
        assert forbidden_fields.isdisjoint(field.name for field in fields(model))


def test_semantic_actions_do_not_depend_on_legacy_action_prose() -> None:
    original_brief = _brief()
    prose_mutated_brief = replace(
        original_brief,
        approved_training_actions=(
            replace(
                original_brief.approved_training_actions[0],
                instruction="Completely different legacy training sentence.",
                allowed_phrasings=("Another legacy training sentence.",),
            ),
        ),
        approved_recovery_interpretations=(
            replace(
                original_brief.approved_recovery_interpretations[0],
                interpretation="Completely different legacy recovery sentence.",
                allowed_phrasings=("Another legacy recovery sentence.",),
            ),
        ),
    )
    assert (
        _packet_for_brief(original_brief).approved_action_catalog
        == _packet_for_brief(prose_mutated_brief).approved_action_catalog
    )


def test_training_rir_parameters_come_from_approved_claim_data() -> None:
    brief = replace(
        _brief(),
        approved_training_actions=(
            ApprovedTrainingAction(
                claim_keys=("training.rir_range",),
                instruction="Legacy prose deliberately contains 8 and 12.",
            ),
        ),
        claim_registry={
            **_brief().claim_registry,
            "training.rir_range": {
                "value": {"min": 1, "max": 3},
                "display_value": "1-3",
                "user_facing_allowed": True,
                "confidence": "High",
            },
        },
    )
    training_action = next(
        action
        for action in _packet_for_brief(brief).approved_action_catalog
        if action.domain == "training"
    )
    assert training_action.parameters["rir_range"] == {"min": 1, "max": 3}


def test_approved_action_catalog_contains_only_approved_brief_actions() -> None:
    catalog = _packet().approved_action_catalog
    assert [item.action_key for item in catalog] == [
        "recovery:maintain_planned_training",
        "nutrition_food:nutrition.food_suggestion.1.friendly_name",
        "training:execute_planned_session",
    ]
    assert {item.action_type for item in catalog} == {
        "maintain_planned_training",
        "consider_food_candidate",
        "execute_planned_session",
    }
    assert all("text" not in item.to_dict() for item in catalog)
    assert catalog[0].parameters == {
        "intensity_change": "none",
        "max_effort_test": False,
    }
    assert catalog[1].parameters == {
        "friendly_name": "canned tuna",
        "macro_reason": "protein",
        "serving_display": None,
        "serving_allowed": False,
    }
    assert catalog[2].parameters == {
        "avoid_grinding_reps": True,
        "max_effort_test": False,
        "rir_range": {"min": 2, "max": 4},
    }


def test_assessment_selectable_actions_are_semantic_and_prose_free() -> None:
    context = _assessment_context(_packet())
    actions = [
        action
        for domain_actions in context.selectable_actions.values()
        for action in domain_actions
    ]
    assert actions
    assert all(action.action_type and action.parameters for action in actions)
    assert all(
        {"text", "copy", "sentence", "phrasing"}.isdisjoint(action.to_dict())
        for action in actions
    )


def test_valid_structured_specialist_json_parses() -> None:
    packet = _packet()
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(packet), packet
    )
    assert assessment.recovery.status == "supportive"
    assert assessment.nutrition.selected_action_keys
    assert assessment.training.observations


def test_markdown_wrapped_specialist_json_is_rejected() -> None:
    packet = _packet()
    raw = f"```json\n{_valid_assessment_json(packet)}\n```"
    with pytest.raises(SpecialistAssessmentValidationError, match="Markdown"):
        parse_cross_domain_specialist_assessment(raw, packet)


def test_unknown_evidence_id_is_rejected() -> None:
    packet = _packet()
    payload = _assessment_payload(packet)
    payload["recovery"]["observations"][0]["evidence_ids"] = ["evidence:unknown"]
    with pytest.raises(SpecialistAssessmentValidationError, match="Unknown evidence"):
        parse_cross_domain_specialist_assessment(json.dumps(payload), packet)


def test_unknown_action_key_is_rejected() -> None:
    packet = _packet()
    payload = _assessment_payload(packet)
    payload["training"]["selected_action_keys"] = ["training:unknown"]
    with pytest.raises(SpecialistAssessmentValidationError, match="Unknown action"):
        parse_cross_domain_specialist_assessment(json.dumps(payload), packet)


def test_cross_domain_action_selection_is_rejected() -> None:
    packet = _packet()
    payload = _assessment_payload(packet)
    payload["nutrition"]["selected_action_keys"] = ["training:execute_planned_session"]
    with pytest.raises(SpecialistAssessmentValidationError, match="another domain"):
        parse_cross_domain_specialist_assessment(json.dumps(payload), packet)
    payload = _assessment_payload(packet)
    payload["recovery"]["action_text"] = "Add another set."
    with pytest.raises(SpecialistAssessmentValidationError, match="exactly"):
        parse_cross_domain_specialist_assessment(json.dumps(payload), packet)


def test_invalid_priority_order_is_rejected() -> None:
    packet = _packet()
    with pytest.raises(SpecialistAssessmentValidationError, match="priority_order"):
        parse_cross_domain_specialist_assessment(
            _valid_assessment_json(
                packet, priority_order=["recovery", "recovery", "training"]
            ),
            packet,
        )


def test_invalid_specialist_output_prevents_narrative_call() -> None:
    packet = _packet()
    result, calls = _run(packet, ["not valid JSON", _passing_narrative_json()])
    assert result.disposition == "REJECTED_SPECIALIST_ASSESSMENT"
    assert result.provider_call_count == 1
    assert len(calls) == 1


def test_scenario_precedence_overrides_specialist_priority() -> None:
    packet = _packet(scenario="recovery_limited")
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(
            packet,
            priority_order=["nutrition", "training", "recovery"],
        ),
        packet,
    )
    resolved = resolve_cross_domain_coaching_brief(
        evidence_packet=packet,
        assessment=assessment,
    )
    assert resolved.primary_domain == "recovery"
    assert (
        resolved.primary_action
        and resolved.primary_action.action_key == "recovery:maintain_planned_training"
    )


def test_recovery_veto_suppresses_conflicting_training_emphasis() -> None:
    packet = _packet()
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(
            packet,
            recovery_status="caution",
            recovery_vetoes=["training:execute_planned_session"],
        ),
        packet,
    )
    resolved = resolve_cross_domain_coaching_brief(
        evidence_packet=packet,
        assessment=assessment,
    )
    assert "training:execute_planned_session" in {
        item.action_key for item in resolved.suppressed_actions
    }
    assert "training:execute_planned_session" not in {
        item.action_key
        for item in (resolved.primary_action, *resolved.supporting_actions)
        if item
    }


def test_resolver_preserves_only_catalog_semantics() -> None:
    packet = _packet()
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(packet), packet
    )
    resolved = resolve_cross_domain_coaching_brief(
        evidence_packet=packet,
        assessment=assessment,
    )
    catalog_semantics = {
        item.action_key: (item.action_type, item.parameters)
        for item in packet.approved_action_catalog
    }
    actions = [
        item for item in (resolved.primary_action, *resolved.supporting_actions) if item
    ]
    assert actions
    assert all(
        catalog_semantics.get(action.action_key)
        == (action.action_type, action.parameters)
        for action in actions
    )
    assert all("text" not in action.to_dict() for action in actions)


def test_narrative_json_parses_into_natural_coach_draft() -> None:
    draft = parse_natural_coach_draft(
        _passing_narrative_json(), provider="mock", model="test-model"
    )
    assert draft.provider == "deterministic"
    assert draft.headline == "A measured day"


def test_existing_claim_audit_runs() -> None:
    packet = _packet()
    result, _ = _run(
        packet, [_valid_assessment_json(packet), _passing_narrative_json()]
    )
    assert result.claim_audit_result is not None


def test_existing_product_voice_audit_runs() -> None:
    packet = _packet()
    result, _ = _run(
        packet, [_valid_assessment_json(packet), _passing_narrative_json()]
    )
    assert result.product_voice_audit_result is not None


def test_failed_claim_audit_yields_rejected_disposition() -> None:
    packet = _packet()
    narrative = json.dumps(
        {
            "headline": "A hard stop",
            "body": "You are underfed today, so do the planned session anyway.",
        }
    )
    result, _ = _run(packet, [_valid_assessment_json(packet), narrative])
    assert result.disposition == "REJECTED_CLAIM_AUDIT"
    assert result.claim_audit_result and not result.claim_audit_result.passed


def test_claim_audit_takes_precedence_over_confidence_coherence() -> None:
    packet, _, _ = _confidence_policy_case()
    narrative = json.dumps(
        {
            "headline": "A hard stop",
            "body": "You are underfed today, so do the planned session anyway.",
        }
    )
    result, _ = _run(packet, [_valid_assessment_json(packet), narrative])
    assert result.claim_audit_result and not result.claim_audit_result.passed
    assert result.confidence_coherence_audit_result
    assert result.confidence_coherence_audit_result.passed is True
    assert result.disposition == "REJECTED_CLAIM_AUDIT"


def test_coherence_failure_has_a_distinct_disposition() -> None:
    packet, _, _ = _confidence_policy_case()
    narrative = json.dumps(
        {
            "headline": "A measured day",
            "body": "You are definitely ready today.",
        }
    )
    result, _ = _run(
        packet,
        [_valid_assessment_json(packet), narrative],
    )
    assert result.claim_audit_result and result.claim_audit_result.passed
    assert result.confidence_coherence_audit_result
    assert result.confidence_coherence_audit_result.passed is False
    assert result.disposition == "REJECTED_CONFIDENCE_COHERENCE"


def test_failed_product_voice_audit_yields_rejected_disposition() -> None:
    packet = _packet()
    narrative = json.dumps(
        {
            "headline": "Keep it simple",
            "body": (
                "Available options can keep the day simple, so log the session and "
                "keep the rest of the day measured without chasing a bigger change."
            ),
        }
    )
    result, _ = _run(packet, [_valid_assessment_json(packet), narrative])
    assert result.claim_audit_result and result.claim_audit_result.passed
    assert result.disposition == "REJECTED_PRODUCT_VOICE"
    assert (
        result.product_voice_audit_result
        and not result.product_voice_audit_result.passed
    )


def test_product_voice_failure_follows_a_passing_coherence_audit() -> None:
    packet, _, _ = _confidence_policy_case()
    narrative = json.dumps(
        {
            "headline": "Keep it simple",
            "body": (
                "Available options can keep the day simple, so log the session and "
                "keep the rest of the day measured without chasing a bigger change."
            ),
        }
    )
    result, _ = _run(packet, [_valid_assessment_json(packet), narrative])
    assert result.confidence_coherence_audit_result
    assert result.confidence_coherence_audit_result.passed is True
    assert result.product_voice_audit_result
    assert result.product_voice_audit_result.passed is False
    assert result.disposition == "REJECTED_PRODUCT_VOICE"


def test_successful_mock_two_call_preview_is_approved() -> None:
    packet = _packet()
    result, calls = _run(
        packet, [_valid_assessment_json(packet), _passing_narrative_json()]
    )
    assert result.disposition == "APPROVED_PREVIEW"
    assert len(calls) == 2


def test_successful_mock_preview_with_natural_narrative_is_approved() -> None:
    packet, _, _ = _confidence_policy_case()
    result, _ = _run(
        packet, [_valid_assessment_json(packet), _passing_narrative_json()]
    )
    assert result.confidence_coherence_audit_result
    assert result.confidence_coherence_audit_result.passed is True
    assert result.disposition == "APPROVED_PREVIEW"


@pytest.mark.parametrize(
    ("headline", "body"),
    (
        (
            "A steady path through today",
            (
                "Work through what is planned with two to four reps left in reserve, "
                "then log how it went. Canned tuna can help with protein if that still "
                "needs attention."
            ),
        ),
        (
            "Let the plan set the pace",
            (
                "Leave two to four reps available as you move through today's work. "
                "If protein remains short, canned tuna is a straightforward food to "
                "consider."
            ),
        ),
        (
            "Keep today's work straightforward",
            (
                "Complete the planned work without chasing a maximal effort, and note "
                "what you finish. For the open protein need, canned tuna remains "
                "available."
            ),
        ),
    ),
)
def test_distinct_original_narratives_pass_without_legacy_fragments(
    headline: str,
    body: str,
) -> None:
    packet = _packet()
    narrative = json.dumps({"headline": headline, "body": body})
    result, _ = _run(packet, [_valid_assessment_json(packet), narrative])
    legacy_fragments = (
        "Recovery looks good enough to train as planned",
        "Train as planned, keep a couple reps in reserve",
        "Use canned tuna if the protein gap is still open",
        "Keep the planned session controlled",
        "Keep effort measured while readiness is moderate",
    )
    assert all(fragment not in f"{headline} {body}" for fragment in legacy_fragments)
    assert result.disposition == "APPROVED_PREVIEW"


def test_unapproved_food_still_fails_claim_audit() -> None:
    brief = replace(
        _brief(),
        approved_food_actions=(
            replace(
                _brief().approved_food_actions[0],
                blocked_user_facing_names=("cooked chicken breast",),
            ),
        ),
    )
    packet = _packet_for_brief(brief)
    narrative = json.dumps(
        {
            "headline": "A simple food move",
            "body": (
                "Work through the planned session and log it. Cooked chicken breast "
                "can cover the protein need afterward."
            ),
        }
    )
    result, _ = _run(
        packet,
        [_valid_assessment_json(packet), narrative],
        brief=brief,
    )
    assert result.disposition == "REJECTED_CLAIM_AUDIT"
    assert result.claim_audit_result and not result.claim_audit_result.passed


@pytest.mark.parametrize(
    "body",
    (
        "Have 100 g of canned tuna and then work through the planned session.",
        "Have canned tuna after training and log the planned session.",
        "Add 60 g of protein with canned tuna before you log the planned session.",
    ),
)
def test_invented_serving_timing_or_macro_value_fails_claim_audit(body: str) -> None:
    packet = _packet()
    narrative = json.dumps({"headline": "A specific plan", "body": body})
    result, _ = _run(packet, [_valid_assessment_json(packet), narrative])
    assert result.disposition == "REJECTED_CLAIM_AUDIT"
    assert result.claim_audit_result and not result.claim_audit_result.passed


def test_invented_workout_change_fails_claim_audit() -> None:
    packet = _packet()
    narrative = json.dumps(
        {
            "headline": "A bigger session",
            "body": (
                "Add a set to the planned workout, then log the result and consider "
                "canned tuna for protein."
            ),
        }
    )
    result, _ = _run(packet, [_valid_assessment_json(packet), narrative])
    assert result.disposition == "REJECTED_CLAIM_AUDIT"
    assert result.claim_audit_result
    assert any(
        finding.finding_type == "unsupported_semantic_action_claim"
        for finding in result.claim_audit_result.findings
    )


def test_provider_failure_is_safe_and_sanitized() -> None:
    packet = _packet()

    def failing_provider(_: str) -> str:
        raise RuntimeError("provider rejected sk-secret-preview-key")

    result = run_cross_domain_coaching_preview(
        evidence_packet=packet,
        approved_brief=_brief(),
        assessment_provider="mock",
        assessment_model="assessment-test-model",
        narrative_provider="mock",
        narrative_model="narrative-test-model",
        assessment_prompt="assessment prompt",
        narrative_prompt="narrative prompt",
        assessment_provider_callable=failing_provider,
    )
    assert result.disposition == "PROVIDER_FAILURE"
    assert result.error_message and "sk-secret-preview-key" not in result.error_message
    assert "[redacted]" in result.error_message


def test_preview_writes_no_files_without_an_output_directory(tmp_path) -> None:
    packet = _packet()
    _run(packet, [_valid_assessment_json(packet), _passing_narrative_json()])
    assert list(tmp_path.iterdir()) == []


def test_output_artifacts_contain_no_secret_like_values(tmp_path) -> None:
    packet = _packet()
    result, _ = _run(
        packet, [_valid_assessment_json(packet), _passing_narrative_json()]
    )
    output_dir = tmp_path / "preview"
    write_preview_artifacts(
        output_dir=output_dir,
        result=result,
        assessment_provider_input="prompt sk-secret-preview-key",
        narrative_provider_input="narrative sk-secret-preview-key",
        run_config={"token": "sk-secret-preview-key"},
    )
    contents = "\n".join(
        path.read_text(encoding="utf-8") for path in output_dir.iterdir()
    )
    assert "sk-secret-preview-key" not in contents
    assert "[redacted]" in contents


def test_preview_does_not_mutate_the_database(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "preview_contract.db"
    db_path.write_bytes(b"unchanged temporary database")
    monkeypatch.setattr(database, "DB_PATH", db_path)
    packet = _packet()
    _run(packet, [_valid_assessment_json(packet), _passing_narrative_json()])
    assert db_path.read_bytes() == b"unchanged temporary database"


def test_exactly_two_provider_calls_occur_on_success() -> None:
    packet = _packet()
    result, calls = _run(
        packet, [_valid_assessment_json(packet), _passing_narrative_json()]
    )
    assert result.provider_call_count == 2
    assert len(calls) == 2


def test_exactly_one_provider_call_occurs_when_specialist_validation_fails() -> None:
    packet = _packet()
    result, calls = _run(packet, ["{}", _passing_narrative_json()])
    assert result.provider_call_count == 1
    assert len(calls) == 1


def test_assessment_and_narrative_providers_may_differ() -> None:
    packet = _packet()
    result, _ = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        assessment_provider="direct_ollama",
        narrative_provider="openai",
    )
    assert result.assessment_provider == "direct_ollama"
    assert result.narrative_provider == "openai"


def test_assessment_and_narrative_models_may_differ() -> None:
    packet = _packet()
    result, _ = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        assessment_model="assessment-model",
        narrative_model="narrative-model",
    )
    assert result.assessment_model == "assessment-model"
    assert result.narrative_model == "narrative-model"


def test_successful_hybrid_preview_calls_providers_in_order() -> None:
    packet = _packet()
    result, calls = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        assessment_provider="direct_ollama",
        narrative_provider="openai",
    )
    assert result.provider_call_count == 2
    assert [stage for stage, _ in calls] == ["assessment", "narrative"]


def test_invalid_assessment_does_not_call_the_narrative_provider() -> None:
    packet = _packet()
    result, calls = _run(packet, ["{}", _passing_narrative_json()])
    assert result.disposition == "REJECTED_SPECIALIST_ASSESSMENT"
    assert [stage for stage, _ in calls] == ["assessment"]


def test_direct_ollama_assessment_mock_response_parses_and_resolves() -> None:
    packet = _packet()
    result, _ = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        assessment_provider="direct_ollama",
        assessment_model="ollama/assessment-model",
    )
    assert result.assessment_model == "assessment-model"
    assert result.specialist_assessment is not None
    assert result.resolved_brief is not None


def test_direct_ollama_narrative_mock_response_reaches_existing_audits() -> None:
    packet = _packet()
    result, _ = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        narrative_provider="direct_ollama",
        narrative_model="ollama/narrative-model",
    )
    assert result.narrative_draft is not None
    assert result.claim_audit_result is not None
    assert result.product_voice_audit_result is not None


def test_direct_ollama_natural_draft_provenance_is_preserved() -> None:
    draft = parse_natural_coach_draft(
        _passing_narrative_json(),
        provider="direct_ollama",
        model="local-model",
    )
    assert draft.provider == "direct_ollama"
    assert draft.model == "local-model"


def test_mock_natural_draft_provenance_remains_deterministic() -> None:
    draft = parse_natural_coach_draft(
        _passing_narrative_json(), provider="mock", model="mock-model"
    )
    assert draft.provider == "deterministic"


def test_openai_natural_draft_provenance_remains_openai() -> None:
    draft = parse_natural_coach_draft(
        _passing_narrative_json(), provider="openai", model="openai-model"
    )
    assert draft.provider == "openai"


def test_narrative_input_excludes_specialist_observation_text() -> None:
    narrative_input = _narrative_input_with_provider_prose(_packet())
    assert "SPECIALIST OBSERVATION" not in narrative_input


def test_narrative_input_excludes_specialist_tension_summary_text() -> None:
    narrative_input = _narrative_input_with_provider_prose(_packet())
    assert "SPECIALIST TENSION" not in narrative_input


def test_narrative_input_excludes_approved_observations() -> None:
    narrative_input = _narrative_input_with_provider_prose(_packet())
    assert "approved_observations" not in narrative_input


def test_narrative_input_keeps_approved_actions_and_resolution() -> None:
    narrative_input = _narrative_input_with_provider_prose(_packet())
    assert "canned tuna" in narrative_input
    assert "resolved_decision" in narrative_input
    assert "resolution_reason_codes" in narrative_input


def test_vetoed_primary_domain_action_is_never_reintroduced() -> None:
    packet = _packet()
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(
            packet, recovery_vetoes=["recovery:maintain_planned_training"]
        ),
        packet,
    )
    resolved = resolve_cross_domain_coaching_brief(
        evidence_packet=packet,
        assessment=assessment,
    )
    resolved_keys = {
        action.action_key
        for action in (resolved.primary_action, *resolved.supporting_actions)
        if action
    }
    assert "recovery:maintain_planned_training" not in resolved_keys
    assert "recovery:maintain_planned_training" in {
        action.action_key for action in resolved.suppressed_actions
    }


def test_vetoed_action_cannot_become_a_supporting_action() -> None:
    packet = _packet()
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(
            packet,
            recovery_vetoes=[
                "nutrition_food:nutrition.food_suggestion.1.friendly_name"
            ],
        ),
        packet,
    )
    resolved = resolve_cross_domain_coaching_brief(
        evidence_packet=packet,
        assessment=assessment,
    )
    assert "nutrition_food:nutrition.food_suggestion.1.friendly_name" not in {
        action.action_key for action in resolved.supporting_actions
    }


def test_recovery_caution_without_veto_keeps_approved_training_action() -> None:
    packet = _packet()
    assessment = parse_cross_domain_specialist_assessment(
        _valid_assessment_json(packet, recovery_status="caution"),
        packet,
    )
    resolved = resolve_cross_domain_coaching_brief(
        evidence_packet=packet,
        assessment=assessment,
    )
    assert "training:execute_planned_session" in {
        action.action_key for action in resolved.supporting_actions
    }
    assert "recovery_constraint_precedence" not in resolved.resolution_reason_codes


def test_artifacts_record_both_provider_and_model_pairs(tmp_path) -> None:
    packet = _packet()
    result, _ = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        assessment_provider="direct_ollama",
        assessment_model="assessment-model",
        narrative_provider="openai",
        narrative_model="narrative-model",
    )
    output_dir = tmp_path / "preview"
    write_preview_artifacts(
        output_dir=output_dir,
        result=result,
        assessment_provider_input="assessment",
        narrative_provider_input="narrative",
        run_config=result.to_dict(),
    )
    rendered = "\n".join(
        path.read_text(encoding="utf-8") for path in output_dir.iterdir()
    )
    assert "assessment-model" in rendered
    assert "narrative-model" in rendered
    assert "direct_ollama" in rendered
    assert "openai" in rendered
    assert (
        json.loads((output_dir / "assessment_context.json").read_text(encoding="utf-8"))
        == result.assessment_context.to_dict()
    )
    assert json.loads(
        (output_dir / "evidence_packet.json").read_text(encoding="utf-8")
    ) == json.loads(json.dumps(result.evidence_packet.to_dict()))
    assert (
        json.loads(
            (output_dir / "confidence_coherence_audit.json").read_text(encoding="utf-8")
        )
        == result.confidence_coherence_audit_result.to_dict()
    )
    assert json.loads(
        (output_dir / "semantic_narrative_context.json").read_text(encoding="utf-8")
    ) == json.loads(json.dumps(result.semantic_narrative_context))


def test_direct_ollama_payload_uses_structured_output_schema(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:11434")
    calls: list[tuple[str, dict[str, object], float]] = []

    def fake_post(
        url: str, payload: dict[str, object], timeout: float
    ) -> dict[str, str]:
        calls.append((url, payload, timeout))
        return {"response": "{}"}

    response = call_direct_ollama_preview(
        provider_input="structured prompt",
        model_name="ollama/local-model",
        response_schema={"type": "object", "properties": {"x": {"type": "string"}}},
        temperature=0,
        timeout_seconds=12,
        http_post=fake_post,
    )
    assert response == "{}"
    assert calls[0][0] == "http://ollama.test:11434/api/generate"
    assert calls[0][1]["stream"] is False
    assert calls[0][1]["format"] == {
        "type": "object",
        "properties": {"x": {"type": "string"}},
    }
    assert calls[0][1]["options"] == {"temperature": 0}
    assert "think" not in calls[0][1]


def test_qwen3_direct_ollama_payload_disables_thinking(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:11434")
    calls: list[dict[str, object]] = []

    def fake_post(_: str, payload: dict[str, object], __: float) -> dict[str, str]:
        calls.append(payload)
        return {"response": "{}"}

    call_direct_ollama_preview(
        provider_input="structured prompt",
        model_name="ollama/qwen3:8b",
        response_schema={"type": "object"},
        temperature=0.2,
        timeout_seconds=12,
        http_post=fake_post,
    )
    assert calls[0]["model"] == "qwen3:8b"
    assert calls[0]["think"] is False


def test_qwen25_direct_ollama_payload_leaves_thinking_unchanged(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:11434")
    calls: list[dict[str, object]] = []

    def fake_post(_: str, payload: dict[str, object], __: float) -> dict[str, str]:
        calls.append(payload)
        return {"response": "{}"}

    call_direct_ollama_preview(
        provider_input="structured prompt",
        model_name="ollama/qwen2.5:3b",
        response_schema={"type": "object"},
        temperature=0.2,
        timeout_seconds=12,
        http_post=fake_post,
    )
    assert calls[0]["model"] == "qwen2.5:3b"
    assert "think" not in calls[0]


def test_direct_ollama_assessment_uses_the_context_generated_schema(
    monkeypatch,
) -> None:
    packet = _packet()
    captured_schemas: list[dict[str, object]] = []

    def fake_ollama(**kwargs: object) -> str:
        captured_schemas.append(cast(dict[str, object], kwargs["response_schema"]))
        return _valid_assessment_json(packet)

    monkeypatch.setattr(preview_service, "call_direct_ollama_preview", fake_ollama)
    result = run_cross_domain_coaching_preview(
        evidence_packet=packet,
        approved_brief=_brief(),
        assessment_provider="direct_ollama",
        assessment_model="local-assessment",
        narrative_provider="mock",
        narrative_model="mock-narrative",
        assessment_prompt="assessment prompt",
        narrative_prompt="narrative prompt",
    )
    expected_schema = build_specialist_response_schema(result.assessment_context)
    assert captured_schemas == [expected_schema]
    assert result.disposition != "PROVIDER_FAILURE"


def test_direct_ollama_provider_error_is_sanitized(monkeypatch) -> None:
    packet = _packet()

    def failing_ollama(**_: object) -> str:
        raise RuntimeError("local provider rejected sk-direct-ollama-secret")

    monkeypatch.setattr(preview_service, "call_direct_ollama_preview", failing_ollama)
    result = run_cross_domain_coaching_preview(
        evidence_packet=packet,
        approved_brief=_brief(),
        assessment_provider="direct_ollama",
        assessment_model="local-model",
        narrative_provider="mock",
        narrative_model="mock-model",
        assessment_prompt="assessment prompt",
        narrative_prompt="narrative prompt",
    )
    assert result.disposition == "PROVIDER_FAILURE"
    assert (
        result.error_message and "sk-direct-ollama-secret" not in result.error_message
    )
    assert "[redacted]" in result.error_message


def test_injected_provider_callables_prevent_live_provider_calls(monkeypatch) -> None:
    packet = _packet()

    def no_live_call(**_: object) -> str:
        raise AssertionError("automated tests must not call a live provider")

    monkeypatch.setattr(preview_service, "call_direct_ollama_preview", no_live_call)
    result, calls = _run(
        packet,
        [_valid_assessment_json(packet), _passing_narrative_json()],
        assessment_provider="direct_ollama",
        narrative_provider="direct_ollama",
    )
    assert result.disposition == "APPROVED_PREVIEW"
    assert [stage for stage, _ in calls] == ["assessment", "narrative"]
