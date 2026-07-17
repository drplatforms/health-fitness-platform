from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WeeklySessionDirective:
    session_type: str
    session_title: str
    session_focus: str
    ordered_slot_families: list[str]
    optional_extension_slot_families: list[str]
    sequence_index: int


@dataclass
class WeeklyTrainingPlanDay:
    id: int
    weekly_training_plan_id: int
    training_date: str
    day_index: int
    day_type: str
    session_sequence_index: int | None = None
    session_type: str | None = None
    session_title: str | None = None
    session_focus: str | None = None
    session_directive: WeeklySessionDirective | None = None
    derived_status: str = "rest"
    is_protected: bool = False
    protection_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class WeeklyTrainingPlan:
    id: int
    user_id: int
    week_start_date: str
    week_end_date: str
    target_session_count: int
    default_workout_size_preference: str
    status: str
    days: list[WeeklyTrainingPlanDay] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
