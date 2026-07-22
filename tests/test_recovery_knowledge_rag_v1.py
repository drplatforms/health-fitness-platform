from __future__ import annotations

import json

import pytest

from models.coach_models import CoachEvidenceItem, CoachEvidencePack
from services.grounded_coach_service import CoachProviderError, ask_grounded_coach
from services.recovery_knowledge_retrieval_service import (
    MAX_RETRIEVED_RECOVERY_KNOWLEDGE_CHARS,
    MAX_RETRIEVED_RECOVERY_KNOWLEDGE_PASSAGES,
    RECOVERY_KNOWLEDGE_INDEX_VERSION,
    RECOVERY_KNOWLEDGE_RETRIEVAL_VERSION,
    RecoveryKnowledgeCorpusError,
    build_recovery_knowledge_index,
    classify_recovery_knowledge_intents,
    retrieve_recovery_knowledge,
)


@pytest.mark.parametrize(
    ("question", "expected_intents", "expected_chunk_ids"),
    [
        (
            "Why poor sleep may make training feel harder",
            {"sleep_training_effect"},
            {"poor-sleep-perceived-effort-v1"},
        ),
        (
            "Sleep duration versus sleep quality",
            {"sleep_duration", "sleep_quality", "sleep_quality_comparison"},
            {"sleep-duration-and-opportunity-v1", "sleep-quality-is-distinct-v1"},
        ),
        (
            "Soreness versus pain",
            {"soreness_pain_comparison", "pain_boundary"},
            {"soreness-versus-pain-v1"},
        ),
        (
            "How do stress and perceived recovery relate?",
            {"stress_perception", "perceived_recovery"},
            {"stress-can-shape-perception-v1"},
        ),
        (
            "Why might motivation be low despite otherwise supportive recovery?",
            {"motivation_readiness"},
            {"motivation-can-diverge-v1"},
        ),
        (
            "Why may soreness remain after a rest day?",
            {"soreness_timing"},
            {"soreness-can-outlast-rest-day-v1"},
        ),
        (
            "What is accumulated fatigue?",
            {"accumulated_fatigue"},
            {"accumulated-fatigue-is-repeated-demand-v1"},
        ),
        (
            "Active recovery versus complete rest",
            {"rest_strategy", "active_recovery_comparison"},
            {"complete-rest-versus-active-recovery-v1"},
        ),
    ],
)
def test_recovery_retrieval_qa_cases_return_expected_concepts(
    question: str,
    expected_intents: set[str],
    expected_chunk_ids: set[str],
) -> None:
    context = retrieve_recovery_knowledge(question)

    assert expected_intents <= set(context.question_intents)
    assert expected_chunk_ids <= {passage.chunk_id for passage in context.passages}
    assert 1 <= len(context.passages) <= MAX_RETRIEVED_RECOVERY_KNOWLEDGE_PASSAGES
    assert (
        sum(len(passage.passage) for passage in context.passages)
        <= MAX_RETRIEVED_RECOVERY_KNOWLEDGE_CHARS
    )
    assert all(
        passage.reference_id.startswith("recovery_knowledge:")
        for passage in context.passages
    )


@pytest.mark.parametrize(
    "question",
    [
        "How many hours did I sleep last night?",
        "What was my average soreness last week?",
        "Has my stress changed this month?",
        "What do my recovery check-ins show?",
        "Do I show accumulated fatigue in my records?",
    ],
)
def test_personal_history_only_recovery_questions_suppress_knowledge(
    question: str,
) -> None:
    context = retrieve_recovery_knowledge(question)

    assert classify_recovery_knowledge_intents(question) == ()
    assert context.passages == ()
    assert context.suppressed_for_personal_history is True


def test_recovery_corpus_has_stable_valid_identities_and_provenance() -> None:
    first = build_recovery_knowledge_index()
    second = build_recovery_knowledge_index()

    assert first == second
    assert first.index_version == RECOVERY_KNOWLEDGE_INDEX_VERSION
    assert first.corpus_version == "recovery_knowledge_corpus_v1"
    assert len(first.chunks) == 30
    assert len({chunk.reference_id for chunk in first.chunks}) == 30
    assert all(
        chunk.reference_id == f"recovery_knowledge:{chunk.source_id}:{chunk.chunk_id}"
        for chunk in first.chunks
    )
    assert all(
        chunk.provenance.startswith("knowledge/recovery_knowledge_v1.json")
        for chunk in first.chunks
    )
    assert all("curated from https://" in chunk.provenance for chunk in first.chunks)


def test_recovery_retrieval_bounds_caller_requested_limits() -> None:
    context = retrieve_recovery_knowledge(
        "Explain sleep quality, stress, soreness, accumulated fatigue, motivation, active recovery, hydration, and hard training recovery",
        max_passages=999,
        max_context_chars=999_999,
    )

    assert len(context.passages) <= MAX_RETRIEVED_RECOVERY_KNOWLEDGE_PASSAGES
    assert (
        sum(len(passage.passage) for passage in context.passages)
        <= MAX_RETRIEVED_RECOVERY_KNOWLEDGE_CHARS
    )
    assert context.retrieval_version == RECOVERY_KNOWLEDGE_RETRIEVAL_VERSION


def test_invalid_recovery_corpus_provenance_is_rejected(tmp_path) -> None:
    corpus_path = tmp_path / "invalid-recovery-corpus.json"
    corpus_path.write_text(
        json.dumps(
            {
                "corpus_version": "test",
                "documents": [
                    {
                        "source_id": "source",
                        "title": "Title",
                        "source_path": "https://example.com/not-canonical",
                        "derived_from": ["https://example.com/research"],
                        "topic_tags": ["sleep"],
                        "chunks": [
                            {
                                "chunk_id": "chunk-v1",
                                "heading": "Heading",
                                "intents": ["sleep_quality"],
                                "search_terms": ["sleep"],
                                "text": "Original text.",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RecoveryKnowledgeCorpusError):
        build_recovery_knowledge_index(corpus_path)


def _recovery_pack() -> CoachEvidencePack:
    item = CoachEvidenceItem(
        reference_id="recovery:summary:2026-07-21",
        domain="recovery",
        evidence_type="recovery_summary",
        label="Recent recovery summary",
        fact="Recent sleep was below the user's baseline while logged effort was higher.",
        confidence="Moderate",
        source="recovery_intelligence_v2_service",
        observed_at="2026-07-21",
    )
    return CoachEvidencePack(
        pack_version="grounded_coach_evidence_v1",
        user_id=1,
        as_of_date="2026-07-21",
        question_topics=("recovery",),
        matched_exercise_name=None,
        evidence=(item,),
        limitations=("The records show an association, not a cause.",),
        source_services=("recovery_intelligence_v2_service",),
        confidence="Moderate",
    )


def test_grounded_coach_keeps_recovery_evidence_and_knowledge_distinct() -> None:
    pack = _recovery_pack()
    recovery_knowledge = retrieve_recovery_knowledge(
        "Why poor sleep may make training feel harder"
    )
    knowledge_reference = recovery_knowledge.passages[0].reference_id

    def generate(model, prompt, timeout, schema):
        del model, timeout, schema
        assert "RECOVERY_KNOWLEDGE=" in prompt
        assert knowledge_reference in prompt
        assert '"knowledge_domain":"recovery"' in prompt
        assert "may_change_personal_confidence" in prompt
        assert "EXERCISE_KNOWLEDGE=" in prompt
        assert "knowledge:fatigue-and-technique" not in prompt
        return json.dumps(
            {
                "answer": (
                    "Your records show a coincident sleep and effort pattern. "
                    "Poor sleep can generally increase perceived effort, but it does not "
                    "establish the cause of your harder sessions."
                ),
                "evidence_references": [pack.evidence[0].reference_id],
                "knowledge_references": [knowledge_reference],
                "uncertainty": "The personal records establish association, not causation.",
                "suggested_action": None,
            }
        )

    result = ask_grounded_coach(
        user_id=1,
        question="Why poor sleep may make training feel harder",
        provider="local",
        model="qwen3:8b",
        local_generate=generate,
        evidence_pack=pack,
        recovery_knowledge_context=recovery_knowledge,
        environ={},
    )
    public = result.to_public_dict()

    assert result.confidence == pack.confidence
    assert result.knowledge_context.passages == ()
    assert result.recovery_knowledge_context == recovery_knowledge
    assert public["supporting_evidence"][0]["domain"] == "recovery"
    assert public["supporting_knowledge"][0]["knowledge_domain"] == "recovery"
    assert public["recovery_knowledge_context"]["knowledge_domain"] == "recovery"


def test_recovery_knowledge_does_not_raise_application_confidence() -> None:
    recovery_knowledge = retrieve_recovery_knowledge("Soreness versus pain")
    reference = recovery_knowledge.passages[0].reference_id

    def generate(model, prompt, timeout, schema):
        del model, prompt, timeout, schema
        return json.dumps(
            {
                "answer": "Soreness and pain are different general signals.",
                "evidence_references": [],
                "knowledge_references": [reference],
                "uncertainty": None,
                "suggested_action": None,
            }
        )

    result = ask_grounded_coach(
        user_id=1,
        question="Soreness versus pain",
        provider="local",
        model="qwen3:8b",
        local_generate=generate,
        evidence_pack=_recovery_pack(),
        recovery_knowledge_context=recovery_knowledge,
        environ={},
    )

    assert result.confidence == "Limited"


def test_unknown_recovery_knowledge_reference_is_rejected() -> None:
    def generate(model, prompt, timeout, schema):
        del model, prompt, timeout, schema
        return json.dumps(
            {
                "answer": "A general recovery explanation.",
                "evidence_references": [],
                "knowledge_references": ["recovery_knowledge:unknown:unknown-v1"],
                "uncertainty": None,
                "suggested_action": None,
            }
        )

    with pytest.raises(CoachProviderError) as error:
        ask_grounded_coach(
            user_id=1,
            question="Soreness versus pain",
            provider="local",
            model="qwen3:8b",
            local_generate=generate,
            evidence_pack=_recovery_pack(),
            environ={},
        )

    assert error.value.validation_reasons == ("knowledge_reference_mismatch",)
