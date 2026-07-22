from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from models.ai_run_models import AIRunTelemetry
from models.measurement_display_models import QuantityPresentation

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
    cooking_instructions: tuple[str, ...] | None = None
    instruction_telemetry: AIRunTelemetry | None = None
    source_type: str | None = None
    source_provider: str | None = None
    source_model: str | None = None


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
    quantity_display: QuantityPresentation
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
        payload = asdict(self)
        payload["quantity_display"] = self.quantity_display.to_public_dict()
        return payload


@dataclass(frozen=True)
class SavedMeal:
    id: int
    user_id: int
    display_name: str
    default_meal_type: str | None
    active: bool
    created_at: str
    updated_at: str
    cooking_instructions: tuple[str, ...]
    instruction_telemetry: AIRunTelemetry | None
    source_type: str
    source_provider: str | None
    source_model: str | None
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
            "cooking_instructions": list(self.cooking_instructions),
            "instruction_telemetry": (
                self.instruction_telemetry.to_public_dict()
                if self.instruction_telemetry is not None
                else None
            ),
            "source_type": self.source_type,
            "source_provider": self.source_provider,
            "source_model": self.source_model,
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
