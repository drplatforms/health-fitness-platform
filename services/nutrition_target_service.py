from models.nutrition_target_models import NutritionTargets
from models.user_state_models import UserHealthState


def _as_float(value) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _round_to_nearest_10(value: float) -> int:
    return int(round(value / 10.0) * 10)


def _goal_key(primary_goal: str) -> str:
    return primary_goal.lower().replace("/", "_").replace(" ", "_")


def _activity_multiplier(activity_level: str | None) -> float:
    activity = (activity_level or "").lower()
    if activity in {"high", "very_active", "very active"}:
        return 16.0
    if activity in {"low", "sedentary", "light"}:
        return 12.0
    return 14.0


def _goal_calorie_adjustment(primary_goal: str) -> tuple[float, float, str]:
    goal = _goal_key(primary_goal)
    if "fat_loss" in goal or "fat loss" in goal:
        return 0.85, 0.95, "fat_loss_adjustment"
    if "performance" in goal or "strength_progression" in goal:
        return 1.0, 1.08, "performance_or_strength_adjustment"
    if "recomposition" in goal or "recomp" in goal:
        return 0.95, 1.02, "recomposition_adjustment"
    return 0.95, 1.05, "general_goal_adjustment"


def _carb_factors(training_load: str) -> tuple[float, float, str]:
    if training_load == "High":
        return 1.5, 2.25, "high_training_carb_range"
    if training_load == "Moderate":
        return 1.0, 1.75, "moderate_training_carb_range"
    if training_load == "Low":
        return 0.75, 1.25, "low_training_carb_range"
    return 0.5, 1.0, "inactive_or_unknown_training_carb_range"


def build_nutrition_targets(health_state: UserHealthState) -> NutritionTargets:
    """Calculate transparent v1 nutrition target ranges from factual health state.

    These are planning ranges, not medical prescriptions. If body weight is missing,
    target grams/calories stay unavailable rather than being invented.
    """
    body_weight = _as_float(health_state.latest_body_weight) or _as_float(
        health_state.starting_weight
    )
    reason_codes: list[str] = []

    nutrition_state = health_state.nutrition_state
    incomplete_nutrition = (
        nutrition_state.calories == "Unknown"
        or nutrition_state.calorie_status == "Unknown"
        or nutrition_state.protein_status == "Unknown"
        or nutrition_state.carbohydrate_grams == "Unknown"
        or nutrition_state.fat_grams == "Unknown"
        or "Incomplete" in nutrition_state.recovery_nutrition_status
    )

    if body_weight is None:
        return NutritionTargets(
            body_weight_lb=None,
            calorie_target_min=None,
            calorie_target_max=None,
            protein_grams_min=None,
            protein_grams_max=None,
            carbohydrate_grams_min=None,
            carbohydrate_grams_max=None,
            fat_grams_min=None,
            fat_grams_max=None,
            confidence="Low",
            reason_codes=["missing_body_weight"],
        )

    activity_multiplier = _activity_multiplier(health_state.activity_level)
    goal_min, goal_max, goal_reason = _goal_calorie_adjustment(
        health_state.primary_goal
    )
    carb_min_factor, carb_max_factor, carb_reason = _carb_factors(
        health_state.training_state.training_load
    )

    base_calories = body_weight * activity_multiplier
    protein_min = _round_to_nearest_10(body_weight * 0.7)
    protein_max = _round_to_nearest_10(body_weight * 1.0)
    carbs_min = _round_to_nearest_10(body_weight * carb_min_factor)
    carbs_max = _round_to_nearest_10(body_weight * carb_max_factor)
    fat_min = _round_to_nearest_10(body_weight * 0.3)
    fat_max = _round_to_nearest_10(body_weight * 0.45)

    reason_codes.extend(
        [
            "body_weight_available",
            goal_reason,
            carb_reason,
            f"activity_level_{health_state.activity_level or 'unknown'}",
        ]
    )

    confidence = "Moderate"
    if not incomplete_nutrition and nutrition_state.has_nutrition_data:
        confidence = "High"
    else:
        reason_codes.append("nutrition_logging_incomplete")

    return NutritionTargets(
        body_weight_lb=round(body_weight, 1),
        calorie_target_min=_round_to_nearest_10(base_calories * goal_min),
        calorie_target_max=_round_to_nearest_10(base_calories * goal_max),
        protein_grams_min=protein_min,
        protein_grams_max=protein_max,
        carbohydrate_grams_min=carbs_min,
        carbohydrate_grams_max=carbs_max,
        fat_grams_min=fat_min,
        fat_grams_max=fat_max,
        confidence=confidence,
        reason_codes=reason_codes,
    )
