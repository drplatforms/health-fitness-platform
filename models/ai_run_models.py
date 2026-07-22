from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AIProviderTextResult:
    """Provider-boundary result before request runtime and cost are normalized."""

    text: str
    model: str | None = None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class AIRunTelemetry:
    provider: str
    model: str
    runtime_seconds: float
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    estimated_api_cost_usd: float | None
    pricing_version: str | None

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)
