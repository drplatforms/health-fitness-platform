from __future__ import annotations

import pytest

from services.meal_idea_model_service import (
    OPENAI_MEAL_IDEA_MODELS,
    build_meal_idea_model_options,
    validate_selected_meal_idea_model,
)


def test_model_options_use_installed_ollama_models_and_curated_openai_boundary():
    result = build_meal_idea_model_options(
        environ={
            "MEAL_IDEAS_LOCAL_MODEL": "qwen3:8b",
            "MEAL_IDEAS_OPENAI_MODEL": "gpt-5.6-luna",
        },
        ollama_tags_fetch=lambda base_url, timeout: {
            "models": [
                {"name": "hermes3:8b"},
                {"name": "qwen3:8b"},
                {"model": "qwen3:14b"},
            ]
        },
    )

    local = result["providers"]["local"]
    assert [item["id"] for item in local["models"]] == [
        "hermes3:8b",
        "qwen3:8b",
        "qwen3:14b",
    ]
    assert local["default_model"] == "qwen3:8b"
    assert local["source"] == "ollama"

    openai = result["providers"]["openai"]
    assert [item["id"] for item in openai["models"]] == list(OPENAI_MEAL_IDEA_MODELS)
    assert openai["default_model"] == "gpt-5.6-luna"


def test_local_model_discovery_failure_preserves_configured_default():
    def fail_discovery(base_url, timeout):
        del base_url, timeout
        raise TimeoutError("offline")

    result = build_meal_idea_model_options(
        environ={"MEAL_IDEAS_LOCAL_MODEL": "my-local-model:latest"},
        ollama_tags_fetch=fail_discovery,
    )
    local = result["providers"]["local"]

    assert local["models"] == [
        {"id": "my-local-model:latest", "label": "my-local-model:latest"}
    ]
    assert local["default_model"] == "my-local-model:latest"
    assert local["source"] == "configured_fallback"
    assert "discovery is unavailable" in local["message"]


def test_openai_model_validation_rejects_names_outside_curated_boundary():
    assert validate_selected_meal_idea_model("openai", "gpt-5.4-mini") == "gpt-5.4-mini"
    with pytest.raises(ValueError, match="not supported"):
        validate_selected_meal_idea_model("openai", "gpt-4.1-mini")
