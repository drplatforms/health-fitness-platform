from __future__ import annotations

from datetime import date, timedelta

from models.nutrition_trend_models import (
    INTAKE_PLAUSIBILITY_NOT_FLAGGED,
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_NO_LOGS,
    NutritionTargetContext,
    NutritionTrendDay,
)
from services.nutrition_intelligence_service import build_nutrition_observations


def _day(
    target_date: date,
    *,
    calories: float | None,
    protein: float | None,
    training: bool = False,
    weight: float | None = None,
    target_status: str = "unavailable",
) -> NutritionTrendDay:
    logged = calories is not None or protein is not None
    return NutritionTrendDay(
        date=target_date.isoformat(),
        logged_calories=calories,
        logged_protein=protein,
        logged_carbohydrate=(250.0 if logged else None),
        logged_fat=(70.0 if logged else None),
        logging_completeness=(
            LOGGING_COMPLETENESS_COMPLETE_ENOUGH
            if logged
            else LOGGING_COMPLETENESS_NO_LOGS
        ),
        confidence="High" if logged else "Limited",
        bodyweight_lb=weight,
        training_day=training,
        logged_entry_count=6 if logged else 0,
        logged_meal_count=4 if logged else 0,
        meal_types=(["breakfast", "lunch", "dinner", "snack"] if logged else []),
        logging_present=logged,
        intake_plausibility=(INTAKE_PLAUSIBILITY_NOT_FLAGGED if logged else "unknown"),
        plausibility_threshold_calories=1000.0 if logged else None,
        target_context_available=target_status != "unavailable",
        calorie_target_min=2000.0 if target_status != "unavailable" else None,
        calorie_target_max=2400.0 if target_status != "unavailable" else None,
        protein_target_min=140.0 if target_status != "unavailable" else None,
        protein_target_max=175.0 if target_status != "unavailable" else None,
        calorie_target_status=target_status,
        protein_target_status=target_status,
        evidence_references=[f"nutrition-log-day:{target_date.isoformat()}"],
        reason_codes=["test_daily_state"],
    )


def _rich_days() -> list[NutritionTrendDay]:
    start = date(2026, 5, 18)
    days: list[NutritionTrendDay] = []
    for index in range(56):
        current = start + timedelta(days=index)
        weekday = current.weekday() < 5
        training = current.weekday() in {0, 2, 4}
        recent_delta = 180 if index >= 42 else 0
        calories = 1900 + (180 if weekday else 0) + (120 if training else 0)
        protein = 125 + (15 if weekday else 0) + (20 if training else 0)
        weight = 190.0 - index * 0.04 if index % 3 == 0 else None
        target_status = "near_target" if index % 5 != 0 else "below_target"
        days.append(
            _day(
                current,
                calories=calories + recent_delta,
                protein=protein + (10 if recent_delta else 0),
                training=training,
                weight=weight,
                target_status=target_status,
            )
        )
    return days


def _target_context() -> NutritionTargetContext:
    return NutritionTargetContext(
        available=True,
        effective_start_date="2026-05-18",
        effective_end_date="2026-07-12",
        calorie_target_min=2000,
        calorie_target_max=2400,
        protein_target_min=140,
        protein_target_max=175,
        confidence="High",
        reason_codes=["test_target_context"],
    )


def test_measurements_cover_recent_prior_variability_calendar_training_and_weight() -> (
    None
):
    observations = build_nutrition_observations(
        _rich_days(), target_context=_target_context()
    )
    by_type = {item.observation_type: item for item in observations}

    assert {
        "logging_coverage",
        "logging_coverage_change",
        "recent_vs_previous",
        "intake_variability",
        "target_hit_frequency",
        "weekday_vs_weekend_logging",
        "weekday_vs_weekend_intake",
        "training_day_vs_rest_day_logging",
        "training_day_vs_rest_day_intake",
        "nutrition_bodyweight_period_alignment",
    }.issubset(by_type)

    recent = by_type["recent_vs_previous"]
    assert (
        recent.current_value["average_calories"]
        > recent.comparison_value["average_calories"]
    )
    assert recent.current_observation_count == 14
    assert recent.comparison_observation_count == 14

    weekday = by_type["weekday_vs_weekend_intake"]
    assert weekday.current_value["group"] == "weekday"
    assert (
        weekday.current_value["average_calories"]
        > weekday.comparison_value["average_calories"]
    )

    training = by_type["training_day_vs_rest_day_intake"]
    assert training.current_value["group"] == "training_day"
    assert (
        training.current_value["average_protein_g"]
        > training.comparison_value["average_protein_g"]
    )

    aligned = by_type["nutrition_bodyweight_period_alignment"]
    assert aligned.coverage["current_weigh_in_count"] >= 2
    assert (
        aligned.current_value["end_weight_lb"]
        < aligned.comparison_value["end_weight_lb"]
    )
    assert "no_causal_interpretation" in aligned.reason_codes
    assert all(item.evidence_references for item in observations)


def test_sparse_or_missing_intake_suppresses_unsupported_measurements() -> None:
    start = date(2026, 6, 1)
    days = [
        _day(
            start + timedelta(days=index),
            calories=(2100.0 if index in {5, 20} else None),
            protein=(150.0 if index in {5, 20} else None),
        )
        for index in range(28)
    ]

    observations = build_nutrition_observations(
        days,
        target_context=NutritionTargetContext(
            reason_codes=["target_context_unavailable"]
        ),
    )
    types = {item.observation_type for item in observations}

    assert "logging_coverage" in types
    assert "logging_coverage_change" in types
    assert "recent_vs_previous" not in types
    assert "intake_variability" not in types
    assert "target_hit_frequency" not in types
    assert "weekday_vs_weekend_intake" not in types
    assert "training_day_vs_rest_day_intake" not in types
    assert "nutrition_bodyweight_period_alignment" not in types
    assert all(
        day.logged_calories is None and day.logged_protein is None
        for day in days
        if not day.logging_present
    )


def test_target_hit_frequency_requires_available_statuses_and_enough_days() -> None:
    start = date(2026, 7, 1)
    unavailable_days = [
        _day(start + timedelta(days=index), calories=2200, protein=155)
        for index in range(7)
    ]
    assert "target_hit_frequency" not in {
        item.observation_type
        for item in build_nutrition_observations(
            unavailable_days,
            target_context=NutritionTargetContext(
                reason_codes=["target_context_unavailable"]
            ),
        )
    }

    available_days = [
        _day(
            start + timedelta(days=index),
            calories=2200,
            protein=155,
            target_status="near_target" if index < 5 else "above_target",
        )
        for index in range(7)
    ]
    target_observation = next(
        item
        for item in build_nutrition_observations(
            available_days, target_context=_target_context()
        )
        if item.observation_type == "target_hit_frequency"
    )

    assert target_observation.current_value["calorie_target_hit_rate"] == 0.714
    assert target_observation.current_value["protein_target_hit_rate"] == 0.714
    assert target_observation.target_context["available"] is True
