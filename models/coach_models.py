from __future__ import annotations

from dataclasses import asdict, dataclass, field
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


@dataclass(frozen=True)
class CoachConversationTurn:
    role: CoachConversationRole
    content: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


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

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "domain": self.domain,
            "label": self.label,
            "fact": self.fact,
            "confidence": self.confidence,
            "observed_at": self.observed_at,
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        payload = {
            "reference_id": self.reference_id,
            "domain": self.domain,
            "evidence_type": self.evidence_type,
            "evidence_role": self._prompt_evidence_role(),
            "label": self.label,
            "fact": self.fact,
            "confidence": self.confidence,
            "observed_at": self.observed_at,
        }
        if self.evidence_type == "deterministic_progression_decision":
            payload["authoritative_value"] = {"decision": self.metadata.get("decision")}
        return payload

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

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "pack_version": self.pack_version,
            "as_of_date": self.as_of_date,
            "question_topics": list(self.question_topics),
            "matched_exercise_name": self.matched_exercise_name,
            "matched_exercise_context": dict(self.matched_exercise_context),
            "evidence": [item.to_public_dict() for item in self.evidence],
            "limitations": list(self.limitations),
            "confidence": self.confidence,
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "pack_version": self.pack_version,
            "as_of_date": self.as_of_date,
            "question_topics": list(self.question_topics),
            "matched_exercise_name": self.matched_exercise_name,
            "matched_exercise_context": dict(self.matched_exercise_context),
            "evidence": [item.to_prompt_dict() for item in self.evidence],
            "limitations": list(self.limitations),
            "confidence_ceiling": self.confidence,
            "backend_truth_contract": {
                "evidence_is_authoritative": True,
                "limitations_are_authoritative": True,
                "provider_may_add_personal_facts": False,
                "provider_may_make_causal_claims": False,
                "provider_may_mutate_application_state": False,
            },
        }


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
