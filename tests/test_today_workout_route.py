from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.daily_driver as daily_driver_routes
from api.main import app
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
        workout_id="plan_321",
        generated_at="2026-07-05T07:15:00",
        estimated_duration_minutes=45,
        focus="Upper body strength",
        equipment=["dumbbell", "bench"],
        exercises=[
            TodayWorkoutExerciseItem(
                exercise_id="planned_777",
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


def test_today_workout_route_returns_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_driver_routes,
        "build_today_workout_response",
        lambda user_id, target_date=None: _response(),
    )

    client = TestClient(app)
    response = client.get(
        "/api/today/workout",
        params={"user_id": 102, "date": "2026-07-05"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "today_workout_view_v0"
    assert payload["status"] == "selected"
    assert payload["exercises"][0]["name"] == "Incline Dumbbell Press"


def test_today_workout_route_maps_value_error_to_404(monkeypatch) -> None:
    monkeypatch.setattr(
        daily_driver_routes,
        "build_today_workout_response",
        lambda user_id, target_date=None: (_ for _ in ()).throw(ValueError("bad user")),
    )

    client = TestClient(app)
    response = client.get("/api/today/workout", params={"user_id": 999})

    assert response.status_code == 404
    assert response.json()["detail"] == "bad user"
