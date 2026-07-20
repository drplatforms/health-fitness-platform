import re
from pathlib import Path

import pytest

import database
from services import exercise_catalog_service as catalog_service
from services import exercise_instruction_seed_data as seed_data
from services.exercise_catalog_service import (
    CURATED_EXERCISE_CATALOG,
    clear_exercise_catalog_cache,
    get_exercise_instruction,
    seed_exercise_catalog,
    seed_exercise_instructions,
)

FORBIDDEN_PRODUCTION_PHRASES = (
    "specified",
    "required",
    "chosen",
    "specified position",
    "required position",
    "required path",
    "specified grip",
    "specified squat style",
    "chosen shoulder position",
    "press, hold, or guide",
    "easy, steady, tempo, or interval",
    "hinged or supported",
    "supported or hinged",
    "step or split",
    "one or both arms",
    "stance or seat",
    "seated or standing position",
    "support, handles, or anchor",
    "when one is used",
    "when provided",
    "stand or kneel",
    "exercise's",
    "drill's starting position",
    "named conditioning quality",
)


@pytest.fixture(autouse=True)
def pytest_owned_database(tmp_path, monkeypatch):
    test_db = tmp_path / "fitness_ai_instruction_seed_test.db"
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert test_db.resolve() != canonical_db.resolve()

    monkeypatch.setattr(database, "DB_PATH", test_db)
    clear_exercise_catalog_cache()
    yield test_db
    clear_exercise_catalog_cache()


def _initialize_and_seed_instructions():
    database.initialize_database()
    return seed_exercise_instructions()


def _instruction_row_count() -> int:
    conn = database.get_connection()
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM exercise_catalog_instructions"
    ).fetchone()["count"]
    conn.close()
    return count


def _catalog_business_rows():
    conn = database.get_connection()
    rows = [
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
    ]
    conn.close()
    return rows


def test_seed_corpus_covers_exactly_all_300_curated_exercises():
    catalog_names = [entry.name for entry in CURATED_EXERCISE_CATALOG]
    seed_names = list(seed_data.EXERCISE_INSTRUCTION_SEEDS)

    assert len(catalog_names) == 300
    assert len(set(catalog_names)) == 300
    assert len(seed_names) == 300
    assert len(set(seed_names)) == 300
    assert set(seed_names) == set(catalog_names)


def test_every_seed_has_meaningful_complete_content_without_placeholders():
    blocked_markers = ("TODO", "PLACEHOLDER", "SAME AS")
    distinctive_steps = {
        seed.execution_steps[-1]
        for seed in seed_data.EXERCISE_INSTRUCTION_SEEDS.values()
    }

    assert len(distinctive_steps) == 300

    for name, seed in seed_data.EXERCISE_INSTRUCTION_SEEDS.items():
        assert len(seed.overview.strip()) >= 24, name
        list_fields = (
            seed.setup_steps,
            seed.execution_steps,
            seed.form_cues,
            seed.common_mistakes,
            seed.safety_notes,
        )
        assert all(values for values in list_fields), name
        all_content = (
            seed.overview,
            *(item for values in list_fields for item in values),
        )
        assert all(len(value.strip()) >= 12 for value in all_content), name
        upper_content = " ".join(all_content).upper()
        assert all(marker not in upper_content for marker in blocked_markers), name


def test_final_corpus_rejects_template_leakage_and_tautological_overviews():
    generic_execution_steps = {
        step
        for template in seed_data._TEMPLATES.values()
        for step in template.execution_steps
    }

    for name, seed in seed_data.EXERCISE_INSTRUCTION_SEEDS.items():
        all_content = " ".join(
            (
                seed.overview,
                *seed.setup_steps,
                *seed.execution_steps,
                *seed.form_cues,
                *seed.common_mistakes,
                *seed.safety_notes,
            )
        ).lower()

        assert all(
            phrase not in all_content for phrase in FORBIDDEN_PRODUCTION_PHRASES
        ), name
        assert generic_execution_steps.isdisjoint(seed.execution_steps), name
        assert not seed.overview.lower().startswith(
            f"{name.lower()} is a {name.lower()}"
        ), name


def test_seed_copy_does_not_require_unlisted_equipment():
    equipment_terms = {
        "dumbbell": "dumbbell",
        "barbell": "barbell",
        "cable": "cable",
        "band": "resistance_band",
        "bench": "adjustable_bench",
        "machine": "machine",
        "stability ball": "exercise_ball",
        "treadmill": "treadmill",
        "bike": "bike",
        "plate": "plates",
    }

    for entry in CURATED_EXERCISE_CATALOG:
        seed = seed_data.EXERCISE_INSTRUCTION_SEEDS[entry.name]
        content = " ".join(
            (
                seed.overview,
                *seed.setup_steps,
                *seed.execution_steps,
                *seed.form_cues,
                *seed.common_mistakes,
                *seed.safety_notes,
            )
        ).lower()
        for term, equipment in equipment_terms.items():
            if re.search(rf"\b{term}s?\b", content):
                assert equipment in entry.equipment_required, (entry.name, term)


def test_seeded_rows_use_persisted_catalog_ids_and_one_row_per_exercise():
    instructions = _initialize_and_seed_instructions()

    conn = database.get_connection()
    rows = conn.execute(
        """
        SELECT catalog.id AS catalog_id, instructions.exercise_id AS instruction_id
        FROM exercise_catalog_exercises AS catalog
        JOIN exercise_catalog_instructions AS instructions
          ON instructions.exercise_id = catalog.id
        ORDER BY catalog.id
        """
    ).fetchall()
    total_count = conn.execute(
        "SELECT COUNT(*) AS count FROM exercise_catalog_instructions"
    ).fetchone()["count"]
    distinct_count = conn.execute(
        "SELECT COUNT(DISTINCT exercise_id) AS count FROM exercise_catalog_instructions"
    ).fetchone()["count"]
    conn.close()

    assert len(instructions) == 300
    assert len(rows) == 300
    assert total_count == distinct_count == 300
    assert all(row["catalog_id"] == row["instruction_id"] for row in rows)


def test_all_300_seeded_instructions_are_readable_only_by_catalog_id():
    instructions = _initialize_and_seed_instructions()

    loaded = [
        get_exercise_instruction(instruction.catalog_exercise_id)
        for instruction in instructions
    ]

    assert len(loaded) == 300
    assert all(instruction is not None for instruction in loaded)
    assert loaded == instructions


def test_repeated_seeding_is_idempotent_and_preserves_complete_count():
    first = _initialize_and_seed_instructions()
    second = seed_exercise_instructions()

    assert len(first) == len(second) == 300
    assert first == second
    assert _instruction_row_count() == 300


@pytest.mark.parametrize(
    ("mismatch", "message"),
    (
        ("missing", "missing seed exercises: Push-Up"),
        ("unknown", "unknown seed exercises: Unknown Exercise"),
    ),
)
def test_seed_coverage_mismatch_fails_before_any_instruction_write(
    mismatch,
    message,
    monkeypatch,
):
    database.initialize_database()
    mismatched_seeds = dict(seed_data.EXERCISE_INSTRUCTION_SEEDS)
    if mismatch == "missing":
        mismatched_seeds.pop("Push-Up")
    else:
        mismatched_seeds["Unknown Exercise"] = next(iter(mismatched_seeds.values()))
    monkeypatch.setattr(seed_data, "EXERCISE_INSTRUCTION_SEEDS", mismatched_seeds)

    with pytest.raises(ValueError, match=message):
        seed_exercise_instructions()

    assert _instruction_row_count() == 0


def test_instruction_writes_roll_back_atomically_on_unexpected_failure(monkeypatch):
    database.initialize_database()
    original_upsert = catalog_service._upsert_exercise_instruction_row
    calls = 0

    def failing_upsert(cursor, instruction):
        nonlocal calls
        calls += 1
        original_upsert(cursor, instruction)
        if calls == 2:
            raise RuntimeError("simulated seed write failure")

    monkeypatch.setattr(
        catalog_service,
        "_upsert_exercise_instruction_row",
        failing_upsert,
    )

    with pytest.raises(RuntimeError, match="simulated seed write failure"):
        seed_exercise_instructions()

    assert calls == 2
    assert _instruction_row_count() == 0


def test_instruction_seeding_preserves_existing_catalog_records_and_ids():
    database.initialize_database()
    seed_exercise_catalog()
    before = _catalog_business_rows()

    seed_exercise_instructions()

    assert _catalog_business_rows() == before


def test_existing_catalog_seeding_remains_deterministic_with_instruction_seeds():
    database.initialize_database()
    seed_exercise_catalog()
    first = _catalog_business_rows()
    seed_exercise_instructions()

    seed_exercise_catalog()

    assert _catalog_business_rows() == first
    assert _instruction_row_count() == 300


def test_seed_tests_are_bound_to_pytest_owned_database(pytest_owned_database):
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"

    assert Path(database.DB_PATH).resolve() == pytest_owned_database.resolve()
    assert Path(database.DB_PATH).resolve() != canonical_db.resolve()


def _seed_content(exercise_name: str) -> str:
    seed = seed_data.EXERCISE_INSTRUCTION_SEEDS[exercise_name]
    return " ".join(
        (
            seed.overview,
            *seed.setup_steps,
            *seed.execution_steps,
            *seed.form_cues,
            *seed.common_mistakes,
            *seed.safety_notes,
        )
    ).lower()


def test_batch_1_physical_setup_profiles_avoid_generic_instruction_contradictions():
    dumbbell_push_press = _seed_content("Dumbbell Push Press")
    assert "dumbbells at shoulder height" in dumbbell_push_press
    assert "hold the bar" not in dumbbell_push_press
    assert "lower the bar" not in dumbbell_push_press

    dumbbell_cuban_press = _seed_content("Dumbbell Cuban Press")
    assert "raise the elbows" in dumbbell_cuban_press
    assert "upper arm still" not in dumbbell_cuban_press

    dumbbell_seated_calf_raise = _seed_content("Dumbbell Seated Calf Raise")
    assert "sit upright on the bench" in dumbbell_seated_calf_raise
    assert "stand tall" not in dumbbell_seated_calf_raise

    machine_seated_calf_raise = _seed_content("Machine Seated Calf Raise")
    assert "sit fully into the machine" in machine_seated_calf_raise
    assert "stand tall" not in machine_seated_calf_raise

    barbell_hack_squat = _seed_content("Barbell Hack Squat")
    assert "close behind the calves" in barbell_hack_squat
    assert "unrack" not in barbell_hack_squat
    assert "rack hooks" not in barbell_hack_squat

    standing_cable_crunch = _seed_content("Standing Cable Crunch")
    assert "stand facing away from the cable stack" in standing_cable_crunch
    assert "kneel" not in standing_cable_crunch
    assert "padding for the knees" not in standing_cable_crunch

    band_step_up = _seed_content("Band Step-Up")
    assert "stand on the band" in band_step_up
    assert "anchor" not in band_step_up

    low_cable_fly = _seed_content("Low Cable Fly")
    assert "hands low beside the hips" in low_cable_fly
    assert "hands in front of the chest" not in low_cable_fly

    self_assisted_nordic_curl = _seed_content("Self-Assisted Nordic Curl")
    assert "lower the torso under hamstring control" in self_assisted_nordic_curl
    assert "heels toward the hips" not in self_assisted_nordic_curl

    cable_assisted_nordic_curl = _seed_content("Cable-Assisted Nordic Curl")
    assert "lowering forward from the knees" in cable_assisted_nordic_curl
    assert "heels toward the hips" not in cable_assisted_nordic_curl


def test_final_batch_1_profiles_avoid_remaining_generic_template_leakage():
    archer_push_up = _seed_content("Archer Push-Up")
    assert "hands well wider than shoulder width" in archer_push_up
    assert "about shoulder width" not in archer_push_up

    pistol_squat = _seed_content("Pistol Squat")
    assert "one working foot" in pistol_squat
    assert "extend the free leg forward" in pistol_squat
    assert "feet at a comfortable squat width" not in pistol_squat

    single_arm_shoulder_press = _seed_content("Single-Arm Dumbbell Shoulder Press")
    assert "one dumbbell at the working shoulder" in single_arm_shoulder_press
    assert "one side faster than the other" not in single_arm_shoulder_press
    assert "wrists stacked above the elbows" not in single_arm_shoulder_press

    single_arm_bench_press = _seed_content("Single-Arm Dumbbell Bench Press")
    assert "hold one dumbbell over the working side" in single_arm_bench_press
    assert "dumbbells over the chest" not in single_arm_bench_press

    dumbbell_single_leg_calf_raise = _seed_content("Dumbbell Single-Leg Calf Raise")
    assert "free foot off the floor" in dumbbell_single_leg_calf_raise
    assert "distribute weight evenly" not in dumbbell_single_leg_calf_raise

    reverse_grip_incline_row = _seed_content("Reverse-Grip Incline Dumbbell Row")
    assert "incline bench securely" in reverse_grip_incline_row
    assert "row station or anchor" not in reverse_grip_incline_row

    rear_delt_row = _seed_content("Bench-Supported Dumbbell Rear Delt Row")
    assert "rear-delt row" in rear_delt_row
    assert "turning the movement into a row" not in rear_delt_row

    cable_reverse_crunch = _seed_content("Cable Reverse Crunch")
    assert "controlled posterior pelvic curl" in cable_reverse_crunch
    assert "lifts or arches the lower back" not in cable_reverse_crunch

    band_seated_row = _seed_content("Resistance Band Seated Row")
    assert "band looped securely around both feet" in band_seated_row
    assert "row station or anchor" not in band_seated_row

    band_single_leg_calf_raise = _seed_content("Band Single-Leg Calf Raise")
    assert "free foot off the floor" in band_single_leg_calf_raise
    assert "distribute weight evenly" not in band_single_leg_calf_raise

    band_reverse_fly = _seed_content("Band Reverse Fly")
    assert "band in front at chest height" in band_reverse_fly
    assert "arms hanging" not in band_reverse_fly

    machine_reverse_fly = _seed_content("Machine Reverse Fly")
    assert "face the chest pad" in machine_reverse_fly
    assert "arms hanging" not in machine_reverse_fly

    assisted_triceps_dip = _seed_content("Assisted Triceps Dip")
    assert "kneel on the assistance pad" in assisted_triceps_dip
    assert "shoulders controlled rather than forcing" in assisted_triceps_dip
    assert "move at the elbows rather than the shoulders" not in assisted_triceps_dip
