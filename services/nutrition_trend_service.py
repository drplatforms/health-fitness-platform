from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Any

from database import get_connection
from models.nutrition_trend_models import (
    BODYWEIGHT_TREND_DECREASING,
    BODYWEIGHT_TREND_INCREASING,
    BODYWEIGHT_TREND_STABLE,
    BODYWEIGHT_TREND_UNAVAILABLE,
    CALIBRATION_READINESS_EARLY_SIGNAL,
    CALIBRATION_READINESS_NOT_READY,
    CALIBRATION_READINESS_STRONG,
    CALIBRATION_READINESS_USABLE,
    INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD,
    INTAKE_PLAUSIBILITY_NOT_FLAGGED,
    INTAKE_PLAUSIBILITY_UNKNOWN,
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    LOGGING_CONSISTENCY_INCONSISTENT,
    LOGGING_CONSISTENCY_INSUFFICIENT,
    LOGGING_CONSISTENCY_STRONG,
    LOGGING_CONSISTENCY_USABLE,
    BodyweightTrendSummary,
    NutritionCalibrationReadiness,
    NutritionIntakeTrendSummary,
    NutritionTargetContext,
    NutritionTrendDay,
    NutritionTrendWindow,
    NutritionTrendWindowMetadata,
)
from services.nutrition_intelligence_service import build_nutrition_observations
from services.nutrition_target_vs_actual_service import (
    _logging_summary_from_actuals,
    build_formula_derived_nutrition_targets,
    build_nutrition_actuals,
)
from services.user_service import get_user_profile
from services.user_state_service import build_user_health_state

MINIMUM_TREND_WINDOW_DAYS = 14
PREFERRED_TREND_WINDOW_DAYS = 28
STABLE_WEEKLY_WEIGHT_RATE_LB = 0.25
DEFAULT_COMPLETE_DAY_CALORIE_FLOOR = 600.0
CURRENT_TARGET_CONTEXT_DAYS = 28

_COMPLETE_LOGGING_VALUES = {
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
}
_PARTIAL_LOGGING_VALUES = {
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
}
_CONFIDENCE_RANK = {"Limited": 0, "Low": 1, "Moderate": 2, "High": 3}


def build_nutrition_trend_window(
    user_id: int,
    *,
    end_date: str | None = None,
    window_days: int = PREFERRED_TREND_WINDOW_DAYS,
    start_date: str | None = None,
) -> NutritionTrendWindow:
    """Build deterministic trend evidence for a user's nutrition calibration window.

    This service is read-only. It summarizes logged intake, logging completeness,
    bodyweight trend, goal/profile context, and training context. It does not
    calibrate, mutate, or recommend nutrition targets.
    """

    end = _parse_date(end_date) if end_date else date.today()
    if start_date:
        start = _parse_date(start_date)
        if start > end:
            raise ValueError("start_date must be on or before end_date")
        window_days = (end - start).days + 1
    else:
        if window_days <= 0:
            raise ValueError("window_days must be positive")
        start = end - timedelta(days=window_days - 1)

    target_context = _build_target_context(
        user_id=user_id,
        start_date=start,
        end_date=end,
    )
    trend_days = build_nutrition_trend_days(
        user_id=user_id,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        target_context=target_context,
    )
    complete_logging_day_count = sum(
        1 for day in trend_days if day.logging_completeness in _COMPLETE_LOGGING_VALUES
    )
    partial_logging_day_count = sum(
        1 for day in trend_days if day.logging_completeness in _PARTIAL_LOGGING_VALUES
    )
    no_log_day_count = sum(
        1
        for day in trend_days
        if day.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS
    )
    logged_day_count = complete_logging_day_count + partial_logging_day_count
    observations = build_nutrition_observations(
        trend_days,
        target_context=target_context,
    )

    intake_summary = summarize_nutrition_intake_trend(trend_days)
    bodyweight_summary = summarize_bodyweight_trend(
        user_id=user_id,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )
    goal_context_available = _goal_context_available(user_id)
    training_context_available = _training_context_available(
        user_id=user_id,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )
    readiness = assess_nutrition_calibration_readiness(
        window_days=window_days,
        intake_trend_summary=intake_summary,
        bodyweight_trend_summary=bodyweight_summary,
        goal_context_available=goal_context_available,
        training_context_available=training_context_available,
    )
    confidence = _window_confidence(readiness)
    reason_codes = _window_reason_codes(
        window_days=window_days,
        intake_summary=intake_summary,
        bodyweight_summary=bodyweight_summary,
        readiness=readiness,
        goal_context_available=goal_context_available,
        training_context_available=training_context_available,
    )
    limitations = _window_limitations(
        intake_summary=intake_summary,
        bodyweight_summary=bodyweight_summary,
        readiness=readiness,
        goal_context_available=goal_context_available,
        training_context_available=training_context_available,
    )

    return NutritionTrendWindow(
        user_id=user_id,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        window_days=window_days,
        logged_day_count=logged_day_count,
        complete_logging_day_count=complete_logging_day_count,
        partial_logging_day_count=partial_logging_day_count,
        no_log_day_count=no_log_day_count,
        intake_trend_summary=intake_summary,
        bodyweight_trend_summary=bodyweight_summary,
        calibration_readiness=readiness,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
        trend_days=trend_days,
        observations=observations,
        target_context=target_context,
        metadata=NutritionTrendWindowMetadata(
            generated_at=datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            inputs_used=_metadata_inputs_used(
                logged_day_count=logged_day_count,
                bodyweight_summary=bodyweight_summary,
                goal_context_available=goal_context_available,
                training_context_available=training_context_available,
                target_context_available=target_context.available,
            ),
            reason_codes=["trend_window_created"],
            limitations=(
                ["Trend evidence is read-only and does not mutate nutrition targets."]
                if confidence in {"Limited", "Low"}
                else []
            ),
        ),
    )


def build_nutrition_trend_days(
    *,
    user_id: int,
    start_date: str,
    end_date: str,
    target_context: NutritionTargetContext | None = None,
) -> list[NutritionTrendDay]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("start_date must be on or before end_date")

    bodyweights = _bodyweights_by_date(user_id=user_id, start_date=start, end_date=end)
    training_days = _training_days(user_id=user_id, start_date=start, end_date=end)
    target_context = target_context or NutritionTargetContext(
        reason_codes=["target_context_not_evaluated"],
        limitations=["Target context was not requested for these daily states."],
    )
    days: list[NutritionTrendDay] = []

    for current in _inclusive_dates(start, end):
        target_date = current.isoformat()
        actuals = build_nutrition_actuals(user_id, target_date)
        logging_summary = _logging_summary_from_actuals(actuals)
        target_applies = _target_context_applies(target_context, target_date)
        plausibility, plausibility_threshold = _intake_plausibility(
            logged_calories=actuals.logged_calories,
            logging_present=actuals.entry_count > 0,
            calorie_target_min=(
                target_context.calorie_target_min if target_applies else None
            ),
        )
        logging_completeness = logging_summary.logging_completeness
        confidence = logging_summary.confidence
        reason_codes = _unique(
            [
                *actuals.reason_codes,
                *logging_summary.reason_codes,
                _reason_code_for_logging_completeness(
                    logging_summary.logging_completeness
                ),
            ]
        )
        limitations = list(logging_summary.limitations)
        if (
            logging_completeness in _COMPLETE_LOGGING_VALUES
            and plausibility == INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD
        ):
            logging_completeness = LOGGING_COMPLETENESS_LIKELY_INCOMPLETE
            confidence = "Low"
            reason_codes.extend(
                [
                    "intake_below_complete_day_threshold",
                    "completeness_limited_by_intake_plausibility",
                ]
            )
            limitations.append(
                "Logged calories are below the threshold used to treat this as a complete day."
            )

        if logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
            reason_codes.append("no_log_day")
        elif logging_completeness in _PARTIAL_LOGGING_VALUES:
            reason_codes.append("partial_log_day")
        elif logging_completeness in _COMPLETE_LOGGING_VALUES:
            reason_codes.append("complete_logging_day")

        calorie_status = _target_status(
            actuals.logged_calories,
            target_context.calorie_target_min if target_applies else None,
            target_context.calorie_target_max if target_applies else None,
            trustworthy=logging_completeness in _COMPLETE_LOGGING_VALUES,
        )
        protein_status = _target_status(
            actuals.logged_protein,
            target_context.protein_target_min if target_applies else None,
            target_context.protein_target_max if target_applies else None,
            trustworthy=logging_completeness in _COMPLETE_LOGGING_VALUES,
        )
        if target_applies:
            reason_codes.append("approved_target_context_available")
        else:
            reason_codes.append("target_context_unavailable_for_date")

        evidence_references = [f"nutrition-log-day:{target_date}"]
        if target_date in bodyweights:
            evidence_references.append(f"body-weight-day:{target_date}")
        if target_date in training_days:
            evidence_references.append(f"training-day:{target_date}")

        days.append(
            NutritionTrendDay(
                date=target_date,
                logged_calories=actuals.logged_calories,
                logged_protein=actuals.logged_protein,
                logged_carbohydrate=actuals.logged_carbs,
                logged_fat=actuals.logged_fat,
                logging_completeness=logging_completeness,
                confidence=confidence,
                bodyweight_lb=bodyweights.get(target_date),
                training_day=target_date in training_days,
                logged_entry_count=actuals.entry_count,
                logged_meal_count=actuals.logged_meal_count,
                meal_types=list(actuals.meal_types),
                logging_present=actuals.entry_count > 0,
                intake_plausibility=plausibility,
                plausibility_threshold_calories=plausibility_threshold,
                target_context_available=target_applies,
                calorie_target_min=(
                    target_context.calorie_target_min if target_applies else None
                ),
                calorie_target_max=(
                    target_context.calorie_target_max if target_applies else None
                ),
                protein_target_min=(
                    target_context.protein_target_min if target_applies else None
                ),
                protein_target_max=(
                    target_context.protein_target_max if target_applies else None
                ),
                calorie_target_status=calorie_status,
                protein_target_status=protein_status,
                evidence_references=evidence_references,
                reason_codes=_unique(reason_codes),
                limitations=limitations,
            )
        )

    return days


def summarize_nutrition_intake_trend(
    trend_days: list[NutritionTrendDay],
) -> NutritionIntakeTrendSummary:
    if not trend_days:
        return NutritionIntakeTrendSummary(
            logging_consistency_status=LOGGING_CONSISTENCY_INSUFFICIENT,
            confidence="Limited",
            reason_codes=["logging_quality_insufficient"],
            limitations=["No trend days are available."],
        )

    window_days = len(trend_days)
    complete_logging_day_count = sum(
        1 for day in trend_days if day.logging_completeness in _COMPLETE_LOGGING_VALUES
    )
    logged_day_count = sum(
        1
        for day in trend_days
        if day.logging_completeness != LOGGING_COMPLETENESS_NO_LOGS
    )
    complete_logging_rate = round(complete_logging_day_count / window_days, 3)
    consistency = _logging_consistency_status(
        window_days=window_days,
        logged_day_count=logged_day_count,
        complete_logging_day_count=complete_logging_day_count,
    )
    confidence = _intake_confidence(consistency)
    reason_codes = [
        (
            "logging_quality_usable"
            if consistency in {LOGGING_CONSISTENCY_USABLE, LOGGING_CONSISTENCY_STRONG}
            else "logging_quality_insufficient"
        )
    ]
    limitations: list[str] = []
    if consistency in {
        LOGGING_CONSISTENCY_INSUFFICIENT,
        LOGGING_CONSISTENCY_INCONSISTENT,
    }:
        limitations.append(
            "Logging consistency is not strong enough for nutrition target calibration."
        )

    trustworthy_days = _trustworthy_intake_days(trend_days)
    calorie_hit_rate, protein_hit_rate = _target_hit_rates(trustworthy_days)

    return NutritionIntakeTrendSummary(
        average_calories=_average_logged_value(
            [day.logged_calories for day in trustworthy_days]
        ),
        average_protein_g=_average_logged_value(
            [day.logged_protein for day in trustworthy_days]
        ),
        average_carbohydrate_g=_average_logged_value(
            [day.logged_carbohydrate for day in trustworthy_days]
        ),
        average_fat_g=_average_logged_value(
            [day.logged_fat for day in trustworthy_days]
        ),
        calorie_target_hit_rate=calorie_hit_rate,
        protein_target_hit_rate=protein_hit_rate,
        complete_logging_rate=complete_logging_rate,
        trustworthy_day_count=len(trustworthy_days),
        logging_consistency_status=consistency,
        confidence=confidence,
        reason_codes=reason_codes,
        limitations=limitations,
    )


def summarize_bodyweight_trend(
    *, user_id: int, start_date: str, end_date: str
) -> BodyweightTrendSummary:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    rows = _bodyweight_rows(user_id=user_id, start_date=start, end_date=end)

    if len(rows) < 2:
        return BodyweightTrendSummary(
            trend_direction=BODYWEIGHT_TREND_UNAVAILABLE,
            confidence="Limited",
            reason_codes=["bodyweight_trend_unavailable"],
            limitations=[
                "At least two bodyweight entries are needed for trend direction."
            ],
        )

    first_date, first_weight = rows[0]
    last_date, last_weight = rows[-1]
    days_between = max((last_date - first_date).days, 1)
    weekly_rate = round((last_weight - first_weight) / days_between * 7, 2)
    average_weight = round(sum(weight for _, weight in rows) / len(rows), 1)
    trend_direction = _bodyweight_direction(weekly_rate)
    confidence = _bodyweight_confidence(
        weigh_in_count=len(rows), window_days=(end - start).days + 1
    )

    return BodyweightTrendSummary(
        weigh_in_count=len(rows),
        start_weight_lb=round(first_weight, 1),
        end_weight_lb=round(last_weight, 1),
        average_weight_lb=average_weight,
        trend_direction=trend_direction,
        weekly_rate_lb=weekly_rate,
        confidence=confidence,
        reason_codes=["bodyweight_trend_available"],
        limitations=(
            ["Bodyweight trend is available but based on limited weigh-ins."]
            if confidence == "Low"
            else []
        ),
    )


def assess_nutrition_calibration_readiness(
    *,
    window_days: int,
    intake_trend_summary: NutritionIntakeTrendSummary,
    bodyweight_trend_summary: BodyweightTrendSummary,
    goal_context_available: bool,
    training_context_available: bool,
) -> NutritionCalibrationReadiness:
    minimum_window_met = window_days >= MINIMUM_TREND_WINDOW_DAYS
    preferred_window_met = window_days >= PREFERRED_TREND_WINDOW_DAYS
    logging_quality_met = intake_trend_summary.logging_consistency_status in {
        LOGGING_CONSISTENCY_USABLE,
        LOGGING_CONSISTENCY_STRONG,
    }
    bodyweight_trend_available = (
        bodyweight_trend_summary.trend_direction != BODYWEIGHT_TREND_UNAVAILABLE
    )

    reason_codes: list[str] = []
    limitations: list[str] = []

    if minimum_window_met:
        reason_codes.append("minimum_window_met")
    else:
        reason_codes.append("minimum_window_not_met")
        limitations.append("At least 14 days are needed for early trend context.")

    if preferred_window_met:
        reason_codes.append("preferred_window_met")

    if logging_quality_met:
        reason_codes.append("logging_quality_usable")
    else:
        reason_codes.append("logging_quality_insufficient")
        limitations.append(
            "Logging quality is not sufficient for calibration readiness."
        )

    if bodyweight_trend_available:
        reason_codes.append("bodyweight_trend_available")
    else:
        reason_codes.append("bodyweight_trend_unavailable")
        limitations.append("Bodyweight trend data is unavailable.")

    if goal_context_available:
        reason_codes.append("goal_context_available")
    else:
        limitations.append("Goal context is unavailable.")

    if training_context_available:
        reason_codes.append("training_context_available")
    else:
        limitations.append("Training context is unavailable.")

    if not (
        minimum_window_met
        and logging_quality_met
        and bodyweight_trend_available
        and goal_context_available
    ):
        readiness_level = CALIBRATION_READINESS_NOT_READY
        calibration_allowed = False
        reason_codes.append("calibration_not_ready")
    elif preferred_window_met and (
        intake_trend_summary.logging_consistency_status == LOGGING_CONSISTENCY_STRONG
    ):
        readiness_level = CALIBRATION_READINESS_STRONG
        calibration_allowed = True
        reason_codes.append("calibration_strong")
    elif preferred_window_met:
        readiness_level = CALIBRATION_READINESS_USABLE
        calibration_allowed = True
        reason_codes.append("calibration_usable")
    else:
        readiness_level = CALIBRATION_READINESS_EARLY_SIGNAL
        calibration_allowed = False
        reason_codes.append("calibration_early_signal")
        limitations.append(
            "Trend evidence is early; 28 days are preferred before calibration."
        )

    return NutritionCalibrationReadiness(
        calibration_allowed=calibration_allowed,
        readiness_level=readiness_level,
        minimum_window_met=minimum_window_met,
        preferred_window_met=preferred_window_met,
        logging_quality_met=logging_quality_met,
        bodyweight_trend_available=bodyweight_trend_available,
        goal_context_available=goal_context_available,
        training_context_available=training_context_available,
        reason_codes=_unique(reason_codes),
        limitations=_unique(limitations),
    )


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format") from exc


def _inclusive_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _reason_code_for_logging_completeness(logging_completeness: str) -> str:
    if logging_completeness == LOGGING_COMPLETENESS_NO_LOGS:
        return "no_nutrition_logs_today"
    if logging_completeness in _COMPLETE_LOGGING_VALUES:
        return "complete_enough_for_trend"
    return "partial_or_incomplete_logging"


def _average_logged_value(values: list[float | None]) -> float | None:
    present_values = [float(value) for value in values if value is not None]
    if not present_values:
        return None
    return round(sum(present_values) / len(present_values), 1)


def _trustworthy_intake_days(
    trend_days: list[NutritionTrendDay],
) -> list[NutritionTrendDay]:
    return [
        day
        for day in trend_days
        if day.logging_completeness in _COMPLETE_LOGGING_VALUES
        and day.intake_plausibility != INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD
    ]


def _intake_plausibility(
    *,
    logged_calories: float | None,
    logging_present: bool,
    calorie_target_min: float | None,
) -> tuple[str, float | None]:
    if not logging_present or logged_calories is None:
        return INTAKE_PLAUSIBILITY_UNKNOWN, None
    threshold = DEFAULT_COMPLETE_DAY_CALORIE_FLOOR
    if calorie_target_min is not None:
        threshold = max(threshold, float(calorie_target_min) * 0.5)
    threshold = round(threshold, 1)
    if float(logged_calories) < threshold:
        return INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD, threshold
    return INTAKE_PLAUSIBILITY_NOT_FLAGGED, threshold


def _target_status(
    actual: float | None,
    target_min: float | None,
    target_max: float | None,
    *,
    trustworthy: bool,
) -> str:
    if not trustworthy or actual is None or target_min is None or target_max is None:
        return "unavailable"
    if actual < target_min:
        return "below_target"
    if actual > target_max:
        return "above_target"
    return "near_target"


def _logging_consistency_status(
    *, window_days: int, logged_day_count: int, complete_logging_day_count: int
) -> str:
    if window_days <= 0 or logged_day_count == 0:
        return LOGGING_CONSISTENCY_INSUFFICIENT

    complete_rate = complete_logging_day_count / window_days
    logged_rate = logged_day_count / window_days

    if complete_rate >= 0.75 and logged_rate >= 0.85:
        return LOGGING_CONSISTENCY_STRONG
    if complete_rate >= 0.5 and logged_rate >= 0.65:
        return LOGGING_CONSISTENCY_USABLE
    if logged_rate >= 0.35:
        return LOGGING_CONSISTENCY_INCONSISTENT
    return LOGGING_CONSISTENCY_INSUFFICIENT


def _intake_confidence(logging_consistency_status: str) -> str:
    if logging_consistency_status == LOGGING_CONSISTENCY_STRONG:
        return "High"
    if logging_consistency_status == LOGGING_CONSISTENCY_USABLE:
        return "Moderate"
    if logging_consistency_status == LOGGING_CONSISTENCY_INCONSISTENT:
        return "Low"
    return "Limited"


def _target_hit_rates(
    trend_days: list[NutritionTrendDay],
) -> tuple[float | None, float | None]:
    calorie_days = [
        day for day in trend_days if day.calorie_target_status != "unavailable"
    ]
    protein_days = [
        day for day in trend_days if day.protein_target_status != "unavailable"
    ]
    calorie_rate = (
        round(
            sum(day.calorie_target_status == "near_target" for day in calorie_days)
            / len(calorie_days),
            3,
        )
        if calorie_days
        else None
    )
    protein_rate = (
        round(
            sum(day.protein_target_status == "near_target" for day in protein_days)
            / len(protein_days),
            3,
        )
        if protein_days
        else None
    )
    return calorie_rate, protein_rate


def _build_target_context(
    *, user_id: int, start_date: date, end_date: date
) -> NutritionTargetContext:
    latest_observation = _latest_user_observation_date(user_id)
    if latest_observation is not None and end_date < latest_observation:
        return NutritionTargetContext(
            reason_codes=["historical_target_context_unavailable"],
            limitations=[
                "Current profile-derived targets are not applied to an earlier historical window."
            ],
        )

    try:
        health_state = build_user_health_state(user_id)
        targets, _approved = build_formula_derived_nutrition_targets(
            health_state,
            calculation_date=end_date.isoformat(),
        )
    except (KeyError, TypeError, ValueError):
        return NutritionTargetContext(
            reason_codes=["approved_target_context_unavailable"],
            limitations=["Approved nutrition target context is unavailable."],
        )

    target_values = {
        "calorie_target_min": (
            targets.calorie_target_min if targets.allow_calorie_targets else None
        ),
        "calorie_target_max": (
            targets.calorie_target_max if targets.allow_calorie_targets else None
        ),
        "protein_target_min": (
            targets.protein_grams_min if targets.allow_protein_targets else None
        ),
        "protein_target_max": (
            targets.protein_grams_max if targets.allow_protein_targets else None
        ),
    }
    has_range = any(value is not None for value in target_values.values())
    if targets.confidence not in {"Moderate", "High"} or not has_range:
        return NutritionTargetContext(
            confidence=targets.confidence,
            reason_codes=["approved_target_context_unavailable"],
            limitations=[
                "Approved nutrition targets do not have enough confidence for longitudinal comparison."
            ],
        )

    effective_start = max(
        start_date,
        end_date - timedelta(days=CURRENT_TARGET_CONTEXT_DAYS - 1),
    )
    return NutritionTargetContext(
        available=True,
        effective_start_date=effective_start.isoformat(),
        effective_end_date=end_date.isoformat(),
        confidence=targets.confidence,
        source="nutrition_target_formula_service:current_profile",
        reason_codes=["approved_current_target_context_available"],
        limitations=[
            "Current profile-derived targets apply only to the latest 28 days in this window."
        ],
        **target_values,
    )


def _target_context_applies(
    target_context: NutritionTargetContext, target_date: str
) -> bool:
    return bool(
        target_context.available
        and target_context.effective_start_date is not None
        and target_context.effective_end_date is not None
        and target_context.effective_start_date
        <= target_date
        <= target_context.effective_end_date
    )


def _latest_user_observation_date(user_id: int) -> date | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT MAX(observed_date) AS observed_date
        FROM (
            SELECT entry_date AS observed_date
            FROM food_entries
            WHERE user_id = ?
            UNION ALL
            SELECT checkin_date AS observed_date
            FROM daily_checkins
            WHERE user_id = ?
            UNION ALL
            SELECT workout_date AS observed_date
            FROM workout_sessions
            WHERE user_id = ?
            UNION ALL
            SELECT substr(completed_at, 1, 10) AS observed_date
            FROM workout_execution_sessions
            WHERE user_id = ? AND completed_at IS NOT NULL
        )
        """,
        (user_id, user_id, user_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    value = row["observed_date"] if row is not None else None
    return _parse_date(str(value)) if value else None


def _bodyweight_rows(
    *, user_id: int, start_date: date, end_date: date
) -> list[tuple[date, float]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT checkin_date, body_weight
        FROM daily_checkins
        WHERE user_id = ?
          AND checkin_date BETWEEN ? AND ?
          AND body_weight IS NOT NULL
        ORDER BY checkin_date, id
        """,
        (user_id, start_date.isoformat(), end_date.isoformat()),
    )
    rows = cursor.fetchall()
    conn.close()

    latest_by_date: dict[str, float] = {}
    for row in rows:
        latest_by_date[str(row["checkin_date"])] = float(row["body_weight"])

    return [
        (_parse_date(day), weight) for day, weight in sorted(latest_by_date.items())
    ]


def _bodyweights_by_date(
    *, user_id: int, start_date: date, end_date: date
) -> dict[str, float]:
    return {
        day.isoformat(): round(weight, 1)
        for day, weight in _bodyweight_rows(
            user_id=user_id, start_date=start_date, end_date=end_date
        )
    }


def _bodyweight_direction(weekly_rate: float) -> str:
    if weekly_rate <= -STABLE_WEEKLY_WEIGHT_RATE_LB:
        return BODYWEIGHT_TREND_DECREASING
    if weekly_rate >= STABLE_WEEKLY_WEIGHT_RATE_LB:
        return BODYWEIGHT_TREND_INCREASING
    return BODYWEIGHT_TREND_STABLE


def _bodyweight_confidence(*, weigh_in_count: int, window_days: int) -> str:
    if weigh_in_count >= 10 and window_days >= PREFERRED_TREND_WINDOW_DAYS:
        return "Moderate"
    if weigh_in_count >= 4:
        return "Low"
    return "Limited"


def _training_days(*, user_id: int, start_date: date, end_date: date) -> set[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT workout_date AS training_date
        FROM workout_sessions
        WHERE user_id = ?
          AND workout_date BETWEEN ? AND ?
        UNION
        SELECT substr(completed_at, 1, 10) AS training_date
        FROM workout_execution_sessions
        WHERE user_id = ?
          AND completed_at IS NOT NULL
          AND substr(completed_at, 1, 10) BETWEEN ? AND ?
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat(),
            user_id,
            start_date.isoformat(),
            end_date.isoformat(),
        ),
    )
    rows = cursor.fetchall()
    conn.close()
    return {str(row["training_date"]) for row in rows if row["training_date"]}


def _training_context_available(
    *, user_id: int, start_date: str, end_date: str
) -> bool:
    return bool(
        _training_days(
            user_id=user_id,
            start_date=_parse_date(start_date),
            end_date=_parse_date(end_date),
        )
    )


def _goal_context_available(user_id: int) -> bool:
    profile = get_user_profile(user_id)
    if not profile:
        return False
    primary_goal = _row_value(profile, "primary_goal")
    activity_level = _row_value(profile, "activity_level")
    return bool(primary_goal and activity_level)


def _row_value(row: Any, key: str) -> Any:
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _window_confidence(readiness: NutritionCalibrationReadiness) -> str:
    if readiness.readiness_level == CALIBRATION_READINESS_STRONG:
        return "High"
    if readiness.readiness_level == CALIBRATION_READINESS_USABLE:
        return "Moderate"
    if readiness.readiness_level == CALIBRATION_READINESS_EARLY_SIGNAL:
        return "Low"
    return "Limited"


def _window_reason_codes(
    *,
    window_days: int,
    intake_summary: NutritionIntakeTrendSummary,
    bodyweight_summary: BodyweightTrendSummary,
    readiness: NutritionCalibrationReadiness,
    goal_context_available: bool,
    training_context_available: bool,
) -> list[str]:
    reason_codes = ["trend_window_created"]
    reason_codes.append(
        "preferred_window_met"
        if window_days >= PREFERRED_TREND_WINDOW_DAYS
        else (
            "minimum_window_met"
            if window_days >= MINIMUM_TREND_WINDOW_DAYS
            else "minimum_window_not_met"
        )
    )
    reason_codes.extend(intake_summary.reason_codes)
    reason_codes.extend(bodyweight_summary.reason_codes)
    reason_codes.extend(readiness.reason_codes)
    if goal_context_available:
        reason_codes.append("goal_context_available")
    if training_context_available:
        reason_codes.append("training_context_available")
    return _unique(reason_codes)


def _window_limitations(
    *,
    intake_summary: NutritionIntakeTrendSummary,
    bodyweight_summary: BodyweightTrendSummary,
    readiness: NutritionCalibrationReadiness,
    goal_context_available: bool,
    training_context_available: bool,
) -> list[str]:
    limitations = [
        *intake_summary.limitations,
        *bodyweight_summary.limitations,
        *readiness.limitations,
    ]
    if not goal_context_available:
        limitations.append("Goal/profile context is incomplete.")
    if not training_context_available:
        limitations.append("Training context is not available for this window.")
    return _unique(limitations)


def _metadata_inputs_used(
    *,
    logged_day_count: int,
    bodyweight_summary: BodyweightTrendSummary,
    goal_context_available: bool,
    training_context_available: bool,
    target_context_available: bool,
) -> list[str]:
    inputs = ["logged_nutrition_actuals", "logging_completeness"]
    if logged_day_count == 0:
        inputs.append("no_logged_intake")
    if bodyweight_summary.trend_direction != BODYWEIGHT_TREND_UNAVAILABLE:
        inputs.append("bodyweight_trend")
    if goal_context_available:
        inputs.append("goal_context")
    if training_context_available:
        inputs.append("training_context")
    if target_context_available:
        inputs.append("approved_current_nutrition_targets")
    return inputs
