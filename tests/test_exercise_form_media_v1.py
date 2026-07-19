import sqlite3
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

import database
from services import exercise_catalog_service as catalog_service
from services import exercise_form_media_seed_data as seed_data
from services.exercise_catalog_service import (
    clear_exercise_catalog_cache,
    get_exercise_catalog,
    get_exercise_catalog_entry_by_id,
    get_exercise_form_media,
    seed_exercise_form_media,
    seed_exercise_taxonomy,
)


@pytest.fixture(autouse=True)
def pytest_owned_database(tmp_path, monkeypatch):
    test_db = tmp_path / "fitness_ai_form_media_test.db"
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert test_db.resolve() != canonical_db.resolve()

    monkeypatch.setattr(database, "DB_PATH", test_db)
    clear_exercise_catalog_cache()
    yield test_db
    clear_exercise_catalog_cache()


def _seed_media():
    database.initialize_database()
    seed_exercise_taxonomy()
    return seed_exercise_form_media()


def _media_row_count() -> int:
    conn = database.get_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM exercise_catalog_form_media"
        ).fetchone()["count"]
    except sqlite3.OperationalError:
        count = 0
    conn.close()
    return count


def _media_rows() -> list[tuple]:
    conn = database.get_connection()
    rows = [
        tuple(row)
        for row in conn.execute(
            "SELECT * FROM exercise_catalog_form_media ORDER BY exercise_id, sort_order"
        ).fetchall()
    ]
    conn.close()
    return rows


def test_final_pack_has_eighty_three_exact_catalog_mappings_and_one_hundred_sixty_six_images():
    seeds = seed_data.EXERCISE_FORM_MEDIA_SEEDS

    assert len(seeds) == 166
    assert len({seed.canonical_exercise_name for seed in seeds}) == 83
    assert (
        len({(seed.canonical_exercise_name, seed.media_key) for seed in seeds}) == 166
    )
    assert len({seed.source_exercise_id for seed in seeds}) == 83
    assert all(seed.media_key in {"start", "finish"} for seed in seeds)
    assert "Seated Dumbbell Shoulder Press" in {
        seed.canonical_exercise_name for seed in seeds
    }
    assert "Dumbbell Shoulder Press" not in {
        seed.canonical_exercise_name for seed in seeds
    }
    assert "Hanging Knee Raise" not in {seed.canonical_exercise_name for seed in seeds}
    assert "Push Press" not in {seed.canonical_exercise_name for seed in seeds}
    assert {
        "Push-Up",
        "Pull-Up",
        "Bench Dip",
        "Rack Pull",
        "EZ-Bar Curl",
        "Chin-Up",
        "Decline Push-Up",
        "Barbell Glute Bridge",
        "Scapular Pull-Up",
        "Band Good Morning",
        "Cable Internal Rotation",
        "Barbell Shrug",
        "Barbell Lunge",
    }.issubset({seed.canonical_exercise_name for seed in seeds})


def test_expanded_manifest_has_one_complete_ordered_pair_per_canonical_exercise():
    by_name = {}
    for seed in seed_data.EXERCISE_FORM_MEDIA_SEEDS:
        by_name.setdefault(seed.canonical_exercise_name, []).append(seed)

    assert all(
        [(seed.media_key, seed.sort_order) for seed in seeds]
        == [("start", 1), ("finish", 2)]
        for seeds in by_name.values()
    )
    assert all(
        seed.source_url.endswith(f"/{seed.sort_order - 1}.jpg")
        for seed in seed_data.EXERCISE_FORM_MEDIA_SEEDS
    )


def test_every_seeded_asset_is_local_checksum_verified_and_has_complete_provenance():
    for seed in seed_data.EXERCISE_FORM_MEDIA_SEEDS:
        local_asset = catalog_service._PUBLIC_DIRECTORY / seed.asset_path.lstrip("/")

        assert seed.asset_path.startswith("/exercise-media/free-exercise-db/")
        assert local_asset.is_file()
        assert sha256(local_asset.read_bytes()).hexdigest() == seed.asset_sha256
        assert seed.source_url.startswith(
            "https://raw.githubusercontent.com/yuhonas/free-exercise-db/"
        )
        assert seed_data.SOURCE_NAME == "Free Exercise DB"
        assert seed_data.LICENSE_NAME == "Unlicense"
        assert (
            seed_data.LICENSE_URL
            == "https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md"
        )
        assert seed.alt_text


def test_media_table_is_additive_and_uses_catalog_identity_with_composite_key():
    _seed_media()

    conn = database.get_connection()
    columns = {
        row["name"]: row
        for row in conn.execute(
            "PRAGMA table_info(exercise_catalog_form_media)"
        ).fetchall()
    }
    foreign_keys = conn.execute(
        "PRAGMA foreign_key_list(exercise_catalog_form_media)"
    ).fetchall()
    conn.close()

    assert columns["exercise_id"]["pk"] == 1
    assert columns["media_key"]["pk"] == 2
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["table"] == "exercise_catalog_exercises"
    assert foreign_keys[0]["from"] == "exercise_id"
    assert foreign_keys[0]["to"] == "id"


def test_seeded_media_reads_by_stable_id_in_deterministic_order_without_fallback():
    assets = _seed_media()
    covered_id = next(
        asset.catalog_exercise_id
        for asset in assets
        if get_exercise_catalog_entry_by_id(asset.catalog_exercise_id).name == "Plank"
    )
    uncovered_id = next(
        entry.id for entry in get_exercise_catalog() if entry.name == "Back Squat"
    )
    assert uncovered_id is not None

    covered = get_exercise_form_media(covered_id)

    assert [asset.media_key for asset in covered] == ["start", "finish"]
    assert [asset.sort_order for asset in covered] == [1, 2]
    assert {asset.catalog_exercise_id for asset in covered} == {covered_id}
    assert get_exercise_form_media(uncovered_id) == []


def test_reseeding_is_idempotent_and_does_not_rewrite_catalog_records():
    database.initialize_database()
    seed_exercise_taxonomy()
    conn = database.get_connection()
    before_catalog = [
        tuple(row)
        for row in conn.execute(
            """
            SELECT id, name, exercise_type, movement_pattern,
                   primary_muscle_groups_json, difficulty, created_at, updated_at
            FROM exercise_catalog_exercises
            ORDER BY id
            """
        ).fetchall()
    ]
    before_equipment = [
        tuple(row)
        for row in conn.execute(
            "SELECT * FROM exercise_equipment_requirements ORDER BY id"
        ).fetchall()
    ]
    before_taxonomy = [
        tuple(row)
        for row in conn.execute(
            "SELECT * FROM exercise_catalog_taxonomy ORDER BY exercise_id"
        ).fetchall()
    ]
    conn.close()

    first = seed_exercise_form_media()
    second = seed_exercise_form_media()

    conn = database.get_connection()
    after_catalog = [
        tuple(row)
        for row in conn.execute(
            """
            SELECT id, name, exercise_type, movement_pattern,
                   primary_muscle_groups_json, difficulty, created_at, updated_at
            FROM exercise_catalog_exercises
            ORDER BY id
            """
        ).fetchall()
    ]
    after_equipment = [
        tuple(row)
        for row in conn.execute(
            "SELECT * FROM exercise_equipment_requirements ORDER BY id"
        ).fetchall()
    ]
    after_taxonomy = [
        tuple(row)
        for row in conn.execute(
            "SELECT * FROM exercise_catalog_taxonomy ORDER BY exercise_id"
        ).fetchall()
    ]
    conn.close()

    assert first == second
    assert _media_row_count() == len(seed_data.EXERCISE_FORM_MEDIA_SEEDS)
    assert after_catalog == before_catalog
    assert after_equipment == before_equipment
    assert after_taxonomy == before_taxonomy


def test_reseeding_replaces_removed_manifest_asset_without_stale_runtime_media(
    monkeypatch,
):
    initial_assets = _seed_media()
    removed_seed = seed_data.EXERCISE_FORM_MEDIA_SEEDS[-1]
    removed_asset = next(
        asset
        for asset in initial_assets
        if (
            asset.media_key == removed_seed.media_key
            and asset.asset_path == removed_seed.asset_path
        )
    )
    monkeypatch.setattr(
        seed_data,
        "EXERCISE_FORM_MEDIA_SEEDS",
        tuple(seed_data.EXERCISE_FORM_MEDIA_SEEDS[:-1]),
    )

    reseeded = seed_exercise_form_media()
    returned = get_exercise_form_media(removed_asset.catalog_exercise_id)

    assert len(reseeded) == len(seed_data.EXERCISE_FORM_MEDIA_SEEDS)
    assert _media_row_count() == len(seed_data.EXERCISE_FORM_MEDIA_SEEDS)
    assert removed_asset.asset_path not in {asset.asset_path for asset in returned}
    assert removed_asset.media_key not in {asset.media_key for asset in returned}


@pytest.mark.parametrize("kind", ("unknown", "duplicate_key", "duplicate_order"))
def test_invalid_seed_manifest_fails_before_any_media_write(monkeypatch, kind):
    database.initialize_database()
    seeds = list(seed_data.EXERCISE_FORM_MEDIA_SEEDS)
    if kind == "unknown":
        seeds[0] = replace(seeds[0], canonical_exercise_name="Unknown Exercise")
    elif kind == "duplicate_key":
        seeds.append(replace(seeds[1], media_key="start"))
    else:
        seeds.append(replace(seeds[1], sort_order=1))
    monkeypatch.setattr(seed_data, "EXERCISE_FORM_MEDIA_SEEDS", tuple(seeds))

    with pytest.raises(ValueError):
        seed_exercise_form_media()

    assert _media_row_count() == 0


def test_form_media_seed_requires_established_catalog_and_taxonomy_before_writes():
    database.initialize_database()

    with pytest.raises(ValueError, match="established complete catalog"):
        seed_exercise_form_media()

    assert _media_row_count() == 0

    catalog_service.seed_exercise_catalog()
    with pytest.raises(ValueError, match="established taxonomy"):
        seed_exercise_form_media()

    assert _media_row_count() == 0


def test_media_seed_rolls_back_atomically_on_unexpected_write_failure(monkeypatch):
    database.initialize_database()
    seed_exercise_taxonomy()
    original_upsert = catalog_service._upsert_exercise_form_media_row
    calls = 0

    def failing_upsert(cursor, asset):
        nonlocal calls
        calls += 1
        original_upsert(cursor, asset)
        if calls == 2:
            raise RuntimeError("simulated media seed failure")

    monkeypatch.setattr(
        catalog_service, "_upsert_exercise_form_media_row", failing_upsert
    )

    with pytest.raises(RuntimeError, match="simulated media seed failure"):
        seed_exercise_form_media()

    assert calls == 2
    assert _media_row_count() == 0


def test_media_replacement_failure_rolls_back_to_previous_complete_projection(
    monkeypatch,
):
    initial_assets = _seed_media()
    before = _media_rows()
    removed_seed = seed_data.EXERCISE_FORM_MEDIA_SEEDS[-1]
    removed_asset = next(
        asset
        for asset in initial_assets
        if (
            asset.media_key == removed_seed.media_key
            and asset.asset_path == removed_seed.asset_path
        )
    )
    monkeypatch.setattr(
        seed_data,
        "EXERCISE_FORM_MEDIA_SEEDS",
        tuple(seed_data.EXERCISE_FORM_MEDIA_SEEDS[:-1]),
    )
    original_upsert = catalog_service._upsert_exercise_form_media_row
    calls = 0

    def failing_upsert(cursor, asset):
        nonlocal calls
        calls += 1
        original_upsert(cursor, asset)
        if calls == 2:
            raise RuntimeError("simulated media replacement failure")

    monkeypatch.setattr(
        catalog_service, "_upsert_exercise_form_media_row", failing_upsert
    )

    with pytest.raises(RuntimeError, match="simulated media replacement failure"):
        seed_exercise_form_media()

    assert calls == 2
    assert _media_row_count() == len(before)
    assert _media_rows() == before
    assert removed_asset.asset_path in {
        asset.asset_path
        for asset in get_exercise_form_media(removed_asset.catalog_exercise_id)
    }


def test_form_media_tests_are_bound_to_pytest_owned_database(pytest_owned_database):
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"

    assert Path(database.DB_PATH).resolve() == pytest_owned_database.resolve()
    assert Path(database.DB_PATH).resolve() != canonical_db.resolve()
