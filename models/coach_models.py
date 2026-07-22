from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Literal

from models.ai_run_models import AIRunTelemetry
from models.exercise_knowledge_models import ExerciseKnowledgeContext
from models.recovery_knowledge_models import RecoveryKnowledgeContext

CoachProvider = Literal["local", "openai"]
CoachConfidence = Literal["Limited", "Low", "Moderate", "High"]
CoachConversationRole = Literal["user", "assistant"]
CoachProgressionDecision = Literal[
    "hold",
    "increase_load",
    "decrease_load",
    "build_baseline",
]
CoachEvidenceComparisonMode = Literal[
    "none",
    "adjacent_periods",
    "earlier_vs_recent",
    "best_period",
    "change_points",
    "recurring_patterns",
    "event_response",
]
CoachEvidenceHistoricalDepth = Literal["baseline", "window", "extended"]

_PROMPT_DOMAIN_ORDER = (
    "profile",
    "recovery",
    "training",
    "nutrition",
    "body_weight",
    "equipment",
    "preferences",
    "cross_domain",
)
_PROMPT_EVIDENCE_CLASS_ORDER = (
    "facts",
    "snapshots",
    "history",
    "comparisons",
    "observations",
    "authoritative_constraints",
)


@dataclass(frozen=True)
class CoachConversationTurn:
    role: CoachConversationRole
    content: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CoachEvidenceWindow:
    label: str
    start_date: str
    end_date: str
    role: str
    period_kind: str = "analysis_window"
    expected_days: int | None = None
    is_partial_period: bool = False

    @property
    def days(self) -> int:
        return (
            date.fromisoformat(self.end_date) - date.fromisoformat(self.start_date)
        ).days + 1

    def to_dict(self) -> dict[str, Any]:
        expected_days = self.expected_days or self.days
        return {
            **asdict(self),
            "days": self.days,
            "days_covered": self.days,
            "expected_days": expected_days,
            "coverage_rate": round(self.days / expected_days, 3),
        }


@dataclass(frozen=True)
class CoachEvidencePlanLimitation:
    code: str
    message: str
    domain: str | None = None
    requested_start_date: str | None = None
    requested_end_date: str | None = None
    available_start_date: str | None = None
    available_end_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class CoachEvidencePlan:
    plan_version: str
    requested_domains: tuple[str, ...]
    subject: str | None
    horizon_kind: str
    requested_start_date: str | None
    requested_end_date: str | None
    retrieval_start_date: str | None
    retrieval_end_date: str | None
    comparison_mode: CoachEvidenceComparisonMode
    historical_depth: CoachEvidenceHistoricalDepth
    windows: tuple[CoachEvidenceWindow, ...]
    presentation_windows: tuple[CoachEvidenceWindow, ...] = ()
    inherited_subject: bool = False
    inherited_horizon: bool = False
    limitations: tuple[CoachEvidencePlanLimitation, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_version": self.plan_version,
            "requested_domains": list(self.requested_domains),
            "subject": self.subject,
            "horizon": {
                "kind": self.horizon_kind,
                "requested_start_date": self.requested_start_date,
                "requested_end_date": self.requested_end_date,
                "retrieval_start_date": self.retrieval_start_date,
                "retrieval_end_date": self.retrieval_end_date,
            },
            "comparison_mode": self.comparison_mode,
            "historical_depth": self.historical_depth,
            "windows": [
                window.to_dict()
                for window in (self.presentation_windows or self.windows)
            ],
            "inherited_subject": self.inherited_subject,
            "inherited_horizon": self.inherited_horizon,
            "limitations": [item.to_dict() for item in self.limitations],
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        payload = {
            "requested_domains": list(self.requested_domains),
            "subject": self.subject,
            "requested_window": {
                "start_date": self.requested_start_date,
                "end_date": self.requested_end_date,
            },
            "retrieval_window": {
                "start_date": self.retrieval_start_date,
                "end_date": self.retrieval_end_date,
            },
            "comparison_mode": self.comparison_mode,
            "historical_depth": self.historical_depth,
            "inherited_subject": self.inherited_subject,
            "inherited_horizon": self.inherited_horizon,
            "limitations": [item.to_dict() for item in self.limitations],
        }
        if self.presentation_windows:
            payload["presentation_periods"] = {
                "columns": [
                    "period",
                    "start_date",
                    "end_date",
                    "days_covered",
                    "expected_days",
                    "coverage_rate",
                    "partial_period",
                ],
                "rows": [
                    [
                        window.label,
                        window.start_date,
                        window.end_date,
                        window.days,
                        window.expected_days or window.days,
                        round(
                            window.days / (window.expected_days or window.days),
                            3,
                        ),
                        window.is_partial_period,
                    ]
                    for window in self.presentation_windows
                ],
            }
        return payload


@dataclass(frozen=True)
class CoachEvidenceItem:
    reference_id: str
    domain: str
    evidence_type: str
    label: str
    fact: str
    confidence: CoachConfidence
    source: str
    observed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    structured_data: dict[str, Any] = field(default_factory=dict)
    synthesis_data: dict[str, Any] = field(default_factory=dict)
    public_data: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        payload = {
            "reference_id": self.reference_id,
            "domain": self.domain,
            "label": self.label,
            "fact": self.fact,
            "confidence": self.confidence,
            "observed_at": self.observed_at,
        }
        if self.public_data:
            payload["data"] = dict(self.public_data)
        return payload

    def to_prompt_dict(self, *, reference_id: str | None = None) -> dict[str, Any]:
        payload = {
            "reference_id": reference_id or self.reference_id,
            "evidence_role": self._prompt_evidence_role(),
            "observed_at": self.observed_at,
        }
        model_data = self.synthesis_data or self.structured_data
        if model_data:
            payload["data"] = dict(model_data)
        else:
            payload["label"] = self.label
            payload["fact"] = self.fact
        if self.evidence_type == "deterministic_progression_decision":
            payload["authoritative_value"] = {
                "decision": self.metadata.get("decision"),
                "guidance": self.fact,
            }
        return payload

    def prompt_evidence_class(self) -> str:
        role = self._prompt_evidence_role()
        if role == "authoritative_constraint":
            return "authoritative_constraints"
        if role == "validated_personal_fact":
            return "facts"
        if self.evidence_type in {"current_recovery_checkin"}:
            return "snapshots"
        if "history" in self.evidence_type or "overview" in self.evidence_type:
            return "history"
        if (
            "comparison" in self.evidence_type
            or "trend" in self.evidence_type
            or self.evidence_type == "longitudinal_insight"
        ):
            return "comparisons"
        return "observations"

    def _prompt_evidence_role(self) -> str:
        if self.evidence_type == "deterministic_progression_decision":
            return "authoritative_constraint"
        if self.domain == "profile" or self.evidence_type in {
            "exercise_identity",
            "exercise_preference",
            "equipment_profile",
        }:
            return "validated_personal_fact"
        return "deterministic_observation"


@dataclass(frozen=True)
class CoachEvidencePack:
    pack_version: str
    user_id: int
    as_of_date: str
    question_topics: tuple[str, ...]
    matched_exercise_name: str | None
    evidence: tuple[CoachEvidenceItem, ...]
    limitations: tuple[str, ...]
    source_services: tuple[str, ...]
    confidence: CoachConfidence
    matched_exercise_context: dict[str, Any] = field(default_factory=dict)
    evidence_plan: CoachEvidencePlan | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "pack_version": self.pack_version,
            "as_of_date": self.as_of_date,
            "question_topics": list(self.question_topics),
            "matched_exercise_name": self.matched_exercise_name,
            "matched_exercise_context": dict(self.matched_exercise_context),
            "evidence_plan": (
                self.evidence_plan.to_dict() if self.evidence_plan is not None else None
            ),
            "evidence": [item.to_public_dict() for item in self.evidence],
            "limitations": list(self.limitations),
            "confidence": self.confidence,
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        aliases = self.prompt_reference_aliases()
        grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
        domains = [
            *(
                domain
                for domain in _PROMPT_DOMAIN_ORDER
                if any(item.domain == domain for item in self.evidence)
            ),
            *sorted(
                {
                    item.domain
                    for item in self.evidence
                    if item.domain not in _PROMPT_DOMAIN_ORDER
                }
            ),
        ]
        for domain in domains:
            domain_items = [item for item in self.evidence if item.domain == domain]
            classes: dict[str, list[dict[str, Any]]] = {}
            for evidence_class in _PROMPT_EVIDENCE_CLASS_ORDER:
                items = [
                    item.to_prompt_dict(reference_id=aliases[item.reference_id])
                    for item in domain_items
                    if item.prompt_evidence_class() == evidence_class
                ]
                if items:
                    classes[evidence_class] = items
            grouped[domain] = classes
        return {
            "pack_version": self.pack_version,
            "as_of_date": self.as_of_date,
            "question_topics": list(self.question_topics),
            "matched_exercise_name": self.matched_exercise_name,
            "matched_exercise_context": dict(self.matched_exercise_context),
            "evidence_plan": (
                self.evidence_plan.to_prompt_dict()
                if self.evidence_plan is not None
                else None
            ),
            "evidence_by_domain": grouped,
            "limitations": list(self.limitations),
            "backend_truth_contract": {
                "personal_facts_are_limited_to_evidence": True,
                "limitations_are_authoritative": True,
                "structured_constraints_are_authoritative_for_actions": True,
                "provider_may_mutate_application_state": False,
            },
        }

    def prompt_reference_aliases(self) -> dict[str, str]:
        counts: dict[tuple[str, str], int] = {}
        aliases: dict[str, str] = {}
        for item in self.evidence:
            evidence_class = item.prompt_evidence_class()
            key = (item.domain, evidence_class)
            counts[key] = counts.get(key, 0) + 1
            aliases[item.reference_id] = (
                f"personal_evidence:{item.domain}:{evidence_class}:{counts[key]}"
            )
        return aliases


@dataclass(frozen=True)
class CoachSuggestedAction:
    action_type: Literal["progression_decision"]
    decision: CoachProgressionDecision
    evidence_reference: str

    def to_public_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class GroundedCoachAnswer:
    answer: str
    supporting_evidence_references: tuple[str, ...]
    supporting_knowledge_references: tuple[str, ...]
    confidence: CoachConfidence
    uncertainty: str | None
    suggested_action: CoachSuggestedAction | None
    evidence_pack: CoachEvidencePack
    knowledge_context: ExerciseKnowledgeContext
    recovery_knowledge_context: RecoveryKnowledgeContext
    configured_provider: CoachProvider
    selected_provider: CoachProvider
    configured_model: str
    selected_model: str
    telemetry: AIRunTelemetry

    def to_public_dict(self) -> dict[str, Any]:
        evidence_by_reference = {
            item.reference_id: item for item in self.evidence_pack.evidence
        }
        supporting_evidence = [
            evidence_by_reference[reference].to_public_dict()
            for reference in self.supporting_evidence_references
            if reference in evidence_by_reference
        ]
        knowledge_by_reference = {
            passage.reference_id: {
                **passage.to_public_dict(),
                "knowledge_domain": "exercise",
            }
            for passage in self.knowledge_context.passages
        }
        knowledge_by_reference.update(
            {
                passage.reference_id: passage.to_public_dict()
                for passage in self.recovery_knowledge_context.passages
            }
        )
        supporting_knowledge = [
            knowledge_by_reference[reference]
            for reference in self.supporting_knowledge_references
            if reference in knowledge_by_reference
        ]
        return {
            "success": True,
            "user_id": self.evidence_pack.user_id,
            "answer": self.answer,
            "supporting_evidence_references": list(self.supporting_evidence_references),
            "supporting_evidence": supporting_evidence,
            "supporting_knowledge_references": list(
                self.supporting_knowledge_references
            ),
            "supporting_knowledge": supporting_knowledge,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "suggested_action": (
                self.suggested_action.to_public_dict()
                if self.suggested_action is not None
                else None
            ),
            "evidence_pack": self.evidence_pack.to_public_dict(),
            "knowledge_context": self.knowledge_context.to_public_dict(),
            "recovery_knowledge_context": (
                self.recovery_knowledge_context.to_public_dict()
            ),
            "provider_run": {
                "configured_provider": self.configured_provider,
                "selected_provider": self.selected_provider,
                "configured_model": self.configured_model,
                "selected_model": self.selected_model,
                "actual_model": self.telemetry.model,
            },
            "telemetry": self.telemetry.to_public_dict(),
        }
