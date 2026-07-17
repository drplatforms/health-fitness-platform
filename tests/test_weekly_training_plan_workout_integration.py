from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.exercise_catalog_service import find_catalog_entry_by_name
from services.weekly_training_plan_service import create_weekly_training_plan

HOME_GYM_EQUIPMENT = [
    "adjustable_bench",
    "barbell",
    "bike",
    "bodyweight",
    "cable",
    "dumbbell",
    "exercise_ball",
    "ez_bar",
    "plates",
    "pull_up_bar",
    "rack",
    "resistance_band",
    "rope_cable_attachment",
    "treadmill",
]


def _seed(tmp_path, monkeypatch, user_id: int = 102) -> TestClient:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "weekly_integration.db")
    seed_qa_scenarios()
    save_equipment_profile(
        user_id=user_id,
        training_environment="home_gym",
        available_equipment=HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )
    return TestClient(app)


def _patterns(payload: dict) -> list[str]:
    return [
        find_catalog_entry_by_name(exercise["name"]).movement_pattern
        for exercise in payload["approved_workout_plan"]["exercises"]
    ]


def test_no_weekly_plan_preserves_existing_generation(tmp_path, monkeypatch):
    client = _seed(tmp_path, monkeypatch)

    legacy = client.get(
        "/workout-plans/preview/102?workout_size_preference=standard&preview_variation_index=0"
    )
    dated = client.get(
        "/workout-plans/preview/102?target_date=2026-07-13&workout_size_preference=standard&preview_variation_index=0"
    )

    assert legacy.status_code == dated.status_code == 200
    assert (
        legacy.json()["approved_workout_plan"] == dated.json()["approved_workout_plan"]
    )
    assert dated.json()["weekly_training_context"]["has_weekly_plan"] is False


def test_scheduled_directive_preview_variation_and_size_integration(
    tmp_path,
    monkeypatch,
):
    client = _seed(tmp_path, monkeypatch)
    create_weekly_training_plan(
        102,
        "2026-07-13",
        [0, 1, 3, 5],
        "extended",
        current_date="2026-07-13",
    )

    initial = client.get(
        "/workout-plans/preview/102?target_date=2026-07-13&preview_variation_index=0"
    )
    varied = client.get(
        "/workout-plans/preview/102?target_date=2026-07-13&preview_variation_index=1"
    )
    quick = client.get(
        "/workout-plans/preview/102?target_date=2026-07-13&workout_size_preference=quick"
    )

    assert initial.status_code == varied.status_code == quick.status_code == 200
    initial_payload = initial.json()
    varied_payload = varied.json()
    assert initial_payload["target_date"] == "2026-07-13"
    assert initial_payload["weekly_training_context"]["session_title"] == "Upper A"
    assert initial_payload["workout_exercise_count"]["requested_size"] == "full"
    assert _patterns(initial_payload)[:5] == [
        "horizontal_push",
        "horizontal_pull",
        "vertical_push",
        "vertical_pull",
        _patterns(initial_payload)[4],
    ]
    assert _patterns(initial_payload)[:4] == _patterns(varied_payload)[:4]
    assert [
        item["name"] for item in initial_payload["approved_workout_plan"]["exercises"]
    ][:4] != [
        item["name"] for item in varied_payload["approved_workout_plan"]["exercises"]
    ][:4]
    assert len(quick.json()["approved_workout_plan"]["exercises"]) in range(3, 5)


def test_recovery_limited_day_keeps_scheduled_structure(tmp_path, monkeypatch):
    client = _seed(tmp_path, monkeypatch, user_id=101)
    create_weekly_training_plan(
        101,
        "2026-07-13",
        [0, 1, 3, 5],
        current_date="2026-07-13",
    )

    response = client.get(
        "/workout-plans/preview/101?target_date=2026-07-14&workout_size_preference=standard"
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["scenario"] == "recovery_limited"
    assert payload["weekly_training_context"]["session_title"] == "Lower A"
    assert _patterns(payload)[:4] == [
        "squat",
        "hinge",
        "lunge",
        "core_anti_extension",
    ] or _patterns(payload)[:4] == [
        "squat",
        "hinge",
        "lunge",
        "core_anti_rotation",
    ]
    assert all(
        exercise["rir_min"] >= 2
        for exercise in payload["approved_workout_plan"]["exercises"]
    )


def test_rest_day_suppression_and_train_anyway_override(tmp_path, monkeypatch):
    client = _seed(tmp_path, monkeypatch)
    create_weekly_training_plan(
        102,
        "2026-07-13",
        [0, 2, 4],
        current_date="2026-07-13",
    )

    rest = client.get("/workout-plans/preview/102?target_date=2026-07-14")
    override = client.get(
        "/workout-plans/preview/102?target_date=2026-07-14&train_anyway=true"
    )

    assert rest.status_code == 200
    assert rest.json()["rest_day"] is True
    assert rest.json()["approved_workout_plan"] is None
    assert override.status_code == 200
    assert override.json()["rest_day"] is False
    assert override.json()["weekly_training_context"]["is_override"] is True
    assert override.json()["approved_workout_plan"]["exercises"]
