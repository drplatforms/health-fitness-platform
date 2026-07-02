from __future__ import annotations

from dataclasses import asdict, dataclass

DAILY_COACH_PROVIDER_PREVIEW_RUNTIME_SPIKE_RESULT_VERSION = (
    "daily_coach_provider_preview_runtime_spike_result_v1"
)


@dataclass(frozen=True)
class DailyCoachProviderPreviewRuntimeSpikeResult:
    result_version: str
    user_id: int
    target_date: str
    model_name: str
    generated_at: str
    elapsed_seconds: float
    latency_ms: int
    developer_preview_only: bool
    provider_call_was_opt_in: bool
    persistence_allowed: bool
    product_surface_allowed: bool
    normal_today_surface_allowed: bool
    payload_version: str
    source_snapshot_version: str
    raw_model_output: str | None = None
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        _validate_required_text("result_version", self.result_version)
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("target_date", self.target_date)
        _validate_required_text("model_name", self.model_name)
        _validate_required_text("generated_at", self.generated_at)
        _validate_non_negative_number("elapsed_seconds", self.elapsed_seconds)
        _validate_non_negative_int("latency_ms", self.latency_ms)
        _validate_required_text("payload_version", self.payload_version)
        _validate_required_text("source_snapshot_version", self.source_snapshot_version)
        _validate_runtime_boundaries(
            developer_preview_only=self.developer_preview_only,
            provider_call_was_opt_in=self.provider_call_was_opt_in,
            persistence_allowed=self.persistence_allowed,
            product_surface_allowed=self.product_surface_allowed,
            normal_today_surface_allowed=self.normal_today_surface_allowed,
        )

    @property
    def succeeded(self) -> bool:
        return self.error_type is None and self.raw_model_output is not None

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_required_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _validate_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_non_negative_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_non_negative_number(name: str, value: float) -> None:
    if not isinstance(value, int | float) or value < 0:
        raise ValueError(f"{name} must be a non-negative number")


def _validate_runtime_boundaries(
    *,
    developer_preview_only: bool,
    provider_call_was_opt_in: bool,
    persistence_allowed: bool,
    product_surface_allowed: bool,
    normal_today_surface_allowed: bool,
) -> None:
    if developer_preview_only is not True:
        raise ValueError("developer_preview_only must be true")
    if provider_call_was_opt_in is not True:
        raise ValueError("provider_call_was_opt_in must be true")
    if persistence_allowed is not False:
        raise ValueError("persistence_allowed must be false")
    if product_surface_allowed is not False:
        raise ValueError("product_surface_allowed must be false")
    if normal_today_surface_allowed is not False:
        raise ValueError("normal_today_surface_allowed must be false")
