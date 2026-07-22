from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.ai_run_models import AIRunTelemetry


@dataclass(frozen=True)
class GroundedRecipeIngredient:
    canonical_food_id: int | None
    personal_food_id: int | None
    display_name: str
    amount_grams: float


@dataclass(frozen=True)
class MealInstructionGenerationRequest:
    provider: str
    model: str | None
    meal_name: str
    ingredients: tuple[GroundedRecipeIngredient, ...]


@dataclass(frozen=True)
class MealInstructionResult:
    provider: str
    model: str
    instructions: tuple[str, ...]
    telemetry: AIRunTelemetry

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "success": True,
            "provider": self.provider,
            "model": self.model,
            "instructions": list(self.instructions),
            "telemetry": self.telemetry.to_public_dict(),
        }
