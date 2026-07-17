from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SavedMealFoodType = Literal["canonical", "personal"]


@dataclass(frozen=True)
class SavedMealItemInput:
    food_type: SavedMealFoodType | str
    canonical_food_id: int | None = None
    personal_food_id: int | None = None
    grams: float | None = None
    serving_unit_id: int | None = None
    serving_quantity: float | None = None
    personal_serving_quantity: float | None = None


@dataclass(frozen=True)
class SavedMealMutationInput:
    display_name: str
    default_meal_type: str | None = None
    items: tuple[SavedMealItemInput, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SavedMealItem:
    id: int
    item_order: int
    food_type: SavedMealFoodType
    canonical_food_id: int | None
    personal_food_id: int | None
    display_name: str
    active: bool
    resolved_grams: float
    canonical_serving_unit_id: int | None
    serving_quantity: float | None
    serving_display_snapshot: str | None
    amount_source: str
    validation_status: str
    validation_reason: str | None
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SavedMeal:
    id: int
    user_id: int
    display_name: str
    default_meal_type: str | None
    active: bool
    created_at: str
    updated_at: str
    items: tuple[SavedMealItem, ...]
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    validation_status: str
    invalid_item_count: int

    @property
    def item_count(self) -> int:
        return len(self.items)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "default_meal_type": self.default_meal_type,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "item_count": self.item_count,
            "items": [item.to_public_dict() for item in self.items],
            "current_macros": {
                "calories": self.calories,
                "protein_g": self.protein_g,
                "carbs_g": self.carbs_g,
                "fat_g": self.fat_g,
            },
            "validation_status": self.validation_status,
            "invalid_item_count": self.invalid_item_count,
        }
