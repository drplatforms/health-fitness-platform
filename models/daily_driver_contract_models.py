from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DAILY_DRIVER_CONTRACT_VERSION = "daily_driver_today_v0"

DAILY_DRIVER_READINESS_STATUSES = {"ready", "light", "recover", "unknown"}
DAILY_DRIVER_WORKOUT_STATUSES = {
    "not_started",
    "in_progress",
    "completed",
    "not_planned",
    "unknown",
}
DAILY_DRIVER_NUTRITION_STATUSES = {
    "on_track",
    "behind",
    "complete",
    "not_logged",
    "unknown",
}
DAILY_DRIVER_NEXT_ACTION_TYPES = {
    "start_workout",
    "continue_workout",
    "log_workout",
    "log_meal",
    "review_recovery",
    "review_today",
    "done",
    "unknown",
}
DAILY_DRIVER_CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}

_FORBIDDEN_COACH_NOTE_TERMS = {
    "source_services",
    "source_tables",
    "source_table",
    "model_version",
    "payload_version",
    "source_snapshot_version",
    "provider_input",
    "provider_output",
    "backend_truth_contract",
    "forbidden_provider_authority",
    "raw_backend_payload_json",
    "dailycoachproviderpreviewrawdatapayload",
    "openai",
    "ollama",
    "crewai",
    "json schema",
}
_MARKDOWN_SNIPPETS = ("##", "**", "`", "|", "[", "]", "http://", "https://")
_MARKDOWN_LINE_PREFIXES = ("- ", "* ", "1. ")


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return value.strip()


def _validate_choice(value: str, allowed: set[str], field_name: str) -> str:
    normalized = _require_non_empty_text(value, field_name)
    if normalized not in allowed:
        raise ValueError(f"{field_name} must be one of {sorted(allowed)}.")
    return normalized


def _contains_markdown(value: str) -> bool:
    if any(snippet in value for snippet in _MARKDOWN_SNIPPETS):
        return True
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return any(
        any(line.startswith(prefix) for prefix in _MARKDOWN_LINE_PREFIXES)
        for line in lines
    )


def _validate_coach_note_text(value: str) -> str:
    text = _require_non_empty_text(value, "coach_note.text")
    lowered = text.lower()
    if _contains_markdown(text):
        raise ValueError("coach_note.text must be plain text only.")
    for term in _FORBIDDEN_COACH_NOTE_TERMS:
        if term in lowered:
            raise ValueError("coach_note.text exposes forbidden internal metadata.")
    return text


@dataclass(frozen=True)
class DailyDriverReadinessSummary:
    status: str
    headline: str
    reason: str
    confidence: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            _validate_choice(
                self.status,
                DAILY_DRIVER_READINESS_STATUSES,
                "readiness.status",
            ),
        )
        object.__setattr__(
            self,
            "headline",
            _require_non_empty_text(self.headline, "readiness.headline"),
        )
        object.__setattr__(
            self,
            "reason",
            _require_non_empty_text(self.reason, "readiness.reason"),
        )
        object.__setattr__(
            self,
            "confidence",
            _validate_choice(
                self.confidence,
                DAILY_DRIVER_CONFIDENCE_VALUES,
                "readiness.confidence",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyDriverWorkoutSummary:
    planned: bool
    workout_id: str | None
    title: str
    summary: str
    status: str
    first_action_label: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "title",
            _require_non_empty_text(self.title, "workout.title"),
        )
        object.__setattr__(
            self,
            "summary",
            _require_non_empty_text(self.summary, "workout.summary"),
        )
        object.__setattr__(
            self,
            "status",
            _validate_choice(
                self.status,
                DAILY_DRIVER_WORKOUT_STATUSES,
                "workout.status",
            ),
        )
        object.__setattr__(
            self,
            "first_action_label",
            _require_non_empty_text(
                self.first_action_label,
                "workout.first_action_label",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyDriverNutritionSummary:
    status: str
    calorie_target: int | None
    protein_target_g: int | None
    calories_logged: int | None
    protein_logged_g: int | None
    today_mission: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            _validate_choice(
                self.status,
                DAILY_DRIVER_NUTRITION_STATUSES,
                "nutrition.status",
            ),
        )
        object.__setattr__(
            self,
            "today_mission",
            _require_non_empty_text(
                self.today_mission,
                "nutrition.today_mission",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyDriverNextAction:
    type: str
    label: str
    context: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "type",
            _validate_choice(
                self.type,
                DAILY_DRIVER_NEXT_ACTION_TYPES,
                "next_action.type",
            ),
        )
        object.__setattr__(
            self,
            "label",
            _require_non_empty_text(self.label, "next_action.label"),
        )
        object.__setattr__(
            self,
            "context",
            _require_non_empty_text(self.context, "next_action.context"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyDriverCoachNote:
    enabled: bool
    text: str | None = None

    def __post_init__(self) -> None:
        if self.enabled:
            object.__setattr__(self, "text", _validate_coach_note_text(self.text or ""))
        elif self.text not in (None, ""):
            object.__setattr__(self, "text", _validate_coach_note_text(self.text))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyDriverTodayResponse:
    user_id: int
    target_date: str
    readiness: DailyDriverReadinessSummary
    workout: DailyDriverWorkoutSummary
    nutrition: DailyDriverNutritionSummary
    next_action: DailyDriverNextAction
    coach_note: DailyDriverCoachNote
    data_gaps: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    contract_version: str = DAILY_DRIVER_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("user_id must be a positive integer.")
        object.__setattr__(
            self,
            "target_date",
            _require_non_empty_text(self.target_date, "target_date"),
        )
        object.__setattr__(
            self,
            "contract_version",
            _require_non_empty_text(self.contract_version, "contract_version"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "user_id": self.user_id,
            "target_date": self.target_date,
            "readiness": self.readiness.to_dict(),
            "workout": self.workout.to_dict(),
            "nutrition": self.nutrition.to_dict(),
            "next_action": self.next_action.to_dict(),
            "coach_note": self.coach_note.to_dict(),
            "data_gaps": list(self.data_gaps),
            "limitations": list(self.limitations),
        }
