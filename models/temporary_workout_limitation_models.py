from dataclasses import dataclass, field


@dataclass
class TemporaryWorkoutLimitation:
    user_id: int
    affected_regions: list[str] = field(default_factory=list)
    restricted_movement_patterns: list[str] = field(default_factory=list)
    excluded_catalog_exercise_ids: list[int] = field(default_factory=list)
    expires_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class WorkoutLimitationConflict:
    planned_exercise_id: int | None
    exercise_name: str
    conflict_type: str
    movement_pattern: str | None = None
