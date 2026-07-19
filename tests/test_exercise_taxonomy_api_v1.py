from dataclasses import asdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app
from services import exercise_catalog_service


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    path = tmp_path / "taxonomy_api.db"
    canonical_path = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert path.resolve() != canonical_path.resolve()
    monkeypatch.setattr(database, "DB_PATH", path)
    exercise_catalog_service.clear_exercise_catalog_cache()
    yield path
    exercise_catalog_service.clear_exercise_catalog_cache()


def _seeded_entry(name):
    database.initialize_database()
    exercise_catalog_service.seed_exercise_taxonomy()
    return next(
        entry
        for entry in exercise_catalog_service.get_exercise_catalog()
        if entry.name == name
    )


def test_taxonomy_api_returns_representative_reviewed_contract():
    entry = _seeded_entry("Incline Dumbbell Press")
    response = TestClient(app).get(f"/exercise-catalog/{entry.id}/taxonomy")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "success": True,
        "exercise": asdict(entry),
        "taxonomy": {
            "family": "horizontal_press",
            "base_movement": "bench_press",
            "visual_identity": "visual_incline_dumbbell_press",
            "status": "reviewed",
            "variants": {
                "support_type": "bench",
                "bench_angle": "incline",
            },
        },
    }
    assert entry.equipment_required
    assert "equipment_required" not in payload["taxonomy"]["variants"]
    assert "equipment" not in payload["taxonomy"]["variants"]


def test_taxonomy_api_returns_review_and_alias_status_boundaries():
    _seeded_entry("Barbell Squat")
    entries = {
        entry.name: entry
        for entry in exercise_catalog_service.get_exercise_catalog()
        if entry.name in {"Barbell Squat", "Dead Hang"}
    }
    client = TestClient(app)

    review_response = client.get(
        f"/exercise-catalog/{entries['Barbell Squat'].id}/taxonomy"
    )
    assert review_response.status_code == 200
    assert review_response.json()["taxonomy"] == {
        "family": "bilateral_knee_dominant",
        "base_movement": "barbell_squat_unspecified",
        "visual_identity": "visual_barbell_squat",
        "status": "review_required",
        "variants": {},
    }

    alias_response = client.get(f"/exercise-catalog/{entries['Dead Hang'].id}/taxonomy")
    assert alias_response.status_code == 200
    assert alias_response.json()["taxonomy"] == {
        "family": "vertical_pull",
        "base_movement": "bar_hang",
        "visual_identity": "visual_dead_hang",
        "status": "alias_candidate",
        "variants": {"execution_mode": "isometric"},
    }


def test_taxonomy_api_extension_output_is_deterministic():
    entry = _seeded_entry("Push Press")
    client = TestClient(app)
    first = client.get(f"/exercise-catalog/{entry.id}/taxonomy")
    second = client.get(f"/exercise-catalog/{entry.id}/taxonomy")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["taxonomy"] == {
        "family": "vertical_press",
        "base_movement": "push_press",
        "visual_identity": "visual_push_press",
        "status": "reviewed",
        "variants": {"execution_mode": "dynamic"},
        "extensions": {"lower_body_drive": "deliberate"},
    }


def test_taxonomy_api_returns_404_for_unknown_exercise():
    database.initialize_database()
    exercise_catalog_service.seed_exercise_taxonomy()
    response = TestClient(app).get("/exercise-catalog/999999/taxonomy")
    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}


def test_taxonomy_api_returns_404_for_known_exercise_without_taxonomy():
    database.initialize_database()
    exercise_catalog_service.seed_exercise_catalog()
    entry = next(
        entry
        for entry in exercise_catalog_service.get_exercise_catalog()
        if entry.name == "Push-Up"
    )
    response = TestClient(app).get(f"/exercise-catalog/{entry.id}/taxonomy")
    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise taxonomy not found"}


@pytest.mark.parametrize("catalog_exercise_id", (0, -1))
def test_taxonomy_api_rejects_nonpositive_path_id(catalog_exercise_id):
    response = TestClient(app).get(f"/exercise-catalog/{catalog_exercise_id}/taxonomy")
    assert response.status_code == 422
