from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean

from models.longitudinal_insight_models import (
    InsightDataCoverage,
    InsightEvidence,
    InsightWindow,
    LongitudinalInsight,
    LongitudinalInsightFeed,
)
from models.nutrition_trend_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    LOGGING_CONSISTENCY_STRONG,
    LOGGING_CONSISTENCY_USABLE,
    NutritionTrendDay,
    NutritionTrendWindow,
)
from models.recovery_intelligence_v2_models import RecoveryIntelligenceV2Summary
from services.nutrition_target_vs_actual_service import (
    build_target_vs_actual_nutrition_summary,
)
from services.nutrition_trend_service import build_nutrition_trend_window
from services.recovery_intelligence_v2_service import build_recovery_intelligence_v2
from services.workout_exercise_history_analytics_service import (
    ExerciseHistoryAnalyticsSummary,
    build_workout_exercise_history_analytics_from_sessions,
)
from services.workout_progression_history_service import (
    ExerciseProgressionSession,
    load_completed_user_progression_sessions,
)

LONGITUDINAL_INSIGHT_ENGINE_VERSION = "longitudinal_insight_engine_v1"
DEFAULT_MAX_INSIGHTS = 5
MAX_INSIGHTS = 10
RECOVERY_WINDOW_DAYS = 7
NUTRITION_WINDOW_DAYS = 28
TRAINING_LOOKBACK_DAYS = 180
TRAINING_EXPOSURE_FRESHNESS_DAYS = 28

_COMPLETE_NUTRITION_DAYS = {
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
}


@dataclass(frozen=True)
class _Candidate:
    insight: LongitudinalInsight
    score: int
    dedupe_key: str


@dataclass(frozen=True)
class _TrainingExposure:
    performed_at: date
    weight_lb: float
    average_rir: float
    average_reps: float


@dataclass(frozen=True)
class _RecoveryChangeProfile:
    worsening_evidence: list[InsightEvidence]
    improving_evidence: list[InsightEvidence]
    recent_count: int
    prior_count: int


def build_longitudinal_insight_feed(
    *,
    user_id: int,
    as_of_date: str | date | None = None,
    target_date: str | date | None = None,
    max_insights: int = DEFAULT_MAX_INSIGHTS,
) -> LongitudinalInsightFeed:
    """Build deterministic, evidence-backed observations from existing history.

    The engine composes existing intelligence and history services. It does not
    persist insights, change targets, make progression decisions, or use AI.
    """

    target = _resolve_as_of_date(as_of_date=as_of_date, target_date=target_date)
    resolved_limit = max(1, min(int(max_insights), MAX_INSIGHTS))

    recovery = build_recovery_intelligence_v2(
        user_id=user_id,
        target_date=target,
    )
    nutrition = build_nutrition_trend_window(
        user_id=user_id,
        end_date=target.isoformat(),
        window_days=NUTRITION_WINDOW_DAYS,
    )
    training_sessions = load_completed_user_progression_sessions(
        user_id=user_id,
        lookback_days=TRAINING_LOOKBACK_DAYS,
        end_date=target,
    )
    training_analytics = build_workout_exercise_history_analytics_from_sessions(
        user_id=user_id,
        sessions=training_sessions,
        exercise_limit=48,
        session_limit=12,
    )

    recovery_candidates = _recovery_candidates(recovery, target)
    training_candidates = _training_candidates(
        training_analytics.exercises,
        training_sessions,
        target,
    )
    nutrition_candidates = _nutrition_candidates(
        user_id=user_id,
        trend=nutrition,
        target=target,
    )
    body_weight_candidates = _body_weight_candidates(nutrition, target)
    cross_domain_candidates = _cross_domain_candidates(
        recovery=recovery,
        training_candidates=training_candidates,
    )

    ranked = _rank_and_dedupe(
        [
            *recovery_candidates,
            *training_candidates,
            *nutrition_candidates,
            *body_weight_candidates,
            *cross_domain_candidates,
        ],
        limit=resolved_limit,
    )
    return LongitudinalInsightFeed(
        user_id=user_id,
        as_of_date=target.isoformat(),
        engine_version=LONGITUDINAL_INSIGHT_ENGINE_VERSION,
        insights=[candidate.insight for candidate in ranked],
    )


def _recovery_candidates(
    recovery: RecoveryIntelligenceV2Summary,
    target: date,
) -> list[_Candidate]:
    recent = recovery.windows["recent_7_days"]
    prior = recovery.windows["prior_7_days"]
    recent_count = int(recent["checkin_days"])
    prior_count = int(prior["checkin_days"])
    candidates: list[_Candidate] = []

    if recent_count >= 4 and prior_count >= 4:
        recent_sleep = _optional_number(recent.get("average_sleep_hours"))
        prior_sleep = _optional_number(prior.get("average_sleep_hours"))
        recent_quality = _optional_number(recent.get("average_sleep_quality"))
        prior_quality = _optional_number(prior.get("average_sleep_quality"))
        quality_recent_count = int(recent.get("sleep_quality_value_days") or 0)
        quality_prior_count = int(prior.get("sleep_quality_value_days") or 0)
        sleep_delta = _delta(recent_sleep, prior_sleep)
        quality_delta = _delta(recent_quality, prior_quality)
        sleep_declined = sleep_delta is not None and sleep_delta <= -0.5
        quality_declined = (
            quality_delta is not None
            and quality_delta <= -0.75
            and quality_recent_count >= 4
            and quality_prior_count >= 4
        )
        if sleep_declined or quality_declined:
            evidence = []
            if recent_sleep is not None and prior_sleep is not None:
                evidence.append(
                    _comparison_evidence(
                        metric="sleep_hours",
                        label="Average sleep",
                        recent_value=recent_sleep,
                        prior_value=prior_sleep,
                        unit="h",
                        source="daily_checkins",
                        source_fields=["sleep_hours", "checkin_date"],
                    )
                )
            if (
                quality_declined
                and recent_quality is not None
                and prior_quality is not None
            ):
                evidence.append(
                    _comparison_evidence(
                        metric="sleep_quality",
                        label="Average sleep quality",
                        recent_value=recent_quality,
                        prior_value=prior_quality,
                        unit="/5",
                        source="daily_checkins",
                        source_fields=["sleep_quality", "checkin_date"],
                    )
                )
            primary_change = (
                f"{abs(sleep_delta):.1f} hours"
                if sleep_declined and sleep_delta is not None
                else f"{abs(quality_delta):.1f} points"
            )
            candidates.append(
                _candidate(
                    stable_id="lie_v1:recovery:sleep_decline",
                    domain="recovery",
                    insight_type="sleep_decline",
                    title="Sleep has declined from your recent baseline",
                    explanation=(
                        f"The latest 7-day average is down {primary_change} "
                        "from the preceding 7 days."
                    ),
                    observation_window=_calendar_window(
                        target, 7, recent_count, "Latest 7 days"
                    ),
                    comparison_window=_calendar_window(
                        target - timedelta(days=7),
                        7,
                        prior_count,
                        "Preceding 7 days",
                    ),
                    evidence=evidence,
                    evidence_strength=(
                        "strong"
                        if recent_count >= 6
                        and prior_count >= 6
                        and sleep_delta is not None
                        and sleep_delta <= -0.8
                        else "moderate"
                    ),
                    coverage=_paired_coverage(recent_count, prior_count, expected=7),
                    direction="worsening",
                    status="attention",
                    score=88 if sleep_delta is not None and sleep_delta <= -0.8 else 82,
                    dedupe_key="recovery:trend",
                )
            )

        recent_soreness = _optional_number(recent.get("average_soreness_level"))
        prior_soreness = _optional_number(prior.get("average_soreness_level"))
        soreness_delta = _delta(recent_soreness, prior_soreness)
        if recent_soreness is not None and recent_soreness >= 6.0:
            evidence = [
                _comparison_evidence(
                    metric="soreness_level",
                    label="Average soreness",
                    recent_value=recent_soreness,
                    prior_value=prior_soreness,
                    unit="/10",
                    source="daily_checkins",
                    source_fields=["soreness_level", "checkin_date"],
                )
            ]
            candidates.append(
                _candidate(
                    stable_id="lie_v1:recovery:elevated_soreness",
                    domain="recovery",
                    insight_type="elevated_soreness",
                    title="Soreness has stayed elevated",
                    explanation=(
                        f"Average soreness was {_format_number(recent_soreness)}/10 "
                        f"across {recent_count} recent check-ins."
                    ),
                    observation_window=_calendar_window(
                        target, 7, recent_count, "Latest 7 days"
                    ),
                    comparison_window=_calendar_window(
                        target - timedelta(days=7),
                        7,
                        prior_count,
                        "Preceding 7 days",
                    ),
                    evidence=evidence,
                    evidence_strength=(
                        "strong"
                        if recent_count >= 6
                        and recent_soreness >= 7
                        and soreness_delta is not None
                        and soreness_delta >= 0.5
                        else "moderate"
                    ),
                    coverage=_paired_coverage(recent_count, prior_count, expected=7),
                    direction="worsening",
                    status="attention",
                    score=90 if recent_soreness >= 7 else 83,
                    dedupe_key="recovery:trend",
                )
            )

        profile = _recovery_change_profile(recovery)
        if len(profile.improving_evidence) >= 2 and not profile.worsening_evidence:
            candidates.append(
                _candidate(
                    stable_id="lie_v1:recovery:rebound",
                    domain="recovery",
                    insight_type="recovery_rebound",
                    title="Recovery signals are improving",
                    explanation=(
                        f"{len(profile.improving_evidence)} recovery measures improved "
                        "across the latest 7 days compared with the preceding 7 days."
                    ),
                    observation_window=_calendar_window(
                        target, 7, recent_count, "Latest 7 days"
                    ),
                    comparison_window=_calendar_window(
                        target - timedelta(days=7), 7, prior_count, "Preceding 7 days"
                    ),
                    evidence=profile.improving_evidence,
                    evidence_strength=(
                        "strong"
                        if len(profile.improving_evidence) >= 3
                        and recent_count >= 6
                        and prior_count >= 6
                        else "moderate"
                    ),
                    coverage=_paired_coverage(recent_count, prior_count, expected=7),
                    direction="improving",
                    status="supportive",
                    score=78 + len(profile.improving_evidence),
                    dedupe_key="recovery:trend",
                )
            )

    baseline = recovery.windows["baseline_28_days"]
    baseline_count = int(baseline["checkin_days"])
    pain_area_counts = dict(baseline.get("pain_area_counts") or {})
    pain_concern_counts = dict(baseline.get("pain_concern_counts") or {})
    non_none_pain_count = int(pain_concern_counts.get("mild") or 0) + int(
        pain_concern_counts.get("significant") or 0
    )
    if baseline_count >= 8 and non_none_pain_count >= 3 and pain_area_counts:
        area, area_count = max(
            pain_area_counts.items(), key=lambda item: (int(item[1]), str(item[0]))
        )
        area_count = int(area_count)
        if area_count >= 3 and area_count / baseline_count >= 0.15:
            candidates.append(
                _candidate(
                    stable_id=f"lie_v1:recovery:recurring_pain:{_stable_token(area)}",
                    domain="recovery",
                    insight_type="recurring_pain_concern",
                    title=f"{_label_token(area)} concern has recurred",
                    explanation=(
                        f"That area was logged with a pain or restriction concern on "
                        f"{area_count} of {baseline_count} check-in days in the latest 28 days."
                    ),
                    observation_window=_calendar_window(
                        target, 28, baseline_count, "Latest 28 days"
                    ),
                    comparison_window=None,
                    evidence=[
                        InsightEvidence(
                            metric="pain_area_occurrences",
                            label="Recurring area",
                            value=f"{_label_token(area)} · {area_count} check-ins",
                            source="daily_checkins",
                            source_fields=[
                                "pain_concern",
                                "pain_area",
                                "checkin_date",
                            ],
                        )
                    ],
                    evidence_strength=(
                        "strong"
                        if area_count >= 5 and baseline_count >= 14
                        else "moderate"
                    ),
                    coverage=_coverage(baseline_count, expected=28),
                    direction="recurring",
                    status="attention",
                    score=94
                    if int(pain_concern_counts.get("significant") or 0) >= 2
                    else 84,
                    dedupe_key="recovery:pain",
                )
            )

    return candidates


def _training_candidates(
    exercises: list[ExerciseHistoryAnalyticsSummary],
    sessions: list[ExerciseProgressionSession],
    target: date,
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for exercise in exercises:
        exposures = _training_exposures(exercise)
        if len(exposures) < 4:
            continue
        if (target - exposures[0].performed_at).days > TRAINING_EXPOSURE_FRESHNESS_DAYS:
            continue
        recent = exposures[:2]
        prior = exposures[2:4]
        recent_weight = mean(item.weight_lb for item in recent)
        prior_weight = mean(item.weight_lb for item in prior)
        recent_rir = mean(item.average_rir for item in recent)
        prior_rir = mean(item.average_rir for item in prior)
        weight_delta = recent_weight - prior_weight
        rir_delta = recent_rir - prior_rir
        stable_tolerance = max(1.0, prior_weight * 0.01)
        identity = _exercise_identity(exercise)
        evidence = [
            _comparison_evidence(
                metric="comparable_working_weight",
                label="Average comparable working load",
                recent_value=recent_weight,
                prior_value=prior_weight,
                unit="lb",
                source="workout_progression_history",
                source_fields=[
                    "actual_weight",
                    "completed",
                    "skipped",
                    "performed_at",
                ],
            ),
            _comparison_evidence(
                metric="average_actual_rir",
                label="Average effort",
                recent_value=recent_rir,
                prior_value=prior_rir,
                unit=" RIR",
                source="workout_progression_history",
                source_fields=["actual_rir", "completed", "skipped"],
            ),
        ]
        observation_window = _exposure_window(recent, "2 latest comparable exposures")
        comparison_window = _exposure_window(prior, "2 preceding comparable exposures")

        if weight_delta >= max(2.5, prior_weight * 0.02) and rir_delta >= -0.5:
            candidates.append(
                _candidate(
                    stable_id=f"lie_v1:training:clear_progression:{identity}",
                    domain="training",
                    insight_type="clear_progression",
                    title=f"{exercise.exercise_name} is progressing",
                    explanation=(
                        f"Comparable working load increased from "
                        f"{_format_number(prior_weight)} to {_format_number(recent_weight)} lb "
                        "without a meaningful rise in effort."
                    ),
                    observation_window=observation_window,
                    comparison_window=comparison_window,
                    evidence=evidence,
                    evidence_strength=(
                        "strong"
                        if len(exposures) >= 6 and weight_delta >= 5
                        else "moderate"
                    ),
                    coverage=_paired_exposure_coverage(len(recent), len(prior)),
                    direction="improving",
                    status="supportive",
                    score=86 if weight_delta >= 5 else 80,
                    dedupe_key=f"training:{identity}:performance",
                )
            )
            continue

        if abs(weight_delta) <= stable_tolerance and rir_delta <= -0.75:
            candidates.append(
                _candidate(
                    stable_id=f"lie_v1:training:rising_effort:{identity}",
                    domain="training",
                    insight_type="stable_load_rising_effort",
                    title=f"{exercise.exercise_name} is getting harder at the same load",
                    explanation=(
                        f"Comparable load stayed near {_format_number(recent_weight)} lb "
                        f"while average RIR fell from {_format_number(prior_rir)} to "
                        f"{_format_number(recent_rir)}."
                    ),
                    observation_window=observation_window,
                    comparison_window=comparison_window,
                    evidence=evidence,
                    evidence_strength=(
                        "strong"
                        if len(exposures) >= 6 and rir_delta <= -1.0
                        else "moderate"
                    ),
                    coverage=_paired_exposure_coverage(len(recent), len(prior)),
                    direction="worsening",
                    status="attention",
                    score=92 if rir_delta <= -1.0 else 87,
                    dedupe_key=f"training:{identity}:performance",
                )
            )
            continue

        if len(exposures) >= 6:
            latest_three = exposures[:3]
            prior_three = exposures[3:6]
            latest_weight = mean(item.weight_lb for item in latest_three)
            comparison_weight = mean(item.weight_lb for item in prior_three)
            latest_rir = mean(item.average_rir for item in latest_three)
            comparison_rir = mean(item.average_rir for item in prior_three)
            latest_reps = mean(item.average_reps for item in latest_three)
            comparison_reps = mean(item.average_reps for item in prior_three)
            date_span = (exposures[0].performed_at - exposures[5].performed_at).days
            if (
                date_span >= 21
                and abs(latest_weight - comparison_weight)
                <= max(1.0, comparison_weight * 0.01)
                and abs(latest_rir - comparison_rir) <= 0.35
                and abs(latest_reps - comparison_reps) <= 0.35
            ):
                candidates.append(
                    _candidate(
                        stable_id=f"lie_v1:training:plateau:{identity}",
                        domain="training",
                        insight_type="performance_plateau",
                        title=f"{exercise.exercise_name} performance has been stable",
                        explanation=(
                            "Load, reps, and RIR stayed within narrow bands across 6 "
                            f"comparable exposures spanning {date_span} days."
                        ),
                        observation_window=_exposure_window(
                            latest_three, "3 latest comparable exposures"
                        ),
                        comparison_window=_exposure_window(
                            prior_three, "3 preceding comparable exposures"
                        ),
                        evidence=[
                            *evidence,
                            _comparison_evidence(
                                metric="average_completed_reps",
                                label="Average completed reps",
                                recent_value=latest_reps,
                                prior_value=comparison_reps,
                                unit=" reps",
                                source="workout_progression_history",
                                source_fields=["actual_reps", "completed", "skipped"],
                            ),
                        ],
                        evidence_strength="moderate",
                        coverage=_paired_exposure_coverage(3, 3),
                        direction="stable",
                        status="plateau",
                        score=74,
                        dedupe_key=f"training:{identity}:performance",
                    )
                )

    candidates.extend(_training_consistency_candidates(sessions, target))
    return candidates


def _training_consistency_candidates(
    sessions: list[ExerciseProgressionSession], target: date
) -> list[_Candidate]:
    workout_dates: dict[int, date] = {}
    for session in sessions:
        performed_at = _optional_date(session.performed_at)
        if performed_at is not None:
            workout_dates.setdefault(session.workout_plan_instance_id, performed_at)

    recent_start = target - timedelta(days=27)
    prior_start = target - timedelta(days=55)
    prior_end = target - timedelta(days=28)
    recent_dates = [
        value for value in workout_dates.values() if recent_start <= value <= target
    ]
    prior_dates = [
        value for value in workout_dates.values() if prior_start <= value <= prior_end
    ]
    recent_count = len(recent_dates)
    prior_count = len(prior_dates)
    candidates: list[_Candidate] = []

    evidence = [
        _comparison_evidence(
            metric="completed_workouts",
            label="Completed workouts",
            recent_value=recent_count,
            prior_value=prior_count,
            unit="",
            source="workout_progression_history",
            source_fields=["workout_status", "execution_status", "performed_at"],
        )
    ]
    if (
        prior_count >= 6
        and recent_count <= prior_count - 3
        and recent_count / prior_count <= 0.6
    ):
        candidates.append(
            _candidate(
                stable_id="lie_v1:training:consistency_decline",
                domain="training",
                insight_type="training_consistency_decline",
                title="Training consistency has declined",
                explanation=(
                    f"Completed workouts fell from {prior_count} in the preceding 28 days "
                    f"to {recent_count} in the latest 28 days."
                ),
                observation_window=_calendar_window(
                    target, 28, recent_count, "Latest 28 days"
                ),
                comparison_window=_calendar_window(
                    prior_end, 28, prior_count, "Preceding 28 days"
                ),
                evidence=evidence,
                evidence_strength="strong"
                if prior_count - recent_count >= 5
                else "moderate",
                coverage=InsightDataCoverage(
                    status="strong" if prior_count >= 8 else "sufficient",
                    observation_count=recent_count,
                    comparison_observation_count=prior_count,
                ),
                direction="worsening",
                status="attention",
                score=79,
                dedupe_key="training:consistency",
            )
        )
    elif recent_count >= 8 and _active_week_count(recent_dates, target) >= 3:
        candidates.append(
            _candidate(
                stable_id="lie_v1:training:sustained_consistency",
                domain="training",
                insight_type="sustained_training_consistency",
                title="Training has been consistent",
                explanation=(
                    f"You completed {recent_count} workouts across "
                    f"{_active_week_count(recent_dates, target)} of the latest 4 weeks."
                ),
                observation_window=_calendar_window(
                    target, 28, recent_count, "Latest 28 days"
                ),
                comparison_window=None,
                evidence=[
                    InsightEvidence(
                        metric="completed_workouts",
                        label="Completed workout consistency",
                        value=(
                            f"{recent_count} workouts · "
                            f"{_active_week_count(recent_dates, target)}/4 active weeks"
                        ),
                        source="workout_progression_history",
                        source_fields=[
                            "workout_status",
                            "execution_status",
                            "performed_at",
                        ],
                    )
                ],
                evidence_strength="strong" if recent_count >= 12 else "moderate",
                coverage=InsightDataCoverage(
                    status="strong" if recent_count >= 12 else "sufficient",
                    observation_count=recent_count,
                ),
                direction="stable",
                status="consistent",
                score=64,
                dedupe_key="training:consistency",
            )
        )
    return candidates


def _nutrition_candidates(
    *,
    user_id: int,
    trend: NutritionTrendWindow,
    target: date,
) -> list[_Candidate]:
    recent_start = target - timedelta(days=13)
    prior_end = target - timedelta(days=14)
    recent_days = [
        day for day in trend.trend_days if _parse_date(day.date) >= recent_start
    ]
    prior_days = [day for day in trend.trend_days if _parse_date(day.date) <= prior_end]
    recent_complete = _complete_nutrition_days(recent_days)
    prior_complete = _complete_nutrition_days(prior_days)
    recent_logged = sum(
        1 for day in recent_days if day.logging_completeness != "no_logs"
    )
    prior_logged = sum(1 for day in prior_days if day.logging_completeness != "no_logs")
    recent_complete_rate = len(recent_complete) / 14
    prior_complete_rate = len(prior_complete) / 14
    recent_logged_rate = recent_logged / 14
    prior_logged_rate = prior_logged / 14
    candidates: list[_Candidate] = []

    if (
        prior_logged_rate >= 0.65
        and prior_complete_rate >= 0.5
        and prior_logged_rate - recent_logged_rate >= 0.25
        and recent_logged_rate <= 0.6
    ):
        candidates.append(
            _candidate(
                stable_id="lie_v1:nutrition:logging_decline",
                domain="nutrition",
                insight_type="nutrition_logging_decline",
                title="Nutrition logging has become less consistent",
                explanation=(
                    f"Logged days fell from {prior_logged} of 14 to {recent_logged} of 14. "
                    "Unlogged days remain unknown, not zero intake."
                ),
                observation_window=_calendar_window(
                    target, 14, recent_logged, "Latest 14 days"
                ),
                comparison_window=_calendar_window(
                    prior_end, 14, prior_logged, "Preceding 14 days"
                ),
                evidence=[
                    _comparison_evidence(
                        metric="nutrition_logged_days",
                        label="Days with nutrition logs",
                        recent_value=recent_logged,
                        prior_value=prior_logged,
                        unit="/14 days",
                        source="nutrition_trend_window",
                        source_fields=[
                            "logging_completeness",
                            "entry_count",
                            "entry_date",
                        ],
                    )
                ],
                evidence_strength=(
                    "strong" if prior_logged - recent_logged >= 6 else "moderate"
                ),
                coverage=InsightDataCoverage(
                    status="strong" if prior_logged >= 11 else "sufficient",
                    observation_count=recent_logged,
                    comparison_observation_count=prior_logged,
                    expected_observation_count=14,
                    observation_rate=round(recent_logged_rate, 2),
                    limitations=["Days without logs are treated as unknown intake."],
                ),
                direction="worsening",
                status="attention",
                score=81,
                dedupe_key="nutrition:logging",
            )
        )
    elif recent_complete_rate >= 0.75 and recent_logged_rate >= 0.85:
        candidates.append(
            _candidate(
                stable_id="lie_v1:nutrition:sustained_logging",
                domain="nutrition",
                insight_type="sustained_nutrition_logging",
                title="Nutrition logging has been consistent",
                explanation=(
                    f"{len(recent_complete)} of the latest 14 days were complete enough "
                    "for cautious trend use."
                ),
                observation_window=_calendar_window(
                    target, 14, len(recent_complete), "Latest 14 days"
                ),
                comparison_window=None,
                evidence=[
                    InsightEvidence(
                        metric="complete_nutrition_days",
                        label="Complete-enough logged days",
                        value=f"{len(recent_complete)}/14 days",
                        source="nutrition_trend_window",
                        source_fields=[
                            "logging_completeness",
                            "entry_count",
                            "entry_date",
                        ],
                    )
                ],
                evidence_strength="strong"
                if len(recent_complete) >= 13
                else "moderate",
                coverage=InsightDataCoverage(
                    status="strong" if len(recent_complete) >= 13 else "sufficient",
                    observation_count=len(recent_complete),
                    expected_observation_count=14,
                    observation_rate=round(recent_complete_rate, 2),
                ),
                direction="stable",
                status="consistent",
                score=63,
                dedupe_key="nutrition:logging",
            )
        )

    if trend.intake_trend_summary.logging_consistency_status in {
        LOGGING_CONSISTENCY_USABLE,
        LOGGING_CONSISTENCY_STRONG,
    }:
        recent_protein_days = [
            day for day in recent_complete if day.logged_protein is not None
        ]
        prior_protein_days = [
            day for day in prior_complete if day.logged_protein is not None
        ]
        if len(recent_protein_days) >= 5 and len(prior_protein_days) >= 5:
            recent_protein = mean(
                float(day.logged_protein) for day in recent_protein_days
            )
            prior_protein = mean(
                float(day.logged_protein) for day in prior_protein_days
            )
            protein_delta = recent_protein - prior_protein
            if (
                abs(protein_delta) >= 15
                and abs(protein_delta) / max(prior_protein, 1) >= 0.1
            ):
                latest_complete_day = max(recent_protein_days, key=lambda day: day.date)
                target_summary = build_target_vs_actual_nutrition_summary(
                    user_id=user_id,
                    target_date=latest_complete_day.date,
                )
                protein_comparison = target_summary.comparisons["protein"]
                if (
                    protein_comparison.comparison_available
                    and protein_comparison.confidence in {"Moderate", "High"}
                    and protein_comparison.target_min is not None
                    and protein_comparison.target_max is not None
                ):
                    direction = "increasing" if protein_delta > 0 else "decreasing"
                    title_direction = "higher" if protein_delta > 0 else "lower"
                    candidates.append(
                        _candidate(
                            stable_id=f"lie_v1:nutrition:protein_{direction}",
                            domain="nutrition",
                            insight_type="logged_protein_trend",
                            title=f"Logged protein has been {title_direction} recently",
                            explanation=(
                                f"Across complete-enough days, average logged protein moved "
                                f"from {_format_number(prior_protein)} to "
                                f"{_format_number(recent_protein)} g/day."
                            ),
                            observation_window=_calendar_window(
                                target,
                                14,
                                len(recent_protein_days),
                                "Latest 14 days",
                            ),
                            comparison_window=_calendar_window(
                                prior_end,
                                14,
                                len(prior_protein_days),
                                "Preceding 14 days",
                            ),
                            evidence=[
                                _comparison_evidence(
                                    metric="average_logged_protein",
                                    label="Average logged protein",
                                    recent_value=recent_protein,
                                    prior_value=prior_protein,
                                    unit="g/day",
                                    source="nutrition_trend_window",
                                    source_fields=[
                                        "logged_protein",
                                        "logging_completeness",
                                        "entry_date",
                                    ],
                                ),
                                InsightEvidence(
                                    metric="approved_protein_target_range",
                                    label="Approved protein target context",
                                    value=(
                                        f"{_format_number(protein_comparison.target_min)}–"
                                        f"{_format_number(protein_comparison.target_max)} g/day"
                                    ),
                                    source="nutrition_target_vs_actual",
                                    source_fields=[
                                        "protein_target_min",
                                        "protein_target_max",
                                        "comparison_available",
                                    ],
                                ),
                            ],
                            evidence_strength=(
                                "strong"
                                if len(recent_protein_days) >= 8
                                and len(prior_protein_days) >= 8
                                else "moderate"
                            ),
                            coverage=InsightDataCoverage(
                                status=(
                                    "strong"
                                    if len(recent_protein_days) >= 8
                                    and len(prior_protein_days) >= 8
                                    else "sufficient"
                                ),
                                observation_count=len(recent_protein_days),
                                comparison_observation_count=len(prior_protein_days),
                                expected_observation_count=14,
                                limitations=[
                                    "Only complete-enough days with present protein values are compared."
                                ],
                            ),
                            direction=direction,
                            status="notable",
                            score=76,
                            dedupe_key="nutrition:protein",
                        )
                    )

    return candidates


def _body_weight_candidates(
    trend: NutritionTrendWindow,
    target: date,
) -> list[_Candidate]:
    bodyweight = trend.bodyweight_trend_summary
    weight_days = [day for day in trend.trend_days if day.bodyweight_lb is not None]
    if (
        bodyweight.weigh_in_count < 6
        or bodyweight.confidence not in {"Moderate", "High"}
        or bodyweight.weekly_rate_lb is None
        or bodyweight.start_weight_lb is None
        or bodyweight.end_weight_lb is None
        or len(weight_days) < 2
    ):
        return []
    span_days = (
        _parse_date(weight_days[-1].date) - _parse_date(weight_days[0].date)
    ).days
    if span_days < 14:
        return []

    weekly_rate = float(bodyweight.weekly_rate_lb)
    direction = bodyweight.trend_direction
    if direction in {"increasing", "decreasing"} and abs(weekly_rate) < 0.35:
        return []
    if direction == "stable" and abs(weekly_rate) > 0.15:
        return []
    if direction not in {"increasing", "decreasing", "stable"}:
        return []

    title = {
        "increasing": "Body weight is trending upward",
        "decreasing": "Body weight is trending downward",
        "stable": "Body weight has been relatively stable",
    }[direction]
    explanation = (
        f"Across {bodyweight.weigh_in_count} weigh-ins spanning {span_days} days, "
        f"the existing trend estimate is {abs(weekly_rate):.2f} lb/week "
        f"{('up' if weekly_rate > 0 else 'down' if weekly_rate < 0 else 'from baseline')}."
    )
    return [
        _candidate(
            stable_id=f"lie_v1:body_weight:{direction}",
            domain="body_weight",
            insight_type="body_weight_trend",
            title=title,
            explanation=explanation,
            observation_window=_calendar_window(
                target,
                28,
                bodyweight.weigh_in_count,
                "Latest 28 days",
            ),
            comparison_window=None,
            evidence=[
                InsightEvidence(
                    metric="body_weight_trend",
                    label="Body-weight measurements",
                    value=(
                        f"{_format_number(bodyweight.start_weight_lb)} → "
                        f"{_format_number(bodyweight.end_weight_lb)} lb · "
                        f"{weekly_rate:+.2f} lb/week"
                    ),
                    source="nutrition_trend_window",
                    source_fields=["body_weight", "checkin_date"],
                )
            ],
            evidence_strength=(
                "strong"
                if bodyweight.weigh_in_count >= 10 and span_days >= 21
                else "moderate"
            ),
            coverage=InsightDataCoverage(
                status=(
                    "strong"
                    if bodyweight.weigh_in_count >= 10 and span_days >= 21
                    else "sufficient"
                ),
                observation_count=bodyweight.weigh_in_count,
                expected_observation_count=28,
                observation_rate=round(bodyweight.weigh_in_count / 28, 2),
                limitations=["Short-term scale fluctuations are not interpreted."],
            ),
            direction=direction,
            status="notable" if direction != "stable" else "consistent",
            score=70 if direction != "stable" else 60,
            dedupe_key="body_weight:trend",
        )
    ]


def _cross_domain_candidates(
    *,
    recovery: RecoveryIntelligenceV2Summary,
    training_candidates: list[_Candidate],
) -> list[_Candidate]:
    profile = _recovery_change_profile(recovery)
    if profile.recent_count < 4 or profile.prior_count < 4:
        return []
    candidates: list[_Candidate] = []
    for training_candidate in sorted(
        training_candidates,
        key=lambda candidate: (-candidate.score, candidate.insight.stable_id),
    ):
        insight = training_candidate.insight
        if (
            insight.insight_type == "stable_load_rising_effort"
            and len(profile.worsening_evidence) >= 2
        ):
            candidates.append(
                _candidate(
                    stable_id=insight.stable_id.replace(
                        "lie_v1:training:rising_effort",
                        "lie_v1:cross_domain:rising_effort_recovery",
                    ),
                    domain="cross_domain",
                    insight_type="rising_effort_with_poorer_recovery",
                    title=f"{insight.title} while recovery signals are poorer",
                    explanation=(
                        f"The exercise pattern overlaps with {len(profile.worsening_evidence)} "
                        "worsening recovery measures. This is an association, not proof of cause."
                    ),
                    observation_window=insight.observation_window,
                    comparison_window=insight.comparison_window,
                    evidence=[*insight.evidence, *profile.worsening_evidence],
                    evidence_strength=(
                        "strong"
                        if insight.evidence_strength == "strong"
                        and len(profile.worsening_evidence) >= 3
                        else "moderate"
                    ),
                    coverage=InsightDataCoverage(
                        status=(
                            "strong"
                            if insight.evidence_strength == "strong"
                            and profile.recent_count >= 6
                            and profile.prior_count >= 6
                            else "sufficient"
                        ),
                        observation_count=(
                            insight.data_coverage.observation_count
                            + profile.recent_count
                        ),
                        comparison_observation_count=(
                            (insight.data_coverage.comparison_observation_count or 0)
                            + profile.prior_count
                        ),
                        limitations=["Coincident patterns do not establish causation."],
                    ),
                    direction="associated",
                    status="attention",
                    score=101,
                    dedupe_key=training_candidate.dedupe_key,
                )
            )
        elif (
            insight.insight_type == "clear_progression"
            and len(profile.improving_evidence) >= 2
        ):
            candidates.append(
                _candidate(
                    stable_id=insight.stable_id.replace(
                        "lie_v1:training:clear_progression",
                        "lie_v1:cross_domain:progression_recovery",
                    ),
                    domain="cross_domain",
                    insight_type="progression_with_improved_recovery",
                    title=f"{insight.title} alongside improving recovery",
                    explanation=(
                        f"The performance change overlaps with "
                        f"{len(profile.improving_evidence)} improving recovery measures. "
                        "This is an association, not proof of cause."
                    ),
                    observation_window=insight.observation_window,
                    comparison_window=insight.comparison_window,
                    evidence=[*insight.evidence, *profile.improving_evidence],
                    evidence_strength=(
                        "strong"
                        if insight.evidence_strength == "strong"
                        and len(profile.improving_evidence) >= 3
                        else "moderate"
                    ),
                    coverage=InsightDataCoverage(
                        status=(
                            "strong"
                            if insight.evidence_strength == "strong"
                            and profile.recent_count >= 6
                            and profile.prior_count >= 6
                            else "sufficient"
                        ),
                        observation_count=(
                            insight.data_coverage.observation_count
                            + profile.recent_count
                        ),
                        comparison_observation_count=(
                            (insight.data_coverage.comparison_observation_count or 0)
                            + profile.prior_count
                        ),
                        limitations=["Coincident patterns do not establish causation."],
                    ),
                    direction="associated",
                    status="supportive",
                    score=91,
                    dedupe_key=training_candidate.dedupe_key,
                )
            )
    return candidates[:2]


def _recovery_change_profile(
    recovery: RecoveryIntelligenceV2Summary,
) -> _RecoveryChangeProfile:
    recent = recovery.windows["recent_7_days"]
    prior = recovery.windows["prior_7_days"]
    recent_count = int(recent["checkin_days"])
    prior_count = int(prior["checkin_days"])
    if recent_count < 4 or prior_count < 4:
        return _RecoveryChangeProfile([], [], recent_count, prior_count)

    worsening: list[InsightEvidence] = []
    improving: list[InsightEvidence] = []
    metrics = [
        ("sleep_hours", "Sleep", "h", 0.5, 1),
        ("average_energy_level", "Energy", "/10", 0.75, 1),
        ("average_soreness_level", "Soreness", "/10", 0.75, -1),
        ("average_stress_level", "Stress", "/5", 0.5, -1),
        ("average_training_motivation", "Motivation", "/5", 0.5, 1),
    ]
    for key, label, unit, threshold, positive_sign in metrics:
        recent_key = "average_sleep_hours" if key == "sleep_hours" else key
        recent_value = _optional_number(recent.get(recent_key))
        prior_value = _optional_number(prior.get(recent_key))
        change = _delta(recent_value, prior_value)
        if change is None or abs(change) < threshold:
            continue
        evidence = _comparison_evidence(
            metric=key,
            label=label,
            recent_value=recent_value,
            prior_value=prior_value,
            unit=unit,
            source="daily_checkins",
            source_fields=[key, "checkin_date"],
        )
        if change * positive_sign > 0:
            improving.append(evidence)
        else:
            worsening.append(evidence)
    return _RecoveryChangeProfile(worsening, improving, recent_count, prior_count)


def _training_exposures(
    exercise: ExerciseHistoryAnalyticsSummary,
) -> list[_TrainingExposure]:
    exposures = []
    for session in exercise.recent_sessions:
        performed_at = _optional_date(session.performed_at)
        if (
            performed_at is None
            or session.comparable_working_weight is None
            or session.average_actual_rir is None
            or not session.completed_sets
            or any(item.actual_reps is None for item in session.completed_sets)
        ):
            continue
        exposures.append(
            _TrainingExposure(
                performed_at=performed_at,
                weight_lb=float(session.comparable_working_weight),
                average_rir=float(session.average_actual_rir),
                average_reps=mean(
                    float(item.actual_reps)
                    for item in session.completed_sets
                    if item.actual_reps is not None
                ),
            )
        )
    return exposures


def _complete_nutrition_days(days: list[NutritionTrendDay]) -> list[NutritionTrendDay]:
    return [day for day in days if day.logging_completeness in _COMPLETE_NUTRITION_DAYS]


def _candidate(
    *,
    stable_id: str,
    domain: str,
    insight_type: str,
    title: str,
    explanation: str,
    observation_window: InsightWindow,
    comparison_window: InsightWindow | None,
    evidence: list[InsightEvidence],
    evidence_strength: str,
    coverage: InsightDataCoverage,
    direction: str,
    status: str,
    score: int,
    dedupe_key: str,
) -> _Candidate:
    return _Candidate(
        insight=LongitudinalInsight(
            stable_id=stable_id,
            domain=domain,
            insight_type=insight_type,
            title=title,
            explanation=explanation,
            observation_window=observation_window,
            comparison_window=comparison_window,
            evidence=evidence,
            evidence_strength=evidence_strength,
            data_coverage=coverage,
            direction=direction,
            status=status,
        ),
        score=score,
        dedupe_key=dedupe_key,
    )


def _rank_and_dedupe(candidates: list[_Candidate], *, limit: int) -> list[_Candidate]:
    ordered = sorted(candidates, key=lambda item: (-item.score, item.insight.stable_id))
    selected: list[_Candidate] = []
    seen_keys: set[str] = set()
    domain_counts: dict[str, int] = {}
    domain_limits = {
        "recovery": 2,
        "training": 2,
        "nutrition": 1,
        "body_weight": 1,
        "cross_domain": 2,
    }
    for candidate in ordered:
        domain = candidate.insight.domain
        if candidate.dedupe_key in seen_keys:
            continue
        if domain_counts.get(domain, 0) >= domain_limits[domain]:
            continue
        selected.append(candidate)
        seen_keys.add(candidate.dedupe_key)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if len(selected) >= limit:
            break
    return selected


def _comparison_evidence(
    *,
    metric: str,
    label: str,
    recent_value: float | int | None,
    prior_value: float | int | None,
    unit: str,
    source: str,
    source_fields: list[str],
) -> InsightEvidence:
    recent_display = "unknown" if recent_value is None else _format_number(recent_value)
    prior_display = "unknown" if prior_value is None else _format_number(prior_value)
    return InsightEvidence(
        metric=metric,
        label=label,
        value=f"{prior_display}{unit} → {recent_display}{unit}",
        source=source,
        source_fields=source_fields,
    )


def _calendar_window(
    end_date: date,
    days: int,
    observation_count: int,
    label: str,
) -> InsightWindow:
    return InsightWindow(
        start_date=(end_date - timedelta(days=days - 1)).isoformat(),
        end_date=end_date.isoformat(),
        days=days,
        observation_count=observation_count,
        label=label,
    )


def _exposure_window(
    exposures: list[_TrainingExposure],
    label: str,
) -> InsightWindow:
    dates = [item.performed_at for item in exposures]
    start = min(dates)
    end = max(dates)
    return InsightWindow(
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        days=(end - start).days + 1,
        observation_count=len(exposures),
        label=label,
    )


def _coverage(observation_count: int, *, expected: int) -> InsightDataCoverage:
    rate = observation_count / expected
    return InsightDataCoverage(
        status="strong" if rate >= 0.85 else "sufficient",
        observation_count=observation_count,
        expected_observation_count=expected,
        observation_rate=round(rate, 2),
    )


def _paired_coverage(
    observation_count: int,
    comparison_count: int,
    *,
    expected: int,
) -> InsightDataCoverage:
    rate = min(observation_count, comparison_count) / expected
    return InsightDataCoverage(
        status="strong" if rate >= 0.85 else "sufficient",
        observation_count=observation_count,
        comparison_observation_count=comparison_count,
        expected_observation_count=expected,
        observation_rate=round(rate, 2),
    )


def _paired_exposure_coverage(
    observation_count: int,
    comparison_count: int,
) -> InsightDataCoverage:
    return InsightDataCoverage(
        status=(
            "strong"
            if observation_count >= 3 and comparison_count >= 3
            else "sufficient"
        ),
        observation_count=observation_count,
        comparison_observation_count=comparison_count,
    )


def _active_week_count(workout_dates: list[date], target: date) -> int:
    return sum(
        1
        for week_index in range(4)
        if any(
            target - timedelta(days=(week_index + 1) * 7 - 1)
            <= workout_date
            <= target - timedelta(days=week_index * 7)
            for workout_date in workout_dates
        )
    )


def _exercise_identity(exercise: ExerciseHistoryAnalyticsSummary) -> str:
    if exercise.catalog_exercise_id is not None:
        return f"catalog_{exercise.catalog_exercise_id}"
    return f"name_{_stable_token(exercise.exercise_name)}"


def _stable_token(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return normalized or "unknown"


def _label_token(value: str) -> str:
    return str(value).replace("_", " ").strip().title()


def _delta(recent: float | None, prior: float | None) -> float | None:
    if recent is None or prior is None:
        return None
    return round(recent - prior, 2)


def _optional_number(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _format_number(value: float | int) -> str:
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.1f}"


def _optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _resolve_as_of_date(
    *,
    as_of_date: str | date | None,
    target_date: str | date | None,
) -> date:
    resolved_as_of = _parse_date(as_of_date) if as_of_date is not None else None
    resolved_target = _parse_date(target_date) if target_date is not None else None
    if (
        resolved_as_of is not None
        and resolved_target is not None
        and resolved_as_of != resolved_target
    ):
        raise ValueError("as_of_date and target_date must match when both are provided")
    return resolved_as_of or resolved_target or date.today()


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format") from exc
