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
    assert payload["include_set_details"] is False
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
    assert payload["exercises"][0]["measurement_type"] == "reps"
    assert payload["exercises"][0]["modality"] == "externally_weighted"
    assert payload["exercises"][0]["progression_recommendation"] == {
        "decision": "increase_reps",
        "headline": "Increase reps",
        "target_guidance": "45 lb × 8–12",
        "evidence_session_count": 1,
        "confidence": "Moderate",
    }
    session = payload["exercises"][0]["recent_sessions"][0]
    assert session["performance_metric"]["label"] == "Load"
    assert session["has_set_details"] is False
    assert session["recorded_sets"] == []
    assert session["completed_sets"] == []
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
        "session_limit=401",
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


def test_exercise_history_summary_series_and_selected_session_detail_are_split(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _insert_plan(
        actual_reps=[12, 10, 8],
        actual_weights=[45.0, 45.0, 45.0],
        actual_rirs=[2, 1, 0],
        completed_flags=[1, 1, 0],
        skipped_flags=[0, 1, 0],
    )
    client = TestClient(app)

    summary_response = client.get(
        "/workout-plans/1/exercise-history-analytics?session_limit=400"
    )

    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    session = summary_payload["exercises"][0]["recent_sessions"][0]
    assert summary_payload["include_set_details"] is False
    assert session["has_set_details"] is False
    assert session["recorded_sets"] == []
    assert session["completed_sets"] == []

    detail_response = client.get(
        "/workout-plans/1/exercise-history-analytics/sessions/"
        f"{session['session_key']}?lookback_days=365"
    )

    assert detail_response.status_code == 200
    detail = detail_response.json()["session"]
    assert detail["session_key"] == session["session_key"]
    assert detail["has_set_details"] is True
    assert detail["completed_set_count"] == 1
    assert detail["planned_set_count"] == 3
    assert [
        (item["set_number"], item["completed"], item["skipped"])
        for item in detail["recorded_sets"]
    ] == [
        (1, True, False),
        (2, True, True),
        (3, False, False),
    ]
    assert [item["actual_reps"] for item in detail["completed_sets"]] == [12]

    other_user_response = client.get(
        "/workout-plans/2/exercise-history-analytics/sessions/"
        f"{session['session_key']}?lookback_days=365"
    )
    assert other_user_response.status_code == 404

    missing_response = client.get(
        "/workout-plans/1/exercise-history-analytics/sessions/not-a-real-key"
    )
    assert missing_response.status_code == 404
