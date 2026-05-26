from dataclasses import dataclass, field


@dataclass
class ExerciseCatalogEntry:
    id: int | None
    name: str
    exercise_type: str
    movement_pattern: str
    primary_muscle_groups: list[str] = field(default_factory=list)
    equipment_required: list[str] = field(default_factory=list)
    difficulty: str = "intermediate"
