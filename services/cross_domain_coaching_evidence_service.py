from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any

from models.cross_domain_coaching_preview_models import (
    ApprovedActionCatalogItem,
    ConfidenceLevel,
    CrossDomainActionSupportingClaim,
    CrossDomainAssessmentContext,
    CrossDomainAssessmentEvidenceFact,
    CrossDomainEvidenceDomain,
    CrossDomainEvidenceFact,
    CrossDomainEvidencePacket,
    CrossDomainSelectableAction,
    CrossDomainSemanticCondition,
    SpecialistDomain,
)
from models.daily_coach_natural_draft_audit_models import ApprovedCoachBrief
from models.daily_coach_provider_preview_payload_models import (
    DailyCoachProviderPreviewRawDataPayload,
)
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_intelligence_snapshot_service import (
    build_daily_coach_intelligence_snapshot,
)
from services.daily_coach_provider_preview_payload_service import (
    build_daily_coach_provider_preview_raw_data_payload,
)
from services.daily_coach_synthesis_service import build_daily_coach_synthesis

CROSS_DOMAIN_COACHING_EVIDENCE_PACKET_VERSION = (
    "cross_domain_coaching_evidence_packet_v1"
)
CROSS_DOMAIN_ASSESSMENT_CONTEXT_VERSION = "cross_domain_assessment_context_v1"

_CONFIDENCE_ORDER: dict[ConfidenceLevel, int] = {
    "Limited": 0,
    "Low": 1,
    "Moderate": 2,
    "High": 3,
}

_DOMAIN_SOURCE_SECTIONS: dict[CrossDomainEvidenceDomain, tuple[str, ...]] = {
    "recovery": (
        "recovery_intelligence",
        "recovery_intelligence_v2",
    ),
    "nutrition": ("nutrition_trend_window",),
    "training": (
        "workout_set_intelligence",
        "training_execution_summary",
    ),
    "shared/data-quality": (
        "foundation_layer_status",
        "data_completeness",
        "source_data_gaps",
        "reason_codes",
        "limitations",
    ),
}
_ASSESSMENT_FACT_CAPS: dict[CrossDomainEvidenceDomain, int] = {
    "recovery": 8,
    "nutrition": 8,
    "training": 10,
    "shared/data-quality": 5,
}
_SPECIALIST_DOMAINS: tuple[SpecialistDomain, ...] = (
    "recovery",
    "nutrition",
    "training",
)
_ASSESSMENT_PRIORITY_TERMS: dict[CrossDomainEvidenceDomain, tuple[str, ...]] = {
    "recovery": (
        "readiness",
        "fatigue",
        "coach_safe",
        "sleep",
        "energy",
        "soreness",
        "coverage",
        "confidence",
        "limitation",
    ),
    "nutrition": (
        "logging_completeness",
        "logged",
        "complete",
        "no_log",
        "bodyweight",
        "calibration",
        "logging_quality",
        "confidence",
        "limitation",
    ),
    "training": (
        "training_execution_summary",
        "completion",
        "effort",
        "completed_set_count",
        "average_completion",
        "rir",
        "below",
        "inside",
        "above",
        "incomplete",
        "confidence",
        "limitation",
    ),
    "shared/data-quality": ("source_data_gaps", "limitations"),
}
_COMMON_ASSESSMENT_METADATA_TOKENS = (
    "model_version",
    "source_table",
    "user_id",
    "target_date",
    "source_snapshot_version",
    "source_services",
)
_SUPPORT_PROSE_CLAIM_KEY_TOKENS = (
    "instruction",
    "interpretation",
    "summary",
    "recommendation",
    "today_intent",
    "recommended_focus",
    "desired_coaching_move",
    "limitation",
    "source_data_gap",
)
_SUPPORT_SEMANTIC_STRING_KEY_SUFFIXES = (
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
_ASSESSMENT_FACT_KEYS: dict[CrossDomainEvidenceDomain, dict[str, str]] = {
    "recovery": {
        "readiness": "recovery.readiness_level",
        "readiness_level": "recovery.readiness_level",
        "fatigue_risk": "recovery.fatigue_risk",
        "readiness_classification": "recovery.readiness_classification",
        "recovery_pressure": "recovery.recovery_pressure",
        "fatigue_support": "recovery.fatigue_support",
        "sleep_consistency": "recovery.sleep_consistency",
        "primary_sleep": "recovery.sleep_status",
        "primary_energy": "recovery.energy_status",
        "primary_soreness": "recovery.soreness_status",
        "coverage": "recovery.coverage_status",
        "confidence": "recovery.confidence",
    },
    "nutrition": {
        "window_days": "nutrition.window_days",
        "logged_day_count": "nutrition.logged_day_count",
        "complete_logging_day_count": "nutrition.complete_logging_day_count",
        "partial_logging_day_count": "nutrition.partial_logging_day_count",
        "no_log_day_count": "nutrition.no_log_day_count",
        "logging_completeness": "nutrition.logging_completeness",
        "logged_count": "nutrition.logged_day_count",
        "complete_count": "nutrition.complete_logging_day_count",
        "no_log_count": "nutrition.no_log_day_count",
        "overall_trend_confidence": "nutrition.trend_confidence",
        "bodyweight_direction": "nutrition.bodyweight_direction",
        "calibration_readiness": "nutrition.calibration_readiness",
        "logging_quality": "nutrition.logging_quality",
        "confidence": "nutrition.confidence",
        "protein_status": "nutrition.protein.status",
    },
    "training": {
        "completed_execution_count": "training.completed_execution_count",
        "completed_set_count": "training.completed_set_count",
        "planned_set_count": "training.planned_set_count",
        "average_completion_percentage": "training.average_completion_percentage",
        "average_completion": "training.average_completion_percentage",
        "completion_rate": "training.completion_rate",
        "average_planned_rir": "training.average_planned_rir",
        "average_actual_rir": "training.average_actual_rir",
        "average_rir_deviation": "training.average_rir_deviation",
        "planned_vs_actual_rir": "training.planned_vs_actual_rir",
        "skipped_exercise_count": "training.skipped_exercise_count",
        "substituted_exercise_count": "training.substituted_exercise_count",
        "sets_below_planned_reps": "training.sets_below_planned_reps",
        "sets_inside_planned_reps": "training.sets_inside_planned_reps",
        "sets_above_planned_reps": "training.sets_above_planned_reps",
        "incomplete_logging_count": "training.incomplete_logging_count",
        "missing_actual_rir_count": "training.missing_actual_rir_count",
        "missing_actual_reps_count": "training.missing_actual_reps_count",
        "execution_quality": "training.execution_quality",
        "execution_effort_trend": "training.execution_effort_trend",
        "execution_completion_trend": "training.execution_completion_trend",
        "effort_trend": "training.execution_effort_trend",
        "overall_completion_indicator": "training.completion_indicator",
        "overall_effort_indicator": "training.effort_indicator",
        "overall_rep_range_indicator": "training.rep_range_indicator",
        "overall_logging_quality": "training.logging_quality",
        "confidence": "training.confidence",
    },
    "shared/data-quality": {},
}


def build_cross_domain_coaching_context_for_user(
    *,
    user_id: int,
    target_date: str,
) -> tuple[CrossDomainEvidencePacket, ApprovedCoachBrief]:
    """Build the developer-only evidence and approved action boundaries.

    This composes existing Daily Coach services only. It does not query database
    tables directly, call providers, mutate state, or expose a product surface.
    """

    snapshot = build_daily_coach_intelligence_snapshot(
        user_id=user_id,
        target_date=target_date,
    )
    payload = build_daily_coach_provider_preview_raw_data_payload(snapshot)
    synthesis = build_daily_coach_synthesis(user_id)
    scenario = str(getattr(synthesis, "scenario", "") or "unknown")
    brief = build_approved_coach_brief(
        user_id=user_id,
        target_date=target_date,
        scenario_id=scenario,
        synthesis=synthesis,
    )
    return (
        build_cross_domain_coaching_evidence_packet(
            payload=payload,
            approved_brief=brief,
            scenario=scenario,
        ),
        brief,
    )


def build_cross_domain_coaching_evidence_packet(
    *,
    payload: DailyCoachProviderPreviewRawDataPayload | Mapping[str, Any],
    approved_brief: ApprovedCoachBrief,
    scenario: str | None = None,
) -> CrossDomainEvidencePacket:
    """Translate approved/raw Daily Coach sections into deterministic facts."""

    payload_dict = _payload_to_dict(payload)
    source_data = payload_dict.get("source_data")
    if not isinstance(source_data, Mapping):
        raise ValueError("Cross-domain evidence requires provider preview source_data.")

    default_confidence = _confidence_from_value(payload_dict.get("overall_confidence"))
    domain_evidence: dict[
        CrossDomainEvidenceDomain, tuple[CrossDomainEvidenceFact, ...]
    ] = {}
    confidence_values: list[ConfidenceLevel] = []
    for domain, sections in _DOMAIN_SOURCE_SECTIONS.items():
        facts: list[CrossDomainEvidenceFact] = []
        for section in sections:
            facts.extend(
                _facts_for_section(
                    domain=domain,
                    section=section,
                    value=source_data.get(section),
                    default_confidence=default_confidence,
                )
            )
        domain_evidence[domain] = tuple(facts)
        confidence_values.extend(fact.confidence for fact in facts)

    resolved_scenario = str(
        scenario or approved_brief.scenario or payload_dict.get("scenario") or "unknown"
    )
    return CrossDomainEvidencePacket(
        packet_version=CROSS_DOMAIN_COACHING_EVIDENCE_PACKET_VERSION,
        user_id=int(payload_dict["user_id"]),
        target_date=str(payload_dict["target_date"]),
        scenario=resolved_scenario,
        overall_confidence=_minimum_confidence(
            confidence_values or [default_confidence]
        ),
        source_snapshot_version=str(payload_dict["source_snapshot_version"]),
        source_services=tuple(str(item) for item in payload_dict["source_services"]),
        domain_evidence=domain_evidence,
        approved_action_catalog=tuple(_build_action_catalog(approved_brief)),
        limitations=tuple(str(item) for item in payload_dict.get("limitations") or []),
        source_data_gaps=tuple(
            str(item) for item in payload_dict.get("source_data_gaps") or []
        ),
        backend_truth_contract=dict(payload_dict.get("backend_truth_contract") or {}),
    )


def build_cross_domain_assessment_context(
    evidence_packet: CrossDomainEvidencePacket,
    approved_brief: ApprovedCoachBrief,
) -> CrossDomainAssessmentContext:
    """Project full audit evidence into a compact, provider-safe assessment context."""

    domain_evidence = {
        domain: tuple(
            _select_assessment_facts(
                domain=domain,
                facts=evidence_packet.domain_evidence[domain],
                limit=_ASSESSMENT_FACT_CAPS[domain],
            )
        )
        for domain in _ASSESSMENT_FACT_CAPS
    }
    selectable_actions = {
        domain: tuple(
            CrossDomainSelectableAction(
                action_key=item.action_key,
                domain=domain,
                action_type=item.action_type,
                parameters=dict(item.parameters),
                supporting_claims=_action_supporting_claims(item, approved_brief),
            )
            for item in evidence_packet.approved_action_catalog
            if item.domain == domain
        )
        for domain in _SPECIALIST_DOMAINS
    }
    source_data_gaps = build_cross_domain_semantic_conditions(
        evidence_packet.source_data_gaps,
        kind="source_data_gap",
        limit=5,
    )
    material_limitations = build_cross_domain_semantic_conditions(
        evidence_packet.limitations,
        kind="material_limitation",
        limit=5,
    )
    return CrossDomainAssessmentContext(
        context_version=CROSS_DOMAIN_ASSESSMENT_CONTEXT_VERSION,
        scenario=evidence_packet.scenario,
        overall_confidence=evidence_packet.overall_confidence,
        domain_evidence=domain_evidence,
        selectable_actions=selectable_actions,
        material_limitations=material_limitations,
        source_data_gaps=source_data_gaps,
        backend_truth_contract=dict(evidence_packet.backend_truth_contract),
    )


def _action_supporting_claims(
    action: ApprovedActionCatalogItem,
    approved_brief: ApprovedCoachBrief,
) -> tuple[CrossDomainActionSupportingClaim, ...]:
    supporting_claims: list[CrossDomainActionSupportingClaim] = []
    seen_claim_keys: set[str] = set()
    for claim_key in action.source_claim_keys:
        if claim_key in seen_claim_keys:
            continue
        claim = approved_brief.claim_registry.get(claim_key)
        if (
            not isinstance(claim, Mapping)
            or claim.get("user_facing_allowed") is not True
        ):
            continue
        value = claim.get("value")
        if not _is_provider_safe_support_value(claim_key, value):
            continue
        display_value = _provider_safe_display_value(claim_key, claim)
        confidence_value = claim.get("confidence")
        confidence = (
            confidence_value
            if isinstance(confidence_value, str)
            and confidence_value in _CONFIDENCE_ORDER
            else None
        )
        supporting_claims.append(
            CrossDomainActionSupportingClaim(
                claim_key=claim_key,
                value=value,
                display_value=display_value,
                confidence=confidence,
            )
        )
        seen_claim_keys.add(claim_key)
    return tuple(supporting_claims)


def _select_assessment_facts(
    *,
    domain: CrossDomainEvidenceDomain,
    facts: Sequence[CrossDomainEvidenceFact],
    limit: int,
) -> list[CrossDomainAssessmentEvidenceFact]:
    selected: list[CrossDomainAssessmentEvidenceFact] = []
    seen_display_values: set[str] = set()
    ordered_facts = sorted(
        facts,
        key=lambda fact: (
            _assessment_fact_priority(domain, fact),
            fact.source_path,
            fact.evidence_id,
        ),
    )
    for fact in ordered_facts:
        fact_key = _assessment_fact_key(domain, fact)
        if fact_key is None:
            continue
        display_key = " ".join(fact.display_value.lower().split())
        if not display_key or display_key in seen_display_values:
            continue
        selected.append(
            CrossDomainAssessmentEvidenceFact(
                evidence_id=fact.evidence_id,
                domain=fact.domain,
                fact_key=fact_key,
                value=fact.value,
                display_value=fact.display_value,
                confidence=fact.confidence,
            )
        )
        seen_display_values.add(display_key)
        if len(selected) == limit:
            break
    return selected


def _assessment_fact_priority(
    domain: CrossDomainEvidenceDomain,
    fact: CrossDomainEvidenceFact,
) -> int:
    searchable = f"{fact.source_path} {fact.label}".lower()
    for index, term in enumerate(_ASSESSMENT_PRIORITY_TERMS[domain]):
        if term in searchable:
            return index
    return len(_ASSESSMENT_PRIORITY_TERMS[domain])


def _assessment_fact_key(
    domain: CrossDomainEvidenceDomain,
    fact: CrossDomainEvidenceFact,
) -> str | None:
    source_path = fact.source_path.lower()
    if any(token in source_path for token in _COMMON_ASSESSMENT_METADATA_TOKENS):
        return None
    if any(
        token in source_path
        for token in (
            "coach_safe_summary",
            "summary",
            "interpretation",
            "recommendation",
            "desired_coaching_move",
            "today_intent",
            "recommended_focus",
            "limitations",
            "source_data_gaps",
            "reason_codes",
            "source_facts",
            "trend_days[",
            "exercise_indicators",
            "session_summaries",
        )
    ):
        return None
    leaf = source_path.rsplit(".", maxsplit=1)[-1].split("[", maxsplit=1)[0]
    return _ASSESSMENT_FACT_KEYS[domain].get(leaf)


def build_cross_domain_semantic_conditions(
    values: Sequence[str],
    *,
    kind: str,
    limit: int,
) -> tuple[CrossDomainSemanticCondition, ...]:
    conditions: list[CrossDomainSemanticCondition] = []
    seen: set[tuple[str, CrossDomainEvidenceDomain]] = set()
    for value in values:
        condition = _semantic_condition(value, kind=kind)
        key = (condition.code, condition.scope)
        if key in seen:
            continue
        seen.add(key)
        conditions.append(condition)
        if len(conditions) == limit:
            break
    return tuple(conditions)


def _semantic_condition(value: str, *, kind: str) -> CrossDomainSemanticCondition:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    if "food_knowledge_expansion" in normalized:
        code = "food_knowledge_expansion_pending"
        scope: CrossDomainEvidenceDomain = "nutrition"
    elif "food" in normalized or "nutrition" in normalized:
        code = (
            "food_logging_incomplete"
            if "log" in normalized or "incomplete" in normalized
            else f"{kind}_present"
        )
        scope = "nutrition"
    elif any(token in normalized for token in ("recovery", "sleep", "check_in")):
        code = "recovery_data_incomplete"
        scope = "recovery"
    elif any(token in normalized for token in ("training", "workout", "exercise")):
        code = "training_data_incomplete"
        scope = "training"
    elif "logging" in normalized and "incomplete" in normalized:
        code = "logging_incomplete"
        scope = "shared/data-quality"
    else:
        code = f"{kind}_present"
        scope = "shared/data-quality"
    return CrossDomainSemanticCondition(code=code, scope=scope)


def _facts_for_section(
    *,
    domain: CrossDomainEvidenceDomain,
    section: str,
    value: Any,
    default_confidence: ConfidenceLevel,
) -> list[CrossDomainEvidenceFact]:
    if value is None:
        return []
    return list(
        _flatten_evidence(
            domain=domain,
            value=value,
            source_path=f"source_data.{section}",
            inherited_confidence=default_confidence,
        )
    )


def _flatten_evidence(
    *,
    domain: CrossDomainEvidenceDomain,
    value: Any,
    source_path: str,
    inherited_confidence: ConfidenceLevel,
) -> list[CrossDomainEvidenceFact]:
    if isinstance(value, Mapping):
        current_confidence = _confidence_from_value(
            value.get("confidence"), fallback=inherited_confidence
        )
        facts: list[CrossDomainEvidenceFact] = []
        for key in sorted(value, key=str):
            if key in {"generated_at", "created_at", "updated_at"}:
                continue
            facts.extend(
                _flatten_evidence(
                    domain=domain,
                    value=value[key],
                    source_path=f"{source_path}.{key}",
                    inherited_confidence=current_confidence,
                )
            )
        return facts
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        facts: list[CrossDomainEvidenceFact] = []
        for index, item in enumerate(value):
            facts.extend(
                _flatten_evidence(
                    domain=domain,
                    value=item,
                    source_path=f"{source_path}[{index}]",
                    inherited_confidence=inherited_confidence,
                )
            )
        return facts
    if value is None:
        return []
    return [
        CrossDomainEvidenceFact(
            evidence_id=_evidence_id(source_path, value),
            domain=domain,
            source_path=source_path,
            label=_label_for_path(source_path),
            value=value,
            display_value=_display_value(value),
            confidence=inherited_confidence,
            user_facing_allowed=domain != "shared/data-quality",
        )
    ]


def _build_action_catalog(
    brief: ApprovedCoachBrief,
) -> list[ApprovedActionCatalogItem]:
    items: list[ApprovedActionCatalogItem] = []
    for index, action in enumerate(brief.approved_recovery_interpretations, start=1):
        items.append(
            ApprovedActionCatalogItem(
                action_key=_indexed_action_key(
                    "recovery:maintain_planned_training",
                    index,
                ),
                domain="recovery",
                action_type="maintain_planned_training",
                parameters={
                    "intensity_change": "none",
                    "max_effort_test": False,
                },
                source_claim_keys=tuple(action.claim_keys),
            )
        )
    for action in brief.approved_food_actions:
        friendly_name = action.friendly_name or action.canonical_name
        if not friendly_name:
            continue
        source_claim_keys = [action.food_claim_key]
        macro_status_key = (
            f"nutrition.{action.macro_reason}.status" if action.macro_reason else None
        )
        if macro_status_key and macro_status_key in brief.claim_registry:
            source_claim_keys.append(macro_status_key)
        items.append(
            ApprovedActionCatalogItem(
                action_key=f"nutrition_food:{action.food_claim_key}",
                domain="nutrition",
                action_type="consider_food_candidate",
                parameters={
                    "friendly_name": friendly_name,
                    "macro_reason": action.macro_reason,
                    "serving_display": (
                        action.serving_display if action.serving_allowed else None
                    ),
                    "serving_allowed": action.serving_allowed,
                },
                source_claim_keys=tuple(source_claim_keys),
            )
        )
    for index, action in enumerate(brief.approved_training_actions, start=1):
        items.append(
            ApprovedActionCatalogItem(
                action_key=_indexed_action_key(
                    "training:execute_planned_session",
                    index,
                ),
                domain="training",
                action_type="execute_planned_session",
                parameters=_training_action_parameters(
                    action.claim_keys,
                    brief.claim_registry,
                ),
                source_claim_keys=tuple(action.claim_keys),
            )
        )
    action_keys = [item.action_key for item in items]
    if len(action_keys) != len(set(action_keys)):
        raise ValueError("Approved action catalog contains duplicate action keys.")
    return items


def _indexed_action_key(base_key: str, index: int) -> str:
    return base_key if index == 1 else f"{base_key}:{index}"


def _training_action_parameters(
    claim_keys: Sequence[str],
    claim_registry: Mapping[str, Any],
) -> dict[str, Any]:
    parameters: dict[str, Any] = {
        "avoid_grinding_reps": True,
        "max_effort_test": False,
    }
    for claim_key in claim_keys:
        if "rir_range" not in claim_key:
            continue
        claim = claim_registry.get(claim_key)
        if not isinstance(claim, Mapping):
            continue
        rir_range = _parse_numeric_range(claim.get("value"))
        if rir_range is not None:
            parameters["rir_range"] = rir_range
            break
    return parameters


def _parse_numeric_range(value: Any) -> dict[str, int | float] | None:
    minimum: Any = None
    maximum: Any = None
    if isinstance(value, Mapping):
        minimum = value.get("min")
        maximum = value.get("max")
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        if len(value) == 2:
            minimum, maximum = value
    elif isinstance(value, str):
        match = re.fullmatch(
            r"\s*(-?\d+(?:\.\d+)?)\s*[-–]\s*(-?\d+(?:\.\d+)?)\s*",
            value,
        )
        if match:
            minimum, maximum = match.groups()
    parsed_minimum = _numeric_value(minimum)
    parsed_maximum = _numeric_value(maximum)
    if parsed_minimum is None or parsed_maximum is None:
        return None
    return {"min": parsed_minimum, "max": parsed_maximum}


def _numeric_value(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return None
    else:
        return None
    return int(number) if number.is_integer() else number


def _is_semantic_data_value(value: Any) -> bool:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, Mapping):
        return all(
            isinstance(key, str) and _is_semantic_data_value(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return all(_is_semantic_data_value(item) for item in value)
    return False


def _is_provider_safe_support_value(claim_key: str, value: Any) -> bool:
    normalized_key = claim_key.lower()
    if any(token in normalized_key for token in _SUPPORT_PROSE_CLAIM_KEY_TOKENS):
        return False
    if isinstance(value, str):
        return normalized_key.endswith(_SUPPORT_SEMANTIC_STRING_KEY_SUFFIXES)
    return value is not None and _is_semantic_data_value(value)


def _provider_safe_display_value(
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
    if isinstance(value, str) and _normalized_text(display_value) == _normalized_text(
        value
    ):
        return display_value
    if re.fullmatch(r"-?\d+(?:\.\d+)?\s*(?:%|g|kg|lb|lbs|kcal)?", display_value):
        return display_value
    return None


def _normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def _payload_to_dict(
    payload: DailyCoachProviderPreviewRawDataPayload | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        return dict(payload)
    if hasattr(payload, "to_dict"):
        return payload.to_dict()
    return asdict(payload)


def _evidence_id(source_path: str, value: Any) -> str:
    canonical_value = json.dumps(
        value, sort_keys=True, default=str, separators=(",", ":")
    )
    digest = hashlib.sha256(f"{source_path}:{canonical_value}".encode())
    return f"evidence:{digest.hexdigest()[:16]}"


def _label_for_path(source_path: str) -> str:
    leaf = source_path.rsplit(".", maxsplit=1)[-1]
    leaf = leaf.split("[", maxsplit=1)[0]
    return leaf.replace("_", " ").strip().title()


def _display_value(value: Any) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _confidence_from_value(
    value: Any,
    *,
    fallback: ConfidenceLevel = "Moderate",
) -> ConfidenceLevel:
    if isinstance(value, str) and value in _CONFIDENCE_ORDER:
        return value  # type: ignore[return-value]
    return fallback


def _minimum_confidence(values: list[ConfidenceLevel]) -> ConfidenceLevel:
    return min(values, key=lambda value: _CONFIDENCE_ORDER[value])
