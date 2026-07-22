from __future__ import annotations

from collections.abc import Iterable
from fractions import Fraction
from math import isfinite

from models.measurement_display_models import (
    QuantityPresentation,
    TrustedQuantityMeasure,
)
from models.nutrition_serving_unit_models import NutritionServingUnit

GRAMS_PER_OUNCE = 28.349523125
GRAMS_PER_POUND = 453.59237

_TRUSTED_CONFIDENCE = {"High", "Moderate"}
_VOLUME_TOKENS = ("cup", "tablespoon", "teaspoon", "tbsp", "tsp")
_MASS_OR_GENERIC_UNITS = {
    "g",
    "gram",
    "grams",
    "oz",
    "ounce",
    "ounces",
    "oz serving",
    "lb",
    "lbs",
    "pound",
    "pounds",
    "serving",
    "portion",
}


def grams_to_ounces(grams: float) -> float:
    return _positive_grams(grams) / GRAMS_PER_OUNCE


def grams_to_pounds(grams: float) -> float:
    return _positive_grams(grams) / GRAMS_PER_POUND


def serving_unit_as_measure(unit: NutritionServingUnit) -> TrustedQuantityMeasure:
    return TrustedQuantityMeasure(
        unit_name=unit.unit_name,
        unit_quantity=unit.unit_quantity,
        grams=unit.grams_default,
        confidence=unit.confidence,
        source=unit.source,
        source_note=unit.source_note,
        serving_unit_id=unit.id,
        sort_order=unit.sort_order,
    )


def present_food_quantity(
    *,
    grams: float,
    canonical_food_id: int | None = None,
    trusted_measures: Iterable[TrustedQuantityMeasure] | None = None,
    prefer_household: bool = True,
) -> QuantityPresentation:
    """Build display-only quantity text without changing canonical grams."""

    canonical_grams = _positive_grams(grams)
    measures = list(trusted_measures or ())
    if trusted_measures is None and canonical_food_id is not None:
        from services.nutrition_serving_unit_service import (
            get_active_serving_units_for_canonical_food,
        )

        measures = [
            serving_unit_as_measure(unit)
            for unit in get_active_serving_units_for_canonical_food(canonical_food_id)
        ]

    if prefer_household:
        household = _household_presentation(canonical_grams, measures)
        if household is not None:
            return household

    mass = _mass_presentation(canonical_grams)
    if mass is not None:
        return mass
    return _grams_presentation(canonical_grams)


def _household_presentation(
    grams: float,
    measures: list[TrustedQuantityMeasure],
) -> QuantityPresentation | None:
    candidates: list[tuple[float, int, QuantityPresentation]] = []
    for measure in sorted(measures, key=lambda item: (item.sort_order, item.unit_name)):
        normalized_unit = " ".join(measure.unit_name.strip().lower().split())
        if (
            not normalized_unit
            or normalized_unit in _MASS_OR_GENERIC_UNITS
            or measure.confidence.title() not in _TRUSTED_CONFIDENCE
            or not isfinite(measure.unit_quantity)
            or not isfinite(measure.grams)
            or measure.unit_quantity <= 0
            or measure.grams <= 0
        ):
            continue
        raw_quantity = grams * measure.unit_quantity / measure.grams
        is_volume = any(token in normalized_unit for token in _VOLUME_TOKENS)
        rounded_quantity, denominator = _practical_household_quantity(
            raw_quantity,
            is_volume=is_volume,
        )
        if rounded_quantity is None:
            continue
        represented_grams = rounded_quantity * measure.grams / measure.unit_quantity
        relative_error = abs(represented_grams - grams) / grams
        if relative_error > 0.06:
            continue

        quantity_text = _format_fraction(rounded_quantity)
        unit_text = _display_unit(normalized_unit, rounded_quantity)
        primary_text = f"{quantity_text} {unit_text}"
        secondary_text = f"{_format_grams(grams)} g"
        complexity_penalty = {1: 0.0, 2: 0.001, 4: 0.002, 3: 0.003, 8: 0.004}.get(
            denominator,
            0.005,
        )
        presentation = QuantityPresentation(
            canonical_grams=grams,
            primary_quantity=quantity_text,
            primary_unit=unit_text,
            primary_text=primary_text,
            secondary_grams=grams,
            secondary_text=secondary_text,
            display_text=f"{primary_text} ({secondary_text})",
            conversion_source="food_specific_measure",
            reliability=measure.confidence.title(),
            source=measure.source,
            source_note=measure.source_note,
            serving_unit_id=measure.serving_unit_id,
        )
        candidates.append(
            (relative_error + complexity_penalty, measure.sort_order, presentation)
        )

    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def _mass_presentation(grams: float) -> QuantityPresentation | None:
    pounds = grams_to_pounds(grams)
    if pounds >= 1:
        rounded_pounds = round(pounds * 4) / 4
        if rounded_pounds > 0 and abs(rounded_pounds - pounds) / pounds <= 0.03:
            return _converted_mass_presentation(grams, rounded_pounds, "lb")

    ounces = grams_to_ounces(grams)
    if ounces >= 1:
        rounded_ounces = round(ounces * 4) / 4
        if rounded_ounces > 0 and abs(rounded_ounces - ounces) / ounces <= 0.03:
            return _converted_mass_presentation(grams, rounded_ounces, "oz")
    return None


def _converted_mass_presentation(
    grams: float,
    quantity: float,
    unit: str,
) -> QuantityPresentation:
    quantity_text = _format_decimal(quantity)
    primary_text = f"{quantity_text} {unit}"
    secondary_text = f"{_format_grams(grams)} g"
    return QuantityPresentation(
        canonical_grams=grams,
        primary_quantity=quantity_text,
        primary_unit=unit,
        primary_text=primary_text,
        secondary_grams=grams,
        secondary_text=secondary_text,
        display_text=f"{primary_text} ({secondary_text})",
        conversion_source="exact_mass_conversion",
        reliability="Exact",
        source="NIST_mass_conversion",
    )


def _grams_presentation(grams: float) -> QuantityPresentation:
    quantity_text = _format_grams(grams)
    primary_text = f"{quantity_text} g"
    return QuantityPresentation(
        canonical_grams=grams,
        primary_quantity=quantity_text,
        primary_unit="g",
        primary_text=primary_text,
        secondary_grams=None,
        secondary_text=None,
        display_text=primary_text,
        conversion_source="grams_fallback",
        reliability="Canonical",
    )


def _practical_household_quantity(
    quantity: float,
    *,
    is_volume: bool,
) -> tuple[float | None, int]:
    if not isfinite(quantity) or quantity < 0.125:
        return None, 1
    denominators = (1, 2, 4, 3, 8) if is_volume else (1, 2)
    options: list[tuple[float, int, float]] = []
    for denominator in denominators:
        rounded = round(quantity * denominator) / denominator
        if rounded <= 0:
            continue
        relative_error = abs(rounded - quantity) / quantity
        options.append((relative_error, denominator, rounded))
    if not options:
        return None, 1
    _, denominator, rounded = min(
        options,
        key=lambda item: (item[0], denominators.index(item[1])),
    )
    return rounded, denominator


def _format_fraction(value: float) -> str:
    fraction = Fraction(value).limit_denominator(8)
    whole, remainder = divmod(fraction.numerator, fraction.denominator)
    if remainder == 0:
        return str(whole)
    fraction_text = f"{remainder}/{fraction.denominator}"
    return f"{whole} {fraction_text}" if whole else fraction_text


def _display_unit(unit_name: str, quantity: float) -> str:
    aliases = {
        "tablespoon": ("tbsp", "tbsp"),
        "tablespoons": ("tbsp", "tbsp"),
        "teaspoon": ("tsp", "tsp"),
        "teaspoons": ("tsp", "tsp"),
        "cup": ("cup", "cups"),
        "cup dry": ("cup dry", "cups dry"),
    }
    singular, plural = aliases.get(unit_name, (unit_name, _pluralize(unit_name)))
    return singular if quantity <= 1 else plural


def _pluralize(unit_name: str) -> str:
    if unit_name.endswith("s"):
        return unit_name
    if unit_name.endswith(("potato", "tomato")):
        return f"{unit_name}es"
    if unit_name.endswith("y") and len(unit_name) > 1:
        return f"{unit_name[:-1]}ies"
    return f"{unit_name}s"


def _format_grams(grams: float) -> str:
    return _format_decimal(round(grams, 2))


def _format_decimal(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _positive_grams(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("grams must be a positive number.")
    resolved = float(value)
    if not isfinite(resolved) or resolved <= 0:
        raise ValueError("grams must be a positive number.")
    return resolved
