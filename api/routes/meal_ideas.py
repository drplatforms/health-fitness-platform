from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.meal_idea_models import MealIdeaGenerationRequest
from models.meal_instruction_models import (
    GroundedRecipeIngredient,
    MealInstructionGenerationRequest,
)
from services.meal_idea_history_service import (
    MealIdeaHistoryUserNotFoundError,
    MealIdeaHistoryValidationError,
    list_generation_sets,
)
from services.meal_idea_model_service import build_meal_idea_model_options
from services.meal_idea_service import (
    MealIdeaError,
    MealIdeaProviderError,
    MealIdeaUserNotFoundError,
    generate_meal_ideas,
)
from services.meal_instruction_service import (
    MealInstructionError,
    MealInstructionProviderError,
    MealInstructionUserNotFoundError,
    generate_and_save_cooking_instructions,
    generate_cooking_instructions,
)
from services.saved_meal_service import (
    SavedMealNotFoundError,
    SavedMealValidationError,
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


class GroundedRecipeIngredientRequest(BaseModel):
    canonical_food_id: int | None = None
    personal_food_id: int | None = None
    display_name: str = Field(max_length=120)
    amount_grams: float


class MealInstructionsRequest(BaseModel):
    provider: str
    model: str | None = Field(default=None, max_length=200)
    meal_name: str = Field(max_length=120)
    ingredients: list[GroundedRecipeIngredientRequest] = Field(
        min_length=1, max_length=50
    )


class SavedMealInstructionsRequest(BaseModel):
    provider: str
    model: str | None = Field(default=None, max_length=200)


@router.get("/nutrition/meal-ideas/model-options")
def meal_idea_model_options():
    return build_meal_idea_model_options()


@router.get("/nutrition/{user_id}/meal-ideas/history")
def meal_idea_generation_history(user_id: int):
    try:
        generation_sets = list_generation_sets(user_id=user_id)
    except MealIdeaHistoryUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MealIdeaHistoryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "user_id": user_id,
        "results": [
            generation_set.to_public_dict() for generation_set in generation_sets
        ],
    }


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


@router.post("/nutrition/{user_id}/meal-instructions")
def create_meal_instructions(user_id: int, request: MealInstructionsRequest):
    try:
        result = generate_cooking_instructions(
            user_id=user_id,
            request=MealInstructionGenerationRequest(
                provider=request.provider,
                model=request.model,
                meal_name=request.meal_name,
                ingredients=tuple(
                    GroundedRecipeIngredient(
                        canonical_food_id=item.canonical_food_id,
                        personal_food_id=item.personal_food_id,
                        display_name=item.display_name,
                        amount_grams=item.amount_grams,
                    )
                    for item in request.ingredients
                ),
            ),
        )
    except MealInstructionUserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MealInstructionProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": exc.code, "message": exc.public_message},
        ) from exc
    except MealInstructionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_public_dict()


@router.post("/nutrition/{user_id}/saved-meals/{saved_meal_id}/instructions")
def create_saved_meal_instructions(
    user_id: int,
    saved_meal_id: int,
    request: SavedMealInstructionsRequest,
):
    try:
        result, saved_meal = generate_and_save_cooking_instructions(
            user_id=user_id,
            saved_meal_id=saved_meal_id,
            provider=request.provider,
            model=request.model,
        )
    except (MealInstructionUserNotFoundError, SavedMealNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MealInstructionProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": exc.code, "message": exc.public_message},
        ) from exc
    except (MealInstructionError, SavedMealValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    payload = result.to_public_dict()
    payload["saved_meal"] = saved_meal.to_public_dict()
    return payload
