from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

import api.routes.daily_driver as daily_driver_routes
import database
from api.main import app
from models.daily_driver_contract_models import (
    DailyDriverCoachNote,
    DailyDriverNextAction,
    DailyDriverNutritionSummary,
    DailyDriverReadinessSummary,
    DailyDriverTodayResponse,
    DailyDriverWorkoutSummary,
)
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
)
from services.nutrition_service import add_canonical_food_entry


def _today() -> str:
    return date.today().isoformat()


def _tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def _seed_today_route_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    seed_qa_scenarios()
    ensure_food_normalization_tables()


def _create_today_test_canonical_food() -> int:
    canonical_food = create_canonical_food("Today Route Test Food", "generic")
    create_canonical_food_nutrient(canonical_food.id, "Calories", "kcal", 200)
    create_canonical_food_nutrient(canonical_food.id, "Protein", "g", 25)
    create_canonical_food_nutrient(canonical_food.id, "Carbohydrate", "g", 30)
    create_canonical_food_nutrient(canonical_food.id, "Fat", "g", 10)
    return canonical_food.id


def _response() -> DailyDriverTodayResponse:
    return DailyDriverTodayResponse(
        user_id=102,
        target_date="2026-07-04",
        readiness=DailyDriverReadinessSummary(
            status="ready",
            headline="Ready to train",
            reason="Recovery signals support normal training today.",
            confidence="medium",
            score=90,
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
            carbohydrate_target_g=240,
            fat_target_g=75,
            calories_logged=900,
            protein_logged_g=72,
            carbs_logged_g=120,
            fat_logged_g=35,
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
    assert payload["readiness"]["score"] == 90
    assert payload["nutrition"]["carbohydrate_target_g"] == 240
    assert payload["nutrition"]["fat_logged_g"] == 35
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


def test_daily_driver_today_route_reflects_canonical_logged_food_totals(
    tmp_path, monkeypatch
) -> None:
    _seed_today_route_db(tmp_path, monkeypatch)
    canonical_food_id = _create_today_test_canonical_food()
    client = TestClient(app)

    before = client.get("/api/today", params={"user_id": 102, "date": _today()})
    other_user_before = client.get(
        "/api/today", params={"user_id": 103, "date": _today()}
    )
    assert before.status_code == 200
    assert other_user_before.status_code == 200

    add_canonical_food_entry(
        user_id=102,
        canonical_food_id=canonical_food_id,
        grams=100,
        entry_date=_today(),
    )

    after = client.get("/api/today", params={"user_id": 102, "date": _today()})
    other_user = client.get("/api/today", params={"user_id": 103, "date": _today()})

    assert after.status_code == 200
    assert other_user.status_code == 200
    before_nutrition = before.json()["nutrition"]
    after_nutrition = after.json()["nutrition"]

    assert (
        after_nutrition["calories_logged"] == before_nutrition["calories_logged"] + 200
    )
    assert (
        after_nutrition["protein_logged_g"] == before_nutrition["protein_logged_g"] + 25
    )
    assert after_nutrition["carbs_logged_g"] == before_nutrition["carbs_logged_g"] + 30
    assert after_nutrition["fat_logged_g"] == before_nutrition["fat_logged_g"] + 10
    assert other_user.json()["nutrition"] == other_user_before.json()["nutrition"]


def test_daily_driver_today_route_returns_clean_not_logged_payload_for_empty_day(
    tmp_path, monkeypatch
) -> None:
    _seed_today_route_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/api/today", params={"user_id": 102, "date": _tomorrow()})

    assert response.status_code == 200
    assert response.json()["nutrition"]["status"] == "not_logged"
    assert response.json()["nutrition"]["calories_logged"] is None
    assert response.json()["nutrition"]["protein_logged_g"] is None
    assert response.json()["nutrition"]["carbs_logged_g"] is None
    assert response.json()["nutrition"]["fat_logged_g"] is None
