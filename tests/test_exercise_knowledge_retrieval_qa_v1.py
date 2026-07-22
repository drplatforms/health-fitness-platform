from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from services.exercise_knowledge_retrieval_service import (
    DEFAULT_CORPUS_PATH,
    MAX_RETRIEVED_KNOWLEDGE_CHARS,
    MAX_RETRIEVED_KNOWLEDGE_PASSAGES,
    build_exercise_knowledge_index,
    retrieve_exercise_knowledge,
)


@dataclass(frozen=True)
class RetrievalQACase:
    question: str
    expected_chunk_id: str
    expected_source_id: str
    irrelevant_source_ids: tuple[str, ...]


RETRIEVAL_QA_CASES = (
    RetrievalQACase(
        question="Why does my lower back work during unsupported rows?",
        expected_chunk_id="row-hinge-and-trunk-demand-v1",
        expected_source_id="rowing-mechanics",
        irrelevant_source_ids=("arm-isolation-mechanics", "conditioning-fundamentals"),
    ),
    RetrievalQACase(
        question="Why do I feel RDLs more in my back than my hamstrings?",
        expected_chunk_id="rdl-back-demand-boundary-v1",
        expected_source_id="hip-hinge-mechanics",
        irrelevant_source_ids=(
            "horizontal-pressing-mechanics",
            "calf-and-ankle-mechanics",
        ),
    ),
    RetrievalQACase(
        question="How is a Pendlay Row different from a regular Barbell Row?",
        expected_chunk_id="pendlay-versus-continuous-row-v1",
        expected_source_id="rowing-mechanics",
        irrelevant_source_ids=("squat-mechanics", "conditioning-fundamentals"),
    ),
    RetrievalQACase(
        question="What should I do if overhead pressing feels uncomfortable?",
        expected_chunk_id="overhead-press-discomfort-boundary-v1",
        expected_source_id="vertical-pressing-mechanics",
        irrelevant_source_ids=(
            "vertical-pulling-mechanics",
            "calf-and-ankle-mechanics",
        ),
    ),
    RetrievalQACase(
        question="What supported row can I substitute for Barbell Rows?",
        expected_chunk_id="supported-row-substitution-v1",
        expected_source_id="rowing-mechanics",
        irrelevant_source_ids=("conditioning-fundamentals", "arm-isolation-mechanics"),
    ),
    RetrievalQACase(
        question="How deep should I squat?",
        expected_chunk_id="squat-depth-and-range-v1",
        expected_source_id="squat-mechanics",
        irrelevant_source_ids=("rowing-mechanics", "arm-isolation-mechanics"),
    ),
    RetrievalQACase(
        question="How should I brace during a lift?",
        expected_chunk_id="brace-for-repeatable-position-v1",
        expected_source_id="bracing-and-trunk-stability",
        irrelevant_source_ids=("conditioning-fundamentals", "calf-and-ankle-mechanics"),
    ),
    RetrievalQACase(
        question="Why does my technique change as I get fatigued?",
        expected_chunk_id="fatigue-range-drift-v1",
        expected_source_id="fatigue-and-technique",
        irrelevant_source_ids=("arm-isolation-mechanics", "calf-and-ankle-mechanics"),
    ),
    RetrievalQACase(
        question="How should a vertical pull move?",
        expected_chunk_id="vertical-pull-shoulder-and-elbow-path-v1",
        expected_source_id="vertical-pulling-mechanics",
        irrelevant_source_ids=("horizontal-pressing-mechanics", "squat-mechanics"),
    ),
    RetrievalQACase(
        question="How do unilateral and bilateral variations differ?",
        expected_chunk_id="unilateral-versus-bilateral-v1",
        expected_source_id="substitution-and-regression",
        irrelevant_source_ids=("conditioning-fundamentals", "calf-and-ankle-mechanics"),
    ),
)


LEGACY_REFERENCE_IDS = {
    "knowledge:rowing-mechanics:row-hinge-and-trunk-demand-v1",
    "knowledge:rowing-mechanics:row-path-and-common-errors-v1",
    "knowledge:rowing-mechanics:pendlay-versus-continuous-row-v1",
    "knowledge:hip-hinge-mechanics:rdl-position-and-range-v1",
    "knowledge:hip-hinge-mechanics:hinge-common-errors-v1",
    "knowledge:squat-mechanics:balanced-squat-v1",
    "knowledge:squat-mechanics:squat-errors-and-regressions-v1",
    "knowledge:pressing-pulling-fundamentals:pressing-stack-and-control-v1",
    "knowledge:pressing-pulling-fundamentals:vertical-pulling-control-v1",
    "knowledge:bracing-and-trunk-stability:brace-for-repeatable-position-v1",
    "knowledge:fatigue-and-technique:technique-under-fatigue-v1",
    "knowledge:discomfort-boundaries:muscle-effort-versus-concerning-symptoms-v1",
    "knowledge:discomfort-boundaries:first-adjustments-for-discomfort-v1",
    "knowledge:substitution-and-regression:preserve-purpose-not-appearance-v1",
    "knowledge:substitution-and-regression:regression-order-v1",
}


@pytest.mark.parametrize(
    "case", RETRIEVAL_QA_CASES, ids=lambda case: case.expected_chunk_id
)
def test_retrieval_qa_returns_the_expected_concept_without_irrelevant_dominance(
    case: RetrievalQACase,
) -> None:
    context = retrieve_exercise_knowledge(case.question)
    top_two = context.passages[:2]

    assert context.passages
    assert context.passages[0].source_id == case.expected_source_id
    assert case.expected_chunk_id in {passage.chunk_id for passage in top_two}
    assert not set(case.irrelevant_source_ids).intersection(
        passage.source_id for passage in top_two
    )


@pytest.mark.parametrize(
    "question",
    (
        "Why is my Barbell Row getting harder?",
        "What did I log for squats last Tuesday?",
        "Was my last Pull-Up session better than the previous one?",
        "Which RDL load did I use last week?",
    ),
)
def test_personal_history_only_questions_suppress_exercise_knowledge(
    question: str,
) -> None:
    context = retrieve_exercise_knowledge(question)

    assert context.question_intents == ()
    assert context.passages == ()


def test_expanded_retrieval_remains_bounded_at_service_limits() -> None:
    context = retrieve_exercise_knowledge(
        "Compare technique, range, discomfort, fatigue, and substitutions across exercises.",
        max_passages=MAX_RETRIEVED_KNOWLEDGE_PASSAGES + 50,
        max_context_chars=MAX_RETRIEVED_KNOWLEDGE_CHARS + 50_000,
    )

    assert len(context.passages) <= MAX_RETRIEVED_KNOWLEDGE_PASSAGES
    assert sum(len(passage.passage) for passage in context.passages) <= (
        MAX_RETRIEVED_KNOWLEDGE_CHARS
    )


def test_expanded_corpus_preserves_legacy_ids_and_valid_provenance() -> None:
    index = build_exercise_knowledge_index()
    reference_ids = [chunk.reference_id for chunk in index.chunks]
    repository_root = DEFAULT_CORPUS_PATH.parents[1]
    corpus = json.loads(DEFAULT_CORPUS_PATH.read_text(encoding="utf-8"))

    assert len(index.chunks) == 57
    assert len(reference_ids) == len(set(reference_ids))
    assert LEGACY_REFERENCE_IDS.issubset(reference_ids)
    assert all(
        chunk.reference_id == f"knowledge:{chunk.source_id}:{chunk.chunk_id}"
        for chunk in index.chunks
    )
    assert all(
        chunk.provenance.startswith("knowledge/exercise_knowledge_v1.json")
        for chunk in index.chunks
    )
    conditioning = next(
        chunk
        for chunk in index.chunks
        if chunk.source_id == "conditioning-fundamentals"
    )
    assert "health.gov" in conditioning.provenance
    assert "cdc.gov" in conditioning.provenance
    for document in corpus["documents"]:
        assert (repository_root / document["source_path"]).is_file()
        for source in document["derived_from"]:
            if "://" not in source:
                assert (repository_root / source.split("#", maxsplit=1)[0]).is_file()
