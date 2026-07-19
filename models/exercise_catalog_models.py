from dataclasses import dataclass, field

EXERCISE_PRESCRIPTION_MEASUREMENT_TYPES = frozenset({"reps", "duration", "distance"})
EXERCISE_PRESCRIPTION_LOAD_APPLICABILITIES = frozenset(
    {"applicable", "optional", "not_applicable", "ambiguous"}
)
EXERCISE_PRESCRIPTION_RIR_APPLICABILITIES = frozenset(
    {"applicable", "not_applicable", "ambiguous"}
)
EXERCISE_PRESCRIPTION_DISTANCE_UNITS = frozenset({"meters"})
EXERCISE_PROTOCOL_SLUGS = frozenset(
    {
        "intervals",
        "steady_state",
        "tempo",
        "pause",
        "easy",
        "hill_intervals",
        "recovery",
        "easy_intervals",
        "cadence_drill",
    }
)


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
class ExerciseFormMediaAsset:
    catalog_exercise_id: int
    media_key: str
    media_type: str
    asset_path: str
    alt_text: str
    caption: str | None
    sort_order: int
    source_name: str
    source_exercise_id: str
    source_url: str
    license_name: str
    license_url: str
    asset_sha256: str


@dataclass(frozen=True)
class ExerciseVisualMediaItem:
    """Provider-neutral media returned with an exercise instruction."""

    media_key: str
    media_type: str
    role: str
    url: str
    alt_text: str
    caption: str | None
    source_type: str
    source_catalog_exercise_id: int | None
    provider: str | None
    provider_exercise_id: str | None
    attribution: str | None
    provenance: str


@dataclass(frozen=True)
class ExerciseVisualMediaResolution:
    """How media for one requested catalog exercise was resolved."""

    requested_catalog_exercise_id: int
    visual_identity_slug: str | None
    resolution_mode: str
    source_type: str
    source_catalog_exercise_id: int | None
    provider: str | None
    provider_exercise_id: str | None


@dataclass
class ExerciseTaxonomyMetadata:
    catalog_exercise_id: int
    family_slug: str
    base_movement_slug: str
    visual_identity_slug: str
    taxonomy_status: str
    body_position: str | None = None
    support_type: str | None = None
    bench_angle: str | None = None
    laterality: str | None = None
    grip: str | None = None
    stance: str | None = None
    load_position: str | None = None
    attachment: str | None = None
    movement_direction: str | None = None
    locomotion_mode: str | None = None
    execution_mode: str | None = None
    variant_extensions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExercisePrescriptionMeasurementMetadata:
    catalog_exercise_id: int
    default_measurement_type: str
    allowed_measurement_types: tuple[str, ...]
    sets_applicable: bool
    load_applicability: str
    rir_applicability: str
    distance_unit: str | None = None


@dataclass(frozen=True)
class ExerciseProtocolTemplate:
    protocol_slug: str
    display_name: str
    description: str


@dataclass(frozen=True)
class ExerciseProtocolMetadata:
    catalog_exercise_id: int
    protocol_slug: str


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
