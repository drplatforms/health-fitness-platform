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


@dataclass
class ExerciseInstruction:
    catalog_exercise_id: int
    overview: str
    setup_steps: list[str]
    execution_steps: list[str]
    form_cues: list[str]
    common_mistakes: list[str]
    safety_notes: list[str]


@dataclass
class ExerciseSubstitutionCandidate:
    catalog_exercise_id: int
    name: str
    movement_pattern: str
    required_equipment: list[str] = field(default_factory=list)
    primary_muscle_groups: list[str] = field(default_factory=list)
    exercise_type: str = "strength"
    difficulty: str = "intermediate"
    compatibility_reason_codes: list[str] = field(default_factory=list)
    rank: int = 0
    match_tier: str = "also_compatible"
    why_this_fits: str = ""
    ranking_reason_codes: list[str] = field(default_factory=list)
