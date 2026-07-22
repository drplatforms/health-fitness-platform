from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RecoveryKnowledgePassage:
    reference_id: str
    source_id: str
    source_title: str
    chunk_id: str
    heading: str
    passage: str
    provenance: str
    corpus_version: str
    topic_tags: tuple[str, ...]
    intent_tags: tuple[str, ...]
    relevance_score: float

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "knowledge_domain": "recovery",
            "source_id": self.source_id,
            "source_title": self.source_title,
            "chunk_id": self.chunk_id,
            "heading": self.heading,
            "passage": self.passage,
            "provenance": self.provenance,
            "corpus_version": self.corpus_version,
            "topic_tags": list(self.topic_tags),
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "knowledge_domain": "recovery",
            "knowledge_role": "curated_domain_context",
            "source_title": self.source_title,
            "heading": self.heading,
            "passage": self.passage,
            "provenance": self.provenance,
            "topic_tags": list(self.topic_tags),
            "intent_tags": list(self.intent_tags),
        }


@dataclass(frozen=True)
class RecoveryKnowledgeContext:
    retrieval_version: str
    corpus_version: str
    corpus_digest: str
    question_intents: tuple[str, ...]
    passages: tuple[RecoveryKnowledgePassage, ...]
    suppressed_for_personal_history: bool = False

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "knowledge_domain": "recovery",
            "retrieval_version": self.retrieval_version,
            "corpus_version": self.corpus_version,
            "corpus_digest": self.corpus_digest,
            "question_intents": list(self.question_intents),
            "suppressed_for_personal_history": self.suppressed_for_personal_history,
            "passages": [passage.to_public_dict() for passage in self.passages],
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "knowledge_domain": "recovery",
            "retrieval_version": self.retrieval_version,
            "corpus_version": self.corpus_version,
            "question_intents": list(self.question_intents),
            "passages": [passage.to_prompt_dict() for passage in self.passages],
            "authority_contract": {
                "role": "domain_context_not_personal_evidence",
                "may_explain_general_recovery_concepts": True,
                "may_establish_personal_causation": False,
                "may_change_personal_confidence": False,
                "may_override_personal_facts": False,
                "may_override_application_decisions": False,
                "may_diagnose_or_prescribe_treatment": False,
            },
        }


@dataclass(frozen=True)
class IndexedRecoveryKnowledgeChunk:
    reference_id: str
    source_id: str
    source_title: str
    chunk_id: str
    heading: str
    passage: str
    provenance: str
    topic_tags: tuple[str, ...]
    intent_tags: tuple[str, ...]
    search_terms: tuple[str, ...]
    vector: tuple[tuple[str, float], ...]

    def to_rebuild_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["vector"] = [[term, round(weight, 12)] for term, weight in self.vector]
        return payload


@dataclass(frozen=True)
class RecoveryKnowledgeIndex:
    index_version: str
    corpus_version: str
    corpus_digest: str
    chunks: tuple[IndexedRecoveryKnowledgeChunk, ...]

    def to_rebuild_dict(self) -> dict[str, Any]:
        return {
            "index_version": self.index_version,
            "corpus_version": self.corpus_version,
            "corpus_digest": self.corpus_digest,
            "chunks": [chunk.to_rebuild_dict() for chunk in self.chunks],
        }
