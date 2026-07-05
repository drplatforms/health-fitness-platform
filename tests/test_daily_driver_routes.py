from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.daily_driver as daily_driver_routes
from api.main import app
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
            workout_id="plan_321",
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


def test_daily_driver_today_route_returns_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_driver_routes,
        "build_daily_driver_today_response",
        lambda user_id, target_date=None: _response(),
    )

    client = TestClient(app)
    response = client.get("/api/today", params={"user_id": 102, "date": "2026-07-04"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "daily_driver_today_v0"
    assert payload["next_action"]["type"] == "start_workout"
    assert payload["coach_note"] == {"enabled": False, "text": None}
    assert "provider_output" not in str(payload)


def test_daily_driver_today_route_maps_value_error_to_404(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_driver_routes,
        "build_daily_driver_today_response",
        lambda user_id, target_date=None: (_ for _ in ()).throw(ValueError("bad user")),
    )

    client = TestClient(app)
    response = client.get("/api/today", params={"user_id": 999})

    assert response.status_code == 404
    assert response.json()["detail"] == "bad user"
