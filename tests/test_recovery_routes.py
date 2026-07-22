from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.recovery as recovery_routes
from api.main import app


def test_get_recovery_checkin_returns_saved_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        recovery_routes,
        "get_recent_recovery_checkins",
        lambda user_id, limit=7: [],
    )
    monkeypatch.setattr(
        recovery_routes,
        "get_recovery_checkin",
        lambda user_id, target_date=None: {
            "id": 18,
            "user_id": user_id,
            "checkin_date": target_date or "2026-07-05",
            "body_weight": 190.0,
            "sleep_hours": 7.5,
            "energy_level": 7,
            "soreness_level": 3,
            "mood": "managed",
            "notes": "Pain/restriction: Left shoulder is tight.",
            "created_at": "2026-07-05 09:15:00",
        },
    )

    response = TestClient(app).get(
        "/recovery/checkins/101",
        params={"target_date": "2026-07-05"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["checkin"]["user_id"] == 101
    assert payload["checkin"]["checkin_date"] == "2026-07-05"
    assert payload["recent_checkins"] == []


def test_create_recovery_checkin_accepts_optional_fields(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _save(**kwargs):
        captured.update(kwargs)
        return 77

    monkeypatch.setattr(recovery_routes, "save_recovery_checkin", _save)

    response = TestClient(app).post(
        "/recovery/checkins",
        json={
            "user_id": 101,
            "target_date": "2026-07-05",
            "body_weight": 190.5,
            "sleep_hours": 7.0,
            "energy_level": 6,
            "soreness_level": 4,
            "mood": "high",
            "notes": "General notes: Keep today lighter.",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["checkin_id"] == 77
    assert captured == {
        "user_id": 101,
        "target_date": "2026-07-05",
        "body_weight": 190.5,
        "sleep_hours": 7.0,
        "sleep_quality": None,
        "energy_level": 6,
        "soreness_level": 4,
        "stress_level": None,
        "training_motivation": None,
        "pain_concern": None,
        "pain_area": None,
        "mood": "high",
        "notes": "General notes: Keep today lighter.",
    }


def test_create_recovery_checkin_accepts_structured_recovery_signals(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _save(**kwargs):
        captured.update(kwargs)
        return 88

    monkeypatch.setattr(recovery_routes, "save_recovery_checkin", _save)

    response = TestClient(app).post(
        "/recovery/checkins",
        json={
            "user_id": 101,
            "target_date": "2026-07-06",
            "sleep_hours": 7.5,
            "sleep_quality": 2,
            "energy_level": 7,
            "soreness_level": 3,
            "stress_level": 4,
            "training_motivation": 2,
            "pain_concern": "mild",
            "pain_area": "shoulder",
        },
    )

    assert response.status_code == 200
    assert captured["sleep_quality"] == 2
    assert captured["stress_level"] == 4
    assert captured["training_motivation"] == 2
    assert captured["pain_concern"] == "mild"
    assert captured["pain_area"] == "shoulder"


def test_create_recovery_checkin_rejects_out_of_range_signal() -> None:
    response = TestClient(app).post(
        "/recovery/checkins",
        json={
            "user_id": 101,
            "sleep_hours": 7.5,
            "sleep_quality": 6,
            "energy_level": 7,
            "soreness_level": 3,
        },
    )

    assert response.status_code == 422


def test_create_recovery_checkin_rejects_area_without_relevant_concern() -> None:
    response = TestClient(app).post(
        "/recovery/checkins",
        json={
            "user_id": 101,
            "sleep_hours": 7.5,
            "energy_level": 7,
            "soreness_level": 3,
            "pain_concern": "none",
            "pain_area": "knee",
        },
    )

    assert response.status_code == 422
