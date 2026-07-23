from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
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
MAX_ANALYTICS_SESSION_LIMIT = 400

WorkingLoadTrendStatus = Literal[
    "higher_recently",
    "steady",
    "lower_recently",
    "insufficient_data",
]
ExerciseMeasurementType = Literal["reps", "duration", "distance"]
ExercisePerformanceModality = Literal[
    "externally_weighted",
    "bodyweight",
    "timed",
    "carry",
    "cardio",
    "distance",
]
ExercisePerformanceMetricType = Literal["load", "reps", "duration", "distance"]
ExercisePerformanceMetricUnit = Literal["lb", "reps", "seconds", "meters"]
ExercisePerformancePhaseCode = Literal[
    "progression",
    "stable_effort_rise",
    "plateau",
    "deload",
    "rebound",
]
ExercisePerformanceMilestoneCode = Literal["personal_best"]


@dataclass(frozen=True)
class ExerciseHistoryAnalyticsOverview:
    has_history: bool
    completed_workout_count: int
    completed_set_count: int
    distinct_effective_exercise_count: int
    most_recent_completed_workout_date: str | None


@dataclass(frozen=True)
class ExerciseHistoryRecentSession:
    session_key: str
    performed_at: str | None
    completed_set_count: int
    planned_set_count: int
    summary: str
    measurement_type: ExerciseMeasurementType
    modality: ExercisePerformanceModality
    comparable_working_weight: float | None
    average_actual_rir: float | None
    performance_metric: ExercisePerformanceMetric | None
    relative_position: float | None
    previous_comparison: ExercisePerformanceComparison | None
    phase: ExercisePerformancePhase | None
    milestones: list[ExercisePerformanceMilestone]
    has_set_details: bool
    recorded_sets: list[ExerciseHistoryRecordedSet]
    completed_sets: list[ExerciseHistoryCompletedSet]


@dataclass(frozen=True)
class ExerciseHistoryCompletedSet:
    set_number: int
    measurement_type: ExerciseMeasurementType
    actual_reps: int | None
    actual_duration_seconds: int | None
    actual_distance_meters: float | None
    actual_weight: float | None
    actual_rir: int | None


@dataclass(frozen=True)
class ExerciseHistoryRecordedSet:
    set_number: int
    measurement_type: ExerciseMeasurementType
    actual_reps: int | None
    actual_duration_seconds: int | None
    actual_distance_meters: float | None
    actual_weight: float | None
    actual_rir: int | None
    completed: bool
    skipped: bool


@dataclass(frozen=True)
class ExercisePerformanceMetric:
    metric_type: ExercisePerformanceMetricType
    label: str
    value: float
    unit: ExercisePerformanceMetricUnit


@dataclass(frozen=True)
class ExercisePerformanceComparison:
    metric_type: ExercisePerformanceMetricType
    unit: ExercisePerformanceMetricUnit
    then_performed_at: str | None
    then_value: float
    now_performed_at: str | None
    now_value: float
    absolute_change: float
    percent_change: float | None
    direction: Literal["higher", "lower", "steady"]
    comparable_session_count: int


@dataclass(frozen=True)
class ExercisePerformancePhase:
    code: ExercisePerformancePhaseCode
    label: str
    evidence: str
    evidence_session_count: int


@dataclass(frozen=True)
class ExercisePerformancePhaseSegment:
    code: ExercisePerformancePhaseCode
    label: str
    evidence: str
    start_date: str
    end_date: str
    start_session_key: str
    end_session_key: str
    evidence_session_count: int


@dataclass(frozen=True)
class ExercisePerformanceMilestone:
    code: ExercisePerformanceMilestoneCode
    label: str
    evidence: str
    performed_at: str
    session_key: str


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
    measurement_type: ExerciseMeasurementType
    modality: ExercisePerformanceModality
    completed_session_count: int
    last_performed_at: str | None
    latest_completed_session_summary: str
    recent_best_set: WorkoutExerciseBestSet | None
    progression_recommendation: ExerciseHistoryProgressionRecommendation
    logging_quality: str
    limitation: str | None
    recent_working_load_trend: RecentWorkingLoadTrend
    then_vs_now: ExercisePerformanceComparison | None
    performance_phase: ExercisePerformancePhase | None
    current_trend: ExercisePerformancePhase | None
    historical_phase_segments: list[ExercisePerformancePhaseSegment]
    milestones: list[ExercisePerformanceMilestone]
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
    include_set_details: bool = False,
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
        include_all_measurement_types=True,
    )
    return build_workout_exercise_history_analytics_from_sessions(
        user_id=user_id,
        sessions=sessions,
        exercise_limit=bounded_exercise_limit,
        session_limit=bounded_session_limit,
        include_set_details=include_set_details,
    )


def build_workout_exercise_history_analytics_from_sessions(
    *,
    user_id: int,
    sessions: list[ExerciseProgressionSession],
    exercise_limit: int = DEFAULT_ANALYTICS_EXERCISE_LIMIT,
    session_limit: int = DEFAULT_ANALYTICS_SESSION_LIMIT,
    include_set_details: bool = True,
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
        _build_exercise_summary(
            user_id,
            group,
            bounded_session_limit,
            include_set_details=include_set_details,
        )
        for group in ordered_groups[:bounded_exercise_limit]
    ]
    return WorkoutExerciseHistoryAnalytics(overview=overview, exercises=exercises)


def build_workout_exercise_history_session_detail(
    *,
    user_id: int,
    session_key: str,
    lookback_days: int = MAX_ANALYTICS_LOOKBACK_DAYS,
    end_date: str | None = None,
) -> ExerciseHistoryRecentSession | None:
    """Resolve one opaque, user-scoped completed-session key to exact sets."""

    bounded_lookback = min(
        MAX_ANALYTICS_LOOKBACK_DAYS,
        max(1, int(lookback_days)),
    )
    sessions = load_completed_user_progression_sessions(
        user_id=user_id,
        lookback_days=bounded_lookback,
        end_date=end_date,
        include_all_measurement_types=True,
    )
    for group in _group_sessions_by_effective_identity(sessions).values():
        ordered = sorted(
            _unique_execution_sessions(group),
            key=lambda session: (
                session.performed_at or "",
                session.workout_plan_instance_id,
            ),
            reverse=True,
        )
        if not ordered:
            continue
        measurement_type = _measurement_type(ordered[0])
        modality = _performance_modality(ordered, measurement_type)
        metrics = [
            _session_performance_metric(session, modality) for session in ordered
        ]
        comparison_metrics = [
            _session_comparison_metric(session, metric, modality)
            for session, metric in zip(ordered, metrics, strict=True)
        ]
        positions = _relative_metric_positions(metrics)
        previous_comparisons = _previous_session_comparisons(
            ordered,
            comparison_metrics,
        )
        historical_phase_segments = _historical_phase_segments(
            user_id,
            ordered,
            comparison_metrics,
        )
        phase_by_session_key = _phase_by_session_key(
            user_id,
            ordered,
            historical_phase_segments,
        )
        milestones_by_session_key = _milestones_by_session_key(
            _performance_milestones(user_id, ordered, comparison_metrics)
        )
        for session, metric, position, previous_comparison in zip(
            ordered,
            metrics,
            positions,
            previous_comparisons,
            strict=True,
        ):
            current_session_key = _session_key(user_id, session)
            if current_session_key != session_key:
                continue
            return _build_recent_session(
                user_id,
                session,
                modality=modality,
                metric=metric,
                relative_position=position,
                previous_comparison=previous_comparison,
                phase=phase_by_session_key.get(current_session_key),
                milestones=milestones_by_session_key.get(current_session_key, []),
                include_set_details=True,
            )
    return None


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
    *,
    include_set_details: bool,
) -> ExerciseHistoryAnalyticsSummary:
    ordered = sorted(
        sessions,
        key=lambda session: (
            session.performed_at or "",
            session.workout_plan_instance_id,
        ),
        reverse=True,
    )
    bounded_sessions = _unique_execution_sessions(ordered)[:session_limit]
    measurement_type = _measurement_type(bounded_sessions[0])
    modality = _performance_modality(ordered, measurement_type)
    metrics = [
        _session_performance_metric(session, modality) for session in bounded_sessions
    ]
    comparison_metrics = [
        _session_comparison_metric(session, metric, modality)
        for session, metric in zip(bounded_sessions, metrics, strict=True)
    ]
    relative_positions = _relative_metric_positions(metrics)
    previous_comparisons = _previous_session_comparisons(
        bounded_sessions,
        comparison_metrics,
    )
    historical_phase_segments = _historical_phase_segments(
        user_id,
        bounded_sessions,
        comparison_metrics,
    )
    phase_by_session_key = _phase_by_session_key(
        user_id,
        bounded_sessions,
        historical_phase_segments,
    )
    milestones = _performance_milestones(
        user_id,
        bounded_sessions,
        comparison_metrics,
    )
    milestones_by_session_key = _milestones_by_session_key(milestones)
    recent_sessions = [
        _build_recent_session(
            user_id,
            session,
            modality=modality,
            metric=metric,
            relative_position=relative_position,
            previous_comparison=previous_comparison,
            phase=phase_by_session_key.get(_session_key(user_id, session)),
            milestones=milestones_by_session_key.get(
                _session_key(user_id, session),
                [],
            ),
            include_set_details=include_set_details,
        )
        for session, metric, relative_position, previous_comparison in zip(
            bounded_sessions,
            metrics,
            relative_positions,
            previous_comparisons,
            strict=True,
        )
    ]
    latest_session = recent_sessions[0]
    logging_quality = _analytics_logging_quality(ordered)
    current_trend = _performance_phase(bounded_sessions, comparison_metrics)
    return ExerciseHistoryAnalyticsSummary(
        catalog_exercise_id=_group_catalog_exercise_id(ordered),
        exercise_name=ordered[0].effective_exercise_name,
        measurement_type=measurement_type,
        modality=modality,
        completed_session_count=len(
            {session.workout_execution_session_id for session in ordered}
        ),
        last_performed_at=bounded_sessions[0].performed_at,
        latest_completed_session_summary=latest_session.summary,
        recent_best_set=(
            select_recent_best_set(ordered) if measurement_type == "reps" else None
        ),
        progression_recommendation=_progression_recommendation(
            user_id,
            ordered[0],
        ),
        logging_quality=logging_quality,
        limitation=_logging_limitation(logging_quality, measurement_type),
        recent_working_load_trend=_working_load_trend(bounded_sessions),
        then_vs_now=_then_vs_now(bounded_sessions, comparison_metrics),
        performance_phase=current_trend,
        current_trend=current_trend,
        historical_phase_segments=historical_phase_segments,
        milestones=milestones,
        recent_sessions=recent_sessions,
    )


def _build_recent_session(
    user_id: int,
    session: ExerciseProgressionSession,
    *,
    modality: ExercisePerformanceModality,
    metric: ExercisePerformanceMetric | None,
    relative_position: float | None,
    previous_comparison: ExercisePerformanceComparison | None,
    phase: ExercisePerformancePhase | None,
    milestones: list[ExercisePerformanceMilestone],
    include_set_details: bool,
) -> ExerciseHistoryRecentSession:
    completed_rows = completed_exercise_actual_rows(session)
    recorded_rows = sorted(
        session.actual_rows,
        key=lambda row: int(row.get("set_number") or 0),
    )
    return ExerciseHistoryRecentSession(
        session_key=_session_key(user_id, session),
        performed_at=session.performed_at,
        completed_set_count=len(completed_rows),
        planned_set_count=session.planned_set_count,
        summary=_performance_session_summary(session, completed_rows),
        measurement_type=_measurement_type(session),
        modality=modality,
        comparable_working_weight=comparable_working_weight(session),
        average_actual_rir=_session_average_rir(session),
        performance_metric=metric,
        relative_position=relative_position,
        previous_comparison=previous_comparison,
        phase=phase,
        milestones=milestones,
        has_set_details=include_set_details,
        recorded_sets=(
            [_build_recorded_set(row) for row in recorded_rows]
            if include_set_details
            else []
        ),
        completed_sets=(
            [_build_completed_set(row) for row in completed_rows]
            if include_set_details
            else []
        ),
    )


def _build_recorded_set(row: dict[str, object]) -> ExerciseHistoryRecordedSet:
    return ExerciseHistoryRecordedSet(
        set_number=int(row["set_number"]),
        measurement_type=_actual_measurement_type(row),
        actual_reps=(
            None if row.get("actual_reps") is None else int(row["actual_reps"])
        ),
        actual_duration_seconds=(
            None
            if row.get("actual_duration_seconds") is None
            else int(row["actual_duration_seconds"])
        ),
        actual_distance_meters=(
            None
            if row.get("actual_distance_meters") is None
            else float(row["actual_distance_meters"])
        ),
        actual_weight=(
            None if row.get("actual_weight") is None else float(row["actual_weight"])
        ),
        actual_rir=(None if row.get("actual_rir") is None else int(row["actual_rir"])),
        completed=_is_truthy(row.get("completed")),
        skipped=_is_truthy(row.get("skipped")),
    )


def _build_completed_set(row: dict[str, object]) -> ExerciseHistoryCompletedSet:
    return ExerciseHistoryCompletedSet(
        set_number=int(row["set_number"]),
        measurement_type=_actual_measurement_type(row),
        actual_reps=(
            None if row.get("actual_reps") is None else int(row["actual_reps"])
        ),
        actual_duration_seconds=(
            None
            if row.get("actual_duration_seconds") is None
            else int(row["actual_duration_seconds"])
        ),
        actual_distance_meters=(
            None
            if row.get("actual_distance_meters") is None
            else float(row["actual_distance_meters"])
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
            measurement_type=latest_session.measurement_type,
            reps_min=latest_session.planned_reps_min,
            reps_max=latest_session.planned_reps_max,
            target_duration_seconds=latest_session.planned_duration_seconds,
            target_distance_meters=latest_session.planned_distance_meters,
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


def _measurement_type(
    session: ExerciseProgressionSession,
) -> ExerciseMeasurementType:
    if session.measurement_type == "duration":
        return "duration"
    if session.measurement_type == "distance":
        return "distance"
    return "reps"


def _actual_measurement_type(
    row: dict[str, object],
) -> ExerciseMeasurementType:
    if row.get("measurement_type") == "duration":
        return "duration"
    if row.get("measurement_type") == "distance":
        return "distance"
    return "reps"


def _performance_modality(
    sessions: list[ExerciseProgressionSession],
    measurement_type: ExerciseMeasurementType,
) -> ExercisePerformanceModality:
    exercise_type = next(
        (
            session.exercise_type.strip().lower()
            for session in sessions
            if session.exercise_type
        ),
        "",
    )
    movement_pattern = next(
        (
            session.movement_pattern.strip().lower()
            for session in sessions
            if session.movement_pattern
        ),
        "",
    )
    exercise_name = sessions[0].effective_exercise_name.strip().lower()
    is_cardio = exercise_type in {"cardio", "conditioning"}
    if measurement_type == "duration":
        return "cardio" if is_cardio else "timed"
    if measurement_type == "distance":
        if "carry" in movement_pattern or "carry" in exercise_name:
            return "carry"
        return "cardio" if is_cardio else "distance"
    has_external_load = any(
        row.get("actual_weight") is not None and float(row["actual_weight"]) > 0
        for session in sessions
        for row in completed_exercise_actual_rows(session)
    )
    return "externally_weighted" if has_external_load else "bodyweight"


def _session_performance_metric(
    session: ExerciseProgressionSession,
    modality: ExercisePerformanceModality,
) -> ExercisePerformanceMetric | None:
    completed_rows = completed_exercise_actual_rows(session)
    measurement_type = _measurement_type(session)
    if measurement_type == "duration":
        values = [
            int(row["actual_duration_seconds"])
            for row in completed_rows
            if row.get("actual_duration_seconds") is not None
        ]
        return (
            ExercisePerformanceMetric(
                metric_type="duration",
                label="Longest set",
                value=float(max(values)),
                unit="seconds",
            )
            if values
            else None
        )
    if measurement_type == "distance":
        values = [
            float(row["actual_distance_meters"])
            for row in completed_rows
            if row.get("actual_distance_meters") is not None
        ]
        return (
            ExercisePerformanceMetric(
                metric_type="distance",
                label="Longest set",
                value=max(values),
                unit="meters",
            )
            if values
            else None
        )
    if modality == "externally_weighted":
        loads = [
            float(row["actual_weight"])
            for row in completed_rows
            if row.get("actual_weight") is not None and float(row["actual_weight"]) > 0
        ]
        return (
            ExercisePerformanceMetric(
                metric_type="load",
                label="Load",
                value=max(loads),
                unit="lb",
            )
            if loads
            else None
        )
    reps = [
        int(row["actual_reps"])
        for row in completed_rows
        if row.get("actual_reps") is not None
    ]
    return (
        ExercisePerformanceMetric(
            metric_type="reps",
            label="Best set",
            value=float(max(reps)),
            unit="reps",
        )
        if reps
        else None
    )


def _session_comparison_metric(
    session: ExerciseProgressionSession,
    display_metric: ExercisePerformanceMetric | None,
    modality: ExercisePerformanceModality,
) -> ExercisePerformanceMetric | None:
    if display_metric is None:
        return None
    if modality != "externally_weighted":
        return display_metric
    comparable_load = comparable_working_weight(session)
    if comparable_load is None:
        return None
    return ExercisePerformanceMetric(
        metric_type="load",
        label="Load",
        value=float(comparable_load),
        unit="lb",
    )


def _relative_metric_positions(
    metrics: list[ExercisePerformanceMetric | None],
) -> list[float | None]:
    values_by_type: dict[ExercisePerformanceMetricType, list[float]] = defaultdict(list)
    for metric in metrics:
        if metric is not None:
            values_by_type[metric.metric_type].append(metric.value)

    positions: list[float | None] = []
    for metric in metrics:
        if metric is None:
            positions.append(None)
            continue
        values = values_by_type[metric.metric_type]
        lowest = min(values)
        highest = max(values)
        if highest == lowest:
            positions.append(0.55)
        else:
            positions.append(round((metric.value - lowest) / (highest - lowest), 3))
    return positions


def _then_vs_now(
    sessions: list[ExerciseProgressionSession],
    metrics: list[ExercisePerformanceMetric | None],
) -> ExercisePerformanceComparison | None:
    now_pair = next(
        (
            (session, metric)
            for session, metric in zip(sessions, metrics, strict=True)
            if metric is not None
        ),
        None,
    )
    if now_pair is None:
        return None
    now_session, now_metric = now_pair
    comparable = [
        (session, metric)
        for session, metric in zip(sessions, metrics, strict=True)
        if metric is not None and metric.metric_type == now_metric.metric_type
    ]
    if len(comparable) < 2:
        return None
    then_session, then_metric = comparable[-1]
    return _build_comparison(
        then_session,
        then_metric,
        now_session,
        now_metric,
        comparable_session_count=len(comparable),
    )


def _previous_session_comparisons(
    sessions: list[ExerciseProgressionSession],
    metrics: list[ExercisePerformanceMetric | None],
) -> list[ExercisePerformanceComparison | None]:
    comparisons: list[ExercisePerformanceComparison | None] = []
    for index, (session, metric) in enumerate(zip(sessions, metrics, strict=True)):
        if metric is None:
            comparisons.append(None)
            continue
        previous = next(
            (
                (older_session, older_metric)
                for older_session, older_metric in zip(
                    sessions[index + 1 :],
                    metrics[index + 1 :],
                    strict=True,
                )
                if older_metric is not None
                and older_metric.metric_type == metric.metric_type
            ),
            None,
        )
        if previous is None:
            comparisons.append(None)
            continue
        previous_session, previous_metric = previous
        comparisons.append(
            _build_comparison(
                previous_session,
                previous_metric,
                session,
                metric,
                comparable_session_count=2,
            )
        )
    return comparisons


def _build_comparison(
    then_session: ExerciseProgressionSession,
    then_metric: ExercisePerformanceMetric,
    now_session: ExerciseProgressionSession,
    now_metric: ExercisePerformanceMetric,
    *,
    comparable_session_count: int,
) -> ExercisePerformanceComparison:
    change = round(now_metric.value - then_metric.value, 2)
    if change > 0:
        direction: Literal["higher", "lower", "steady"] = "higher"
    elif change < 0:
        direction = "lower"
    else:
        direction = "steady"
    return ExercisePerformanceComparison(
        metric_type=now_metric.metric_type,
        unit=now_metric.unit,
        then_performed_at=then_session.performed_at,
        then_value=then_metric.value,
        now_performed_at=now_session.performed_at,
        now_value=now_metric.value,
        absolute_change=change,
        percent_change=(
            None
            if then_metric.value == 0
            else round((change / then_metric.value) * 100, 1)
        ),
        direction=direction,
        comparable_session_count=comparable_session_count,
    )


def _performance_phase(
    sessions: list[ExerciseProgressionSession],
    metrics: list[ExercisePerformanceMetric | None],
) -> ExercisePerformancePhase | None:
    latest_metric = metrics[0] if metrics else None
    if latest_metric is None:
        return None
    if latest_metric.metric_type in {"duration", "distance"}:
        return None
    comparable = [
        (session, metric)
        for session, metric in reversed(list(zip(sessions, metrics, strict=True)))
        if metric is not None and metric.metric_type == latest_metric.metric_type
    ]
    if len(comparable) < 3:
        return None

    values = [metric.value for _, metric in comparable]
    latest_value = values[-1]
    metric_label = _metric_evidence_label(latest_metric.metric_type)
    if len(values) >= 4:
        prior_peak = max(values[:-2])
        if values[-2] <= prior_peak * 0.9 and latest_value >= prior_peak * 0.95:
            return ExercisePerformancePhase(
                code="rebound",
                label="Rebound",
                evidence=(
                    f"{metric_label} returned to within 5% of the earlier "
                    "selected-range high after a lower session."
                ),
                evidence_session_count=3,
            )
        if max(values[-2:]) <= prior_peak * 0.9:
            return ExercisePerformancePhase(
                code="deload",
                label="Deload pattern",
                evidence=(
                    f"The last two comparable sessions remained at least 10% "
                    f"below the earlier selected-range {metric_label.lower()} high."
                ),
                evidence_session_count=3,
            )

    last_three = values[-3:]
    stable_last_three = (
        max(last_three) - min(last_three) <= max(abs(max(last_three)), 1.0) * 0.02
    )
    if stable_last_three and latest_metric.metric_type == "load":
        rirs = [_session_average_rir(session) for session, _ in comparable[-3:]]
        if (
            all(rir is not None for rir in rirs)
            and float(rirs[0]) - float(rirs[-1]) >= 1
        ):
            return ExercisePerformancePhase(
                code="stable_effort_rise",
                label="Stable load, rising effort",
                evidence=(
                    "Comparable load stayed within 2% across three sessions "
                    "while average logged RIR fell by at least 1."
                ),
                evidence_session_count=3,
            )
    if all(newer > older * 1.01 for older, newer in pairwise(last_three)):
        return ExercisePerformancePhase(
            code="progression",
            label="Progression",
            evidence=(
                f"{metric_label} rose in each of the last three comparable sessions."
            ),
            evidence_session_count=3,
        )
    if len(values) >= 4 and (
        max(values[-4:]) - min(values[-4:]) <= max(abs(max(values[-4:])), 1.0) * 0.02
    ):
        return ExercisePerformancePhase(
            code="plateau",
            label="Stable phase",
            evidence=(
                f"{metric_label} stayed within 2% across four comparable sessions."
            ),
            evidence_session_count=4,
        )
    return None


def _historical_phase_segments(
    user_id: int,
    sessions: list[ExerciseProgressionSession],
    metrics: list[ExercisePerformanceMetric | None],
) -> list[ExercisePerformancePhaseSegment]:
    chronological = list(reversed(list(zip(sessions, metrics, strict=True))))
    segments: list[ExercisePerformancePhaseSegment] = []
    previous_classified_index: int | None = None
    last_segment_end_index = -1
    for end_index in range(len(chronological)):
        if chronological[end_index][1] is None:
            previous_classified_index = None
            continue
        prefix = chronological[: end_index + 1]
        phase = _performance_phase(
            [session for session, _ in reversed(prefix)],
            [metric for _, metric in reversed(prefix)],
        )
        if phase is None:
            previous_classified_index = None
            continue
        end_session = chronological[end_index][0]
        if end_session.performed_at is None:
            previous_classified_index = None
            continue
        if (
            segments
            and previous_classified_index == end_index - 1
            and segments[-1].code == phase.code
        ):
            previous = segments[-1]
            segments[-1] = ExercisePerformancePhaseSegment(
                code=previous.code,
                label=phase.label,
                evidence=phase.evidence,
                start_date=previous.start_date,
                end_date=end_session.performed_at,
                start_session_key=previous.start_session_key,
                end_session_key=_session_key(user_id, end_session),
                evidence_session_count=max(
                    previous.evidence_session_count,
                    phase.evidence_session_count,
                ),
            )
        else:
            evidence_window = {
                "progression": 3,
                "stable_effort_rise": 3,
                "plateau": 4,
                "deload": 2,
                "rebound": 2,
            }[phase.code]
            start_index = max(
                0,
                end_index - evidence_window + 1,
                last_segment_end_index,
            )
            start_session = chronological[start_index][0]
            if (
                start_session.performed_at is None
                or start_session.performed_at >= end_session.performed_at
            ):
                previous_classified_index = None
                continue
            segments.append(
                ExercisePerformancePhaseSegment(
                    code=phase.code,
                    label=phase.label,
                    evidence=phase.evidence,
                    start_date=start_session.performed_at,
                    end_date=end_session.performed_at,
                    start_session_key=_session_key(user_id, start_session),
                    end_session_key=_session_key(user_id, end_session),
                    evidence_session_count=phase.evidence_session_count,
                )
            )
        previous_classified_index = end_index
        last_segment_end_index = end_index
    return segments


def _performance_milestones(
    user_id: int,
    sessions: list[ExerciseProgressionSession],
    metrics: list[ExercisePerformanceMetric | None],
) -> list[ExercisePerformanceMilestone]:
    chronological = list(reversed(list(zip(sessions, metrics, strict=True))))
    prior_values: dict[ExercisePerformanceMetricType, list[float]] = defaultdict(list)
    milestones: list[ExercisePerformanceMilestone] = []
    for session, metric in chronological:
        if metric is None or session.performed_at is None:
            continue
        if metric.metric_type not in {"load", "reps"}:
            continue
        earlier = prior_values[metric.metric_type]
        if earlier and metric.value > max(earlier) * 1.01:
            label = (
                "Personal best"
                if metric.metric_type != "load"
                else "Comparable load best"
            )
            milestones.append(
                ExercisePerformanceMilestone(
                    code="personal_best",
                    label=label,
                    evidence=(
                        f"{metric.label} exceeded every earlier comparable "
                        "session in the selected range."
                    ),
                    performed_at=session.performed_at,
                    session_key=_session_key(user_id, session),
                )
            )
        earlier.append(metric.value)
    return milestones


def _milestones_by_session_key(
    milestones: list[ExercisePerformanceMilestone],
) -> dict[str, list[ExercisePerformanceMilestone]]:
    grouped: dict[str, list[ExercisePerformanceMilestone]] = defaultdict(list)
    for milestone in milestones:
        grouped[milestone.session_key].append(milestone)
    return grouped


def _phase_by_session_key(
    user_id: int,
    sessions: list[ExerciseProgressionSession],
    segments: list[ExercisePerformancePhaseSegment],
) -> dict[str, ExercisePerformancePhase]:
    phases: dict[str, ExercisePerformancePhase] = {}
    for session in sessions:
        if session.performed_at is None:
            continue
        segment = next(
            (
                item
                for item in segments
                if item.start_date <= session.performed_at <= item.end_date
            ),
            None,
        )
        if segment is None:
            continue
        phases[_session_key(user_id, session)] = ExercisePerformancePhase(
            code=segment.code,
            label=segment.label,
            evidence=segment.evidence,
            evidence_session_count=segment.evidence_session_count,
        )
    return phases


def _session_average_rir(session: ExerciseProgressionSession) -> float | None:
    completed_rows = completed_exercise_actual_rows(session)
    if not completed_rows or any(
        row.get("actual_rir") is None for row in completed_rows
    ):
        return None
    return round(mean(int(row["actual_rir"]) for row in completed_rows), 1)


def _metric_evidence_label(
    metric_type: ExercisePerformanceMetricType,
) -> str:
    return {
        "load": "Comparable load",
        "reps": "Best set reps",
        "duration": "Longest set duration",
        "distance": "Longest set distance",
    }[metric_type]


def _performance_session_summary(
    session: ExerciseProgressionSession,
    completed_rows: list[dict[str, object]],
) -> str:
    measurement_type = _measurement_type(session)
    if measurement_type == "reps":
        return summarize_exercise_progression_session(session).summary
    if not completed_rows:
        return "No completed sets logged."
    if measurement_type == "duration":
        values = [
            int(row["actual_duration_seconds"])
            for row in completed_rows
            if row.get("actual_duration_seconds") is not None
        ]
        unit = "sec"
    else:
        values = [
            float(row["actual_distance_meters"])
            for row in completed_rows
            if row.get("actual_distance_meters") is not None
        ]
        unit = "m"
    if not values:
        return f"{len(completed_rows)} completed sets; values not fully logged."
    value_summary = (
        _format_history_number(values[0])
        if min(values) == max(values)
        else (
            f"{_format_history_number(min(values))}–"
            f"{_format_history_number(max(values))}"
        )
    )
    return f"{len(completed_rows)} completed sets, {value_summary} {unit}"


def _analytics_logging_quality(
    sessions: list[ExerciseProgressionSession],
) -> str:
    planned = sum(session.planned_set_count for session in sessions)
    completed_by_session = [
        (session, completed_exercise_actual_rows(session)) for session in sessions
    ]
    completed_count = sum(len(rows) for _, rows in completed_by_session)
    if planned <= 0 or completed_count == 0:
        return "limited"
    missing_measurements = 0
    missing_effort = 0
    for session, rows in completed_by_session:
        measurement_type = _measurement_type(session)
        for row in rows:
            if measurement_type == "duration":
                missing_measurements += row.get("actual_duration_seconds") is None
            elif measurement_type == "distance":
                missing_measurements += row.get("actual_distance_meters") is None
            else:
                missing_measurements += row.get("actual_reps") is None
                missing_effort += row.get("actual_rir") is None
    if planned > completed_count or missing_measurements or missing_effort:
        return "incomplete"
    return "complete"


def _logging_limitation(
    logging_quality: str,
    measurement_type: ExerciseMeasurementType,
) -> str | None:
    if logging_quality == "complete":
        return None
    if measurement_type == "duration":
        return "Some sessions have incomplete set or duration logging."
    if measurement_type == "distance":
        return "Some sessions have incomplete set or distance logging."
    return "Some sessions have incomplete set, rep, or effort logging."


def _format_history_number(value: float | int) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def _is_truthy(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _session_key(user_id: int, session: ExerciseProgressionSession) -> str:
    identity = (
        f"{user_id}:{session.workout_execution_session_id}:"
        f"{session.planned_exercise_id}"
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


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
