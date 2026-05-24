from dataclasses import dataclass, field


@dataclass
class NutritionTargets:
    body_weight_lb: float | None
    calorie_target_min: int | None
    calorie_target_max: int | None
    protein_grams_min: int | None
    protein_grams_max: int | None
    carbohydrate_grams_min: int | None
    carbohydrate_grams_max: int | None
    fat_grams_min: int | None
    fat_grams_max: int | None
    confidence: str
    reason_codes: list[str] = field(default_factory=list)
