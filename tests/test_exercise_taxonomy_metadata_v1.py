import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import pytest

import database
from services import exercise_catalog_service, exercise_taxonomy_seed_data

EXPECTED_FAMILIES = frozenset(
    {
        "ankle_plantarflexion",
        "back_extension",
        "bilateral_knee_dominant",
        "chest_fly",
        "core_anti_extension",
        "core_anti_rotation",
        "elbow_extension",
        "elbow_flexion",
        "gait_drill",
        "ground_conditioning",
        "hip_abduction",
        "hip_extension",
        "hip_hinge",
        "horizontal_press",
        "knee_flexion",
        "lateral_core_stability",
        "lateral_trunk_flexion",
        "loaded_carry",
        "mobility",
        "quadrupedal_locomotion",
        "rear_delt_retraction",
        "rotational_core",
        "rowing",
        "scapular_elevation",
        "shoulder_elevation",
        "shoulder_extension",
        "shoulder_mobility",
        "shoulder_rotation",
        "stationary_cycling",
        "treadmill_locomotion",
        "trunk_flexion",
        "unilateral_knee_dominant",
        "vertical_power_pull",
        "vertical_press",
        "vertical_pull",
    }
)
EXPECTED_SHARED_VISUAL_IDENTITIES = {
    "visual_goblet_squat": ("Goblet Squat", "Dumbbell Tempo Goblet Squat"),
    "visual_push_up": ("Push-Up", "Tempo Push-Up"),
    "visual_stationary_bike": (
        "Bike Steady State",
        "Bike Intervals",
        "Bike Recovery Ride",
        "Bike Tempo Ride",
        "Bike Hill Intervals",
        "Bike Easy Spin",
        "Bike Cadence Drill",
    ),
    "visual_treadmill_walk": ("Treadmill Walk", "Treadmill Recovery Walk"),
}
EXPECTED_CONTROLLED_VALUES = {
    "body_position": frozenset(
        {
            "chest_supported",
            "childs_pose",
            "half_kneeling",
            "plank",
            "prone",
            "quadruped",
            "seated",
            "standing",
            "tall_kneeling",
        }
    ),
    "support_type": frozenset({"bench", "floor", "machine", "thigh", "wall"}),
    "bench_angle": frozenset({"decline", "incline", "low_incline"}),
    "laterality": frozenset({"bilateral", "unilateral"}),
    "grip": frozenset(
        {
            "close",
            "hammer",
            "mixed",
            "neutral",
            "pinch",
            "pronated",
            "reverse",
            "supinated",
        }
    ),
    "stance": frozenset({"split", "sumo"}),
    "load_position": frozenset(
        {"front_rack", "goblet", "overhead", "sides", "suitcase"}
    ),
    "attachment": frozenset({"rope"}),
    "movement_direction": frozenset(
        {"cross_body", "high_diagonal", "horizontal", "rotation", "vertical"}
    ),
    "locomotion_mode": frozenset({"jog", "march", "run", "unspecified", "walk"}),
    "execution_mode": frozenset({"dynamic", "eccentric_only", "isometric"}),
}
EXPECTED_SEMANTIC_INVARIANTS = {
    "Dumbbell Skater Squat": (
        "unilateral_knee_dominant",
        "skater_squat",
        "reviewed",
        {"laterality": "unilateral"},
        {},
    ),
    "Romanian Deadlift": (
        "hip_hinge",
        "romanian_deadlift",
        "reviewed",
        {},
        {},
    ),
    "Conventional Deadlift": (
        "hip_hinge",
        "conventional_deadlift",
        "reviewed",
        {},
        {},
    ),
    "Cable High Row": (
        "rowing",
        "high_row",
        "reviewed",
        {"movement_direction": "high_diagonal"},
        {},
    ),
    "Cable Rear Delt Row": (
        "rear_delt_retraction",
        "rear_delt_row",
        "reviewed",
        {"movement_direction": "horizontal"},
        {},
    ),
    "Pike Push-Up": (
        "vertical_press",
        "pike_push_up",
        "reviewed",
        {},
        {},
    ),
    "Push Press": (
        "vertical_press",
        "push_press",
        "reviewed",
        {"execution_mode": "dynamic"},
        {"lower_body_drive": "deliberate"},
    ),
    "Barbell Squat": (
        "bilateral_knee_dominant",
        "barbell_squat_unspecified",
        "review_required",
        {},
        {},
    ),
    "Cable Kickback": (
        "hip_extension",
        "glute_kickback",
        "review_required",
        {},
        {},
    ),
    "Dead Hang": (
        "vertical_pull",
        "bar_hang",
        "alias_candidate",
        {"execution_mode": "isometric"},
        {},
    ),
}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    path = tmp_path / "taxonomy.db"
    canonical_path = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert path.resolve() != canonical_path.resolve()
    monkeypatch.setattr(database, "DB_PATH", path)
    exercise_catalog_service.clear_exercise_catalog_cache()
    yield path
    exercise_catalog_service.clear_exercise_catalog_cache()


def _catalog_id(name):
    conn = database.get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM exercise_catalog_exercises WHERE name = ?", (name,)
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return row["id"]


def _taxonomy_projection():
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                e.name,
                t.exercise_id,
                t.family_slug,
                t.base_movement_slug,
                t.visual_identity_slug,
                t.taxonomy_status,
                t.body_position,
                t.support_type,
                t.bench_angle,
                t.laterality,
                t.grip,
                t.stance,
                t.load_position,
                t.attachment,
                t.movement_direction,
                t.locomotion_mode,
                t.execution_mode,
                t.variant_extensions_json
            FROM exercise_catalog_taxonomy AS t
            JOIN exercise_catalog_exercises AS e ON e.id = t.exercise_id
            ORDER BY e.name
            """
        ).fetchall()
    finally:
        conn.close()
    return tuple(tuple(row) for row in rows)


def _catalog_semantics():
    conn = database.get_connection()
    try:
        exercises = tuple(
            tuple(row)
            for row in conn.execute(
                """
                SELECT
                    id,
                    name,
                    exercise_type,
                    movement_pattern,
                    primary_muscle_groups_json,
                    difficulty
                FROM exercise_catalog_exercises
                ORDER BY id
                """
            ).fetchall()
        )
        equipment = tuple(
            tuple(row)
            for row in conn.execute(
                """
                SELECT exercise_id, equipment
                FROM exercise_equipment_requirements
                ORDER BY exercise_id, equipment
                """
            ).fetchall()
        )
    finally:
        conn.close()
    return exercises, equipment


def test_taxonomy_controlled_vocabularies_are_immutable_module_constants():
    assert isinstance(exercise_catalog_service._TAXONOMY_CONTROLLED_FIELDS, tuple)
    controlled_values = exercise_catalog_service._TAXONOMY_CONTROLLED_VALUES
    assert isinstance(controlled_values, MappingProxyType)
    assert dict(controlled_values) == EXPECTED_CONTROLLED_VALUES
    assert (
        tuple(controlled_values) == exercise_catalog_service._TAXONOMY_CONTROLLED_FIELDS
    )
    assert all(isinstance(values, frozenset) for values in controlled_values.values())
    assert exercise_catalog_service._ALLOWED_TAXONOMY_EXTENSION_KEYS == frozenset(
        {"grade", "range", "range_of_motion_variant", "lower_body_drive"}
    )
    assert exercise_catalog_service._SUPPORTED_TAXONOMY_STATUSES == frozenset(
        {"reviewed", "alias_candidate", "review_required"}
    )

    with pytest.raises(TypeError):
        controlled_values["body_position"] = frozenset()
    with pytest.raises(AttributeError):
        controlled_values["body_position"].add("unsupported")
    with pytest.raises(AttributeError):
        exercise_catalog_service._ALLOWED_TAXONOMY_EXTENSION_KEYS.add("unsupported")
    with pytest.raises(AttributeError):
        exercise_catalog_service._SUPPORTED_TAXONOMY_STATUSES.add("unsupported")


def test_manifest_has_exact_accepted_coverage_counts_and_shared_visual_groups():
    seeds = exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS
    catalog_names = {
        entry.name for entry in exercise_catalog_service.CURATED_EXERCISE_CATALOG
    }
    seed_names = [seed.canonical_exercise_name for seed in seeds]
    assert len(seeds) == len(seed_names) == len(set(seed_names)) == 240
    assert set(seed_names) == catalog_names
    assert {seed.family_slug for seed in seeds} == EXPECTED_FAMILIES
    assert len({seed.visual_identity_slug for seed in seeds}) == 231
    assert Counter(seed.taxonomy_status for seed in seeds) == {
        "reviewed": 233,
        "alias_candidate": 3,
        "review_required": 4,
    }

    names_by_visual_identity = defaultdict(list)
    for seed in seeds:
        names_by_visual_identity[seed.visual_identity_slug].append(
            seed.canonical_exercise_name
        )
    shared = {
        visual_identity: tuple(names)
        for visual_identity, names in names_by_visual_identity.items()
        if len(names) > 1
    }
    assert shared == EXPECTED_SHARED_VISUAL_IDENTITIES


def test_manifest_preserves_representative_semantic_invariants():
    seeds_by_name = {
        seed.canonical_exercise_name: seed
        for seed in exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS
    }
    for name, expected in EXPECTED_SEMANTIC_INVARIANTS.items():
        seed = seeds_by_name[name]
        assert (
            seed.family_slug,
            seed.base_movement_slug,
            seed.taxonomy_status,
            seed.variants,
            seed.variant_extensions,
        ) == expected


def test_taxonomy_schema_owns_primary_key_fk_and_excludes_equipment():
    database.initialize_database()
    exercise_catalog_service.ensure_exercise_catalog_tables()
    conn = database.get_connection()
    try:
        columns = conn.execute(
            "PRAGMA table_info(exercise_catalog_taxonomy)"
        ).fetchall()
        foreign_keys = conn.execute(
            "PRAGMA foreign_key_list(exercise_catalog_taxonomy)"
        ).fetchall()
    finally:
        conn.close()

    assert [(row["name"], row["pk"]) for row in columns if row["pk"]] == [
        ("exercise_id", 1)
    ]
    assert {(row["from"], row["table"], row["to"]) for row in foreign_keys} == {
        ("exercise_id", "exercise_catalog_exercises", "id")
    }
    assert "equipment" not in {row["name"] for row in columns}


def test_seed_projects_all_rows_exactly_and_is_idempotent_with_stable_catalog_ids():
    database.initialize_database()
    first_metadata = exercise_catalog_service.seed_exercise_taxonomy()
    first_projection = _taxonomy_projection()
    first_ids = {
        seed.canonical_exercise_name: metadata.catalog_exercise_id
        for seed, metadata in zip(
            exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS,
            first_metadata,
            strict=True,
        )
    }
    assert len(first_projection) == len(first_metadata) == 240

    persisted_by_name = {row[0]: row for row in first_projection}
    for seed in exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS:
        row = persisted_by_name[seed.canonical_exercise_name]
        assert row[1] == first_ids[seed.canonical_exercise_name]
        assert row[2:6] == (
            seed.family_slug,
            seed.base_movement_slug,
            seed.visual_identity_slug,
            seed.taxonomy_status,
        )
        assert {
            field: row[index]
            for index, field in enumerate(
                exercise_catalog_service._TAXONOMY_CONTROLLED_FIELDS, start=6
            )
            if row[index] is not None
        } == seed.variants
        assert json.loads(row[-1]) == seed.variant_extensions

    second_metadata = exercise_catalog_service.seed_exercise_taxonomy()
    assert _taxonomy_projection() == first_projection
    assert {
        seed.canonical_exercise_name: metadata.catalog_exercise_id
        for seed, metadata in zip(
            exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS,
            second_metadata,
            strict=True,
        )
    } == first_ids


def test_reseeding_removes_stale_taxonomy_rows():
    database.initialize_database()
    exercise_catalog_service.seed_exercise_taxonomy()
    conn = database.get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO exercise_catalog_exercises (
                    name,
                    exercise_type,
                    movement_pattern,
                    primary_muscle_groups_json,
                    difficulty
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("Stale Taxonomy Exercise", "strength", "hinge", "[]", "beginner"),
            )
            stale_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO exercise_catalog_taxonomy (
                    exercise_id,
                    family_slug,
                    base_movement_slug,
                    visual_identity_slug,
                    taxonomy_status,
                    variant_extensions_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    stale_id,
                    "hip_hinge",
                    "stale_movement",
                    "visual_stale_movement",
                    "reviewed",
                    "{}",
                ),
            )
    finally:
        conn.close()

    assert len(_taxonomy_projection()) == 241
    exercise_catalog_service.seed_exercise_taxonomy()
    projection = _taxonomy_projection()
    assert len(projection) == 240
    assert "Stale Taxonomy Exercise" not in {row[0] for row in projection}


def _duplicate_manifest(seeds):
    return seeds + (seeds[0],)


def _unknown_manifest(seeds):
    return (replace(seeds[0], canonical_exercise_name="Unknown Exercise"), *seeds[1:])


def _incomplete_manifest(seeds):
    return seeds[:-1]


def _invalid_token_manifest(seeds):
    return (replace(seeds[0], family_slug="invalid/family"), *seeds[1:])


def _invalid_controlled_value_manifest(seeds):
    return (replace(seeds[0], variants={"support_type": "ceiling"}), *seeds[1:])


def _invalid_extension_key_manifest(seeds):
    return (
        replace(seeds[0], variant_extensions={"unsupported_extension": "value"}),
        *seeds[1:],
    )


def _invalid_status_manifest(seeds):
    return (replace(seeds[0], taxonomy_status="unsupported"), *seeds[1:])


@pytest.mark.parametrize(
    ("mutate_manifest", "message"),
    (
        (_duplicate_manifest, "exact unique canonical-name coverage"),
        (_unknown_manifest, "exact unique canonical-name coverage"),
        (_incomplete_manifest, "exact unique canonical-name coverage"),
        (_invalid_token_manifest, "strict normalized tokens"),
        (_invalid_controlled_value_manifest, "Unsupported taxonomy controlled value"),
        (_invalid_extension_key_manifest, "Unsupported taxonomy variant field"),
        (_invalid_status_manifest, "Unsupported taxonomy status"),
    ),
)
def test_invalid_manifests_fail_before_taxonomy_projection_writes(
    monkeypatch, mutate_manifest, message
):
    database.initialize_database()
    exercise_catalog_service.seed_exercise_taxonomy()
    before = _taxonomy_projection()
    original = exercise_taxonomy_seed_data.EXERCISE_TAXONOMY_SEEDS
    monkeypatch.setattr(
        exercise_taxonomy_seed_data,
        "EXERCISE_TAXONOMY_SEEDS",
        mutate_manifest(original),
    )

    with pytest.raises(ValueError, match=message):
        exercise_catalog_service.seed_exercise_taxonomy()
    assert _taxonomy_projection() == before


def test_unexpected_insert_failure_rolls_back_exact_taxonomy_projection():
    database.initialize_database()
    exercise_catalog_service.seed_exercise_taxonomy()
    before = _taxonomy_projection()
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                """
                CREATE TRIGGER fail_taxonomy_insert
                BEFORE INSERT ON exercise_catalog_taxonomy
                BEGIN
                    SELECT RAISE(ABORT, 'forced taxonomy insert failure');
                END
                """
            )
    finally:
        conn.close()

    with pytest.raises(sqlite3.IntegrityError, match="forced taxonomy insert failure"):
        exercise_catalog_service.seed_exercise_taxonomy()
    assert _taxonomy_projection() == before


def test_taxonomy_reseeding_preserves_catalog_ids_and_semantic_fields():
    database.initialize_database()
    exercise_catalog_service.seed_exercise_catalog()
    before = _catalog_semantics()
    exercise_catalog_service.seed_exercise_taxonomy()
    exercise_catalog_service.seed_exercise_taxonomy()
    assert _catalog_semantics() == before


def test_taxonomy_read_service_uses_stable_ids_and_decodes_variants_and_extensions():
    database.initialize_database()
    exercise_catalog_service.seed_exercise_taxonomy()
    incline_id = _catalog_id("Incline Dumbbell Press")
    incline = exercise_catalog_service.get_exercise_taxonomy(incline_id)
    assert incline is not None
    assert incline.catalog_exercise_id == incline_id
    assert incline.support_type == "bench"
    assert incline.bench_angle == "incline"
    assert incline.variant_extensions == {}

    push_press = exercise_catalog_service.get_exercise_taxonomy(
        _catalog_id("Push Press")
    )
    assert push_press is not None
    assert push_press.execution_mode == "dynamic"
    assert push_press.variant_extensions == {"lower_body_drive": "deliberate"}
    assert exercise_catalog_service.get_exercise_taxonomy(999_999) is None


@pytest.mark.parametrize("catalog_exercise_id", (0, -1))
def test_taxonomy_read_rejects_nonpositive_id(catalog_exercise_id):
    with pytest.raises(ValueError, match="positive integer"):
        exercise_catalog_service.get_exercise_taxonomy(catalog_exercise_id)


@pytest.mark.parametrize(
    "persisted_extensions",
    ("{", "[]", '{"grade": 1}', '{"grade": null}'),
)
def test_taxonomy_read_raises_for_malformed_or_invalid_extension_payloads(
    persisted_extensions,
):
    database.initialize_database()
    exercise_catalog_service.seed_exercise_taxonomy()
    exercise_id = _catalog_id("Treadmill Incline Walk")
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                """
                UPDATE exercise_catalog_taxonomy
                SET variant_extensions_json = ?
                WHERE exercise_id = ?
                """,
                (persisted_extensions, exercise_id),
            )
    finally:
        conn.close()

    with pytest.raises(
        ValueError, match="Invalid persisted taxonomy variant extensions"
    ):
        exercise_catalog_service.get_exercise_taxonomy(exercise_id)
