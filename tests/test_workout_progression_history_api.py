from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from tests.test_workout_progression_history_service import (
    _insert_completed_plan,
    _seed_test_db,
)


def test_progression_history_endpoint_returns_user_scoped_summaries(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_completed_plan(
        user_id=1,
        exercise_name="Bench Press",
        actual_reps=[10, 10, 10],
        actual_weights=[25.0, 25.0, 25.0],
        actual_rirs=[2, 2, 2],
        notes="Private API note should not be returned.",
    )
    _insert_completed_plan(user_id=2, exercise_name="Squat")
    client = TestClient(app)

    response = client.post(
        "/workout-plans/1/progression-history",
        json={"exercise_names": ["Bench Press", "Squat"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["lookback_days"] == 90
    histories = payload["exercise_histories"]
    bench = histories[0]
    squat = histories[1]
    assert bench["exercise_name"] == "Bench Press"
    assert bench["has_history"] is True
    assert bench["last_session_summary"] == "3x10, @ 25 lb, RIR 2"
    assert bench["recent_best_set"]["summary"] == "10 reps @ 25 lb RIR 2"
    assert squat["has_history"] is False

    serialized = str(payload).lower()
    assert "private api note" not in serialized
    assert "actual_rows" not in serialized
    assert "notes" not in serialized


def test_progression_history_endpoint_handles_no_history_state(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post(
        "/workout-plans/1/progression-history",
        json={"exercise_names": ["Romanian Deadlift"]},
    )

    assert response.status_code == 200
    history = response.json()["exercise_histories"][0]
    assert history["has_history"] is False
    assert history["message"] == "No recent history for this exercise yet."
    assert history["recent_best_set"] is None


def test_progression_history_endpoint_respects_limit(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for day in range(1, 4):
        _insert_completed_plan(completed_at=f"2026-07-0{day}T10:00:00")
    client = TestClient(app)

    response = client.post(
        "/workout-plans/1/progression-history",
        json={"exercise_names": ["Bench Press"], "limit": 1},
    )

    assert response.status_code == 200
    history = response.json()["exercise_histories"][0]
    assert history["completed_session_count"] == 1
    assert history["last_performed_at"] == "2026-07-03"
