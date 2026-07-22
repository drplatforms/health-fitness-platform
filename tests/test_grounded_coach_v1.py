from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app
from api.routes import coach as coach_route
from models.ai_run_models import AIProviderTextResult
from models.coach_models import (
    CoachConversationTurn,
    CoachEvidenceItem,
    CoachEvidencePack,
)
from models.exercise_catalog_models import ExerciseCatalogEntry
from models.longitudinal_insight_models import (
    InsightDataCoverage,
    InsightEvidence,
    InsightWindow,
    LongitudinalInsight,
)
from scripts.seed_longitudinal_qa_data import seed_longitudinal_qa_data
from services.coach_evidence_service import (
    MAX_CONVERSATION_TOTAL_CHARS,
    MAX_CONVERSATION_TURNS,
    bound_coach_conversation_context,
    build_coach_evidence_pack,
    build_coach_evidence_pack_from_sources,
    classify_coach_question,
    resolve_referenced_exercise,
)
from services.coach_model_service import build_coach_model_options
from services.grounded_coach_service import (
    CoachProviderError,
    ask_grounded_coach,
)
from services.workout_exercise_history_analytics_service import (
    ExerciseHistoryAnalyticsOverview,
    ExerciseHistoryAnalyticsSummary,
    ExerciseHistoryProgressionRecommendation,
    ExerciseHistoryRecentSession,
    RecentWorkingLoadTrend,
    WorkoutExerciseHistoryAnalytics,
)


def _insight(domain: str, stable_id: str, title: str) -> LongitudinalInsight:
    return LongitudinalInsight(
        stable_id=stable_id,
        domain=domain,
        insight_type=f"{domain}_pattern",
        title=title,
        explanation=f"{title} was observed in the bounded comparison window.",
        observation_window=InsightWindow(
            start_date="2026-07-08",
            end_date="2026-07-21",
            days=14,
            observation_count=7,
            label="recent window",
        ),
        comparison_window=InsightWindow(
            start_date="2026-06-24",
            end_date="2026-07-07",
            days=14,
            observation_count=7,
            label="prior window",
        ),
        evidence=[
            InsightEvidence(
                metric="observed_value",
                label="Observed value",
                value="7 recent observations",
                source="test source",
                source_fields=["observed_value"],
            )
        ],
        evidence_strength="strong",
        data_coverage=InsightDataCoverage(
            status="strong",
            observation_count=7,
            comparison_observation_count=7,
        ),
        direction="stable",
        status="notable",
    )


def _barbell_row_history() -> WorkoutExerciseHistoryAnalytics:
    exercise = ExerciseHistoryAnalyticsSummary(
        catalog_exercise_id=42,
        exercise_name="Barbell Row",
        completed_session_count=4,
        last_performed_at="2026-07-20",
        latest_completed_session_summary="3 of 3 planned sets completed at 100 lb.",
        recent_best_set=None,
        progression_recommendation=ExerciseHistoryProgressionRecommendation(
            decision="hold",
            headline="Hold the current target",
            target_guidance="Keep the current target while effort is reviewed.",
            evidence_session_count=4,
            confidence="Moderate",
        ),
        logging_quality="complete",
        limitation=None,
        recent_working_load_trend=RecentWorkingLoadTrend(
            status="steady",
            latest_comparable_working_weight=100,
            comparison_working_weight=100,
            absolute_change_lb=0,
            qualifying_session_count=4,
        ),
        recent_sessions=[
            ExerciseHistoryRecentSession(
                performed_at="2026-07-20",
                completed_set_count=3,
                planned_set_count=3,
                summary="3 completed sets",
                comparable_working_weight=100,
                average_actual_rir=1,
                completed_sets=[],
            ),
            ExerciseHistoryRecentSession(
                performed_at="2026-07-06",
                completed_set_count=3,
                planned_set_count=3,
                summary="3 completed sets",
                comparable_working_weight=100,
                average_actual_rir=3,
                completed_sets=[],
            ),
        ],
    )
    return WorkoutExerciseHistoryAnalytics(
        overview=ExerciseHistoryAnalyticsOverview(
            has_history=True,
            completed_workout_count=4,
            completed_set_count=12,
            distinct_effective_exercise_count=1,
            most_recent_completed_workout_date="2026-07-20",
        ),
        exercises=[exercise],
    )


def _empty_training() -> WorkoutExerciseHistoryAnalytics:
    return WorkoutExerciseHistoryAnalytics(
        overview=ExerciseHistoryAnalyticsOverview(
            has_history=False,
            completed_workout_count=0,
            completed_set_count=0,
            distinct_effective_exercise_count=0,
            most_recent_completed_workout_date=None,
        ),
        exercises=[],
    )


def _exercise() -> ExerciseCatalogEntry:
    return ExerciseCatalogEntry(
        id=42,
        name="Barbell Row",
        exercise_type="strength",
        movement_pattern="horizontal_pull",
        equipment_required=["barbell", "plates"],
    )


def _provider_pack() -> CoachEvidencePack:
    item = CoachEvidenceItem(
        reference_id="exercise:42:effort-trend",
        domain="training",
        evidence_type="exercise_effort_trend",
        label="Recent logged effort",
        fact="Average logged RIR was 1 recently versus 3 earlier at the same 100 lb load.",
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
        limitations=(),
        source_services=("workout_exercise_history_analytics_service",),
        confidence="Moderate",
    )


def _progression_guidance_pack() -> CoachEvidencePack:
    guidance = CoachEvidenceItem(
        reference_id="exercise:42:progression-decision",
        domain="training",
        evidence_type="deterministic_progression_decision",
        label="Hold the current target",
        fact="Keep the current load and rep target while logged effort is reviewed.",
        confidence="Moderate",
        source="workout_progression_decision_service",
        observed_at="2026-07-20",
        metadata={"decision": "hold"},
    )
    base = _provider_pack()
    return CoachEvidencePack(
        pack_version=base.pack_version,
        user_id=base.user_id,
        as_of_date=base.as_of_date,
        question_topics=base.question_topics,
        matched_exercise_name=base.matched_exercise_name,
        evidence=(*base.evidence, guidance),
        limitations=(),
        source_services=(
            "workout_exercise_history_analytics_service",
            "workout_progression_decision_service",
        ),
        confidence="Moderate",
    )


def _ask_with_raw_output(
    raw_output: str,
    *,
    evidence_pack: CoachEvidencePack | None = None,
):
    def generate(model, prompt, timeout, schema):
        del model, prompt, timeout, schema
        return raw_output

    return ask_grounded_coach(
        user_id=1,
        question="What would you suggest I pay attention to?",
        provider="local",
        model="qwen3:8b",
        local_generate=generate,
        evidence_pack=evidence_pack or _provider_pack(),
        environ={},
    )


def test_exercise_resolution_and_evidence_selection_are_specific_and_repeatable():
    catalog = [
        ExerciseCatalogEntry(
            id=11,
            name="One-Arm Dumbbell Row",
            exercise_type="strength",
            movement_pattern="horizontal_pull",
        ),
        _exercise(),
    ]
    matched = resolve_referenced_exercise(
        "Why is my Barbell Row getting harder?",
        catalog,
    )
    assert matched is not None
    assert matched.id == 42
    topics = classify_coach_question("Why is my Barbell Row getting harder?")
    inputs = {
        "user_id": 1,
        "question": "Why is my Barbell Row getting harder?",
        "as_of_date": "2026-07-21",
        "topics": topics,
        "user_profile": {"primary_goal": "strength"},
        "insights": [
            _insight(
                "training",
                "training:dumbbell-bench-press",
                "Dumbbell Bench Press progressed",
            )
        ],
        "training": _barbell_row_history(),
        "matched_exercise": matched,
        "source_services": ["exercise_catalog_service"],
    }

    first = build_coach_evidence_pack_from_sources(**inputs)
    second = build_coach_evidence_pack_from_sources(**inputs)
    references = {item.reference_id for item in first.evidence}

    assert first == second
    assert first.matched_exercise_name == "Barbell Row"
    assert references >= {
        "exercise:42:catalog",
        "exercise:42:history",
        "exercise:42:load-trend",
        "exercise:42:effort-trend",
    }
    assert "insight:training:dumbbell-bench-press" not in references


def test_question_classification_and_cross_domain_evidence_remain_bounded():
    assert classify_coach_question(
        "What patterns have you noticed in my training?"
    ) == ("training",)
    assert classify_coach_question("What changed in my recovery?") == ("recovery",)

    recovery = SimpleNamespace(
        current_day=None,
        coach_safe_summary="Recent recovery markers were steadier than the prior window.",
        confidence="Moderate",
        target_date="2026-07-21",
        limitations=[],
    )
    nutrition = SimpleNamespace(
        start_date="2026-06-24",
        end_date="2026-07-21",
        window_days=28,
        logged_day_count=24,
        complete_logging_day_count=20,
        partial_logging_day_count=4,
        intake_trend_summary=SimpleNamespace(
            logging_consistency_status="consistent",
            average_calories=2200,
            average_protein_g=170,
            average_carbohydrate_g=230,
            average_fat_g=70,
            confidence="High",
        ),
        bodyweight_trend_summary=SimpleNamespace(
            weigh_in_count=12,
            trend_direction="stable",
            start_weight_lb=180,
            end_weight_lb=180.4,
            weekly_rate_lb=0.1,
            confidence="Moderate",
        ),
        limitations=[],
    )
    topics = classify_coach_question("What changed over the last month?")
    pack = build_coach_evidence_pack_from_sources(
        user_id=1,
        question="What changed over the last month?",
        as_of_date="2026-07-21",
        topics=topics,
        user_profile={"primary_goal": "strength_and_recomposition"},
        insights=[
            _insight("recovery", "recovery:steady", "Recovery steadied"),
            _insight("training", "training:progress", "Working loads increased"),
            _insight("nutrition", "nutrition:logging", "Logging stayed consistent"),
            _insight("body_weight", "weight:stable", "Body weight stayed stable"),
            _insight("cross_domain", "cross:association", "Domains shifted together"),
        ],
        recovery=recovery,
        nutrition=nutrition,
        training=_barbell_row_history(),
        source_services=["longitudinal_insight_service"],
    )

    assert {item.domain for item in pack.evidence} >= {
        "profile",
        "recovery",
        "training",
        "nutrition",
        "body_weight",
        "cross_domain",
    }
    assert len(pack.evidence) <= 16


def test_unsupported_sources_are_suppressed_instead_of_becoming_personal_facts():
    pack = build_coach_evidence_pack_from_sources(
        user_id=1,
        question="Am I making progress?",
        as_of_date="2026-07-21",
        topics=("broad", "training", "recovery", "nutrition", "body_weight"),
        user_profile={"primary_goal": None},
        insights=[],
        recovery=SimpleNamespace(
            current_day=None,
            coach_safe_summary="",
            confidence="Limited",
            target_date="2026-07-21",
            limitations=[],
        ),
        nutrition=SimpleNamespace(
            start_date="2026-06-24",
            end_date="2026-07-21",
            window_days=28,
            logged_day_count=0,
            complete_logging_day_count=0,
            partial_logging_day_count=0,
            intake_trend_summary=SimpleNamespace(
                logging_consistency_status="insufficient_data",
                average_calories=None,
                average_protein_g=None,
                average_carbohydrate_g=None,
                average_fat_g=None,
                confidence="Limited",
            ),
            bodyweight_trend_summary=SimpleNamespace(
                weigh_in_count=0,
                trend_direction="unavailable",
                start_weight_lb=None,
                end_weight_lb=None,
                weekly_rate_lb=None,
                confidence="Limited",
            ),
            limitations=[],
        ),
        training=_empty_training(),
    )

    assert pack.evidence == ()
    assert pack.confidence == "Limited"
    assert any("enough supported evidence" in item for item in pack.limitations)
    assert not any("0 calories" in item for item in pack.limitations)


def test_historical_question_without_comparable_earlier_phase_caps_confidence():
    pack = build_coach_evidence_pack_from_sources(
        user_id=1,
        question="Was I progressing better before?",
        as_of_date="2026-07-21",
        topics=("training", "historical_comparison"),
        user_profile={"primary_goal": "strength"},
        insights=[],
        training=_barbell_row_history(),
        matched_exercise=_exercise(),
    )

    assert pack.confidence == "Limited"
    assert any("did not contain both an earlier" in item for item in pack.limitations)


def test_seeded_user_102_conversation_reaches_synthesis_with_authoritative_evidence(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "seeded_coach_synthesis.db")
    target = date(2026, 6, 14)
    seed_longitudinal_qa_data(end_date=target)
    conversation: list[CoachConversationTurn] = []
    prompts: list[str] = []
    scenarios = (
        (
            "Why is my Barbell Row getting harder?",
            ("exercise_effort_trend",),
            False,
        ),
        (
            "Was I making better progress on it before?",
            (
                "exercise_historical_progression_phase",
                "exercise_current_comparison_phase",
            ),
            False,
        ),
        (
            "What would you suggest I pay attention to?",
            ("exercise_effort_trend", "deterministic_progression_decision"),
            False,
        ),
        (
            "Can I increase the weight, but decrease reps?",
            ("deterministic_progression_decision",),
            True,
        ),
    )

    for index, (question, required_types, include_action) in enumerate(scenarios):
        pack = build_coach_evidence_pack(
            user_id=102,
            question=question,
            conversation_context=conversation,
            as_of_date=target,
        )
        evidence_by_type = {item.evidence_type: item for item in pack.evidence}
        assert pack.matched_exercise_name == "Barbell Row"
        assert set(required_types).issubset(evidence_by_type)
        assert len(pack.evidence) <= 16
        references = [
            evidence_by_type[evidence_type].reference_id
            for evidence_type in required_types
        ]
        if index == 1:
            earlier = evidence_by_type["exercise_historical_progression_phase"]
            current = evidence_by_type["exercise_current_comparison_phase"]
            assert "97.5 to 102.5 lb" in earlier.fact
            assert "RIR moved from 2 to 2" in earlier.fact
            assert "staying near 102.5 lb" in current.fact
            assert "RIR fell from 3 to 2" in current.fact
            assert all("150" not in item.fact for item in pack.evidence)
        if index == 3:
            assert "body_weight" not in pack.question_topics

        action_item = evidence_by_type.get("deterministic_progression_decision")
        suggested_action = None
        if include_action:
            assert action_item is not None
            suggested_action = {
                "action_type": "progression_decision",
                "decision": action_item.metadata["decision"],
                "evidence_reference": action_item.reference_id,
            }

        def generate(
            model,
            prompt,
            timeout,
            schema,
            expected_references=tuple(references),
            expected_action=suggested_action,
        ):
            del model, timeout
            prompts.append(prompt)
            assert "confidence" not in schema["required"]
            assert "suggested_action" in schema["required"]
            return json.dumps(
                {
                    "answer": "A conversational synthesis using the selected observations.",
                    "evidence_references": expected_references,
                    "uncertainty": "The observations do not establish a cause.",
                    "suggested_action": expected_action,
                }
            )

        result = ask_grounded_coach(
            user_id=102,
            question=question,
            provider="local",
            model="qwen3:8b",
            conversation_context=conversation,
            local_generate=generate,
            evidence_pack=pack,
            environ={},
        )

        known_references = {item.reference_id for item in pack.evidence}
        assert set(result.supporting_evidence_references).issubset(known_references)
        assert result.confidence == pack.confidence
        if include_action:
            assert result.suggested_action is not None
            assert result.suggested_action.decision == action_item.metadata["decision"]
            assert (
                result.suggested_action.evidence_reference == action_item.reference_id
            )
        else:
            assert result.suggested_action is None

        assistant_context = (
            "You previously rowed 150 lb." if index == 0 else result.answer
        )
        conversation.extend(
            (
                CoachConversationTurn(role="user", content=question),
                CoachConversationTurn(role="assistant", content=assistant_context),
            )
        )

    assert len(prompts) == 4
    assert "prior assistant messages are never authoritative" in prompts[-1]
    assert '"evidence_role":"authoritative_constraint"' in prompts[-1]


def test_response_contract_returns_known_references_telemetry_and_confidence():
    pack = _provider_pack()

    def generate(model, prompt, timeout, schema):
        del timeout
        assert model == "qwen3:8b"
        assert "exercise:42:effort-trend" in prompt
        assert '"evidence_role":"deterministic_observation"' in prompt
        assert "confidence" not in schema["properties"]
        return AIProviderTextResult(
            text=json.dumps(
                {
                    "answer": "The logged effort pattern changed across the compared sessions.",
                    "evidence_references": ["exercise:42:effort-trend"],
                    "uncertainty": "The history does not establish why effort changed.",
                    "suggested_action": None,
                }
            ),
            model="qwen3:8b",
            input_tokens=180,
            output_tokens=60,
        )

    result = ask_grounded_coach(
        user_id=1,
        question="Why is my Barbell Row getting harder?",
        provider="local",
        model="qwen3:8b",
        local_generate=generate,
        evidence_pack=pack,
        environ={},
    )
    public = result.to_public_dict()

    assert public["supporting_evidence_references"] == ["exercise:42:effort-trend"]
    assert public["supporting_evidence"][0]["fact"] == pack.evidence[0].fact
    assert public["confidence"] == pack.confidence
    assert public["suggested_action"] is None
    assert public["telemetry"]["estimated_api_cost_usd"] == 0.0
    assert public["provider_run"]["actual_model"] == "qwen3:8b"


def test_no_evidence_references_yields_limited_application_confidence():
    raw = json.dumps(
        {
            "answer": "The available history is not enough for a personal conclusion.",
            "evidence_references": [],
            "uncertainty": "The available history is too sparse.",
            "suggested_action": None,
        }
    )

    result = _ask_with_raw_output(raw)

    assert result.supporting_evidence_references == ()
    assert result.confidence == "Limited"


def test_natural_language_is_not_semantically_reinterpreted_after_generation():
    raw = json.dumps(
        {
            "answer": "I would keep the target steady and watch the pattern over the next three sessions.",
            "evidence_references": [
                "exercise:42:effort-trend",
                "exercise:42:progression-decision",
            ],
            "uncertainty": "Logged patterns cannot establish the cause.",
            "suggested_action": None,
        }
    )

    result = _ask_with_raw_output(raw, evidence_pack=_progression_guidance_pack())

    assert result.supporting_evidence_references == (
        "exercise:42:effort-trend",
        "exercise:42:progression-decision",
    )


@pytest.mark.parametrize(
    ("raw_output", "expected_reason"),
    [
        ("not-json", "invalid_response_json"),
        (
            json.dumps(
                {
                    "answer": "An answer.",
                    "evidence_references": [],
                    "uncertainty": None,
                }
            ),
            "invalid_response_contract",
        ),
        (
            json.dumps(
                {
                    "answer": "   ",
                    "evidence_references": [],
                    "uncertainty": None,
                    "suggested_action": None,
                }
            ),
            "invalid_answer_contract",
        ),
        (
            json.dumps(
                {
                    "answer": "An answer.",
                    "evidence_references": [
                        "exercise:42:effort-trend",
                        "exercise:42:effort-trend",
                    ],
                    "uncertainty": None,
                    "suggested_action": None,
                }
            ),
            "invalid_evidence_references",
        ),
        (
            json.dumps(
                {
                    "answer": "An answer.",
                    "evidence_references": [],
                    "uncertainty": ["not", "text"],
                    "suggested_action": None,
                }
            ),
            "invalid_uncertainty_contract",
        ),
    ],
)
def test_only_objective_response_contract_failures_are_rejected(
    raw_output, expected_reason
):
    with pytest.raises(CoachProviderError) as error:
        _ask_with_raw_output(raw_output)

    assert error.value.code == "provider_output_rejected"
    assert error.value.validation_reasons == (expected_reason,)


def test_unknown_evidence_reference_is_rejected_objectively():
    raw = json.dumps(
        {
            "answer": "A synthesis.",
            "evidence_references": ["exercise:42:not-in-pack"],
            "uncertainty": None,
            "suggested_action": None,
        }
    )

    with pytest.raises(CoachProviderError) as error:
        _ask_with_raw_output(raw)

    assert error.value.validation_reasons == ("evidence_reference_mismatch",)


def test_structured_progression_action_is_validated_and_exposed():
    raw = json.dumps(
        {
            "answer": "The current application guidance is to keep the target steady.",
            "evidence_references": ["exercise:42:progression-decision"],
            "uncertainty": None,
            "suggested_action": {
                "action_type": "progression_decision",
                "decision": "hold",
                "evidence_reference": "exercise:42:progression-decision",
            },
        }
    )

    result = _ask_with_raw_output(raw, evidence_pack=_progression_guidance_pack())

    assert result.to_public_dict()["suggested_action"] == {
        "action_type": "progression_decision",
        "decision": "hold",
        "evidence_reference": "exercise:42:progression-decision",
    }


@pytest.mark.parametrize(
    ("references", "action", "expected_reason"),
    [
        (
            ["exercise:42:progression-decision"],
            {
                "action_type": "progression_decision",
                "decision": "increase_load",
                "evidence_reference": "exercise:42:progression-decision",
            },
            "suggested_action_conflict",
        ),
        (
            ["exercise:42:effort-trend"],
            {
                "action_type": "progression_decision",
                "decision": "hold",
                "evidence_reference": "exercise:42:effort-trend",
            },
            "suggested_action_reference_mismatch",
        ),
        (
            ["exercise:42:effort-trend"],
            {
                "action_type": "progression_decision",
                "decision": "hold",
                "evidence_reference": "exercise:42:progression-decision",
            },
            "suggested_action_reference_not_cited",
        ),
        (
            ["exercise:42:progression-decision"],
            {
                "action_type": "progression_decision",
                "decision": ["hold"],
                "evidence_reference": "exercise:42:progression-decision",
            },
            "invalid_suggested_action_contract",
        ),
    ],
)
def test_invalid_structured_actions_are_rejected_objectively(
    references, action, expected_reason
):
    raw = json.dumps(
        {
            "answer": "A synthesis.",
            "evidence_references": references,
            "uncertainty": None,
            "suggested_action": action,
        }
    )

    with pytest.raises(CoachProviderError) as error:
        _ask_with_raw_output(raw, evidence_pack=_progression_guidance_pack())

    assert error.value.validation_reasons == (expected_reason,)


def test_selected_provider_failure_is_controlled_and_has_no_fabricated_fallback():
    calls = []

    def fail_local(model, prompt, timeout, schema):
        calls.append((model, prompt, timeout, schema))
        raise TimeoutError("provider timed out")

    with pytest.raises(CoachProviderError) as error:
        ask_grounded_coach(
            user_id=1,
            question="Am I making progress?",
            provider="local",
            model="qwen3:8b",
            local_generate=fail_local,
            evidence_pack=_provider_pack(),
            environ={},
        )

    assert error.value.code == "local_provider_failed"
    assert "switch providers" in error.value.public_message
    assert len(calls) == 1


def test_openai_coach_path_reaches_shared_adapter_with_mocked_sdk(monkeypatch):
    captured: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return SimpleNamespace(
                output_text=json.dumps(
                    {
                        "answer": "A synthesis from the bounded training observation.",
                        "evidence_references": ["exercise:42:effort-trend"],
                        "uncertainty": None,
                        "suggested_action": None,
                    }
                ),
                model="gpt-5.4-mini-2026-03-17",
                usage=SimpleNamespace(
                    input_tokens=120,
                    input_tokens_details=SimpleNamespace(cached_tokens=20),
                    output_tokens=40,
                ),
            )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.responses = FakeResponses()

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    result = ask_grounded_coach(
        user_id=1,
        question="Why is my Barbell Row getting harder?",
        provider="openai",
        model="gpt-5.4-mini",
        evidence_pack=_provider_pack(),
        environ={"OPENAI_API_KEY": "test-key"},
    )

    request = captured["request"]
    assert isinstance(request, dict)
    assert request["model"] == "gpt-5.4-mini"
    assert request["text"]["format"]["schema"]["required"] == [
        "answer",
        "evidence_references",
        "uncertainty",
        "suggested_action",
    ]
    assert "temperature" not in request
    assert result.supporting_evidence_references == ("exercise:42:effort-trend",)
    assert result.telemetry.model == "gpt-5.4-mini-2026-03-17"


def test_provider_selection_changes_synthesis_only_not_grounding():
    pack = _provider_pack()
    prompts: dict[str, str] = {}

    def response_for(provider):
        def generate(model, prompt, timeout, schema):
            del timeout, schema
            prompts[provider] = prompt
            return AIProviderTextResult(
                text=json.dumps(
                    {
                        "answer": "A provider-specific synthesis.",
                        "evidence_references": ["exercise:42:effort-trend"],
                        "uncertainty": None,
                        "suggested_action": None,
                    }
                ),
                model=model,
                input_tokens=100,
                output_tokens=30,
            )

        return generate

    local = ask_grounded_coach(
        user_id=1,
        question="What changed?",
        provider="local",
        model="qwen3:8b",
        local_generate=response_for("local"),
        evidence_pack=pack,
        environ={},
    )
    openai = ask_grounded_coach(
        user_id=1,
        question="What changed?",
        provider="openai",
        model="gpt-5.4-mini",
        openai_generate=response_for("openai"),
        evidence_pack=pack,
        environ={"OPENAI_API_KEY": "test"},
    )

    assert local.evidence_pack == openai.evidence_pack
    assert prompts["local"] == prompts["openai"]
    assert local.telemetry.provider == "local"
    assert openai.telemetry.provider == "openai"


def test_coach_model_options_reuse_openai_and_ollama_discovery():
    options = build_coach_model_options(
        environ={
            "COACH_PROVIDER": "openai",
            "COACH_LOCAL_MODEL": "configured-local:latest",
            "COACH_OPENAI_MODEL": "gpt-5.4-mini",
        },
        ollama_tags_fetch=lambda base_url, timeout: {
            "models": [{"name": "qwen3:8b"}, {"name": "gemma3:4b"}]
        },
    )

    assert options["configured_provider"] == "openai"
    assert [item["id"] for item in options["providers"]["local"]["models"]] == [
        "qwen3:8b",
        "gemma3:4b",
    ]
    assert options["providers"]["openai"]["default_model"] == "gpt-5.4-mini"


def test_conversation_context_is_bounded_by_turn_and_character_limits():
    turns = [
        CoachConversationTurn(
            role="user" if index % 2 == 0 else "assistant",
            content=f"turn-{index} " + ("x" * 900),
        )
        for index in range(12)
    ]
    bounded = bound_coach_conversation_context(turns)

    assert 0 < len(bounded) <= MAX_CONVERSATION_TURNS
    assert sum(len(turn.content) for turn in bounded) <= MAX_CONVERSATION_TOTAL_CHARS
    assert bounded[-1].content.startswith("turn-11")
    assert all(len(turn.content) <= 600 for turn in bounded)


def test_coach_api_is_user_scoped_and_preserves_provider_selection(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "coach_api.db")
    database.initialize_database()
    captured = {}

    class FakeResult:
        def to_public_dict(self):
            return {
                "success": True,
                "answer": "Grounded answer.",
                "supporting_evidence_references": ["ref:1"],
                "supporting_evidence": [],
                "confidence": "Moderate",
                "uncertainty": None,
                "suggested_action": None,
            }

    def fake_ask(**kwargs):
        captured.update(kwargs)
        return FakeResult()

    monkeypatch.setattr(coach_route, "ask_grounded_coach", fake_ask)
    with TestClient(app) as client:
        response = client.post(
            "/coach/ask",
            json={
                "user_id": 101,
                "question": "Am I making progress?",
                "provider": "openai",
                "model": "gpt-5.4-mini",
                "conversation_context": [
                    {"role": "user", "content": "What about my rows?"}
                ],
            },
        )

    assert response.status_code == 200
    assert captured["user_id"] == 101
    assert captured["provider"] == "openai"
    assert captured["model"] == "gpt-5.4-mini"
    assert captured["conversation_context"][0].role == "user"


def test_coach_model_options_api_uses_shared_provider_boundary(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "coach_models_api.db")
    database.initialize_database()
    expected = {
        "configured_provider": "local",
        "providers": {
            "local": {
                "models": [{"id": "qwen3:8b", "label": "qwen3:8b"}],
                "default_model": "qwen3:8b",
                "source": "ollama",
                "message": None,
            },
            "openai": {
                "models": [{"id": "gpt-5.4-mini", "label": "gpt-5.4-mini"}],
                "default_model": "gpt-5.4-mini",
                "source": "curated",
                "message": None,
            },
        },
    }
    monkeypatch.setattr(coach_route, "build_coach_model_options", lambda: expected)

    with TestClient(app) as client:
        response = client.get("/coach/models")

    assert response.status_code == 200
    assert response.json() == expected


def test_coach_api_returns_controlled_provider_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "coach_api_failure.db")
    database.initialize_database()

    def fail(**kwargs):
        del kwargs
        raise CoachProviderError(
            "local_provider_failed",
            "Local could not answer this Coach question. Retry or switch providers.",
        )

    monkeypatch.setattr(coach_route, "ask_grounded_coach", fail)
    with TestClient(app) as client:
        response = client.post(
            "/coach/ask",
            json={
                "user_id": 101,
                "question": "Am I making progress?",
                "provider": "local",
                "model": "qwen3:8b",
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "local_provider_failed"


def test_coach_api_exposes_objective_contract_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "coach_api_contract.db")
    database.initialize_database()

    def fail(**kwargs):
        del kwargs
        raise CoachProviderError(
            "provider_output_rejected",
            "The selected model returned a response that did not satisfy the Coach synthesis contract. Retry or switch providers.",
            validation_reasons=(
                "invalid_response_contract",
                "suggested_action_conflict",
            ),
        )

    monkeypatch.setattr(coach_route, "ask_grounded_coach", fail)
    with TestClient(app) as client:
        response = client.post(
            "/coach/ask",
            json={
                "user_id": 101,
                "question": "Can I add weight?",
                "provider": "local",
                "model": "qwen3:8b",
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"]["validation_reasons"] == [
        "invalid_response_contract",
        "suggested_action_conflict",
    ]
