from dataclasses import asdict, replace
from datetime import date, datetime

import database
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.user_state_service import build_user_health_state
from services.workout_daily_state_service import resolve_workout_daily_state
from services.workout_plan_persistence_service import (
    approved_workout_plan_from_payload,
    get_planned_workout_exercises,
    select_approved_workout_plan,
)
from services.workout_plan_service import build_approved_workout_plan


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def test_select_approved_workout_plan_persists_exact_visible_preview(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(102)
    visible_preview = build_approved_workout_plan(
        health_state,
        workout_size_preference="standard",
    )
    selected = select_approved_workout_plan(102, visible_preview)

    planned_exercises = selected["planned_exercises"]

    assert selected["workout_plan_instance"].status == "selected"
    assert selected["approved_workout_plan"].title == visible_preview.title
    assert [exercise.name for exercise in planned_exercises] == [
        exercise.name for exercise in visible_preview.exercises
    ]
    assert [exercise.sets for exercise in planned_exercises] == [
        exercise.sets for exercise in visible_preview.exercises
    ]


def test_select_approved_workout_plan_does_not_rebuild_when_visible_preview_differs(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(102)
    visible_preview = build_approved_workout_plan(health_state)
    changed_preview = replace(
        visible_preview,
        exercises=list(reversed(visible_preview.exercises)),
    )

    selected = select_approved_workout_plan(102, changed_preview)
    planned_exercises = get_planned_workout_exercises(
        selected["workout_plan_instance"].id
    )

    assert [exercise.name for exercise in planned_exercises] == [
        exercise.name for exercise in changed_preview.exercises
    ]
    assert [exercise.name for exercise in planned_exercises] != [
        exercise.name for exercise in visible_preview.exercises
    ]


def test_approved_workout_plan_payload_round_trips_for_selection(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(105)
    visible_preview = build_approved_workout_plan(health_state)

    approved_plan = approved_workout_plan_from_payload(asdict(visible_preview))
    selected = select_approved_workout_plan(105, approved_plan)

    assert selected["workout_plan_instance"].user_id == 105
    assert [exercise.name for exercise in selected["planned_exercises"]] == [
        exercise.name for exercise in visible_preview.exercises
    ]


def test_select_preview_endpoint_persists_exact_visible_preview(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    preview_response = client.get("/workout-plans/preview/102")
    visible_plan = preview_response.json()["approved_workout_plan"]

    select_response = client.post(
        "/workout-plans/102/select-preview",
        json={"approved_workout_plan": visible_plan},
    )

    assert select_response.status_code == 200
    payload = select_response.json()
    assert payload["success"] is True
    assert [exercise["name"] for exercise in payload["planned_exercises"]] == [
        exercise["name"] for exercise in visible_plan["exercises"]
    ]


def test_select_approved_workout_plan_is_visible_to_current_day_state(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    health_state = build_user_health_state(102)
    visible_preview = build_approved_workout_plan(health_state)

    import services.workout_plan_persistence_service as persistence_service

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 20, 9, 30, 0)

    monkeypatch.setattr(persistence_service, "datetime", FixedDateTime)

    selected = select_approved_workout_plan(102, visible_preview)
    instance = selected["workout_plan_instance"]

    assert str(instance.selected_at).startswith("2026-06-20")
    assert str(instance.created_at).startswith("2026-06-20")

    daily_state = resolve_workout_daily_state(102, target_date=date(2026, 6, 20))

    assert daily_state.state == "selected_today"
    assert daily_state.selected_plan_id == instance.id
    assert daily_state.stale_state_detected is False


def test_preview_variation_does_not_change_selected_or_active_workout(
    tmp_path, monkeypatch
):
    from fastapi.testclient import TestClient

    from api.main import app
    from services.equipment_profile_service import save_equipment_profile

    _seed_test_db(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=102,
        training_environment="home_gym",
        available_equipment=[
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
        ],
        unavailable_equipment=["machine"],
    )
    client = TestClient(app)

    preview_response = client.get(
        "/workout-plans/preview/102"
        "?workout_size_preference=full&preview_variation_index=0"
    )
    assert preview_response.status_code == 200
    visible_plan = preview_response.json()["approved_workout_plan"]
    visible_names = [exercise["name"] for exercise in visible_plan["exercises"]]

    select_response = client.post(
        "/workout-plans/102/select-preview",
        json={"approved_workout_plan": visible_plan},
    )
    assert select_response.status_code == 200
    selected_payload = select_response.json()
    plan_instance_id = selected_payload["workout_plan_instance"]["id"]
    assert [
        exercise["name"] for exercise in selected_payload["planned_exercises"]
    ] == visible_names

    alternate_preview_response = client.get(
        "/workout-plans/preview/102"
        "?workout_size_preference=full&preview_variation_index=1"
    )
    assert alternate_preview_response.status_code == 200
    alternate_names = [
        exercise["name"]
        for exercise in alternate_preview_response.json()["approved_workout_plan"][
            "exercises"
        ]
    ]
    assert alternate_names != visible_names

    current_response = client.get("/workout-plans/current/102")
    assert current_response.status_code == 200
    current_payload = current_response.json()["current_execution_state"]
    assert current_payload is not None
    assert [
        exercise["name"] for exercise in current_payload["planned_exercises"]
    ] == visible_names

    start_response = client.post(f"/workout-plans/{plan_instance_id}/start")
    assert start_response.status_code == 200
    assert [
        exercise["name"] for exercise in start_response.json()["planned_exercises"]
    ] == visible_names

    active_response = client.get("/workout-plans/current/102")
    assert active_response.status_code == 200
    active_payload = active_response.json()["current_execution_state"]
    assert active_payload is not None
    assert active_response.json()["workout_daily_state"]["state"] == "active_today"
    assert [
        exercise["name"] for exercise in active_payload["planned_exercises"]
    ] == visible_names
