from dataclasses import asdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.routes.workouts as workouts_route
import database
from api.main import app
from services.exercise_catalog_service import (
    clear_exercise_catalog_cache,
    get_exercise_catalog,
    get_exercise_catalog_entry_by_id,
    get_exercise_instruction,
    get_exercise_taxonomy,
    seed_exercise_catalog,
    seed_exercise_form_media,
    seed_exercise_instructions,
    seed_exercise_taxonomy,
)


@pytest.fixture(autouse=True)
def pytest_owned_database(tmp_path, monkeypatch):
    test_db = tmp_path / "fitness_ai_instruction_api_test.db"
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert test_db.resolve() != canonical_db.resolve()

    monkeypatch.setattr(database, "DB_PATH", test_db)
    monkeypatch.delenv("EXERCISE_VISUAL_MEDIA_PROVIDER", raising=False)
    clear_exercise_catalog_cache()
    yield test_db
    clear_exercise_catalog_cache()


def _initialize_and_seed_instructions():
    database.initialize_database()
    instructions = seed_exercise_instructions()
    seed_exercise_taxonomy()
    return instructions


def _instruction_row_counts() -> tuple[int, int]:
    conn = database.get_connection()
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_count,
            COUNT(DISTINCT exercise_id) AS distinct_count
        FROM exercise_catalog_instructions
        """
    ).fetchone()
    conn.close()
    return row["total_count"], row["distinct_count"]


def test_valid_catalog_id_returns_complete_persisted_instruction_contract():
    instructions = _initialize_and_seed_instructions()
    instruction = instructions[0]
    exercise = get_exercise_catalog_entry_by_id(instruction.catalog_exercise_id)
    taxonomy = get_exercise_taxonomy(instruction.catalog_exercise_id)
    assert exercise is not None
    assert taxonomy is not None

    response = TestClient(app).get(
        f"/exercise-catalog/{instruction.catalog_exercise_id}/instruction"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["exercise"] == asdict(exercise)
    assert payload["instruction"] == asdict(instruction)
    assert payload["form_media"] == []
    assert payload["visual_media"] == []
    assert payload["visual_media_resolution"] == {
        "requested_catalog_exercise_id": instruction.catalog_exercise_id,
        "visual_identity_slug": taxonomy.visual_identity_slug,
        "resolution_mode": "none",
        "source_type": "none",
        "source_catalog_exercise_id": None,
        "provider": None,
        "provider_exercise_id": None,
    }
    assert (
        response.json()["instruction"]["catalog_exercise_id"]
        == response.json()["exercise"]["id"]
    )


def test_instruction_response_exposes_no_second_identity_or_persistence_fields():
    instruction = _initialize_and_seed_instructions()[0]

    response = TestClient(app).get(
        f"/exercise-catalog/{instruction.catalog_exercise_id}/instruction"
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload["instruction"]) == {
        "catalog_exercise_id",
        "overview",
        "setup_steps",
        "execution_steps",
        "form_cues",
        "common_mistakes",
        "safety_notes",
    }
    assert "id" not in payload["instruction"]
    assert not any(key.endswith("_json") for key in payload["instruction"])
    assert "created_at" not in payload["instruction"]
    assert "updated_at" not in payload["instruction"]


def test_covered_instruction_response_includes_ordered_local_form_media():
    _initialize_and_seed_instructions()
    seed_exercise_form_media()
    covered = next(
        entry
        for entry in get_exercise_catalog()
        if entry.name == "Incline Dumbbell Press"
    )
    assert covered.id is not None

    response = TestClient(app).get(f"/exercise-catalog/{covered.id}/instruction")

    assert response.status_code == 200
    assert [asset["media_key"] for asset in response.json()["form_media"]] == [
        "start",
        "finish",
    ]
    assert all(
        asset["catalog_exercise_id"] == covered.id
        and asset["asset_path"].startswith("/exercise-media/free-exercise-db/")
        for asset in response.json()["form_media"]
    )
    assert {asset["source_exercise_id"] for asset in response.json()["form_media"]} == {
        "Incline_Dumbbell_Press"
    }
    assert (
        response.json()["visual_media_resolution"]["resolution_mode"] == "direct_local"
    )
    assert {
        asset["source_catalog_exercise_id"] for asset in response.json()["visual_media"]
    } == {covered.id}


def test_uncovered_instruction_response_remains_text_only_after_media_expansion():
    _initialize_and_seed_instructions()
    seed_exercise_form_media()
    uncovered = next(
        entry for entry in get_exercise_catalog() if entry.name == "Back Squat"
    )
    assert uncovered.id is not None

    response = TestClient(app).get(f"/exercise-catalog/{uncovered.id}/instruction")

    assert response.status_code == 200
    assert response.json()["form_media"] == []
    assert response.json()["visual_media"] == []
    assert response.json()["visual_media_resolution"]["resolution_mode"] == "none"


def test_configured_free_v1_instruction_response_is_normalized_without_a_key(
    monkeypatch,
):
    _initialize_and_seed_instructions()
    seed_exercise_form_media()
    monkeypatch.setenv("EXERCISE_VISUAL_MEDIA_PROVIDER", "ascendapi_free_v1")
    provider_backed = next(
        entry for entry in get_exercise_catalog() if entry.name == "Back Squat"
    )
    assert provider_backed.id is not None

    response = TestClient(app).get(
        f"/exercise-catalog/{provider_backed.id}/instruction"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["form_media"] == []
    assert payload["visual_media_resolution"] == {
        "requested_catalog_exercise_id": provider_backed.id,
        "visual_identity_slug": "visual_back_squat",
        "resolution_mode": "provider",
        "source_type": "remote_provider",
        "source_catalog_exercise_id": None,
        "provider": "ascendapi_free_v1",
        "provider_exercise_id": "DhMl549",
    }
    assert payload["visual_media"][0]["media_type"] == "animated_image"
    assert payload["visual_media"][0]["url"].endswith("/DhMl549.gif")
    assert "ExerciseDB / AscendAPI Free V1" in response.text
    assert "non-commercial prototype phase" in response.text


def test_unknown_catalog_id_returns_bounded_exercise_not_found_response():
    instructions = _initialize_and_seed_instructions()
    unknown_id = max(item.catalog_exercise_id for item in instructions) + 1_000

    response = TestClient(app).get(f"/exercise-catalog/{unknown_id}/instruction")

    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}


def test_known_catalog_exercise_without_instruction_fails_without_fabrication():
    database.initialize_database()
    seed_exercise_catalog()
    exercise = get_exercise_catalog()[0]
    assert exercise.id is not None
    assert get_exercise_instruction(exercise.id) is None

    response = TestClient(app).get(f"/exercise-catalog/{exercise.id}/instruction")

    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise instruction not found"}


def test_public_instruction_lookup_accepts_only_positive_stable_ids():
    instruction = _initialize_and_seed_instructions()[0]

    id_response = TestClient(app).get(
        f"/exercise-catalog/{instruction.catalog_exercise_id}/instruction"
    )
    name_response = TestClient(app).get("/exercise-catalog/Push-Up/instruction")
    nonpositive_response = TestClient(app).get("/exercise-catalog/0/instruction")

    assert id_response.status_code == 200
    assert name_response.status_code == 422
    assert nonpositive_response.status_code == 422


def test_catalog_entry_service_lookup_uses_positive_persisted_id_only():
    instructions = _initialize_and_seed_instructions()
    catalog_exercise_id = instructions[0].catalog_exercise_id

    entry = get_exercise_catalog_entry_by_id(catalog_exercise_id)

    assert entry is not None
    assert entry.id == catalog_exercise_id
    assert get_exercise_catalog_entry_by_id(10_000) is None
    with pytest.raises(
        ValueError,
        match="catalog_exercise_id must be a positive integer",
    ):
        get_exercise_catalog_entry_by_id(0)


def test_existing_exercise_catalog_response_remains_instruction_free(monkeypatch):
    expected_exercise = {
        "id": 27,
        "name": "Back Squat",
        "exercise_type": "strength",
        "movement_pattern": "squat",
        "primary_muscle_groups": ["quadriceps", "glutes"],
        "equipment_required": ["barbell", "plates", "rack"],
        "difficulty": "intermediate",
    }
    monkeypatch.setattr(
        workouts_route,
        "get_exercise_catalog_dicts",
        lambda: [expected_exercise],
    )

    response = TestClient(app).get("/exercise-catalog")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "exercises": [expected_exercise],
    }
    assert "instruction" not in response.json()["exercises"][0]


def test_existing_exercises_response_remains_unchanged(monkeypatch):
    expected_exercise = {
        "id": 1,
        "name": "Barbell Bench Press",
        "muscle_group": "Chest",
        "equipment": "Barbell",
    }
    monkeypatch.setattr(
        workouts_route,
        "get_all_exercises",
        lambda: [expected_exercise],
    )

    response = TestClient(app).get("/exercises")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "exercises": [expected_exercise],
    }


def test_fastapi_lifespan_seeds_complete_instruction_coverage():
    assert not Path(database.DB_PATH).exists()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert _instruction_row_counts() == (240, 240)


def test_repeated_fastapi_lifespan_initialization_is_idempotent():
    with TestClient(app):
        first_counts = _instruction_row_counts()
    with TestClient(app):
        second_counts = _instruction_row_counts()

    assert first_counts == second_counts == (240, 240)


def test_api_tests_are_bound_to_pytest_owned_database(pytest_owned_database):
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"

    assert Path(database.DB_PATH).resolve() == pytest_owned_database.resolve()
    assert Path(database.DB_PATH).resolve() != canonical_db.resolve()
