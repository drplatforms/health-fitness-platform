from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import requests

from models.daily_coach_provider_preview_payload_models import (
    DailyCoachProviderPreviewRawDataPayload,
)
from models.daily_coach_provider_preview_runtime_models import (
    DAILY_COACH_PROVIDER_PREVIEW_RUNTIME_SPIKE_RESULT_VERSION,
    DailyCoachProviderPreviewRuntimeSpikeResult,
)
from services.daily_coach_provider_preview_payload_service import (
    build_daily_coach_provider_preview_raw_data_payload_for_user,
)

MINIMAL_FREE_VOICE_PROVIDER_INSTRUCTION = (
    "You are a developer-preview Daily Coach voice experiment. "
    "Use the raw backend data below as your only source of facts. "
    "Speak naturally and directly to the user. "
    "You may vary structure and phrasing. "
    "Do not claim to change the app, workouts, nutrition targets, "
    "or Daily Next Action. "
    "Do not invent facts. "
    "This is not product output."
)

ProviderPreviewCallable = Callable[[str, str, float, str, float], str]


def build_daily_coach_provider_preview_free_voice_input(
    payload: DailyCoachProviderPreviewRawDataPayload,
) -> str:
    payload_json = json.dumps(payload.to_dict(), indent=2, sort_keys=True)
    return (
        f"{MINIMAL_FREE_VOICE_PROVIDER_INSTRUCTION}\n\n"
        f"RAW_BACKEND_PAYLOAD_JSON:\n{payload_json}"
    )


def run_daily_coach_provider_preview_runtime_spike(
    *,
    payload: DailyCoachProviderPreviewRawDataPayload | None = None,
    user_id: int | None = None,
    target_date: str | None = None,
    model_name: str,
    timeout_seconds: float = 300.0,
    ollama_base_url: str = "http://localhost:11434",
    temperature: float = 0.9,
    provider_callable: ProviderPreviewCallable | None = None,
) -> DailyCoachProviderPreviewRuntimeSpikeResult:
    if payload is None:
        if user_id is None:
            raise ValueError("user_id is required when payload is not provided")
        payload = build_daily_coach_provider_preview_raw_data_payload_for_user(
            user_id=user_id,
            target_date=target_date,
        )

    provider = provider_callable or call_ollama_provider_preview_free_voice
    provider_input = build_daily_coach_provider_preview_free_voice_input(payload)
    started = perf_counter()
    raw_output: str | None = None
    error_type: str | None = None
    error_message: str | None = None

    try:
        raw_output = provider(
            model_name,
            provider_input,
            timeout_seconds,
            ollama_base_url,
            temperature,
        )
    except Exception as exc:  # noqa: BLE001 - developer spike preserves error metadata
        error_type = type(exc).__name__
        error_message = str(exc)

    elapsed_seconds = perf_counter() - started
    return DailyCoachProviderPreviewRuntimeSpikeResult(
        result_version=DAILY_COACH_PROVIDER_PREVIEW_RUNTIME_SPIKE_RESULT_VERSION,
        user_id=payload.user_id,
        target_date=payload.target_date,
        model_name=model_name,
        generated_at=datetime.now(UTC).isoformat(),
        elapsed_seconds=round(elapsed_seconds, 3),
        latency_ms=round(elapsed_seconds * 1000),
        developer_preview_only=True,
        provider_call_was_opt_in=True,
        persistence_allowed=False,
        product_surface_allowed=False,
        normal_today_surface_allowed=False,
        payload_version=payload.payload_version,
        source_snapshot_version=payload.source_snapshot_version,
        raw_model_output=raw_output,
        error_type=error_type,
        error_message=error_message,
    )


def call_ollama_provider_preview_free_voice(
    model_name: str,
    provider_input: str,
    timeout_seconds: float,
    ollama_base_url: str,
    temperature: float,
) -> str:
    endpoint = f"{ollama_base_url.rstrip('/')}/api/generate"
    request_payload: dict[str, Any] = {
        "model": model_name,
        "prompt": provider_input,
        "stream": False,
        "options": {"temperature": temperature},
    }
    response = requests.post(endpoint, json=request_payload, timeout=timeout_seconds)
    response.raise_for_status()
    response_payload = response.json()
    raw_output = response_payload.get("response")
    if not isinstance(raw_output, str):
        raise ValueError("Ollama response did not include string response text")
    return raw_output
