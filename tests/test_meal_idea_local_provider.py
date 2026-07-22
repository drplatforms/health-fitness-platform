from __future__ import annotations

import io
import json
import urllib.error

import pytest

from services import meal_idea_service


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_local_provider_uses_chat_with_small_schema_and_exact_selected_model(
    monkeypatch,
):
    captured: dict = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(
            {
                "message": {
                    "role": "assistant",
                    "content": '{"meals": []}',
                }
            }
        )

    monkeypatch.setattr(meal_idea_service.urllib.request, "urlopen", fake_urlopen)
    output = meal_idea_service._call_local_provider(
        "hermes3:8b",
        "meal prompt",
        17,
        meal_idea_service.LOCAL_MEAL_IDEAS_PROVIDER_SCHEMA,
        base_url="http://localhost:11434",
    )

    assert output == '{"meals": []}'
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["timeout"] == 17
    assert captured["payload"]["model"] == "hermes3:8b"
    assert captured["payload"]["think"] is False
    assert captured["payload"]["format"] == (
        meal_idea_service.LOCAL_MEAL_IDEAS_PROVIDER_SCHEMA
    )


def test_local_timeout_exposes_selected_model_and_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        del args, kwargs
        raise TimeoutError("timed out")

    monkeypatch.setattr(meal_idea_service.urllib.request, "urlopen", timeout)
    with pytest.raises(meal_idea_service.MealIdeaProviderError) as exc_info:
        meal_idea_service._call_local_provider(
            "qwen3:8b",
            "meal prompt",
            12,
            meal_idea_service.LOCAL_MEAL_IDEAS_PROVIDER_SCHEMA,
            base_url="http://localhost:11434",
        )

    assert exc_info.value.code == "local_timeout"
    assert "qwen3:8b" in exc_info.value.public_message
    assert "12 seconds" in exc_info.value.public_message


def test_local_http_error_preserves_bounded_ollama_reason(monkeypatch):
    def missing_model(*args, **kwargs):
        del args, kwargs
        raise urllib.error.HTTPError(
            "http://localhost:11434/api/chat",
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"error":"model not found"}'),
        )

    monkeypatch.setattr(meal_idea_service.urllib.request, "urlopen", missing_model)
    with pytest.raises(meal_idea_service.MealIdeaProviderError) as exc_info:
        meal_idea_service._call_local_provider(
            "missing:latest",
            "meal prompt",
            12,
            meal_idea_service.LOCAL_MEAL_IDEAS_PROVIDER_SCHEMA,
            base_url="http://localhost:11434",
        )

    assert exc_info.value.code == "local_model_not_found"
    assert "HTTP 404" in exc_info.value.public_message
    assert "model not found" in exc_info.value.public_message
