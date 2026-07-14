from __future__ import annotations

import json
import os
import re
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from models.cross_domain_coaching_preview_models import (
    ApprovedActionCatalogItem,
    ConfidenceCoherenceAuditResult,
    ConfidenceLevel,
    CrossDomainAssessmentContext,
    CrossDomainCoachingPreviewResult,
    CrossDomainEvidenceDomain,
    CrossDomainEvidencePacket,
    CrossDomainSemanticCondition,
    CrossDomainSpecialistAssessment,
    CrossDomainTension,
    NarrativeConfidencePolicy,
    NaturalCoachDraft,
    ResolvedCoachingAction,
    ResolvedCrossDomainBrief,
    SpecialistDomain,
    SpecialistDomainAssessment,
    SpecialistObservation,
)
from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,
    ClaimAuditFinding,
    ClaimAuditResult,
)
from services.cross_domain_coaching_evidence_service import (
    build_cross_domain_assessment_context,
    build_cross_domain_coaching_context_for_user,
    build_cross_domain_semantic_conditions,
)
from services.daily_coach_claim_audit_service import audit_extracted_draft_claims
from services.daily_coach_claim_extraction_service import (
    extract_claims_from_natural_draft,
)
from services.daily_coach_product_voice_audit_service import (
    audit_daily_coach_product_voice,
)
from services.openai_human_voice_prompt_preview_service import (
    call_openai_human_voice_prompt_preview,
)
from services.provider_lifecycle_service import (
    build_ollama_generate_payload,
    normalize_ollama_model_name,
    resolve_ollama_base_url,
    resolve_provider_lifecycle_policy,
)

CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION = "cross_domain_specialist_assessment_v1"
RESOLVED_CROSS_DOMAIN_BRIEF_VERSION = "resolved_cross_domain_brief_v1"
CROSS_DOMAIN_COACHING_PREVIEW_RESULT_VERSION = "cross_domain_coaching_preview_result_v1"
CROSS_DOMAIN_SEMANTIC_NARRATIVE_CONTEXT_VERSION = (
    "cross_domain_semantic_narrative_context_v1"
)
SPECIALIST_DOMAINS: tuple[SpecialistDomain, ...] = (
    "recovery",
    "nutrition",
    "training",
)
_CONFIDENCE_ORDER: dict[ConfidenceLevel, int] = {
    "Limited": 0,
    "Low": 1,
    "Moderate": 2,
    "High": 3,
}
_STATUSES = {"supportive", "caution", "limiting", "unknown"}
_ASSESSMENT_KEYS = {
    "assessment_version",
    "recovery",
    "nutrition",
    "training",
    "cross_domain_tensions",
    "priority_order",
}
_DOMAIN_ASSESSMENT_KEYS = {
    "status",
    "confidence",
    "observations",
    "selected_action_keys",
    "veto_action_keys",
}
_OBSERVATION_KEYS = {"text", "evidence_ids"}
_TENSION_KEYS = {"domains", "summary", "evidence_ids"}
_FORBIDDEN_AUTHORITY_LANGUAGE = (
    "add a set",
    "add another set",
    "add sets",
    "remove a set",
    "remove sets",
    "add an exercise",
    "remove an exercise",
    "increase load",
    "increase weight",
    "add weight",
    "change the workout",
    "change workout",
    "modify workout",
    "alter workout",
    "change nutrition target",
    "change the nutrition target",
    "change calories",
    "change protein",
    "change macros",
    "deload",
    "diagnose",
    "treat",
    "injury",
    "illness",
    "overtraining",
    "force progression",
)
_SEMANTIC_ACTION_CHANGE_PHRASES = tuple(
    phrase
    for phrase in _FORBIDDEN_AUTHORITY_LANGUAGE
    if phrase not in {"diagnose", "treat", "injury", "illness", "overtraining"}
)
_LIMITED_CONFIDENCE_FORBIDDEN_CERTAINTY_PHRASES = (
    "fully recovered",
    "definitely ready",
    "clearly ready",
    "no recovery concerns",
    "no concerns",
    "all signs confirm",
    "completely ready",
    "guaranteed",
    "certainly",
)
_SOURCE_GAP_DENIAL_PHRASES = (
    "data is complete",
    "data are complete",
    "all data is complete",
    "all data are complete",
    "no missing data",
    "no data gaps",
)
ProviderCallable = Callable[[str], str]
DirectOllamaHttpPost = Callable[[str, dict[str, Any], float], dict[str, Any]]

_SUPPORTED_PROVIDERS = {"mock", "openai", "direct_ollama"}
_NARRATIVE_FACT_CAPS: dict[SpecialistDomain, int] = {
    "recovery": 6,
    "nutrition": 8,
    "training": 6,
}
_NARRATIVE_FACT_CLAIM_TYPES = {
    "food_identity_claim",
    "macro_status_claim",
    "nutrition_claim",
    "recovery_status_claim",
    "training_intensity_claim",
    "training_plan_claim",
}
_NARRATIVE_PROSE_CLAIM_KEY_TOKENS = (
    "coach_safe_summary",
    "summary",
    "interpretation",
    "recommendation",
    "desired_coaching_move",
    "today_intent",
    "recommended_focus",
    "limitation",
    "source_data_gap",
)
_NARRATIVE_SEMANTIC_STRING_KEY_SUFFIXES = (
    ".friendly_name",
    ".display_name",
    ".status",
    "_status",
    ".level",
    "_level",
    ".risk",
    "_risk",
    ".classification",
    "_classification",
    ".direction",
    "_direction",
    ".readiness",
    "_readiness",
    ".quality",
    "_quality",
    ".confidence",
    "_confidence",
    ".range",
    "_range",
    ".trend",
    "_trend",
)
_NARRATIVE_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["headline", "body"],
    "properties": {
        "headline": {"type": "string"},
        "body": {"type": "string"},
    },
}


def build_specialist_response_schema(
    assessment_context: CrossDomainAssessmentContext,
) -> dict[str, Any]:
    """Build the exact provider schema from the bounded assessment context."""

    tension_evidence_ids = [
        fact.evidence_id
        for domain in SPECIALIST_DOMAINS
        for fact in assessment_context.domain_evidence[domain]
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": sorted(_ASSESSMENT_KEYS),
        "properties": {
            "assessment_version": {
                "const": CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION,
            },
            **{
                domain: _specialist_domain_schema(assessment_context, domain)
                for domain in SPECIALIST_DOMAINS
            },
            "cross_domain_tensions": {
                "type": "array",
                "maxItems": 3,
                "items": _tension_schema(tension_evidence_ids),
            },
            "priority_order": {
                "type": "array",
                "items": {"type": "string", "enum": list(SPECIALIST_DOMAINS)},
                "minItems": 3,
                "maxItems": 3,
                "uniqueItems": True,
            },
        },
    }


def _specialist_domain_schema(
    assessment_context: CrossDomainAssessmentContext,
    domain: SpecialistDomain,
) -> dict[str, Any]:
    evidence_ids = [
        fact.evidence_id for fact in assessment_context.domain_evidence[domain]
    ]
    action_keys = [
        action.action_key for action in assessment_context.selectable_actions[domain]
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": sorted(_DOMAIN_ASSESSMENT_KEYS),
        "properties": {
            "status": {"type": "string", "enum": sorted(_STATUSES)},
            "confidence": {
                "type": "string",
                "enum": list(_CONFIDENCE_ORDER),
            },
            "observations": _observation_array_schema(evidence_ids),
            "selected_action_keys": _action_key_array_schema(action_keys),
            "veto_action_keys": _action_key_array_schema(action_keys),
        },
    }


def _observation_array_schema(evidence_ids: list[str]) -> dict[str, Any]:
    if not evidence_ids:
        return {"type": "array", "maxItems": 0}
    return {
        "type": "array",
        "maxItems": 3,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": sorted(_OBSERVATION_KEYS),
            "properties": {
                "text": {"type": "string"},
                "evidence_ids": _evidence_id_array_schema(evidence_ids),
            },
        },
    }


def _action_key_array_schema(action_keys: list[str]) -> dict[str, Any]:
    if not action_keys:
        return {"type": "array", "maxItems": 0}
    return {
        "type": "array",
        "items": {"type": "string", "enum": action_keys},
        "uniqueItems": True,
    }


def _tension_schema(evidence_ids: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": sorted(_TENSION_KEYS),
        "properties": {
            "domains": {
                "type": "array",
                "items": {"type": "string", "enum": list(SPECIALIST_DOMAINS)},
                "minItems": 2,
                "maxItems": 3,
                "uniqueItems": True,
            },
            "summary": {"type": "string"},
            "evidence_ids": _evidence_id_array_schema(evidence_ids),
        },
    }


def _evidence_id_array_schema(evidence_ids: list[str]) -> dict[str, Any]:
    if not evidence_ids:
        return {"type": "array", "maxItems": 0}
    return {
        "type": "array",
        "items": {"type": "string", "enum": evidence_ids},
        "minItems": 1,
        "uniqueItems": True,
    }


class SpecialistAssessmentValidationError(ValueError):
    """Raised when the provider assessment exceeds its candidate boundary."""


def run_cross_domain_coaching_preview_for_user(
    *,
    user_id: int,
    target_date: str,
    assessment_provider: str,
    assessment_model: str,
    narrative_provider: str,
    narrative_model: str,
    assessment_prompt: str,
    narrative_prompt: str,
    timeout_seconds: float = 300,
    assessment_provider_callable: ProviderCallable | None = None,
    narrative_provider_callable: ProviderCallable | None = None,
) -> CrossDomainCoachingPreviewResult:
    evidence_packet, approved_brief = build_cross_domain_coaching_context_for_user(
        user_id=user_id,
        target_date=target_date,
    )
    return run_cross_domain_coaching_preview(
        evidence_packet=evidence_packet,
        approved_brief=approved_brief,
        assessment_provider=assessment_provider,
        assessment_model=assessment_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        assessment_prompt=assessment_prompt,
        narrative_prompt=narrative_prompt,
        timeout_seconds=timeout_seconds,
        assessment_provider_callable=assessment_provider_callable,
        narrative_provider_callable=narrative_provider_callable,
    )


def run_cross_domain_coaching_preview(
    *,
    evidence_packet: CrossDomainEvidencePacket,
    approved_brief: ApprovedCoachBrief,
    assessment_provider: str,
    assessment_model: str,
    narrative_provider: str,
    narrative_model: str,
    assessment_prompt: str,
    narrative_prompt: str,
    timeout_seconds: float = 300,
    assessment_provider_callable: ProviderCallable | None = None,
    narrative_provider_callable: ProviderCallable | None = None,
) -> CrossDomainCoachingPreviewResult:
    """Run the bounded two-call developer preview without product side effects."""

    _require_supported_provider("assessment provider", assessment_provider)
    _require_supported_provider("narrative provider", narrative_provider)
    _require_text("assessment model", assessment_model)
    _require_text("narrative model", narrative_model)
    assessment_model = _resolved_model_name(assessment_provider, assessment_model)
    narrative_model = _resolved_model_name(narrative_provider, narrative_model)
    assessment_context = build_cross_domain_assessment_context(
        evidence_packet,
        approved_brief,
    )
    assessment_input = build_specialist_provider_input(
        assessment_prompt,
        assessment_context,
    )
    provider_call_count = 1
    try:
        assessment_raw_output = _call_provider(
            provider=assessment_provider,
            model=assessment_model,
            provider_input=assessment_input,
            timeout_seconds=timeout_seconds,
            provider_callable=assessment_provider_callable,
            mock_response=_mock_specialist_response(evidence_packet),
            response_schema=build_specialist_response_schema(assessment_context),
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001 - preview must return a safe failure
        return _provider_failure_result(
            evidence_packet=evidence_packet,
            assessment_context=assessment_context,
            assessment_provider=assessment_provider,
            assessment_model=assessment_model,
            narrative_provider=narrative_provider,
            narrative_model=narrative_model,
            provider_call_count=provider_call_count,
            error=exc,
        )

    safe_assessment_output = _sanitize_text(assessment_raw_output)
    try:
        assessment = parse_cross_domain_specialist_assessment(
            safe_assessment_output,
            evidence_packet,
        )
    except SpecialistAssessmentValidationError as exc:
        return CrossDomainCoachingPreviewResult(
            result_version=CROSS_DOMAIN_COACHING_PREVIEW_RESULT_VERSION,
            user_id=evidence_packet.user_id,
            target_date=evidence_packet.target_date,
            assessment_provider=assessment_provider,
            assessment_model=assessment_model,
            narrative_provider=narrative_provider,
            narrative_model=narrative_model,
            evidence_packet=evidence_packet,
            assessment_context=assessment_context,
            disposition="REJECTED_SPECIALIST_ASSESSMENT",
            provider_call_count=provider_call_count,
            specialist_raw_output=safe_assessment_output,
            error_type=exc.__class__.__name__,
            error_message=_sanitize_text(str(exc)),
        )

    resolved_brief = resolve_cross_domain_coaching_brief(
        evidence_packet=evidence_packet,
        assessment=assessment,
    )
    confidence_policy = build_narrative_confidence_policy(
        evidence_packet=evidence_packet,
        resolved_brief=resolved_brief,
    )
    semantic_narrative_context = build_provider_safe_narrative_context(
        approved_brief=approved_brief,
        assessment_context=assessment_context,
        assessment=assessment,
        resolved_brief=resolved_brief,
        confidence_policy=confidence_policy,
    )
    narrative_input = build_narrative_provider_input(
        narrative_prompt,
        semantic_narrative_context=semantic_narrative_context,
    )
    provider_call_count += 1
    try:
        narrative_raw_output = _call_provider(
            provider=narrative_provider,
            model=narrative_model,
            provider_input=narrative_input,
            timeout_seconds=timeout_seconds,
            provider_callable=narrative_provider_callable,
            mock_response=_mock_narrative_response(),
            response_schema=_NARRATIVE_RESPONSE_SCHEMA,
            temperature=0.2,
        )
        narrative_draft = parse_natural_coach_draft(
            _sanitize_text(narrative_raw_output),
            provider=narrative_provider,
            model=narrative_model,
        )
    except Exception as exc:  # noqa: BLE001 - preview must return a safe failure
        return _provider_failure_result(
            evidence_packet=evidence_packet,
            assessment_context=assessment_context,
            assessment_provider=assessment_provider,
            assessment_model=assessment_model,
            narrative_provider=narrative_provider,
            narrative_model=narrative_model,
            provider_call_count=provider_call_count,
            error=exc,
            specialist_raw_output=safe_assessment_output,
            specialist_assessment=assessment,
            resolved_brief=resolved_brief,
            semantic_narrative_context=semantic_narrative_context,
            narrative_confidence_policy=confidence_policy,
        )

    extracted_claims = extract_claims_from_natural_draft(
        narrative_draft, approved_brief
    )
    claim_audit_result = _merge_semantic_action_claim_findings(
        audit_extracted_draft_claims(
            extracted_claims,
            approved_brief,
        ),
        draft=narrative_draft,
        resolved_brief=resolved_brief,
    )
    confidence_coherence_audit_result = (
        audit_cross_domain_narrative_confidence_coherence(
            draft=narrative_draft,
            confidence_policy=confidence_policy,
        )
    )
    product_voice_audit_result = audit_daily_coach_product_voice(
        narrative_draft,
        approved_brief,
        mode="approval",
    )
    if not claim_audit_result.passed:
        disposition = "REJECTED_CLAIM_AUDIT"
    elif not confidence_coherence_audit_result.passed:
        disposition = "REJECTED_CONFIDENCE_COHERENCE"
    elif not product_voice_audit_result.passed:
        disposition = "REJECTED_PRODUCT_VOICE"
    else:
        disposition = "APPROVED_PREVIEW"
    return CrossDomainCoachingPreviewResult(
        result_version=CROSS_DOMAIN_COACHING_PREVIEW_RESULT_VERSION,
        user_id=evidence_packet.user_id,
        target_date=evidence_packet.target_date,
        assessment_provider=assessment_provider,
        assessment_model=assessment_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        evidence_packet=evidence_packet,
        assessment_context=assessment_context,
        disposition=disposition,
        provider_call_count=provider_call_count,
        specialist_raw_output=safe_assessment_output,
        specialist_assessment=assessment,
        resolved_brief=resolved_brief,
        semantic_narrative_context=semantic_narrative_context,
        narrative_raw_output=_sanitize_text(narrative_raw_output),
        narrative_draft=narrative_draft,
        claim_audit_result=claim_audit_result,
        narrative_confidence_policy=confidence_policy,
        confidence_coherence_audit_result=confidence_coherence_audit_result,
        product_voice_audit_result=product_voice_audit_result,
    )


def build_specialist_provider_input(
    prompt_text: str,
    assessment_context: CrossDomainAssessmentContext,
) -> str:
    _require_text("assessment prompt", prompt_text)
    response_shape = {
        "assessment_version": CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION,
        "recovery": {
            "status": "supportive",
            "confidence": "Moderate",
            "observations": [],
            "selected_action_keys": [],
            "veto_action_keys": [],
        },
        "nutrition": {
            "status": "supportive",
            "confidence": "Moderate",
            "observations": [],
            "selected_action_keys": [],
            "veto_action_keys": [],
        },
        "training": {
            "status": "supportive",
            "confidence": "Moderate",
            "observations": [],
            "selected_action_keys": [],
            "veto_action_keys": [],
        },
        "cross_domain_tensions": [],
        "priority_order": ["recovery", "nutrition", "training"],
    }
    return "\n\n".join(
        [
            prompt_text.strip(),
            "=== BOUNDED ASSESSMENT CONTEXT JSON ===\n"
            + json.dumps(assessment_context.to_dict(), indent=2, sort_keys=True),
            "=== REQUIRED JSON RESPONSE EXAMPLE ===\n"
            + json.dumps(response_shape, indent=2),
            "Return one JSON object only. Select listed action keys only; do not create action text.",
        ]
    )


def build_narrative_provider_input(
    prompt_text: str,
    *,
    semantic_narrative_context: Mapping[str, Any],
) -> str:
    _require_text("narrative prompt", prompt_text)
    return "\n\n".join(
        [
            prompt_text.strip(),
            "=== SEMANTIC NARRATIVE CONTEXT JSON ===\n"
            + json.dumps(semantic_narrative_context, indent=2, sort_keys=True),
            "Return one JSON object only with exactly headline and body string keys.",
        ]
    )


def build_provider_safe_narrative_context(
    *,
    approved_brief: ApprovedCoachBrief,
    assessment_context: CrossDomainAssessmentContext,
    assessment: CrossDomainSpecialistAssessment,
    resolved_brief: ResolvedCrossDomainBrief,
    confidence_policy: NarrativeConfidencePolicy,
) -> dict[str, Any]:
    """Project a bounded semantic contract into the narrative call."""

    return {
        "context_version": CROSS_DOMAIN_SEMANTIC_NARRATIVE_CONTEXT_VERSION,
        "scenario": approved_brief.scenario,
        "resolved_decision": {
            "primary_domain": resolved_brief.primary_domain,
            "primary_action": (
                _resolved_action_with_support(
                    resolved_brief.primary_action,
                    assessment_context=assessment_context,
                )
                if resolved_brief.primary_action
                else None
            ),
            "supporting_actions": [
                _resolved_action_with_support(
                    action,
                    assessment_context=assessment_context,
                )
                for action in resolved_brief.supporting_actions
            ],
            "suppressed_action_keys": [
                action.action_key for action in resolved_brief.suppressed_actions
            ],
            "resolution_reason_codes": list(resolved_brief.resolution_reason_codes),
        },
        "domain_assessments": {
            domain: {
                "status": assessment.for_domain(domain).status,
                "confidence": assessment.for_domain(domain).confidence,
                "selected_action_keys": list(
                    assessment.for_domain(domain).selected_action_keys
                ),
                "veto_action_keys": list(
                    assessment.for_domain(domain).veto_action_keys
                ),
            }
            for domain in SPECIALIST_DOMAINS
        },
        "approved_facts": _bounded_narrative_facts(
            approved_brief=approved_brief,
            resolved_brief=resolved_brief,
        ),
        "confidence": {
            "resolved": confidence_policy.resolved_confidence,
            "material_limitations_present": bool(
                assessment_context.material_limitations
            ),
            "material_limitations": [
                condition.to_dict()
                for condition in assessment_context.material_limitations
            ],
            "source_data_gaps_present": bool(assessment_context.source_data_gaps),
            "source_data_gaps": [
                condition.to_dict() for condition in assessment_context.source_data_gaps
            ],
        },
        "forbidden_topic_codes": [
            _code_for_text(topic) for topic in approved_brief.blocked_topics
        ],
    }


def build_narrative_confidence_policy(
    *,
    evidence_packet: CrossDomainEvidencePacket,
    resolved_brief: ResolvedCrossDomainBrief,
) -> NarrativeConfidencePolicy:
    """Preserve resolved uncertainty as structured narrative-call context."""

    material_limitations = resolved_brief.limitations
    primary_domain = resolved_brief.primary_domain
    reason_codes: list[str] = []
    if resolved_brief.confidence in {"Limited", "Low"}:
        reason_codes.append("limited_resolved_confidence")
    if material_limitations:
        reason_codes.append("material_limitations_preserved")
    if evidence_packet.source_data_gaps:
        reason_codes.append("source_data_gaps_preserved")
    return NarrativeConfidencePolicy(
        resolved_confidence=resolved_brief.confidence,
        primary_domain=primary_domain,
        material_limitations=material_limitations,
        source_data_gaps_preserved=bool(evidence_packet.source_data_gaps),
        forbidden_certainty_phrases=(
            _LIMITED_CONFIDENCE_FORBIDDEN_CERTAINTY_PHRASES
            if resolved_brief.confidence in {"Limited", "Low"}
            else ()
        ),
        reason_codes=tuple(reason_codes),
    )


def audit_cross_domain_narrative_confidence_coherence(
    *,
    draft: NaturalCoachDraft,
    confidence_policy: NarrativeConfidencePolicy,
) -> ConfidenceCoherenceAuditResult:
    """Reject explicit certainty or limitation contradictions."""

    findings: list[str] = []
    normalized_body = _normalize_text(draft.body)
    certainty_violations = [
        phrase
        for phrase in confidence_policy.forbidden_certainty_phrases
        if phrase in normalized_body
    ]
    findings.extend(
        f"forbidden_certainty_phrase:{phrase}" for phrase in certainty_violations
    )
    if confidence_policy.source_data_gaps_preserved:
        data_gap_denials = [
            phrase for phrase in _SOURCE_GAP_DENIAL_PHRASES if phrase in normalized_body
        ]
        findings.extend(
            f"source_data_gap_denial:{phrase}" for phrase in data_gap_denials
        )
    if confidence_policy.material_limitations:
        if "no limitations" in normalized_body:
            findings.append("material_limitation_denial:no limitations")
        if (
            "no concerns" in normalized_body
            and "no concerns" not in certainty_violations
        ):
            findings.append("material_limitation_denial:no concerns")

    return ConfidenceCoherenceAuditResult(
        passed=not findings,
        decision="PASS" if not findings else "REJECTED_CONFIDENCE_COHERENCE",
        findings=tuple(findings),
        certainty_violation_count=len(certainty_violations),
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _resolved_action_with_support(
    action: ResolvedCoachingAction,
    *,
    assessment_context: CrossDomainAssessmentContext,
) -> dict[str, Any]:
    support_by_action_key = {
        selectable.action_key: selectable.supporting_claims
        for actions in assessment_context.selectable_actions.values()
        for selectable in actions
    }
    payload = action.to_dict()
    payload["supporting_claims"] = [
        claim.to_dict() for claim in support_by_action_key.get(action.action_key, ())
    ]
    return payload


def _bounded_narrative_facts(
    *,
    approved_brief: ApprovedCoachBrief,
    resolved_brief: ResolvedCrossDomainBrief,
) -> dict[SpecialistDomain, list[dict[str, Any]]]:
    action_claim_keys = [
        claim_key
        for action in (
            resolved_brief.primary_action,
            *resolved_brief.supporting_actions,
        )
        if action is not None
        for claim_key in action.source_claim_keys
    ]
    semantic_fact_claim_keys = {
        fact.claim_key
        for fact in approved_brief.approved_facts
        if fact.claim_type in _NARRATIVE_FACT_CLAIM_TYPES
    }
    ordered_claim_keys = _dedupe_text(
        [
            *action_claim_keys,
            *(
                fact.claim_key
                for fact in approved_brief.approved_facts
                if fact.claim_key in semantic_fact_claim_keys
            ),
        ]
    )
    facts_by_domain: dict[SpecialistDomain, list[dict[str, Any]]] = {
        "recovery": [],
        "nutrition": [],
        "training": [],
    }
    for claim_key in ordered_claim_keys:
        domain = _claim_domain(claim_key)
        if (
            domain is None
            or len(facts_by_domain[domain]) >= _NARRATIVE_FACT_CAPS[domain]
        ):
            continue
        claim = approved_brief.claim_registry.get(claim_key)
        if not isinstance(claim, Mapping):
            fact = next(
                (
                    item
                    for item in approved_brief.approved_facts
                    if item.claim_key == claim_key
                ),
                None,
            )
            claim = fact.to_dict() if fact else None
        if not isinstance(claim, Mapping) or claim.get("user_facing_allowed") is False:
            continue
        payload = _semantic_claim_payload(claim_key, claim)
        if payload is not None:
            facts_by_domain[domain].append(payload)
    return facts_by_domain


def _claim_domain(claim_key: str) -> SpecialistDomain | None:
    for domain in SPECIALIST_DOMAINS:
        if claim_key.startswith(f"{domain}."):
            return domain
    return None


def _semantic_claim_payload(
    claim_key: str,
    claim: Mapping[str, Any],
) -> dict[str, Any] | None:
    value = claim.get("value")
    if not _is_narrative_semantic_value(claim_key, value):
        return None
    payload: dict[str, Any] = {
        "claim_key": claim_key,
        "value": value,
    }
    confidence = claim.get("confidence")
    if isinstance(confidence, str) and confidence in _CONFIDENCE_ORDER:
        payload["confidence"] = confidence
    display_value = _semantic_display_value(claim_key, claim)
    if display_value is not None:
        payload["display_value"] = display_value
    return payload


def _is_narrative_semantic_value(claim_key: str, value: Any) -> bool:
    normalized_key = claim_key.lower()
    if any(token in normalized_key for token in _NARRATIVE_PROSE_CLAIM_KEY_TOKENS):
        return False
    if isinstance(value, bool | int | float):
        return True
    return isinstance(value, str) and normalized_key.endswith(
        _NARRATIVE_SEMANTIC_STRING_KEY_SUFFIXES
    )


def _semantic_display_value(
    claim_key: str,
    claim: Mapping[str, Any],
) -> str | None:
    value = claim.get("value")
    display_value = claim.get("friendly_display_value") or claim.get("display_value")
    if not isinstance(display_value, str) or not display_value.strip():
        return None
    display_value = display_value.strip()
    if claim_key.endswith((".friendly_name", ".display_name")):
        return display_value
    if isinstance(value, int | float) and not isinstance(value, bool):
        return display_value
    if isinstance(value, str) and _normalize_text(display_value) == _normalize_text(
        value
    ):
        return display_value
    if re.fullmatch(r"-?\d+(?:\.\d+)?\s*(?:%|g|kg|lb|lbs|kcal)?", display_value):
        return display_value
    return None


def _code_for_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unspecified"


def _merge_semantic_action_claim_findings(
    result: ClaimAuditResult,
    *,
    draft: NaturalCoachDraft,
    resolved_brief: ResolvedCrossDomainBrief,
) -> ClaimAuditResult:
    normalized = _normalize_text(f"{draft.headline} {draft.body}")
    unsupported_changes = tuple(
        phrase for phrase in _SEMANTIC_ACTION_CHANGE_PHRASES if phrase in normalized
    )
    if not unsupported_changes:
        return result
    available_support = tuple(
        action.action_key
        for action in (
            resolved_brief.primary_action,
            *resolved_brief.supporting_actions,
        )
        if action is not None
    )
    semantic_findings = tuple(
        ClaimAuditFinding(
            finding_type="unsupported_semantic_action_claim",
            severity="block",
            text_span=phrase,
            extracted_claim=phrase,
            reason="The narrative changes training or nutrition beyond the resolved semantic actions.",
            required_support="A resolved semantic action that explicitly permits this change.",
            available_support=available_support,
            repair_instruction="Remove the unsupported change.",
            repairable=False,
        )
        for phrase in unsupported_changes
    )
    findings = (*result.findings, *semantic_findings)
    return ClaimAuditResult(
        passed=False,
        findings=findings,
        repairable=False,
        final_decision="fallback_required",
        unsupported_claim_count=result.unsupported_claim_count + len(semantic_findings),
        food_claim_count=result.food_claim_count,
        causal_claim_count=result.causal_claim_count,
        addressing_violation_count=result.addressing_violation_count,
    )


def parse_cross_domain_specialist_assessment(
    raw_output: str,
    evidence_packet: CrossDomainEvidencePacket,
) -> CrossDomainSpecialistAssessment:
    payload = _parse_single_json_object(raw_output, "specialist assessment")
    _require_exact_keys(payload, _ASSESSMENT_KEYS, "specialist assessment")
    if payload.get("assessment_version") != CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION:
        raise SpecialistAssessmentValidationError("Unexpected assessment_version.")
    action_catalog = {
        item.action_key: item for item in evidence_packet.approved_action_catalog
    }
    evidence_catalog = {
        fact.evidence_id
        for domain_facts in evidence_packet.domain_evidence.values()
        for fact in domain_facts
    }
    assessments: dict[SpecialistDomain, SpecialistDomainAssessment] = {}
    for domain in SPECIALIST_DOMAINS:
        assessments[domain] = _parse_domain_assessment(
            payload.get(domain),
            domain=domain,
            action_catalog=action_catalog,
            evidence_catalog=evidence_catalog,
        )
    tensions = _parse_cross_domain_tensions(
        payload.get("cross_domain_tensions"),
        evidence_catalog=evidence_catalog,
    )
    priority_order = _string_list(payload.get("priority_order"), "priority_order")
    if len(priority_order) != 3 or set(priority_order) != set(SPECIALIST_DOMAINS):
        raise SpecialistAssessmentValidationError(
            "priority_order must be an exact recovery/nutrition/training permutation."
        )
    return CrossDomainSpecialistAssessment(
        assessment_version=CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION,
        recovery=assessments["recovery"],
        nutrition=assessments["nutrition"],
        training=assessments["training"],
        cross_domain_tensions=tuple(tensions),
        priority_order=tuple(priority_order),  # type: ignore[arg-type]
    )


def resolve_cross_domain_coaching_brief(
    *,
    evidence_packet: CrossDomainEvidencePacket,
    assessment: CrossDomainSpecialistAssessment,
) -> ResolvedCrossDomainBrief:
    catalog = {
        item.action_key: item for item in evidence_packet.approved_action_catalog
    }
    primary_domain, domain_order, scenario_code = _resolution_order(
        evidence_packet.scenario,
        assessment.priority_order,
    )
    vetoed_keys = {
        key
        for domain in SPECIALIST_DOMAINS
        for key in assessment.for_domain(domain).veto_action_keys
    }
    suppressed: list[ResolvedCoachingAction] = [
        _resolved_action(catalog[key]) for key in vetoed_keys if key in catalog
    ]
    selected: list[ResolvedCoachingAction] = []
    for domain in domain_order:
        domain_assessment = assessment.for_domain(domain)
        for action_key in domain_assessment.selected_action_keys:
            action = catalog[action_key]
            resolved = _resolved_action(action)
            if action_key in vetoed_keys:
                suppressed.append(resolved)
                continue
            selected.append(resolved)
            break

    primary_action = next(
        (action for action in selected if action.domain == primary_domain), None
    )
    excluded_action_keys = vetoed_keys.union(action.action_key for action in suppressed)
    if primary_action is None:
        for fallback_domain in _fallback_primary_domains(primary_domain, domain_order):
            primary_action = _first_catalog_action(
                catalog.values(),
                fallback_domain,
                excluded_action_keys=excluded_action_keys,
            )
            if primary_action is not None:
                break

    supporting: list[ResolvedCoachingAction] = []
    selected_domains = {primary_action.domain} if primary_action else set()
    for action in selected:
        if primary_action and action.action_key == primary_action.action_key:
            continue
        if action.domain in selected_domains:
            continue
        supporting.append(action)
        selected_domains.add(action.domain)
        if len(supporting) == 2:
            break
    limitations = _dedupe_conditions(
        [
            *build_cross_domain_semantic_conditions(
                evidence_packet.limitations,
                kind="material_limitation",
                limit=5,
            ),
            *build_cross_domain_semantic_conditions(
                evidence_packet.source_data_gaps,
                kind="source_data_gap",
                limit=5,
            ),
        ]
    )
    reason_codes = [scenario_code]
    if vetoed_keys:
        reason_codes.append("specialist_veto_applied")
    recovery_vetoed_training = any(
        catalog[action_key].domain == "training"
        for action_key in assessment.recovery.veto_action_keys
        if action_key in catalog
    )
    if recovery_vetoed_training:
        reason_codes.append("recovery_constraint_precedence")
    if evidence_packet.source_data_gaps:
        reason_codes.append("source_data_gaps_preserved")
    confidence = _minimum_confidence(
        [
            evidence_packet.overall_confidence,
            *(
                assessment.for_domain(domain).confidence
                for domain in SPECIALIST_DOMAINS
            ),
        ]
    )
    return ResolvedCrossDomainBrief(
        resolved_brief_version=RESOLVED_CROSS_DOMAIN_BRIEF_VERSION,
        primary_domain=primary_domain,
        primary_action=primary_action,
        supporting_actions=tuple(supporting),
        suppressed_actions=tuple(_dedupe_actions(suppressed)),
        approved_observations={
            domain: assessment.for_domain(domain).observations
            for domain in SPECIALIST_DOMAINS
        },
        cross_domain_tensions=assessment.cross_domain_tensions,
        limitations=tuple(limitations),
        confidence=confidence,
        resolution_reason_codes=tuple(reason_codes),
    )


def parse_natural_coach_draft(
    raw_output: str,
    *,
    provider: str,
    model: str,
) -> NaturalCoachDraft:
    payload = _parse_single_json_object(raw_output, "narrative")
    if set(payload) != {"headline", "body"}:
        raise ValueError("Narrative JSON must contain exactly headline and body.")
    headline = payload.get("headline")
    body = payload.get("body")
    if not isinstance(headline, str) or not headline.strip():
        raise ValueError("Narrative headline must be a non-empty string.")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("Narrative body must be a non-empty string.")
    return NaturalCoachDraft(
        headline=headline.strip(),
        body=body.strip(),
        provider=_natural_draft_provider(provider),
        model=model,
    )


def _parse_domain_assessment(
    value: Any,
    *,
    domain: SpecialistDomain,
    action_catalog: Mapping[str, ApprovedActionCatalogItem],
    evidence_catalog: set[str],
) -> SpecialistDomainAssessment:
    if not isinstance(value, Mapping):
        raise SpecialistAssessmentValidationError(f"{domain} assessment is required.")
    _require_exact_keys(value, _DOMAIN_ASSESSMENT_KEYS, f"{domain} assessment")
    status = value.get("status")
    if status not in _STATUSES:
        raise SpecialistAssessmentValidationError(f"{domain} has an unknown status.")
    confidence = value.get("confidence")
    if confidence not in _CONFIDENCE_ORDER:
        raise SpecialistAssessmentValidationError(
            f"{domain} has an unknown confidence."
        )
    observations_value = value.get("observations")
    if not isinstance(observations_value, list) or len(observations_value) > 3:
        raise SpecialistAssessmentValidationError(
            f"{domain} observations must contain at most three items."
        )
    observations: list[SpecialistObservation] = []
    observed_evidence_ids: set[str] = set()
    for observation in observations_value:
        if not isinstance(observation, Mapping):
            raise SpecialistAssessmentValidationError(
                f"{domain} observations must be objects."
            )
        _require_exact_keys(
            observation,
            _OBSERVATION_KEYS,
            f"{domain} observation",
        )
        text = observation.get("text")
        if not isinstance(text, str) or not text.strip():
            raise SpecialistAssessmentValidationError(
                f"{domain} observation text is required."
            )
        _reject_forbidden_authority_language(text)
        evidence_ids = _string_list(
            observation.get("evidence_ids"),
            f"{domain} observation evidence_ids",
        )
        if not evidence_ids:
            raise SpecialistAssessmentValidationError(
                f"{domain} observations require evidence IDs."
            )
        _assert_known_ids(evidence_ids, evidence_catalog, "evidence ID")
        _assert_unique(evidence_ids, f"{domain} observation evidence IDs")
        duplicate_observed_ids = observed_evidence_ids.intersection(evidence_ids)
        if duplicate_observed_ids:
            raise SpecialistAssessmentValidationError(
                f"{domain} repeats evidence IDs across observations."
            )
        observed_evidence_ids.update(evidence_ids)
        observations.append(
            SpecialistObservation(text=text.strip(), evidence_ids=tuple(evidence_ids))
        )
    selected_action_keys = _string_list(
        value.get("selected_action_keys"),
        f"{domain} selected_action_keys",
    )
    veto_action_keys = _string_list(
        value.get("veto_action_keys"),
        f"{domain} veto_action_keys",
    )
    _assert_unique(selected_action_keys, f"{domain} selected action keys")
    _assert_unique(veto_action_keys, f"{domain} veto action keys")
    _assert_known_ids(selected_action_keys, set(action_catalog), "action key")
    _assert_known_ids(veto_action_keys, set(action_catalog), "action key")
    for action_key in selected_action_keys:
        if action_catalog[action_key].domain != domain:
            raise SpecialistAssessmentValidationError(
                f"{domain} selected an action owned by another domain."
            )
    return SpecialistDomainAssessment(
        status=status,  # type: ignore[arg-type]
        confidence=confidence,  # type: ignore[arg-type]
        observations=tuple(observations),
        selected_action_keys=tuple(selected_action_keys),
        veto_action_keys=tuple(veto_action_keys),
    )


def _parse_cross_domain_tensions(
    value: Any,
    *,
    evidence_catalog: set[str],
) -> list[CrossDomainTension]:
    if not isinstance(value, list):
        raise SpecialistAssessmentValidationError(
            "cross_domain_tensions must be a list."
        )
    tensions: list[CrossDomainTension] = []
    for tension in value:
        if not isinstance(tension, Mapping):
            raise SpecialistAssessmentValidationError(
                "cross_domain_tensions must contain objects."
            )
        _require_exact_keys(tension, _TENSION_KEYS, "cross-domain tension")
        domains = _string_list(tension.get("domains"), "tension domains")
        if len(domains) < 2 or len(set(domains)) != len(domains):
            raise SpecialistAssessmentValidationError(
                "A cross-domain tension requires at least two unique domains."
            )
        if any(domain not in SPECIALIST_DOMAINS for domain in domains):
            raise SpecialistAssessmentValidationError(
                "A tension has an unknown domain."
            )
        summary = tension.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise SpecialistAssessmentValidationError("A tension summary is required.")
        _reject_forbidden_authority_language(summary)
        evidence_ids = _string_list(tension.get("evidence_ids"), "tension evidence_ids")
        _assert_unique(evidence_ids, "tension evidence IDs")
        _assert_known_ids(evidence_ids, evidence_catalog, "evidence ID")
        tensions.append(
            CrossDomainTension(
                domains=tuple(domains),  # type: ignore[arg-type]
                summary=summary.strip(),
                evidence_ids=tuple(evidence_ids),
            )
        )
    return tensions


def _resolution_order(
    scenario: str,
    specialist_priority: tuple[SpecialistDomain, ...],
) -> tuple[CrossDomainEvidenceDomain, tuple[SpecialistDomain, ...], str]:
    if scenario == "recovery_limited":
        return "recovery", SPECIALIST_DOMAINS, "scenario_recovery_limited"
    if scenario == "nutrition_training_mismatch":
        return (
            "nutrition",
            ("nutrition", "recovery", "training"),
            "scenario_nutrition_training_mismatch",
        )
    if scenario == "data_quality_limited":
        return (
            "shared/data-quality",
            SPECIALIST_DOMAINS,
            "scenario_data_quality_limited",
        )
    if scenario == "improving_after_deload":
        return (
            "recovery",
            ("recovery", "training", "nutrition"),
            "scenario_improving_after_deload",
        )
    if scenario == "aligned_managed":
        return (
            specialist_priority[0],
            specialist_priority,
            "scenario_aligned_managed_specialist_emphasis",
        )
    return "recovery", SPECIALIST_DOMAINS, "scenario_unknown_conservative_order"


def _first_catalog_action(
    catalog: Sequence[ApprovedActionCatalogItem],
    domain: CrossDomainEvidenceDomain,
    *,
    excluded_action_keys: set[str],
) -> ResolvedCoachingAction | None:
    for action in catalog:
        if action.domain == domain and action.action_key not in excluded_action_keys:
            return _resolved_action(action)
    return None


def _fallback_primary_domains(
    primary_domain: CrossDomainEvidenceDomain,
    domain_order: tuple[SpecialistDomain, ...],
) -> tuple[CrossDomainEvidenceDomain, ...]:
    domains: list[CrossDomainEvidenceDomain] = [primary_domain]
    domains.extend(domain for domain in domain_order if domain not in domains)
    return tuple(domains)


def _resolved_action(action: ApprovedActionCatalogItem) -> ResolvedCoachingAction:
    return ResolvedCoachingAction(
        action_key=action.action_key,
        domain=action.domain,
        action_type=action.action_type,
        parameters=dict(action.parameters),
        source_claim_keys=action.source_claim_keys,
    )


def _call_provider(
    *,
    provider: str,
    model: str,
    provider_input: str,
    timeout_seconds: float,
    provider_callable: ProviderCallable | None,
    mock_response: str,
    response_schema: dict[str, Any],
    temperature: float,
) -> str:
    if provider_callable is not None:
        output = provider_callable(provider_input)
    elif provider == "mock":
        output = mock_response
    elif provider == "openai":
        output = call_openai_human_voice_prompt_preview(
            provider_input=provider_input,
            model_name=model,
            timeout_seconds=timeout_seconds,
        )
    elif provider == "direct_ollama":
        output = call_direct_ollama_preview(
            provider_input=provider_input,
            model_name=model,
            response_schema=response_schema,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )
    else:
        raise ValueError("provider must be mock, openai, or direct_ollama")
    if not isinstance(output, str):
        raise TypeError("provider must return a string")
    return output


def call_direct_ollama_preview(
    *,
    provider_input: str,
    model_name: str,
    response_schema: dict[str, Any],
    temperature: float,
    timeout_seconds: float,
    http_post: DirectOllamaHttpPost | None = None,
) -> str:
    """Call local Ollama once using the repository lifecycle conventions."""

    normalized_model = normalize_ollama_model_name(model_name)
    policy = resolve_provider_lifecycle_policy(
        provider_name="direct_ollama",
        model_name=normalized_model,
    )
    payload = build_ollama_generate_payload(
        model_name=normalized_model,
        prompt=provider_input,
        response_schema=response_schema,
        stream=False,
        options={"temperature": temperature},
        policy=policy,
    )
    if normalized_model.lower().startswith("qwen3"):
        payload["think"] = False
    endpoint = f"{resolve_ollama_base_url().rstrip('/')}/api/generate"
    response = (http_post or _post_direct_ollama_json)(
        endpoint,
        payload,
        timeout_seconds,
    )
    output = response.get("response")
    if not isinstance(output, str):
        raise ValueError("Ollama response must contain a string response field.")
    return output


def _post_direct_ollama_json(
    url: str,
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        raw_response = response.read().decode("utf-8")
    response_payload = json.loads(raw_response) if raw_response else {}
    if not isinstance(response_payload, dict):
        raise ValueError("Ollama response must be a JSON object.")
    return response_payload


def _mock_specialist_response(evidence_packet: CrossDomainEvidencePacket) -> str:
    catalog_by_domain: dict[str, list[str]] = {
        domain: [] for domain in SPECIALIST_DOMAINS
    }
    for action in evidence_packet.approved_action_catalog:
        if action.domain in catalog_by_domain:
            catalog_by_domain[action.domain].append(action.action_key)
    payload: dict[str, Any] = {
        "assessment_version": CROSS_DOMAIN_SPECIALIST_ASSESSMENT_VERSION,
        "cross_domain_tensions": [],
        "priority_order": list(SPECIALIST_DOMAINS),
    }
    for domain in SPECIALIST_DOMAINS:
        evidence_ids = [
            fact.evidence_id
            for fact in evidence_packet.domain_evidence.get(domain, ())[:1]
        ]
        payload[domain] = {
            "status": "limiting"
            if domain == "recovery" and evidence_packet.scenario == "recovery_limited"
            else "supportive",
            "confidence": evidence_packet.overall_confidence,
            "observations": (
                [
                    {
                        "text": "Uses the available backend evidence.",
                        "evidence_ids": evidence_ids,
                    }
                ]
                if evidence_ids
                else []
            ),
            "selected_action_keys": catalog_by_domain[domain][:1],
            "veto_action_keys": [],
        }
    return json.dumps(payload)


def _mock_narrative_response() -> str:
    return json.dumps(
        {
            "headline": "Keep the day simple",
            "body": "Let the session stay measured, write down what you do, and use the available food options only when they fit the goals already laid out for today.",
        }
    )


def _provider_failure_result(
    *,
    evidence_packet: CrossDomainEvidencePacket,
    assessment_context: CrossDomainAssessmentContext,
    assessment_provider: str,
    assessment_model: str,
    narrative_provider: str,
    narrative_model: str,
    provider_call_count: int,
    error: Exception,
    specialist_raw_output: str | None = None,
    specialist_assessment: CrossDomainSpecialistAssessment | None = None,
    resolved_brief: ResolvedCrossDomainBrief | None = None,
    semantic_narrative_context: dict[str, Any] | None = None,
    narrative_confidence_policy: NarrativeConfidencePolicy | None = None,
) -> CrossDomainCoachingPreviewResult:
    return CrossDomainCoachingPreviewResult(
        result_version=CROSS_DOMAIN_COACHING_PREVIEW_RESULT_VERSION,
        user_id=evidence_packet.user_id,
        target_date=evidence_packet.target_date,
        assessment_provider=assessment_provider,
        assessment_model=assessment_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        evidence_packet=evidence_packet,
        assessment_context=assessment_context,
        disposition="PROVIDER_FAILURE",
        provider_call_count=provider_call_count,
        specialist_raw_output=specialist_raw_output,
        specialist_assessment=specialist_assessment,
        resolved_brief=resolved_brief,
        semantic_narrative_context=semantic_narrative_context,
        narrative_confidence_policy=narrative_confidence_policy,
        error_type=error.__class__.__name__,
        error_message=_sanitize_text(str(error)),
    )


def _parse_single_json_object(raw_output: str, label: str) -> dict[str, Any]:
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise SpecialistAssessmentValidationError(f"{label} output is empty.")
    stripped = raw_output.strip()
    if stripped.startswith("```") or stripped.endswith("```"):
        raise SpecialistAssessmentValidationError(
            f"{label} must not use Markdown fences."
        )
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise SpecialistAssessmentValidationError(
            f"{label} must be a single JSON object."
        ) from exc
    if not isinstance(payload, dict):
        raise SpecialistAssessmentValidationError(f"{label} must be a JSON object.")
    return payload


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise SpecialistAssessmentValidationError(f"{label} must be a string list.")
    return [item.strip() for item in value]


def _assert_known_ids(
    values: Sequence[str],
    allowed: set[str],
    label: str,
) -> None:
    unknown = sorted(set(values).difference(allowed))
    if unknown:
        raise SpecialistAssessmentValidationError(f"Unknown {label}: {unknown[0]}")


def _assert_unique(values: Sequence[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise SpecialistAssessmentValidationError(f"Duplicate {label} are not allowed.")


def _require_exact_keys(
    value: Mapping[str, Any],
    expected_keys: set[str],
    label: str,
) -> None:
    if set(value) != expected_keys:
        raise SpecialistAssessmentValidationError(
            f"{label} must contain exactly the required keys."
        )


def _reject_forbidden_authority_language(text: str) -> None:
    normalized = " ".join(text.casefold().split())
    if any(term in normalized for term in _FORBIDDEN_AUTHORITY_LANGUAGE):
        raise SpecialistAssessmentValidationError(
            "Specialist output contains forbidden authority language."
        )


def _minimum_confidence(values: Sequence[ConfidenceLevel]) -> ConfidenceLevel:
    return min(values, key=lambda value: _CONFIDENCE_ORDER[value])


def _dedupe_actions(
    actions: Sequence[ResolvedCoachingAction],
) -> list[ResolvedCoachingAction]:
    seen: set[str] = set()
    return [
        action
        for action in actions
        if not (action.action_key in seen or seen.add(action.action_key))
    ]


def _dedupe_text(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value.strip()))


def _dedupe_conditions(
    conditions: Sequence[CrossDomainSemanticCondition],
) -> list[CrossDomainSemanticCondition]:
    seen: set[tuple[str, CrossDomainEvidenceDomain]] = set()
    return [
        condition
        for condition in conditions
        if not (
            (condition.code, condition.scope) in seen
            or seen.add((condition.code, condition.scope))
        )
    ]


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _require_supported_provider(name: str, provider: str) -> None:
    _require_text(name, provider)
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(f"{name} must be mock, openai, or direct_ollama")


def _resolved_model_name(provider: str, model: str) -> str:
    return normalize_ollama_model_name(model) if provider == "direct_ollama" else model


def _natural_draft_provider(provider: str) -> str:
    if provider == "mock":
        return "deterministic"
    if provider in {"openai", "direct_ollama"}:
        return provider
    raise ValueError("Narrative provider must be mock, openai, or direct_ollama")


def _sanitize_text(value: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    sanitized = value.replace(api_key, "[redacted]") if api_key else value
    return re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", sanitized)
