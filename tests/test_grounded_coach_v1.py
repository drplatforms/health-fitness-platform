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
from models.exercise_knowledge_models import ExerciseKnowledgeContext
from models.longitudinal_insight_models import (
    InsightDataCoverage,
    InsightEvidence,
    InsightWindow,
    LongitudinalInsight,
)
from models.recovery_knowledge_models import RecoveryKnowledgeContext
from scripts.seed_longitudinal_qa_data import seed_longitudinal_qa_data
from services.coach_evidence_service import (
    BASELINE_TRAINING_LOOKBACK_DAYS,
    MAX_BASELINE_LONGITUDINAL_ITEMS,
    MAX_CONVERSATION_TOTAL_CHARS,
    MAX_CONVERSATION_TURNS,
    MAX_EVIDENCE_PROMPT_CHARS,
    bound_coach_conversation_context,
    build_coach_evidence_pack,
    build_coach_evidence_pack_from_sources,
    classify_coach_question,
    resolve_referenced_exercise,
)
from services.coach_model_service import build_coach_model_options
from services.exercise_knowledge_retrieval_service import retrieve_exercise_knowledge
from services.grounded_coach_service import (
    COACH_OPENAI_MAX_OUTPUT_TOKENS,
    MAX_FAILED_OUTPUT_PREVIEW_CHARS,
    MAX_REFERENCE_DIAGNOSTIC_CHARS,
    CoachProviderError,
    ask_grounded_coach,
    build_coach_response_schema,
)
from services.recovery_knowledge_retrieval_service import retrieve_recovery_knowledge
from services.workout_exercise_history_analytics_service import (
    ExerciseHistoryAnalyticsOverview,
    ExerciseHistoryAnalyticsSummary,
    ExerciseHistoryProgressionRecommendation,
    ExerciseHistoryRecentSession,
    RecentWorkingLoadTrend,
    WorkoutExerciseHistoryAnalytics,
)

STRESS_TEST_QUESTION = (
    "Forget giving me the safest answer. Looking at everything you actually have "
    "available, what do you genuinely think is going on with me right now? Walk "
    "me through your reasoning like a great coach would."
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
        structured_data={
            "observation_type": "logged_effort_comparison",
            "exercise_name": "Barbell Row",
            "latest": {
                "performed_at": "2026-07-20",
                "comparable_working_weight_lb": 100,
                "average_actual_rir": 1,
            },
            "comparison": {
                "performed_at": "2026-07-06",
                "comparable_working_weight_lb": 100,
                "average_actual_rir": 3,
            },
        },
        synthesis_data={
            "exercise": "Barbell Row",
            "recent": {
                "performed_at": "2026-07-20",
                "comparable_working_weight_lb": 100,
                "average_actual_rir": 1,
            },
            "previous": {
                "performed_at": "2026-07-06",
                "comparable_working_weight_lb": 100,
                "average_actual_rir": 3,
            },
        },
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
        structured_data={
            "decision": "hold",
            "evidence_session_count": 4,
            "confidence": "Moderate",
        },
        synthesis_data={"evidence_session_count": 4},
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


def _empty_exercise_knowledge_context() -> ExerciseKnowledgeContext:
    return ExerciseKnowledgeContext(
        retrieval_version="test",
        corpus_version="test",
        corpus_digest="test",
        question_intents=(),
        matched_exercise_name=None,
        passages=(),
    )


def _empty_recovery_knowledge_context() -> RecoveryKnowledgeContext:
    return RecoveryKnowledgeContext(
        retrieval_version="test",
        corpus_version="test",
        corpus_digest="test",
        question_intents=(),
        passages=(),
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


def test_exercise_resolution_keeps_baseline_and_adds_specific_depth_repeatably():
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
    assert "insight:training:dumbbell-bench-press" in references


def test_question_classification_and_cross_domain_evidence_remain_bounded():
    assert classify_coach_question(
        "What patterns have you noticed in my training?"
    ) == ("training",)
    assert classify_coach_question("What changed in my recovery?") == ("recovery",)

    recovery = SimpleNamespace(
        current_day=None,
        recent_vs_baseline=None,
        recent_vs_prior=SimpleNamespace(
            comparison_name="recent_vs_prior",
            recent_window_days=7,
            comparison_window_days=7,
            sleep_delta=0.4,
            energy_delta=0.5,
            soreness_delta=-0.5,
            body_weight_delta=None,
            trend_direction="improving",
            confidence="Moderate",
        ),
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
    serialized = json.dumps(pack.to_prompt_dict(), separators=(",", ":"), default=str)
    assert len(serialized) <= MAX_EVIDENCE_PROMPT_CHARS


def test_every_question_gets_whole_person_baseline_and_intent_adds_depth(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "coach_baseline.db")
    target = date(2026, 6, 14)
    seed_longitudinal_qa_data(end_date=target)

    assert classify_coach_question(STRESS_TEST_QUESTION) == ("broad",)
    assert classify_coach_question("What equipment do I have available?") == (
        "equipment",
    )

    baseline_pack = build_coach_evidence_pack(
        user_id=102,
        question=STRESS_TEST_QUESTION,
        as_of_date=target,
    )
    baseline_domains = {item.domain for item in baseline_pack.evidence}
    assert baseline_domains >= {
        "profile",
        "training",
        "recovery",
        "nutrition",
        "body_weight",
    }
    assert "equipment" not in baseline_pack.question_topics
    assert any(
        item.evidence_type == "longitudinal_insight" for item in baseline_pack.evidence
    )
    training_overview = next(
        item
        for item in baseline_pack.evidence
        if item.evidence_type == "training_history_overview"
    )
    assert training_overview.structured_data["window_days"] == (
        BASELINE_TRAINING_LOOKBACK_DAYS
    )
    prompt_payload = json.dumps(
        baseline_pack.to_prompt_dict(), separators=(",", ":"), default=str
    )
    assert len(prompt_payload) <= MAX_EVIDENCE_PROMPT_CHARS
    assert '"evidence_strength"' not in prompt_payload
    assert "stable_load_rising_effort" not in prompt_payload

    exercise_pack = build_coach_evidence_pack(
        user_id=102,
        question="Why is my Barbell Row getting harder?",
        as_of_date=target,
    )
    assert {item.domain for item in exercise_pack.evidence} >= baseline_domains
    assert exercise_pack.matched_exercise_name == "Barbell Row"
    assert {
        "exercise_identity",
        "exercise_history",
        "exercise_effort_trend",
    }.issubset({item.evidence_type for item in exercise_pack.evidence})

    recovery_pack = build_coach_evidence_pack(
        user_id=102,
        question="How has my recovery changed lately?",
        as_of_date=target,
    )
    assert {item.domain for item in recovery_pack.evidence} >= baseline_domains
    assert "recovery" in recovery_pack.question_topics
    assert any(
        item.evidence_type == "recovery_window_comparison"
        for item in recovery_pack.evidence
    )


def test_model_facing_recovery_snapshot_includes_subjective_scale_bounds():
    recovery = SimpleNamespace(
        current_day=SimpleNamespace(
            date="2026-07-21",
            sleep_hours=7.5,
            sleep_quality=4,
            energy_level=7,
            soreness_level=3,
            stress_level=2,
            training_motivation=5,
            pain_concern="none",
            pain_area=None,
            data_quality_status="usable",
        ),
        recent_vs_baseline=None,
        recent_vs_prior=None,
        confidence="Moderate",
        target_date="2026-07-21",
        limitations=[],
    )
    pack = build_coach_evidence_pack_from_sources(
        user_id=1,
        question="How am I doing overall?",
        as_of_date="2026-07-21",
        topics=("broad",),
        user_profile={"primary_goal": None},
        insights=[],
        recovery=recovery,
    )

    recovery_snapshot = pack.to_prompt_dict()["evidence_by_domain"]["recovery"][
        "snapshots"
    ][0]["data"]

    assert recovery_snapshot["sleep_quality"] == {
        "value": 4,
        "scale_min": 1,
        "scale_max": 5,
    }
    assert recovery_snapshot["energy_level"] == {
        "value": 7,
        "scale_min": 1,
        "scale_max": 10,
    }
    assert recovery_snapshot["soreness_level"] == {
        "value": 3,
        "scale_min": 1,
        "scale_max": 10,
    }
    assert recovery_snapshot["stress_level"] == {
        "value": 2,
        "scale_min": 1,
        "scale_max": 5,
    }
    assert recovery_snapshot["training_motivation"] == {
        "value": 5,
        "scale_min": 1,
        "scale_max": 5,
    }
    internal_snapshot = next(
        item
        for item in pack.evidence
        if item.evidence_type == "current_recovery_checkin"
    )
    assert internal_snapshot.structured_data["sleep_quality"] == 4
    assert internal_snapshot.structured_data["energy_level"] == 7


def test_baseline_longitudinal_state_is_domain_balanced_and_bounded():
    insights = [
        _insight(domain, f"{domain}:{index}", f"{domain} observation {index}")
        for domain in (
            "recovery",
            "training",
            "nutrition",
            "body_weight",
            "cross_domain",
        )
        for index in range(3)
    ]
    pack = build_coach_evidence_pack_from_sources(
        user_id=1,
        question="What equipment can I use?",
        as_of_date="2026-07-21",
        topics=("equipment",),
        user_profile={"primary_goal": "strength"},
        insights=insights,
        training=_barbell_row_history(),
    )

    longitudinal = [
        item for item in pack.evidence if item.evidence_type == "longitudinal_insight"
    ]
    assert len(longitudinal) == MAX_BASELINE_LONGITUDINAL_ITEMS
    assert len({item.domain for item in longitudinal}) == len(longitudinal)
    serialized = json.dumps(pack.to_prompt_dict(), separators=(",", ":"), default=str)
    assert len(serialized) <= MAX_EVIDENCE_PROMPT_CHARS


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
            recent_vs_baseline=None,
            recent_vs_prior=None,
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
    assert pack.to_prompt_dict()["evidence_by_domain"] == {}
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
        serialized = json.dumps(
            pack.to_prompt_dict(), separators=(",", ":"), default=str
        )
        assert len(serialized) <= MAX_EVIDENCE_PROMPT_CHARS
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
                    "knowledge_references": [],
                    "uncertainty": None,
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
    assert "Use RECENT_CONVERSATION for dialogue continuity" in prompts[-1]
    assert '"evidence_role":"authoritative_constraint"' in prompts[-1]
    assert "do not establish a cause" not in prompts[-1]
    assert "provider_may_make_causal_claims" not in prompts[-1]
    assert '"previous_average_load_lb"' in prompts[-1]
    assert '"previous_average_rir"' in prompts[-1]
    assert "stable_load_rising_effort" not in prompts[-1]
    assert "rising_effort" not in prompts[-1]
    assert '"evidence_strength"' not in prompts[-1]
    assert '"confidence":"High"' not in prompts[-1]
    assert "Lower RIR means the sets were logged closer to failure" not in prompts[-1]
    assert any('"comparison_name":"recent_vs_baseline"' in prompt for prompt in prompts)
    assert any('"recovery":{' in prompt for prompt in prompts)
    assert all('"evidence":[' not in prompt for prompt in prompts)
    assert all(
        "Reason and communicate according to the strength and coverage" not in prompt
        for prompt in prompts
    )
    assert all(
        "Recent recovery indicators look supportive" not in prompt for prompt in prompts
    )
    assert all(
        "Coincident patterns do not establish causation" not in prompt
        for prompt in prompts
    )
    assert all('"confidence_ceiling"' not in prompt for prompt in prompts)


def test_response_contract_returns_known_references_telemetry_and_confidence():
    pack = _provider_pack()

    def generate(model, prompt, timeout, schema):
        del timeout
        assert model == "qwen3:8b"
        assert "personal_evidence:training:comparisons:1" in prompt
        assert "exercise:42:effort-trend" not in prompt
        assert '"evidence_role":"deterministic_observation"' in prompt
        assert '"data":{"exercise":"Barbell Row","recent"' in prompt
        assert '"observation_type"' not in prompt
        assert '"confidence":"Moderate"' not in prompt
        assert "Average logged RIR was 1 recently" not in prompt
        assert "confidence" not in schema["properties"]
        return AIProviderTextResult(
            text=json.dumps(
                {
                    "answer": "The logged effort pattern changed across the compared sessions.",
                    "evidence_references": ["personal_evidence:training:comparisons:1"],
                    "knowledge_references": [],
                    "uncertainty": None,
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


def test_response_schema_uses_exact_evidence_and_knowledge_aliases():
    pack = _progression_guidance_pack()
    exercise_knowledge = retrieve_exercise_knowledge(
        "What should I focus on during an RDL?"
    )
    recovery_knowledge = retrieve_recovery_knowledge(
        "Why poor sleep may make training feel harder"
    )

    schema = build_coach_response_schema(
        evidence_pack=pack,
        knowledge_context=exercise_knowledge,
        recovery_knowledge_context=recovery_knowledge,
    )

    evidence_schema = schema["properties"]["evidence_references"]
    assert evidence_schema["maxItems"] == 8
    assert evidence_schema["items"]["enum"] == list(
        pack.prompt_reference_aliases().values()
    )
    knowledge_schema = schema["properties"]["knowledge_references"]
    assert knowledge_schema["maxItems"] == 4
    assert knowledge_schema["items"]["enum"] == [
        *(passage.reference_id for passage in exercise_knowledge.passages),
        *(passage.reference_id for passage in recovery_knowledge.passages),
    ]
    assert set(evidence_schema["items"]["enum"]).isdisjoint(
        knowledge_schema["items"]["enum"]
    )


@pytest.mark.parametrize(
    "returned_aliases",
    [
        [],
        ["personal_evidence:training:comparisons:1"],
    ],
)
def test_response_schema_allows_empty_or_valid_evidence_subset(returned_aliases):
    pack = _provider_pack()

    def generate(model, prompt, timeout, schema):
        del model, prompt, timeout
        assert schema["properties"]["evidence_references"]["items"]["enum"] == [
            "personal_evidence:training:comparisons:1"
        ]
        return json.dumps(
            {
                "answer": "A bounded answer.",
                "evidence_references": returned_aliases,
                "knowledge_references": [],
                "uncertainty": None,
                "suggested_action": None,
            }
        )

    result = ask_grounded_coach(
        user_id=1,
        question="What changed?",
        provider="local",
        model="qwen3:8b",
        local_generate=generate,
        evidence_pack=pack,
        knowledge_context=_empty_exercise_knowledge_context(),
        recovery_knowledge_context=_empty_recovery_knowledge_context(),
        environ={},
    )

    expected = ("exercise:42:effort-trend",) if returned_aliases else ()
    assert result.supporting_evidence_references == expected


def test_zero_reference_aliases_require_clean_empty_arrays():
    empty_pack = CoachEvidencePack(
        pack_version="grounded_coach_evidence_v1",
        user_id=1,
        as_of_date="2026-07-21",
        question_topics=("broad",),
        matched_exercise_name=None,
        evidence=(),
        limitations=(),
        source_services=(),
        confidence="Limited",
    )
    empty_exercise_knowledge = _empty_exercise_knowledge_context()
    empty_recovery_knowledge = _empty_recovery_knowledge_context()

    def generate(model, prompt, timeout, schema):
        del model, prompt, timeout
        for field in ("evidence_references", "knowledge_references"):
            reference_schema = schema["properties"][field]
            assert reference_schema["maxItems"] == 0
            assert reference_schema["items"] == {"type": "string"}
            assert "enum" not in reference_schema["items"]
        return json.dumps(
            {
                "answer": "There is no supported context to cite.",
                "evidence_references": [],
                "knowledge_references": [],
                "uncertainty": None,
                "suggested_action": None,
            }
        )

    result = ask_grounded_coach(
        user_id=1,
        question="What is available?",
        provider="local",
        model="qwen3:8b",
        local_generate=generate,
        evidence_pack=empty_pack,
        knowledge_context=empty_exercise_knowledge,
        recovery_knowledge_context=empty_recovery_knowledge,
        environ={},
    )

    assert result.supporting_evidence_references == ()
    assert result.supporting_knowledge_references == ()


def test_no_evidence_references_yields_limited_application_confidence():
    raw = json.dumps(
        {
            "answer": "The available history is not enough for a personal conclusion.",
            "evidence_references": [],
            "knowledge_references": [],
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
            "knowledge_references": [],
            "uncertainty": None,
            "suggested_action": None,
        }
    )

    result = _ask_with_raw_output(raw, evidence_pack=_progression_guidance_pack())

    assert result.supporting_evidence_references == (
        "exercise:42:effort-trend",
        "exercise:42:progression-decision",
    )


@pytest.mark.parametrize(
    "answer",
    [
        "The same load is costing you more effort lately; I would watch whether that persists.",
        "Your recent sets look tougher than the comparison session even though the weight is unchanged.",
        "At 100 lb, logged RIR moved from 3 to 1. That is a meaningful change in effort.",
    ],
)
def test_valid_grounded_reasoning_styles_need_no_disclaimer(answer):
    raw = json.dumps(
        {
            "answer": answer,
            "evidence_references": ["exercise:42:effort-trend"],
            "knowledge_references": [],
            "uncertainty": None,
            "suggested_action": None,
        }
    )

    result = _ask_with_raw_output(raw)

    assert result.answer == answer
    assert result.uncertainty is None


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
                    "knowledge_references": [],
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
                    "knowledge_references": [],
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
                    "knowledge_references": [],
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
            "knowledge_references": [],
            "uncertainty": None,
            "suggested_action": None,
        }
    )

    with pytest.raises(CoachProviderError) as error:
        _ask_with_raw_output(raw)

    assert error.value.validation_reasons == ("evidence_reference_mismatch",)


def test_injected_unknown_alias_still_fails_with_bounded_diagnostics():
    pack = _provider_pack()
    unknown_alias = "personal_evidence:training:comparisons:999:" + ("x" * 500)

    def generate(model, prompt, timeout, schema):
        del prompt, timeout
        assert schema["properties"]["evidence_references"]["items"]["enum"] == [
            "personal_evidence:training:comparisons:1"
        ]
        return AIProviderTextResult(
            text=json.dumps(
                {
                    "answer": "An injected response.",
                    "evidence_references": [unknown_alias],
                    "knowledge_references": [],
                    "uncertainty": None,
                    "suggested_action": None,
                }
            ),
            model=f"{model}-2026-07-15",
            input_tokens=800,
            cached_input_tokens=200,
            output_tokens=80,
            reasoning_tokens=50,
            total_tokens=880,
            response_id="resp_reference_mismatch",
            status="completed",
            max_output_tokens=COACH_OPENAI_MAX_OUTPUT_TOKENS,
        )

    with pytest.raises(CoachProviderError) as error:
        ask_grounded_coach(
            user_id=1,
            question="What changed?",
            provider="openai",
            model="gpt-5.6-sol",
            openai_generate=generate,
            evidence_pack=pack,
            knowledge_context=_empty_exercise_knowledge_context(),
            recovery_knowledge_context=_empty_recovery_knowledge_context(),
            environ={"OPENAI_API_KEY": "test-key"},
        )

    assert error.value.validation_reasons == ("evidence_reference_mismatch",)
    diagnostics = error.value.provider_diagnostics
    assert diagnostics["response_id"] == "resp_reference_mismatch"
    assert diagnostics["actual_model"] == "gpt-5.6-sol-2026-07-15"
    assert diagnostics["status"] == "completed"
    assert diagnostics["usage"] == {
        "input_tokens": 800,
        "cached_input_tokens": 200,
        "output_tokens": 80,
        "reasoning_tokens": 50,
        "total_tokens": 880,
    }
    assert diagnostics["allowed_evidence_aliases"] == [
        "personal_evidence:training:comparisons:1"
    ]
    assert diagnostics["returned_evidence_references"] == [
        unknown_alias[:MAX_REFERENCE_DIAGNOSTIC_CHARS]
    ]
    assert diagnostics["unresolved_evidence_references"] == [
        unknown_alias[:MAX_REFERENCE_DIAGNOSTIC_CHARS]
    ]
    assert diagnostics["reference_diagnostics_truncated"] is True
    assert "raw_output_preview" not in diagnostics


def test_structured_progression_action_is_validated_and_exposed():
    raw = json.dumps(
        {
            "answer": "The current application guidance is to keep the target steady.",
            "evidence_references": [
                "personal_evidence:training:authoritative_constraints:1"
            ],
            "knowledge_references": [],
            "uncertainty": None,
            "suggested_action": {
                "action_type": "progression_decision",
                "decision": "hold",
                "evidence_reference": (
                    "personal_evidence:training:authoritative_constraints:1"
                ),
            },
        }
    )

    result = _ask_with_raw_output(raw, evidence_pack=_progression_guidance_pack())

    assert result.to_public_dict()["suggested_action"] == {
        "action_type": "progression_decision",
        "decision": "hold",
        "evidence_reference": "exercise:42:progression-decision",
    }


def test_structured_progression_action_does_not_require_duplicate_general_reference():
    raw = json.dumps(
        {
            "answer": "The current application guidance is to keep the target steady.",
            "evidence_references": [],
            "knowledge_references": [],
            "uncertainty": None,
            "suggested_action": {
                "action_type": "progression_decision",
                "decision": "hold",
                "evidence_reference": "exercise:42:progression-decision",
            },
        }
    )

    result = _ask_with_raw_output(raw, evidence_pack=_progression_guidance_pack())

    assert result.supporting_evidence_references == ()
    assert result.suggested_action is not None
    assert result.suggested_action.decision == "hold"
    assert (
        result.suggested_action.evidence_reference == "exercise:42:progression-decision"
    )


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
            "knowledge_references": [],
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


@pytest.mark.parametrize(
    ("requested_model", "actual_model"),
    [
        ("gpt-5.4-mini", "gpt-5.4-mini-2026-03-17"),
        ("gpt-5.6-luna", "gpt-5.6-luna-2026-07-15"),
    ],
)
def test_openai_completed_valid_structured_output_uses_shared_adapter(
    monkeypatch,
    requested_model,
    actual_model,
):
    captured: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return SimpleNamespace(
                id="resp_completed",
                output_text=json.dumps(
                    {
                        "answer": "A synthesis from the bounded training observation.",
                        "evidence_references": [
                            "personal_evidence:training:comparisons:1"
                        ],
                        "knowledge_references": [],
                        "uncertainty": None,
                        "suggested_action": None,
                    }
                ),
                model=actual_model,
                status="completed",
                incomplete_details=None,
                usage=SimpleNamespace(
                    input_tokens=120,
                    input_tokens_details=SimpleNamespace(cached_tokens=20),
                    output_tokens=40,
                    output_tokens_details=SimpleNamespace(reasoning_tokens=12),
                    total_tokens=160,
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
        model=requested_model,
        evidence_pack=_provider_pack(),
        environ={"OPENAI_API_KEY": "test-key"},
    )

    request = captured["request"]
    assert isinstance(request, dict)
    assert request["model"] == requested_model
    assert request["max_output_tokens"] == COACH_OPENAI_MAX_OUTPUT_TOKENS
    assert request["text"]["format"]["schema"]["required"] == [
        "answer",
        "evidence_references",
        "knowledge_references",
        "uncertainty",
        "suggested_action",
    ]
    assert request["text"]["format"]["schema"]["properties"]["evidence_references"][
        "items"
    ]["enum"] == ["personal_evidence:training:comparisons:1"]
    assert "temperature" not in request
    assert result.supporting_evidence_references == ("exercise:42:effort-trend",)
    assert result.telemetry.model == actual_model


def test_openai_incomplete_max_tokens_is_distinct_provider_output_failure(
    monkeypatch,
):
    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["max_output_tokens"] == COACH_OPENAI_MAX_OUTPUT_TOKENS
            return SimpleNamespace(
                id="resp_incomplete",
                output_text='{"answer":"partial',
                model="gpt-5.6-sol-2026-07-15",
                status="incomplete",
                incomplete_details=SimpleNamespace(reason="max_output_tokens"),
                usage=SimpleNamespace(
                    input_tokens=2_100,
                    input_tokens_details=SimpleNamespace(cached_tokens=500),
                    output_tokens=2_400,
                    output_tokens_details=SimpleNamespace(reasoning_tokens=2_250),
                    total_tokens=4_500,
                ),
            )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            del kwargs
            self.responses = FakeResponses()

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    with pytest.raises(CoachProviderError) as error:
        ask_grounded_coach(
            user_id=1,
            question="What is going on with me right now?",
            provider="openai",
            model="gpt-5.6-sol",
            evidence_pack=_provider_pack(),
            environ={"OPENAI_API_KEY": "test-key"},
        )

    assert error.value.code == "provider_output_rejected"
    assert error.value.validation_reasons == ("provider_response_incomplete",)
    diagnostics = error.value.provider_diagnostics
    assert diagnostics["response_id"] == "resp_incomplete"
    assert diagnostics["actual_model"] == "gpt-5.6-sol-2026-07-15"
    assert diagnostics["status"] == "incomplete"
    assert diagnostics["incomplete_reason"] == "max_output_tokens"
    assert diagnostics["max_output_tokens"] == COACH_OPENAI_MAX_OUTPUT_TOKENS
    assert diagnostics["usage"] == {
        "input_tokens": 2_100,
        "cached_input_tokens": 500,
        "output_tokens": 2_400,
        "reasoning_tokens": 2_250,
        "total_tokens": 4_500,
    }
    assert "raw_output_preview" not in diagnostics


def test_openai_completed_non_json_output_remains_invalid_response_json(monkeypatch):
    class FakeResponses:
        def create(self, **kwargs):
            del kwargs
            return SimpleNamespace(
                id="resp_invalid_json",
                output_text="not-json",
                model="gpt-5.6-sol-2026-07-15",
                status="completed",
                incomplete_details=None,
                usage=SimpleNamespace(
                    input_tokens=100,
                    input_tokens_details=SimpleNamespace(cached_tokens=0),
                    output_tokens=5,
                    output_tokens_details=SimpleNamespace(reasoning_tokens=0),
                    total_tokens=105,
                ),
            )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            del kwargs
            self.responses = FakeResponses()

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)

    with pytest.raises(CoachProviderError) as error:
        ask_grounded_coach(
            user_id=1,
            question="What changed?",
            provider="openai",
            model="gpt-5.6-sol",
            evidence_pack=_provider_pack(),
            environ={"OPENAI_API_KEY": "test-key"},
        )

    assert error.value.validation_reasons == ("invalid_response_json",)
    assert error.value.provider_diagnostics["status"] == "completed"
    assert error.value.provider_diagnostics["raw_output_preview"] == "not-json"


def test_openai_failure_diagnostics_bound_raw_output_preview():
    raw_output = "x" * (MAX_FAILED_OUTPUT_PREVIEW_CHARS + 75)

    def generate(model, prompt, timeout, schema):
        del prompt, timeout, schema
        return AIProviderTextResult(
            text=raw_output,
            model=f"{model}-2026-07-15",
            input_tokens=900,
            cached_input_tokens=300,
            output_tokens=120,
            reasoning_tokens=80,
            total_tokens=1_020,
            response_id="resp_bounded_preview",
            status="completed",
            max_output_tokens=COACH_OPENAI_MAX_OUTPUT_TOKENS,
        )

    with pytest.raises(CoachProviderError) as error:
        ask_grounded_coach(
            user_id=1,
            question="What changed?",
            provider="openai",
            model="gpt-5.6-sol",
            openai_generate=generate,
            evidence_pack=_provider_pack(),
            environ={"OPENAI_API_KEY": "test-key"},
        )

    diagnostics = error.value.provider_diagnostics
    assert diagnostics["raw_output_length"] == len(raw_output)
    assert len(diagnostics["raw_output_preview"]) == MAX_FAILED_OUTPUT_PREVIEW_CHARS
    assert diagnostics["raw_output_preview_truncated"] is True
    assert diagnostics["actual_model"] == "gpt-5.6-sol-2026-07-15"
    assert diagnostics["usage"]["reasoning_tokens"] == 80


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
                        "knowledge_references": [],
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
            provider_diagnostics={
                "actual_model": "gpt-5.6-sol-2026-07-15",
                "status": "completed",
                "raw_output_preview": "bounded preview",
            },
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
    assert response.json()["detail"]["provider_diagnostics"] == {
        "actual_model": "gpt-5.6-sol-2026-07-15",
        "status": "completed",
        "raw_output_preview": "bounded preview",
    }
