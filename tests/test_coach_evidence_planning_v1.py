from __future__ import annotations

import json
from datetime import date

import pytest

import database
from models.coach_models import CoachConversationTurn
from scripts.seed_longitudinal_qa_data import seed_longitudinal_qa_data
from services.coach_evidence_plan_service import build_coach_evidence_plan
from services.coach_evidence_service import (
    MAX_EVIDENCE_PROMPT_CHARS,
    build_coach_evidence_pack,
)

TARGET = date(2026, 7, 22)
HISTORICAL_TYPES_BY_DOMAIN = {
    "training": "training_history_windows",
    "recovery": "recovery_history_windows",
    "nutrition": "nutrition_history_windows",
    "body_weight": "body_weight_history_periods",
}
BASELINE_TYPES = {
    "user_goal",
    "training_history_overview",
    "current_recovery_checkin",
    "nutrition_logging_quality",
    "body_weight_trend",
}


@pytest.fixture
def rich_seed(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "coach_evidence_planning.db")
    seed_longitudinal_qa_data(end_date=TARGET)


@pytest.mark.parametrize(
    ("question", "kind", "start_date", "mode", "window_days"),
    (
        (
            "Was last week better than the week before?",
            "week_over_week",
            "2026-07-09",
            "adjacent_periods",
            [7, 7],
        ),
        ("Show me the last 14 days", "last_14_days", "2026-07-09", "none", [14]),
        ("Show me the last 28 days", "last_28_days", "2026-06-25", "none", [28]),
        ("Review the last quarter", "last_90_days", "2026-04-24", "none", [30, 30, 30]),
        (
            "Review the last six months",
            "last_6_months",
            "2026-01-23",
            "none",
            [31, 30, 30, 30, 30, 30],
        ),
        (
            "What changed across my last year?",
            "last_year",
            "2025-07-23",
            "none",
            [41, 41, 41, 41, 41, 40, 40, 40, 40],
        ),
    ),
)
def test_planner_recognizes_common_horizons(
    question, kind, start_date, mode, window_days
):
    plan = build_coach_evidence_plan(
        question=question,
        as_of_date=TARGET,
        question_topics=("broad",),
    )

    assert plan.horizon_kind == kind
    assert plan.retrieval_start_date == start_date
    assert plan.retrieval_end_date == "2026-07-22"
    assert plan.comparison_mode == mode
    assert [window.days for window in plan.windows] == window_days


def test_planner_exposes_calendar_months_and_human_short_periods():
    annual = build_coach_evidence_plan(
        question="What changed across my last year?",
        as_of_date=TARGET,
        question_topics=("broad",),
    )
    short = build_coach_evidence_plan(
        question="Show me the last 28 days",
        as_of_date=TARGET,
        question_topics=("training",),
    )
    ninety_days = build_coach_evidence_plan(
        question="Review the last 90 days",
        as_of_date=TARGET,
        question_topics=("training",),
    )
    explicit = build_coach_evidence_plan(
        question="Review training from March 10, 2026 to May 15, 2026",
        as_of_date=TARGET,
        question_topics=("training",),
    )

    assert len(annual.windows) == 9  # Internal analysis partitions stay unchanged.
    assert len(annual.presentation_windows) == 13
    first, full_month, last = (
        annual.presentation_windows[0],
        annual.presentation_windows[1],
        annual.presentation_windows[-1],
    )
    assert (first.start_date, first.end_date, first.days) == (
        "2025-07-23",
        "2025-07-31",
        9,
    )
    assert first.label == "July 23–31, 2025 (partial month)"
    assert first.expected_days == 31
    assert first.is_partial_period is True
    assert (full_month.label, full_month.days, full_month.expected_days) == (
        "August 2025",
        31,
        31,
    )
    assert full_month.is_partial_period is False
    assert (last.start_date, last.end_date, last.days, last.expected_days) == (
        "2026-07-01",
        "2026-07-22",
        22,
        31,
    )
    assert last.is_partial_period is True
    assert [window.days for window in short.presentation_windows] == [14, 14]
    assert all(
        window.label.startswith("the two weeks ending")
        for window in short.presentation_windows
    )
    assert [window.label for window in ninety_days.presentation_windows] == [
        "April 24–30, 2026 (partial month)",
        "May 2026",
        "June 2026",
        "July 1–22, 2026 (partial month)",
    ]
    assert [window.label for window in explicit.presentation_windows] == [
        "March 10–31, 2026 (partial month)",
        "April 2026",
        "May 1–15, 2026 (partial month)",
    ]


def test_planner_supports_explicit_ranges_comparisons_and_bounded_limits():
    explicit = build_coach_evidence_plan(
        question="Compare training from March 1, 2026 to May 15, 2026",
        as_of_date=TARGET,
        question_topics=("training",),
    )
    two_weeks_ago = build_coach_evidence_plan(
        question="Was my recovery worse two weeks ago than it is now?",
        as_of_date=TARGET,
        question_topics=("recovery",),
    )
    capped = build_coach_evidence_plan(
        question="What changed from 2024-01-01 to 2026-07-22?",
        as_of_date=TARGET,
        question_topics=("broad",),
    )
    fourteen_day_comparison = build_coach_evidence_plan(
        question="Compare my last 14 days with the previous 14 days",
        as_of_date=TARGET,
        question_topics=("broad",),
    )

    assert explicit.horizon_kind == "explicit_date_range"
    assert explicit.requested_start_date == "2026-03-01"
    assert explicit.requested_end_date == "2026-05-15"
    assert explicit.comparison_mode == "adjacent_periods"
    assert two_weeks_ago.comparison_mode == "adjacent_periods"
    assert [(item.start_date, item.end_date) for item in two_weeks_ago.windows] == [
        ("2026-07-02", "2026-07-08"),
        ("2026-07-16", "2026-07-22"),
    ]
    assert capped.requested_start_date == "2024-01-01"
    assert capped.retrieval_start_date == "2025-07-23"
    assert {item.code for item in capped.limitations} == {
        "requested_horizon_exceeds_v1_limit"
    }
    assert fourteen_day_comparison.horizon_kind == ("last_14_days_vs_previous_14")
    assert [window.days for window in fourteen_day_comparison.windows] == [14, 14]


def test_plan_inherits_only_prior_user_horizon_and_supplied_subject():
    plan = build_coach_evidence_plan(
        question="What changed on it?",
        as_of_date=TARGET,
        question_topics=("training",),
        conversation_context=(
            CoachConversationTurn(
                role="user",
                content="Show me Dumbbell Bench Press over the last six months.",
            ),
            CoachConversationTurn(
                role="assistant",
                content="I think the relevant period is the last year.",
            ),
        ),
        subject="Dumbbell Bench Press",
        subject_inherited=True,
    )

    assert plan.subject == "Dumbbell Bench Press"
    assert plan.inherited_subject is True
    assert plan.inherited_horizon is True
    assert plan.horizon_kind == "last_6_months"
    assert plan.retrieval_start_date == "2026-01-23"


@pytest.mark.parametrize(
    ("question", "mode", "domains"),
    (
        (
            "What are the biggest changes you see across my last year?",
            "change_points",
            {"training", "recovery", "nutrition", "body_weight"},
        ),
        ("When was my training going best?", "best_period", {"training"}),
        (
            "What happened when my progress started stalling?",
            "change_points",
            {"training", "recovery", "nutrition", "body_weight"},
        ),
        (
            "How did I respond to the deload?",
            "event_response",
            {"training", "recovery"},
        ),
        (
            "Was my recovery worse two weeks ago than it is now?",
            "adjacent_periods",
            {"recovery"},
        ),
        (
            "What patterns seem to keep repeating?",
            "recurring_patterns",
            {"training", "recovery", "nutrition", "body_weight"},
        ),
    ),
)
def test_user_104_open_ended_questions_keep_baseline_and_add_planned_depth(
    rich_seed, question, mode, domains
):
    pack = build_coach_evidence_pack(
        user_id=104,
        question=question,
        as_of_date=TARGET,
    )
    evidence_types = {item.evidence_type for item in pack.evidence}
    prompt = json.dumps(pack.to_prompt_dict(), default=str)

    assert pack.evidence_plan is not None
    assert pack.evidence_plan.comparison_mode == mode
    assert set(pack.evidence_plan.requested_domains) == domains
    assert BASELINE_TYPES.issubset(evidence_types)
    assert {HISTORICAL_TYPES_BY_DOMAIN[domain] for domain in domains}.issubset(
        evidence_types
    )
    assert len(prompt) <= MAX_EVIDENCE_PROMPT_CHARS
    assert "longitudinal_qa_scenario_manifest" not in prompt
    assert "manifest_version" not in prompt
    assert "phase_id" not in prompt
    assert "recovery_decline" not in prompt
    if domains == {"recovery"}:
        summaries = [
            item
            for item in pack.evidence
            if item.evidence_type == "recovery_window_summary"
        ]
        assert {item.structured_data["window_name"] for item in summaries} == {
            "recent_7_days",
            "baseline_28_days",
        }
    if question == "How did I respond to the deload?":
        training = next(
            item
            for item in pack.evidence
            if item.evidence_type == "training_history_windows"
        )
        recovery = next(
            item
            for item in pack.evidence
            if item.evidence_type == "recovery_history_windows"
        )
        training_by_start = {
            item["start_date"]: item for item in training.structured_data["windows"]
        }
        recovery_by_start = {
            item["start_date"]: item for item in recovery.structured_data["windows"]
        }
        assert (
            training_by_start["2026-04-01"]["completed_sets_per_week"]
            < training_by_start["2026-03-01"]["completed_sets_per_week"]
        )
        assert (
            training_by_start["2026-05-01"]["completed_sets_per_week"]
            > training_by_start["2026-04-01"]["completed_sets_per_week"]
        )
        assert (
            recovery_by_start["2026-04-01"]["average_sleep_hours"]
            > recovery_by_start["2026-03-01"]["average_sleep_hours"]
        )
        assert (
            recovery_by_start["2026-04-01"]["average_soreness_level"]
            < recovery_by_start["2026-03-01"]["average_soreness_level"]
        )


def test_user_103_change_questions_retrieve_cross_domain_history_with_log_quality(
    rich_seed,
):
    for question in (
        "What changed when my weight started dropping?",
        "How did my nutrition and training change during the fat-loss phase?",
    ):
        pack = build_coach_evidence_pack(
            user_id=103,
            question=question,
            as_of_date=TARGET,
        )
        evidence_types = {item.evidence_type for item in pack.evidence}
        nutrition = next(
            item
            for item in pack.evidence
            if item.evidence_type == "nutrition_history_windows"
        )

        assert pack.evidence_plan is not None
        assert set(pack.evidence_plan.requested_domains) == {
            "training",
            "recovery",
            "nutrition",
            "body_weight",
        }
        assert set(HISTORICAL_TYPES_BY_DOMAIN.values()).issubset(evidence_types)
        assert any(
            window["partial_logging_day_count"] > 0
            for window in nutrition.structured_data["windows"]
        )
        assert len(json.dumps(pack.to_prompt_dict(), default=str)) <= (
            MAX_EVIDENCE_PROMPT_CHARS
        )


def test_nutrition_measurements_reach_baseline_and_historical_coach_evidence(
    rich_seed,
):
    baseline = build_coach_evidence_pack(
        user_id=104,
        question="Am I more consistent during the week than on weekends?",
        as_of_date=TARGET,
    )
    baseline_nutrition = next(
        item
        for item in baseline.evidence
        if item.evidence_type == "nutrition_logging_quality"
    )
    baseline_types = {
        item["type"] for item in baseline_nutrition.synthesis_data["measurements"]
    }

    assert "weekday_vs_weekend_logging" in baseline_types
    assert "weekday_vs_weekend_intake" in baseline_types
    assert "nutrition_intelligence_service" in baseline.source_services

    cross_domain = build_coach_evidence_pack(
        user_id=104,
        question="Why might training have started feeling harder?",
        as_of_date=TARGET,
    )
    assert {"training", "recovery", "nutrition"}.issubset(
        set(cross_domain.question_topics)
    )
    assert any(
        item.evidence_type == "nutrition_logging_quality"
        for item in cross_domain.evidence
    )

    historical = build_coach_evidence_pack(
        user_id=104,
        question="How did nutrition differ when training was going better?",
        as_of_date=TARGET,
    )
    historical_nutrition = next(
        item
        for item in historical.evidence
        if item.evidence_type == "nutrition_history_windows"
    )
    assert historical.evidence_plan is not None
    assert historical.evidence_plan.comparison_mode == "best_period"
    assert any(
        window["measurements"]
        for window in historical_nutrition.structured_data["windows"]
    )
    prompt = json.dumps(historical.to_prompt_dict(), default=str)
    assert "longitudinal_qa_scenario_manifest" not in prompt
    assert len(prompt) <= MAX_EVIDENCE_PROMPT_CHARS


def test_sparse_and_stable_controls_expose_truthful_coverage(rich_seed):
    stable = build_coach_evidence_pack(
        user_id=102,
        question="What are the biggest changes over the last 90 days?",
        as_of_date=TARGET,
    )
    sparse = build_coach_evidence_pack(
        user_id=105,
        question="What patterns keep repeating over the last six months?",
        as_of_date=TARGET,
    )

    assert stable.evidence_plan is not None
    assert stable.evidence_plan.horizon_kind == "last_90_days"
    assert not stable.evidence_plan.limitations
    assert sparse.evidence_plan is not None
    assert sparse.evidence_plan.limitations
    assert {item.code for item in sparse.evidence_plan.limitations}.intersection(
        {
            "no_history_for_requested_range",
            "partial_history_for_requested_range",
        }
    )
    assert sparse.limitations
    assert len(json.dumps(sparse.to_prompt_dict(), default=str)) <= (
        MAX_EVIDENCE_PROMPT_CHARS
    )


def test_follow_up_inherits_exercise_and_horizon_without_assistant_authority(
    rich_seed,
):
    pack = build_coach_evidence_pack(
        user_id=104,
        question="What changed on it?",
        conversation_context=(
            CoachConversationTurn(
                role="user",
                content=("Show me Dumbbell Bench Press over the last six months."),
            ),
            CoachConversationTurn(
                role="assistant",
                content="The most relevant period is definitely the last year.",
            ),
        ),
        as_of_date=TARGET,
    )

    assert pack.matched_exercise_name == "Dumbbell Bench Press"
    assert pack.evidence_plan is not None
    assert pack.evidence_plan.inherited_subject is True
    assert pack.evidence_plan.inherited_horizon is True
    assert pack.evidence_plan.horizon_kind == "last_6_months"
    assert pack.evidence_plan.retrieval_start_date == "2026-01-23"
    training = next(
        item
        for item in pack.evidence
        if item.evidence_type == "training_history_windows"
    )
    assert training.structured_data["scope"] == "Dumbbell Bench Press"


def test_exact_annual_training_follow_up_keeps_its_explicit_plan_and_pack(rich_seed):
    question = "When was my training going best over the last year?"
    standalone = build_coach_evidence_pack(
        user_id=104,
        question=question,
        as_of_date=TARGET,
    )
    follow_up = build_coach_evidence_pack(
        user_id=104,
        question=question,
        conversation_context=(
            CoachConversationTurn(
                role="user",
                content="What are the biggest changes you see across my last year?",
            ),
            CoachConversationTurn(
                role="assistant",
                content="Prior assistant prose is conversational context only.",
            ),
        ),
        as_of_date=TARGET,
    )

    assert follow_up.evidence_plan is not None
    assert follow_up.evidence_plan.requested_domains == ("training",)
    assert follow_up.evidence_plan.horizon_kind == "last_year"
    assert follow_up.evidence_plan.comparison_mode == "best_period"
    assert follow_up.evidence_plan.subject is None
    assert follow_up.evidence_plan.inherited_horizon is False
    assert follow_up.evidence_plan.inherited_subject is False
    assert follow_up.to_prompt_dict() == standalone.to_prompt_dict()


def test_annual_training_evidence_separates_workload_from_exercise_progression(
    rich_seed,
):
    pack = build_coach_evidence_pack(
        user_id=104,
        question="When was my training going best over the last year?",
        as_of_date=TARGET,
    )
    training = next(
        item
        for item in pack.evidence
        if item.evidence_type == "training_history_windows"
    )
    workload = training.synthesis_data["workload_and_consistency"]
    progression = training.synthesis_data["like_for_like_exercise_progression"]
    public_data = training.to_public_dict()["data"]
    public_workload = public_data["workload_and_consistency"]
    public_progression = public_data["like_for_like_exercise_progression"]

    assert workload["columns"] == [
        "period",
        "workouts",
        "workouts_per_week",
        "completed_sets",
        "completed_sets_per_week",
        "completed_sets_per_workout",
        "set_completion_rate",
        "consistently_trained_exercise_count",
    ]
    assert len(workload["rows"]) == 13
    assert progression["selection_basis"] == "exposure_count_not_performance"
    assert public_progression["selection_basis"] == (
        "highest_exposure_count_strength_exercises_with_stable_catalog_tiebreak"
    )
    assert len(progression["series"]) == 3
    assert {series["exercise_type"] for series in public_progression["series"]} == {
        "strength"
    }
    assert all(len(series["rows"]) == 2 for series in progression["series"])
    assert all(
        series["columns"]
        == [
            "period",
            "exposures",
            "comparable_load_lb",
            "average_reps",
            "average_rir",
        ]
        for series in progression["series"]
    )
    assert all(len(series["rows"]) == 13 for series in public_progression["series"])
    assert public_workload["columns"] == [
        "period",
        "start_date",
        "end_date",
        "days_covered",
        "expected_days",
        "coverage_rate",
        "partial_period",
        "workouts",
        "workouts_per_week",
        "completed_sets",
        "completed_sets_per_week",
        "completed_sets_per_workout",
        "set_completion_rate",
        "consistently_trained_exercise_count",
    ]
    workload_rows = [
        dict(zip(public_workload["columns"], row, strict=True))
        for row in public_workload["rows"]
    ]
    assert workload_rows[0]["partial_period"] is True
    assert workload_rows[0]["coverage_rate"] == round(9 / 31, 3)
    assert workload_rows[-1]["partial_period"] is True
    assert workload_rows[-1]["coverage_rate"] == round(22 / 31, 3)
    assert all(
        row["completed_sets_per_week"]
        == round(row["completed_sets"] * 7 / row["days_covered"], 2)
        for row in workload_rows
    )
    model_history = json.dumps(training.synthesis_data, default=str)
    public_history = json.dumps(public_data, default=str)
    assert "volume_load_lb" not in model_history
    assert "volume_load_lb" not in public_history
    assert "average_load_lb" not in model_history
    assert "average_load_lb" not in public_history
    assert "selected_best_period" not in model_history

    prompt = json.dumps(pack.to_prompt_dict(), default=str)
    public_pack = json.dumps(pack.to_public_dict(), default=str)
    for serialized in (prompt, public_pack):
        assert "segment_" not in serialized
        assert "historical_segment" not in serialized
        assert "40-day" not in serialized
        assert "41-day" not in serialized
    assert len(json.dumps(pack.to_prompt_dict(), default=str)) <= (
        MAX_EVIDENCE_PROMPT_CHARS
    )
