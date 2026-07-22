from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from models.nutrition_trend_models import (
    INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD,
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
    NutritionObservation,
    NutritionTargetContext,
    NutritionTrendDay,
)

MIN_INTAKE_DAYS_PER_GROUP = 4
MIN_VARIABILITY_DAYS = 5
MIN_BODYWEIGHT_DAYS_PER_PERIOD = 2

_TRUSTWORTHY_COMPLETENESS = {
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_REASONABLY_COMPLETE,
}


def build_nutrition_observations(
    trend_days: list[NutritionTrendDay],
    *,
    target_context: NutritionTargetContext,
) -> list[NutritionObservation]:
    """Build bounded neutral measurements from normalized daily nutrition states."""

    days = sorted(trend_days, key=lambda item: item.date)
    if not days:
        return []

    observations = [_logging_coverage_observation(days)]
    if len(days) >= 28:
        prior = days[-28:-14]
        recent = days[-14:]
        observations.append(_logging_change_observation(recent, prior))
        recent_prior = _intake_comparison_observation(
            recent,
            prior,
            observation_type="recent_vs_previous",
            metric="calories_and_protein",
        )
        if recent_prior is not None:
            observations.append(recent_prior)
        aligned = _nutrition_bodyweight_alignment(recent, prior)
        if aligned is not None:
            observations.append(aligned)

    variability = _variability_observation(days)
    if variability is not None:
        observations.append(variability)

    target_hits = _target_hit_observation(days, target_context)
    if target_hits is not None:
        observations.append(target_hits)

    weekday_days = [day for day in days if _weekday(day) < 5]
    weekend_days = [day for day in days if _weekday(day) >= 5]
    if len(weekday_days) >= 5 and len(weekend_days) >= 2:
        observations.append(
            _group_logging_observation(
                weekday_days,
                weekend_days,
                observation_type="weekday_vs_weekend_logging",
                current_label="weekday",
                comparison_label="weekend",
            )
        )
        weekday_intake = _group_intake_observation(
            weekday_days,
            weekend_days,
            observation_type="weekday_vs_weekend_intake",
            current_label="weekday",
            comparison_label="weekend",
        )
        if weekday_intake is not None:
            observations.append(weekday_intake)

    training_days = [day for day in days if day.training_day]
    rest_days = [day for day in days if not day.training_day]
    if len(training_days) >= 3 and len(rest_days) >= 3:
        observations.append(
            _group_logging_observation(
                training_days,
                rest_days,
                observation_type="training_day_vs_rest_day_logging",
                current_label="training_day",
                comparison_label="rest_day",
            )
        )
        training_intake = _group_intake_observation(
            training_days,
            rest_days,
            observation_type="training_day_vs_rest_day_intake",
            current_label="training_day",
            comparison_label="rest_day",
        )
        if training_intake is not None:
            observations.append(training_intake)

    return observations


def _logging_coverage_observation(
    days: list[NutritionTrendDay],
) -> NutritionObservation:
    stats = _logging_stats(days)
    return _observation(
        days,
        observation_type="logging_coverage",
        metric="logging_presence_completeness_plausibility",
        current_value=stats,
        current_observation_count=int(stats["logged_day_count"]),
        coverage={"expected_day_count": len(days), **stats},
        data_quality=_data_quality(days),
        reason_codes=["calendar_days_classified"],
    )


def _logging_change_observation(
    recent: list[NutritionTrendDay], prior: list[NutritionTrendDay]
) -> NutritionObservation:
    recent_stats = _logging_stats(recent)
    prior_stats = _logging_stats(prior)
    return _observation(
        recent,
        comparison_days=prior,
        observation_type="logging_coverage_change",
        metric="logging_presence_completeness_plausibility",
        current_value=recent_stats,
        comparison_value=prior_stats,
        current_observation_count=int(recent_stats["logged_day_count"]),
        comparison_observation_count=int(prior_stats["logged_day_count"]),
        coverage={
            "current_expected_day_count": len(recent),
            "comparison_expected_day_count": len(prior),
        },
        data_quality={
            "current": _data_quality(recent),
            "comparison": _data_quality(prior),
        },
        reason_codes=["adjacent_14_day_windows"],
    )


def _intake_comparison_observation(
    current_days: list[NutritionTrendDay],
    comparison_days: list[NutritionTrendDay],
    *,
    observation_type: str,
    metric: str,
) -> NutritionObservation | None:
    current_usable = _usable_intake_days(current_days)
    comparison_usable = _usable_intake_days(comparison_days)
    if (
        len(current_usable) < MIN_INTAKE_DAYS_PER_GROUP
        or len(comparison_usable) < MIN_INTAKE_DAYS_PER_GROUP
    ):
        return None
    return _observation(
        current_days,
        comparison_days=comparison_days,
        observation_type=observation_type,
        metric=metric,
        current_value=_intake_averages(current_usable),
        comparison_value=_intake_averages(comparison_usable),
        current_observation_count=len(current_usable),
        comparison_observation_count=len(comparison_usable),
        unit="per_day",
        coverage={
            "current_expected_day_count": len(current_days),
            "comparison_expected_day_count": len(comparison_days),
        },
        data_quality={
            "eligibility_rule": "complete_and_not_below_plausibility_threshold",
            "current": _data_quality(current_days),
            "comparison": _data_quality(comparison_days),
        },
        reason_codes=["trustworthy_days_only"],
    )


def _variability_observation(
    days: list[NutritionTrendDay],
) -> NutritionObservation | None:
    usable = _usable_intake_days(days)
    if len(usable) < MIN_VARIABILITY_DAYS:
        return None
    calorie_values = [float(day.logged_calories) for day in usable]
    protein_values = [float(day.logged_protein) for day in usable]
    return _observation(
        days,
        observation_type="intake_variability",
        metric="calories_and_protein",
        current_value={
            "calories": _variability(calorie_values),
            "protein_g": _variability(protein_values),
        },
        current_observation_count=len(usable),
        unit="per_day",
        coverage={
            "expected_day_count": len(days),
            "eligible_day_count": len(usable),
        },
        data_quality=_data_quality(days),
        reason_codes=["population_standard_deviation", "trustworthy_days_only"],
    )


def _target_hit_observation(
    days: list[NutritionTrendDay], target_context: NutritionTargetContext
) -> NutritionObservation | None:
    calorie_days = [day for day in days if day.calorie_target_status != "unavailable"]
    protein_days = [day for day in days if day.protein_target_status != "unavailable"]
    if (
        len(calorie_days) < MIN_INTAKE_DAYS_PER_GROUP
        and len(protein_days) < MIN_INTAKE_DAYS_PER_GROUP
    ):
        return None
    current_value: dict[str, Any] = {}
    if len(calorie_days) >= MIN_INTAKE_DAYS_PER_GROUP:
        current_value["calorie_target_hit_rate"] = _hit_rate(
            calorie_days, "calorie_target_status"
        )
        current_value["calorie_observation_count"] = len(calorie_days)
    if len(protein_days) >= MIN_INTAKE_DAYS_PER_GROUP:
        current_value["protein_target_hit_rate"] = _hit_rate(
            protein_days, "protein_target_status"
        )
        current_value["protein_observation_count"] = len(protein_days)
    return _observation(
        days,
        observation_type="target_hit_frequency",
        metric="calories_and_protein",
        current_value=current_value,
        current_observation_count=max(len(calorie_days), len(protein_days)),
        unit="rate",
        coverage={
            "target_eligible_day_count": max(len(calorie_days), len(protein_days))
        },
        data_quality=_data_quality(days),
        target_context=target_context.to_dict(),
        reason_codes=["approved_target_context", "trustworthy_days_only"],
    )


def _group_logging_observation(
    current_days: list[NutritionTrendDay],
    comparison_days: list[NutritionTrendDay],
    *,
    observation_type: str,
    current_label: str,
    comparison_label: str,
) -> NutritionObservation:
    current_stats = _logging_stats(current_days)
    comparison_stats = _logging_stats(comparison_days)
    return _observation(
        current_days,
        comparison_days=comparison_days,
        observation_type=observation_type,
        metric="logging_presence_completeness_plausibility",
        current_value={"group": current_label, **current_stats},
        comparison_value={"group": comparison_label, **comparison_stats},
        current_observation_count=int(current_stats["logged_day_count"]),
        comparison_observation_count=int(comparison_stats["logged_day_count"]),
        coverage={
            "current_expected_day_count": len(current_days),
            "comparison_expected_day_count": len(comparison_days),
        },
        data_quality={
            "current": _data_quality(current_days),
            "comparison": _data_quality(comparison_days),
        },
        reason_codes=["calendar_group_comparison"],
    )


def _group_intake_observation(
    current_days: list[NutritionTrendDay],
    comparison_days: list[NutritionTrendDay],
    *,
    observation_type: str,
    current_label: str,
    comparison_label: str,
) -> NutritionObservation | None:
    observation = _intake_comparison_observation(
        current_days,
        comparison_days,
        observation_type=observation_type,
        metric="calories_and_protein",
    )
    if observation is None:
        return None
    observation.current_value = {"group": current_label, **observation.current_value}
    observation.comparison_value = {
        "group": comparison_label,
        **observation.comparison_value,
    }
    return observation


def _nutrition_bodyweight_alignment(
    recent: list[NutritionTrendDay], prior: list[NutritionTrendDay]
) -> NutritionObservation | None:
    recent_intake = _usable_intake_days(recent)
    prior_intake = _usable_intake_days(prior)
    recent_weights = [day for day in recent if day.bodyweight_lb is not None]
    prior_weights = [day for day in prior if day.bodyweight_lb is not None]
    if (
        len(recent_intake) < MIN_INTAKE_DAYS_PER_GROUP
        or len(prior_intake) < MIN_INTAKE_DAYS_PER_GROUP
        or len(recent_weights) < MIN_BODYWEIGHT_DAYS_PER_PERIOD
        or len(prior_weights) < MIN_BODYWEIGHT_DAYS_PER_PERIOD
    ):
        return None
    return _observation(
        recent,
        comparison_days=prior,
        observation_type="nutrition_bodyweight_period_alignment",
        metric="calories_protein_and_bodyweight",
        current_value={
            **_intake_averages(recent_intake),
            **_weight_measurements(recent_weights),
        },
        comparison_value={
            **_intake_averages(prior_intake),
            **_weight_measurements(prior_weights),
        },
        current_observation_count=len(recent_intake),
        comparison_observation_count=len(prior_intake),
        unit="period_measurements",
        coverage={
            "current_nutrition_day_count": len(recent_intake),
            "comparison_nutrition_day_count": len(prior_intake),
            "current_weigh_in_count": len(recent_weights),
            "comparison_weigh_in_count": len(prior_weights),
        },
        data_quality={
            "current": _data_quality(recent),
            "comparison": _data_quality(prior),
        },
        reason_codes=["aligned_adjacent_14_day_periods", "no_causal_interpretation"],
    )


def _observation(
    current_days: list[NutritionTrendDay],
    *,
    observation_type: str,
    metric: str,
    current_value: Any,
    current_observation_count: int,
    comparison_days: list[NutritionTrendDay] | None = None,
    comparison_value: Any = None,
    comparison_observation_count: int = 0,
    unit: str | None = None,
    coverage: dict[str, Any] | None = None,
    data_quality: dict[str, Any] | None = None,
    target_context: dict[str, Any] | None = None,
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> NutritionObservation:
    comparison_days = comparison_days or []
    return NutritionObservation(
        observation_id=(
            f"nutrition:{observation_type}:{metric}:"
            f"{current_days[0].date}:{current_days[-1].date}"
        ),
        observation_type=observation_type,
        metric=metric,
        current_start_date=current_days[0].date,
        current_end_date=current_days[-1].date,
        current_value=current_value,
        current_observation_count=current_observation_count,
        comparison_start_date=(comparison_days[0].date if comparison_days else None),
        comparison_end_date=(comparison_days[-1].date if comparison_days else None),
        comparison_value=comparison_value,
        comparison_observation_count=comparison_observation_count,
        unit=unit,
        coverage=dict(coverage or {}),
        data_quality=dict(data_quality or {}),
        target_context=dict(target_context or {}),
        evidence_references=_evidence_references([*current_days, *comparison_days]),
        reason_codes=list(reason_codes or []),
        limitations=list(limitations or []),
    )


def _logging_stats(days: list[NutritionTrendDay]) -> dict[str, int | float]:
    logged = sum(
        day.logging_completeness != LOGGING_COMPLETENESS_NO_LOGS for day in days
    )
    complete = sum(
        day.logging_completeness in _TRUSTWORTHY_COMPLETENESS for day in days
    )
    below_threshold = sum(
        day.intake_plausibility == INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD
        for day in days
    )
    return {
        "logged_day_count": logged,
        "complete_day_count": complete,
        "partial_or_incomplete_day_count": logged - complete,
        "no_log_day_count": len(days) - logged,
        "below_plausibility_threshold_day_count": below_threshold,
        "logging_presence_rate": round(logged / len(days), 3),
        "complete_logging_rate": round(complete / len(days), 3),
    }


def _data_quality(days: list[NutritionTrendDay]) -> dict[str, Any]:
    usable = _usable_intake_days(days)
    return {
        "trustworthy_intake_day_count": len(usable),
        "incomplete_or_missing_day_count": len(days) - len(usable),
        "below_plausibility_threshold_day_count": sum(
            day.intake_plausibility == INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD
            for day in days
        ),
        "eligibility_rule": "complete_and_not_below_plausibility_threshold",
    }


def _usable_intake_days(days: list[NutritionTrendDay]) -> list[NutritionTrendDay]:
    return [
        day
        for day in days
        if day.logging_completeness in _TRUSTWORTHY_COMPLETENESS
        and day.intake_plausibility != INTAKE_PLAUSIBILITY_BELOW_COMPLETE_DAY_THRESHOLD
        and day.logged_calories is not None
        and day.logged_protein is not None
    ]


def _intake_averages(days: list[NutritionTrendDay]) -> dict[str, float]:
    return {
        "average_calories": round(mean(float(day.logged_calories) for day in days), 1),
        "average_protein_g": round(mean(float(day.logged_protein) for day in days), 1),
    }


def _variability(values: list[float]) -> dict[str, float]:
    average = mean(values)
    standard_deviation = pstdev(values)
    return {
        "mean": round(average, 1),
        "standard_deviation": round(standard_deviation, 1),
        "coefficient_of_variation": round(standard_deviation / average, 3)
        if average
        else 0.0,
    }


def _weight_measurements(days: list[NutritionTrendDay]) -> dict[str, float | int]:
    values = [float(day.bodyweight_lb) for day in days]
    return {
        "weigh_in_count": len(values),
        "start_weight_lb": round(values[0], 1),
        "end_weight_lb": round(values[-1], 1),
        "average_weight_lb": round(mean(values), 1),
    }


def _hit_rate(days: list[NutritionTrendDay], attribute: str) -> float:
    return round(
        sum(getattr(day, attribute) == "near_target" for day in days) / len(days), 3
    )


def _weekday(day: NutritionTrendDay) -> int:
    from datetime import date

    return date.fromisoformat(day.date).weekday()


def _evidence_references(days: list[NutritionTrendDay]) -> list[str]:
    references: list[str] = []
    for day in days:
        references.extend(day.evidence_references or [f"nutrition-log-day:{day.date}"])
    return list(dict.fromkeys(references))[:80]
