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

from models.recovery_knowledge_models import (
    IndexedRecoveryKnowledgeChunk,
    RecoveryKnowledgeContext,
    RecoveryKnowledgeIndex,
    RecoveryKnowledgePassage,
)

RECOVERY_KNOWLEDGE_INDEX_VERSION = "recovery_knowledge_sparse_vector_v1"
RECOVERY_KNOWLEDGE_RETRIEVAL_VERSION = "recovery_knowledge_retrieval_v1"
DEFAULT_CORPUS_PATH = (
    Path(__file__).resolve().parents[1] / "knowledge" / "recovery_knowledge_v1.json"
)
MAX_RETRIEVED_RECOVERY_KNOWLEDGE_PASSAGES = 4
MAX_RETRIEVED_RECOVERY_KNOWLEDGE_CHARS = 2400
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
_COMPARISON_PHRASES = ("versus", " vs ", "difference between", "compare")
_PERSONAL_HISTORY_MARKERS = (
    "my records",
    "my history",
    "my check in",
    "my check ins",
    "my checkin",
    "my checkins",
    "check ins show",
    "last night",
    "last week",
    "this week",
    "this month",
    "yesterday",
    "today",
    "how many",
    "how much",
    "what was my",
    "what were my",
    "did i",
    "have i",
    "do i show",
    "show me",
    "my average",
    "my trend",
    "has my",
    "logged",
    "recorded",
)
_GENERAL_PERSONAL_EXPLANATION_MARKERS = (
    "why might my",
    "why may my",
    "why can my",
    "could my",
    "can my",
    "in general",
)
_QUERY_EXPANSIONS = {
    "poor sleep": "sleep loss duration quality perceived effort training fatigue",
    "sleep duration": "hours amount short sleep opportunity",
    "sleep quality": "restless fragmented continuous restorative sleep",
    "soreness versus pain": "muscle tenderness stiffness sharp focal escalating discomfort boundary",
    "sore after": "delayed soreness doms timing rest day unfamiliar hard training",
    "stress": "life demands perceived recovery fatigue wellbeing",
    "accumulated fatigue": "repeated demand cumulative load residual fatigue several sessions",
    "low motivation": "willingness readiness mixed signals physical mental",
    "active recovery": "easy movement complete rest low demand rest strategy",
    "hydration": "fluid sweat heat duration sufficient exercise context",
    "hard training": "unusually demanding novel high volume residual fatigue soreness",
    "cause": "association personal causation mechanism evidence boundary",
}


class RecoveryKnowledgeCorpusError(ValueError):
    pass


def classify_recovery_knowledge_intents(question: str) -> tuple[str, ...]:
    normalized = _normalize(question)
    words = set(normalized.split())
    if _is_personal_history_only(normalized, words):
        return ()

    intents: list[str] = []
    is_comparison = any(phrase in f" {normalized} " for phrase in _COMPARISON_PHRASES)
    has_sleep = bool(words.intersection({"sleep", "slept", "restless"}))
    has_duration = bool(
        words.intersection({"duration", "hours", "amount", "short", "long"})
    )
    has_quality = bool(
        words.intersection({"quality", "restless", "fragmented", "restorative"})
    )
    has_training = bool(
        words.intersection(
            {"training", "workout", "exercise", "session", "performance"}
        )
    )
    has_recovery = bool(
        words.intersection({"recovery", "recover", "recovered", "readiness"})
    )

    if has_sleep and has_duration:
        intents.append("sleep_duration")
    if has_sleep and has_quality:
        intents.append("sleep_quality")
    if has_sleep and (is_comparison or (has_duration and has_quality)):
        intents.append("sleep_quality_comparison")
    if (
        has_sleep
        and has_training
        and words.intersection(
            {"hard", "harder", "effort", "fatigue", "performance", "feel", "feels"}
        )
    ):
        intents.append("sleep_training_effect")

    has_stress = bool(words.intersection({"stress", "stressed", "strain"}))
    if has_stress and (
        has_recovery
        or has_training
        or words.intersection({"fatigue", "fatigued", "energy", "perceived", "feel"})
    ):
        intents.append("stress_perception")

    has_soreness = bool(words.intersection({"sore", "soreness", "stiff", "stiffness"}))
    has_pain = bool(words.intersection({"pain", "painful", "hurt", "discomfort"}))
    if has_soreness and has_pain:
        intents.extend(("soreness_pain_comparison", "pain_boundary"))
    elif has_pain and words.intersection(
        {"boundary", "difference", "sharp", "focal", "escalating", "recovery"}
    ):
        intents.append("pain_boundary")
    if has_soreness and (
        words.intersection({"after", "remain", "remains", "rest", "delayed", "days"})
        or "rest day" in normalized
    ):
        intents.append("soreness_timing")

    has_fatigue = bool(words.intersection({"fatigue", "fatigued", "tired"}))
    if has_fatigue and words.intersection(
        {"accumulated", "cumulative", "building", "repeated", "several"}
    ):
        intents.append("accumulated_fatigue")
    if words.intersection(
        {"load", "workload", "volume", "intensity", "frequency"}
    ) and (has_recovery or has_fatigue or has_training):
        intents.append("training_load_recovery")

    has_motivation = bool(words.intersection({"motivation", "motivated", "drive"}))
    if has_motivation and (has_recovery or "ready" in words or "readiness" in words):
        intents.append("motivation_readiness")

    has_rest = "rest day" in normalized or bool(words.intersection({"rest", "resting"}))
    has_active_recovery = "active recovery" in normalized
    if has_rest and (has_active_recovery or has_recovery):
        intents.append("rest_strategy")
    if has_active_recovery and (has_rest or is_comparison):
        intents.append("active_recovery_comparison")

    if words.intersection({"vary", "varies", "variable", "variability", "fluctuate"}):
        intents.append("recovery_variability")
    if "baseline" in words and has_recovery:
        intents.append("recovery_variability")
    if words.intersection({"hydration", "hydrated", "dehydration", "fluid", "fluids"}):
        intents.append("hydration_context")
    if (
        words.intersection(
            {"hard", "harder", "unusual", "unusually", "demanding", "novel"}
        )
        and has_training
        and (has_recovery or has_fatigue or has_soreness)
    ):
        intents.append("hard_training_recovery")
    if "perceived recovery" in normalized or (
        "perceived" in words and (has_recovery or has_fatigue)
    ):
        intents.append("perceived_recovery")
    if words.intersection(
        {"cause", "causes", "caused", "causation", "association", "correlation"}
    ):
        if has_recovery or has_sleep or has_stress or has_fatigue or has_training:
            intents.append("causation_boundary")

    return tuple(dict.fromkeys(intents))


def build_recovery_knowledge_index(
    corpus_path: str | Path = DEFAULT_CORPUS_PATH,
) -> RecoveryKnowledgeIndex:
    path = Path(corpus_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryKnowledgeCorpusError(
            f"Unable to load recovery knowledge corpus: {path}"
        ) from exc
    _validate_corpus(payload)

    normalized_payload = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    corpus_digest = hashlib.sha256(normalized_payload.encode("utf-8")).hexdigest()
    raw_chunks = _flatten_corpus_chunks(payload)
    document_terms = [Counter(_index_terms(chunk)) for chunk in raw_chunks]
    document_frequency: Counter[str] = Counter()
    for counts in document_terms:
        document_frequency.update(counts.keys())

    chunks = []
    for raw, term_counts in zip(raw_chunks, document_terms, strict=True):
        vector = _normalized_vector(
            term_counts,
            document_frequency=document_frequency,
            document_count=len(raw_chunks),
        )
        chunks.append(
            IndexedRecoveryKnowledgeChunk(
                reference_id=raw["reference_id"],
                source_id=raw["source_id"],
                source_title=raw["source_title"],
                chunk_id=raw["chunk_id"],
                heading=raw["heading"],
                passage=raw["passage"],
                provenance=raw["provenance"],
                topic_tags=tuple(raw["topic_tags"]),
                intent_tags=tuple(raw["intent_tags"]),
                search_terms=tuple(raw["search_terms"]),
                vector=tuple(sorted(vector.items())),
            )
        )

    return RecoveryKnowledgeIndex(
        index_version=RECOVERY_KNOWLEDGE_INDEX_VERSION,
        corpus_version=payload["corpus_version"],
        corpus_digest=corpus_digest,
        chunks=tuple(sorted(chunks, key=lambda chunk: chunk.reference_id)),
    )


@lru_cache(maxsize=1)
def get_recovery_knowledge_index() -> RecoveryKnowledgeIndex:
    return build_recovery_knowledge_index()


def rebuild_recovery_knowledge_index() -> RecoveryKnowledgeIndex:
    get_recovery_knowledge_index.cache_clear()
    return get_recovery_knowledge_index()


def retrieve_recovery_knowledge(
    question: str,
    *,
    index: RecoveryKnowledgeIndex | None = None,
    max_passages: int = MAX_RETRIEVED_RECOVERY_KNOWLEDGE_PASSAGES,
    max_context_chars: int = MAX_RETRIEVED_RECOVERY_KNOWLEDGE_CHARS,
) -> RecoveryKnowledgeContext:
    active_index = index or get_recovery_knowledge_index()
    normalized = _normalize(question)
    words = set(normalized.split())
    suppressed = _is_personal_history_only(normalized, words)
    intents = classify_recovery_knowledge_intents(question)
    if suppressed or not intents:
        return _empty_context(active_index, (), suppressed=suppressed)

    bounded_passages = max(
        0, min(max_passages, MAX_RETRIEVED_RECOVERY_KNOWLEDGE_PASSAGES)
    )
    bounded_chars = max(
        0, min(max_context_chars, MAX_RETRIEVED_RECOVERY_KNOWLEDGE_CHARS)
    )
    if bounded_passages == 0 or bounded_chars == 0:
        return _empty_context(active_index, intents)

    query_text = _expanded_query_text(question, intents=intents)
    document_frequency = _document_frequency(active_index.chunks)
    query_vector = _normalized_vector(
        Counter(_tokenize(query_text)),
        document_frequency=document_frequency,
        document_count=len(active_index.chunks),
    )

    ranked: list[tuple[float, str, IndexedRecoveryKnowledgeChunk]] = []
    for chunk in active_index.chunks:
        intent_overlap = len(set(intents).intersection(chunk.intent_tags))
        if intent_overlap == 0:
            continue
        score = _cosine(query_vector, dict(chunk.vector))
        score += min(0.48, 0.16 * intent_overlap)
        if score >= MIN_RELEVANCE_SCORE:
            ranked.append((score, chunk.reference_id, chunk))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    selected: list[RecoveryKnowledgePassage] = []
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
            RecoveryKnowledgePassage(
                reference_id=chunk.reference_id,
                source_id=chunk.source_id,
                source_title=chunk.source_title,
                chunk_id=chunk.chunk_id,
                heading=chunk.heading,
                passage=chunk.passage,
                provenance=chunk.provenance,
                corpus_version=active_index.corpus_version,
                topic_tags=chunk.topic_tags,
                intent_tags=chunk.intent_tags,
                relevance_score=round(score, 6),
            )
        )
        selected_chars += passage_chars
        source_counts[chunk.source_id] += 1

    return RecoveryKnowledgeContext(
        retrieval_version=RECOVERY_KNOWLEDGE_RETRIEVAL_VERSION,
        corpus_version=active_index.corpus_version,
        corpus_digest=active_index.corpus_digest,
        question_intents=intents,
        passages=tuple(selected),
    )


def _empty_context(
    index: RecoveryKnowledgeIndex,
    intents: Sequence[str],
    *,
    suppressed: bool = False,
) -> RecoveryKnowledgeContext:
    return RecoveryKnowledgeContext(
        retrieval_version=RECOVERY_KNOWLEDGE_RETRIEVAL_VERSION,
        corpus_version=index.corpus_version,
        corpus_digest=index.corpus_digest,
        question_intents=tuple(intents),
        passages=(),
        suppressed_for_personal_history=suppressed,
    )


def _is_personal_history_only(normalized: str, words: set[str]) -> bool:
    personal = bool(words.intersection({"my", "me", "i"}))
    if not personal:
        return False
    if any(marker in normalized for marker in _GENERAL_PERSONAL_EXPLANATION_MARKERS):
        return False
    return any(marker in normalized for marker in _PERSONAL_HISTORY_MARKERS)


def _validate_corpus(payload: Any) -> None:
    if not isinstance(payload, dict) or set(payload) != {"corpus_version", "documents"}:
        raise RecoveryKnowledgeCorpusError("Invalid recovery knowledge corpus contract")
    if not _nonblank(payload["corpus_version"]):
        raise RecoveryKnowledgeCorpusError("Corpus version must be nonblank")
    documents = payload["documents"]
    if not isinstance(documents, list) or not documents:
        raise RecoveryKnowledgeCorpusError("Recovery knowledge documents are required")

    source_ids: set[str] = set()
    reference_ids: set[str] = set()
    for document in documents:
        expected_document_fields = {
            "source_id",
            "title",
            "source_path",
            "derived_from",
            "topic_tags",
            "chunks",
        }
        if not isinstance(document, dict) or set(document) != expected_document_fields:
            raise RecoveryKnowledgeCorpusError("Invalid knowledge document contract")
        source_id = document["source_id"]
        if not _nonblank(source_id) or source_id in source_ids:
            raise RecoveryKnowledgeCorpusError("Knowledge source IDs must be unique")
        source_ids.add(source_id)
        for field in ("title", "source_path"):
            if not _nonblank(document[field]):
                raise RecoveryKnowledgeCorpusError(
                    f"Knowledge {field} must be nonblank"
                )
        if document["source_path"] != "knowledge/recovery_knowledge_v1.json":
            raise RecoveryKnowledgeCorpusError(
                "Recovery knowledge source_path must identify the canonical corpus"
            )
        for field in ("derived_from", "topic_tags"):
            if not _string_list(document[field], allow_empty=False):
                raise RecoveryKnowledgeCorpusError(
                    f"Knowledge {field} must contain text"
                )
        if not isinstance(document["chunks"], list) or not document["chunks"]:
            raise RecoveryKnowledgeCorpusError("Knowledge documents require chunks")
        chunk_ids: set[str] = set()
        for chunk in document["chunks"]:
            if not isinstance(chunk, dict) or set(chunk) != {
                "chunk_id",
                "heading",
                "intents",
                "search_terms",
                "text",
            }:
                raise RecoveryKnowledgeCorpusError("Invalid knowledge chunk contract")
            chunk_id = chunk["chunk_id"]
            reference_id = f"recovery_knowledge:{source_id}:{chunk_id}"
            if (
                not _nonblank(chunk_id)
                or chunk_id in chunk_ids
                or reference_id in reference_ids
            ):
                raise RecoveryKnowledgeCorpusError("Knowledge chunk IDs must be unique")
            chunk_ids.add(chunk_id)
            reference_ids.add(reference_id)
            if not _nonblank(chunk["heading"]) or not _nonblank(chunk["text"]):
                raise RecoveryKnowledgeCorpusError(
                    "Knowledge chunk text must be nonblank"
                )
            for field in ("intents", "search_terms"):
                if not _string_list(chunk[field], allow_empty=False):
                    raise RecoveryKnowledgeCorpusError(
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
                    "reference_id": (
                        f"recovery_knowledge:{document['source_id']}:{chunk['chunk_id']}"
                    ),
                    "source_id": document["source_id"],
                    "source_title": document["title"],
                    "chunk_id": chunk["chunk_id"],
                    "heading": " ".join(chunk["heading"].split()),
                    "passage": " ".join(chunk["text"].split()),
                    "provenance": provenance,
                    "topic_tags": sorted(set(document["topic_tags"])),
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
        " ".join(chunk["topic_tags"] * 2),
        " ".join(chunk["intent_tags"] * 3),
        " ".join(chunk["search_terms"] * 3),
    ]
    return _tokenize(" ".join(text_parts))


def _expanded_query_text(question: str, *, intents: Sequence[str]) -> str:
    normalized = _normalize(question)
    expansions = [
        expansion
        for phrase, expansion in _QUERY_EXPANSIONS.items()
        if phrase in normalized
    ]
    return " ".join((question, " ".join(expansions), " ".join(intents * 3)))


def _document_frequency(
    chunks: Sequence[IndexedRecoveryKnowledgeChunk],
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


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, allow_empty: bool) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_nonblank(item) for item in value)
        and len(value) == len(set(value))
    )
