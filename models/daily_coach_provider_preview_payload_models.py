from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_VERSION = (
    "daily_coach_provider_preview_raw_data_payload_v1"
)

FORBIDDEN_PROVIDER_PREVIEW_PAYLOAD_KEYS = {
    "approved_sentences",
    "sentence_templates",
    "final_coach_note",
    "final_daily_coach_copy",
    "rendered_note",
    "safe_copy_options",
}


@dataclass(frozen=True)
class DailyCoachProviderPreviewRawDataPayload:
    payload_version: str
    user_id: int
    target_date: str
    generated_at: str
    developer_preview_only: bool
    provider_call_allowed: bool
    persistence_allowed: bool
    product_surface_allowed: bool
    source_snapshot_version: str
    source_services: list[str]
    source_data: dict[str, Any]
    data_completeness: dict[str, str]
    source_data_gaps: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    backend_truth_contract: dict[str, bool] = field(default_factory=dict)
    provider_voice_space: dict[str, Any] = field(default_factory=dict)
    provider_input_guidance: dict[str, Any] = field(default_factory=dict)
    forbidden_provider_authority: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_required_text("payload_version", self.payload_version)
        _validate_positive_int("user_id", self.user_id)
        _validate_required_text("target_date", self.target_date)
        _validate_required_text("generated_at", self.generated_at)
        _validate_required_text("source_snapshot_version", self.source_snapshot_version)
        _validate_non_empty_string_list("source_services", self.source_services)
        if not isinstance(self.source_data, dict) or not self.source_data:
            raise ValueError("source_data is required")
        if not isinstance(self.data_completeness, dict):
            raise ValueError("data_completeness must be a dictionary")
        _validate_string_list("source_data_gaps", self.source_data_gaps)
        _validate_string_list("reason_codes", self.reason_codes)
        _validate_string_list("limitations", self.limitations)
        _validate_string_list(
            "forbidden_provider_authority", self.forbidden_provider_authority
        )
        _validate_hard_boundaries(
            developer_preview_only=self.developer_preview_only,
            provider_call_allowed=self.provider_call_allowed,
            persistence_allowed=self.persistence_allowed,
            product_surface_allowed=self.product_surface_allowed,
        )
        _validate_no_forbidden_sentence_bank_keys(self.to_dict_shallow())
        _validate_no_forbidden_sentence_bank_keys(self.source_data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_dict_shallow(self) -> dict[str, Any]:
        return {
            "payload_version": self.payload_version,
            "user_id": self.user_id,
            "target_date": self.target_date,
            "generated_at": self.generated_at,
            "developer_preview_only": self.developer_preview_only,
            "provider_call_allowed": self.provider_call_allowed,
            "persistence_allowed": self.persistence_allowed,
            "product_surface_allowed": self.product_surface_allowed,
            "source_snapshot_version": self.source_snapshot_version,
            "source_services": self.source_services,
            "source_data": self.source_data,
            "data_completeness": self.data_completeness,
            "source_data_gaps": self.source_data_gaps,
            "reason_codes": self.reason_codes,
            "limitations": self.limitations,
            "backend_truth_contract": self.backend_truth_contract,
            "provider_voice_space": self.provider_voice_space,
            "provider_input_guidance": self.provider_input_guidance,
            "forbidden_provider_authority": self.forbidden_provider_authority,
        }


def _validate_required_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _validate_positive_int(name: str, value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_string_list(name: str, values: list[str]) -> None:
    if not isinstance(values, list):
        raise ValueError(f"{name} must be a list")
    if not all(isinstance(value, str) for value in values):
        raise ValueError(f"{name} must contain only strings")


def _validate_non_empty_string_list(name: str, values: list[str]) -> None:
    _validate_string_list(name, values)
    if not values:
        raise ValueError(f"{name} must not be empty")


def _validate_hard_boundaries(
    *,
    developer_preview_only: bool,
    provider_call_allowed: bool,
    persistence_allowed: bool,
    product_surface_allowed: bool,
) -> None:
    if developer_preview_only is not True:
        raise ValueError("developer_preview_only must be true")
    if provider_call_allowed is not False:
        raise ValueError("provider_call_allowed must be false")
    if persistence_allowed is not False:
        raise ValueError("persistence_allowed must be false")
    if product_surface_allowed is not False:
        raise ValueError("product_surface_allowed must be false")


def _validate_no_forbidden_sentence_bank_keys(payload: dict[str, Any]) -> None:
    forbidden = FORBIDDEN_PROVIDER_PREVIEW_PAYLOAD_KEYS.intersection(payload)
    if forbidden:
        message = (
            "provider preview payload may not include final copy or "
            "sentence-bank keys: "
        )
        raise ValueError(message + ", ".join(sorted(forbidden)))
