from __future__ import annotations

from datetime import date, timedelta

import pytest

import database
from models.nutrition_target_models import NutritionTargets
from models.nutrition_target_vs_actual_models import (
    LOGGING_COMPLETENESS_COMPLETE_ENOUGH,
    LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    LOGGING_COMPLETENESS_NO_LOGS,
    LOGGING_COMPLETENESS_PARTIAL_DAY,
    TARGET_STATUS_BELOW,
    TARGET_STATUS_NEAR,
    TARGET_STATUS_UNAVAILABLE,
)
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.nutrition_target_vs_actual_service import (
    build_approved_nutrition_guidance,
    build_nutrition_actuals,
    build_target_vs_actual_nutrition_summary,
    validate_target_vs_actual_nutrition_summary,
)
from services.user_state_service import build_user_health_state


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def _today() -> str:
    return date.today().isoformat()


def _future_date() -> str:
    return (date.today() + timedelta(days=7)).isoformat()


def _limited_targets() -> NutritionTargets:
    return NutritionTargets(
        body_weight_lb=190,
        calorie_target_min=2200,
        calorie_target_max=2500,
        protein_grams_min=140,
        protein_grams_max=180,
        carbohydrate_grams_min=180,
        carbohydrate_grams_max=260,
        fat_grams_min=60,
        fat_grams_max=90,
        confidence="Limited",
        allow_calorie_targets=False,
        allow_protein_targets=True,
        allow_carbohydrate_targets=False,
        allow_fat_targets=False,
        nutrition_display_message="Nutrition targets are limited.",
        reason_codes=["unit_test_limited_targets"],
    )


def _approved_targets(
    *, calories: bool = True, macros: bool = True
) -> NutritionTargets:
    return NutritionTargets(
        body_weight_lb=178,
        calorie_target_min=2200,
        calorie_target_max=2500,
        protein_grams_min=130,
        protein_grams_max=180,
        carbohydrate_grams_min=180,
        carbohydrate_grams_max=280,
        fat_grams_min=55,
        fat_grams_max=90,
        confidence="High",
        allow_calorie_targets=calories,
        allow_protein_targets=True,
        allow_carbohydrate_targets=macros,
        allow_fat_targets=macros,
        nutrition_display_message="Unit test targets.",
        reason_codes=["unit_test_approved_targets"],
    )


def _food_id(name: str) -> int:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM foods WHERE name = ?", (name,))
    food_id = cursor.fetchone()["id"]
    conn.close()
    return int(food_id)


def _insert_food_entry(
    user_id: int, food_name: str, grams: float, entry_date: str
) -> None:
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_entries (user_id, food_id, grams, entry_date)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, _food_id(food_name), grams, entry_date),
    )
    conn.commit()
    conn.close()


def test_no_logs_returns_limited_confidence_and_safe_limitations(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(102, _future_date())
    guidance = build_approved_nutrition_guidance(summary)

    assert summary.logging_completeness == LOGGING_COMPLETENESS_NO_LOGS
    assert summary.confidence == "Limited"
    assert "no_nutrition_logs_today" in summary.reason_codes
    assert "nutrition_actuals_unavailable" in summary.reason_codes
    assert summary.comparisons["protein"].target_status == TARGET_STATUS_UNAVAILABLE
    assert "No nutrition logs" in guidance.summary_message
    assert validate_target_vs_actual_nutrition_summary(summary, guidance) == []


def test_partial_logs_limit_calorie_conclusions(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        101,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    guidance = build_approved_nutrition_guidance(summary)

    assert summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }
    assert summary.comparisons["calories"].comparison_available is False
    assert "calorie_delta_not_available" in summary.reason_codes
    assert "calorie conclusions should stay limited" in guidance.calorie_guidance
    assert validate_target_vs_actual_nutrition_summary(summary, guidance) == []


def test_protein_comparison_works_when_protein_target_is_approved(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    protein = summary.comparisons["protein"]

    assert protein.comparison_available is True
    assert protein.actual is not None
    assert protein.target_status in {TARGET_STATUS_BELOW, TARGET_STATUS_NEAR}
    assert "protein_target_available" in protein.reason_codes
    assert validate_target_vs_actual_nutrition_summary(summary) == []


def test_calorie_comparison_is_blocked_when_calorie_targets_not_approved(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(calories=False),
    )

    assert summary.comparisons["calories"].comparison_available is False
    assert summary.comparisons["calories"].target_status == TARGET_STATUS_UNAVAILABLE
    assert "calorie_target_unavailable" in summary.comparisons["calories"].reason_codes


def test_carbs_and_fats_compare_only_when_display_flags_and_confidence_allow(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    allowed_summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(macros=True),
    )
    blocked_summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(macros=False),
    )

    assert allowed_summary.comparisons["carbs"].comparison_available is True
    assert allowed_summary.comparisons["fat"].comparison_available is True
    assert blocked_summary.comparisons["carbs"].comparison_available is False
    assert blocked_summary.comparisons["fat"].comparison_available is False


def test_missing_nutrient_fields_are_tracked_and_not_coerced_to_zero(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    actuals = build_nutrition_actuals(105, _today())
    summary = build_target_vs_actual_nutrition_summary(
        105,
        _today(),
        nutrition_targets=_limited_targets(),
    )

    assert actuals.entry_count > 0
    assert actuals.logged_calories is None
    assert actuals.logged_protein is not None
    assert actuals.missing_calorie_entries == actuals.entry_count
    assert "missing_calorie_values" in actuals.reason_codes
    assert "calories" in summary.logging_summary.missing_nutrient_fields
    assert summary.comparisons["calories"].comparison_available is False


def test_incomplete_logging_limits_macro_certainty(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        105,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    guidance = build_approved_nutrition_guidance(summary)

    assert summary.logging_completeness in {
        LOGGING_COMPLETENESS_PARTIAL_DAY,
        LOGGING_COMPLETENESS_LIKELY_INCOMPLETE,
    }
    assert "macro_targets_limited_by_logging_quality" in summary.reason_codes
    assert "Macro comparisons are limited" in guidance.macro_guidance


def test_low_entry_and_meal_count_reason_codes_appear(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    single_entry_date = (date.today() - timedelta(days=5)).isoformat()
    _insert_food_entry(102, "QA Recovery Shake", 100, single_entry_date)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        single_entry_date,
        nutrition_targets=_approved_targets(),
    )

    assert summary.logging_completeness == LOGGING_COMPLETENESS_PARTIAL_DAY
    assert "entry_count_low" in summary.reason_codes
    assert "meal_count_low" in summary.reason_codes


def test_training_day_context_can_be_included_as_context_only(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
        training_day_context_available=True,
    )
    guidance = build_approved_nutrition_guidance(summary)
    combined = str(guidance.to_dict()).lower()

    assert "training_day_context_available" in summary.reason_codes
    assert "caused your workout" not in combined
    assert "caused poor performance" not in combined


def test_guidance_avoids_shame_restriction_medical_and_stalled_fat_loss_language(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    summary = build_target_vs_actual_nutrition_summary(
        105,
        _today(),
        nutrition_targets=_limited_targets(),
    )
    guidance = build_approved_nutrition_guidance(summary)
    combined = str(guidance.to_dict()).lower()

    forbidden = [
        "you failed",
        "bad food",
        "medical",
        "supplement",
        "stalled fat loss",
        "must cut calories",
        "skip meals",
        "compensate tomorrow",
        "burn this off",
    ]
    assert not any(term in combined for term in forbidden)
    assert validate_target_vs_actual_nutrition_summary(summary, guidance) == []


def test_deterministic_output_remains_stable(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    first = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )
    second = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )

    assert first.to_dict() == second.to_dict()


def test_complete_enough_logs_can_compare_calories_cautiously(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _insert_food_entry(102, "QA Complete Performance Meal", 100, _today())

    summary = build_target_vs_actual_nutrition_summary(
        102,
        _today(),
        nutrition_targets=_approved_targets(),
    )

    assert summary.logging_completeness == LOGGING_COMPLETENESS_COMPLETE_ENOUGH
    assert summary.comparisons["calories"].comparison_available is True
    assert "calorie_target_available" in summary.comparisons["calories"].reason_codes


@pytest.mark.parametrize("user_id", [101, 102, 103, 104, 105])
def test_seeded_users_build_safe_target_vs_actual_summaries(
    user_id, tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(user_id)

    summary = build_target_vs_actual_nutrition_summary(
        user_id,
        _today(),
        health_state=health_state,
    )
    guidance = build_approved_nutrition_guidance(summary)
    violations = validate_target_vs_actual_nutrition_summary(summary, guidance)

    assert summary.user_id == user_id
    assert summary.nutrition_actuals.user_id == user_id
    assert set(summary.comparisons) == {"calories", "protein", "carbs", "fat"}
    assert violations == []
