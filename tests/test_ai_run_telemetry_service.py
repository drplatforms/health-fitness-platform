from __future__ import annotations

from types import SimpleNamespace

from openai.types.responses.response import Response
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText
from openai.types.responses.response_usage import (
    InputTokensDetails,
    OutputTokensDetails,
    ResponseUsage,
)

from services.ai_run_telemetry_service import (
    AI_TEXT_PRICING_VERSION,
    estimate_api_cost_usd,
    local_provider_text_result,
    normalize_ai_run_telemetry,
    openai_provider_text_result,
)
from services.meal_idea_service import _call_openai_provider


def _openai_sdk_response(*, usage: ResponseUsage | None) -> Response:
    return Response(
        id="resp_meal_ideas_test",
        created_at=0.0,
        model="gpt-5.4-mini-2026-03-17",
        object="response",
        output=[
            ResponseOutputMessage(
                id="msg_meal_ideas_test",
                content=[
                    ResponseOutputText(
                        annotations=[],
                        text='{"ideas": []}',
                        type="output_text",
                    )
                ],
                role="assistant",
                status="completed",
                type="message",
            )
        ],
        parallel_tool_calls=True,
        tool_choice="auto",
        tools=[],
        usage=usage,
    )


def _stub_openai_response(monkeypatch, response: Response) -> None:
    class _FakeResponses:
        def create(self, **kwargs):
            del kwargs
            return response

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            del kwargs
            self.responses = _FakeResponses()

    monkeypatch.setattr("openai.OpenAI", _FakeOpenAI)


def test_openai_usage_and_cached_token_cost_are_normalized_from_response() -> None:
    response = SimpleNamespace(
        model="gpt-5.6-luna",
        usage=SimpleNamespace(
            input_tokens=1_000,
            input_tokens_details=SimpleNamespace(cached_tokens=400),
            output_tokens=200,
        ),
    )
    provider_result = openai_provider_text_result(
        response,
        text='{"ideas": []}',
        requested_model="gpt-5.4-mini",
    )

    text, telemetry = normalize_ai_run_telemetry(
        provider="openai",
        requested_model="gpt-5.4-mini",
        runtime_seconds=6.81234,
        provider_result=provider_result,
    )

    assert text == '{"ideas": []}'
    assert telemetry.model == "gpt-5.6-luna"
    assert telemetry.runtime_seconds == 6.8123
    assert telemetry.input_tokens == 1_000
    assert telemetry.cached_input_tokens == 400
    assert telemetry.output_tokens == 200
    assert telemetry.estimated_api_cost_usd == 0.00184
    assert telemetry.pricing_version == AI_TEXT_PRICING_VERSION


def test_unknown_openai_model_keeps_usage_but_has_no_cost_estimate() -> None:
    _, telemetry = normalize_ai_run_telemetry(
        provider="openai",
        requested_model="future-model",
        runtime_seconds=1,
        provider_result=openai_provider_text_result(
            {
                "model": "future-model-actual",
                "usage": {
                    "input_tokens": 12,
                    "input_tokens_details": {"cached_tokens": 3},
                    "output_tokens": 4,
                },
            },
            text="{}",
            requested_model="future-model",
        ),
    )

    assert telemetry.model == "future-model-actual"
    assert telemetry.input_tokens == 12
    assert telemetry.cached_input_tokens == 3
    assert telemetry.output_tokens == 4
    assert telemetry.estimated_api_cost_usd is None
    assert telemetry.pricing_version is None


def test_real_openai_sdk_response_prices_dated_snapshot_and_preserves_actual_model(
    monkeypatch,
) -> None:
    response = _openai_sdk_response(
        usage=ResponseUsage(
            input_tokens=1_000,
            input_tokens_details=InputTokensDetails(cached_tokens=400),
            output_tokens=200,
            output_tokens_details=OutputTokensDetails(reasoning_tokens=50),
            total_tokens=1_200,
        )
    )
    _stub_openai_response(monkeypatch, response)

    provider_result = _call_openai_provider(
        "gpt-5.4-mini",
        "Generate grounded meal ideas.",
        30.0,
        {"type": "object"},
        api_key="test-key",
        base_url=None,
        with_metadata=True,
    )

    text, telemetry = normalize_ai_run_telemetry(
        provider="openai",
        requested_model="gpt-5.4-mini",
        runtime_seconds=2.5,
        provider_result=provider_result,
    )

    assert text == '{"ideas": []}'
    assert telemetry.model == "gpt-5.4-mini-2026-03-17"
    assert telemetry.input_tokens == 1_000
    assert telemetry.cached_input_tokens == 400
    assert telemetry.output_tokens == 200
    assert telemetry.estimated_api_cost_usd == 0.00138
    assert telemetry.pricing_version == AI_TEXT_PRICING_VERSION


def test_real_openai_sdk_response_without_usage_remains_unpriced(monkeypatch) -> None:
    _stub_openai_response(monkeypatch, _openai_sdk_response(usage=None))

    provider_result = _call_openai_provider(
        "gpt-5.4-mini",
        "Generate grounded meal ideas.",
        30.0,
        {"type": "object"},
        api_key="test-key",
        base_url=None,
        with_metadata=True,
    )
    _, telemetry = normalize_ai_run_telemetry(
        provider="openai",
        requested_model="gpt-5.4-mini",
        runtime_seconds=2.5,
        provider_result=provider_result,
    )

    assert telemetry.model == "gpt-5.4-mini-2026-03-17"
    assert telemetry.input_tokens is None
    assert telemetry.cached_input_tokens is None
    assert telemetry.output_tokens is None
    assert telemetry.estimated_api_cost_usd is None


def test_local_usage_runtime_and_zero_api_cost_are_normalized_without_invention() -> (
    None
):
    provider_result = local_provider_text_result(
        {
            "model": "qwen3:8b",
            "prompt_eval_count": 321,
            "eval_count": 87,
        },
        text="{}",
        requested_model="configured-model",
    )
    _, telemetry = normalize_ai_run_telemetry(
        provider="local",
        requested_model="configured-model",
        runtime_seconds=47.3,
        provider_result=provider_result,
    )

    assert telemetry.model == "qwen3:8b"
    assert telemetry.runtime_seconds == 47.3
    assert telemetry.input_tokens == 321
    assert telemetry.cached_input_tokens is None
    assert telemetry.output_tokens == 87
    assert telemetry.estimated_api_cost_usd == 0.0
    assert telemetry.pricing_version is None

    missing_usage = local_provider_text_result(
        {"model": "qwen3:8b"},
        text="{}",
        requested_model="qwen3:8b",
    )
    assert missing_usage.input_tokens is None
    assert missing_usage.output_tokens is None


def test_reasoning_tokens_are_not_added_to_output_token_cost() -> None:
    cost = estimate_api_cost_usd(
        provider="openai",
        model="gpt-5.4-mini",
        input_tokens=100,
        cached_input_tokens=0,
        output_tokens=50,
    )

    assert cost == 0.0003
