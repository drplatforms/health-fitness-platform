from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from models.exercise_knowledge_models import (
    ExerciseKnowledgeContext,
    ExerciseKnowledgeIndex,
    ExerciseKnowledgePassage,
    IndexedExerciseKnowledgeChunk,
)

EXERCISE_KNOWLEDGE_INDEX_VERSION = "exercise_knowledge_sparse_vector_v1"
EXERCISE_KNOWLEDGE_RETRIEVAL_VERSION = "exercise_knowledge_retrieval_v1"
DEFAULT_CORPUS_PATH = (
    Path(__file__).resolve().parents[1] / "knowledge" / "exercise_knowledge_v1.json"
)
MAX_RETRIEVED_KNOWLEDGE_PASSAGES = 4
MAX_RETRIEVED_KNOWLEDGE_CHARS = 2400
MIN_RELEVANCE_SCORE = 0.18

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "might",
    "my",
    "of",
    "on",
    "or",
    "should",
    "so",
    "than",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "while",
    "why",
    "with",
}
_MECHANICS_TERMS = {
    "alignment",
    "brace",
    "bracing",
    "control",
    "cue",
    "cues",
    "deep",
    "depth",
    "focus",
    "form",
    "mechanics",
    "motion",
    "position",
    "range",
    "rom",
    "setup",
    "stability",
    "stabilize",
    "tempo",
    "technique",
    "torso",
    "working",
}
_ANATOMY_TERMS = {
    "back",
    "chest",
    "core",
    "elbow",
    "hamstring",
    "hamstrings",
    "hip",
    "hips",
    "ankle",
    "ankles",
    "calf",
    "calves",
    "knee",
    "knees",
    "lower back",
    "shoulder",
    "shoulders",
    "trunk",
    "wrist",
    "wrists",
}
_MISTAKE_TERMS = {"avoid", "error", "errors", "mistake", "mistakes", "wrong"}
_COMPARISON_PHRASES = (
    "compare",
    "compared with",
    "differ",
    "different from",
    "difference between",
    "versus",
    " vs ",
)
_SUBSTITUTION_TERMS = {
    "alternative",
    "alternatives",
    "instead",
    "regress",
    "regression",
    "replacement",
    "swap",
    "substitute",
    "substitution",
    "variation",
    "variations",
}
_DISCOMFORT_TERMS = {
    "ache",
    "discomfort",
    "hurt",
    "hurts",
    "numb",
    "pain",
    "painful",
    "pinch",
    "pinching",
    "sharp",
    "tingling",
    "uncomfortable",
    "unstable",
}
_QUERY_EXPANSIONS = {
    "back than": "trunk lumbar brace load range position drift",
    "bracing": "brace trunk ribs pelvis breathing tension stability",
    "brace": "bracing trunk ribs pelvis breathing tension stability",
    "fatigue": "technique form drift range path tempo control load",
    "lower back": "trunk lumbar hinge brace torso fatigue",
    "working hard": "demand fatigue mechanics technique",
    "work so hard": "demand fatigue mechanics technique",
    "watch for": "mistakes errors technique",
    "focus on": "technique cues mechanics",
    "uncomfortable": "discomfort substitution regression support range load",
    "alternative": "substitution regression variation support",
    "different": "comparison difference versus",
    "overhead press": "vertical press shoulder ribs pelvis grip range support",
    "rdl": "romanian deadlift hip hinge hamstrings",
    "squat depth": "range motion comfortable control balance stance heel",
    "supported row": "chest supported horizontal pull trunk hinge bench support",
    "unilateral": "single side one arm one leg balance anti rotation bilateral",
    "bilateral": "both sides two arm two leg stable unilateral",
    "vertical pull": "pull up pulldown elbows ribs shoulder blades control",
}


class ExerciseKnowledgeCorpusError(ValueError):
    pass


def classify_exercise_knowledge_intents(question: str) -> tuple[str, ...]:
    normalized = _normalize(question)
    words = set(normalized.split())
    intents: list[str] = []

    mechanics_anchor = bool(words.intersection(_MECHANICS_TERMS)) or any(
        phrase in normalized
        for phrase in ("how do i", "how should", "what should i focus", "work so hard")
    )
    why_body_mechanics = normalized.startswith("why") and (
        bool(words.intersection(_ANATOMY_TERMS))
        or any(phrase in normalized for phrase in _ANATOMY_TERMS if " " in phrase)
    )
    if mechanics_anchor or why_body_mechanics:
        intents.append("mechanics")
    if words.intersection(_MISTAKE_TERMS) or "watch for" in normalized:
        intents.append("mistakes")
    if any(phrase in f" {normalized} " for phrase in _COMPARISON_PHRASES):
        intents.append("comparison")
    if words.intersection(_SUBSTITUTION_TERMS):
        intents.append("substitution")
    if words.intersection(_DISCOMFORT_TERMS):
        intents.append("discomfort")
    if "fatigue" in words and ("technique" in words or "form" in words):
        intents.append("technique")
    return tuple(dict.fromkeys(intents))


def build_exercise_knowledge_index(
    corpus_path: str | Path = DEFAULT_CORPUS_PATH,
) -> ExerciseKnowledgeIndex:
    path = Path(corpus_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExerciseKnowledgeCorpusError(
            f"Unable to load exercise knowledge corpus: {path}"
        ) from exc
    _validate_corpus(payload)

    normalized_payload = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    corpus_digest = hashlib.sha256(normalized_payload.encode("utf-8")).hexdigest()
    corpus_version = payload["corpus_version"]
    raw_chunks = _flatten_corpus_chunks(payload)
    document_terms = [Counter(_index_terms(chunk)) for chunk in raw_chunks]
    document_frequency: Counter[str] = Counter()
    for counts in document_terms:
        document_frequency.update(counts.keys())
    document_count = len(raw_chunks)

    chunks = []
    for raw, term_counts in zip(raw_chunks, document_terms, strict=True):
        vector = _normalized_vector(
            term_counts,
            document_frequency=document_frequency,
            document_count=document_count,
        )
        chunks.append(
            IndexedExerciseKnowledgeChunk(
                reference_id=raw["reference_id"],
                source_id=raw["source_id"],
                source_title=raw["source_title"],
                chunk_id=raw["chunk_id"],
                heading=raw["heading"],
                passage=raw["passage"],
                provenance=raw["provenance"],
                related_exercises=tuple(raw["related_exercises"]),
                taxonomy_tags=tuple(raw["taxonomy_tags"]),
                intent_tags=tuple(raw["intent_tags"]),
                search_terms=tuple(raw["search_terms"]),
                vector=tuple(sorted(vector.items())),
            )
        )

    return ExerciseKnowledgeIndex(
        index_version=EXERCISE_KNOWLEDGE_INDEX_VERSION,
        corpus_version=corpus_version,
        corpus_digest=corpus_digest,
        exercise_aliases=tuple(sorted(payload["exercise_aliases"].items())),
        chunks=tuple(sorted(chunks, key=lambda chunk: chunk.reference_id)),
    )


@lru_cache(maxsize=1)
def get_exercise_knowledge_index() -> ExerciseKnowledgeIndex:
    return build_exercise_knowledge_index()


def rebuild_exercise_knowledge_index() -> ExerciseKnowledgeIndex:
    get_exercise_knowledge_index.cache_clear()
    return get_exercise_knowledge_index()


def retrieve_exercise_knowledge(
    question: str,
    *,
    matched_exercise_name: str | None = None,
    exercise_context: Mapping[str, Any] | None = None,
    index: ExerciseKnowledgeIndex | None = None,
    max_passages: int = MAX_RETRIEVED_KNOWLEDGE_PASSAGES,
    max_context_chars: int = MAX_RETRIEVED_KNOWLEDGE_CHARS,
) -> ExerciseKnowledgeContext:
    active_index = index or get_exercise_knowledge_index()
    intents = classify_exercise_knowledge_intents(question)
    resolved_exercise_name = matched_exercise_name or _match_exercise_name(
        question, active_index
    )
    if not intents:
        return _empty_context(active_index, (), resolved_exercise_name)

    bounded_passages = max(0, min(max_passages, MAX_RETRIEVED_KNOWLEDGE_PASSAGES))
    bounded_chars = max(0, min(max_context_chars, MAX_RETRIEVED_KNOWLEDGE_CHARS))
    if bounded_passages == 0 or bounded_chars == 0:
        return _empty_context(active_index, intents, resolved_exercise_name)

    taxonomy_tags = _exercise_context_tags(exercise_context)
    query_text = _expanded_query_text(
        question,
        intents=intents,
        matched_exercise_name=resolved_exercise_name,
        taxonomy_tags=taxonomy_tags,
    )
    document_frequency = _document_frequency(active_index.chunks)
    query_vector = _normalized_vector(
        Counter(_tokenize(query_text)),
        document_frequency=document_frequency,
        document_count=len(active_index.chunks),
    )

    ranked: list[tuple[float, str, IndexedExerciseKnowledgeChunk]] = []
    normalized_exercise = _normalize(resolved_exercise_name or "")
    for chunk in active_index.chunks:
        score = _cosine(query_vector, dict(chunk.vector))
        related = {_normalize(name) for name in chunk.related_exercises}
        taxonomy_overlap = len(set(taxonomy_tags).intersection(chunk.taxonomy_tags))
        if (
            normalized_exercise
            and related
            and normalized_exercise not in related
            and taxonomy_overlap == 0
        ):
            continue
        if normalized_exercise and normalized_exercise in related:
            score += 0.55
        intent_overlap = len(set(intents).intersection(chunk.intent_tags))
        score += min(0.36, 0.12 * intent_overlap)
        score += min(0.16, 0.08 * taxonomy_overlap)
        if score >= MIN_RELEVANCE_SCORE:
            ranked.append((score, chunk.reference_id, chunk))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    selected: list[ExerciseKnowledgePassage] = []
    selected_chars = 0
    source_counts: Counter[str] = Counter()
    for score, _, chunk in ranked:
        if len(selected) >= bounded_passages:
            break
        if source_counts[chunk.source_id] >= 2:
            continue
        passage_chars = len(chunk.passage)
        if selected_chars + passage_chars > bounded_chars:
            continue
        selected.append(
            ExerciseKnowledgePassage(
                reference_id=chunk.reference_id,
                source_id=chunk.source_id,
                source_title=chunk.source_title,
                chunk_id=chunk.chunk_id,
                heading=chunk.heading,
                passage=chunk.passage,
                provenance=chunk.provenance,
                corpus_version=active_index.corpus_version,
                related_exercises=chunk.related_exercises,
                taxonomy_tags=chunk.taxonomy_tags,
                intent_tags=chunk.intent_tags,
                relevance_score=round(score, 6),
            )
        )
        selected_chars += passage_chars
        source_counts[chunk.source_id] += 1

    return ExerciseKnowledgeContext(
        retrieval_version=EXERCISE_KNOWLEDGE_RETRIEVAL_VERSION,
        corpus_version=active_index.corpus_version,
        corpus_digest=active_index.corpus_digest,
        question_intents=intents,
        matched_exercise_name=resolved_exercise_name,
        passages=tuple(selected),
    )


def _empty_context(
    index: ExerciseKnowledgeIndex,
    intents: Sequence[str],
    matched_exercise_name: str | None,
) -> ExerciseKnowledgeContext:
    return ExerciseKnowledgeContext(
        retrieval_version=EXERCISE_KNOWLEDGE_RETRIEVAL_VERSION,
        corpus_version=index.corpus_version,
        corpus_digest=index.corpus_digest,
        question_intents=tuple(intents),
        matched_exercise_name=matched_exercise_name,
        passages=(),
    )


def _validate_corpus(payload: Any) -> None:
    if not isinstance(payload, dict) or set(payload) != {
        "corpus_version",
        "exercise_aliases",
        "documents",
    }:
        raise ExerciseKnowledgeCorpusError("Invalid exercise knowledge corpus contract")
    if not _nonblank(payload["corpus_version"]):
        raise ExerciseKnowledgeCorpusError("Corpus version must be nonblank")
    aliases = payload["exercise_aliases"]
    if not isinstance(aliases, dict) or any(
        not _nonblank(alias) or not _nonblank(name) for alias, name in aliases.items()
    ):
        raise ExerciseKnowledgeCorpusError("Exercise aliases must map text to names")
    documents = payload["documents"]
    if not isinstance(documents, list) or not documents:
        raise ExerciseKnowledgeCorpusError("Exercise knowledge documents are required")

    source_ids: set[str] = set()
    reference_ids: set[str] = set()
    for document in documents:
        expected_document_fields = {
            "source_id",
            "title",
            "source_path",
            "derived_from",
            "related_exercises",
            "taxonomy_tags",
            "chunks",
        }
        if not isinstance(document, dict) or set(document) != expected_document_fields:
            raise ExerciseKnowledgeCorpusError("Invalid knowledge document contract")
        source_id = document["source_id"]
        if not _nonblank(source_id) or source_id in source_ids:
            raise ExerciseKnowledgeCorpusError("Knowledge source IDs must be unique")
        source_ids.add(source_id)
        for field in ("title", "source_path"):
            if not _nonblank(document[field]):
                raise ExerciseKnowledgeCorpusError(
                    f"Knowledge {field} must be nonblank"
                )
        for field in ("derived_from", "related_exercises", "taxonomy_tags"):
            if not _string_list(document[field], allow_empty=True):
                raise ExerciseKnowledgeCorpusError(f"Knowledge {field} must be text")
        if not isinstance(document["chunks"], list) or not document["chunks"]:
            raise ExerciseKnowledgeCorpusError("Knowledge documents require chunks")
        chunk_ids: set[str] = set()
        for chunk in document["chunks"]:
            if not isinstance(chunk, dict) or set(chunk) != {
                "chunk_id",
                "heading",
                "intents",
                "search_terms",
                "text",
            }:
                raise ExerciseKnowledgeCorpusError("Invalid knowledge chunk contract")
            chunk_id = chunk["chunk_id"]
            reference_id = f"knowledge:{source_id}:{chunk_id}"
            if (
                not _nonblank(chunk_id)
                or chunk_id in chunk_ids
                or reference_id in reference_ids
            ):
                raise ExerciseKnowledgeCorpusError("Knowledge chunk IDs must be unique")
            chunk_ids.add(chunk_id)
            reference_ids.add(reference_id)
            if not _nonblank(chunk["heading"]) or not _nonblank(chunk["text"]):
                raise ExerciseKnowledgeCorpusError(
                    "Knowledge chunk text must be nonblank"
                )
            for field in ("intents", "search_terms"):
                if not _string_list(chunk[field], allow_empty=False):
                    raise ExerciseKnowledgeCorpusError(
                        f"Knowledge chunk {field} must contain text"
                    )


def _flatten_corpus_chunks(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for document in payload["documents"]:
        provenance = document["source_path"]
        if document["derived_from"]:
            provenance += " (curated from " + "; ".join(document["derived_from"]) + ")"
        for chunk in document["chunks"]:
            flattened.append(
                {
                    "reference_id": f"knowledge:{document['source_id']}:{chunk['chunk_id']}",
                    "source_id": document["source_id"],
                    "source_title": document["title"],
                    "chunk_id": chunk["chunk_id"],
                    "heading": " ".join(chunk["heading"].split()),
                    "passage": " ".join(chunk["text"].split()),
                    "provenance": provenance,
                    "related_exercises": sorted(set(document["related_exercises"])),
                    "taxonomy_tags": sorted(set(document["taxonomy_tags"])),
                    "intent_tags": sorted(set(chunk["intents"])),
                    "search_terms": sorted(set(chunk["search_terms"])),
                }
            )
    return sorted(flattened, key=lambda chunk: chunk["reference_id"])


def _index_terms(chunk: Mapping[str, Any]) -> list[str]:
    text_parts = [
        chunk["source_title"],
        chunk["heading"],
        chunk["heading"],
        chunk["passage"],
        " ".join(chunk["related_exercises"] * 2),
        " ".join(chunk["taxonomy_tags"] * 2),
        " ".join(chunk["intent_tags"] * 3),
        " ".join(chunk["search_terms"] * 3),
    ]
    return _tokenize(" ".join(text_parts))


def _expanded_query_text(
    question: str,
    *,
    intents: Sequence[str],
    matched_exercise_name: str | None,
    taxonomy_tags: Sequence[str],
) -> str:
    normalized = _normalize(question)
    expansions = [
        expansion
        for phrase, expansion in _QUERY_EXPANSIONS.items()
        if phrase in normalized
    ]
    parts = [question, " ".join(expansions), " ".join(intents * 3)]
    if matched_exercise_name:
        parts.append((matched_exercise_name + " ") * 3)
    if taxonomy_tags:
        parts.append(" ".join(taxonomy_tags * 2))
    return " ".join(parts)


def _match_exercise_name(question: str, index: ExerciseKnowledgeIndex) -> str | None:
    normalized = f" {_normalize(question)} "
    candidates: list[tuple[int, str]] = []
    for alias, canonical_name in index.exercise_aliases:
        normalized_alias = _normalize(alias)
        if f" {normalized_alias} " in normalized:
            candidates.append((len(normalized_alias), canonical_name))
    for chunk in index.chunks:
        for name in chunk.related_exercises:
            normalized_name = _normalize(name)
            if normalized_name in normalized.strip():
                candidates.append((len(normalized_name), name))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def _exercise_context_tags(context: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not context:
        return ()
    values = []
    for key in (
        "movement_pattern",
        "family_slug",
        "base_movement_slug",
        "exercise_type",
    ):
        value = context.get(key)
        if isinstance(value, str) and value.strip():
            values.append(_normalize_tag(value))
    return tuple(dict.fromkeys(values))


def _document_frequency(
    chunks: Sequence[IndexedExerciseKnowledgeChunk],
) -> Counter[str]:
    frequency: Counter[str] = Counter()
    for chunk in chunks:
        frequency.update(term for term, _ in chunk.vector)
    return frequency


def _normalized_vector(
    term_counts: Counter[str],
    *,
    document_frequency: Mapping[str, int],
    document_count: int,
) -> dict[str, float]:
    weighted: dict[str, float] = {}
    for term, count in term_counts.items():
        if count <= 0:
            continue
        inverse_document_frequency = (
            math.log((1 + document_count) / (1 + document_frequency.get(term, 0))) + 1.0
        )
        weighted[term] = (1.0 + math.log(count)) * inverse_document_frequency
    magnitude = math.sqrt(sum(value * value for value in weighted.values()))
    if magnitude == 0:
        return {}
    return {term: value / magnitude for term, value in weighted.items()}


def _cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(weight * right.get(term, 0.0) for term, weight in left.items())


def _tokenize(value: str) -> list[str]:
    tokens: list[str] = []
    for raw in _TOKEN_PATTERN.findall(value.lower()):
        if raw in _STOP_WORDS:
            continue
        tokens.append(raw)
        stem = _light_stem(raw)
        if stem != raw and len(stem) >= 3:
            tokens.append(stem)
    return tokens


def _light_stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _normalize(value: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(value.lower()))


def _normalize_tag(value: str) -> str:
    return "_".join(_TOKEN_PATTERN.findall(value.lower()))


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, allow_empty: bool) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_nonblank(item) for item in value)
        and len(value) == len(set(value))
    )
