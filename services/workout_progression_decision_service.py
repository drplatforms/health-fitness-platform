from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal

from models.recovery_intelligence_v2_models import RecoveryIntelligenceV2Summary
from services.workout_progression_history_service import (
    DEFAULT_LOOKBACK_DAYS,
    ExerciseProgressionSession,
    load_completed_exercise_progression_sessions,
)

ProgressionDecisionCode = Literal[
    "progress_reps",
    "increase_load",
    "hold",
    "ease_back",
    "insufficient_data",
]
SessionClassification = Literal[
    "top_range",
    "within_range",
    "underperformance",
    "mixed",
]


@dataclass(frozen=True)
class CurrentExercisePrescription:
    exercise_name: str
    catalog_exercise_id: int | None
    sets: int
    reps_min: int | None
    reps_max: int | None
    rir_min: int | None
    rir_max: int | None
    measurement_type: str = "reps"
    target_duration_seconds: int | None = None
    target_distance_meters: float | None = None


@dataclass(frozen=True)
class WorkoutProgressionDecision:
    exercise_name: str
    catalog_exercise_id: int | None
    decision: ProgressionDecisionCode
    headline: str
    target_guidance: str
    why_this_recommendation: str
    reason_codes: list[str]
    evidence_session_count: int
    confidence: str
    reference_weight: float | None
    recovery_brake_applied: bool


@dataclass(frozen=True)
class _ClassifiedSession:
    classification: SessionClassification
    required_rows: list[dict[str, Any]]


def build_workout_progression_decisions(
    *,
    user_id: int,
    current_exercises: Iterable[CurrentExercisePrescription | dict[str, Any]],
    recovery: RecoveryIntelligenceV2Summary,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> list[WorkoutProgressionDecision]:
    """Build bounded advisory decisions without mutating workout state."""

    return [
        build_exercise_progression_decision(
            user_id=user_id,
            current_exercise=_coerce_current_exercise(exercise),
            recovery=recovery,
            lookback_days=lookback_days,
        )
        for exercise in current_exercises
    ]


def build_exercise_progression_decision(
    *,
    user_id: int,
    current_exercise: CurrentExercisePrescription,
    recovery: RecoveryIntelligenceV2Summary,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> WorkoutProgressionDecision:
    if current_exercise.measurement_type in {"duration", "distance"}:
        return _decision(
            current_exercise,
            decision="insufficient_data",
            headline="Follow the plan",
            target_guidance=("Follow the planned primary measurement target today."),
            why=(
                "Automated duration and distance progression is not supported "
                "in this version."
            ),
            reason_codes=["unsupported_measurement_type_for_progression_v1"],
            evidence_session_count=0,
            confidence="Limited",
        )

    sessions = load_completed_exercise_progression_sessions(
        user_id=user_id,
        exercise_name=current_exercise.exercise_name,
        catalog_exercise_id=current_exercise.catalog_exercise_id,
        lookback_days=lookback_days,
        limit=2,
    )
    if not sessions:
        return _decision(
            current_exercise,
            decision="insufficient_data",
            headline="Follow the plan",
            target_guidance=("Follow the planned rep and effort targets today."),
            why=(
                "More complete recent set history is needed before progression "
                "guidance is available."
            ),
            reason_codes=["no_completed_history", "reference_weight_unavailable"],
            evidence_session_count=0,
            confidence="Limited",
        )

    latest = _classify_session(sessions[0])
    if latest is None:
        return _decision(
            current_exercise,
            decision="insufficient_data",
            headline="Follow the plan",
            target_guidance=("Follow the planned rep and effort targets today."),
            why=(
                "The most recent completed session does not have complete rep "
                "and effort evidence for every required working set."
            ),
            reason_codes=[
                "latest_history_incomplete",
                "reference_weight_unavailable",
            ],
            evidence_session_count=0,
            confidence="Limited",
        )

    second = _classify_session(sessions[1]) if len(sessions) > 1 else None
    reference_weight = comparable_working_weight(sessions[0])
    reference_reason = (
        "consistent_reference_weight_available"
        if reference_weight is not None
        else "reference_weight_unavailable"
    )

    if latest.classification == "top_range":
        if second is not None and second.classification == "top_range":
            decision_code: ProgressionDecisionCode = "increase_load"
            headline = "Increase difficulty"
            target_guidance = _increase_load_guidance(reference_weight)
            why = (
                "You reached the top of the prescribed rep range at the target "
                "effort in the last two qualifying sessions."
            )
            reason_codes = [
                "two_consecutive_top_range_sessions",
                reference_reason,
            ]
            evidence_count = 2
            confidence = "Moderate"
        else:
            decision_code = "progress_reps"
            headline = "Repeat the top range"
            target_guidance = _repeat_top_range_guidance(reference_weight)
            why = (
                "The latest session is the first recent top-range confirmation; "
                "repeat it once more before increasing resistance."
            )
            reason_codes = [
                "latest_session_top_range_first_confirmation",
                reference_reason,
            ]
            evidence_count = 1
            confidence = "Low"
    elif latest.classification == "within_range":
        decision_code = "progress_reps"
        headline = "Add reps"
        target_guidance = _progress_reps_guidance(reference_weight)
        why = (
            "Last time you completed the planned work inside the target rep and "
            "effort ranges."
        )
        reason_codes = ["latest_session_within_range", reference_reason]
        evidence_count = 1
        confidence = "Low"
    elif latest.classification == "underperformance":
        if second is not None and second.classification == "underperformance":
            decision_code = "ease_back"
            headline = "Ease back"
            target_guidance = (
                "Use a slightly easier load, resistance, or setup today and "
                "rebuild clean reps inside the target range."
            )
            why = (
                "The two most recent qualifying sessions both fell below the "
                "planned rep and effort floors on at least half of the required sets."
            )
            reason_codes = [
                "two_consecutive_underperformance_sessions",
                reference_reason,
            ]
            evidence_count = 2
            confidence = "Moderate"
        else:
            decision_code = "hold"
            headline = "Hold steady"
            target_guidance = (
                "Keep the load and rep target steady today. Focus on clean "
                "execution inside the planned effort range."
            )
            why = (
                "The latest session was harder than planned, but one difficult "
                "session is not enough to recommend easing back."
            )
            reason_codes = ["latest_session_underperformed_once", reference_reason]
            evidence_count = 1
            confidence = "Low"
    else:
        decision_code = "hold"
        headline = "Hold steady"
        target_guidance = (
            "Keep the load and rep target steady today. Focus on clean execution "
            "inside the planned effort range."
        )
        why = (
            "The latest complete session was mixed and does not justify an upward "
            "or downward progression."
        )
        reason_codes = ["latest_session_mixed", reference_reason]
        evidence_count = 1
        confidence = "Low"

    recovery_brake_applied = False
    if decision_code in {"progress_reps", "increase_load"} and _recovery_brakes(
        recovery
    ):
        decision_code = "hold"
        headline = "Hold progression"
        target_guidance = (
            "Hold progression today and work within the current planned rep and "
            "effort targets."
        )
        why = (
            "Recent performance supports moving forward, but current recovery is "
            "explicitly limiting."
        )
        reason_codes = [
            *reason_codes,
            "recovery_limited_progression_brake",
        ]
        recovery_brake_applied = True

    return _decision(
        current_exercise,
        decision=decision_code,
        headline=headline,
        target_guidance=target_guidance,
        why=why,
        reason_codes=reason_codes,
        evidence_session_count=evidence_count,
        confidence=confidence,
        reference_weight=reference_weight,
        recovery_brake_applied=recovery_brake_applied,
    )


def _classify_session(
    session: ExerciseProgressionSession,
) -> _ClassifiedSession | None:
    required_rows = _required_working_rows(session)
    if required_rows is None:
        return None

    if all(
        int(row["actual_reps"]) >= int(row["planned_reps_max"])
        and int(row["actual_rir"]) >= int(row["planned_rir_min"])
        for row in required_rows
    ):
        return _ClassifiedSession("top_range", required_rows)

    if all(
        int(row["actual_reps"]) >= int(row["planned_reps_min"])
        and int(row["actual_rir"]) >= int(row["planned_rir_min"])
        for row in required_rows
    ):
        return _ClassifiedSession("within_range", required_rows)

    underperforming_sets = sum(
        1
        for row in required_rows
        if int(row["actual_reps"]) < int(row["planned_reps_min"])
        and int(row["actual_rir"]) < int(row["planned_rir_min"])
    )
    if underperforming_sets * 2 >= len(required_rows):
        return _ClassifiedSession("underperformance", required_rows)

    return _ClassifiedSession("mixed", required_rows)


def _required_working_rows(
    session: ExerciseProgressionSession,
) -> list[dict[str, Any]] | None:
    if session.planned_set_count <= 0:
        return None

    rows_by_set_number: dict[int, dict[str, Any]] = {}
    for row in session.actual_rows:
        try:
            set_number = int(row.get("set_number"))
        except (TypeError, ValueError):
            continue
        if 1 <= set_number <= session.planned_set_count:
            rows_by_set_number.setdefault(set_number, row)

    required_rows = [
        rows_by_set_number.get(set_number)
        for set_number in range(1, session.planned_set_count + 1)
    ]
    if any(row is None for row in required_rows):
        return None

    typed_rows = [row for row in required_rows if row is not None]
    required_fields = (
        "actual_reps",
        "actual_rir",
        "planned_reps_min",
        "planned_reps_max",
        "planned_rir_min",
        "planned_rir_max",
    )
    if any(
        not _is_truthy(row.get("completed"))
        or _is_truthy(row.get("skipped"))
        or any(row.get(field) is None for field in required_fields)
        for row in typed_rows
    ):
        return None
    return typed_rows


def _consistent_reference_weight(rows: list[dict[str, Any]]) -> float | None:
    weights: list[float] = []
    for row in rows:
        value = row.get("actual_weight")
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric <= 0:
            return None
        weights.append(numeric)
    if not weights or any(weight != weights[0] for weight in weights[1:]):
        return None
    return weights[0]


def comparable_working_weight(
    session: ExerciseProgressionSession,
) -> float | None:
    """Return one conservative comparable load using progression eligibility."""

    classified = _classify_session(session)
    if classified is None:
        return None
    return _consistent_reference_weight(classified.required_rows)


def _recovery_brakes(recovery: RecoveryIntelligenceV2Summary) -> bool:
    return (
        recovery.readiness_classification == "recovery_limited"
        or recovery.fatigue_support == "limiting"
    )


def _progress_reps_guidance(reference_weight: float | None) -> str:
    load = (
        f"Keep {_format_weight(reference_weight)} lb"
        if reference_weight is not None
        else "Keep the load or resistance similar"
    )
    return (
        f"{load} and add a rep where you can while staying inside the target "
        "effort range."
    )


def _repeat_top_range_guidance(reference_weight: float | None) -> str:
    load = (
        f"Keep {_format_weight(reference_weight)} lb"
        if reference_weight is not None
        else "Keep the load or resistance similar"
    )
    return (
        f"{load} and repeat the top of the rep range with the target effort once "
        "more before increasing resistance."
    )


def _increase_load_guidance(reference_weight: float | None) -> str:
    if reference_weight is not None:
        return (
            f"Move up from {_format_weight(reference_weight)} lb to the next "
            "practical load, then work back toward the lower end of the current "
            "rep range."
        )
    return (
        "Increase resistance or difficulty by the next practical step, then work "
        "back toward the lower end of the current rep range."
    )


def _decision(
    current_exercise: CurrentExercisePrescription,
    *,
    decision: ProgressionDecisionCode,
    headline: str,
    target_guidance: str,
    why: str,
    reason_codes: list[str],
    evidence_session_count: int,
    confidence: str,
    reference_weight: float | None = None,
    recovery_brake_applied: bool = False,
) -> WorkoutProgressionDecision:
    return WorkoutProgressionDecision(
        exercise_name=current_exercise.exercise_name,
        catalog_exercise_id=current_exercise.catalog_exercise_id,
        decision=decision,
        headline=headline,
        target_guidance=target_guidance,
        why_this_recommendation=why,
        reason_codes=reason_codes,
        evidence_session_count=evidence_session_count,
        confidence=confidence,
        reference_weight=reference_weight,
        recovery_brake_applied=recovery_brake_applied,
    )


def _coerce_current_exercise(
    value: CurrentExercisePrescription | dict[str, Any],
) -> CurrentExercisePrescription:
    if isinstance(value, CurrentExercisePrescription):
        return value
    return CurrentExercisePrescription(
        exercise_name=str(value["exercise_name"]).strip(),
        catalog_exercise_id=(
            None
            if value.get("catalog_exercise_id") is None
            else int(value["catalog_exercise_id"])
        ),
        sets=int(value["sets"]),
        reps_min=(None if value.get("reps_min") is None else int(value["reps_min"])),
        reps_max=(None if value.get("reps_max") is None else int(value["reps_max"])),
        rir_min=(None if value.get("rir_min") is None else int(value["rir_min"])),
        rir_max=(None if value.get("rir_max") is None else int(value["rir_max"])),
        measurement_type=str(value.get("measurement_type") or "reps"),
        target_duration_seconds=(
            None
            if value.get("target_duration_seconds") is None
            else int(value["target_duration_seconds"])
        ),
        target_distance_meters=(
            None
            if value.get("target_distance_meters") is None
            else float(value["target_distance_meters"])
        ),
    )


def _format_weight(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def _is_truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
