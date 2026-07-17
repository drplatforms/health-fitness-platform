from __future__ import annotations

import pytest

import database
from services.exercise_catalog_service import seed_exercise_catalog
from services.workout_exercise_profile_service import (
    MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE,
    WorkoutExerciseProfileNotFoundError,
    WorkoutExerciseProfileValidationError,
    delete_workout_exercise_profile,
    ensure_workout_exercise_profile_table,
    get_workout_exercise_preference_map,
    resolve_workout_exercise_profiles,
    save_workout_exercise_profile,
)


def _seed_profile_test_db(tmp_path, monkeypatch) -> list[int]:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "workout_profile_test.db")
    database.initialize_database()
    conn = database.get_connection()
    conn.executemany(
        """
        INSERT OR IGNORE INTO users (id, name, starting_weight)
        VALUES (?, ?, ?)
        """,
        [
            (1, "Profile User", 180.0),
            (2, "Other Profile User", 175.0),
        ],
    )
    conn.commit()
    conn.close()
    seed_exercise_catalog()
    conn = database.get_connection()
    catalog_ids = [
        int(row["id"])
        for row in conn.execute(
            "SELECT id FROM exercise_catalog_exercises ORDER BY id LIMIT 3"
        ).fetchall()
    ]
    conn.close()
    return catalog_ids


def test_profile_crud_preserves_independent_dimensions(tmp_path, monkeypatch) -> None:
    catalog_id = _seed_profile_test_db(tmp_path, monkeypatch)[0]

    created = save_workout_exercise_profile(
        1,
        catalog_exercise_id=catalog_id,
        familiarity_state="learning",
        preference_state="favorite",
    )
    familiarity_only = save_workout_exercise_profile(
        1,
        catalog_exercise_id=catalog_id,
        familiarity_state="familiar",
        preference_state=None,
    )

    assert created is not None
    assert created.familiarity_state == "learning"
    assert created.preference_state == "favorite"
    assert familiarity_only is not None
    assert familiarity_only.profile_id == created.profile_id
    assert familiarity_only.familiarity_state == "familiar"
    assert familiarity_only.preference_state is None
    assert resolve_workout_exercise_profiles(1, [catalog_id])[0].profile == (
        familiarity_only
    )


def test_clearing_both_dimensions_deletes_the_profile(tmp_path, monkeypatch) -> None:
    catalog_id = _seed_profile_test_db(tmp_path, monkeypatch)[0]
    save_workout_exercise_profile(
        1,
        catalog_exercise_id=catalog_id,
        familiarity_state="unfamiliar",
        preference_state="disliked",
    )

    cleared = save_workout_exercise_profile(
        1,
        catalog_exercise_id=catalog_id,
        familiarity_state=None,
        preference_state=None,
    )

    assert cleared is None
    assert resolve_workout_exercise_profiles(1, [catalog_id])[0].profile is None
    assert delete_workout_exercise_profile(1, catalog_id) is False


def test_profile_identity_is_catalog_only_and_catalog_validated(
    tmp_path, monkeypatch
) -> None:
    _seed_profile_test_db(tmp_path, monkeypatch)

    with pytest.raises(WorkoutExerciseProfileValidationError):
        save_workout_exercise_profile(
            1,
            catalog_exercise_id=0,
            familiarity_state="familiar",
            preference_state=None,
        )
    with pytest.raises(WorkoutExerciseProfileNotFoundError):
        save_workout_exercise_profile(
            1,
            catalog_exercise_id=999999,
            familiarity_state="familiar",
            preference_state=None,
        )
    with pytest.raises(WorkoutExerciseProfileValidationError):
        save_workout_exercise_profile(
            1,
            catalog_exercise_id=1,
            familiarity_state="expert",
            preference_state=None,
        )
    with pytest.raises(WorkoutExerciseProfileValidationError):
        save_workout_exercise_profile(
            1,
            catalog_exercise_id=1,
            familiarity_state=None,
            preference_state="never_use",
        )


def test_profile_resolution_is_bounded_deduplicated_and_user_isolated(
    tmp_path, monkeypatch
) -> None:
    catalog_ids = _seed_profile_test_db(tmp_path, monkeypatch)
    saved = save_workout_exercise_profile(
        1,
        catalog_exercise_id=catalog_ids[0],
        familiarity_state="learning",
        preference_state="favorite",
    )

    resolutions = resolve_workout_exercise_profiles(
        1,
        [catalog_ids[0], catalog_ids[0], catalog_ids[1]],
    )

    assert [item.requested_catalog_exercise_id for item in resolutions] == (
        catalog_ids[:2]
    )
    assert resolutions[0].profile == saved
    assert resolutions[1].profile is None
    assert resolve_workout_exercise_profiles(2, [catalog_ids[0]])[0].profile is None
    with pytest.raises(WorkoutExerciseProfileValidationError):
        resolve_workout_exercise_profiles(
            1,
            [catalog_ids[0]] * (MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE + 1),
        )


def test_preference_map_is_read_only_and_ignores_familiarity(
    tmp_path, monkeypatch
) -> None:
    catalog_ids = _seed_profile_test_db(tmp_path, monkeypatch)

    assert get_workout_exercise_preference_map(1) == {}
    conn = database.get_connection()
    table_exists_before = conn.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'workout_exercise_profiles'
        """
    ).fetchone()
    conn.close()
    assert table_exists_before is None

    save_workout_exercise_profile(
        1,
        catalog_exercise_id=catalog_ids[0],
        familiarity_state="familiar",
        preference_state=None,
    )
    save_workout_exercise_profile(
        1,
        catalog_exercise_id=catalog_ids[1],
        familiarity_state="unfamiliar",
        preference_state="disliked",
    )

    assert get_workout_exercise_preference_map(1) == {catalog_ids[1]: "disliked"}
    assert get_workout_exercise_preference_map(2) == {}


def test_profile_table_ensure_is_idempotent(tmp_path, monkeypatch) -> None:
    _seed_profile_test_db(tmp_path, monkeypatch)

    ensure_workout_exercise_profile_table()
    ensure_workout_exercise_profile_table()

    conn = database.get_connection()
    count = conn.execute(
        """
        SELECT COUNT(*) AS count FROM sqlite_master
        WHERE type = 'table' AND name = 'workout_exercise_profiles'
        """
    ).fetchone()["count"]
    conn.close()
    assert count == 1
