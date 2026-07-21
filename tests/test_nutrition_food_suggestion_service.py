from __future__ import annotations

import database
from models.nutrition_food_suggestion_models import (
    CanonicalFoodSuggestionCandidate,
    NutritionMacroGap,
)
from models.nutrition_target_models import NutritionTargets
from models.nutrition_target_vs_actual_models import TARGET_STATUS_UNAVAILABLE
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
    seed_starter_canonical_foods,
)
from services.nutrition_food_suggestion_service import (
    approve_food_suggestions,
    build_approved_nutrition_food_suggestions,
    build_nutrition_macro_gaps,
    get_canonical_food_suggestion_candidates,
    rank_food_suggestion_candidates,
)
from services.nutrition_service import add_canonical_food_entry
from services.nutrition_serving_unit_service import (
    create_or_update_serving_unit,
    ensure_serving_unit_schema,
    seed_canonical_food_serving_units,
)
from services.nutrition_target_vs_actual_service import (
    build_target_vs_actual_nutrition_summary,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    seed_starter_canonical_foods()
    ensure_serving_unit_schema()
    seed_canonical_food_serving_units()


def _approved_targets(
    *,
    protein: bool = True,
    calories: bool = False,
    macros: bool = False,
    confidence: str = "Moderate",
) -> NutritionTargets:
    return NutritionTargets(
        body_weight_lb=190,
        calorie_target_min=2200 if calories else None,
        calorie_target_max=2500 if calories else None,
        protein_grams_min=150 if protein else None,
        protein_grams_max=185 if protein else None,
        carbohydrate_grams_min=180 if macros else None,
        carbohydrate_grams_max=280 if macros else None,
        fat_grams_min=55 if macros else None,
        fat_grams_max=90 if macros else None,
        confidence=confidence,
        allow_calorie_targets=calories,
        allow_protein_targets=protein,
        allow_carbohydrate_targets=macros,
        allow_fat_targets=macros,
        nutrition_display_message="Unit test targets.",
        reason_codes=["unit_test_targets"],
    )


def _macro_gap(
    macro_name: str,
    *,
    target_status: str,
    display_allowed: bool = True,
    gap_value: float | None = None,
    reason_codes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> NutritionMacroGap:
    unit = "kcal" if macro_name == "calories" else "g"
    return NutritionMacroGap(
        macro_name=macro_name,
        target_value=(
            (100.0 + gap_value)
            if display_allowed and gap_value
            else (100.0 if display_allowed else None)
        ),
        actual_value=100.0 if display_allowed else None,
        gap_value=gap_value,
        unit=unit,
        target_status=target_status,
        display_allowed=display_allowed,
        confidence="Moderate" if display_allowed else "Limited",
        reason_codes=reason_codes
        or (["target_not_approved"] if not display_allowed else []),
        limitations=limitations
        or (["Target is limited."] if not display_allowed else []),
    )


def _canonical_id_for_query(query: str) -> int:
    from services.food_normalization_service import search_canonical_foods

    results = search_canonical_foods(query, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def _candidate_for_food(candidates, display_name: str, macro_name: str):
    return next(
        candidate
        for candidate in candidates
        if candidate.display_name == display_name
        and candidate.macro_gap_addressed == macro_name
    )


def _create_complete_canonical_food(
    display_name: str,
    *,
    food_type: str = "branded",
    calories: float,
    protein_g: float,
    carbohydrate_g: float,
    fat_g: float,
):
    food = create_canonical_food(display_name, food_type, search_priority=100)
    create_canonical_food_nutrient(food.id, "Calories", "kcal", calories)
    create_canonical_food_nutrient(food.id, "Protein", "g", protein_g)
    create_canonical_food_nutrient(
        food.id,
        "Carbohydrate",
        "g",
        carbohydrate_g,
    )
    create_canonical_food_nutrient(food.id, "Fat", "g", fat_g)
    return food


def _ranked_candidate(
    canonical_food_id: int,
    macro_gap_addressed: str,
    *,
    score: float,
    serving_grams: float = 100,
    display_name: str | None = None,
    calories: float = 100,
    protein_g: float = 10,
    carbohydrate_g: float = 10,
    fat_g: float = 5,
    reason_codes: list[str] | None = None,
) -> CanonicalFoodSuggestionCandidate:
    return CanonicalFoodSuggestionCandidate(
        canonical_food_id=canonical_food_id,
        display_name=display_name or f"Food {canonical_food_id}",
        food_type="cooked",
        serving_grams=serving_grams,
        calories=calories,
        protein_g=protein_g,
        carbohydrate_g=carbohydrate_g,
        fat_g=fat_g,
        macro_gap_addressed=macro_gap_addressed,
        score=score,
        confidence="Moderate",
        reason_codes=reason_codes or [],
    )


def _protein_gap_macro_gaps(gap_value: float = 40) -> list[NutritionMacroGap]:
    return [
        _macro_gap(
            "protein_g",
            target_status="below_target",
            gap_value=gap_value,
            reason_codes=["protein_gap_available"],
        ),
        _macro_gap("calories", target_status="near_target", gap_value=None),
        _macro_gap("carbohydrate_g", target_status="near_target", gap_value=None),
        _macro_gap("fat_g", target_status="near_target", gap_value=None),
    ]


def _remaining_state_macro_gaps(
    *,
    calories: float,
    protein_g: float,
    carbohydrate_g: float,
    fat_g: float,
) -> list[NutritionMacroGap]:
    values = {
        "calories": (2200.0, calories),
        "protein_g": (150.0, protein_g),
        "carbohydrate_g": (240.0, carbohydrate_g),
        "fat_g": (70.0, fat_g),
    }
    gaps: list[NutritionMacroGap] = []
    for macro_name, (target, remaining) in values.items():
        unit = "kcal" if macro_name == "calories" else "g"
        gaps.append(
            NutritionMacroGap(
                macro_name=macro_name,
                target_value=target,
                actual_value=target - remaining,
                gap_value=remaining,
                unit=unit,
                target_status="below_target",
                display_allowed=True,
                confidence="Moderate",
            )
        )
    return gaps


def _protein_gap_summary(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=100,
        entry_date="2026-06-06",
    )
    return build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(),
    )


def test_build_nutrition_macro_gaps_detects_approved_protein_gap(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    gaps = build_nutrition_macro_gaps(summary)
    protein_gap = next(gap for gap in gaps if gap.macro_name == "protein_g")

    assert protein_gap.display_allowed is True
    assert protein_gap.target_status == "below_target"
    assert protein_gap.gap_value == 119.0
    assert "protein_gap_available" in protein_gap.reason_codes


def test_protein_gap_produces_approved_canonical_food_suggestions(
    tmp_path, monkeypatch
):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.primary_gap == "protein_g"
    assert approved.suggestions
    assert "protein_gap_available" in approved.reason_codes
    assert all(suggestion.canonical_food_id > 0 for suggestion in approved.suggestions)
    assert all(
        suggestion.macro_gap_addressed == "protein_g"
        for suggestion in approved.suggestions
    )


def test_no_protein_target_produces_no_protein_suggestions_with_limitations(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(1, chicken_id, 100, "2026-06-06")
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(protein=False),
    )

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.suggestions == []
    assert "target_not_approved" in approved.reason_codes
    assert approved.limitations
    protein_gap = next(
        gap for gap in approved.macro_gaps if gap.macro_name == "protein_g"
    )
    assert protein_gap.display_allowed is False


def test_blocked_protein_target_produces_no_suggestions(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(protein=False),
    )

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.suggestions == []
    protein_gap = next(
        gap for gap in approved.macro_gaps if gap.macro_name == "protein_g"
    )
    assert protein_gap.target_status in {"limited", "unavailable"}
    assert protein_gap.display_allowed is False


def test_no_macro_gap_produces_no_suggestion_state(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(1, chicken_id, 700, "2026-06-06")
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(),
    )

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.suggestions == []
    assert "no_macro_gap_detected" in approved.reason_codes


def test_protein_above_target_with_calorie_gap_produces_calorie_support_suggestions(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = [
        _macro_gap("protein_g", target_status="above_target", gap_value=None),
        _macro_gap(
            "calories",
            target_status="below_target",
            gap_value=400,
            reason_codes=["calorie_gap_available"],
        ),
        _macro_gap(
            "carbohydrate_g",
            target_status="near_target",
            gap_value=None,
        ),
        _macro_gap("fat_g", target_status="near_target", gap_value=None),
    ]
    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions
    assert approved.primary_gap == "calories"
    assert "no_macro_gap_detected" not in approved.reason_codes
    assert "no_supported_suggestion_gap_available" not in approved.reason_codes
    assert "calorie_support_suggestion_available" in approved.reason_codes
    assert all(
        suggestion.macro_gap_addressed == "calories"
        for suggestion in approved.suggestions
    )


def _carbohydrate_gap_macro_gaps(
    *,
    calorie_status: str = "below_target",
    carbohydrate_display_allowed: bool = True,
    calorie_display_allowed: bool = True,
) -> list[NutritionMacroGap]:
    return [
        _macro_gap("protein_g", target_status="above_target", gap_value=None),
        _macro_gap(
            "calories",
            target_status=calorie_status,
            display_allowed=calorie_display_allowed,
            gap_value=(500 if calorie_status == "below_target" else None),
            reason_codes=(
                ["calorie_gap_available"] if calorie_status == "below_target" else []
            ),
        ),
        _macro_gap(
            "carbohydrate_g",
            target_status=(
                "below_target" if carbohydrate_display_allowed else "limited"
            ),
            display_allowed=carbohydrate_display_allowed,
            gap_value=(75 if carbohydrate_display_allowed else None),
            reason_codes=(
                ["carbohydrate_gap_available"]
                if carbohydrate_display_allowed
                else ["target_not_approved"]
            ),
            limitations=(
                [] if carbohydrate_display_allowed else ["Target is limited."]
            ),
        ),
        _macro_gap("fat_g", target_status="near_target", gap_value=None),
    ]


def test_approved_carbohydrate_gap_produces_canonical_suggestions(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _carbohydrate_gap_macro_gaps()

    # Build directly from approved macro gaps so this test focuses only on carb expansion.
    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.primary_gap == "calories"
    assert approved.suggestions
    assert "carbohydrate_gap_available" in approved.reason_codes
    assert "carbohydrate_suggestion_available" in approved.reason_codes
    assert approved.suggestions[0].macro_gap_addressed == "calories"
    assert {suggestion.macro_gap_addressed for suggestion in approved.suggestions} <= {
        "carbohydrate_g",
        "calories",
    }


def test_carbohydrate_suggestions_reference_canonical_food_and_nutrients(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _carbohydrate_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert all(suggestion.canonical_food_id > 0 for suggestion in approved.suggestions)
    assert all(
        suggestion.estimated_carbohydrate_g is not None
        and suggestion.estimated_carbohydrate_g > 0
        for suggestion in approved.suggestions
    )
    assert all(
        suggestion.estimated_calories is not None and suggestion.estimated_calories >= 0
        for suggestion in approved.suggestions
    )


def test_carbohydrate_serving_grams_are_positive_and_practical(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _carbohydrate_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    for suggestion in approved.suggestions:
        assert suggestion.suggested_grams > 0
        if "Rice" in suggestion.display_name or "Pasta" in suggestion.display_name:
            assert 100 <= suggestion.suggested_grams <= 250
        if suggestion.display_name == "Oats, Dry":
            assert 30 <= suggestion.suggested_grams <= 80
        if "Potato" in suggestion.display_name:
            assert 100 <= suggestion.suggested_grams <= 300
        if suggestion.display_name in {"Banana", "Apple"}:
            assert 100 <= suggestion.suggested_grams <= 200


def test_protein_above_target_with_carbohydrate_gap_no_longer_uses_unsupported_v1_semantics(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _carbohydrate_gap_macro_gaps()
    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions
    assert "no_macro_gap_detected" not in approved.reason_codes
    assert "no_supported_suggestion_gap_available" not in approved.reason_codes
    assert "carbohydrate_gap_suggestions_not_enabled_v1" not in approved.reason_codes


def test_carbohydrate_target_blocked_produces_no_carb_suggestions_with_limitations():
    macro_gaps = _carbohydrate_gap_macro_gaps(carbohydrate_display_allowed=False)

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert all(
        suggestion.macro_gap_addressed != "carbohydrate_g"
        for suggestion in approved.suggestions
    )
    assert approved.suggestions
    assert all(
        suggestion.macro_gap_addressed == "calories"
        for suggestion in approved.suggestions
    )


def test_calorie_target_blocked_produces_no_carb_suggestions_with_limitations():
    macro_gaps = _carbohydrate_gap_macro_gaps(calorie_display_allowed=False)

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert "carb_suggestion_limited" in approved.reason_codes
    assert any("calorie target" in limitation for limitation in approved.limitations)


def test_incomplete_logging_limits_carbohydrate_suggestions():
    macro_gaps = _carbohydrate_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=True,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Low",
        logging_incomplete=True,
    )

    assert approved.suggestions == []
    assert "logging_incomplete_limits_suggestions" in approved.reason_codes
    assert any("logging appears incomplete" in item for item in approved.limitations)


def test_calorie_above_target_conflict_blocks_carbohydrate_suggestions():
    macro_gaps = _carbohydrate_gap_macro_gaps(calorie_status="above_target")

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert "carb_suggestion_limited" in approved.reason_codes
    assert "calorie_conflict_limits_carb_suggestions" in approved.reason_codes
    assert any(
        "calories are already above target" in item for item in approved.limitations
    )


def _calorie_gap_macro_gaps(
    *,
    calorie_display_allowed: bool = True,
    logging_conflict_macro: str | None = None,
) -> list[NutritionMacroGap]:
    return [
        _macro_gap("protein_g", target_status="near_target", gap_value=None),
        _macro_gap(
            "calories",
            target_status="below_target" if calorie_display_allowed else "limited",
            display_allowed=calorie_display_allowed,
            gap_value=(450 if calorie_display_allowed else None),
            reason_codes=(
                ["calorie_gap_available"]
                if calorie_display_allowed
                else ["target_not_approved"]
            ),
            limitations=[] if calorie_display_allowed else ["Target is limited."],
        ),
        _macro_gap(
            "carbohydrate_g",
            target_status=(
                "above_target"
                if logging_conflict_macro == "carbohydrate_g"
                else "near_target"
            ),
            gap_value=None,
        ),
        _macro_gap(
            "fat_g",
            target_status=(
                "above_target" if logging_conflict_macro == "fat_g" else "near_target"
            ),
            gap_value=None,
        ),
    ]


def test_approved_calorie_gap_produces_canonical_calorie_support_suggestions(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _calorie_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.primary_gap == "calories"
    assert approved.suggestions
    assert "calorie_gap_available" in approved.reason_codes
    assert "calorie_support_suggestion_available" in approved.reason_codes
    assert all(
        suggestion.macro_gap_addressed == "calories"
        for suggestion in approved.suggestions
    )
    assert all(suggestion.canonical_food_id > 0 for suggestion in approved.suggestions)


def test_calorie_support_suggestions_use_canonical_nutrients_and_practical_servings(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _calorie_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    for suggestion in approved.suggestions:
        assert suggestion.estimated_calories is not None
        assert suggestion.estimated_calories > 0
        assert suggestion.estimated_protein_g is not None
        assert suggestion.estimated_protein_g >= 0
        assert suggestion.estimated_carbohydrate_g is not None
        assert suggestion.estimated_carbohydrate_g >= 0
        assert suggestion.estimated_fat_g is not None
        assert suggestion.estimated_fat_g >= 0
        assert suggestion.suggested_grams > 0
        if suggestion.display_name in {"Almonds", "Walnuts", "Cashews"}:
            assert 15 <= suggestion.suggested_grams <= 30
        if suggestion.display_name == "Peanut Butter":
            assert 16 <= suggestion.suggested_grams <= 32
        if "Rice" in suggestion.display_name or "Pasta" in suggestion.display_name:
            assert 100 <= suggestion.suggested_grams <= 250
        if suggestion.display_name == "Oats, Dry":
            assert 30 <= suggestion.suggested_grams <= 80


def test_calorie_target_blocked_produces_no_calorie_support_suggestions():
    macro_gaps = _calorie_gap_macro_gaps(calorie_display_allowed=False)

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert all(
        suggestion.macro_gap_addressed != "calories"
        for suggestion in approved.suggestions
    )
    assert approved.limitations


def test_incomplete_logging_limits_calorie_support_suggestions():
    macro_gaps = _calorie_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=True,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Low",
        logging_incomplete=True,
    )

    assert approved.suggestions == []
    assert "logging_incomplete_limits_suggestions" in approved.reason_codes
    assert any("logging appears incomplete" in item for item in approved.limitations)


def test_fat_above_target_conflict_avoids_high_fat_calorie_support_options(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _calorie_gap_macro_gaps(logging_conflict_macro="fat_g")

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions
    assert "calorie_support_suggestion_available" in approved.reason_codes
    assert all(
        (suggestion.estimated_fat_g or 0.0) <= 9.0
        for suggestion in approved.suggestions
    )


def test_carb_above_target_conflict_avoids_high_carb_calorie_support_options(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _calorie_gap_macro_gaps(logging_conflict_macro="carbohydrate_g")

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions
    assert "calorie_support_suggestion_available" in approved.reason_codes
    assert all(
        (suggestion.estimated_carbohydrate_g or 0.0) <= 30.0
        for suggestion in approved.suggestions
    )


def test_incomplete_logging_adds_cautious_limitations(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert approved.confidence == "Low"
    assert "logging_incomplete_limits_suggestions" in approved.reason_codes
    assert any(
        "logging appears incomplete" in limitation
        for limitation in approved.limitations
    )


def test_suggestions_use_canonical_nutrient_data(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(),
        logging_incomplete=False,
    )
    chicken = _candidate_for_food(
        candidates,
        "Chicken Breast, Cooked, Skinless",
        "protein_g",
    )

    assert chicken.calories == round(165 * chicken.serving_grams / 100, 1)
    assert chicken.protein_g == round(31 * chicken.serving_grams / 100, 1)
    assert chicken.carbohydrate_g == 0.0
    assert chicken.fat_g == round(3.6 * chicken.serving_grams / 100, 1)
    assert "serving_unit_metadata_available" in chicken.reason_codes


def test_suggested_grams_are_positive_and_within_practical_bounds(
    tmp_path, monkeypatch
):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    for suggestion in approved.suggestions:
        assert suggestion.suggested_grams > 0
        if suggestion.display_name == "Chicken Breast, Cooked, Skinless":
            assert 100 <= suggestion.suggested_grams <= 200
        if suggestion.display_name == "Whey Protein Powder, Generic":
            assert 25 <= suggestion.suggested_grams <= 35


def test_estimated_nutrients_are_non_negative(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    for suggestion in approved.suggestions:
        assert (
            suggestion.estimated_calories is not None
            and suggestion.estimated_calories >= 0
        )
        assert (
            suggestion.estimated_protein_g is not None
            and suggestion.estimated_protein_g >= 0
        )
        assert (
            suggestion.estimated_carbohydrate_g is not None
            and suggestion.estimated_carbohydrate_g >= 0
        )
        assert (
            suggestion.estimated_fat_g is not None and suggestion.estimated_fat_g >= 0
        )


def test_foods_with_incomplete_nutrients_are_excluded(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    incomplete_food = create_canonical_food(
        "Incomplete Protein Canonical Food",
        "generic",
        search_priority=1,
    )
    create_canonical_food_nutrient(incomplete_food.id, "Protein", "g", 95)
    chicken_id = _canonical_id_for_query("chicken breast")
    add_canonical_food_entry(1, chicken_id, 100, "2026-06-06")
    summary = build_target_vs_actual_nutrition_summary(
        1,
        "2026-06-06",
        nutrition_targets=_approved_targets(),
    )
    gaps = build_nutrition_macro_gaps(summary)

    candidates = get_canonical_food_suggestion_candidates(gaps)

    assert all(
        candidate.canonical_food_id != incomplete_food.id for candidate in candidates
    )


def test_non_curated_catalog_protein_food_can_become_a_candidate(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(),
        logging_incomplete=False,
    )

    chicken_thigh = _candidate_for_food(
        candidates,
        "Chicken Thigh, Cooked, Skinless",
        "protein_g",
    )
    assert 75 <= chicken_thigh.serving_grams <= 250
    assert "catalog_fallback_serving_bounds" in chicken_thigh.reason_codes


def test_non_curated_catalog_carbohydrate_food_can_become_a_candidate(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _carbohydrate_gap_macro_gaps()
    macro_gaps[2] = _macro_gap(
        "carbohydrate_g",
        target_status="below_target",
        gap_value=40,
        reason_codes=["carbohydrate_gap_available"],
    )

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    quinoa = _candidate_for_food(candidates, "Quinoa, Cooked", "carbohydrate_g")
    assert 75 <= quinoa.serving_grams <= 300
    assert "catalog_fallback_serving_bounds" in quinoa.reason_codes


def test_non_curated_catalog_calorie_support_food_can_become_a_candidate(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    candidates = get_canonical_food_suggestion_candidates(
        _calorie_gap_macro_gaps(),
        logging_incomplete=False,
    )

    granola = _candidate_for_food(candidates, "Granola", "calories")
    assert 50 <= granola.serving_grams <= 250
    assert "catalog_fallback_serving_bounds" in granola.reason_codes


def test_non_curated_catalog_fat_support_food_can_become_a_candidate(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    candidates = get_canonical_food_suggestion_candidates(
        _fat_gap_macro_gaps(),
        logging_incomplete=False,
    )

    coconut_oil = _candidate_for_food(candidates, "Coconut Oil", "fat_g")
    assert 5 <= coconut_oil.serving_grams <= 40
    assert "catalog_fallback_serving_bounds" in coconut_oil.reason_codes


def test_curated_protein_food_retains_bounds_and_preference_advantage(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(),
        logging_incomplete=False,
    )

    chicken_breast = _candidate_for_food(
        candidates,
        "Chicken Breast, Cooked, Skinless",
        "protein_g",
    )
    chicken_thigh = _candidate_for_food(
        candidates,
        "Chicken Thigh, Cooked, Skinless",
        "protein_g",
    )
    assert 100 <= chicken_breast.serving_grams <= 200
    assert "catalog_fallback_serving_bounds" not in chicken_breast.reason_codes
    assert chicken_breast.score > chicken_thigh.score


def test_raw_animal_food_is_excluded_from_a_role_it_would_otherwise_qualify_for(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(),
        logging_incomplete=False,
    )

    candidate_names = {candidate.display_name for candidate in candidates}
    assert "Chicken Thigh, Raw, Skinless" not in candidate_names
    assert "Chicken Thigh, Cooked, Skinless" in candidate_names


def test_raw_produce_remains_eligible_for_an_appropriate_macro_role(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _carbohydrate_gap_macro_gaps()
    macro_gaps[2] = _macro_gap(
        "carbohydrate_g",
        target_status="below_target",
        gap_value=40,
        reason_codes=["carbohydrate_gap_available"],
    )

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    candidate_names = {candidate.display_name for candidate in candidates}
    assert "Plantain, Raw" in candidate_names


def test_nonzero_but_unsuitable_macro_sources_are_not_candidates(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    protein_candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(),
        logging_incomplete=False,
    )
    carbohydrate_macro_gaps = _carbohydrate_gap_macro_gaps()
    carbohydrate_macro_gaps[2] = _macro_gap(
        "carbohydrate_g",
        target_status="below_target",
        gap_value=40,
        reason_codes=["carbohydrate_gap_available"],
    )
    carbohydrate_candidates = get_canonical_food_suggestion_candidates(
        carbohydrate_macro_gaps,
        logging_incomplete=False,
    )

    assert not any(
        candidate.display_name == "Broccoli, Cooked"
        and candidate.macro_gap_addressed == "protein_g"
        for candidate in protein_candidates
    )
    assert not any(
        candidate.display_name == "Honey"
        and candidate.macro_gap_addressed == "carbohydrate_g"
        for candidate in carbohydrate_candidates
    )


def test_non_curated_food_uses_bounded_partial_protein_improvement(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(),
        logging_incomplete=False,
    )

    edamame = _candidate_for_food(candidates, "Edamame", "protein_g")

    assert 75 <= edamame.serving_grams <= 150
    assert "practical_serving_bounds_used" in edamame.reason_codes


def test_recent_log_quantity_is_used_when_serving_metadata_is_unavailable(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    recent_food = _create_complete_canonical_food(
        "Recent Lean Protein",
        food_type="cooked",
        calories=160,
        protein_g=25,
        carbohydrate_g=2,
        fat_g=5,
    )
    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(gap_value=80),
        logging_incomplete=False,
        recent_quantity_rows=[
            {
                "canonical_food_id": recent_food.id,
                "recent_grams": 125,
                "usage_count": 3,
            }
        ],
    )
    recent_candidate = next(
        candidate
        for candidate in candidates
        if candidate.canonical_food_id == recent_food.id
        and candidate.macro_gap_addressed == "protein_g"
    )

    assert recent_candidate.serving_grams in {62.5, 125.0, 187.5, 250.0}
    assert "recent_log_quantity_reference" in recent_candidate.reason_codes


def test_heavily_consumed_food_drops_out_of_same_day_suggestions(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)
    tuna_id = _canonical_id_for_query("tuna")
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=tuna_id,
        grams=300,
        entry_date="2026-06-06",
    )

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
        limit=8,
    )

    assert all(
        suggestion.canonical_food_id != tuna_id for suggestion in approved.suggestions
    )


def test_low_confidence_serving_metadata_does_not_anchor_a_suggestion(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    low_confidence_food = _create_complete_canonical_food(
        "Low Confidence Lean Protein",
        food_type="cooked",
        calories=160,
        protein_g=25,
        carbohydrate_g=2,
        fat_g=5,
    )
    create_or_update_serving_unit(
        canonical_food_id=low_confidence_food.id,
        unit_name="serving",
        unit_quantity=1,
        display_name="1 estimated portion",
        grams_default=40,
        grams_min=20,
        grams_max=80,
        confidence="Low",
        source="unit_test",
        source_note="Intentionally unreliable serving metadata fixture.",
    )

    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(gap_value=80),
        logging_incomplete=False,
    )
    candidate = next(
        candidate
        for candidate in candidates
        if candidate.canonical_food_id == low_confidence_food.id
        and candidate.macro_gap_addressed == "protein_g"
    )

    assert candidate.serving_grams >= 75
    assert "practical_serving_bounds_used" in candidate.reason_codes
    assert "serving_unit_metadata_available" not in candidate.reason_codes


def test_concentrated_protein_forms_use_bounded_serving_options_not_gap_scaling(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    collagen = _create_complete_canonical_food(
        "Collagen Peptides + Probiotics",
        calories=313.7,
        protein_g=90.5,
        carbohydrate_g=0,
        fat_g=0,
    )
    protein_powder = _create_complete_canonical_food(
        "Custom Protein Powder",
        calories=390,
        protein_g=80,
        carbohydrate_g=8,
        fat_g=4,
    )
    create_or_update_serving_unit(
        canonical_food_id=collagen.id,
        unit_name="serving",
        unit_quantity=1,
        display_name="1 portion (21 g)",
        grams_default=21,
        grams_min=21,
        grams_max=21,
        confidence="High",
        source="unit_test",
        source_note="Barcode serving metadata fixture.",
    )

    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(gap_value=119),
        logging_incomplete=False,
    )
    collagen_candidate = next(
        candidate
        for candidate in candidates
        if candidate.canonical_food_id == collagen.id
        and candidate.macro_gap_addressed == "protein_g"
    )
    powder_candidate = next(
        candidate
        for candidate in candidates
        if candidate.canonical_food_id == protein_powder.id
        and candidate.macro_gap_addressed == "protein_g"
    )

    assert collagen_candidate.serving_grams == 21.0
    assert powder_candidate.serving_grams <= 35
    assert "serving_unit_metadata_available" in collagen_candidate.reason_codes
    assert "concentrated_food_form_deprioritized" in collagen_candidate.reason_codes


def test_practical_concentrated_protein_form_is_deprioritized_to_ordinary_food(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    powder = _create_complete_canonical_food(
        "Custom Protein Powder",
        calories=390,
        protein_g=80,
        carbohydrate_g=8,
        fat_g=4,
    )

    candidates = get_canonical_food_suggestion_candidates(
        _protein_gap_macro_gaps(gap_value=20),
        logging_incomplete=False,
    )
    powder_candidate = next(
        candidate
        for candidate in candidates
        if candidate.canonical_food_id == powder.id
        and candidate.macro_gap_addressed == "protein_g"
    )
    chicken_candidate = _candidate_for_food(
        candidates,
        "Chicken Breast, Cooked, Skinless",
        "protein_g",
    )

    assert 25 <= powder_candidate.serving_grams <= 35
    assert "concentrated_food_form_deprioritized" in powder_candidate.reason_codes
    assert powder_candidate.score < chicken_candidate.score


def test_protein_candidates_use_available_remaining_calorie_and_macro_context(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    dense_food = _create_complete_canonical_food(
        "Dense Protein Bite",
        calories=700,
        protein_g=70,
        carbohydrate_g=10,
        fat_g=40,
    )
    macro_gaps = [
        _macro_gap(
            "protein_g",
            target_status="below_target",
            gap_value=40,
            reason_codes=["protein_gap_available"],
        ),
        _macro_gap(
            "calories",
            target_status="below_target",
            gap_value=100,
            reason_codes=["calorie_gap_available"],
        ),
        _macro_gap("carbohydrate_g", target_status="near_target"),
        _macro_gap("fat_g", target_status="above_target"),
    ]

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    chicken_candidate = _candidate_for_food(
        candidates,
        "Chicken Breast, Cooked, Skinless",
        "protein_g",
    )

    assert not any(
        candidate.canonical_food_id == dense_food.id
        and candidate.macro_gap_addressed == "protein_g"
        for candidate in candidates
    )
    assert "remaining_macro_context_checked" in chicken_candidate.reason_codes
    assert "multi_gap_context_fit" in chicken_candidate.reason_codes


def test_ketchup_is_not_a_catalog_carbohydrate_action_for_representative_gap(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _carbohydrate_gap_macro_gaps()
    macro_gaps[2] = _macro_gap(
        "carbohydrate_g",
        target_status="below_target",
        gap_value=40,
        reason_codes=["carbohydrate_gap_available"],
    )

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    assert not any(
        candidate.display_name == "Ketchup"
        and candidate.macro_gap_addressed == "carbohydrate_g"
        for candidate in candidates
    )
    assert any(
        candidate.display_name == "Quinoa, Cooked"
        and candidate.macro_gap_addressed == "carbohydrate_g"
        for candidate in candidates
    )


def test_impractical_chia_and_protein_bar_servings_are_not_default_calorie_actions(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _calorie_gap_macro_gaps()
    macro_gaps[1] = _macro_gap(
        "calories",
        target_status="below_target",
        gap_value=500,
        reason_codes=["calorie_gap_available"],
    )
    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    approved_names = {suggestion.display_name for suggestion in approved.suggestions}
    assert "Chia Seeds" not in approved_names
    assert "Protein Bar, Generic" not in approved_names
    assert any(candidate.display_name == "Granola" for candidate in candidates)


def test_curated_portion_ceiling_applies_across_macro_roles(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    candidates = get_canonical_food_suggestion_candidates(
        _calorie_gap_macro_gaps(),
        logging_incomplete=False,
    )
    almond_butter = _candidate_for_food(candidates, "Almond Butter", "calories")

    assert almond_butter.serving_grams <= 32


def test_small_remaining_macro_roles_drop_out_of_candidate_generation(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _remaining_state_macro_gaps(
        calories=800,
        protein_g=12,
        carbohydrate_g=20,
        fat_g=5,
    )

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    candidate_roles = {candidate.macro_gap_addressed for candidate in candidates}
    assert candidate_roles == {"calories"}


def test_recommendation_roster_evolves_with_remaining_nutrition_state(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    early_gaps = _remaining_state_macro_gaps(
        calories=1800,
        protein_g=120,
        carbohydrate_g=200,
        fat_g=50,
    )
    protein_dominant_gaps = _remaining_state_macro_gaps(
        calories=500,
        protein_g=70,
        carbohydrate_g=20,
        fat_g=5,
    )

    early = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=early_gaps,
        candidates=get_canonical_food_suggestion_candidates(
            early_gaps,
            logging_incomplete=False,
        ),
        summary_confidence="Moderate",
        limit=8,
    )
    protein_dominant = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=protein_dominant_gaps,
        candidates=get_canonical_food_suggestion_candidates(
            protein_dominant_gaps,
            logging_incomplete=False,
        ),
        summary_confidence="Moderate",
        limit=8,
    )

    early_ids = {suggestion.canonical_food_id for suggestion in early.suggestions}
    protein_ids = {
        suggestion.canonical_food_id for suggestion in protein_dominant.suggestions
    }
    assert early.suggestions[0].macro_gap_addressed == "carbohydrate_g"
    assert protein_dominant.suggestions[0].macro_gap_addressed == "protein_g"
    assert len(early_ids.symmetric_difference(protein_ids)) >= 4


def test_blocked_calorie_carb_fat_targets_do_not_generate_hard_suggestions(
    tmp_path, monkeypatch
):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )

    assert all(
        suggestion.macro_gap_addressed == "protein_g"
        for suggestion in approved.suggestions
    )
    blocked_macros = {
        gap.macro_name
        for gap in approved.macro_gaps
        if gap.target_status in {"limited", "unavailable", TARGET_STATUS_UNAVAILABLE}
    }
    assert {"calories", "carbohydrate_g", "fat_g"}.issubset(blocked_macros)


def test_ranking_is_deterministic(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)
    gaps = build_nutrition_macro_gaps(summary)
    candidates = get_canonical_food_suggestion_candidates(gaps)

    first = rank_food_suggestion_candidates(candidates, limit=5)
    second = rank_food_suggestion_candidates(list(reversed(candidates)), limit=5)

    assert [candidate.canonical_food_id for candidate in first] == [
        candidate.canonical_food_id for candidate in second
    ]


def test_ranking_diversifies_macro_roles_before_second_role_choices():
    candidates = [
        _ranked_candidate(1, "protein_g", score=100),
        _ranked_candidate(2, "protein_g", score=90),
        _ranked_candidate(3, "carbohydrate_g", score=100),
        _ranked_candidate(4, "carbohydrate_g", score=90),
        _ranked_candidate(5, "calories", score=100),
        _ranked_candidate(6, "fat_g", score=100),
    ]

    ranked = rank_food_suggestion_candidates(candidates, limit=6)

    assert [candidate.macro_gap_addressed for candidate in ranked] == [
        "protein_g",
        "carbohydrate_g",
        "calories",
        "fat_g",
        "protein_g",
        "carbohydrate_g",
    ]


def test_ranking_prefers_lexically_distinct_foods_within_a_macro_role():
    candidates = [
        _ranked_candidate(
            1,
            "protein_g",
            score=100,
            display_name="Chicken Breast, Cooked",
        ),
        _ranked_candidate(
            2,
            "protein_g",
            score=99,
            display_name="Chicken Thigh, Cooked",
        ),
        _ranked_candidate(
            3,
            "protein_g",
            score=98,
            display_name="Greek Yogurt, Plain",
        ),
        _ranked_candidate(
            4,
            "protein_g",
            score=97,
            display_name="Tuna, Canned in Water",
        ),
    ]

    ranked = rank_food_suggestion_candidates(candidates, limit=3)

    assert [candidate.canonical_food_id for candidate in ranked] == [1, 3, 4]


def test_ranking_prefers_distinct_nutrition_profiles_within_fit_window():
    candidates = [
        _ranked_candidate(
            1,
            "protein_g",
            score=100,
            display_name="Lean Protein One",
            calories=120,
            protein_g=25,
            carbohydrate_g=0,
            fat_g=1,
        ),
        _ranked_candidate(
            2,
            "protein_g",
            score=99,
            display_name="Lean Protein Two",
            calories=115,
            protein_g=24,
            carbohydrate_g=0,
            fat_g=1,
        ),
        _ranked_candidate(
            3,
            "protein_g",
            score=98,
            display_name="Mixed Protein Option",
            calories=180,
            protein_g=20,
            carbohydrate_g=8,
            fat_g=8,
        ),
    ]

    ranked = rank_food_suggestion_candidates(candidates, limit=2)

    assert [candidate.canonical_food_id for candidate in ranked] == [1, 3]


def test_state_relative_fit_expands_beyond_the_old_leader_score_window():
    macro_gaps = _protein_gap_macro_gaps(gap_value=40)
    candidates = [
        _ranked_candidate(
            1,
            "protein_g",
            score=180,
            display_name="Static Leader Protein",
            calories=130,
            protein_g=30,
            carbohydrate_g=0,
            fat_g=1,
        ),
        _ranked_candidate(
            2,
            "protein_g",
            score=110,
            display_name="Broader Mixed Protein",
            calories=210,
            protein_g=22,
            carbohydrate_g=12,
            fat_g=8,
        ),
    ]

    ranked = rank_food_suggestion_candidates(
        candidates,
        limit=2,
        macro_gaps=macro_gaps,
        rotation_key="state-relative-fit",
    )

    assert {candidate.canonical_food_id for candidate in ranked} == {1, 2}
    assert candidates[0].score - candidates[1].score > 12


def test_state_relative_quality_floor_rejects_nutritionally_weak_novelty():
    macro_gaps = _protein_gap_macro_gaps(gap_value=40)
    candidates = [
        _ranked_candidate(
            1,
            "protein_g",
            score=150,
            protein_g=25,
        ),
        _ranked_candidate(
            2,
            "protein_g",
            score=140,
            display_name="Novel But Weak",
            calories=300,
            protein_g=2,
            carbohydrate_g=40,
            fat_g=12,
        ),
        _ranked_candidate(
            3,
            "protein_g",
            score=30,
            display_name="Below Quality Floor",
            protein_g=30,
        ),
    ]

    ranked = rank_food_suggestion_candidates(
        candidates,
        limit=3,
        macro_gaps=macro_gaps,
        rotation_key="quality-floor",
    )

    assert [candidate.canonical_food_id for candidate in ranked] == [1]


def test_catalog_fallback_requires_stronger_absolute_quality_than_curated_food():
    macro_gaps = _remaining_state_macro_gaps(
        calories=700,
        protein_g=20,
        carbohydrate_g=30,
        fat_g=8,
    )
    candidates = [
        _ranked_candidate(
            1,
            "calories",
            score=140,
            calories=220,
            display_name="Strong Catalog Energy Option",
            reason_codes=["catalog_fallback_serving_bounds"],
        ),
        _ranked_candidate(
            2,
            "calories",
            score=120,
            calories=220,
            display_name="Weak Catalog Novelty",
            reason_codes=["catalog_fallback_serving_bounds"],
        ),
        _ranked_candidate(
            3,
            "calories",
            score=90,
            calories=220,
            display_name="Curated Practical Option",
        ),
    ]

    ranked = rank_food_suggestion_candidates(
        candidates,
        limit=3,
        macro_gaps=macro_gaps,
        rotation_key="fallback-quality-floor",
    )

    assert {candidate.canonical_food_id for candidate in ranked} == {1, 3}


def test_normalized_remaining_gap_pressure_controls_macro_role_order():
    macro_gaps = _remaining_state_macro_gaps(
        calories=1500,
        protein_g=30,
        carbohydrate_g=80,
        fat_g=10,
    )
    candidates = [
        _ranked_candidate(1, "protein_g", score=100),
        _ranked_candidate(2, "carbohydrate_g", score=100),
        _ranked_candidate(3, "calories", score=100, calories=250),
        _ranked_candidate(4, "fat_g", score=100),
    ]

    ranked = rank_food_suggestion_candidates(
        candidates,
        limit=4,
        macro_gaps=macro_gaps,
        rotation_key="state-order-test",
    )

    assert [candidate.macro_gap_addressed for candidate in ranked] == [
        "calories",
        "carbohydrate_g",
        "protein_g",
        "fat_g",
    ]


def test_rotation_key_varies_equally_suitable_candidates_deterministically():
    candidates = [
        _ranked_candidate(candidate_id, "protein_g", score=100)
        for candidate_id in range(1, 7)
    ]

    first = rank_food_suggestion_candidates(
        candidates,
        limit=3,
        rotation_key="user-1|2026-06-06|state-a",
    )
    repeat = rank_food_suggestion_candidates(
        list(reversed(candidates)),
        limit=3,
        rotation_key="user-1|2026-06-06|state-a",
    )
    changed_state = rank_food_suggestion_candidates(
        candidates,
        limit=3,
        rotation_key="user-1|2026-06-07|state-b",
    )

    assert [candidate.canonical_food_id for candidate in first] == [
        candidate.canonical_food_id for candidate in repeat
    ]
    assert [candidate.canonical_food_id for candidate in first] != [
        candidate.canonical_food_id for candidate in changed_state
    ]


def test_ranking_skips_missing_macro_buckets_cleanly():
    candidates = [
        _ranked_candidate(1, "protein_g", score=100),
        _ranked_candidate(2, "protein_g", score=90),
        _ranked_candidate(3, "fat_g", score=100),
    ]

    ranked = rank_food_suggestion_candidates(candidates, limit=3)

    assert [candidate.canonical_food_id for candidate in ranked] == [1, 3, 2]


def test_ranking_returns_multiple_distinct_single_macro_alternatives():
    candidates = [
        _ranked_candidate(candidate_id, "protein_g", score=100 - candidate_id)
        for candidate_id in range(1, 10)
    ]

    ranked = rank_food_suggestion_candidates(candidates, limit=8)

    assert [candidate.canonical_food_id for candidate in ranked] == list(range(1, 9))


def test_ranking_deduplicates_canonical_foods_across_macro_roles():
    candidates = [
        _ranked_candidate(1, "protein_g", score=100),
        _ranked_candidate(1, "carbohydrate_g", score=100),
        _ranked_candidate(2, "carbohydrate_g", score=90),
    ]

    ranked = rank_food_suggestion_candidates(candidates, limit=3)

    assert [candidate.canonical_food_id for candidate in ranked] == [1, 2]
    assert [candidate.macro_gap_addressed for candidate in ranked] == [
        "protein_g",
        "carbohydrate_g",
    ]


def test_no_forbidden_language_appears(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)

    approved = build_approved_nutrition_food_suggestions(
        1,
        "2026-06-06",
        target_vs_actual_summary=summary,
    )
    text = " ".join(
        [suggestion.suggestion_summary for suggestion in approved.suggestions]
        + approved.reason_codes
        + approved.limitations
    ).lower()

    forbidden_terms = [
        "you must eat",
        "you failed",
        "burn this off",
        "skip meals",
        "compensate tomorrow",
        "fat-loss guarantee",
        "exact physiological certainty",
    ]
    assert not any(term in text for term in forbidden_terms)


def test_approve_food_suggestions_can_represent_no_suitable_food(tmp_path, monkeypatch):
    summary = _protein_gap_summary(tmp_path, monkeypatch)
    gaps = build_nutrition_macro_gaps(summary)

    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=gaps,
        candidates=[],
        summary_confidence=summary.confidence,
    )

    assert approved.suggestions == []
    assert "no_suitable_canonical_food_found" in approved.reason_codes
    assert approved.limitations


def _fat_gap_macro_gaps(
    *,
    fat_display_allowed: bool = True,
    calorie_display_allowed: bool = True,
    calorie_status: str = "near_target",
    logging_conflict_macro: str | None = None,
) -> list[NutritionMacroGap]:
    return [
        _macro_gap(
            "protein_g",
            target_status=(
                "above_target"
                if logging_conflict_macro == "protein_g"
                else "near_target"
            ),
            gap_value=None,
        ),
        _macro_gap(
            "calories",
            target_status=(calorie_status if calorie_display_allowed else "limited"),
            display_allowed=calorie_display_allowed,
            gap_value=(
                250
                if calorie_status == "below_target" and calorie_display_allowed
                else None
            ),
            reason_codes=(
                ["calorie_gap_available"]
                if calorie_status == "below_target" and calorie_display_allowed
                else (["target_not_approved"] if not calorie_display_allowed else [])
            ),
            limitations=[] if calorie_display_allowed else ["Target is limited."],
        ),
        _macro_gap(
            "carbohydrate_g",
            target_status=(
                "above_target"
                if logging_conflict_macro == "carbohydrate_g"
                else "near_target"
            ),
            gap_value=None,
        ),
        _macro_gap(
            "fat_g",
            target_status="below_target" if fat_display_allowed else "limited",
            display_allowed=fat_display_allowed,
            gap_value=(20 if fat_display_allowed else None),
            reason_codes=(
                ["fat_gap_available"]
                if fat_display_allowed
                else ["target_not_approved"]
            ),
            limitations=[] if fat_display_allowed else ["Target is limited."],
        ),
    ]


def test_existing_calorie_support_suggestions_still_work_after_fat_expansion(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _calorie_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.primary_gap == "calories"
    assert approved.suggestions
    assert all(
        suggestion.macro_gap_addressed == "calories"
        for suggestion in approved.suggestions
    )


def test_approved_fat_gap_produces_canonical_fat_support_suggestions(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _fat_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.primary_gap == "fat_g"
    assert approved.suggestions
    assert "fat_gap_available" in approved.reason_codes
    assert "fat_support_suggestion_available" in approved.reason_codes
    assert all(
        suggestion.macro_gap_addressed == "fat_g" for suggestion in approved.suggestions
    )
    assert all(suggestion.canonical_food_id > 0 for suggestion in approved.suggestions)


def test_fat_support_suggestions_use_canonical_nutrients_and_practical_servings(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _fat_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    for suggestion in approved.suggestions:
        assert suggestion.estimated_calories is not None
        assert suggestion.estimated_calories >= 0
        assert suggestion.estimated_protein_g is not None
        assert suggestion.estimated_protein_g >= 0
        assert suggestion.estimated_carbohydrate_g is not None
        assert suggestion.estimated_carbohydrate_g >= 0
        assert suggestion.estimated_fat_g is not None
        assert suggestion.estimated_fat_g > 0
        assert suggestion.suggested_grams > 0
        if suggestion.display_name in {"Olive Oil", "Avocado Oil", "Butter"}:
            assert 5 <= suggestion.suggested_grams <= 15
        if suggestion.display_name in {"Peanut Butter", "Almond Butter"}:
            assert 16 <= suggestion.suggested_grams <= 32
        if suggestion.display_name in {"Almonds", "Walnuts", "Cashews"}:
            assert 15 <= suggestion.suggested_grams <= 30
        if suggestion.display_name == "Avocado":
            assert 50 <= suggestion.suggested_grams <= 100
        if "Cheese" in suggestion.display_name:
            assert 15 <= suggestion.suggested_grams <= 40
        if suggestion.display_name == "Whole Egg":
            assert 50 <= suggestion.suggested_grams <= 100


def test_fat_target_blocked_produces_no_fat_support_suggestions():
    macro_gaps = _fat_gap_macro_gaps(fat_display_allowed=False)

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert "fat_support_suggestion_limited" in approved.reason_codes
    assert any("fat target" in limitation for limitation in approved.limitations)


def test_calorie_target_blocked_produces_no_fat_support_suggestions():
    macro_gaps = _fat_gap_macro_gaps(calorie_display_allowed=False)

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert "fat_support_suggestion_limited" in approved.reason_codes
    assert any("calorie target" in limitation for limitation in approved.limitations)


def test_incomplete_logging_limits_fat_support_suggestions():
    macro_gaps = _fat_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=True,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Low",
        logging_incomplete=True,
    )

    assert approved.suggestions == []
    assert "logging_incomplete_limits_suggestions" in approved.reason_codes
    assert any("logging appears incomplete" in item for item in approved.limitations)


def test_calorie_above_target_conflict_blocks_fat_support_suggestions():
    macro_gaps = _fat_gap_macro_gaps(calorie_status="above_target")

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
    )

    assert approved.suggestions == []
    assert "fat_support_suggestion_limited" in approved.reason_codes
    assert "calorie_conflict_limits_fat_suggestions" in approved.reason_codes
    assert any(
        "calories are already above target" in item for item in approved.limitations
    )


def test_fat_support_ranking_is_deterministic(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _fat_gap_macro_gaps()
    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )

    first = rank_food_suggestion_candidates(candidates, limit=5)
    second = rank_food_suggestion_candidates(list(reversed(candidates)), limit=5)

    assert [candidate.canonical_food_id for candidate in first] == [
        candidate.canonical_food_id for candidate in second
    ]


def test_fat_support_does_not_suggest_excessive_oil_nut_or_cheese_servings(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    macro_gaps = _fat_gap_macro_gaps()

    candidates = get_canonical_food_suggestion_candidates(
        macro_gaps,
        logging_incomplete=False,
    )
    approved = approve_food_suggestions(
        user_id=1,
        suggestion_date="2026-06-06",
        macro_gaps=macro_gaps,
        candidates=candidates,
        summary_confidence="Moderate",
        limit=10,
    )

    assert approved.suggestions
    for suggestion in approved.suggestions:
        if suggestion.display_name in {"Olive Oil", "Avocado Oil", "Butter"}:
            assert suggestion.suggested_grams <= 15
        if suggestion.display_name in {
            "Almonds",
            "Walnuts",
            "Cashews",
            "Peanut Butter",
            "Almond Butter",
        }:
            assert suggestion.suggested_grams <= 32
        if "Cheese" in suggestion.display_name:
            assert suggestion.suggested_grams <= 40
