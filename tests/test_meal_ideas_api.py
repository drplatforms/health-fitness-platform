from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from api.routes import meal_ideas as meal_ideas_route
from models.meal_idea_models import MealIdeasResult
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
