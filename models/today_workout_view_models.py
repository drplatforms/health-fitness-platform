from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

TODAY_WORKOUT_CONTRACT_VERSION = "today_workout_view_v0"

TODAY_WORKOUT_STATUSES = {
    "preview",
    "selected",
    "in_progress",
    "completed",
    "not_available",
}
TODAY_WORKOUT_SOURCES = {
    "current_execution_state",
    "deterministic_generation",
    "none",
}


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return value.strip()


def _validate_choice(value: str, allowed: set[str], field_name: str) -> str:
    normalized = _require_non_empty_text(value, field_name)
    if normalized not in allowed:
        raise ValueError(f"{field_name} must be one of {sorted(allowed)}.")
    return normalized


@dataclass(frozen=True)
class TodayWorkoutExerciseItem:
    exercise_id: str | None
    name: str
    order: int
    section: str | None
    sets: int | None
    reps: str | None
    weight: float | None
    weight_unit: str | None
    rest_seconds: int | None
    tempo: str | None
    notes: str | None
    substitution_notes: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "name",
            _require_non_empty_text(self.name, "exercises[].name"),
        )
        if not isinstance(self.order, int) or self.order < 1:
            raise ValueError("exercises[].order must be a positive integer.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TodayWorkoutResponse:
    user_id: int
    target_date: str
    status: str
    title: str
    summary: str
    source: str
    workout_id: str | None
    generated_at: str | None
    estimated_duration_minutes: int | None
    focus: str | None
    equipment: list[str] = field(default_factory=list)
    exercises: list[TodayWorkoutExerciseItem] = field(default_factory=list)
    data_gaps: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    contract_version: str = TODAY_WORKOUT_CONTRACT_VERSION

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
            "status",
            _validate_choice(self.status, TODAY_WORKOUT_STATUSES, "status"),
        )
        object.__setattr__(self, "title", _require_non_empty_text(self.title, "title"))
        object.__setattr__(
            self,
            "summary",
            _require_non_empty_text(self.summary, "summary"),
        )
        object.__setattr__(
            self,
            "source",
            _validate_choice(self.source, TODAY_WORKOUT_SOURCES, "source"),
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
            "status": self.status,
            "title": self.title,
            "summary": self.summary,
            "source": self.source,
            "workout_id": self.workout_id,
            "generated_at": self.generated_at,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "focus": self.focus,
            "equipment": list(self.equipment),
            "exercises": [exercise.to_dict() for exercise in self.exercises],
            "data_gaps": list(self.data_gaps),
            "limitations": list(self.limitations),
        }
