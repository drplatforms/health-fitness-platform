from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "weekly_api.db")
    seed_qa_scenarios()
    return TestClient(app)


def test_create_get_update_and_missing_weekly_plan(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    missing = client.get(
        "/weekly-training-plans/102?week_start_date=2026-07-13&current_date=2026-07-12"
    )
    assert missing.status_code == 200
    assert missing.json()["plan"] is None

    created = client.post(
        "/weekly-training-plans/102",
        json={
            "week_start_date": "2026-07-15",
            "training_weekdays": [0, 2, 4],
            "default_workout_size_preference": "standard",
            "current_date": "2026-07-12",
        },
    )
    assert created.status_code == 200
    plan = created.json()["plan"]
    assert plan["week_start_date"] == "2026-07-13"

    fetched = client.get(
        "/weekly-training-plans/102?week_start_date=2026-07-15&current_date=2026-07-12"
    )
    assert fetched.status_code == 200
    assert fetched.json()["plan"]["id"] == plan["id"]

    updated = client.patch(
        f"/weekly-training-plans/102/{plan['id']}",
        json={
            "training_weekdays": [1, 3, 5, 6],
            "default_workout_size_preference": "extended",
            "current_date": "2026-07-12",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["plan"]["target_session_count"] == 4


def test_api_validation_duplicate_week_and_cross_user_update(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    base_payload = {
        "week_start_date": "2026-07-13",
        "training_weekdays": [0, 2, 4],
        "default_workout_size_preference": "standard",
        "current_date": "2026-07-12",
    }
    created = client.post("/weekly-training-plans/102", json=base_payload)
    assert created.status_code == 200
    plan_id = created.json()["plan"]["id"]

    duplicate = client.post("/weekly-training-plans/102", json=base_payload)
    assert duplicate.status_code == 409

    for weekdays in ([], list(range(7)), [0, 0, 2]):
        invalid = client.post(
            "/weekly-training-plans/101",
            json={**base_payload, "training_weekdays": weekdays},
        )
        assert invalid.status_code == 400

    invalid_date = client.get("/weekly-training-plans/102?week_start_date=not-a-date")
    assert invalid_date.status_code == 400

    cross_user = client.patch(
        f"/weekly-training-plans/101/{plan_id}",
        json={
            "training_weekdays": [1, 3, 5],
            "default_workout_size_preference": "standard",
            "current_date": "2026-07-12",
        },
    )
    assert cross_user.status_code == 404


def test_api_protected_date_edit_rejects_without_partial_update(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/weekly-training-plans/102",
        json={
            "week_start_date": "2026-07-13",
            "training_weekdays": [0, 2, 4],
            "default_workout_size_preference": "standard",
            "current_date": "2026-07-14",
        },
    )
    plan_id = created.json()["plan"]["id"]

    rejected = client.patch(
        f"/weekly-training-plans/102/{plan_id}",
        json={
            "training_weekdays": [1, 3, 5],
            "default_workout_size_preference": "extended",
            "current_date": "2026-07-14",
        },
    )
    assert rejected.status_code == 409
    assert "No changes were saved" in rejected.json()["detail"]

    unchanged = client.get(
        "/weekly-training-plans/102?week_start_date=2026-07-13&current_date=2026-07-14"
    ).json()["plan"]
    assert unchanged["default_workout_size_preference"] == "standard"
    assert [
        day["day_index"] for day in unchanged["days"] if day["day_type"] == "training"
    ] == [0, 2, 4]
