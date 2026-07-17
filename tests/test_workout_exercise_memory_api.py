from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from services.workout_exercise_memory_service import (
    MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE,
    MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS,
    save_workout_exercise_memory,
)
from tests.test_workout_exercise_memory_service import _seed_memory_test_db


def test_exercise_memory_api_create_resolve_update_and_delete(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    create_response = client.put(
        "/workout-plans/1/exercise-memories",
        json={
            "catalog_exercise_id": 55,
            "exercise_name": "Dumbbell Row",
            "memory_text": "Rack 12.",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()["memory"]
    assert created["catalog_exercise_id"] == 55
    assert created["memory_text"] == "Rack 12."

    resolve_response = client.post(
        "/workout-plans/1/exercise-memories/resolve",
        json={
            "exercises": [
                {
                    "catalog_exercise_id": 55,
                    "exercise_name": "Dumbbell Row",
                }
            ]
        },
    )
    assert resolve_response.status_code == 200
    resolved = resolve_response.json()["resolved_exercises"][0]
    assert resolved["requested_catalog_exercise_id"] == 55
    assert resolved["requested_exercise_name"] == "Dumbbell Row"
    assert resolved["memory"] == created

    update_response = client.put(
        "/workout-plans/1/exercise-memories",
        json={
            "memory_id": created["memory_id"],
            "catalog_exercise_id": 55,
            "exercise_name": "Dumbbell Row",
            "memory_text": "Rack 12. Neutral grip.",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["memory"]["memory_text"] == ("Rack 12. Neutral grip.")

    delete_response = client.delete(
        f"/workout-plans/1/exercise-memories/{created['memory_id']}"
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_memory_id"] == created["memory_id"]

    resolved_after_delete = client.post(
        "/workout-plans/1/exercise-memories/resolve",
        json={
            "exercises": [
                {
                    "catalog_exercise_id": 55,
                    "exercise_name": "Dumbbell Row",
                }
            ]
        },
    )
    assert resolved_after_delete.json()["resolved_exercises"][0]["memory"] is None


def test_exercise_memory_api_rejects_invalid_text_identity_and_batch(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    whitespace_response = client.put(
        "/workout-plans/1/exercise-memories",
        json={
            "catalog_exercise_id": 55,
            "exercise_name": "Dumbbell Row",
            "memory_text": "   ",
        },
    )
    assert whitespace_response.status_code == 400

    over_limit_response = client.put(
        "/workout-plans/1/exercise-memories",
        json={
            "catalog_exercise_id": 55,
            "exercise_name": "Dumbbell Row",
            "memory_text": "x" * (MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS + 1),
        },
    )
    assert over_limit_response.status_code == 422

    invalid_catalog_response = client.put(
        "/workout-plans/1/exercise-memories",
        json={
            "catalog_exercise_id": 0,
            "exercise_name": "Dumbbell Row",
            "memory_text": "Rack 12.",
        },
    )
    assert invalid_catalog_response.status_code == 422

    oversized_batch_response = client.post(
        "/workout-plans/1/exercise-memories/resolve",
        json={
            "exercises": [
                {
                    "catalog_exercise_id": index + 1,
                    "exercise_name": f"Exercise {index}",
                }
                for index in range(MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE + 1)
            ]
        },
    )
    assert oversized_batch_response.status_code == 422


def test_exercise_memory_api_enforces_user_ownership_for_update_and_delete(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    memory = save_workout_exercise_memory(
        1,
        catalog_exercise_id=55,
        exercise_name="Dumbbell Row",
        memory_text="User one memory.",
    )
    client = TestClient(app)

    resolve_other_user = client.post(
        "/workout-plans/2/exercise-memories/resolve",
        json={
            "exercises": [
                {
                    "catalog_exercise_id": 55,
                    "exercise_name": "Dumbbell Row",
                }
            ]
        },
    )
    assert resolve_other_user.status_code == 200
    assert resolve_other_user.json()["resolved_exercises"][0]["memory"] is None

    update_other_user = client.put(
        "/workout-plans/2/exercise-memories",
        json={
            "memory_id": memory.memory_id,
            "catalog_exercise_id": 55,
            "exercise_name": "Dumbbell Row",
            "memory_text": "Wrong user update.",
        },
    )
    assert update_other_user.status_code == 404

    delete_other_user = client.delete(
        f"/workout-plans/2/exercise-memories/{memory.memory_id}"
    )
    assert delete_other_user.status_code == 404

    owner_resolve = client.post(
        "/workout-plans/1/exercise-memories/resolve",
        json={
            "exercises": [
                {
                    "catalog_exercise_id": 55,
                    "exercise_name": "Dumbbell Row",
                }
            ]
        },
    )
    assert (
        owner_resolve.json()["resolved_exercises"][0]["memory"]["memory_text"]
        == "User one memory."
    )


def test_exercise_memory_api_batch_deduplicates_and_associates_fallback(
    tmp_path, monkeypatch
) -> None:
    _seed_memory_test_db(tmp_path, monkeypatch)
    fallback = save_workout_exercise_memory(
        1,
        catalog_exercise_id=None,
        exercise_name="Dumbbell Row",
        memory_text="Legacy fallback.",
    )
    client = TestClient(app)

    response = client.post(
        "/workout-plans/1/exercise-memories/resolve",
        json={
            "exercises": [
                {
                    "catalog_exercise_id": 55,
                    "exercise_name": "Dumbbell Row",
                },
                {
                    "catalog_exercise_id": 55,
                    "exercise_name": "Dumbbell Row alias",
                },
            ]
        },
    )

    assert response.status_code == 200
    resolutions = response.json()["resolved_exercises"]
    assert len(resolutions) == 1
    assert resolutions[0]["requested_catalog_exercise_id"] == 55
    assert resolutions[0]["memory"]["memory_id"] == fallback.memory_id
