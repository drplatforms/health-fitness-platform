from __future__ import annotations

import json
import os
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from services.provider_lifecycle_service import resolve_ollama_base_url

MEAL_IDEAS_LOCAL_MODEL_ENV = "MEAL_IDEAS_LOCAL_MODEL"
MEAL_IDEAS_OPENAI_MODEL_ENV = "MEAL_IDEAS_OPENAI_MODEL"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"

DEFAULT_LOCAL_MODEL = "qwen3:8b"
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"
OPENAI_MEAL_IDEA_MODELS = (
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.4-nano",
)
DEFAULT_OLLAMA_DISCOVERY_TIMEOUT_SECONDS = 5.0

OllamaTagsFetch = Callable[[str, float], dict[str, Any]]


def build_meal_idea_model_options(
    *,
    environ: Mapping[str, str] | None = None,
    ollama_tags_fetch: OllamaTagsFetch | None = None,
) -> dict[str, Any]:
    """Return provider-owned model choices without making the UI own model policy."""

    env = os.environ if environ is None else environ
    configured_local = (
        env.get(MEAL_IDEAS_LOCAL_MODEL_ENV, DEFAULT_LOCAL_MODEL).strip()
        or DEFAULT_LOCAL_MODEL
    )
    configured_openai = (
        env.get(MEAL_IDEAS_OPENAI_MODEL_ENV, DEFAULT_OPENAI_MODEL).strip()
        or DEFAULT_OPENAI_MODEL
    )
    openai_default = (
        configured_openai
        if configured_openai in OPENAI_MEAL_IDEA_MODELS
        else DEFAULT_OPENAI_MODEL
    )

    fetch_tags = ollama_tags_fetch or _fetch_ollama_tags
    base_url = resolve_ollama_base_url(base_url=env.get(OLLAMA_BASE_URL_ENV))
    try:
        payload = fetch_tags(base_url, DEFAULT_OLLAMA_DISCOVERY_TIMEOUT_SECONDS)
        local_models = _ollama_model_names(payload)
    except Exception:
        local_models = []

    if local_models:
        local_default = (
            configured_local
            if configured_local in local_models
            else (
                DEFAULT_LOCAL_MODEL
                if DEFAULT_LOCAL_MODEL in local_models
                else local_models[0]
            )
        )
        local_source = "ollama"
        local_message = None
    else:
        local_models = [configured_local]
        local_default = configured_local
        local_source = "configured_fallback"
        local_message = (
            "Ollama model discovery is unavailable. Using the configured Local model."
        )

    return {
        "providers": {
            "local": {
                "models": [_model_option(name) for name in local_models],
                "default_model": local_default,
                "source": local_source,
                "message": local_message,
            },
            "openai": {
                "models": [_model_option(name) for name in OPENAI_MEAL_IDEA_MODELS],
                "default_model": openai_default,
                "source": "curated",
                "message": None,
            },
        }
    }


def validate_selected_meal_idea_model(provider: str, model: str) -> str:
    if not isinstance(model, str):
        raise ValueError("model must be text.")
    selected = model.strip()
    if not selected or len(selected) > 200:
        raise ValueError("model must be between 1 and 200 characters.")
    if provider == "openai" and selected not in OPENAI_MEAL_IDEA_MODELS:
        raise ValueError("The selected OpenAI model is not supported for Meal Ideas.")
    return selected


def configured_meal_idea_model(
    provider: str, *, environ: Mapping[str, str] | None = None
) -> str:
    env = os.environ if environ is None else environ
    if provider == "local":
        return (
            env.get(MEAL_IDEAS_LOCAL_MODEL_ENV, DEFAULT_LOCAL_MODEL).strip()
            or DEFAULT_LOCAL_MODEL
        )
    configured = (
        env.get(MEAL_IDEAS_OPENAI_MODEL_ENV, DEFAULT_OPENAI_MODEL).strip()
        or DEFAULT_OPENAI_MODEL
    )
    return configured if configured in OPENAI_MEAL_IDEA_MODELS else DEFAULT_OPENAI_MODEL


def _model_option(name: str) -> dict[str, str]:
    return {"id": name, "label": name}


def _ollama_model_names(payload: dict[str, Any]) -> list[str]:
    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError("Ollama tags response is missing models.")
    names: list[str] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("model")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
    return list(dict.fromkeys(names))


def _fetch_ollama_tags(base_url: str, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/tags",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Ollama tags response must be an object.")
    return payload
