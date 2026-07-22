from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

import database
from api.main import app
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)


def _seed_empty_database(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "longitudinal_api.db")
    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, name, starting_weight) VALUES (2, 'Other User', 175)"
    )
    conn.commit()
    conn.close()


def test_longitudinal_insight_endpoint_is_user_scoped_and_read_only(
    tmp_path, monkeypatch
) -> None:
    _seed_empty_database(tmp_path, monkeypatch)

    with TestClient(app) as client:
        user_one = client.get(
            "/insights/longitudinal/1",
            params={"as_of_date": "2026-07-20", "max_insights": 5},
        )
        user_two = client.get(
            "/insights/longitudinal/2",
            params={"target_date": "2026-07-20", "max_insights": 5},
        )

    assert user_one.status_code == 200
    assert user_two.status_code == 200
    assert user_one.json() == {
        "success": True,
        "user_id": 1,
        "as_of_date": "2026-07-20",
        "target_date": "2026-07-20",
        "engine_version": "longitudinal_insight_engine_v1",
        "insights": [],
    }
    assert user_two.json()["user_id"] == 2
    assert user_two.json()["as_of_date"] == "2026-07-20"
    assert user_two.json()["insights"] == []


def test_longitudinal_insight_endpoint_bounds_feed_size(tmp_path, monkeypatch) -> None:
    _seed_empty_database(tmp_path, monkeypatch)

    with TestClient(app) as client:
        response = client.get(
            "/insights/longitudinal/1",
            params={"target_date": "2026-07-20", "max_insights": 11},
        )

    assert response.status_code == 422


def test_longitudinal_insight_endpoint_defaults_to_today_and_rejects_conflicting_aliases(
    tmp_path, monkeypatch
) -> None:
    _seed_empty_database(tmp_path, monkeypatch)

    with TestClient(app) as client:
        current = client.get("/insights/longitudinal/1")
        conflict = client.get(
            "/insights/longitudinal/1",
            params={"as_of_date": "2026-07-20", "target_date": "2026-07-19"},
        )

    assert current.status_code == 200
    assert current.json()["as_of_date"] == date.today().isoformat()
    assert current.json()["target_date"] == date.today().isoformat()
    assert conflict.status_code == 422
    assert "must match" in conflict.json()["detail"]
