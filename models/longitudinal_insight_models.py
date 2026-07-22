from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

INSIGHT_DOMAINS = {
    "recovery",
    "training",
    "nutrition",
    "body_weight",
    "cross_domain",
}
INSIGHT_DIRECTIONS = {
    "improving",
    "worsening",
    "stable",
    "increasing",
    "decreasing",
    "recurring",
    "associated",
}
INSIGHT_STATUSES = {
    "notable",
    "supportive",
    "attention",
    "consistent",
    "plateau",
}
EVIDENCE_STRENGTH_VALUES = {"moderate", "strong"}
COVERAGE_STATUS_VALUES = {"sparse", "limited", "sufficient", "strong"}


@dataclass(frozen=True)
class InsightWindow:
    start_date: str
    end_date: str
    days: int
    observation_count: int
    label: str

    def __post_init__(self) -> None:
        _validate_date("start_date", self.start_date)
        _validate_date("end_date", self.end_date)
        _validate_positive_int("days", self.days)
        _validate_non_negative_int("observation_count", self.observation_count)
        _validate_text("label", self.label)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InsightEvidence:
    metric: str
    label: str
    value: str
    source: str
    source_fields: list[str]

    def __post_init__(self) -> None:
        _validate_token("metric", self.metric)
        _validate_text("label", self.label)
        _validate_text("value", self.value)
        _validate_text("source", self.source)
        if not self.source_fields:
            raise ValueError("source_fields must not be empty")
        for source_field in self.source_fields:
            _validate_token("source_field", source_field)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InsightDataCoverage:
    status: str
    observation_count: int
    comparison_observation_count: int | None = None
    expected_observation_count: int | None = None
    observation_rate: float | None = None
    limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_allowed("status", self.status, COVERAGE_STATUS_VALUES)
        _validate_non_negative_int("observation_count", self.observation_count)
        if self.comparison_observation_count is not None:
            _validate_non_negative_int(
                "comparison_observation_count", self.comparison_observation_count
            )
        if self.expected_observation_count is not None:
            _validate_positive_int(
                "expected_observation_count", self.expected_observation_count
            )
        if self.observation_rate is not None and not 0 <= self.observation_rate <= 1:
            raise ValueError("observation_rate must be between 0 and 1")
        for limitation in self.limitations:
            _validate_text("limitation", limitation)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LongitudinalInsight:
    stable_id: str
    domain: str
    insight_type: str
    title: str
    explanation: str
    observation_window: InsightWindow
    comparison_window: InsightWindow | None
    evidence: list[InsightEvidence]
    evidence_strength: str
    data_coverage: InsightDataCoverage
    direction: str
    status: str

    def __post_init__(self) -> None:
        _validate_token("stable_id", self.stable_id, allow_colon=True)
        _validate_allowed("domain", self.domain, INSIGHT_DOMAINS)
        _validate_token("insight_type", self.insight_type)
        _validate_text("title", self.title)
        _validate_text("explanation", self.explanation)
        if not isinstance(self.observation_window, InsightWindow):
            raise ValueError("observation_window must be an InsightWindow")
        if self.comparison_window is not None and not isinstance(
            self.comparison_window, InsightWindow
        ):
            raise ValueError("comparison_window must be an InsightWindow when present")
        if not self.evidence or not all(
            isinstance(item, InsightEvidence) for item in self.evidence
        ):
            raise ValueError("evidence must contain inspectable evidence items")
        _validate_allowed(
            "evidence_strength", self.evidence_strength, EVIDENCE_STRENGTH_VALUES
        )
        if not isinstance(self.data_coverage, InsightDataCoverage):
            raise ValueError("data_coverage must be InsightDataCoverage")
        _validate_allowed("direction", self.direction, INSIGHT_DIRECTIONS)
        _validate_allowed("status", self.status, INSIGHT_STATUSES)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["observation_window"] = self.observation_window.to_dict()
        payload["comparison_window"] = (
            self.comparison_window.to_dict()
            if self.comparison_window is not None
            else None
        )
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        payload["data_coverage"] = self.data_coverage.to_dict()
        return payload


@dataclass(frozen=True)
class LongitudinalInsightFeed:
    user_id: int
    as_of_date: str
    engine_version: str
    insights: list[LongitudinalInsight]

    def __post_init__(self) -> None:
        _validate_positive_int("user_id", self.user_id)
        _validate_date("as_of_date", self.as_of_date)
        _validate_token("engine_version", self.engine_version)
        if not all(isinstance(item, LongitudinalInsight) for item in self.insights):
            raise ValueError("insights must contain LongitudinalInsight items")
        stable_ids = [item.stable_id for item in self.insights]
        if len(stable_ids) != len(set(stable_ids)):
            raise ValueError("insight stable_id values must be unique")

    @property
    def target_date(self) -> str:
        """Compatibility alias for the original v1 response contract."""

        return self.as_of_date

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "as_of_date": self.as_of_date,
            "target_date": self.as_of_date,
            "engine_version": self.engine_version,
            "insights": [item.to_dict() for item in self.insights],
        }


def _validate_allowed(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")


def _validate_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _validate_token(name: str, value: str, *, allow_colon: bool = False) -> None:
    _validate_text(name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if allow_colon:
        allowed.add(":")
    if any(character not in allowed for character in value):
        raise ValueError(f"{name} must be a lowercase stable token")


def _validate_date(name: str, value: str) -> None:
    _validate_text(name, value)
    parts = value.split("-")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"{name} must use YYYY-MM-DD format")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
