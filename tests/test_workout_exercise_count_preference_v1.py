from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.equipment_profile_service import save_equipment_profile
from services.user_state_service import build_user_health_state
from services.workout_exercise_count_service import resolve_workout_exercise_count
from services.workout_plan_persistence_service import (
    get_execution_state,
    select_current_workout_plan,
    start_selected_workout_plan,
)
from services.workout_plan_service import build_approved_workout_plan

USER_HOME_GYM_EQUIPMENT = [
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


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    seed_qa_scenarios()


def _save_home_gym_profile(user_id: int = 102):
    save_equipment_profile(
        user_id=user_id,
        training_environment="home_gym",
        available_equipment=USER_HOME_GYM_EQUIPMENT,
        unavailable_equipment=["machine"],
    )


def test_count_preference_service_maps_and_clamps_safely():
    assert resolve_workout_exercise_count(requested_size="quick").final_count == 4
    assert resolve_workout_exercise_count(requested_size="standard").final_count == 5
    assert resolve_workout_exercise_count(requested_size="full").final_count == 6

    recovery = resolve_workout_exercise_count(
        requested_size="full",
        scenario="recovery_limited",
        confidence="Moderate",
    )
    assert recovery.final_count == 4
    assert recovery.clamp_reason == "recovery_limited"

    explicit = resolve_workout_exercise_count(
        requested_size="full",
        requested_target_count=99,
        scenario="aligned_managed",
        confidence="High",
    )
    assert explicit.requested_count == 7
    assert explicit.final_count == 7


def test_standard_generation_targets_five_clean_exercises(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)

    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(
        health_state,
        workout_size_preference="standard",
    )

    names = [exercise.name for exercise in approved.exercises]
    assert len(approved.exercises) == 5
    assert len(names) == len(set(names))
    assert approved.workout_size_preference == "standard"
    assert approved.final_target_exercise_count == 5
    assert "standard 5-exercise" in approved.exercise_count_user_reason

    for exercise in approved.exercises:
        assert set(exercise.equipment_required).issubset(set(USER_HOME_GYM_EQUIPMENT))


def test_full_generation_targets_six_without_exceeding_v1_max(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)

    health_state = build_user_health_state(102)
    approved = build_approved_workout_plan(
        health_state,
        workout_size_preference="full",
    )

    names = [exercise.name for exercise in approved.exercises]
    assert 6 <= len(approved.exercises) <= 7
    assert len(names) == len(set(names))
    assert approved.workout_size_preference == "full"
    assert approved.final_target_exercise_count == 6
    assert "fuller" in approved.exercise_count_user_reason


def test_recovery_limited_full_request_stays_shorter(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(101)

    health_state = build_user_health_state(101)
    approved = build_approved_workout_plan(
        health_state,
        workout_size_preference="full",
    )

    assert approved.scenario == "recovery_limited"
    assert len(approved.exercises) == 4
    assert approved.final_target_exercise_count == 4
    assert approved.exercise_count_reason == "recovery_limited"
    assert "Shortened to 4 exercises" in approved.exercise_count_user_reason


def test_preview_and_select_routes_accept_workout_size_preference(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)
    client = TestClient(app)

    preview = client.get("/workout-plans/preview/102?workout_size_preference=full")
    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload["workout_exercise_count"]["requested_size"] == "full"
    assert preview_payload["workout_exercise_count"]["final_count"] >= 6

    selected = client.post("/workout-plans/102/select?workout_size_preference=full")
    assert selected.status_code == 200
    selected_payload = selected.json()
    assert len(selected_payload["planned_exercises"]) >= 6
    assert (
        selected_payload["approved_workout_plan"]["workout_size_preference"] == "full"
    )


def test_active_workout_state_handles_five_plus_exercises(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    _save_home_gym_profile(102)

    selected = select_current_workout_plan(102, workout_size_preference="full")
    plan_instance_id = selected["workout_plan_instance"].id
    assert len(selected["planned_exercises"]) >= 6

    start_selected_workout_plan(plan_instance_id)
    state = get_execution_state(plan_instance_id)

    assert state["execution_session"].status == "started"
    assert len(state["planned_exercises"]) >= 6


def test_streamlit_workout_size_ui_uses_user_safe_labels():
    source = Path("ui/streamlit_app.py").read_text(encoding="utf-8")

    assert "Workout size" in source
    assert "Quick — 3 to 4 exercises" in source
    assert "Standard — 5 exercises" in source
    assert "Full — 6 to 7 exercises" in source
    assert "Pick the session size. Recovery and equipment rules still apply" in source

    forbidden_normal_copy = [
        "clamped",
        "candidate pool insufficient",
        "scoring threshold failed",
        "generator target",
    ]
    for term in forbidden_normal_copy:
        assert term not in source
