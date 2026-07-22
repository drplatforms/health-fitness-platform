from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from services.meal_idea_model_service import (
    DEFAULT_LOCAL_MODEL,
    DEFAULT_OPENAI_MODEL,
    OllamaTagsFetch,
    build_ai_text_model_options,
    validate_selected_ai_text_model,
)

COACH_PROVIDER_ENV = "COACH_PROVIDER"
COACH_LOCAL_MODEL_ENV = "COACH_LOCAL_MODEL"
COACH_OPENAI_MODEL_ENV = "COACH_OPENAI_MODEL"


def configured_coach_provider(*, environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    provider = env.get(COACH_PROVIDER_ENV, "local").strip().lower()
    return provider if provider in {"local", "openai"} else "local"


def configured_coach_model(
    provider: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    env = os.environ if environ is None else environ
    if provider == "local":
        return (
            env.get(COACH_LOCAL_MODEL_ENV, DEFAULT_LOCAL_MODEL).strip()
            or DEFAULT_LOCAL_MODEL
        )
    return (
        env.get(COACH_OPENAI_MODEL_ENV, DEFAULT_OPENAI_MODEL).strip()
        or DEFAULT_OPENAI_MODEL
    )


def build_coach_model_options(
    *,
    environ: Mapping[str, str] | None = None,
    ollama_tags_fetch: OllamaTagsFetch | None = None,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    options = build_ai_text_model_options(
        configured_local_model=configured_coach_model("local", environ=env),
        configured_openai_model=configured_coach_model("openai", environ=env),
        environ=env,
        ollama_tags_fetch=ollama_tags_fetch,
        unavailable_message=(
            "Ollama model discovery is unavailable. Using the configured Coach model."
        ),
    )
    return {
        "configured_provider": configured_coach_provider(environ=env),
        **options,
    }


def validate_selected_coach_model(provider: str, model: str) -> str:
    if provider not in {"local", "openai"}:
        raise ValueError("provider must be local or openai.")
    return validate_selected_ai_text_model(
        provider,
        model,
        unsupported_openai_message=(
            "The selected OpenAI model is not supported for Coach."
        ),
    )
