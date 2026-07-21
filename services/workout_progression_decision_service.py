from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal

from services.workout_progression_history_service import (
    DEFAULT_LOOKBACK_DAYS,
    ExerciseProgressionSession,
    load_completed_exercise_progression_sessions,
)

ProgressionDecisionCode = Literal[
    "increase_load",
    "increase_reps",
    "hold",
    "decrease_load",
    "build_baseline",
]
SessionClassification = Literal[
    "top_range",
    "within_range",
    "regression",
    "mixed",
]

PROGRESSION_HISTORY_LIMIT = 6


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


@dataclass(frozen=True)
class _ClassifiedSession:
    classification: SessionClassification
    required_rows: list[dict[str, Any]]
    reference_weight: float


def build_workout_progression_decisions(
    *,
    user_id: int,
    current_exercises: Iterable[CurrentExercisePrescription | dict[str, Any]],
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> list[WorkoutProgressionDecision]:
    """Build deterministic advisory targets without mutating workout state."""

    return [
        build_exercise_progression_decision(
            user_id=user_id,
            current_exercise=_coerce_current_exercise(exercise),
            lookback_days=lookback_days,
        )
        for exercise in current_exercises
    ]


def build_exercise_progression_decision(
    *,
    user_id: int,
    current_exercise: CurrentExercisePrescription,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> WorkoutProgressionDecision:
    if current_exercise.measurement_type != "reps":
        return _build_baseline_decision(
            current_exercise,
            reason_codes=["unsupported_measurement_type_for_progression_v1"],
            why="Load-based progression is not available for this measurement type.",
        )

    if not _has_complete_rep_prescription(current_exercise):
        return _build_baseline_decision(
            current_exercise,
            reason_codes=["incomplete_current_prescription"],
            why="A complete rep and RIR prescription is needed for progression.",
        )

    sessions = load_completed_exercise_progression_sessions(
        user_id=user_id,
        exercise_name=current_exercise.exercise_name,
        catalog_exercise_id=current_exercise.catalog_exercise_id,
        lookback_days=lookback_days,
        limit=PROGRESSION_HISTORY_LIMIT,
    )
    if not sessions:
        return _build_baseline_decision(
            current_exercise,
            reason_codes=["no_completed_history"],
            why="There is not enough completed set history for this exercise yet.",
        )

    # An incomplete or skipped exercise is not a failed exposure. Ignore it and
    # use only completed, consistently loaded working-set evidence.
    classified_sessions = [
        classified
        for session in sessions
        if (classified := _classify_session(session, current_exercise)) is not None
    ]
    if not classified_sessions:
        return _build_baseline_decision(
            current_exercise,
            reason_codes=["no_trustworthy_completed_exposure"],
            why=(
                "Complete load, rep, set, and RIR history is needed before "
                "progression can be recommended."
            ),
        )

    latest = classified_sessions[0]
    second = classified_sessions[1] if len(classified_sessions) > 1 else None
    reference_weight = latest.reference_weight

    if latest.classification == "top_range":
        return _decision(
            current_exercise,
            decision="increase_load",
            headline="Increase load",
            target_guidance=_target_line(
                current_exercise,
                decision="increase_load",
                reference_weight=reference_weight,
            ),
            why=(
                "The most recent completed exposure reached the top of the rep "
                "range across every working set while preserving the RIR target."
            ),
            reason_codes=["latest_completed_exposure_top_range"],
            evidence_session_count=1,
            confidence="Moderate",
            reference_weight=reference_weight,
        )

    if latest.classification == "within_range":
        return _decision(
            current_exercise,
            decision="increase_reps",
            headline="Increase reps",
            target_guidance=_target_line(
                current_exercise,
                decision="increase_reps",
                reference_weight=reference_weight,
            ),
            why=(
                "The most recent completed exposure was inside the prescribed "
                "rep and RIR ranges, with room to build toward the top."
            ),
            reason_codes=["latest_completed_exposure_within_range"],
            evidence_session_count=1,
            confidence="Moderate",
            reference_weight=reference_weight,
        )

    if latest.classification == "regression":
        if second is not None and second.classification == "regression":
            return _decision(
                current_exercise,
                decision="decrease_load",
                headline="Decrease load",
                target_guidance=_target_line(
                    current_exercise,
                    decision="decrease_load",
                    reference_weight=reference_weight,
                ),
                why=(
                    "The last two trustworthy completed exposures both fell "
                    "below the rep and RIR floors across multiple working sets."
                ),
                reason_codes=["two_consecutive_completed_regressions"],
                evidence_session_count=2,
                confidence="Moderate",
                reference_weight=reference_weight,
            )
        return _decision(
            current_exercise,
            decision="hold",
            headline="Hold",
            target_guidance=_target_line(
                current_exercise,
                decision="hold",
                reference_weight=reference_weight,
            ),
            why="One difficult completed exposure is not enough to reduce the load.",
            reason_codes=["single_completed_regression"],
            evidence_session_count=1,
            confidence="Low",
            reference_weight=reference_weight,
        )

    return _decision(
        current_exercise,
        decision="hold",
        headline="Hold",
        target_guidance=_target_line(
            current_exercise,
            decision="hold",
            reference_weight=reference_weight,
        ),
        why="The most recent completed exposure was mixed and does not earn a change.",
        reason_codes=["latest_completed_exposure_mixed"],
        evidence_session_count=1,
        confidence="Low",
        reference_weight=reference_weight,
    )


def _classify_session(
    session: ExerciseProgressionSession,
    current_exercise: CurrentExercisePrescription,
) -> _ClassifiedSession | None:
    required_rows = _required_working_rows(session, current_exercise.sets)
    if required_rows is None:
        return None

    reference_weight = _consistent_reference_weight(required_rows)
    if reference_weight is None:
        return None

    reps_min = int(current_exercise.reps_min)  # guarded by prescription validation
    reps_max = int(current_exercise.reps_max)
    rir_min = int(current_exercise.rir_min)

    # RIR is treated as a safety floor: more reps in reserve never invalidates
    # otherwise complete evidence or forces a load increase by itself.
    if all(
        int(row["actual_reps"]) >= reps_max and int(row["actual_rir"]) >= rir_min
        for row in required_rows
    ):
        classification: SessionClassification = "top_range"
    elif all(
        int(row["actual_reps"]) >= reps_min and int(row["actual_rir"]) >= rir_min
        for row in required_rows
    ):
        classification = "within_range"
    else:
        regressed_sets = sum(
            1
            for row in required_rows
            if int(row["actual_reps"]) < reps_min and int(row["actual_rir"]) < rir_min
        )
        classification = (
            "regression" if regressed_sets * 2 >= len(required_rows) else "mixed"
        )

    return _ClassifiedSession(classification, required_rows, reference_weight)


def _required_working_rows(
    session: ExerciseProgressionSession,
    prescribed_set_count: int,
) -> list[dict[str, Any]] | None:
    if prescribed_set_count <= 0:
        return None

    rows_by_set_number: dict[int, dict[str, Any]] = {}
    for row in session.actual_rows:
        try:
            set_number = int(row.get("set_number"))
        except (TypeError, ValueError):
            continue
        if 1 <= set_number <= prescribed_set_count:
            rows_by_set_number.setdefault(set_number, row)

    required_rows = [
        rows_by_set_number.get(set_number)
        for set_number in range(1, prescribed_set_count + 1)
    ]
    if any(row is None for row in required_rows):
        return None

    typed_rows = [row for row in required_rows if row is not None]
    if any(
        not _is_truthy(row.get("completed"))
        or _is_truthy(row.get("skipped"))
        or row.get("actual_reps") is None
        or row.get("actual_rir") is None
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
    current_exercise: CurrentExercisePrescription | None = None,
) -> float | None:
    """Return one conservative comparable load for a complete exposure."""

    if current_exercise is None:
        required_rows = _required_working_rows(session, session.planned_set_count)
        return (
            None
            if required_rows is None
            else _consistent_reference_weight(required_rows)
        )
    classified = _classify_session(session, current_exercise)
    return None if classified is None else classified.reference_weight


def _build_baseline_decision(
    current_exercise: CurrentExercisePrescription,
    *,
    reason_codes: list[str],
    why: str,
) -> WorkoutProgressionDecision:
    return _decision(
        current_exercise,
        decision="build_baseline",
        headline="Build baseline",
        target_guidance=_baseline_target_line(current_exercise),
        why=why,
        reason_codes=reason_codes,
        evidence_session_count=0,
        confidence="Limited",
    )


def _target_line(
    current_exercise: CurrentExercisePrescription,
    *,
    decision: ProgressionDecisionCode,
    reference_weight: float,
) -> str:
    rep_range = _format_range(current_exercise.reps_min, current_exercise.reps_max)
    if decision == "increase_load":
        load = "Next practical load"
    elif decision == "decrease_load":
        load = f"Lighter than {_format_weight(reference_weight)} lb"
    else:
        load = f"{_format_weight(reference_weight)} lb"
    return f"{load} × {rep_range}"


def _baseline_target_line(current_exercise: CurrentExercisePrescription) -> str:
    if current_exercise.measurement_type == "duration":
        seconds = current_exercise.target_duration_seconds
        if seconds is None:
            return "Follow the current prescription"
        return f"{seconds // 60} min" if seconds % 60 == 0 else f"{seconds} sec"
    if current_exercise.measurement_type == "distance":
        meters = current_exercise.target_distance_meters
        if meters is None:
            return "Follow the current prescription"
        display = str(int(meters)) if float(meters).is_integer() else f"{meters:.1f}"
        return f"{display} m"

    rep_range = _format_range(current_exercise.reps_min, current_exercise.reps_max)
    if current_exercise.rir_min is None or current_exercise.rir_max is None:
        return f"{rep_range} reps"
    rir_range = _format_range(current_exercise.rir_min, current_exercise.rir_max)
    return f"{rep_range} reps · RIR {rir_range}"


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
    )


def _has_complete_rep_prescription(
    current_exercise: CurrentExercisePrescription,
) -> bool:
    return (
        current_exercise.sets > 0
        and current_exercise.reps_min is not None
        and current_exercise.reps_max is not None
        and current_exercise.reps_max >= current_exercise.reps_min
        and current_exercise.rir_min is not None
        and current_exercise.rir_max is not None
        and current_exercise.rir_max >= current_exercise.rir_min
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


def _format_range(minimum: int | None, maximum: int | None) -> str:
    if minimum is None and maximum is None:
        return "current target"
    if minimum is None:
        return str(maximum)
    if maximum is None or minimum == maximum:
        return str(minimum)
    return f"{minimum}–{maximum}"


def _format_weight(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def _is_truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
