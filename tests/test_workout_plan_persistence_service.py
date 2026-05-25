from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.workout_plan_persistence_service import (
    count_workout_plan_instances,
    get_planned_workout_exercises,
    get_workout_execution_session,
    get_workout_plan_instance,
    select_current_workout_plan,
)
from services.workout_service import create_workout_session


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()


def test_preview_endpoint_remains_stateless(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    before_count = count_workout_plan_instances(105)
    response = client.get("/workout-plans/preview/105")
    after_count = count_workout_plan_instances(105)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert before_count == 0
    assert after_count == 0


def test_select_workout_plan_creates_instance_snapshot_and_execution_session(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)

    selected = select_current_workout_plan(105)
    instance = selected["workout_plan_instance"]
    planned_exercises = selected["planned_exercises"]
    execution_session = selected["execution_session"]
    approved_plan = selected["approved_workout_plan"]

    assert instance.user_id == 105
    assert instance.status == "selected"
    assert instance.scenario == "data_quality_limited"
    assert instance.confidence == "Low"
    assert instance.title == approved_plan.title
    assert instance.approved_workout_plan.title == approved_plan.title
    assert instance.approved_workout_plan.scenario == approved_plan.scenario
    assert planned_exercises
    assert len(planned_exercises) == len(approved_plan.exercises)
    assert planned_exercises[0].exercise_order == 1
    assert planned_exercises[0].name == approved_plan.exercises[0].name
    assert execution_session.status == "selected"
    assert execution_session.user_id == 105
    assert execution_session.workout_plan_instance_id == instance.id
    assert execution_session.workout_session_id is None


def test_selected_plan_can_be_read_back_from_database(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(102)
    instance_id = selected["workout_plan_instance"].id

    stored_instance = get_workout_plan_instance(instance_id)
    stored_exercises = get_planned_workout_exercises(instance_id)
    stored_execution_session = get_workout_execution_session(instance_id)

    assert stored_instance is not None
    assert stored_instance.user_id == 102
    assert stored_instance.status == "selected"
    assert stored_instance.approved_workout_plan.exercises
    assert stored_exercises
    assert stored_execution_session is not None
    assert stored_execution_session.status == "selected"


def test_select_workout_plan_endpoint_smoke(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post("/workout-plans/105/select")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["user_id"] == 105
    assert payload["scenario"] == "data_quality_limited"
    assert payload["confidence"] == "Low"
    assert payload["workout_plan_instance"]["status"] == "selected"
    assert payload["workout_plan_instance"]["approved_workout_plan"]
    assert payload["planned_exercises"]
    assert payload["execution_session"]["status"] == "selected"
    assert payload["execution_session"]["workout_session_id"] is None


def test_select_rebuilds_server_side_and_respects_equipment_profile(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    save_equipment_profile(
        user_id=105,
        training_environment="bodyweight_only",
        available_equipment=[],
        unavailable_equipment=[],
    )

    selected = select_current_workout_plan(105)
    planned_exercises = selected["planned_exercises"]
    approved_plan = selected["approved_workout_plan"]

    assert approved_plan.exercises
    for exercise in approved_plan.exercises:
        assert exercise.equipment_required == ["bodyweight"]
    for planned_exercise in planned_exercises:
        assert planned_exercise.equipment_required == ["bodyweight"]


def test_manual_workout_logging_still_works_independently(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_current_workout_plan(105)

    session_id = create_workout_session(
        user_id=105,
        workout_name="Manual QA Workout",
        duration_minutes=30,
        notes="Manual logging remains independent.",
    )
    execution_session = get_workout_execution_session(
        selected["workout_plan_instance"].id
    )

    assert session_id
    assert execution_session is not None
    assert execution_session.workout_session_id is None
    assert execution_session.status == "selected"
