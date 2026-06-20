from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.daily_coach as daily_coach_routes
from api.main import app
from services.daily_coach_today_card_service import build_daily_coach_today_card
from tests.test_daily_coach_today_card_service import FORBIDDEN_NORMAL_TERMS, _action


def test_today_card_route_returns_public_safe_card(monkeypatch):
    def fake_build_card(user_id: int, *, target_date: str | None = None):
        assert user_id == 102
        assert target_date == "2026-06-20"
        return build_daily_coach_today_card(
            user_id,
            target_date=target_date,
            action=_action(),
        )

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_today_card",
        fake_build_card,
    )

    client = TestClient(app)
    response = client.get("/daily-coach/102/today-card", params={"date": "2026-06-20"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 102
    card = payload["today_card"]
    assert card["card_title"] == "Today’s Coach Note"
    assert card["next_action_title"] == "Log a meal or snack"
    assert card["cta_label"] == "Next action: Log a meal or snack"
    assert card["cta_target"] == "nutrition_quick_log"
    assert "developer_metadata" not in card
    assert "display_source" not in card
    assert "is_provider_generated" not in card

    public_text = str(payload).lower()
    for term in FORBIDDEN_NORMAL_TERMS:
        assert term not in public_text


def test_today_card_route_does_not_call_narrative_preview_provider(monkeypatch):
    def preview_should_not_run(*args, **kwargs):
        raise AssertionError("Normal Today card route must not call preview provider.")

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_narrative_preview",
        preview_should_not_run,
    )
    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_today_card",
        lambda user_id, target_date=None: build_daily_coach_today_card(
            user_id,
            target_date=target_date,
            action=_action(),
        ),
    )

    client = TestClient(app)
    response = client.get("/daily-coach/102/today-card")

    assert response.status_code == 200
    assert response.json()["today_card"]["card_title"] == "Today’s Coach Note"


def test_today_card_route_maps_validation_error_to_400(monkeypatch):
    from services.daily_coach_today_card_service import (
        DailyCoachTodayCardValidationError,
    )

    def fake_build_card(*args, **kwargs):
        raise DailyCoachTodayCardValidationError("bad card")

    monkeypatch.setattr(
        daily_coach_routes,
        "build_daily_coach_today_card",
        fake_build_card,
    )

    client = TestClient(app)
    response = client.get("/daily-coach/102/today-card")

    assert response.status_code == 400
    assert response.json()["detail"] == "bad card"
