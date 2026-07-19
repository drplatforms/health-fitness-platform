import sqlite3
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app
from models.exercise_catalog_models import EXERCISE_PROTOCOL_SLUGS
from services import exercise_catalog_service, exercise_protocol_seed_data

EXPECTED_LINKS = {
    "Treadmill Intervals": "intervals",
    "Bike Steady State": "steady_state",
    "Bike Intervals": "intervals",
    "Tempo Push-Up": "tempo",
    "Pause Squat": "pause",
    "Treadmill Easy Jog": "easy",
    "Treadmill Hill Intervals": "hill_intervals",
    "Treadmill Tempo Run": "tempo",
    "Bike Recovery Ride": "recovery",
    "Bike Tempo Ride": "tempo",
    "Bike Hill Intervals": "hill_intervals",
    "Dumbbell Tempo Goblet Squat": "tempo",
    "Treadmill Recovery Walk": "recovery",
    "Treadmill Easy Intervals": "easy_intervals",
    "Bike Easy Spin": "easy",
    "Bike Cadence Drill": "cadence_drill",
}


@pytest.fixture(autouse=True)
def protocol_db(tmp_path, monkeypatch):
    path = tmp_path / "exercise_protocols.db"
    canonical_path = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert path.resolve() != canonical_path.resolve()
    monkeypatch.setattr(database, "DB_PATH", path)
    exercise_catalog_service.clear_exercise_catalog_cache()
    database.initialize_database()
    exercise_catalog_service.seed_exercise_catalog()
    exercise_catalog_service.seed_exercise_protocols()
    yield
    exercise_catalog_service.clear_exercise_catalog_cache()


def _catalog_id(name: str) -> int:
    entry = exercise_catalog_service.find_catalog_entry_by_name(name)
    assert entry is not None and entry.id is not None
    return entry.id


def _projection():
    conn = database.get_connection()
    try:
        return tuple(
            tuple(row)
            for row in conn.execute(
                """
                SELECT e.name, p.exercise_id, p.protocol_slug
                FROM exercise_catalog_protocols AS p
                JOIN exercise_catalog_exercises AS e ON e.id = p.exercise_id
                ORDER BY e.name
                """
            ).fetchall()
        )
    finally:
        conn.close()


def _catalog_semantics():
    conn = database.get_connection()
    try:
        exercises = tuple(
            tuple(row)
            for row in conn.execute(
                """
                SELECT id, name, exercise_type, movement_pattern,
                       primary_muscle_groups_json, difficulty, created_at, updated_at
                FROM exercise_catalog_exercises
                ORDER BY id
                """
            ).fetchall()
        )
        equipment = tuple(
            tuple(row)
            for row in conn.execute(
                """
                SELECT id, exercise_id, equipment, created_at
                FROM exercise_equipment_requirements
                ORDER BY id
                """
            ).fetchall()
        )
    finally:
        conn.close()
    return exercises, equipment


def test_registry_and_manifest_match_accepted_protocol_evidence():
    templates = exercise_protocol_seed_data.EXERCISE_PROTOCOL_TEMPLATES
    links = exercise_protocol_seed_data.EXERCISE_PROTOCOL_SEEDS

    assert isinstance(EXERCISE_PROTOCOL_SLUGS, frozenset)
    assert len(templates) == len(EXERCISE_PROTOCOL_SLUGS) == 9
    assert {item.protocol_slug for item in templates} == EXERCISE_PROTOCOL_SLUGS
    assert len(links) == len({item.canonical_exercise_name for item in links}) == 16
    assert {
        item.canonical_exercise_name: item.protocol_slug for item in links
    } == EXPECTED_LINKS
    assert Counter(item.protocol_slug for item in links) == {
        "tempo": 4,
        "intervals": 2,
        "easy": 2,
        "hill_intervals": 2,
        "recovery": 2,
        "steady_state": 1,
        "pause": 1,
        "easy_intervals": 1,
        "cadence_drill": 1,
    }
    assert all(item.description and item.display_name for item in templates)


def test_seed_is_stable_idempotent_stale_cleaning_and_preserves_catalog_rows():
    before_catalog = _catalog_semantics()
    first = exercise_catalog_service.seed_exercise_protocols()
    first_projection = _projection()
    second = exercise_catalog_service.seed_exercise_protocols()

    assert len(first) == len(second) == 16
    assert len({item.catalog_exercise_id for item in first}) == 16
    assert _projection() == first_projection
    assert _catalog_semantics() == before_catalog

    conn = database.get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO exercise_catalog_exercises (
                    name, exercise_type, movement_pattern,
                    primary_muscle_groups_json, difficulty
                ) VALUES ('Stale Protocol Exercise', 'strength', 'squat', '[]', 'beginner')
                """
            )
            stale_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO exercise_catalog_protocols (exercise_id, protocol_slug)
                VALUES (?, 'tempo')
                """,
                (stale_id,),
            )
    finally:
        conn.close()

    exercise_catalog_service.seed_exercise_protocols()
    assert len(_projection()) == 16
    assert exercise_catalog_service.get_exercise_protocol_metadata(stale_id) is None


def test_seed_requires_an_established_catalog_without_creating_or_mutating_one(
    tmp_path, monkeypatch
):
    path = tmp_path / "missing_catalog.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    exercise_catalog_service.clear_exercise_catalog_cache()
    database.initialize_database()

    with pytest.raises(ValueError, match="missing protocol targets"):
        exercise_catalog_service.seed_exercise_protocols()

    conn = database.get_connection()
    try:
        assert (
            conn.execute("SELECT COUNT(*) FROM exercise_catalog_exercises").fetchone()[
                0
            ]
            == 0
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM exercise_equipment_requirements"
            ).fetchone()[0]
            == 0
        )
    finally:
        conn.close()


def test_invalid_manifest_fails_before_writing_projection(monkeypatch):
    before = _projection()
    original = exercise_protocol_seed_data.EXERCISE_PROTOCOL_SEEDS
    monkeypatch.setattr(
        exercise_protocol_seed_data,
        "EXERCISE_PROTOCOL_SEEDS",
        (replace(original[0], protocol_slug="unsupported"), *original[1:]),
    )

    with pytest.raises(ValueError, match="unsupported protocol"):
        exercise_catalog_service.seed_exercise_protocols()
    assert _projection() == before


def test_seed_rolls_back_on_unexpected_failure_without_catalog_mutation():
    projection_before = _projection()
    catalog_before = _catalog_semantics()
    fail_id = projection_before[len(projection_before) // 2][1]
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                f"""
                CREATE TRIGGER fail_protocol_seed
                BEFORE INSERT ON exercise_catalog_protocols
                WHEN NEW.exercise_id = {int(fail_id)}
                BEGIN
                    SELECT RAISE(ABORT, 'forced protocol seed failure');
                END
                """
            )
        with pytest.raises(
            sqlite3.IntegrityError, match="forced protocol seed failure"
        ):
            exercise_catalog_service.seed_exercise_protocols()
    finally:
        with conn:
            conn.execute("DROP TRIGGER IF EXISTS fail_protocol_seed")
        conn.close()

    assert _projection() == projection_before
    assert _catalog_semantics() == catalog_before


def test_stable_id_reads_are_bounded_and_detect_corrupt_persisted_slugs():
    tempo_push_up_id = _catalog_id("Tempo Push-Up")
    metadata = exercise_catalog_service.get_exercise_protocol_metadata(tempo_push_up_id)
    assert metadata is not None and metadata.protocol_slug == "tempo"
    assert exercise_catalog_service.get_exercise_protocol_template("tempo") is not None
    assert exercise_catalog_service.get_exercise_protocol_template("unknown") is None
    assert (
        exercise_catalog_service.get_exercise_protocol_metadata(
            _catalog_id("Barbell Bench Press")
        )
        is None
    )
    assert exercise_catalog_service.get_exercise_protocol_metadata(999_999) is None
    with pytest.raises(ValueError, match="positive integer"):
        exercise_catalog_service.get_exercise_protocol_metadata(0)

    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE exercise_catalog_protocols SET protocol_slug = 'bad' WHERE exercise_id = ?",
                (tempo_push_up_id,),
            )
    finally:
        conn.close()
    with pytest.raises(ValueError, match="Invalid persisted exercise protocol slug"):
        exercise_catalog_service.get_exercise_protocol_metadata(tempo_push_up_id)


def test_protocol_api_is_read_only_and_handles_present_absent_unknown_and_invalid_ids():
    with TestClient(app) as client:
        present = client.get(
            f"/exercise-catalog/{_catalog_id('Tempo Push-Up')}/protocol"
        )
        absent = client.get(
            f"/exercise-catalog/{_catalog_id('Barbell Bench Press')}/protocol"
        )
        unknown = client.get("/exercise-catalog/999999/protocol")
        invalid = client.get("/exercise-catalog/0/protocol")

    assert present.status_code == 200
    assert present.json()["exercise"]["name"] == "Tempo Push-Up"
    assert present.json()["protocol"]["slug"] == "tempo"
    assert absent.status_code == 200 and absent.json()["protocol"] is None
    assert unknown.status_code == 404
    assert invalid.status_code == 422
