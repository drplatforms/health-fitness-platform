from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExerciseKnowledgePassage:
    reference_id: str
    source_id: str
    source_title: str
    chunk_id: str
    heading: str
    passage: str
    provenance: str
    corpus_version: str
    related_exercises: tuple[str, ...]
    taxonomy_tags: tuple[str, ...]
    intent_tags: tuple[str, ...]
    relevance_score: float

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "source_id": self.source_id,
            "source_title": self.source_title,
            "chunk_id": self.chunk_id,
            "heading": self.heading,
            "passage": self.passage,
            "provenance": self.provenance,
            "corpus_version": self.corpus_version,
            "related_exercises": list(self.related_exercises),
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "knowledge_role": "curated_domain_context",
            "source_title": self.source_title,
            "heading": self.heading,
            "passage": self.passage,
            "provenance": self.provenance,
            "related_exercises": list(self.related_exercises),
            "taxonomy_tags": list(self.taxonomy_tags),
            "intent_tags": list(self.intent_tags),
        }


@dataclass(frozen=True)
class ExerciseKnowledgeContext:
    retrieval_version: str
    corpus_version: str
    corpus_digest: str
    question_intents: tuple[str, ...]
    matched_exercise_name: str | None
    passages: tuple[ExerciseKnowledgePassage, ...]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "retrieval_version": self.retrieval_version,
            "corpus_version": self.corpus_version,
            "corpus_digest": self.corpus_digest,
            "question_intents": list(self.question_intents),
            "matched_exercise_name": self.matched_exercise_name,
            "passages": [passage.to_public_dict() for passage in self.passages],
        }

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "retrieval_version": self.retrieval_version,
            "corpus_version": self.corpus_version,
            "question_intents": list(self.question_intents),
            "matched_exercise_name": self.matched_exercise_name,
            "passages": [passage.to_prompt_dict() for passage in self.passages],
            "authority_contract": {
                "role": "domain_context_not_personal_evidence",
                "may_explain_general_mechanics": True,
                "may_override_personal_facts": False,
                "may_override_application_decisions": False,
                "may_diagnose_or_prescribe_treatment": False,
            },
        }


@dataclass(frozen=True)
class IndexedExerciseKnowledgeChunk:
    reference_id: str
    source_id: str
    source_title: str
    chunk_id: str
    heading: str
    passage: str
    provenance: str
    related_exercises: tuple[str, ...]
    taxonomy_tags: tuple[str, ...]
    intent_tags: tuple[str, ...]
    search_terms: tuple[str, ...]
    vector: tuple[tuple[str, float], ...]

    def to_rebuild_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["vector"] = [[term, round(weight, 12)] for term, weight in self.vector]
        return payload


@dataclass(frozen=True)
class ExerciseKnowledgeIndex:
    index_version: str
    corpus_version: str
    corpus_digest: str
    exercise_aliases: tuple[tuple[str, str], ...]
    chunks: tuple[IndexedExerciseKnowledgeChunk, ...]

    def to_rebuild_dict(self) -> dict[str, Any]:
        return {
            "index_version": self.index_version,
            "corpus_version": self.corpus_version,
            "corpus_digest": self.corpus_digest,
            "exercise_aliases": [list(item) for item in self.exercise_aliases],
            "chunks": [chunk.to_rebuild_dict() for chunk in self.chunks],
        }
