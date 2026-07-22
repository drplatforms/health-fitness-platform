from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Literal

from services.workout_progression_decision_service import (
    CurrentExercisePrescription,
    ProgressionDecisionCode,
    build_exercise_progression_decision,
    comparable_working_weight,
)
from services.workout_progression_history_service import (
    ExerciseProgressionSession,
    WorkoutExerciseBestSet,
    classify_exercise_history_logging_quality,
    completed_exercise_actual_rows,
    load_completed_user_progression_sessions,
    select_recent_best_set,
    summarize_exercise_progression_session,
)

DEFAULT_ANALYTICS_LOOKBACK_DAYS = 180
MAX_ANALYTICS_LOOKBACK_DAYS = 365
DEFAULT_ANALYTICS_EXERCISE_LIMIT = 24
MAX_ANALYTICS_EXERCISE_LIMIT = 48
DEFAULT_ANALYTICS_SESSION_LIMIT = 8
MAX_ANALYTICS_SESSION_LIMIT = 12

WorkingLoadTrendStatus = Literal[
    "higher_recently",
    "steady",
    "lower_recently",
    "insufficient_data",
]


@dataclass(frozen=True)
class ExerciseHistoryAnalyticsOverview:
    has_history: bool
    completed_workout_count: int
    completed_set_count: int
    distinct_effective_exercise_count: int
    most_recent_completed_workout_date: str | None


@dataclass(frozen=True)
class ExerciseHistoryRecentSession:
    performed_at: str | None
    completed_set_count: int
    planned_set_count: int
    summary: str
    comparable_working_weight: float | None
    average_actual_rir: float | None
    completed_sets: list[ExerciseHistoryCompletedSet]


@dataclass(frozen=True)
class ExerciseHistoryCompletedSet:
    set_number: int
    actual_reps: int | None
    actual_weight: float | None
    actual_rir: int | None


@dataclass(frozen=True)
class ExerciseHistoryProgressionRecommendation:
    decision: ProgressionDecisionCode
    headline: str
    target_guidance: str
    evidence_session_count: int
    confidence: str


@dataclass(frozen=True)
class RecentWorkingLoadTrend:
    status: WorkingLoadTrendStatus
    latest_comparable_working_weight: float | None
    comparison_working_weight: float | None
    absolute_change_lb: float | None
    qualifying_session_count: int


@dataclass(frozen=True)
class ExerciseHistoryAnalyticsSummary:
    catalog_exercise_id: int | None
    exercise_name: str
    completed_session_count: int
    last_performed_at: str | None
    latest_completed_session_summary: str
    recent_best_set: WorkoutExerciseBestSet | None
    progression_recommendation: ExerciseHistoryProgressionRecommendation
    logging_quality: str
    limitation: str | None
    recent_working_load_trend: RecentWorkingLoadTrend
    recent_sessions: list[ExerciseHistoryRecentSession]


@dataclass(frozen=True)
class WorkoutExerciseHistoryAnalytics:
    overview: ExerciseHistoryAnalyticsOverview
    exercises: list[ExerciseHistoryAnalyticsSummary]


def build_workout_exercise_history_analytics(
    *,
    user_id: int,
    lookback_days: int = DEFAULT_ANALYTICS_LOOKBACK_DAYS,
    exercise_limit: int = DEFAULT_ANALYTICS_EXERCISE_LIMIT,
    session_limit: int = DEFAULT_ANALYTICS_SESSION_LIMIT,
    end_date: str | None = None,
) -> WorkoutExerciseHistoryAnalytics:
    """Build bounded, read-only descriptive exercise history analytics."""

    bounded_lookback = min(
        MAX_ANALYTICS_LOOKBACK_DAYS,
        max(1, int(lookback_days)),
    )
    bounded_exercise_limit = min(
        MAX_ANALYTICS_EXERCISE_LIMIT,
        max(1, int(exercise_limit)),
    )
    bounded_session_limit = min(
        MAX_ANALYTICS_SESSION_LIMIT,
        max(1, int(session_limit)),
    )
    sessions = load_completed_user_progression_sessions(
        user_id=user_id,
        lookback_days=bounded_lookback,
        end_date=end_date,
    )
    return build_workout_exercise_history_analytics_from_sessions(
        user_id=user_id,
        sessions=sessions,
        exercise_limit=bounded_exercise_limit,
        session_limit=bounded_session_limit,
    )


def build_workout_exercise_history_analytics_from_sessions(
    *,
    user_id: int,
    sessions: list[ExerciseProgressionSession],
    exercise_limit: int = DEFAULT_ANALYTICS_EXERCISE_LIMIT,
    session_limit: int = DEFAULT_ANALYTICS_SESSION_LIMIT,
) -> WorkoutExerciseHistoryAnalytics:
    """Build the existing public analytics contract from preloaded history."""

    bounded_exercise_limit = min(
        MAX_ANALYTICS_EXERCISE_LIMIT,
        max(1, int(exercise_limit)),
    )
    bounded_session_limit = min(
        MAX_ANALYTICS_SESSION_LIMIT,
        max(1, int(session_limit)),
    )
    grouped_sessions = _group_sessions_by_effective_identity(sessions)
    ordered_groups = sorted(
        grouped_sessions.values(),
        key=_most_recent_group_sort_key,
        reverse=True,
    )

    overview = _build_overview(sessions, len(grouped_sessions))
    exercises = [
        _build_exercise_summary(user_id, group, bounded_session_limit)
        for group in ordered_groups[:bounded_exercise_limit]
    ]
    return WorkoutExerciseHistoryAnalytics(overview=overview, exercises=exercises)


def _build_overview(
    sessions: list[ExerciseProgressionSession],
    distinct_exercise_count: int,
) -> ExerciseHistoryAnalyticsOverview:
    workout_ids = {session.workout_plan_instance_id for session in sessions}
    completed_row_ids = {
        int(row["id"])
        for session in sessions
        for row in completed_exercise_actual_rows(session)
        if row.get("id") is not None
    }
    performed_dates = [
        session.performed_at for session in sessions if session.performed_at is not None
    ]
    return ExerciseHistoryAnalyticsOverview(
        has_history=bool(workout_ids),
        completed_workout_count=len(workout_ids),
        completed_set_count=len(completed_row_ids),
        distinct_effective_exercise_count=distinct_exercise_count,
        most_recent_completed_workout_date=(
            max(performed_dates) if performed_dates else None
        ),
    )


def _build_exercise_summary(
    user_id: int,
    sessions: list[ExerciseProgressionSession],
    session_limit: int,
) -> ExerciseHistoryAnalyticsSummary:
    ordered = sorted(
        sessions,
        key=lambda session: (
            session.performed_at or "",
            session.workout_plan_instance_id,
        ),
        reverse=True,
    )
    recent = _unique_execution_sessions(ordered)[:session_limit]
    latest_session = summarize_exercise_progression_session(recent[0])
    logging_quality = classify_exercise_history_logging_quality(ordered)
    return ExerciseHistoryAnalyticsSummary(
        catalog_exercise_id=_group_catalog_exercise_id(ordered),
        exercise_name=ordered[0].effective_exercise_name,
        completed_session_count=len(
            {session.workout_execution_session_id for session in ordered}
        ),
        last_performed_at=latest_session.performed_at,
        latest_completed_session_summary=latest_session.summary,
        recent_best_set=select_recent_best_set(ordered),
        progression_recommendation=_progression_recommendation(
            user_id,
            ordered[0],
        ),
        logging_quality=logging_quality,
        limitation=(
            None
            if logging_quality == "complete"
            else "Some sessions have incomplete set, rep, or effort logging."
        ),
        recent_working_load_trend=_working_load_trend(recent),
        recent_sessions=[_build_recent_session(session) for session in recent],
    )


def _build_recent_session(
    session: ExerciseProgressionSession,
) -> ExerciseHistoryRecentSession:
    summary = summarize_exercise_progression_session(session)
    completed_rows = completed_exercise_actual_rows(session)
    rirs = [
        int(row["actual_rir"])
        for row in completed_rows
        if row.get("actual_rir") is not None
    ]
    return ExerciseHistoryRecentSession(
        performed_at=summary.performed_at,
        completed_set_count=summary.completed_set_count,
        planned_set_count=summary.planned_set_count,
        summary=summary.summary,
        comparable_working_weight=comparable_working_weight(session),
        average_actual_rir=round(mean(rirs), 1) if rirs else None,
        completed_sets=[_build_completed_set(row) for row in completed_rows],
    )


def _build_completed_set(row: dict[str, object]) -> ExerciseHistoryCompletedSet:
    return ExerciseHistoryCompletedSet(
        set_number=int(row["set_number"]),
        actual_reps=(
            None if row.get("actual_reps") is None else int(row["actual_reps"])
        ),
        actual_weight=(
            None if row.get("actual_weight") is None else float(row["actual_weight"])
        ),
        actual_rir=(None if row.get("actual_rir") is None else int(row["actual_rir"])),
    )


def _progression_recommendation(
    user_id: int,
    latest_session: ExerciseProgressionSession,
) -> ExerciseHistoryProgressionRecommendation:
    decision = build_exercise_progression_decision(
        user_id=user_id,
        current_exercise=CurrentExercisePrescription(
            exercise_name=latest_session.effective_exercise_name,
            catalog_exercise_id=latest_session.effective_catalog_exercise_id,
            sets=latest_session.planned_set_count,
            reps_min=latest_session.planned_reps_min,
            reps_max=latest_session.planned_reps_max,
            rir_min=latest_session.planned_rir_min,
            rir_max=latest_session.planned_rir_max,
        ),
    )
    return ExerciseHistoryProgressionRecommendation(
        decision=decision.decision,
        headline=decision.headline,
        target_guidance=decision.target_guidance,
        evidence_session_count=decision.evidence_session_count,
        confidence=decision.confidence,
    )


def _working_load_trend(
    sessions: list[ExerciseProgressionSession],
) -> RecentWorkingLoadTrend:
    qualifying = [
        (session, weight)
        for session in sessions
        if (weight := comparable_working_weight(session)) is not None
    ]
    if len(qualifying) < 2:
        return RecentWorkingLoadTrend(
            status="insufficient_data",
            latest_comparable_working_weight=(qualifying[0][1] if qualifying else None),
            comparison_working_weight=None,
            absolute_change_lb=None,
            qualifying_session_count=len(qualifying),
        )

    latest_weight = qualifying[0][1]
    comparison_weight = qualifying[-1][1]
    delta = latest_weight - comparison_weight
    if delta > 0:
        status: WorkingLoadTrendStatus = "higher_recently"
    elif delta < 0:
        status = "lower_recently"
    else:
        status = "steady"
    return RecentWorkingLoadTrend(
        status=status,
        latest_comparable_working_weight=latest_weight,
        comparison_working_weight=comparison_weight,
        absolute_change_lb=round(abs(delta), 2),
        qualifying_session_count=len(qualifying),
    )


def _group_sessions_by_effective_identity(
    sessions: list[ExerciseProgressionSession],
) -> dict[str, list[ExerciseProgressionSession]]:
    catalog_ids_by_name: dict[str, set[int]] = defaultdict(set)
    for session in sessions:
        if session.effective_catalog_exercise_id is not None:
            catalog_ids_by_name[_normalize_name(session.effective_exercise_name)].add(
                session.effective_catalog_exercise_id
            )

    grouped: dict[str, list[ExerciseProgressionSession]] = defaultdict(list)
    for session in sessions:
        normalized_name = _normalize_name(session.effective_exercise_name)
        catalog_id = session.effective_catalog_exercise_id
        if catalog_id is None and len(catalog_ids_by_name[normalized_name]) == 1:
            catalog_id = next(iter(catalog_ids_by_name[normalized_name]))
        identity = (
            f"catalog:{catalog_id}"
            if catalog_id is not None
            else f"name:{normalized_name}"
        )
        grouped[identity].append(session)
    return dict(grouped)


def _group_catalog_exercise_id(
    sessions: list[ExerciseProgressionSession],
) -> int | None:
    catalog_ids = {
        session.effective_catalog_exercise_id
        for session in sessions
        if session.effective_catalog_exercise_id is not None
    }
    return next(iter(catalog_ids)) if len(catalog_ids) == 1 else None


def _unique_execution_sessions(
    sessions: list[ExerciseProgressionSession],
) -> list[ExerciseProgressionSession]:
    unique: list[ExerciseProgressionSession] = []
    seen: set[int] = set()
    for session in sessions:
        if session.workout_execution_session_id in seen:
            continue
        unique.append(session)
        seen.add(session.workout_execution_session_id)
    return unique


def _most_recent_group_sort_key(
    sessions: list[ExerciseProgressionSession],
) -> tuple[str, int]:
    return max(
        (
            session.performed_at or "",
            session.workout_plan_instance_id,
        )
        for session in sessions
    )


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())
