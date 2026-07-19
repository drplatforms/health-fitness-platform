"""Repository-owned protocol-template registry and canonical exercise links."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExerciseProtocolTemplateSeed:
    protocol_slug: str
    display_name: str
    description: str


@dataclass(frozen=True)
class ExerciseProtocolSeed:
    canonical_exercise_name: str
    protocol_slug: str


EXERCISE_PROTOCOL_TEMPLATES: tuple[ExerciseProtocolTemplateSeed, ...] = (
    ExerciseProtocolTemplateSeed(
        "intervals", "Intervals", "Alternating programmed work and recovery periods."
    ),
    ExerciseProtocolTemplateSeed(
        "steady_state", "Steady State", "Sustained continuous effort."
    ),
    ExerciseProtocolTemplateSeed(
        "tempo", "Tempo", "Controlled, deliberate movement tempo."
    ),
    ExerciseProtocolTemplateSeed(
        "pause", "Pause", "A deliberate pause within the movement."
    ),
    ExerciseProtocolTemplateSeed("easy", "Easy", "Intentionally easy effort."),
    ExerciseProtocolTemplateSeed(
        "hill_intervals",
        "Hill Intervals",
        "Alternating effort organized around hill work.",
    ),
    ExerciseProtocolTemplateSeed(
        "recovery", "Recovery", "Intentionally low-demand recovery-oriented effort."
    ),
    ExerciseProtocolTemplateSeed(
        "easy_intervals", "Easy Intervals", "Easy-effort work organized into intervals."
    ),
    ExerciseProtocolTemplateSeed(
        "cadence_drill",
        "Cadence Drill",
        "A cycling drill centered on cadence practice.",
    ),
)


EXERCISE_PROTOCOL_SEEDS: tuple[ExerciseProtocolSeed, ...] = (
    ExerciseProtocolSeed("Treadmill Intervals", "intervals"),
    ExerciseProtocolSeed("Bike Steady State", "steady_state"),
    ExerciseProtocolSeed("Bike Intervals", "intervals"),
    ExerciseProtocolSeed("Tempo Push-Up", "tempo"),
    ExerciseProtocolSeed("Pause Squat", "pause"),
    ExerciseProtocolSeed("Treadmill Easy Jog", "easy"),
    ExerciseProtocolSeed("Treadmill Hill Intervals", "hill_intervals"),
    ExerciseProtocolSeed("Treadmill Tempo Run", "tempo"),
    ExerciseProtocolSeed("Bike Recovery Ride", "recovery"),
    ExerciseProtocolSeed("Bike Tempo Ride", "tempo"),
    ExerciseProtocolSeed("Bike Hill Intervals", "hill_intervals"),
    ExerciseProtocolSeed("Dumbbell Tempo Goblet Squat", "tempo"),
    ExerciseProtocolSeed("Treadmill Recovery Walk", "recovery"),
    ExerciseProtocolSeed("Treadmill Easy Intervals", "easy_intervals"),
    ExerciseProtocolSeed("Bike Easy Spin", "easy"),
    ExerciseProtocolSeed("Bike Cadence Drill", "cadence_drill"),
)
