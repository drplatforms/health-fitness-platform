from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.main import app
from tests.test_workout_progression_history_service import (
    _insert_completed_plan,
    _seed_test_db,
)


def _payload(exercise_name: str = "Bench Press") -> dict:
    return {
        "target_date": "2026-07-16",
        "exercises": [
            {
                "exercise_name": exercise_name,
                "catalog_exercise_id": None,
                "sets": 3,
                "reps_min": 8,
                "reps_max": 12,
                "rir_min": 1,
                "rir_max": 3,
            }
        ],
    }


def test_progression_decision_endpoint_returns_bounded_user_scoped_guidance(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        user_id=1,
        actual_reps=[10, 10, 10],
        actual_weights=[25.0, 25.0, 25.0],
        actual_rirs=[2, 2, 2],
        notes="Private progression note.",
    )
    _insert_completed_plan(user_id=2, exercise_name="Squat")
    client = TestClient(app)

    response = client.post(
        "/workout-plans/1/progression-decisions",
        json=_payload(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["target_date"] == "2026-07-16"
    decision = payload["progression_decisions"][0]
    assert decision["decision"] == "progress_reps"
    assert decision["reference_weight"] == 25.0
    assert set(decision) == {
        "exercise_name",
        "catalog_exercise_id",
        "decision",
        "headline",
        "target_guidance",
        "why_this_recommendation",
        "reason_codes",
        "evidence_session_count",
        "confidence",
        "reference_weight",
        "recovery_brake_applied",
    }
    serialized = str(payload).lower()
    assert "private progression note" not in serialized
    assert "actual_rows" not in serialized


def test_progression_decision_endpoint_builds_recovery_once_and_applies_brake(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(actual_reps=[10, 10, 10], actual_rirs=[2, 2, 2])
    calls: list[tuple[int, str]] = []

    def fake_recovery(user_id: int, target_date: str):
        calls.append((user_id, target_date))
        return SimpleNamespace(
            readiness_classification="recovery_limited",
            fatigue_support="unknown",
        )

    monkeypatch.setattr(
        "api.routes.workout_plans.build_recovery_intelligence_v2",
        fake_recovery,
    )
    client = TestClient(app)

    response = client.post(
        "/workout-plans/1/progression-decisions",
        json={
            **_payload(),
            "exercises": [
                _payload()["exercises"][0],
                {
                    **_payload("Squat")["exercises"][0],
                    "exercise_name": "Squat",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert calls == [(1, "2026-07-16")]
    decision = response.json()["progression_decisions"][0]
    assert decision["decision"] == "hold"
    assert decision["recovery_brake_applied"] is True


def test_progression_decision_endpoint_requires_structured_current_exercises(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post(
        "/workout-plans/1/progression-decisions",
        json={"target_date": "2026-07-16", "exercises": []},
    )

    assert response.status_code == 422
