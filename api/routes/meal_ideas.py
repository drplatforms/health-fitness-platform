from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.meal_idea_models import MealIdeaGenerationRequest
from services.meal_idea_model_service import build_meal_idea_model_options
from services.meal_idea_service import (
    MealIdeaError,
    MealIdeaProviderError,
    MealIdeaUserNotFoundError,
    generate_meal_ideas,
)

router = APIRouter()


class MealIdeasRequest(BaseModel):
    provider: str
    model: str | None = Field(default=None, max_length=200)
    creative_steering: str = "surprise_me"
    meal_type: str | None = None
    intent: str | None = Field(default=None, max_length=240)
    generation_nonce: str | None = Field(default=None, max_length=100)
    previous_idea_names: list[str] = Field(default_factory=list, max_length=20)
    recent_generated_food_names: list[str] = Field(default_factory=list, max_length=40)


@router.get("/nutrition/meal-ideas/model-options")
def meal_idea_model_options():
    return build_meal_idea_model_options()


@router.post("/nutrition/{user_id}/meal-ideas")
def create_meal_ideas(user_id: int, target_date: str, request: MealIdeasRequest):
    try:
        result = generate_meal_ideas(
            user_id=user_id,
            target_date=target_date,
            request=MealIdeaGenerationRequest(
                provider=request.provider.strip().lower(),
                model=request.model.strip() if request.model else None,
                creative_steering=request.creative_steering.strip().lower(),
                meal_type=(
                    request.meal_type.strip().lower() if request.meal_type else None
                ),
                intent=request.intent.strip() if request.intent else None,
                generation_nonce=request.generation_nonce,
                previous_idea_names=tuple(request.previous_idea_names),
                recent_generated_food_names=tuple(request.recent_generated_food_names),
            ),
        )
    except MealIdeaUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MealIdeaProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": exc.code, "message": exc.public_message},
        ) from exc
    except MealIdeaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_public_dict()
