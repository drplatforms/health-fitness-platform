from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from models.ai_run_models import AIRunTelemetry
from models.measurement_display_models import QuantityPresentation

MEAL_IDEA_PROVIDERS = ("local", "openai")
MEAL_IDEA_STEERING_OPTIONS = (
    "sweet",
    "savory",
    "quick",
    "high_volume",
    "comfort",
    "light_fresh",
    "portable",
    "surprise_me",
)
MEAL_IDEA_MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack", "dessert")


@dataclass(frozen=True)
class MealIdeaGenerationRequest:
    provider: str
    model: str | None = None
    creative_steering: str = "surprise_me"
    meal_type: str | None = None
    intent: str | None = None
    generation_nonce: str | None = None
    previous_idea_names: tuple[str, ...] = ()
    recent_generated_food_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProposedMealIngredient:
    name: str
    amount_grams: float


@dataclass(frozen=True)
class ProposedMealIdea:
    name: str
    meal_type: str
    ingredients: tuple[ProposedMealIngredient, ...]


@dataclass(frozen=True)
class GroundedMealIngredient:
    canonical_food_id: int
    display_name: str
    amount_grams: float
    is_available: bool
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    quantity_display: QuantityPresentation | None = None

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        quantity_display = self.quantity_display
        if quantity_display is None:
            from services.measurement_display_service import present_food_quantity

            quantity_display = present_food_quantity(
                canonical_food_id=self.canonical_food_id,
                grams=self.amount_grams,
            )
        payload["quantity_display"] = quantity_display.to_public_dict()
        return payload


@dataclass(frozen=True)
class GroundedMealIdea:
    name: str
    meal_type: str
    ingredients: tuple[GroundedMealIngredient, ...]
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    available_ingredient_count: int

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ingredients"] = [
            ingredient.to_public_dict() for ingredient in self.ingredients
        ]
        return payload


@dataclass(frozen=True)
class MealIdeasResult:
    provider: str
    model: str
    target_date: str
    ideas: tuple[GroundedMealIdea, ...]
    rejected_concept_count: int = 0
    context_signals: dict[str, Any] = field(default_factory=dict)
    telemetry: AIRunTelemetry | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "success": True,
            "provider": self.provider,
            "model": self.model,
            "target_date": self.target_date,
            "ideas": [idea.to_public_dict() for idea in self.ideas],
            "rejected_concept_count": self.rejected_concept_count,
            "context_signals": dict(self.context_signals),
            "telemetry": (
                self.telemetry.to_public_dict() if self.telemetry is not None else None
            ),
        }
