from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from models.ai_run_models import AIProviderTextResult, AIRunTelemetry
from services.ai_model_identity_service import canonical_openai_model_family

AI_TEXT_PRICING_VERSION = "standard-text-2026-07-21"


@dataclass(frozen=True)
class AITextTokenPricing:
    input_per_million_usd: float
    cached_input_per_million_usd: float
    output_per_million_usd: float


AI_TEXT_TOKEN_PRICING: dict[str, AITextTokenPricing] = {
    "gpt-5.6-sol": AITextTokenPricing(5.00, 0.50, 30.00),
    "gpt-5.6-terra": AITextTokenPricing(2.50, 0.25, 15.00),
    "gpt-5.6-luna": AITextTokenPricing(1.00, 0.10, 6.00),
    "gpt-5.5": AITextTokenPricing(5.00, 0.50, 30.00),
    "gpt-5.4": AITextTokenPricing(2.50, 0.25, 15.00),
    "gpt-5.4-mini": AITextTokenPricing(0.75, 0.075, 4.50),
    "gpt-5.4-nano": AITextTokenPricing(0.20, 0.02, 1.25),
}


def openai_provider_text_result(
    response: Any,
    *,
    text: str,
    requested_model: str,
    configured_max_output_tokens: int | None = None,
) -> AIProviderTextResult:
    usage = _field(response, "usage")
    input_details = _field(usage, "input_tokens_details")
    output_details = _field(usage, "output_tokens_details")
    incomplete_details = _field(response, "incomplete_details")
    return AIProviderTextResult(
        text=text,
        model=_optional_text(_field(response, "model")) or requested_model,
        input_tokens=_optional_nonnegative_int(_field(usage, "input_tokens")),
        cached_input_tokens=_optional_nonnegative_int(
            _field(input_details, "cached_tokens")
        ),
        output_tokens=_optional_nonnegative_int(_field(usage, "output_tokens")),
        reasoning_tokens=_optional_nonnegative_int(
            _field(output_details, "reasoning_tokens")
        ),
        total_tokens=_optional_nonnegative_int(_field(usage, "total_tokens")),
        response_id=_optional_text(_field(response, "id")),
        status=_optional_text(_field(response, "status")),
        incomplete_reason=_optional_text(_field(incomplete_details, "reason")),
        max_output_tokens=(
            _optional_nonnegative_int(configured_max_output_tokens)
            or _optional_nonnegative_int(_field(response, "max_output_tokens"))
        ),
    )


def local_provider_text_result(
    response_payload: Mapping[str, Any],
    *,
    text: str,
    requested_model: str,
) -> AIProviderTextResult:
    return AIProviderTextResult(
        text=text,
        model=_optional_text(response_payload.get("model")) or requested_model,
        input_tokens=_optional_nonnegative_int(
            response_payload.get("prompt_eval_count")
        ),
        cached_input_tokens=None,
        output_tokens=_optional_nonnegative_int(response_payload.get("eval_count")),
    )


def normalize_ai_run_telemetry(
    *,
    provider: str,
    requested_model: str,
    runtime_seconds: float,
    provider_result: str | AIProviderTextResult,
) -> tuple[str, AIRunTelemetry]:
    normalized_provider = provider.strip().lower()
    result = (
        provider_result
        if isinstance(provider_result, AIProviderTextResult)
        else AIProviderTextResult(text=provider_result, model=requested_model)
    )
    actual_model = result.model or requested_model
    estimated_cost = estimate_api_cost_usd(
        provider=normalized_provider,
        model=actual_model,
        input_tokens=result.input_tokens,
        cached_input_tokens=result.cached_input_tokens,
        output_tokens=result.output_tokens,
    )
    pricing_model = canonical_openai_model_family(actual_model)
    pricing_version = (
        AI_TEXT_PRICING_VERSION
        if normalized_provider == "openai" and pricing_model in AI_TEXT_TOKEN_PRICING
        else None
    )
    return result.text, AIRunTelemetry(
        provider=normalized_provider,
        model=actual_model,
        runtime_seconds=round(max(0.0, float(runtime_seconds)), 4),
        input_tokens=result.input_tokens,
        cached_input_tokens=result.cached_input_tokens,
        output_tokens=result.output_tokens,
        estimated_api_cost_usd=estimated_cost,
        pricing_version=pricing_version,
    )


def estimate_api_cost_usd(
    *,
    provider: str,
    model: str,
    input_tokens: int | None,
    cached_input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    if provider.strip().lower() == "local":
        return 0.0
    if provider.strip().lower() != "openai":
        return None
    canonical_model = canonical_openai_model_family(model)
    pricing = (
        AI_TEXT_TOKEN_PRICING.get(canonical_model)
        if canonical_model is not None
        else None
    )
    if pricing is None or input_tokens is None or output_tokens is None:
        return None
    cached = min(cached_input_tokens or 0, input_tokens)
    uncached = max(0, input_tokens - cached)
    cost = (
        uncached * pricing.input_per_million_usd
        + cached * pricing.cached_input_per_million_usd
        + output_tokens * pricing.output_per_million_usd
    ) / 1_000_000
    return round(cost, 10)


def _field(value: Any, field_name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(field_name)
    return getattr(value, field_name, None)


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _optional_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value >= 0 else None
