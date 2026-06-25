from __future__ import annotations

from dataclasses import dataclass

MIN_WORKOUT_EXERCISE_COUNT = 3
MAX_WORKOUT_EXERCISE_COUNT = 7
DEFAULT_WORKOUT_SIZE_PREFERENCE = "standard"

_WORKOUT_SIZE_TO_COUNT = {
    "quick": 3,
    "standard": 5,
    "full": 6,
}
_ALLOWED_SIZE_PREFERENCES = set(_WORKOUT_SIZE_TO_COUNT)


@dataclass(frozen=True)
class ResolvedWorkoutExerciseCount:
    requested_size: str
    requested_count: int
    final_count: int
    min_allowed: int
    max_allowed: int
    clamp_reason: str
    user_safe_reason: str


def normalize_workout_size_preference(value: str | None) -> str:
    normalized = (value or DEFAULT_WORKOUT_SIZE_PREFERENCE).strip().lower()
    if normalized not in _ALLOWED_SIZE_PREFERENCES:
        return DEFAULT_WORKOUT_SIZE_PREFERENCE
    return normalized


def _clamp_requested_count(value: int | None, fallback: int) -> int:
    if value is None:
        return fallback
    return max(MIN_WORKOUT_EXERCISE_COUNT, min(MAX_WORKOUT_EXERCISE_COUNT, int(value)))


def _user_safe_reason(requested_size: str, final_count: int, clamp_reason: str) -> str:
    if clamp_reason == "recovery_limited":
        return f"Shortened to {final_count} exercises today to keep the session manageable."
    if clamp_reason == "data_quality_limited":
        return f"Built as a {final_count}-exercise session while the coach keeps the plan easy to review."
    if requested_size == "quick":
        return f"Built as a quick {final_count}-exercise session."
    if requested_size == "full":
        return f"Built as a fuller {final_count}-exercise session."
    return f"Built as a standard {final_count}-exercise session."


def resolve_workout_exercise_count(
    *,
    requested_size: str | None = None,
    requested_target_count: int | None = None,
    scenario: str | None = None,
    confidence: str | None = None,
    available_candidate_count: int | None = None,
) -> ResolvedWorkoutExerciseCount:
    """Resolve a user-facing workout size into a safe deterministic target count.

    The user preference is an input, not an override. Recovery/data-quality
    constraints may shorten the final target. Candidate availability can also
    reduce the target, but this service never raises volume above the approved
    v1 maximum of seven exercises.
    """

    normalized_size = normalize_workout_size_preference(requested_size)
    mapped_count = _WORKOUT_SIZE_TO_COUNT[normalized_size]
    requested_count = _clamp_requested_count(requested_target_count, mapped_count)

    final_count = requested_count
    clamp_reason = f"{normalized_size}_session"

    normalized_scenario = (scenario or "").strip().lower()
    normalized_confidence = (confidence or "").strip().lower()

    if normalized_scenario == "recovery_limited":
        final_count = min(final_count, 4)
        clamp_reason = "recovery_limited"
    elif normalized_scenario == "data_quality_limited" and final_count > 5:
        final_count = 5
        clamp_reason = "data_quality_limited"
    elif normalized_confidence == "limited" and final_count > 5:
        final_count = 5
        clamp_reason = "data_quality_limited"

    if available_candidate_count is not None:
        final_count = min(final_count, max(0, int(available_candidate_count)))
        if final_count < requested_count:
            clamp_reason = "available_exercises_limited"

    final_count = max(
        MIN_WORKOUT_EXERCISE_COUNT,
        min(MAX_WORKOUT_EXERCISE_COUNT, final_count),
    )

    return ResolvedWorkoutExerciseCount(
        requested_size=normalized_size,
        requested_count=requested_count,
        final_count=final_count,
        min_allowed=MIN_WORKOUT_EXERCISE_COUNT,
        max_allowed=MAX_WORKOUT_EXERCISE_COUNT,
        clamp_reason=clamp_reason,
        user_safe_reason=_user_safe_reason(normalized_size, final_count, clamp_reason),
    )
