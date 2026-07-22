from __future__ import annotations

import json

import pytest

from models.coach_models import CoachEvidenceItem, CoachEvidencePack
from services.exercise_knowledge_retrieval_service import (
    MAX_RETRIEVED_KNOWLEDGE_CHARS,
    MAX_RETRIEVED_KNOWLEDGE_PASSAGES,
    build_exercise_knowledge_index,
    classify_exercise_knowledge_intents,
    retrieve_exercise_knowledge,
)
from services.grounded_coach_service import (
    CoachProviderError,
    ask_grounded_coach,
)


def _personal_evidence_pack() -> CoachEvidencePack:
    item = CoachEvidenceItem(
        reference_id="exercise:42:effort-trend",
        domain="training",
        evidence_type="exercise_effort_trend",
        label="Recent logged effort",
        fact="Average logged RIR was 1 recently versus 3 earlier.",
        confidence="Moderate",
        source="workout_exercise_history_analytics_service",
        observed_at="2026-07-20",
    )
    return CoachEvidencePack(
        pack_version="grounded_coach_evidence_v1",
        user_id=1,
        as_of_date="2026-07-21",
        question_topics=("training",),
        matched_exercise_name="Barbell Row",
        evidence=(item,),
        limitations=(
            "Logged history cannot establish why the lower back felt more involved.",
        ),
        source_services=("workout_exercise_history_analytics_service",),
        confidence="Moderate",
        matched_exercise_context={
            "catalog_exercise_id": 42,
            "name": "Barbell Row",
            "exercise_type": "strength",
            "movement_pattern": "horizontal_pull",
        },
    )


def test_sparse_vector_index_is_deterministic_and_rebuildable() -> None:
    first = build_exercise_knowledge_index()
    second = build_exercise_knowledge_index()

    assert first.to_rebuild_dict() == second.to_rebuild_dict()
    assert first.corpus_version == "exercise_knowledge_corpus_v1"
    assert first.index_version == "exercise_knowledge_sparse_vector_v1"
    assert len(first.chunks) == 57
    assert len(first.corpus_digest) == 64


@pytest.mark.parametrize(
    ("question", "expected_heading"),
    [
        (
            "Why might my lower back be working so hard during Barbell Rows?",
            "Hinge and trunk demand in unsupported rows",
        ),
        (
            "What should I focus on during an RDL?",
            "RDL position and range",
        ),
        (
            "How is a Pendlay Row different from a regular Barbell Row?",
            "Pendlay Row versus a continuous Barbell Row",
        ),
        (
            "What alternatives make sense when an exercise is uncomfortable?",
            "Conservative first adjustments",
        ),
    ],
)
def test_retrieval_selects_relevant_curated_passages(
    question: str, expected_heading: str
) -> None:
    context = retrieve_exercise_knowledge(question)

    assert context.passages
    assert context.passages[0].heading == expected_heading


def test_irrelevant_knowledge_is_suppressed() -> None:
    for question in (
        "Am I making progress?",
        "How has my recovery changed recently?",
        "What did I log last week?",
    ):
        context = retrieve_exercise_knowledge(question)
        assert context.question_intents == ()
        assert context.passages == ()


def test_exercise_identity_and_taxonomy_constrain_retrieval() -> None:
    context = retrieve_exercise_knowledge(
        "What should I focus on during an RDL?",
        matched_exercise_name="Romanian Deadlift",
        exercise_context={
            "exercise_type": "strength",
            "movement_pattern": "hinge",
        },
    )

    headings = {passage.heading for passage in context.passages}
    assert context.matched_exercise_name == "Romanian Deadlift"
    assert "RDL position and range" in headings
    assert "Row path and common row errors" not in headings
    assert "A balanced squat" not in headings


def test_retrieval_context_is_bounded_by_count_and_characters() -> None:
    context = retrieve_exercise_knowledge(
        "What common mistakes, discomfort adjustments, alternatives, and technique cues should I watch for?",
        max_passages=2,
        max_context_chars=700,
    )

    assert len(context.passages) <= 2
    assert sum(len(passage.passage) for passage in context.passages) <= 700
    assert len(context.passages) <= MAX_RETRIEVED_KNOWLEDGE_PASSAGES
    assert sum(len(passage.passage) for passage in context.passages) <= (
        MAX_RETRIEVED_KNOWLEDGE_CHARS
    )


def test_source_references_and_provenance_are_stable_and_inspectable() -> None:
    first = retrieve_exercise_knowledge("What should I focus on during an RDL?")
    second = retrieve_exercise_knowledge("What should I focus on during an RDL?")
    passage = first.passages[0]

    assert [item.reference_id for item in first.passages] == [
        item.reference_id for item in second.passages
    ]
    assert passage.reference_id == (
        "knowledge:hip-hinge-mechanics:rdl-position-and-range-v1"
    )
    assert passage.provenance.startswith("knowledge/exercise_knowledge_v1.json")
    assert passage.to_public_dict()["corpus_version"] == (
        "exercise_knowledge_corpus_v1"
    )


def test_coach_combines_personal_evidence_and_distinct_knowledge_references() -> None:
    pack = _personal_evidence_pack()
    captured: dict[str, object] = {}

    def generate(model, prompt, timeout, schema):
        del model, timeout
        captured["prompt"] = prompt
        captured["schema"] = schema
        knowledge_context = retrieve_exercise_knowledge(
            "Why might my lower back be working so hard during Barbell Rows?",
            matched_exercise_name="Barbell Row",
            exercise_context=pack.matched_exercise_context,
        )
        return json.dumps(
            {
                "answer": (
                    "Your recent rows took more effort at the same load. An unsupported "
                    "row also asks your trunk to hold the hinge, so torso position and "
                    "fatigue are useful possibilities to investigate."
                ),
                "evidence_references": ["exercise:42:effort-trend"],
                "knowledge_references": [knowledge_context.passages[0].reference_id],
                "uncertainty": None,
                "suggested_action": None,
            }
        )

    result = ask_grounded_coach(
        user_id=1,
        question="Why might my lower back be working so hard during Barbell Rows?",
        provider="local",
        model="qwen3:8b",
        local_generate=generate,
        evidence_pack=pack,
        environ={},
    )
    public = result.to_public_dict()

    assert result.supporting_evidence_references == ("exercise:42:effort-trend",)
    assert result.supporting_knowledge_references == (
        "knowledge:rowing-mechanics:row-hinge-and-trunk-demand-v1",
    )
    assert public["supporting_evidence"][0]["domain"] == "training"
    assert public["supporting_knowledge"][0]["source_title"] == "Rowing mechanics"
    assert public["confidence"] == "Moderate"
    assert "domain_context_not_personal_evidence" in captured["prompt"]
    assert "knowledge_references" in captured["schema"]["required"]


def test_knowledge_does_not_gain_personal_authority_or_drive_actions() -> None:
    pack = _personal_evidence_pack()
    knowledge = retrieve_exercise_knowledge(
        "What should I focus on during a Barbell Row?",
        matched_exercise_name="Barbell Row",
        exercise_context=pack.matched_exercise_context,
    )
    knowledge_reference = knowledge.passages[0].reference_id

    def knowledge_only(model, prompt, timeout, schema):
        del model, prompt, timeout, schema
        return json.dumps(
            {
                "answer": "Keep the hinge repeatable and the bar close.",
                "evidence_references": [],
                "knowledge_references": [knowledge_reference],
                "uncertainty": None,
                "suggested_action": None,
            }
        )

    result = ask_grounded_coach(
        user_id=1,
        question="What should I focus on during a Barbell Row?",
        provider="local",
        model="qwen3:8b",
        local_generate=knowledge_only,
        evidence_pack=pack,
        knowledge_context=knowledge,
        environ={},
    )
    assert result.confidence == "Limited"
    assert result.suggested_action is None

    def invalid_action(model, prompt, timeout, schema):
        del model, prompt, timeout, schema
        return json.dumps(
            {
                "answer": "Increase the load.",
                "evidence_references": [],
                "knowledge_references": [knowledge_reference],
                "uncertainty": None,
                "suggested_action": {
                    "action_type": "progression_decision",
                    "decision": "increase_load",
                    "evidence_reference": knowledge_reference,
                },
            }
        )

    with pytest.raises(CoachProviderError) as error:
        ask_grounded_coach(
            user_id=1,
            question="What should I focus on during a Barbell Row?",
            provider="local",
            model="qwen3:8b",
            local_generate=invalid_action,
            evidence_pack=pack,
            knowledge_context=knowledge,
            environ={},
        )

    assert error.value.validation_reasons == ("suggested_action_reference_mismatch",)


def test_question_intent_classifier_does_not_treat_personal_difficulty_as_rag() -> None:
    assert (
        classify_exercise_knowledge_intents("Why is my Barbell Row getting harder?")
        == ()
    )
    assert classify_exercise_knowledge_intents(
        "Why might my lower back be working so hard during Barbell Rows?"
    ) == ("mechanics",)
