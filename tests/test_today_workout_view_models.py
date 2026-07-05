from __future__ import annotations

import pytest

from models.today_workout_view_models import (
    TodayWorkoutExerciseItem,
    TodayWorkoutResponse,
)


def _response() -> TodayWorkoutResponse:
    return TodayWorkoutResponse(
        user_id=102,
        target_date="2026-07-05",
        status="selected",
        title="Upper Body Strength",
        summary="5 planned exercises focused on upper body strength.",
        source="current_execution_state",
        workout_id="plan_123",
        generated_at="2026-07-05T08:00:00",
        estimated_duration_minutes=45,
        focus="Upper body strength",
        equipment=["dumbbell", "bench"],
        exercises=[
            TodayWorkoutExerciseItem(
                exercise_id="planned_1",
                name="Incline Dumbbell Press",
                order=1,
                section="Main Session",
                sets=3,
                reps="8-10",
                weight=None,
                weight_unit=None,
                rest_seconds=None,
                tempo=None,
                notes="Controlled reps.",
                substitution_notes=None,
            )
        ],
        data_gaps=[],
        limitations=[],
    )


def test_valid_today_workout_response_can_be_created() -> None:
    response = _response()

    assert response.user_id == 102
    assert response.contract_version == "today_workout_view_v0"
    assert response.exercises[0].name == "Incline Dumbbell Press"


def test_invalid_status_fails() -> None:
    with pytest.raises(ValueError, match="status"):
        TodayWorkoutResponse(
            user_id=102,
            target_date="2026-07-05",
            status="planned",
            title="Workout",
            summary="Summary",
            source="current_execution_state",
            workout_id=None,
            generated_at=None,
            estimated_duration_minutes=None,
            focus=None,
        )


def test_exercise_requires_positive_order() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        TodayWorkoutExerciseItem(
            exercise_id=None,
            name="Squat",
            order=0,
            section=None,
            sets=3,
            reps="5",
            weight=None,
            weight_unit=None,
            rest_seconds=None,
            tempo=None,
            notes=None,
            substitution_notes=None,
        )


def test_serialization_shape_is_stable() -> None:
    payload = _response().to_dict()

    assert payload["contract_version"] == "today_workout_view_v0"
    assert payload["status"] == "selected"
    assert payload["source"] == "current_execution_state"
    assert payload["exercises"][0]["reps"] == "8-10"
