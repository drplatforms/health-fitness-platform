from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from statistics import mean
from typing import Any

from models.coach_models import (
    CoachEvidenceItem,
    CoachEvidencePlan,
    CoachEvidencePlanLimitation,
    CoachEvidenceWindow,
)
from models.nutrition_trend_models import LOGGING_COMPLETENESS_NO_LOGS
from services.exercise_catalog_service import get_exercise_catalog
from services.nutrition_trend_service import build_nutrition_trend_window
from services.recovery_intelligence_v2_service import build_recovery_history_window
from services.workout_progression_decision_service import comparable_working_weight
from services.workout_progression_history_service import (
    ExerciseProgressionSession,
    completed_exercise_actual_rows,
    load_completed_user_progression_sessions,
)

MAX_BROAD_LIKE_FOR_LIKE_EXERCISE_SERIES = 1
MAX_TRAINING_LIKE_FOR_LIKE_EXERCISE_SERIES = 3


@dataclass(frozen=True)
class CoachHistoricalEvidenceResult:
    evidence: tuple[CoachEvidenceItem, ...]
    limitations: tuple[CoachEvidencePlanLimitation, ...]
    source_services: tuple[str, ...]


def build_coach_historical_evidence(
    *,
    user_id: int,
    plan: CoachEvidencePlan,
) -> CoachHistoricalEvidenceResult:
    """Build compact neutral measurements only for windows selected by the plan."""

    if plan.historical_depth == "baseline" or not plan.windows:
        return CoachHistoricalEvidenceResult((), (), ())

    domains = set(plan.requested_domains)
    presentation_windows = plan.presentation_windows or plan.windows
    evidence: list[CoachEvidenceItem] = []
    limitations: list[CoachEvidencePlanLimitation] = []
    source_services: list[str] = ["coach_historical_evidence_service"]

    if "training" in domains:
        item, domain_limitations = _training_history_item(user_id=user_id, plan=plan)
        if item is not None:
            evidence.append(item)
        limitations.extend(domain_limitations)
        source_services.extend(
            ["workout_progression_history_service", "exercise_catalog_service"]
        )

    recovery_windows: list[dict[str, Any]] = []
    if "recovery" in domains:
        recovery_windows = [
            _recovery_window(user_id=user_id, window=window)
            for window in presentation_windows
        ]
        item = _recovery_history_item(plan=plan, windows=recovery_windows)
        if item is not None:
            evidence.append(item)
        limitations.extend(
            _domain_coverage_limitations(
                domain="recovery",
                plan=plan,
                observed_dates=[
                    value
                    for window in recovery_windows
                    for value in (
                        window.get("first_observed_date"),
                        window.get("last_observed_date"),
                    )
                    if isinstance(value, str)
                ],
                observation_count=sum(
                    int(window.get("checkin_days") or 0) for window in recovery_windows
                ),
                expected_minimum=max(1, _retrieval_days(plan) // 4),
            )
        )
        source_services.append("recovery_intelligence_v2_service")

    nutrition_windows: list[Any] = []
    if {"nutrition", "body_weight"}.intersection(domains):
        nutrition_windows = [
            build_nutrition_trend_window(
                user_id=user_id,
                start_date=window.start_date,
                end_date=window.end_date,
            )
            for window in presentation_windows
        ]
        source_services.append("nutrition_trend_service")

    if "nutrition" in domains:
        item = _nutrition_history_item(
            plan=plan,
            period_windows=presentation_windows,
            windows=nutrition_windows,
        )
        if item is not None:
            evidence.append(item)
        logged_dates = [
            day.date
            for window in nutrition_windows
            for day in window.trend_days
            if day.logging_completeness != LOGGING_COMPLETENESS_NO_LOGS
        ]
        limitations.extend(
            _domain_coverage_limitations(
                domain="nutrition",
                plan=plan,
                observed_dates=logged_dates,
                observation_count=len(logged_dates),
                expected_minimum=max(1, _retrieval_days(plan) // 4),
            )
        )

    if "body_weight" in domains:
        item = _body_weight_history_item(
            plan=plan,
            period_windows=presentation_windows,
            windows=nutrition_windows,
        )
        if item is not None:
            evidence.append(item)
        weigh_in_dates = [
            day.date
            for window in nutrition_windows
            for day in window.trend_days
            if day.bodyweight_lb is not None
        ]
        limitations.extend(
            _domain_coverage_limitations(
                domain="body_weight",
                plan=plan,
                observed_dates=weigh_in_dates,
                observation_count=len(weigh_in_dates),
                expected_minimum=max(2, _retrieval_days(plan) // 28),
            )
        )

    if "profile" in domains:
        limitations.append(
            CoachEvidencePlanLimitation(
                code="persisted_profile_history_unavailable",
                domain="profile",
                message=(
                    "Only the current saved profile is persisted; historical goal or "
                    "profile transitions are not available as Coach evidence."
                ),
                requested_start_date=plan.requested_start_date,
                requested_end_date=plan.requested_end_date,
            )
        )

    return CoachHistoricalEvidenceResult(
        evidence=tuple(evidence),
        limitations=tuple(_dedupe_limitations(limitations)),
        source_services=tuple(dict.fromkeys(source_services)),
    )


def _training_history_item(
    *,
    user_id: int,
    plan: CoachEvidencePlan,
) -> tuple[CoachEvidenceItem | None, list[CoachEvidencePlanLimitation]]:
    retrieval_days = _retrieval_days(plan)
    sessions = load_completed_user_progression_sessions(
        user_id=user_id,
        lookback_days=retrieval_days,
        end_date=plan.retrieval_end_date,
    )
    sessions = [session for session in sessions if _session_in_plan(session, plan)]
    subject = _normalize(plan.subject) if plan.subject else None
    if subject:
        sessions = [
            session
            for session in sessions
            if _normalize(session.effective_exercise_name) == subject
        ]

    presentation_windows = plan.presentation_windows or plan.windows
    windows = [
        _training_window(window=window, sessions=sessions)
        for window in presentation_windows
    ]
    observed_dates = sorted(
        {
            str(session.performed_at)
            for session in sessions
            if session.performed_at is not None
        }
    )
    limitations = _domain_coverage_limitations(
        domain="training",
        plan=plan,
        observed_dates=observed_dates,
        observation_count=len(
            {session.workout_execution_session_id for session in sessions}
        ),
        expected_minimum=max(1, retrieval_days // 28),
    )
    if not observed_dates:
        return None, limitations

    scope = plan.subject or "all completed training"
    public_workload_and_consistency = _table_payload(
        windows,
        (
            ("period", "label"),
            ("start_date", "start_date"),
            ("end_date", "end_date"),
            ("days_covered", "days_covered"),
            ("expected_days", "period_expected_days"),
            ("coverage_rate", "period_coverage_rate"),
            ("partial_period", "is_partial_period"),
            ("workouts", "completed_workout_count"),
            ("workouts_per_week", "workouts_per_week"),
            ("completed_sets", "completed_set_count"),
            ("completed_sets_per_week", "completed_sets_per_week"),
            ("completed_sets_per_workout", "completed_sets_per_workout"),
            ("set_completion_rate", "set_completion_rate"),
            (
                "consistently_trained_exercise_count",
                "consistently_trained_exercise_count",
            ),
        ),
    )
    workload_and_consistency = _table_payload(
        windows,
        (
            ("period", "label"),
            ("workouts", "completed_workout_count"),
            ("workouts_per_week", "workouts_per_week"),
            ("completed_sets", "completed_set_count"),
            ("completed_sets_per_week", "completed_sets_per_week"),
            ("completed_sets_per_workout", "completed_sets_per_workout"),
            ("set_completion_rate", "set_completion_rate"),
            (
                "consistently_trained_exercise_count",
                "consistently_trained_exercise_count",
            ),
        ),
    )
    public_like_for_like_progression = _like_for_like_exercise_progression(
        plan=plan,
        sessions=sessions,
    )
    like_for_like_progression = _compact_progression_for_synthesis(
        public_like_for_like_progression
    )
    model_data = {
        "scope": scope,
        "workload_and_consistency": workload_and_consistency,
        "like_for_like_exercise_progression": like_for_like_progression,
    }
    public_data = {
        "scope": scope,
        "workload_and_consistency": public_workload_and_consistency,
        "like_for_like_exercise_progression": public_like_for_like_progression,
    }
    return (
        CoachEvidenceItem(
            reference_id=_reference("training", plan, plan.subject),
            domain="training",
            evidence_type="training_history_windows",
            label="Planned training history",
            fact=(
                f"Training workload, consistency, and like-for-like exercise "
                f"measurements for {scope} are summarized in "
                f"{len(windows)} {_period_series_name(presentation_windows)} from "
                f"{plan.retrieval_start_date} through {plan.retrieval_end_date}."
            ),
            confidence="Moderate",
            source="workout_progression_history_service",
            observed_at=observed_dates[-1],
            structured_data={
                "scope": scope,
                "windows": windows,
                "measurement_groups": model_data,
            },
            synthesis_data=model_data,
            public_data=public_data,
        ),
        limitations,
    )


def _training_window(
    *,
    window: CoachEvidenceWindow,
    sessions: Sequence[ExerciseProgressionSession],
) -> dict[str, Any]:
    selected = [
        session
        for session in sessions
        if session.performed_at is not None
        and window.start_date <= session.performed_at <= window.end_date
    ]
    rows = [
        row for session in selected for row in completed_exercise_actual_rows(session)
    ]
    planned_sets = sum(max(0, session.planned_set_count) for session in selected)
    completed_sets = len(rows)
    weights = [
        float(row["actual_weight"])
        for row in rows
        if row.get("actual_weight") is not None
    ]
    reps = [
        float(row["actual_reps"]) for row in rows if row.get("actual_reps") is not None
    ]
    rirs = [
        float(row["actual_rir"]) for row in rows if row.get("actual_rir") is not None
    ]
    volumes = [
        float(row["actual_weight"]) * float(row["actual_reps"])
        for row in rows
        if row.get("actual_weight") is not None and row.get("actual_reps") is not None
    ]
    workout_count = len({session.workout_execution_session_id for session in selected})
    exposure_counts: dict[str, int] = {}
    for session in selected:
        exercise_key = _normalize(session.effective_exercise_name)
        exposure_counts[exercise_key] = exposure_counts.get(exercise_key, 0) + 1
    consistency_min_exposures = max(1, (window.days + 13) // 14)
    return {
        **_period_metadata(window),
        "completed_workout_count": workout_count,
        "workouts_per_week": round(workout_count * 7 / window.days, 2),
        "exercise_exposure_count": len(selected),
        "distinct_exercise_count": len(exposure_counts),
        "exercise_consistency_min_exposures": consistency_min_exposures,
        "consistently_trained_exercise_count": sum(
            1
            for count in exposure_counts.values()
            if count >= consistency_min_exposures
        ),
        "planned_set_count": planned_sets,
        "completed_set_count": completed_sets,
        "completed_sets_per_week": round(completed_sets * 7 / window.days, 2),
        "completed_sets_per_workout": (
            round(completed_sets / workout_count, 2) if workout_count else None
        ),
        "set_completion_rate": (
            round(min(1.0, completed_sets / planned_sets), 3)
            if planned_sets > 0
            else None
        ),
        "volume_load_lb": round(sum(volumes), 1) if volumes else None,
        "average_load_lb": _average(weights),
        "average_reps": _average(reps),
        "average_rir": _average(rirs),
        "load_value_set_count": len(weights),
        "rep_value_set_count": len(reps),
        "rir_value_set_count": len(rirs),
    }


def _like_for_like_exercise_progression(
    *,
    plan: CoachEvidencePlan,
    sessions: Sequence[ExerciseProgressionSession],
) -> dict[str, Any]:
    grouped: dict[tuple[int | None, str], list[ExerciseProgressionSession]] = {}
    for session in sessions:
        identity = (
            session.effective_catalog_exercise_id,
            _normalize(session.effective_exercise_name),
        )
        grouped.setdefault(identity, []).append(session)

    catalog_by_name = {
        _normalize(entry.name): entry for entry in get_exercise_catalog()
    }

    def catalog_entry_for(
        exercise_sessions: Sequence[ExerciseProgressionSession],
    ) -> Any | None:
        return catalog_by_name.get(
            _normalize(exercise_sessions[0].effective_exercise_name)
        )

    strength_groups = [
        exercise_sessions
        for exercise_sessions in grouped.values()
        if (
            catalog_entry_for(exercise_sessions) is not None
            and catalog_entry_for(exercise_sessions).exercise_type == "strength"
        )
    ]
    ranking_pool = strength_groups or list(grouped.values())

    def ranking_key(
        exercise_sessions: Sequence[ExerciseProgressionSession],
    ) -> tuple[int, bool, int, str]:
        session = exercise_sessions[0]
        catalog_entry = catalog_entry_for(exercise_sessions)
        catalog_id = (
            catalog_entry.id
            if catalog_entry is not None
            else session.effective_catalog_exercise_id
        )
        return (
            -len(exercise_sessions),
            catalog_id is None,
            catalog_id or 0,
            _normalize(session.effective_exercise_name),
        )

    ranked = sorted(
        ranking_pool,
        key=ranking_key,
    )
    series_limit = (
        1
        if plan.subject
        else (
            MAX_TRAINING_LIKE_FOR_LIKE_EXERCISE_SERIES
            if set(plan.requested_domains) == {"training"}
            else MAX_BROAD_LIKE_FOR_LIKE_EXERCISE_SERIES
        )
    )
    selected = ranked[:series_limit]
    series = []
    for exercise_sessions in selected:
        exercise = exercise_sessions[0]
        catalog_entry = catalog_by_name.get(
            _normalize(exercise.effective_exercise_name)
        )
        measurements = [
            _exercise_progression_window(window=window, sessions=exercise_sessions)
            for window in (plan.presentation_windows or plan.windows)
        ]
        series.append(
            {
                "exercise_name": exercise.effective_exercise_name,
                "catalog_exercise_id": (
                    catalog_entry.id
                    if catalog_entry is not None
                    else exercise.effective_catalog_exercise_id
                ),
                "exercise_type": (
                    catalog_entry.exercise_type if catalog_entry is not None else None
                ),
                "total_exposure_count": len(exercise_sessions),
                **_table_payload(
                    measurements,
                    (
                        ("period", "label"),
                        ("start_date", "start_date"),
                        ("end_date", "end_date"),
                        ("days_covered", "days_covered"),
                        ("coverage_rate", "period_coverage_rate"),
                        ("partial_period", "is_partial_period"),
                        ("exposures", "exercise_exposure_count"),
                        ("comparable_load_lb", "average_comparable_load_lb"),
                        ("average_reps", "average_reps"),
                        ("average_rir", "average_rir"),
                    ),
                ),
            }
        )
    return {
        "selection_basis": (
            "named_subject"
            if plan.subject
            else "highest_exposure_count_strength_exercises_with_stable_catalog_tiebreak"
        ),
        "series_limit": series_limit,
        "available_exercise_count": len(grouped),
        "available_strength_exercise_count": len(strength_groups),
        "series": series,
    }


def _exercise_progression_window(
    *,
    window: CoachEvidenceWindow,
    sessions: Sequence[ExerciseProgressionSession],
) -> dict[str, Any]:
    selected = [
        session
        for session in sessions
        if session.performed_at is not None
        and window.start_date <= session.performed_at <= window.end_date
    ]
    rows = [
        row for session in selected for row in completed_exercise_actual_rows(session)
    ]
    comparable_loads = [
        load
        for session in selected
        if (load := comparable_working_weight(session)) is not None
    ]
    reps = [
        float(row["actual_reps"]) for row in rows if row.get("actual_reps") is not None
    ]
    rirs = [
        float(row["actual_rir"]) for row in rows if row.get("actual_rir") is not None
    ]
    return {
        **_period_metadata(window),
        "exercise_exposure_count": len(selected),
        "completed_set_count": len(rows),
        "average_comparable_load_lb": _average(comparable_loads),
        "average_reps": _average(reps),
        "average_rir": _average(rirs),
    }


def _compact_progression_for_synthesis(
    progression: dict[str, Any],
) -> dict[str, Any]:
    compact_series: list[dict[str, Any]] = []
    for series in progression["series"]:
        columns = series["columns"]
        exposure_index = columns.index("exposures")
        observed_rows = [
            row for row in series["rows"] if int(row[exposure_index] or 0) > 0
        ]
        rows = (
            observed_rows
            if len(observed_rows) <= 2
            else [observed_rows[0], observed_rows[-1]]
        )
        compact_series.append(
            {
                "exercise_name": series["exercise_name"],
                "total_exposure_count": series["total_exposure_count"],
                "columns": [
                    "period",
                    "exposures",
                    "comparable_load_lb",
                    "average_reps",
                    "average_rir",
                ],
                "rows": [
                    [
                        row[columns.index("period")],
                        row[exposure_index],
                        row[columns.index("comparable_load_lb")],
                        row[columns.index("average_reps")],
                        row[columns.index("average_rir")],
                    ]
                    for row in rows
                ],
            }
        )
    return {
        "selection_basis": "exposure_count_not_performance",
        "series": compact_series,
    }


def _recovery_window(
    *,
    user_id: int,
    window: CoachEvidenceWindow,
) -> dict[str, Any]:
    result = build_recovery_history_window(
        user_id=user_id,
        start_date=window.start_date,
        end_date=window.end_date,
    )
    return {
        **result,
        **_period_metadata(window),
        "observation_coverage_rate": round(
            int(result["checkin_days"]) / window.days,
            3,
        ),
    }


def _recovery_history_item(
    *,
    plan: CoachEvidencePlan,
    windows: Sequence[dict[str, Any]],
) -> CoachEvidenceItem | None:
    observed = [window for window in windows if int(window["checkin_days"]) > 0]
    if not observed:
        return None
    public_windows = _table_payload(
        windows,
        (
            ("period", "label"),
            ("start_date", "start_date"),
            ("end_date", "end_date"),
            ("days_covered", "days_covered"),
            ("expected_days", "period_expected_days"),
            ("period_coverage_rate", "period_coverage_rate"),
            ("partial_period", "is_partial_period"),
            ("checkin_days", "checkin_days"),
            ("checkin_coverage_rate", "observation_coverage_rate"),
            ("sleep_hours", "average_sleep_hours"),
            ("sleep_quality_1_5", "average_sleep_quality"),
            ("energy_1_10", "average_energy_level"),
            ("soreness_1_10", "average_soreness_level"),
            ("stress_1_5", "average_stress_level"),
            ("motivation_1_5", "average_training_motivation"),
            ("pain_counts", "pain_concern_counts"),
        ),
    )
    synthesis_windows = _table_payload(
        windows,
        (
            ("period", "label"),
            ("checkin_days", "checkin_days"),
            ("checkin_coverage_rate", "observation_coverage_rate"),
            ("sleep_hours", "average_sleep_hours"),
            ("energy_1_10", "average_energy_level"),
            ("soreness_1_10", "average_soreness_level"),
        ),
    )
    latest_observed = max(
        str(item["last_observed_date"])
        for item in observed
        if item.get("last_observed_date") is not None
    )
    return CoachEvidenceItem(
        reference_id=_reference("recovery", plan),
        domain="recovery",
        evidence_type="recovery_history_windows",
        label="Planned recovery history",
        fact=(
            f"Recovery check-ins are summarized in {len(windows)} "
            f"{_period_series_name(plan.presentation_windows or plan.windows)} from "
            f"{plan.retrieval_start_date} through "
            f"{plan.retrieval_end_date}."
        ),
        confidence="Moderate",
        source="recovery_intelligence_v2_service",
        observed_at=latest_observed,
        structured_data={"windows": list(windows)},
        synthesis_data=synthesis_windows,
        public_data=public_windows,
    )


def _nutrition_history_item(
    *,
    plan: CoachEvidencePlan,
    period_windows: Sequence[CoachEvidenceWindow],
    windows: Sequence[Any],
) -> CoachEvidenceItem | None:
    if not any(window.logged_day_count > 0 for window in windows):
        return None
    structured_windows = [
        _nutrition_window_data(period_window, window)
        for period_window, window in zip(period_windows, windows, strict=True)
    ]
    public_windows = _table_payload(
        structured_windows,
        (
            ("period", "label"),
            ("start_date", "start_date"),
            ("end_date", "end_date"),
            ("days_covered", "days_covered"),
            ("expected_days", "period_expected_days"),
            ("period_coverage_rate", "period_coverage_rate"),
            ("partial_period", "is_partial_period"),
            ("logged_days", "logged_day_count"),
            ("complete_days", "complete_logging_day_count"),
            ("partial_days", "partial_logging_day_count"),
            ("logging_status", "logging_consistency_status"),
            ("average_calories", "average_calories"),
            ("average_protein_g", "average_protein_g"),
            ("average_carbohydrate_g", "average_carbohydrate_g"),
            ("average_fat_g", "average_fat_g"),
        ),
    )
    synthesis_windows = _table_payload(
        structured_windows,
        (
            ("period", "label"),
            ("logged_days", "logged_day_count"),
            ("complete_days", "complete_logging_day_count"),
            ("partial_days", "partial_logging_day_count"),
            ("logging_status", "logging_consistency_status"),
            ("average_calories", "average_calories"),
            ("average_protein_g", "average_protein_g"),
        ),
    )
    observed_dates = [
        day.date
        for window in windows
        for day in window.trend_days
        if day.logging_completeness != LOGGING_COMPLETENESS_NO_LOGS
    ]
    return CoachEvidenceItem(
        reference_id=_reference("nutrition", plan),
        domain="nutrition",
        evidence_type="nutrition_history_windows",
        label="Planned nutrition history",
        fact=(
            f"Nutrition logging coverage and supported averages are summarized "
            f"in {len(windows)} {_period_series_name(period_windows)}; partial "
            "calendar periods and partial logging days remain "
            "identified separately from complete days."
        ),
        confidence="Moderate",
        source="nutrition_trend_service",
        observed_at=max(observed_dates),
        structured_data={"windows": structured_windows},
        synthesis_data=synthesis_windows,
        public_data=public_windows,
    )


def _nutrition_window_data(
    period_window: CoachEvidenceWindow,
    window: Any,
) -> dict[str, Any]:
    intake = window.intake_trend_summary
    return {
        **_period_metadata(period_window),
        "window_days": window.window_days,
        "logged_day_count": window.logged_day_count,
        "complete_logging_day_count": window.complete_logging_day_count,
        "partial_logging_day_count": window.partial_logging_day_count,
        "no_log_day_count": window.no_log_day_count,
        "logging_consistency_status": intake.logging_consistency_status,
        "average_calories": intake.average_calories,
        "average_protein_g": intake.average_protein_g,
        "average_carbohydrate_g": intake.average_carbohydrate_g,
        "average_fat_g": intake.average_fat_g,
        "confidence": intake.confidence,
    }


def _body_weight_history_item(
    *,
    plan: CoachEvidencePlan,
    period_windows: Sequence[CoachEvidenceWindow],
    windows: Sequence[Any],
) -> CoachEvidenceItem | None:
    available = [
        window
        for window in windows
        if window.bodyweight_trend_summary.weigh_in_count > 0
    ]
    if not available:
        return None
    structured_windows = [
        {
            **_period_metadata(period_window),
            "weigh_in_count": window.bodyweight_trend_summary.weigh_in_count,
            "start_weight_lb": window.bodyweight_trend_summary.start_weight_lb,
            "end_weight_lb": window.bodyweight_trend_summary.end_weight_lb,
            "average_weight_lb": window.bodyweight_trend_summary.average_weight_lb,
            "trend_direction": window.bodyweight_trend_summary.trend_direction,
            "weekly_rate_lb": window.bodyweight_trend_summary.weekly_rate_lb,
            "confidence": window.bodyweight_trend_summary.confidence,
        }
        for period_window, window in zip(period_windows, windows, strict=True)
    ]
    public_windows = _table_payload(
        structured_windows,
        (
            ("period", "label"),
            ("start_date", "start_date"),
            ("end_date", "end_date"),
            ("days_covered", "days_covered"),
            ("expected_days", "period_expected_days"),
            ("period_coverage_rate", "period_coverage_rate"),
            ("partial_period", "is_partial_period"),
            ("weigh_ins", "weigh_in_count"),
            ("start_weight_lb", "start_weight_lb"),
            ("end_weight_lb", "end_weight_lb"),
            ("direction", "trend_direction"),
            ("weekly_rate_lb", "weekly_rate_lb"),
        ),
    )
    synthesis_windows = _table_payload(
        structured_windows,
        (
            ("period", "label"),
            ("weigh_ins", "weigh_in_count"),
            ("start_weight_lb", "start_weight_lb"),
            ("end_weight_lb", "end_weight_lb"),
            ("weekly_rate_lb", "weekly_rate_lb"),
        ),
    )
    observed_dates = [
        day.date
        for window in windows
        for day in window.trend_days
        if day.bodyweight_lb is not None
    ]
    return CoachEvidenceItem(
        reference_id=_reference("body-weight", plan),
        domain="body_weight",
        evidence_type="body_weight_history_periods",
        label="Planned body-weight history",
        fact=(
            f"Body-weight measurements are summarized in {len(windows)} "
            f"{_period_series_name(period_windows)}."
        ),
        confidence="Moderate",
        source="nutrition_trend_service",
        observed_at=max(observed_dates),
        structured_data={"windows": structured_windows},
        synthesis_data=synthesis_windows,
        public_data=public_windows,
    )


def _domain_coverage_limitations(
    *,
    domain: str,
    plan: CoachEvidencePlan,
    observed_dates: Sequence[str],
    observation_count: int,
    expected_minimum: int,
) -> list[CoachEvidencePlanLimitation]:
    if not observed_dates or observation_count == 0:
        return [
            CoachEvidencePlanLimitation(
                code="no_history_for_requested_range",
                domain=domain,
                message=(
                    f"No persisted {domain.replace('_', ' ')} history was available "
                    "for the requested retrieval range."
                ),
                requested_start_date=plan.requested_start_date,
                requested_end_date=plan.requested_end_date,
            )
        ]
    first = min(observed_dates)
    last = max(observed_dates)
    retrieval_days = _retrieval_days(plan)
    observed_span = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
    if observation_count >= expected_minimum and (
        retrieval_days <= 31 or observed_span / retrieval_days >= 0.5
    ):
        return []
    return [
        CoachEvidencePlanLimitation(
            code="partial_history_for_requested_range",
            domain=domain,
            message=(
                f"Persisted {domain.replace('_', ' ')} history only partially covers "
                "the requested retrieval range."
            ),
            requested_start_date=plan.requested_start_date,
            requested_end_date=plan.requested_end_date,
            available_start_date=first,
            available_end_date=last,
        )
    ]


def _session_in_plan(
    session: ExerciseProgressionSession,
    plan: CoachEvidencePlan,
) -> bool:
    return bool(
        session.performed_at is not None
        and plan.retrieval_start_date is not None
        and plan.retrieval_end_date is not None
        and plan.retrieval_start_date <= session.performed_at <= plan.retrieval_end_date
    )


def _retrieval_days(plan: CoachEvidencePlan) -> int:
    if plan.retrieval_start_date is None or plan.retrieval_end_date is None:
        return 0
    return (
        date.fromisoformat(plan.retrieval_end_date)
        - date.fromisoformat(plan.retrieval_start_date)
    ).days + 1


def _reference(
    domain: str,
    plan: CoachEvidencePlan,
    subject: str | None = None,
) -> str:
    subject_token = f":{_token(subject)}" if subject else ""
    return (
        f"coach-history:{domain}:{plan.retrieval_start_date}:"
        f"{plan.retrieval_end_date}{subject_token}"
    )


def _average(values: Sequence[float]) -> float | None:
    return round(mean(values), 2) if values else None


def _table_payload(
    windows: Sequence[dict[str, Any]],
    columns: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    return {
        "columns": [label for label, _ in columns],
        "rows": [
            [window.get(source_key) for _, source_key in columns] for window in windows
        ],
    }


def _period_metadata(window: CoachEvidenceWindow) -> dict[str, Any]:
    expected_days = window.expected_days or window.days
    return {
        "label": window.label,
        "role": window.role,
        "period_kind": window.period_kind,
        "start_date": window.start_date,
        "end_date": window.end_date,
        "days_covered": window.days,
        "period_expected_days": expected_days,
        "period_coverage_rate": round(window.days / expected_days, 3),
        "is_partial_period": window.is_partial_period,
    }


def _period_series_name(windows: Sequence[CoachEvidenceWindow]) -> str:
    kinds = {window.period_kind for window in windows}
    if kinds == {"calendar_month"}:
        return "calendar-month summaries"
    if kinds == {"week"}:
        return "weekly summaries"
    if kinds == {"two_week_period"}:
        return "two-week summaries"
    return "dated period summaries"


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", value.lower())).strip()


def _token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _dedupe_limitations(
    limitations: Sequence[CoachEvidencePlanLimitation],
) -> list[CoachEvidencePlanLimitation]:
    return list(dict.fromkeys(limitations))
