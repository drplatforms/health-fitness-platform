from __future__ import annotations

import pytest

from models.daily_driver_contract_models import (
    DailyDriverCoachNote,
    DailyDriverNextAction,
    DailyDriverNutritionSummary,
    DailyDriverReadinessSummary,
    DailyDriverTodayResponse,
    DailyDriverWorkoutSummary,
)


def _response() -> DailyDriverTodayResponse:
    return DailyDriverTodayResponse(
        user_id=102,
        target_date="2026-07-04",
        readiness=DailyDriverReadinessSummary(
            status="ready",
            headline="Ready to train",
            reason="Recovery signals support normal training today.",
            confidence="medium",
        ),
        workout=DailyDriverWorkoutSummary(
            planned=True,
            workout_id="plan_123",
            title="Upper Body Strength",
            summary="5 exercises",
            status="not_started",
            first_action_label="Start today's workout",
        ),
        nutrition=DailyDriverNutritionSummary(
            status="behind",
            calorie_target=2300,
            protein_target_g=180,
            calories_logged=900,
            protein_logged_g=72,
            today_mission="Get protein on track with your next meal.",
        ),
        next_action=DailyDriverNextAction(
            type="start_workout",
            label="Start today's workout",
            context="First exercise is incline dumbbell press.",
        ),
        coach_note=DailyDriverCoachNote(enabled=False, text=None),
        data_gaps=[],
        limitations=[],
    )


def test_valid_response_can_be_created() -> None:
    response = _response()

    assert response.user_id == 102
    assert response.target_date == "2026-07-04"
    assert response.contract_version == "daily_driver_today_v0"


def test_invalid_user_id_fails() -> None:
    with pytest.raises(ValueError, match="user_id"):
        DailyDriverTodayResponse(
            user_id=0,
            target_date="2026-07-04",
            readiness=_response().readiness,
            workout=_response().workout,
            nutrition=_response().nutrition,
            next_action=_response().next_action,
            coach_note=_response().coach_note,
        )


def test_missing_target_date_fails() -> None:
    with pytest.raises(ValueError, match="target_date"):
        DailyDriverTodayResponse(
            user_id=102,
            target_date="",
            readiness=_response().readiness,
            workout=_response().workout,
            nutrition=_response().nutrition,
            next_action=_response().next_action,
            coach_note=_response().coach_note,
        )


def test_invalid_status_values_fail() -> None:
    with pytest.raises(ValueError, match="readiness.status"):
        DailyDriverReadinessSummary(
            status="great",
            headline="Ready",
            reason="Reason",
            confidence="medium",
        )

    with pytest.raises(ValueError, match="workout.status"):
        DailyDriverWorkoutSummary(
            planned=True,
            workout_id="plan_1",
            title="Workout",
            summary="3 exercises",
            status="planned",
            first_action_label="Start",
        )


def test_next_action_requires_type_and_label() -> None:
    with pytest.raises(ValueError, match="next_action.type"):
        DailyDriverNextAction(type="", label="Start", context="Context")

    with pytest.raises(ValueError, match="next_action.label"):
        DailyDriverNextAction(type="start_workout", label="", context="Context")


def test_coach_note_rejects_markdown() -> None:
    with pytest.raises(ValueError, match="plain text only"):
        DailyDriverCoachNote(enabled=True, text="## Headline")


def test_coach_note_rejects_backend_metadata_terms() -> None:
    with pytest.raises(ValueError, match="forbidden internal metadata"):
        DailyDriverCoachNote(
            enabled=True,
            text="Daily plan from source_services looks good today.",
        )


def test_serialization_shape_is_stable() -> None:
    payload = _response().to_dict()

    assert payload["contract_version"] == "daily_driver_today_v0"
    assert payload["readiness"]["status"] == "ready"
    assert payload["workout"]["title"] == "Upper Body Strength"
    assert payload["nutrition"]["protein_target_g"] == 180
    assert payload["next_action"]["type"] == "start_workout"
    assert payload["coach_note"] == {"enabled": False, "text": None}
