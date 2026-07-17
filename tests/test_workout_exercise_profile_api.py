from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from services.workout_exercise_profile_service import (
    MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE,
)
from tests.test_workout_exercise_profile_service import _seed_profile_test_db


def test_exercise_profile_api_create_resolve_update_reset_and_delete(
    tmp_path, monkeypatch
) -> None:
    catalog_ids = _seed_profile_test_db(tmp_path, monkeypatch)
    catalog_id = catalog_ids[0]
    client = TestClient(app)

    create_response = client.put(
        "/workout-plans/1/exercise-profiles",
        json={
            "catalog_exercise_id": catalog_id,
            "familiarity_state": "learning",
            "preference_state": "favorite",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()["profile"]
    assert created["catalog_exercise_id"] == catalog_id
    assert created["familiarity_state"] == "learning"
    assert created["preference_state"] == "favorite"

    resolve_response = client.post(
        "/workout-plans/1/exercise-profiles/resolve",
        json={"catalog_exercise_ids": [catalog_id, catalog_ids[1]]},
    )
    assert resolve_response.status_code == 200
    assert resolve_response.json()["resolved_exercises"] == [
        {
            "requested_catalog_exercise_id": catalog_id,
            "profile": created,
        },
        {
            "requested_catalog_exercise_id": catalog_ids[1],
            "profile": None,
        },
    ]

    reset_response = client.put(
        "/workout-plans/1/exercise-profiles",
        json={
            "catalog_exercise_id": catalog_id,
            "familiarity_state": None,
            "preference_state": None,
        },
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["profile"] is None

    delete_response = client.delete(f"/workout-plans/1/exercise-profiles/{catalog_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is False


def test_exercise_profile_api_enforces_catalog_validation_user_isolation_and_bounds(
    tmp_path, monkeypatch
) -> None:
    catalog_ids = _seed_profile_test_db(tmp_path, monkeypatch)
    client = TestClient(app)
    catalog_id = catalog_ids[0]

    owner_response = client.put(
        "/workout-plans/1/exercise-profiles",
        json={
            "catalog_exercise_id": catalog_id,
            "familiarity_state": "familiar",
            "preference_state": "disliked",
        },
    )
    assert owner_response.status_code == 200

    other_user_response = client.post(
        "/workout-plans/2/exercise-profiles/resolve",
        json={"catalog_exercise_ids": [catalog_id]},
    )
    assert other_user_response.status_code == 200
    assert other_user_response.json()["resolved_exercises"][0]["profile"] is None

    missing_catalog_response = client.put(
        "/workout-plans/1/exercise-profiles",
        json={
            "catalog_exercise_id": 999999,
            "familiarity_state": "familiar",
            "preference_state": None,
        },
    )
    assert missing_catalog_response.status_code == 404

    invalid_state_response = client.put(
        "/workout-plans/1/exercise-profiles",
        json={
            "catalog_exercise_id": catalog_id,
            "familiarity_state": "expert",
            "preference_state": None,
        },
    )
    assert invalid_state_response.status_code == 422

    oversized_response = client.post(
        "/workout-plans/1/exercise-profiles/resolve",
        json={
            "catalog_exercise_ids": list(
                range(1, MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE + 2)
            )
        },
    )
    assert oversized_response.status_code == 422
