from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from models.daily_coach_natural_draft_audit_models import (
    ClaimAuditResult,
    NaturalCoachDraft,
    ProductVoiceAuditResult,
)

CrossDomainEvidenceDomain = Literal[
    "recovery",
    "nutrition",
    "training",
    "shared/data-quality",
]
SpecialistDomain = Literal["recovery", "nutrition", "training"]
SpecialistStatus = Literal["supportive", "caution", "limiting", "unknown"]
ConfidenceLevel = Literal["Limited", "Low", "Moderate", "High"]
PreviewDisposition = Literal[
    "APPROVED_PREVIEW",
    "REJECTED_SPECIALIST_ASSESSMENT",
    "REJECTED_CLAIM_AUDIT",
    "REJECTED_CONFIDENCE_COHERENCE",
    "REJECTED_PRODUCT_VOICE",
    "PROVIDER_FAILURE",
]


@dataclass(frozen=True)
class CrossDomainEvidenceFact:
    evidence_id: str
    domain: CrossDomainEvidenceDomain
    source_path: str
    label: str
    value: Any
    display_value: str
    confidence: ConfidenceLevel
    user_facing_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovedActionCatalogItem:
    action_key: str
    domain: CrossDomainEvidenceDomain
    action_type: str
    parameters: dict[str, Any]
    source_claim_keys: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_key": self.action_key,
            "domain": self.domain,
            "action_type": self.action_type,
            "parameters": dict(self.parameters),
            "source_claim_keys": list(self.source_claim_keys),
        }


@dataclass(frozen=True)
class CrossDomainEvidencePacket:
    packet_version: str
    user_id: int
    target_date: str
    scenario: str
    overall_confidence: ConfidenceLevel
    source_snapshot_version: str
    source_services: tuple[str, ...]
    domain_evidence: dict[
        CrossDomainEvidenceDomain, tuple[CrossDomainEvidenceFact, ...]
    ]
    approved_action_catalog: tuple[ApprovedActionCatalogItem, ...]
    limitations: tuple[str, ...]
    source_data_gaps: tuple[str, ...]
    backend_truth_contract: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_version": self.packet_version,
            "user_id": self.user_id,
            "target_date": self.target_date,
            "scenario": self.scenario,
            "overall_confidence": self.overall_confidence,
            "source_snapshot_version": self.source_snapshot_version,
            "source_services": list(self.source_services),
            "domain_evidence": {
                domain: [fact.to_dict() for fact in facts]
                for domain, facts in self.domain_evidence.items()
            },
            "approved_action_catalog": [
                item.to_dict() for item in self.approved_action_catalog
            ],
            "limitations": list(self.limitations),
            "source_data_gaps": list(self.source_data_gaps),
            "backend_truth_contract": dict(self.backend_truth_contract),
        }


@dataclass(frozen=True)
class CrossDomainAssessmentEvidenceFact:
    """A provider-safe evidence fact selected from the full audit packet."""

    evidence_id: str
    domain: CrossDomainEvidenceDomain
    fact_key: str
    value: Any
    display_value: str
    confidence: ConfidenceLevel

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CrossDomainActionSupportingClaim:
    """Provider-safe approved claim support for one selectable action."""

    claim_key: str
    value: Any
    display_value: str | None
    confidence: ConfidenceLevel | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CrossDomainSelectableAction:
    """An action key a specialist may select with approved claim support only."""

    action_key: str
    domain: SpecialistDomain
    action_type: str
    parameters: dict[str, Any]
    supporting_claims: tuple[CrossDomainActionSupportingClaim, ...] = field(
        default_factory=tuple
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_key": self.action_key,
            "domain": self.domain,
            "action_type": self.action_type,
            "parameters": dict(self.parameters),
            "supporting_claims": [claim.to_dict() for claim in self.supporting_claims],
        }


@dataclass(frozen=True)
class CrossDomainSemanticCondition:
    """A provider-safe limitation or source-gap condition without prose copy."""

    code: str
    scope: CrossDomainEvidenceDomain
    status: Literal["present"] = "present"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CrossDomainAssessmentContext:
    """Bounded deterministic context for the specialist provider call only."""

    context_version: str
    scenario: str
    overall_confidence: ConfidenceLevel
    domain_evidence: dict[
        CrossDomainEvidenceDomain, tuple[CrossDomainAssessmentEvidenceFact, ...]
    ]
    selectable_actions: dict[SpecialistDomain, tuple[CrossDomainSelectableAction, ...]]
    material_limitations: tuple[CrossDomainSemanticCondition, ...]
    source_data_gaps: tuple[CrossDomainSemanticCondition, ...]
    backend_truth_contract: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_version": self.context_version,
            "scenario": self.scenario,
            "overall_confidence": self.overall_confidence,
            "domain_evidence": {
                domain: [fact.to_dict() for fact in facts]
                for domain, facts in self.domain_evidence.items()
            },
            "selectable_actions": {
                domain: [action.to_dict() for action in actions]
                for domain, actions in self.selectable_actions.items()
            },
            "material_limitations": [
                condition.to_dict() for condition in self.material_limitations
            ],
            "source_data_gaps": [
                condition.to_dict() for condition in self.source_data_gaps
            ],
            "backend_truth_contract": dict(self.backend_truth_contract),
        }


@dataclass(frozen=True)
class SpecialistObservation:
    text: str
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SpecialistDomainAssessment:
    status: SpecialistStatus
    confidence: ConfidenceLevel
    observations: tuple[SpecialistObservation, ...]
    selected_action_keys: tuple[str, ...]
    veto_action_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "confidence": self.confidence,
            "observations": [item.to_dict() for item in self.observations],
            "selected_action_keys": list(self.selected_action_keys),
            "veto_action_keys": list(self.veto_action_keys),
        }


@dataclass(frozen=True)
class CrossDomainTension:
    domains: tuple[SpecialistDomain, ...]
    summary: str
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domains": list(self.domains),
            "summary": self.summary,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class CrossDomainSpecialistAssessment:
    assessment_version: str
    recovery: SpecialistDomainAssessment
    nutrition: SpecialistDomainAssessment
    training: SpecialistDomainAssessment
    cross_domain_tensions: tuple[CrossDomainTension, ...]
    priority_order: tuple[SpecialistDomain, ...]

    def for_domain(self, domain: SpecialistDomain) -> SpecialistDomainAssessment:
        return getattr(self, domain)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_version": self.assessment_version,
            "recovery": self.recovery.to_dict(),
            "nutrition": self.nutrition.to_dict(),
            "training": self.training.to_dict(),
            "cross_domain_tensions": [
                tension.to_dict() for tension in self.cross_domain_tensions
            ],
            "priority_order": list(self.priority_order),
        }


@dataclass(frozen=True)
class ResolvedCoachingAction:
    action_key: str
    domain: CrossDomainEvidenceDomain
    action_type: str
    parameters: dict[str, Any]
    source_claim_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_key": self.action_key,
            "domain": self.domain,
            "action_type": self.action_type,
            "parameters": dict(self.parameters),
            "source_claim_keys": list(self.source_claim_keys),
        }


@dataclass(frozen=True)
class ResolvedCrossDomainBrief:
    resolved_brief_version: str
    primary_domain: CrossDomainEvidenceDomain
    primary_action: ResolvedCoachingAction | None
    supporting_actions: tuple[ResolvedCoachingAction, ...]
    suppressed_actions: tuple[ResolvedCoachingAction, ...]
    approved_observations: dict[SpecialistDomain, tuple[SpecialistObservation, ...]]
    cross_domain_tensions: tuple[CrossDomainTension, ...]
    limitations: tuple[CrossDomainSemanticCondition, ...]
    confidence: ConfidenceLevel
    resolution_reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved_brief_version": self.resolved_brief_version,
            "primary_domain": self.primary_domain,
            "primary_action": (
                self.primary_action.to_dict() if self.primary_action else None
            ),
            "supporting_actions": [
                action.to_dict() for action in self.supporting_actions
            ],
            "suppressed_actions": [
                action.to_dict() for action in self.suppressed_actions
            ],
            "approved_observations": {
                domain: [item.to_dict() for item in observations]
                for domain, observations in self.approved_observations.items()
            },
            "cross_domain_tensions": [
                tension.to_dict() for tension in self.cross_domain_tensions
            ],
            "limitations": [condition.to_dict() for condition in self.limitations],
            "confidence": self.confidence,
            "resolution_reason_codes": list(self.resolution_reason_codes),
        }


@dataclass(frozen=True)
class NarrativeConfidencePolicy:
    """Backend-owned confidence and uncertainty rules for one resolved brief."""

    resolved_confidence: ConfidenceLevel
    primary_domain: CrossDomainEvidenceDomain
    material_limitations: tuple[CrossDomainSemanticCondition, ...]
    source_data_gaps_preserved: bool
    forbidden_certainty_phrases: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved_confidence": self.resolved_confidence,
            "primary_domain": self.primary_domain,
            "material_limitations": [
                condition.to_dict() for condition in self.material_limitations
            ],
            "source_data_gaps_preserved": self.source_data_gaps_preserved,
            "forbidden_certainty_phrases": list(self.forbidden_certainty_phrases),
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class ConfidenceCoherenceAuditResult:
    """Deterministic approval gate for confidence and contradiction claims."""

    passed: bool
    decision: str
    findings: tuple[str, ...]
    certainty_violation_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "decision": self.decision,
            "findings": list(self.findings),
            "certainty_violation_count": self.certainty_violation_count,
        }


@dataclass(frozen=True)
class CrossDomainCoachingPreviewResult:
    result_version: str
    user_id: int
    target_date: str
    assessment_provider: str
    assessment_model: str
    narrative_provider: str
    narrative_model: str
    evidence_packet: CrossDomainEvidencePacket
    assessment_context: CrossDomainAssessmentContext
    disposition: PreviewDisposition
    provider_call_count: int
    specialist_raw_output: str | None = None
    specialist_assessment: CrossDomainSpecialistAssessment | None = None
    resolved_brief: ResolvedCrossDomainBrief | None = None
    semantic_narrative_context: dict[str, Any] | None = None
    narrative_raw_output: str | None = None
    narrative_draft: NaturalCoachDraft | None = None
    claim_audit_result: ClaimAuditResult | None = None
    narrative_confidence_policy: NarrativeConfidencePolicy | None = None
    confidence_coherence_audit_result: ConfidenceCoherenceAuditResult | None = None
    product_voice_audit_result: ProductVoiceAuditResult | None = None
    error_type: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_version": self.result_version,
            "user_id": self.user_id,
            "target_date": self.target_date,
            "assessment_provider": self.assessment_provider,
            "assessment_model": self.assessment_model,
            "narrative_provider": self.narrative_provider,
            "narrative_model": self.narrative_model,
            "evidence_packet": self.evidence_packet.to_dict(),
            "assessment_context": self.assessment_context.to_dict(),
            "disposition": self.disposition,
            "provider_call_count": self.provider_call_count,
            "specialist_raw_output": self.specialist_raw_output,
            "specialist_assessment": (
                self.specialist_assessment.to_dict()
                if self.specialist_assessment
                else None
            ),
            "resolved_brief": (
                self.resolved_brief.to_dict() if self.resolved_brief else None
            ),
            "semantic_narrative_context": (
                dict(self.semantic_narrative_context)
                if self.semantic_narrative_context
                else None
            ),
            "narrative_raw_output": self.narrative_raw_output,
            "narrative_draft": (
                self.narrative_draft.to_dict() if self.narrative_draft else None
            ),
            "claim_audit_result": (
                self.claim_audit_result.to_dict() if self.claim_audit_result else None
            ),
            "narrative_confidence_policy": (
                self.narrative_confidence_policy.to_dict()
                if self.narrative_confidence_policy
                else None
            ),
            "confidence_coherence_audit_result": (
                self.confidence_coherence_audit_result.to_dict()
                if self.confidence_coherence_audit_result
                else None
            ),
            "product_voice_audit_result": (
                self.product_voice_audit_result.to_dict()
                if self.product_voice_audit_result
                else None
            ),
            "error_type": self.error_type,
            "error_message": self.error_message,
        }
