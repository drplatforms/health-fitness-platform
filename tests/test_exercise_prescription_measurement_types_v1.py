import json
import sqlite3
from collections import Counter
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app
from models.workout_plan_models import (
    ApprovedWorkoutExercise,
    ApprovedWorkoutPlan,
)
from services.exercise_catalog_service import (
    clear_exercise_catalog_cache,
    find_catalog_entry_by_name,
    get_exercise_prescription_measurement_metadata,
    seed_exercise_prescription_measurements,
    seed_exercise_taxonomy,
)
from services.exercise_substitution_service import get_substitution_candidates
from services.workout_plan_persistence_service import (
    WorkoutPlanPersistenceError,
    WorkoutPlanValidationError,
    _foreign_key_violation_multiset,
    _migrate_planned_workout_exercises_measurement_schema,
    build_planned_vs_actual_summary,
    ensure_workout_plan_persistence_tables,
    get_planned_workout_exercises,
    log_actual_set,
    select_approved_workout_plan,
    start_selected_workout_plan,
    update_actual_set,
)
from services.workout_plan_service import (
    _catalog_validation_violations,
    _exercise,
    _measurement_validation_violations,
    parse_candidate_workout_plan_json,
)
from services.workout_progression_decision_service import (
    CurrentExercisePrescription,
    build_exercise_progression_decision,
)


@pytest.fixture
def measurement_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "measurement_types.db")
    clear_exercise_catalog_cache()
    database.initialize_database()
    seed_exercise_taxonomy()
    seed_exercise_prescription_measurements()
    ensure_workout_plan_persistence_tables()
    yield
    clear_exercise_catalog_cache()


def _catalog_id(name: str) -> int:
    entry = find_catalog_entry_by_name(name)
    assert entry is not None
    assert entry.id is not None
    return entry.id


def _insert_user(user_id: int = 901) -> None:
    conn = database.get_connection()
    with conn:
        conn.execute(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            (user_id, f"Measurement User {user_id}"),
        )
    conn.close()


def _mixed_measurement_plan() -> ApprovedWorkoutPlan:
    return ApprovedWorkoutPlan(
        title="Mixed measurement session",
        session_focus="Exercise prescription measurement validation",
        duration_minutes=30,
        exercises=[
            ApprovedWorkoutExercise(
                name="Barbell Bench Press",
                sets=1,
                reps_min=8,
                reps_max=10,
                rir_min=2,
                rir_max=3,
                notes="Controlled reps.",
                equipment_required=["barbell", "bench", "plates"],
                catalog_exercise_id=_catalog_id("Barbell Bench Press"),
                measurement_type="reps",
            ),
            ApprovedWorkoutExercise(
                name="Plank",
                sets=1,
                reps_min=None,
                reps_max=None,
                rir_min=None,
                rir_max=None,
                notes="Hold a stable position.",
                equipment_required=["bodyweight"],
                catalog_exercise_id=_catalog_id("Plank"),
                measurement_type="duration",
                target_duration_seconds=30,
            ),
            ApprovedWorkoutExercise(
                name="Farmer Carry",
                sets=2,
                reps_min=None,
                reps_max=None,
                rir_min=None,
                rir_max=None,
                notes="Walk with control.",
                equipment_required=["dumbbell"],
                catalog_exercise_id=_catalog_id("Farmer Carry"),
                measurement_type="distance",
                target_distance_meters=20.0,
            ),
        ],
        warmup="Use an easy general warmup.",
        cooldown="Record the completed work.",
        progression_guidance="Keep the written targets stable.",
        rationale="Covers each supported measurement type.",
        confidence="High",
        scenario="aligned_managed",
    )


def _select_and_start_mixed_plan(user_id: int = 901):
    _insert_user(user_id)
    selected = select_approved_workout_plan(user_id, _mixed_measurement_plan())
    started = start_selected_workout_plan(selected["workout_plan_instance"].id)
    planned = {item.measurement_type: item for item in started["planned_exercises"]}
    return selected["workout_plan_instance"].id, planned


def test_seed_projection_is_exact_idempotent_stale_removing_and_read_strict(
    measurement_db,
):
    first = seed_exercise_prescription_measurements()
    second = seed_exercise_prescription_measurements()

    assert len(first) == len(second) == 300
    assert len({item.catalog_exercise_id for item in first}) == 300
    assert Counter(item.default_measurement_type for item in first) == {
        "reps": 263,
        "duration": 29,
        "distance": 8,
    }
    assert sum(len(item.allowed_measurement_types) > 1 for item in first) == 31
    distance_enabled = [
        item for item in first if "distance" in item.allowed_measurement_types
    ]
    assert len(distance_enabled) == 25
    assert {item.distance_unit for item in distance_enabled} == {"meters"}

    representatives = {
        "Barbell Bench Press": ("reps", ("reps",)),
        "Plank": ("duration", ("duration",)),
        "Farmer Carry": ("distance", ("duration", "distance")),
        "Treadmill Walk": ("duration", ("duration", "distance")),
        "Bike Cadence Drill": ("duration", ("duration",)),
        "Bear Crawl": ("distance", ("duration", "distance")),
        "Mountain Climber": ("duration", ("reps", "duration")),
    }
    for name, expected in representatives.items():
        metadata = get_exercise_prescription_measurement_metadata(_catalog_id(name))
        assert metadata is not None
        assert (
            metadata.default_measurement_type,
            metadata.allowed_measurement_types,
        ) == expected

    conn = database.get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO exercise_catalog_exercises (
                name, exercise_type, movement_pattern,
                primary_muscle_groups_json, difficulty
            ) VALUES ('Stale Projection Exercise', 'strength', 'squat', '[]', 'beginner')
            """
        )
        stale_id = conn.execute(
            "SELECT id FROM exercise_catalog_exercises WHERE name = 'Stale Projection Exercise'"
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO exercise_catalog_prescription_measurements (
                exercise_id, default_measurement_type,
                allowed_measurement_types_json, sets_applicable,
                load_applicability, rir_applicability
            ) VALUES (?, 'reps', '["reps"]', 1, 'optional', 'applicable')
            """,
            (stale_id,),
        )
    conn.close()

    seed_exercise_prescription_measurements()
    conn = database.get_connection()
    assert (
        conn.execute(
            "SELECT COUNT(*) AS count FROM exercise_catalog_prescription_measurements"
        ).fetchone()["count"]
        == 300
    )
    assert (
        conn.execute(
            "SELECT COUNT(*) AS count FROM exercise_catalog_exercises WHERE id = ?",
            (stale_id,),
        ).fetchone()["count"]
        == 1
    )
    conn.close()

    assert get_exercise_prescription_measurement_metadata(stale_id) is None
    with pytest.raises(ValueError, match="positive integer"):
        get_exercise_prescription_measurement_metadata(0)

    plank_id = _catalog_id("Plank")
    conn = database.get_connection()
    with conn:
        conn.execute(
            """
            UPDATE exercise_catalog_prescription_measurements
            SET allowed_measurement_types_json = 'not-json'
            WHERE exercise_id = ?
            """,
            (plank_id,),
        )
    conn.close()
    with pytest.raises(ValueError, match="Invalid persisted"):
        get_exercise_prescription_measurement_metadata(plank_id)


def test_seed_projection_rolls_back_without_catalog_mutation(measurement_db):
    conn = database.get_connection()
    catalog_before = [
        tuple(row)
        for row in conn.execute(
            "SELECT id, name, exercise_type, movement_pattern FROM exercise_catalog_exercises ORDER BY id"
        )
    ]
    projection_before = [
        tuple(row)
        for row in conn.execute(
            "SELECT * FROM exercise_catalog_prescription_measurements ORDER BY exercise_id"
        )
    ]
    fail_id = projection_before[len(projection_before) // 2][0]
    with conn:
        conn.execute(
            f"""
            CREATE TRIGGER fail_measurement_seed
            BEFORE INSERT ON exercise_catalog_prescription_measurements
            WHEN NEW.exercise_id = {int(fail_id)}
            BEGIN
                SELECT RAISE(ABORT, 'forced measurement seed failure');
            END
            """
        )
    conn.close()

    with pytest.raises(sqlite3.IntegrityError, match="forced measurement seed failure"):
        seed_exercise_prescription_measurements()

    conn = database.get_connection()
    projection_after = [
        tuple(row)
        for row in conn.execute(
            "SELECT * FROM exercise_catalog_prescription_measurements ORDER BY exercise_id"
        )
    ]
    catalog_after = [
        tuple(row)
        for row in conn.execute(
            "SELECT id, name, exercise_type, movement_pattern FROM exercise_catalog_exercises ORDER BY id"
        )
    ]
    assert projection_after == projection_before
    assert catalog_after == catalog_before
    with conn:
        conn.execute("DROP TRIGGER fail_measurement_seed")
    conn.close()


def test_foreign_key_violation_multiset_ignores_order_and_counts_duplicates():
    rows = [
        ("child", 1, "parent", 0),
        ("child", 1, "parent", 0),
        ("other_child", 2, "parent", 0),
    ]

    class FakeCursor:
        def __init__(self, result_rows):
            self.result_rows = result_rows

        def execute(self, statement):
            assert statement == "PRAGMA foreign_key_check"
            return self

        def fetchall(self):
            return self.result_rows

    forward = _foreign_key_violation_multiset(FakeCursor(rows))
    reverse = _foreign_key_violation_multiset(FakeCursor(list(reversed(rows))))

    assert forward == reverse
    assert forward[("child", 1, "parent", 0)] == 2
    assert sum(forward.values()) == 3


def test_legacy_planned_table_rebuild_preserves_ids_children_and_rolls_back(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "legacy_measurement.db")
    database.initialize_database()
    conn = database.get_connection()
    with conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("DROP TABLE workout_execution_set_actuals")
        conn.execute("DROP TABLE planned_workout_exercises")
        conn.execute(
            """
            CREATE TABLE planned_workout_exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_plan_instance_id INTEGER NOT NULL,
                exercise_order INTEGER NOT NULL,
                name TEXT NOT NULL,
                sets INTEGER NOT NULL,
                reps_min INTEGER NOT NULL,
                reps_max INTEGER NOT NULL,
                rir_min INTEGER NOT NULL,
                rir_max INTEGER NOT NULL,
                notes TEXT NOT NULL,
                equipment_required_json TEXT NOT NULL,
                catalog_exercise_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workout_plan_instance_id) REFERENCES workout_plan_instances(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE workout_execution_set_actuals (
                id INTEGER PRIMARY KEY,
                planned_workout_exercise_id INTEGER,
                substitution_for_planned_exercise_id INTEGER,
                FOREIGN KEY (planned_workout_exercise_id) REFERENCES planned_workout_exercises(id),
                FOREIGN KEY (substitution_for_planned_exercise_id) REFERENCES planned_workout_exercises(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE workout_plan_exercise_substitutions (
                id INTEGER PRIMARY KEY,
                planned_workout_exercise_id INTEGER NOT NULL,
                FOREIGN KEY (planned_workout_exercise_id) REFERENCES planned_workout_exercises(id)
            )
            """
        )
        conn.execute("CREATE TABLE unrelated_fk_parent (id INTEGER PRIMARY KEY)")
        conn.execute(
            """
            CREATE TABLE unrelated_fk_child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES unrelated_fk_parent(id)
            )
            """
        )
        conn.execute("INSERT INTO unrelated_fk_child (id, parent_id) VALUES (1, 999)")
        conn.execute(
            """
            INSERT INTO workout_plan_instances (
                id, user_id, status, scenario, confidence, title,
                approved_workout_plan_json
            ) VALUES (42, 1, 'selected', 'aligned_managed', 'High', 'Legacy', '{}')
            """
        )
        conn.execute(
            """
            INSERT INTO planned_workout_exercises (
                id, workout_plan_instance_id, exercise_order, name, sets,
                reps_min, reps_max, rir_min, rir_max, notes,
                equipment_required_json, catalog_exercise_id, created_at
            ) VALUES (77, 42, 1, 'Legacy Row', 3, 8, 10, 2, 3,
                      'Preserve me', '["barbell"]', 19, '2025-01-02 03:04:05')
            """
        )
        conn.execute("INSERT INTO workout_execution_set_actuals VALUES (9, 77, 77)")
        conn.execute("INSERT INTO workout_plan_exercise_substitutions VALUES (5, 77)")

    foreign_key_baseline = Counter(
        tuple(row) for row in conn.execute("PRAGMA foreign_key_check")
    )
    assert sum(foreign_key_baseline.values()) == 1
    assert next(iter(foreign_key_baseline))[0] == "unrelated_fk_child"

    def fail_after_copy():
        raise RuntimeError("forced rebuild failure")

    with pytest.raises(RuntimeError, match="forced rebuild failure"):
        _migrate_planned_workout_exercises_measurement_schema(
            conn,
            after_copy_hook=fail_after_copy,
        )
    legacy_columns = {
        row["name"]: row
        for row in conn.execute("PRAGMA table_info(planned_workout_exercises)")
    }
    assert legacy_columns["reps_min"]["notnull"] == 1
    assert "measurement_type" not in legacy_columns
    assert (
        conn.execute(
            "SELECT name FROM planned_workout_exercises WHERE id = 77"
        ).fetchone()["name"]
        == "Legacy Row"
    )
    assert (
        Counter(tuple(row) for row in conn.execute("PRAGMA foreign_key_check"))
        == foreign_key_baseline
    )
    conn.close()

    ensure_workout_plan_persistence_tables()
    ensure_workout_plan_persistence_tables()
    conn = database.get_connection()
    columns = {
        row["name"]: row
        for row in conn.execute("PRAGMA table_info(planned_workout_exercises)")
    }
    assert {
        "measurement_type",
        "target_duration_seconds",
        "target_distance_meters",
    } <= set(columns)
    assert all(
        columns[name]["notnull"] == 0
        for name in ("reps_min", "reps_max", "rir_min", "rir_max")
    )
    stored = conn.execute(
        "SELECT * FROM planned_workout_exercises WHERE id = 77"
    ).fetchone()
    assert stored["measurement_type"] is None
    assert stored["reps_min"] == 8
    assert stored["created_at"] == "2025-01-02 03:04:05"
    assert (
        conn.execute(
            "SELECT planned_workout_exercise_id FROM workout_execution_set_actuals WHERE id = 9"
        ).fetchone()[0]
        == 77
    )
    assert (
        conn.execute(
            "SELECT planned_workout_exercise_id FROM workout_plan_exercise_substitutions WHERE id = 5"
        ).fetchone()[0]
        == 77
    )
    assert (
        Counter(tuple(row) for row in conn.execute("PRAGMA foreign_key_check"))
        == foreign_key_baseline
    )
    conn.close()
    assert get_planned_workout_exercises(42)[0].measurement_type == "reps"


def test_planned_table_rebuild_rejects_new_foreign_key_violation_and_rolls_back(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "migration_fk_change.db")
    conn = database.get_connection()
    with conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("CREATE TABLE workout_plan_instances (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO workout_plan_instances (id) VALUES (42)")
        conn.execute(
            """
            CREATE TABLE planned_workout_exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_plan_instance_id INTEGER NOT NULL,
                exercise_order INTEGER NOT NULL,
                name TEXT NOT NULL,
                sets INTEGER NOT NULL,
                reps_min INTEGER NOT NULL,
                reps_max INTEGER NOT NULL,
                rir_min INTEGER NOT NULL,
                rir_max INTEGER NOT NULL,
                notes TEXT NOT NULL,
                equipment_required_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workout_plan_instance_id)
                    REFERENCES workout_plan_instances(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE migration_child (
                id INTEGER PRIMARY KEY,
                planned_workout_exercise_id INTEGER NOT NULL,
                FOREIGN KEY (planned_workout_exercise_id)
                    REFERENCES planned_workout_exercises(id)
            )
            """
        )
        conn.execute(
            """
            INSERT INTO planned_workout_exercises (
                id, workout_plan_instance_id, exercise_order, name, sets,
                reps_min, reps_max, rir_min, rir_max, notes,
                equipment_required_json, created_at
            ) VALUES (77, 42, 1, 'Legacy Row', 3, 8, 10, 2, 3,
                      'Preserve me', '[]', '2025-01-02 03:04:05')
            """
        )
        conn.execute("INSERT INTO migration_child VALUES (1, 77)")

    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    def introduce_foreign_key_violation():
        conn.execute(
            "UPDATE migration_child SET planned_workout_exercise_id = 999 WHERE id = 1"
        )

    with pytest.raises(
        WorkoutPlanPersistenceError,
        match=r"foreign-key violation baseline \(added=1, removed=0\)",
    ):
        _migrate_planned_workout_exercises_measurement_schema(
            conn,
            after_copy_hook=introduce_foreign_key_violation,
        )

    columns = {
        row["name"]: row
        for row in conn.execute("PRAGMA table_info(planned_workout_exercises)")
    }
    assert "measurement_type" not in columns
    assert columns["reps_min"]["notnull"] == 1
    assert (
        conn.execute(
            "SELECT planned_workout_exercise_id FROM migration_child WHERE id = 1"
        ).fetchone()[0]
        == 77
    )
    assert (
        conn.execute(
            "SELECT name FROM planned_workout_exercises WHERE id = 77"
        ).fetchone()[0]
        == "Legacy Row"
    )
    assert (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE name = ?",
            ("planned_workout_exercises_measurement_v1",),
        ).fetchone()
        is None
    )
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    conn.close()


def test_deterministic_targets_use_canonical_defaults(measurement_db):
    bench = _exercise("Barbell Bench Press", 3, 8, 10, 2, 3, "", [])
    plank = _exercise("Plank", 3, 8, 10, 2, 3, "", [])
    carry = _exercise("Farmer Carry", 3, 8, 10, 2, 3, "", [])
    treadmill = _exercise("Treadmill Walk", 3, 8, 10, 2, 3, "", [])
    bike = _exercise("Bike Cadence Drill", 3, 8, 10, 2, 3, "", [])

    assert (bench.measurement_type, bench.reps_min, bench.reps_max) == (
        "reps",
        8,
        10,
    )
    assert (plank.measurement_type, plank.sets, plank.target_duration_seconds) == (
        "duration",
        3,
        30,
    )
    assert plank.reps_min is plank.rir_min is None
    assert (carry.measurement_type, carry.sets, carry.target_distance_meters) == (
        "distance",
        3,
        20.0,
    )
    assert carry.reps_min is carry.rir_min is None
    assert (
        treadmill.measurement_type,
        treadmill.sets,
        treadmill.target_duration_seconds,
    ) == (
        "duration",
        1,
        600,
    )
    assert (bike.measurement_type, bike.sets, bike.target_duration_seconds) == (
        "duration",
        1,
        600,
    )


def test_provider_parsing_and_validation_are_measurement_aware(measurement_db):
    payload = {
        "title": "Provider plan",
        "session_focus": "Controlled work",
        "duration_minutes": 30,
        "exercises": [
            {
                "exercise_name": "Plank",
                "catalog_exercise_id": _catalog_id("Plank"),
                "movement_pattern": "core_anti_extension",
                "target_zone": "core",
                "sets": 3,
                "measurement_type": "duration",
                "reps_min": None,
                "reps_max": None,
                "target_duration_seconds": 30,
                "target_distance_meters": None,
                "target_rir_min": None,
                "target_rir_max": None,
                "required_equipment": ["bodyweight"],
                "notes": "Hold position.",
            }
        ],
        "warmup": "Warm up.",
        "cooldown": "Cool down.",
        "progression_guidance": "Hold steady.",
        "rationale": "Matches the catalog.",
        "confidence": "High",
    }
    parsed = parse_candidate_workout_plan_json(json.dumps(payload))
    assert parsed.exercises[0].measurement_type == "duration"
    assert _measurement_validation_violations(parsed.exercises[0]) == []

    payload["exercises"][0]["reps_min"] = 8
    mixed = parse_candidate_workout_plan_json(json.dumps(payload)).exercises[0]
    assert "Invalid duration target" in _measurement_validation_violations(mixed)[0]

    legacy = payload.copy()
    legacy["exercises"] = [
        {
            **payload["exercises"][0],
            "exercise_name": "Barbell Bench Press",
            "catalog_exercise_id": _catalog_id("Barbell Bench Press"),
            "movement_pattern": "horizontal_push",
            "reps_min": 8,
            "reps_max": 10,
            "target_duration_seconds": None,
            "target_rir_min": 2,
            "target_rir_max": 3,
            "required_equipment": ["barbell", "bench", "plates"],
        }
    ]
    legacy["exercises"][0].pop("measurement_type")
    legacy_rep = parse_candidate_workout_plan_json(json.dumps(legacy)).exercises[0]
    assert legacy_rep.measurement_type == "reps"

    disallowed = ApprovedWorkoutExercise(
        name="Barbell Bench Press",
        sets=1,
        reps_min=None,
        reps_max=None,
        rir_min=None,
        rir_max=None,
        notes="",
        equipment_required=["barbell", "bench", "plates"],
        catalog_exercise_id=_catalog_id("Barbell Bench Press"),
        measurement_type="duration",
        target_duration_seconds=30,
    )
    candidate = SimpleNamespace(
        **disallowed.__dict__, movement_pattern="horizontal_push"
    )
    context = SimpleNamespace(
        workout_constraints=SimpleNamespace(
            available_equipment=[],
            unavailable_equipment=[],
            avoid_movements=[],
            movement_restrictions=[],
            excluded_catalog_exercise_ids=[],
        )
    )
    assert any(
        "not allowed" in violation
        for violation in _catalog_validation_violations(candidate, context)
    )


def test_mixed_plan_persistence_logging_edit_and_summary(measurement_db):
    plan_id, planned = _select_and_start_mixed_plan()

    rep_result = log_actual_set(
        plan_id,
        {
            "planned_workout_exercise_id": planned["reps"].id,
            "measurement_type": "reps",
            "actual_reps": 9,
            "actual_weight": 100,
            "actual_rir": 2,
        },
    )
    duration_result = log_actual_set(
        plan_id,
        {
            "planned_workout_exercise_id": planned["duration"].id,
            "measurement_type": "duration",
            "actual_duration_seconds": 45,
            "actual_weight": 10,
        },
    )
    log_actual_set(
        plan_id,
        {
            "planned_workout_exercise_id": planned["distance"].id,
            "measurement_type": "distance",
            "actual_distance_meters": 25,
        },
    )
    log_actual_set(
        plan_id,
        {
            "planned_workout_exercise_id": planned["distance"].id,
            "measurement_type": "distance",
            "completed": False,
            "skipped": True,
        },
    )

    assert rep_result["actual_set"].planned_reps_min == 8
    assert duration_result["actual_set"].planned_duration_seconds == 30
    assert duration_result["actual_set"].actual_reps is None
    assert duration_result["actual_set"].actual_rir is None

    summary = build_planned_vs_actual_summary(plan_id)
    assert summary.sets_inside_planned_reps == 1
    assert summary.duration_comparable_set_count == 1
    assert summary.duration_delta_seconds_total == 15
    assert summary.distance_comparable_set_count == 1
    assert summary.distance_delta_meters_total == 5.0
    assert summary.average_planned_rir == 2.5
    assert summary.average_actual_rir == 2.0
    assert "missing_actual_reps" not in summary.deviation_flags
    assert "missing_actual_rir" not in summary.deviation_flags

    updated = update_actual_set(
        plan_id,
        duration_result["actual_set"].id,
        {"actual_duration_seconds": 40},
    )
    assert updated["actual_set"].actual_duration_seconds == 40
    assert updated["planned_vs_actual_summary"].duration_delta_seconds_total == 10

    with pytest.raises(WorkoutPlanValidationError, match="cannot include reps"):
        log_actual_set(
            plan_id,
            {
                "planned_workout_exercise_id": planned["duration"].id,
                "measurement_type": "duration",
                "actual_duration_seconds": 30,
                "actual_reps": 10,
            },
        )


def test_non_rep_progression_is_neutral_without_history_query(
    measurement_db,
    monkeypatch,
):
    def fail_history_query(**_kwargs):
        raise AssertionError("non-rep progression must not query rep history")

    monkeypatch.setattr(
        "services.workout_progression_decision_service."
        "load_completed_exercise_progression_sessions",
        fail_history_query,
    )
    decision = build_exercise_progression_decision(
        user_id=901,
        current_exercise=CurrentExercisePrescription(
            exercise_name="Plank",
            catalog_exercise_id=_catalog_id("Plank"),
            sets=3,
            reps_min=None,
            reps_max=None,
            rir_min=None,
            rir_max=None,
            measurement_type="duration",
            target_duration_seconds=30,
        ),
        recovery=None,
    )
    assert decision.decision == "insufficient_data"
    assert decision.reason_codes == ["unsupported_measurement_type_for_progression_v1"]
    assert decision.evidence_session_count == 0


def test_substitutions_and_api_preserve_measurement_type(measurement_db):
    plan_id, planned = _select_and_start_mixed_plan(902)
    candidates = get_substitution_candidates(plan_id, planned["distance"].id)
    assert candidates
    for candidate in candidates:
        metadata = get_exercise_prescription_measurement_metadata(
            candidate.catalog_exercise_id
        )
        assert metadata is not None
        assert "distance" in metadata.allowed_measurement_types

    with TestClient(app) as client:
        response = client.post(
            f"/workout-plans/{plan_id}/actual-sets",
            json={
                "planned_workout_exercise_id": planned["duration"].id,
                "measurement_type": "duration",
                "actual_duration_seconds": 35,
                "actual_weight": 5,
            },
        )
        assert response.status_code == 200
        actual = response.json()["actual_set"]
        assert actual["measurement_type"] == "duration"
        assert actual["planned_duration_seconds"] == 30
        assert actual["actual_duration_seconds"] == 35
        assert actual["actual_reps"] is None
        assert actual["actual_rir"] is None

        invalid = client.post(
            f"/workout-plans/{plan_id}/actual-sets",
            json={
                "planned_workout_exercise_id": planned["distance"].id,
                "measurement_type": "distance",
                "actual_distance_meters": 20,
                "actual_rir": 2,
            },
        )
        assert invalid.status_code == 400
        assert "cannot include" in invalid.json()["detail"]
