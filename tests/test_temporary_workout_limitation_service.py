from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app
from scripts.seed_qa_scenarios import seed_qa_scenarios
from services.exercise_catalog_service import (
    get_exercise_catalog,
    get_exercise_catalog_entry_by_id,
    seed_exercise_catalog,
)
from services.exercise_substitution_service import (
    apply_substitution,
    get_substitution_candidates,
)
from services.temporary_workout_limitation_service import (
    TemporaryWorkoutLimitationValidationError,
    clear_temporary_workout_limitation,
    get_active_temporary_workout_limitation,
    get_temporary_workout_limitation,
    save_temporary_workout_limitation,
)
from services.user_state_service import build_user_health_state
from services.workout_constraint_service import build_workout_constraints
from services.workout_plan_persistence_service import (
    WorkoutPlanValidationError,
    get_workout_plan_instance,
    select_approved_workout_plan,
    start_selected_workout_plan,
)
from services.workout_plan_service import (
    WorkoutPlanUnavailableError,
    build_approved_workout_plan,
)


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    seed_qa_scenarios()
    seed_exercise_catalog()


def _catalog_entry_for_exercise(exercise):
    assert exercise.catalog_exercise_id is not None
    entry = get_exercise_catalog_entry_by_id(exercise.catalog_exercise_id)
    assert entry is not None
    return entry


def test_save_get_update_clear_and_api_contract(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    preview = build_approved_workout_plan(build_user_health_state(102))
    excluded_id = preview.exercises[0].catalog_exercise_id
    assert excluded_id is not None

    saved = save_temporary_workout_limitation(
        102,
        affected_regions=["Shoulder", "shoulder"],
        restricted_movement_patterns=["horizontal_push"],
        excluded_catalog_exercise_ids=[excluded_id],
        expires_at=(datetime.now(UTC) + timedelta(days=3)).isoformat(),
    )

    assert saved.affected_regions == ["shoulder"]
    assert saved.restricted_movement_patterns == ["horizontal_push"]
    assert saved.excluded_catalog_exercise_ids == [excluded_id]
    assert get_active_temporary_workout_limitation(102) == saved

    client = TestClient(app)
    response = client.get("/users/102/temporary-workout-limitation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["active"] is True
    assert payload["limitation"]["user_id"] == 102

    updated = client.put(
        "/users/102/temporary-workout-limitation",
        json={
            "affected_regions": ["elbow"],
            "restricted_movement_patterns": ["vertical_push"],
            "excluded_catalog_exercise_ids": [],
            "expires_at": None,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["limitation"]["affected_regions"] == ["elbow"]

    cleared = client.delete("/users/102/temporary-workout-limitation")
    assert cleared.status_code == 200
    assert cleared.json()["active"] is False
    assert cleared.json()["cleared"] is True
    assert get_temporary_workout_limitation(102) is None


def test_validation_requires_explicit_hard_restriction_and_canonical_values(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)

    with pytest.raises(TemporaryWorkoutLimitationValidationError):
        save_temporary_workout_limitation(102, affected_regions=["shoulder"])
    with pytest.raises(TemporaryWorkoutLimitationValidationError):
        save_temporary_workout_limitation(
            102,
            restricted_movement_patterns=["made_up_pattern"],
        )
    with pytest.raises(TemporaryWorkoutLimitationValidationError):
        save_temporary_workout_limitation(
            102,
            excluded_catalog_exercise_ids=[999999],
        )
    with pytest.raises(TemporaryWorkoutLimitationValidationError):
        save_temporary_workout_limitation(
            102,
            restricted_movement_patterns=["squat"],
            expires_at=(datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        )


def test_expired_profile_is_inactive_and_preserves_default_constraints(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    future = datetime(2030, 1, 2, tzinfo=UTC)
    save_temporary_workout_limitation(
        102,
        restricted_movement_patterns=["squat"],
        expires_at=future.isoformat(),
        now=datetime(2030, 1, 1, tzinfo=UTC),
    )

    assert (
        get_active_temporary_workout_limitation(
            102,
            now=datetime(2030, 1, 3, tzinfo=UTC),
        )
        is None
    )
    clear_temporary_workout_limitation(102)
    constraints = build_workout_constraints(build_user_health_state(102))
    assert constraints.movement_restrictions == []
    assert constraints.excluded_catalog_exercise_ids == []
    assert "temporary_limitation_active" not in constraints.reason_codes


def test_constraints_and_generation_apply_movement_and_catalog_exclusions(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    baseline = build_approved_workout_plan(build_user_health_state(102))
    baseline_entry = _catalog_entry_for_exercise(baseline.exercises[0])
    excluded_id = baseline.exercises[1].catalog_exercise_id
    assert excluded_id is not None

    save_temporary_workout_limitation(
        102,
        restricted_movement_patterns=[baseline_entry.movement_pattern],
        excluded_catalog_exercise_ids=[excluded_id],
    )
    constraints = build_workout_constraints(build_user_health_state(102))
    limited = build_approved_workout_plan(build_user_health_state(102))

    assert baseline_entry.movement_pattern in constraints.movement_restrictions
    assert excluded_id in constraints.excluded_catalog_exercise_ids
    assert "temporary_limitation_active" in constraints.reason_codes
    assert "temporary_movement_restrictions_active" in constraints.reason_codes
    assert "temporary_exercise_exclusions_active" in constraints.reason_codes
    assert excluded_id not in {
        exercise.catalog_exercise_id for exercise in limited.exercises
    }
    assert all(
        _catalog_entry_for_exercise(exercise).movement_pattern
        != baseline_entry.movement_pattern
        for exercise in limited.exercises
    )


def test_core_anti_rotation_restriction_keeps_generated_workout_unique(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    save_temporary_workout_limitation(
        102,
        restricted_movement_patterns=["core_anti_rotation"],
    )

    limited = build_approved_workout_plan(build_user_health_state(102))

    exercise_names = [exercise.name for exercise in limited.exercises]
    assert len(exercise_names) == len(set(exercise_names))
    assert all(
        _catalog_entry_for_exercise(exercise).movement_pattern != "core_anti_rotation"
        for exercise in limited.exercises
    )


def test_restrictive_generation_returns_safe_unavailable_state_not_duplicates(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    catalog = get_exercise_catalog()
    pattern_counts = {
        pattern: sum(1 for entry in catalog if entry.movement_pattern == pattern)
        for pattern in {entry.movement_pattern for entry in catalog}
    }
    allowed_pattern = min(pattern_counts, key=pattern_counts.get)
    restrictions = sorted(
        pattern for pattern in pattern_counts if pattern != allowed_pattern
    )
    allowed_entries = [
        entry for entry in catalog if entry.movement_pattern == allowed_pattern
    ]
    assert len(allowed_entries) > 2
    save_temporary_workout_limitation(
        102,
        restricted_movement_patterns=restrictions,
        excluded_catalog_exercise_ids=[entry.id for entry in allowed_entries[2:]],
    )

    with pytest.raises(WorkoutPlanUnavailableError, match="unique workout"):
        build_approved_workout_plan(build_user_health_state(102))

    response = TestClient(app).get("/workout-plans/preview/102")
    assert response.status_code == 409
    assert "unique workout" in response.json()["detail"]


def test_stale_preview_selection_and_selected_plan_start_are_revalidated(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    preview = build_approved_workout_plan(build_user_health_state(102))
    first_entry = _catalog_entry_for_exercise(preview.exercises[0])

    save_temporary_workout_limitation(
        102,
        restricted_movement_patterns=[first_entry.movement_pattern],
    )
    with pytest.raises(WorkoutPlanValidationError, match="stale"):
        select_approved_workout_plan(102, preview)

    clear_temporary_workout_limitation(102)
    selected = select_approved_workout_plan(102, preview)
    plan_id = selected["workout_plan_instance"].id
    excluded_id = preview.exercises[0].catalog_exercise_id
    assert excluded_id is not None
    save_temporary_workout_limitation(
        102,
        excluded_catalog_exercise_ids=[excluded_id],
    )

    with pytest.raises(WorkoutPlanValidationError, match="before starting"):
        start_selected_workout_plan(plan_id)
    assert get_workout_plan_instance(plan_id).status == "selected"


def test_start_fails_closed_when_limitation_conflict_lookup_errors(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_approved_workout_plan(
        102,
        build_approved_workout_plan(build_user_health_state(102)),
    )
    plan_id = selected["workout_plan_instance"].id

    import services.temporary_workout_limitation_service as limitation_service

    def raise_lookup_error(*_args, **_kwargs):
        raise RuntimeError("conflict lookup unavailable")

    monkeypatch.setattr(
        limitation_service,
        "get_plan_limitation_conflicts",
        raise_lookup_error,
    )

    with pytest.raises(RuntimeError, match="conflict lookup unavailable"):
        start_selected_workout_plan(plan_id)
    assert get_workout_plan_instance(plan_id).status == "selected"


def test_substitution_candidates_and_apply_revalidate_current_limitation(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    preview = build_approved_workout_plan(build_user_health_state(105))
    selected = select_approved_workout_plan(105, preview)
    plan_id = selected["workout_plan_instance"].id

    planned = None
    candidates = []
    for exercise in selected["planned_exercises"]:
        candidates = get_substitution_candidates(plan_id, exercise.id)
        if candidates:
            planned = exercise
            break
    assert planned is not None
    blocked_candidate = candidates[0]

    save_temporary_workout_limitation(
        105,
        excluded_catalog_exercise_ids=[blocked_candidate.catalog_exercise_id],
    )
    refreshed = get_substitution_candidates(plan_id, planned.id)
    assert blocked_candidate.catalog_exercise_id not in {
        candidate.catalog_exercise_id for candidate in refreshed
    }
    with pytest.raises(WorkoutPlanValidationError):
        apply_substitution(
            plan_id,
            planned.id,
            blocked_candidate.catalog_exercise_id,
        )


def test_substitution_candidates_filter_restricted_movements(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_approved_workout_plan(
        105,
        build_approved_workout_plan(build_user_health_state(105)),
    )
    plan_id = selected["workout_plan_instance"].id
    planned = None
    blocked_candidate = None
    for exercise in selected["planned_exercises"]:
        candidates = get_substitution_candidates(plan_id, exercise.id)
        if candidates:
            planned = exercise
            blocked_candidate = candidates[0]
            break
    assert planned is not None
    assert blocked_candidate is not None

    save_temporary_workout_limitation(
        105,
        restricted_movement_patterns=[blocked_candidate.movement_pattern],
    )
    refreshed = get_substitution_candidates(plan_id, planned.id)
    assert all(
        candidate.movement_pattern != blocked_candidate.movement_pattern
        for candidate in refreshed
    )
    with pytest.raises(WorkoutPlanValidationError):
        apply_substitution(
            plan_id,
            planned.id,
            blocked_candidate.catalog_exercise_id,
        )


def test_start_and_conflict_summary_use_effective_substitution_identity(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_approved_workout_plan(
        105,
        build_approved_workout_plan(build_user_health_state(105)),
    )
    plan_id = selected["workout_plan_instance"].id
    planned = None
    candidate = None
    for exercise in selected["planned_exercises"]:
        candidates = get_substitution_candidates(plan_id, exercise.id)
        if candidates:
            planned = exercise
            candidate = candidates[0]
            break
    assert planned is not None
    assert candidate is not None
    apply_substitution(plan_id, planned.id, candidate.catalog_exercise_id)

    save_temporary_workout_limitation(
        105,
        excluded_catalog_exercise_ids=[candidate.catalog_exercise_id],
    )
    payload = TestClient(app).get("/users/105/temporary-workout-limitation").json()
    assert any(
        conflict["exercise_name"] == candidate.name
        for conflict in payload["current_plan_conflicts"]
    )
    with pytest.raises(WorkoutPlanValidationError):
        start_selected_workout_plan(plan_id)
    assert get_workout_plan_instance(plan_id).status == "selected"


def test_allowed_effective_substitution_can_start_when_original_is_excluded(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    selected = select_approved_workout_plan(
        105,
        build_approved_workout_plan(build_user_health_state(105)),
    )
    plan_id = selected["workout_plan_instance"].id
    planned = None
    candidate = None
    for exercise in selected["planned_exercises"]:
        candidates = get_substitution_candidates(plan_id, exercise.id)
        if candidates:
            planned = exercise
            candidate = candidates[0]
            break
    assert planned is not None
    assert planned.catalog_exercise_id is not None
    assert candidate is not None
    apply_substitution(plan_id, planned.id, candidate.catalog_exercise_id)
    save_temporary_workout_limitation(
        105,
        excluded_catalog_exercise_ids=[planned.catalog_exercise_id],
    )

    started = start_selected_workout_plan(plan_id)
    assert started["workout_plan_instance"].status == "started"


def test_in_progress_plan_is_not_mutated_when_limitation_changes(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    preview = build_approved_workout_plan(build_user_health_state(102))
    selected = select_approved_workout_plan(102, preview)
    plan_id = selected["workout_plan_instance"].id
    started = start_selected_workout_plan(plan_id)
    excluded_id = started["planned_exercises"][0].catalog_exercise_id
    before_plan = asdict(get_workout_plan_instance(plan_id))
    assert excluded_id is not None

    save_temporary_workout_limitation(
        102,
        excluded_catalog_exercise_ids=[excluded_id],
    )

    after_plan = asdict(get_workout_plan_instance(plan_id))
    assert after_plan == before_plan
    assert after_plan["status"] == "started"


def test_active_limitation_api_reports_bounded_selected_plan_conflicts(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    preview = build_approved_workout_plan(build_user_health_state(102))
    selected = select_approved_workout_plan(102, preview)
    excluded_id = selected["planned_exercises"][0].catalog_exercise_id
    assert excluded_id is not None
    save_temporary_workout_limitation(
        102,
        excluded_catalog_exercise_ids=[excluded_id],
    )

    payload = TestClient(app).get("/users/102/temporary-workout-limitation").json()
    assert payload["active"] is True
    assert payload["current_plan_conflicts"]
    assert set(payload["current_plan_conflicts"][0]) == {
        "planned_exercise_id",
        "exercise_name",
        "conflict_type",
        "movement_pattern",
    }
    assert "approved_workout_plan" not in asdict(
        get_active_temporary_workout_limitation(102)
    )


def test_expired_prior_selected_plan_is_not_reported_as_current_conflict(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    preview = build_approved_workout_plan(build_user_health_state(102))
    selected = select_approved_workout_plan(102, preview)
    excluded_id = selected["planned_exercises"][0].catalog_exercise_id
    assert excluded_id is not None
    conn = database.get_connection()
    conn.execute(
        "UPDATE workout_plan_instances SET selected_at = ? WHERE id = ?",
        ("2000-01-01 12:00:00", selected["workout_plan_instance"].id),
    )
    conn.commit()
    conn.close()
    save_temporary_workout_limitation(
        102,
        excluded_catalog_exercise_ids=[excluded_id],
    )

    payload = TestClient(app).get("/users/102/temporary-workout-limitation").json()
    assert payload["active"] is True
    assert payload["current_plan_conflicts"] == []
