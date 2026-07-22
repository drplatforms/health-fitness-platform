from __future__ import annotations

import pytest

from models.measurement_display_models import TrustedQuantityMeasure
from services.measurement_display_service import (
    GRAMS_PER_OUNCE,
    GRAMS_PER_POUND,
    grams_to_ounces,
    grams_to_pounds,
    present_food_quantity,
)


def _measure(
    unit_name: str,
    grams: float,
    *,
    unit_quantity: float = 1,
    confidence: str = "High",
) -> TrustedQuantityMeasure:
    return TrustedQuantityMeasure(
        unit_name=unit_name,
        unit_quantity=unit_quantity,
        grams=grams,
        confidence=confidence,
        source="unit_test_catalog_measure",
        serving_unit_id=7,
    )


def test_exact_mass_conversion_constants_are_not_display_rounded() -> None:
    assert grams_to_ounces(GRAMS_PER_OUNCE) == pytest.approx(1)
    assert grams_to_pounds(GRAMS_PER_POUND) == pytest.approx(1)
    assert grams_to_ounces(85) == pytest.approx(2.998286, rel=1e-6)


def test_food_specific_household_measure_is_primary_with_canonical_grams() -> None:
    presentation = present_food_quantity(
        grams=185,
        trusted_measures=(_measure("cup", 180),),
    )

    assert presentation.display_text == "1 cup (185 g)"
    assert presentation.canonical_grams == 185
    assert presentation.conversion_source == "food_specific_measure"
    assert presentation.source == "unit_test_catalog_measure"


def test_food_specific_count_measure_pluralizes_naturally() -> None:
    presentation = present_food_quantity(
        grams=6,
        trusted_measures=(_measure("clove", 3),),
    )

    assert presentation.display_text == "2 cloves (6 g)"


def test_no_generic_grams_to_cups_conversion_and_safe_gram_fallback() -> None:
    presentation = present_food_quantity(grams=14, trusted_measures=())

    assert presentation.display_text == "14 g"
    assert presentation.primary_unit == "g"
    assert presentation.conversion_source == "grams_fallback"


def test_low_confidence_household_measure_is_not_presented_as_trusted() -> None:
    presentation = present_food_quantity(
        grams=180,
        trusted_measures=(_measure("cup", 180, confidence="Low"),),
    )

    assert "cup" not in presentation.display_text
    assert presentation.conversion_source in {
        "exact_mass_conversion",
        "grams_fallback",
    }


def test_exact_mass_fallback_uses_practical_ounces_and_pounds() -> None:
    ounces = present_food_quantity(grams=85, trusted_measures=())
    pounds = present_food_quantity(grams=680, trusted_measures=())

    assert ounces.display_text == "3 oz (85 g)"
    assert pounds.display_text == "1.5 lb (680 g)"
    assert (
        ounces.conversion_source == pounds.conversion_source == "exact_mass_conversion"
    )


def test_practical_fraction_rounding_does_not_change_canonical_grams() -> None:
    presentation = present_food_quantity(
        grams=137.25,
        trusted_measures=(_measure("cup", 180),),
    )

    assert presentation.display_text == "3/4 cup (137.25 g)"
    assert presentation.canonical_grams == 137.25
    assert presentation.secondary_grams == 137.25


def test_misleading_household_rounding_degrades_to_safe_mass_display() -> None:
    presentation = present_food_quantity(
        grams=60,
        trusted_measures=(_measure("large egg", 50),),
    )

    assert presentation.conversion_source in {
        "exact_mass_conversion",
        "grams_fallback",
    }
    assert "large egg" not in presentation.display_text


def test_display_selection_never_changes_nutrition_math() -> None:
    grams = 185.0
    calories_per_100g = 130.0
    canonical_calories = calories_per_100g * grams / 100

    presentation = present_food_quantity(
        grams=grams,
        trusted_measures=(_measure("cup", 180),),
    )

    assert calories_per_100g * presentation.canonical_grams / 100 == pytest.approx(
        canonical_calories
    )
