from __future__ import annotations

import pytest

import database
from models.ai_run_models import AIRunTelemetry
from models.meal_idea_models import (
    GroundedMealIdea,
    GroundedMealIngredient,
    MealIdeaGenerationRequest,
    MealIdeasResult,
)
from services.meal_idea_history_service import (
    list_generation_sets,
    persist_successful_generation,
)
from services.meal_idea_service import MealIdeaProviderError, generate_meal_ideas


@pytest.fixture
def history_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "meal_idea_history.db")
    database.initialize_database()


def _request() -> MealIdeaGenerationRequest:
    return MealIdeaGenerationRequest(
        provider="openai",
        model="gpt-5.4-mini",
        creative_steering="savory",
        meal_type="dinner",
        intent="A quick skillet meal",
        generation_nonce="ephemeral-nonce",
        previous_idea_names=("Older Idea",),
        recent_generated_food_names=("Older Food",),
    )


def _result(name: str) -> MealIdeasResult:
    ingredient = GroundedMealIngredient(
        canonical_food_id=42,
        display_name="Grounded Chicken",
        amount_grams=137.25,
        is_available=True,
        calories=274.5,
        protein_g=41.2,
        carbs_g=0.0,
        fat_g=11.0,
    )
    idea = GroundedMealIdea(
        name=name,
        meal_type="dinner",
        ingredients=(ingredient,),
        calories=274.5,
        protein_g=41.2,
        carbs_g=0.0,
        fat_g=11.0,
        available_ingredient_count=1,
    )
    return MealIdeasResult(
        provider="openai",
        model="gpt-5.4-mini-2026-03-17",
        target_date="2026-07-21",
        ideas=(idea,),
        rejected_concept_count=2,
        context_signals={
            "usable_catalog_food_count": 20,
            "available_ingredient_count": 4,
            "food_preference_count": 3,
            "recent_food_count": 5,
            "nutrition_context_available": False,
        },
        telemetry=AIRunTelemetry(
            provider="openai",
            model="gpt-5.4-mini-2026-03-17",
            runtime_seconds=1.25,
            input_tokens=1_000,
            cached_input_tokens=200,
            output_tokens=300,
            estimated_api_cost_usd=0.00042,
            pricing_version="2026-07-21",
        ),
    )


def test_generation_history_round_trips_exact_grounded_result_and_run_metadata(
    history_db,
) -> None:
    request = _request()
    result = _result("Exact Grounded Dinner")

    persisted = persist_successful_generation(
        user_id=1,
        selected_model="gpt-5.4-mini",
        request=request,
        result=result,
    )
    restored = list_generation_sets(user_id=1)

    assert restored == [persisted]
    assert restored[0].result == result.to_public_dict()
    assert restored[0].request == {
        "provider": "openai",
        "model": "gpt-5.4-mini",
        "creative_steering": "savory",
        "meal_type": "dinner",
        "intent": "A quick skillet meal",
    }
    assert restored[0].result["model"] == "gpt-5.4-mini-2026-03-17"
    assert restored[0].result["ideas"][0]["ingredients"][0] == {
        "canonical_food_id": 42,
        "display_name": "Grounded Chicken",
        "amount_grams": 137.25,
        "is_available": True,
        "calories": 274.5,
        "protein_g": 41.2,
        "carbs_g": 0.0,
        "fat_g": 11.0,
    }
    assert restored[0].result["telemetry"]["estimated_api_cost_usd"] == 0.00042


def test_generation_history_retains_latest_five_per_user_in_newest_first_order(
    history_db,
) -> None:
    request = _request()
    for index in range(6):
        persist_successful_generation(
            user_id=1,
            selected_model="gpt-5.4-mini",
            request=request,
            result=_result(f"User One Run {index}"),
        )
    persist_successful_generation(
        user_id=2,
        selected_model="gpt-5.4-mini",
        request=request,
        result=_result("User Two Only Run"),
    )

    user_one = list_generation_sets(user_id=1)
    user_two = list_generation_sets(user_id=2)

    assert [entry.result["ideas"][0]["name"] for entry in user_one] == [
        "User One Run 5",
        "User One Run 4",
        "User One Run 3",
        "User One Run 2",
        "User One Run 1",
    ]
    assert [entry.result["ideas"][0]["name"] for entry in user_two] == [
        "User Two Only Run"
    ]


def test_failed_generation_is_not_added_to_history(history_db) -> None:
    def fail_provider(*args):
        del args
        raise RuntimeError("provider failed")

    with pytest.raises(MealIdeaProviderError):
        generate_meal_ideas(
            user_id=1,
            target_date="2026-07-21",
            request=_request(),
            openai_generate=fail_provider,
        )

    assert list_generation_sets(user_id=1) == []
