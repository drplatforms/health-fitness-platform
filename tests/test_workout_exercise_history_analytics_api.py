from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from tests.test_workout_exercise_history_analytics_service import (
    _insert_plan,
    _seed_test_db,
)


def test_exercise_history_analytics_endpoint_returns_bounded_public_contract(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(
        exercise_name="Bench Press",
        actual_reps=[10, 10, 10],
        actual_weights=[45.0, 45.0, 45.0],
        notes="Private API analytics note.",
    )

    response = TestClient(app).get(
        "/workout-plans/1/exercise-history-analytics",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 1
    assert payload["lookback_days"] == 180
    assert payload["exercise_limit"] == 24
    assert payload["session_limit"] == 8
    assert payload["overview"] == {
        "has_history": True,
        "completed_workout_count": 1,
        "completed_set_count": 3,
        "distinct_effective_exercise_count": 1,
        "most_recent_completed_workout_date": payload["exercises"][0][
            "last_performed_at"
        ],
    }
    assert payload["exercises"][0]["exercise_name"] == "Bench Press"
    assert payload["exercises"][0]["progression_recommendation"] == {
        "decision": "increase_reps",
        "headline": "Increase reps",
        "target_guidance": "45 lb × 8–12",
        "evidence_session_count": 1,
        "confidence": "Moderate",
    }
    assert payload["exercises"][0]["recent_sessions"][0]["completed_sets"] == [
        {
            "set_number": 1,
            "actual_reps": 10,
            "actual_weight": 45.0,
            "actual_rir": 2,
        },
        {
            "set_number": 2,
            "actual_reps": 10,
            "actual_weight": 45.0,
            "actual_rir": 2,
        },
        {
            "set_number": 3,
            "actual_reps": 10,
            "actual_weight": 45.0,
            "actual_rir": 2,
        },
    ]
    serialized = str(payload).lower()
    assert "private api analytics note" not in serialized
    assert "actual_rows" not in serialized
    assert "reason_codes" not in serialized


def test_exercise_history_analytics_query_bounds_are_enforced(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    for query in (
        "lookback_days=0",
        "lookback_days=366",
        "exercise_limit=0",
        "exercise_limit=49",
        "session_limit=0",
        "session_limit=13",
    ):
        response = client.get(f"/workout-plans/1/exercise-history-analytics?{query}")
        assert response.status_code == 422


def test_exercise_history_analytics_endpoint_returns_safe_empty_state(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    response = TestClient(app).get(
        "/workout-plans/1/exercise-history-analytics?exercise_limit=1&session_limit=1"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["overview"]["has_history"] is False
    assert payload["exercises"] == []
