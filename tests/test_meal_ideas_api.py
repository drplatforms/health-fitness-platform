from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from api.routes import meal_ideas as meal_ideas_route
from models.ai_run_models import AIRunTelemetry
from models.meal_idea_models import (
    GroundedMealIdea,
    GroundedMealIngredient,
    MealIdeaGenerationRequest,
    MealIdeasResult,
)
from models.meal_instruction_models import MealInstructionResult
from services.meal_idea_history_service import persist_successful_generation
from services.meal_idea_service import MealIdeaProviderError


def test_meal_ideas_api_preserves_explicit_provider_selection(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "meal_ideas_api.db")
    database.initialize_database()
    selected: list[str] = []

    def fake_generate(*, user_id, target_date, request):
        assert user_id == 1
        assert request.previous_idea_names == ("Previous Plate",)
        assert request.recent_generated_food_names == ("Recent Ingredient",)
        selected.append(f"{request.provider}:{request.model}")
        return MealIdeasResult(
            provider=request.provider,
            model=f"{request.provider}-model",
            target_date=target_date,
            ideas=(),
        )

    monkeypatch.setattr(meal_ideas_route, "generate_meal_ideas", fake_generate)
    with TestClient(app) as client:
        for provider in ("local", "openai"):
            response = client.post(
                "/nutrition/1/meal-ideas?target_date=2026-07-21",
                json={
                    "provider": provider,
                    "model": f"{provider}-selected-model",
                    "creative_steering": "quick",
                    "previous_idea_names": ["Previous Plate"],
                    "recent_generated_food_names": ["Recent Ingredient"],
                },
            )
            assert response.status_code == 200
            assert response.json()["provider"] == provider

    assert selected == [
        "local:local-selected-model",
        "openai:openai-selected-model",
    ]


def test_meal_ideas_model_options_api_uses_provider_boundary(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "meal_idea_models_api.db")
    database.initialize_database()
    expected = {
        "providers": {
            "local": {
                "models": [{"id": "qwen3:8b", "label": "qwen3:8b"}],
                "default_model": "qwen3:8b",
                "source": "ollama",
                "message": None,
            },
            "openai": {
                "models": [{"id": "gpt-5.4-mini", "label": "gpt-5.4-mini"}],
                "default_model": "gpt-5.4-mini",
                "source": "curated",
                "message": None,
            },
        }
    }
    monkeypatch.setattr(
        meal_ideas_route,
        "build_meal_idea_model_options",
        lambda: expected,
    )
    with TestClient(app) as client:
        response = client.get("/nutrition/meal-ideas/model-options")

    assert response.status_code == 200
    assert response.json() == expected


def test_meal_idea_history_api_restores_latest_user_owned_generation(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "meal_ideas_history_api.db")
    database.initialize_database()
    request = MealIdeaGenerationRequest(
        provider="openai",
        model="gpt-5.4-mini",
        creative_steering="quick",
        meal_type="lunch",
        intent="Fast lunch",
    )
    ingredient = GroundedMealIngredient(
        canonical_food_id=7,
        display_name="History Chicken",
        amount_grams=150,
        is_available=False,
        calories=300,
        protein_g=45,
        carbs_g=0,
        fat_g=12,
    )
    result = MealIdeasResult(
        provider="openai",
        model="gpt-5.4-mini-2026-03-17",
        target_date="2026-07-21",
        ideas=(
            GroundedMealIdea(
                name="Restored Lunch",
                meal_type="lunch",
                ingredients=(ingredient,),
                calories=300,
                protein_g=45,
                carbs_g=0,
                fat_g=12,
                available_ingredient_count=0,
            ),
        ),
        telemetry=AIRunTelemetry(
            provider="openai",
            model="gpt-5.4-mini-2026-03-17",
            runtime_seconds=0.8,
            input_tokens=500,
            cached_input_tokens=100,
            output_tokens=200,
            estimated_api_cost_usd=0.0002,
            pricing_version="2026-07-21",
        ),
    )
    persisted = persist_successful_generation(
        user_id=1,
        selected_model="gpt-5.4-mini",
        request=request,
        result=result,
    )

    with TestClient(app) as client:
        response = client.get("/nutrition/1/meal-ideas/history")
        missing_user = client.get("/nutrition/999/meal-ideas/history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == 1
    assert payload["results"] == [persisted.to_public_dict()]
    assert payload["results"][0]["request"]["model"] == "gpt-5.4-mini"
    assert payload["results"][0]["result"]["model"] == "gpt-5.4-mini-2026-03-17"
    assert missing_user.status_code == 404


def test_meal_ideas_api_returns_useful_selected_provider_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "meal_ideas_error_api.db")
    database.initialize_database()

    def fail_selected_provider(**kwargs):
        del kwargs
        raise MealIdeaProviderError(
            "local_provider_failed",
            "Local could not generate meal ideas. Retry or switch providers.",
        )

    monkeypatch.setattr(
        meal_ideas_route,
        "generate_meal_ideas",
        fail_selected_provider,
    )
    with TestClient(app) as client:
        response = client.post(
            "/nutrition/1/meal-ideas?target_date=2026-07-21",
            json={"provider": "local"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "code": "local_provider_failed",
        "message": "Local could not generate meal ideas. Retry or switch providers.",
    }


def test_meal_instruction_api_preserves_exact_grounded_recipe_facts(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "meal_instructions_api.db")
    database.initialize_database()
    captured = {}

    def fake_generate(*, user_id, request):
        captured["user_id"] = user_id
        captured["request"] = request
        return MealInstructionResult(
            provider=request.provider,
            model=request.model or "qwen3:8b",
            instructions=("Cook the exact grounded ingredients.",),
            telemetry=AIRunTelemetry(
                provider="local",
                model="qwen3:8b",
                runtime_seconds=1.2,
                input_tokens=50,
                cached_input_tokens=None,
                output_tokens=20,
                estimated_api_cost_usd=0.0,
                pricing_version=None,
            ),
        )

    monkeypatch.setattr(
        meal_ideas_route,
        "generate_cooking_instructions",
        fake_generate,
    )
    with TestClient(app) as client:
        response = client.post(
            "/nutrition/1/meal-instructions",
            json={
                "provider": "local",
                "model": "qwen3:8b",
                "meal_name": "Exact API Recipe",
                "ingredients": [
                    {
                        "canonical_food_id": 42,
                        "personal_food_id": None,
                        "display_name": "Exact Chicken",
                        "amount_grams": 137.25,
                    }
                ],
            },
        )

    assert response.status_code == 200
    request = captured["request"]
    assert request.ingredients[0].canonical_food_id == 42
    assert request.ingredients[0].amount_grams == 137.25
    assert response.json()["instructions"] == ["Cook the exact grounded ingredients."]
    assert response.json()["telemetry"]["estimated_api_cost_usd"] == 0.0
