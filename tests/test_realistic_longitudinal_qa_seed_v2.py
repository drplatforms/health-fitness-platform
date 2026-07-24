from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from statistics import median

import pytest

import database
import scripts.seed_realistic_longitudinal_qa_v2 as seed_module
from scripts.seed_realistic_longitudinal_qa_v2 import (
    CANONICAL_DATABASE_PATH,
    HISTORY_END,
    HISTORY_START,
    MANIFEST_FINALIZATION_EXIT_CODE,
    PERSONA_BY_ID,
    QA_USER_IDS,
    SEED_MARKER,
    SEED_VERSION,
    ManifestFinalizationError,
    build_seed_dataset,
    run_realistic_longitudinal_qa_seed_v2,
)
from scripts.seed_realistic_longitudinal_qa_v2 import (
    main as seed_main,
)
from scripts.seed_workout_performance_studio_qa import (
    _ensure_compatibility_food_mirrors,
)
from services.coaching_decision_service import build_coaching_decision
from services.exercise_catalog_service import (
    seed_exercise_catalog,
    seed_exercise_prescription_measurements,
)
from services.food_normalization_service import ensure_starter_canonical_foods_seeded
from services.longitudinal_insight_service import build_longitudinal_insight_feed
from services.nutrition_target_vs_actual_service import (
    build_formula_derived_nutrition_targets,
    build_target_vs_actual_nutrition_summary,
)
from services.nutrition_trend_service import build_nutrition_trend_window
from services.recovery_intelligence_service import build_recovery_intelligence
from services.training_execution_summary_service import (
    build_training_execution_summary,
)
from services.user_state_service import build_user_health_state
from services.workout_exercise_history_analytics_service import (
    build_workout_exercise_history_analytics,
    build_workout_exercise_history_session_detail,
)
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)

EXPECTED_PERSONA_COUNTS = {
    106: {
        "daily_checkins": 136,
        "food_entries": 830,
        "user_equipment_profiles": 1,
        "workout_plan_instances": 87,
        "workout_execution_sessions": 87,
        "workout_sessions": 87,
        "planned_workout_exercises": 174,
        "workout_execution_set_actuals": 494,
        "workout_sets": 430,
    },
    107: {
        "daily_checkins": 80,
        "food_entries": 330,
        "user_equipment_profiles": 1,
        "workout_plan_instances": 42,
        "workout_execution_sessions": 42,
        "workout_sessions": 42,
        "planned_workout_exercises": 84,
        "workout_execution_set_actuals": 236,
        "workout_sets": 228,
    },
    108: {
        "daily_checkins": 139,
        "food_entries": 1014,
        "user_equipment_profiles": 1,
        "workout_plan_instances": 114,
        "workout_execution_sessions": 114,
        "workout_sessions": 114,
        "planned_workout_exercises": 182,
        "workout_execution_set_actuals": 474,
        "workout_sets": 317,
    },
}
EXPECTED_LATEST_ACTIVITY = {
    106: "2026-07-22",
    107: "2026-07-19",
    108: "2026-07-23",
}
EXPECTED_PARTIAL_COUNTS = {
    106: {"partial_sessions": 13, "skipped_sets": 7, "missing_rir": 24},
    107: {"partial_sessions": 16, "skipped_sets": 8, "missing_rir": 13},
    108: {"partial_sessions": 21, "skipped_sets": 11, "missing_rir": 21},
}
EXPECTED_NUTRITION_DAYS = {
    106: {"complete": 112, "partial": 8, "logged": 120, "no_log": 48},
    107: {"complete": 41, "partial": 24, "logged": 65, "no_log": 100},
    108: {"complete": 137, "partial": 8, "logged": 145, "no_log": 24},
}
EXPECTED_LEGACY_QA106_NAME = "Performance Studio Demo"
EXPECTED_LEGACY_QA106_SCENARIO = "workout_performance_studio_qa_v1"


def _prepare_database(path: Path) -> None:
    database.DB_PATH = path
    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    ensure_starter_canonical_foods_seeded()
    seed_exercise_catalog()
    seed_exercise_prescription_measurements()
    conn = database.get_connection()
    try:
        with conn:
            _ensure_compatibility_food_mirrors(conn)
    finally:
        conn.close()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _count(
    path: Path,
    sql: str,
    params: tuple[object, ...] = (),
) -> int:
    conn = _connect(path)
    try:
        return int(conn.execute(sql, params).fetchone()[0])
    finally:
        conn.close()


def _copy_database(source: Path, destination: Path) -> Path:
    shutil.copy2(source, destination)
    return destination


def _staged_manifests(final_path: Path) -> list[Path]:
    return list(final_path.parent.glob(f".{final_path.name}.*.staged"))


def _reference_catalog_snapshot(path: Path) -> dict[str, list[tuple]]:
    table_names = (
        "canonical_foods",
        "canonical_food_nutrients",
        "foods",
        "nutrients",
        "food_nutrients",
        "exercise_catalog_exercises",
        "exercise_catalog_prescription_measurements",
        "exercises",
    )
    conn = _connect(path)
    try:
        return {
            table_name: sorted(
                (
                    tuple(row)
                    for row in conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
                ),
                key=repr,
            )
            for table_name in table_names
        }
    finally:
        conn.close()


@pytest.fixture(scope="module")
def seeded_v2(tmp_path_factory):
    original_path = database.DB_PATH
    path = tmp_path_factory.mktemp("realistic_longitudinal_v2") / "seeded.db"
    _prepare_database(path)
    result = run_realistic_longitudinal_qa_seed_v2(
        database_path=path,
        apply=True,
        confirm_user_ids="106,107,108",
    )
    database.DB_PATH = path
    try:
        yield path, result
    finally:
        database.DB_PATH = original_path


def test_dry_run_is_non_mutating_and_refuses_invalid_paths_and_dates(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    path = tmp_path / "dry-run.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    before_hash = _sha256(path)
    manifest_path = tmp_path / "dry-run.json"

    result = run_realistic_longitudinal_qa_seed_v2(
        database_path=path,
        manifest_path=manifest_path,
    )

    assert result.mode == "dry_run"
    assert result.proposed_operation == "create 106,107,108"
    assert _sha256(path) == before_hash
    assert (
        _count(
            path,
            "SELECT COUNT(*) FROM users WHERE id IN (106, 107, 108)",
        )
        == 0
    )
    written_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written_manifest["seed"] == result.manifest["seed"]
    assert written_manifest["run"]["mode"] == "dry_run"

    assert seed_main(["--database", str(path)]) == 0
    cli_output = capsys.readouterr().out
    assert f"Database: {path.resolve()}" in cli_output
    assert "Mode: dry_run" in cli_output
    assert "Proposed operation: create 106,107,108" in cli_output
    assert "Dry run complete; database writes: 0." in cli_output
    assert _sha256(path) == before_hash

    with pytest.raises(FileNotFoundError, match="does not exist"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=tmp_path / "typo.db",
        )
    with pytest.raises(ValueError, match="requires --end-date"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            end_date=HISTORY_END.replace(day=22),
        )


def test_apply_requires_exact_confirmation_and_rolls_back_injected_failure(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "rollback.db"
    manifest_path = tmp_path / "rollback.json"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)

    with pytest.raises(ValueError, match="Apply requires"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
        )
    with pytest.raises(ValueError, match="must be exactly"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107",
        )

    def fail_after_second_user(stage: str) -> None:
        if stage == "after_user_107":
            raise RuntimeError("injected seed failure")

    with pytest.raises(RuntimeError, match="injected seed failure"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107,108",
            manifest_path=manifest_path,
            _failure_hook=fail_after_second_user,
        )

    assert (
        _count(
            path,
            "SELECT COUNT(*) FROM users WHERE id IN (106, 107, 108)",
        )
        == 0
    )
    assert (
        _count(
            path,
            "SELECT COUNT(*) FROM workout_plan_instances "
            "WHERE user_id IN (106, 107, 108)",
        )
        == 0
    )
    assert not manifest_path.exists()
    assert _staged_manifests(manifest_path) == []


def test_canonical_guard_is_repo_anchored_and_requires_two_acknowledgements(
    tmp_path,
    monkeypatch,
) -> None:
    canonical_path = tmp_path / "canonical" / "fitness_ai.db"
    canonical_path.parent.mkdir()
    _prepare_database(canonical_path)
    other_path = tmp_path / "other" / "fitness_ai.db"
    other_path.parent.mkdir()
    _prepare_database(other_path)

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "misleading.db")
    assert (
        CANONICAL_DATABASE_PATH
        == (Path(seed_module.__file__).resolve().parents[1] / "fitness_ai.db").resolve()
    )
    before_hash = _sha256(canonical_path)

    dry_run = run_realistic_longitudinal_qa_seed_v2(
        database_path=canonical_path,
        _canonical_database_path=canonical_path,
    )
    assert dry_run.canonical_database is True
    assert dry_run.canonical_apply_authorized is False
    assert _sha256(canonical_path) == before_hash

    acknowledgement_cases = (
        {},
        {"allow_canonical_database": True},
        {"confirm_canonical_path": str(canonical_path.resolve())},
        {
            "allow_canonical_database": True,
            "confirm_canonical_path": str(canonical_path.resolve()).upper(),
        },
    )
    for acknowledgements in acknowledgement_cases:
        with pytest.raises(ValueError, match="canonical database|exactly match"):
            run_realistic_longitudinal_qa_seed_v2(
                database_path=canonical_path,
                apply=True,
                confirm_user_ids="106,107,108",
                _canonical_database_path=canonical_path,
                **acknowledgements,
            )
        assert _sha256(canonical_path) == before_hash

    same_name_elsewhere = run_realistic_longitudinal_qa_seed_v2(
        database_path=other_path,
        apply=True,
        confirm_user_ids="106,107,108",
        _canonical_database_path=canonical_path,
    )
    assert same_name_elsewhere.canonical_database is False
    assert same_name_elsewhere.canonical_apply_authorized is False
    assert _sha256(canonical_path) == before_hash

    authorized = run_realistic_longitudinal_qa_seed_v2(
        database_path=canonical_path,
        apply=True,
        confirm_user_ids="106,107,108",
        allow_canonical_database=True,
        confirm_canonical_path=str(canonical_path.resolve()),
        _canonical_database_path=canonical_path,
    )
    assert authorized.canonical_database is True
    assert authorized.canonical_apply_authorized is True
    assert authorized.database_committed is True


def test_canonical_guard_rejects_hardlink_alias_without_acknowledgements(
    tmp_path,
) -> None:
    canonical_path = tmp_path / "canonical.db"
    alias_path = tmp_path / "canonical-alias.db"
    _prepare_database(canonical_path)
    try:
        os.link(canonical_path, alias_path)
    except OSError as exc:
        pytest.skip(f"hard links are unavailable on this filesystem: {exc}")

    before_hash = _sha256(canonical_path)
    with pytest.raises(ValueError, match="canonical database"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=alias_path,
            apply=True,
            confirm_user_ids="106,107,108",
            _canonical_database_path=canonical_path,
        )
    assert os.path.samefile(canonical_path, alias_path)
    assert _sha256(canonical_path) == before_hash


def test_canonical_cli_requires_exact_path_and_prints_prominent_warning(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    canonical_path = tmp_path / "redirected-canonical.db"
    _prepare_database(canonical_path)
    resolved_canonical = canonical_path.resolve()
    monkeypatch.setattr(
        seed_module,
        "CANONICAL_DATABASE_PATH",
        resolved_canonical,
    )

    exit_code = seed_main(
        [
            "--database",
            str(canonical_path),
            "--apply",
            "--confirm-user-ids",
            "106,107,108",
            "--allow-canonical-database",
            "--confirm-canonical-path",
            str(resolved_canonical),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "WARNING: CANONICAL DATABASE APPLY AUTHORIZED" in captured.err
    assert str(resolved_canonical) in captured.err


def test_manifest_staging_precedes_mutation_and_publishes_atomically(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "manifest-success.db"
    manifest_path = tmp_path / "manifest-success.json"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)

    result = run_realistic_longitudinal_qa_seed_v2(
        database_path=path,
        apply=True,
        confirm_user_ids="106,107,108",
        manifest_path=manifest_path,
    )

    assert result.database_committed is True
    assert result.manifest_path == manifest_path.resolve()
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == result.manifest
    assert _staged_manifests(manifest_path) == []


def test_manifest_staging_failures_cannot_mutate_database(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "manifest-preflight.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    before_hash = _sha256(path)

    with pytest.raises(ValueError, match="directory"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107,108",
            manifest_path=tmp_path,
        )
    assert _sha256(path) == before_hash

    missing_parent_manifest = tmp_path / "missing" / "manifest.json"
    with pytest.raises(FileNotFoundError, match="must already exist"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107,108",
            manifest_path=missing_parent_manifest,
        )
    assert _sha256(path) == before_hash
    assert not missing_parent_manifest.parent.exists()


def test_manifest_postcommit_failure_preserves_recoverable_stage_and_exit_code(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    path = tmp_path / "manifest-postcommit.db"
    manifest_path = tmp_path / "manifest-postcommit.json"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)

    def fail_atomic_publish(_source, _destination) -> None:
        raise OSError("injected atomic publish failure")

    monkeypatch.setattr(seed_module.os, "replace", fail_atomic_publish)
    with pytest.raises(ManifestFinalizationError) as error:
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107,108",
            manifest_path=manifest_path,
        )

    assert error.value.database_committed is True
    assert error.value.exit_code == MANIFEST_FINALIZATION_EXIT_CODE
    assert error.value.final_path == manifest_path.resolve()
    assert error.value.staged_path.exists()
    assert not manifest_path.exists()
    assert _count(path, "SELECT COUNT(*) FROM users WHERE id IN (106, 107, 108)") == 3

    cli_path = tmp_path / "manifest-cli.db"
    cli_manifest = tmp_path / "manifest-cli.json"
    _prepare_database(cli_path)
    exit_code = seed_main(
        [
            "--database",
            str(cli_path),
            "--apply",
            "--confirm-user-ids",
            "106,107,108",
            "--manifest",
            str(cli_manifest),
        ]
    )
    assert exit_code == MANIFEST_FINALIZATION_EXIT_CODE
    assert (
        _count(
            cli_path,
            "SELECT COUNT(*) FROM users WHERE id IN (106, 107, 108)",
        )
        == 3
    )
    assert not cli_manifest.exists()
    assert len(_staged_manifests(cli_manifest)) == 1
    assert "DATABASE COMMITTED; MANIFEST FINALIZATION FAILED" in capsys.readouterr().err


def test_v2_apply_does_not_mutate_global_food_or_exercise_catalogs(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "reference-catalogs.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    before = _reference_catalog_snapshot(path)

    run_realistic_longitudinal_qa_seed_v2(
        database_path=path,
        apply=True,
        confirm_user_ids="106,107,108",
    )

    assert _reference_catalog_snapshot(path) == before


def test_clean_creation_has_fixed_boundaries_realistic_training_and_dual_persistence(
    seeded_v2,
) -> None:
    path, result = seeded_v2
    seed = result.manifest["seed"]

    assert seed["version"] == SEED_VERSION
    assert seed["history_start"] == "2026-02-05"
    assert seed["history_end"] == "2026-07-23"
    assert seed["elapsed_days"] == 168
    assert [
        (persona["id"], persona["latest_activity"]) for persona in seed["personas"]
    ] == [
        (106, "2026-07-22"),
        (107, "2026-07-19"),
        (108, "2026-07-23"),
    ]

    conn = _connect(path)
    try:
        users = conn.execute(
            """
            SELECT id, name
            FROM users
            WHERE id IN (106, 107, 108)
            ORDER BY id
            """
        ).fetchall()
        assert [(int(row["id"]), str(row["name"])) for row in users] == [
            (user_id, PERSONA_BY_ID[user_id].name) for user_id in QA_USER_IDS
        ]

        direct_count_queries = {
            "daily_checkins": "SELECT COUNT(*) FROM daily_checkins WHERE user_id = ?",
            "food_entries": "SELECT COUNT(*) FROM food_entries WHERE user_id = ?",
            "user_equipment_profiles": (
                "SELECT COUNT(*) FROM user_equipment_profiles WHERE user_id = ?"
            ),
            "workout_plan_instances": (
                "SELECT COUNT(*) FROM workout_plan_instances WHERE user_id = ?"
            ),
            "workout_execution_sessions": (
                "SELECT COUNT(*) FROM workout_execution_sessions WHERE user_id = ?"
            ),
            "workout_sessions": (
                "SELECT COUNT(*) FROM workout_sessions WHERE user_id = ?"
            ),
        }
        indirect_count_queries = {
            "planned_workout_exercises": """
                SELECT COUNT(*)
                FROM planned_workout_exercises AS planned
                JOIN workout_plan_instances AS plan
                  ON plan.id = planned.workout_plan_instance_id
                WHERE plan.user_id = ?
            """,
            "workout_execution_set_actuals": """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id = ?
            """,
            "workout_sets": """
                SELECT COUNT(*)
                FROM workout_sets AS workout_set
                JOIN workout_sessions AS session
                  ON session.id = workout_set.workout_session_id
                WHERE session.user_id = ?
            """,
        }
        manifests_by_id = {int(persona["id"]): persona for persona in seed["personas"]}
        for user_id, expected_counts in EXPECTED_PERSONA_COUNTS.items():
            stored_counts = {
                label: int(conn.execute(sql, (user_id,)).fetchone()[0])
                for label, sql in {
                    **direct_count_queries,
                    **indirect_count_queries,
                }.items()
            }
            assert stored_counts == expected_counts
            assert manifests_by_id[user_id]["row_counts"] == expected_counts

        contradictory = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                  AND actual.completed = 1
                  AND actual.skipped = 1
                """
            ).fetchone()[0]
        )
        duplicate_set_numbers = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT
                        actual.workout_execution_session_id,
                        actual.planned_workout_exercise_id,
                        actual.set_number
                    FROM workout_execution_set_actuals AS actual
                    JOIN workout_execution_sessions AS execution
                      ON execution.id = actual.workout_execution_session_id
                    WHERE execution.user_id IN (106, 107, 108)
                    GROUP BY
                        actual.workout_execution_session_id,
                        actual.planned_workout_exercise_id,
                        actual.set_number
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]
        )
        skipped = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                  AND actual.completed = 0
                  AND actual.skipped = 1
                """
            ).fetchone()[0]
        )
        missing_rir = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                  AND actual.measurement_type = 'reps'
                  AND actual.completed = 1
                  AND actual.actual_rir IS NULL
                """
            ).fetchone()[0]
        )
        planned_set_total = int(
            conn.execute(
                """
                SELECT COALESCE(SUM(planned.sets), 0)
                FROM planned_workout_exercises AS planned
                JOIN workout_plan_instances AS plan
                  ON plan.id = planned.workout_plan_instance_id
                WHERE plan.user_id IN (106, 107, 108)
                """
            ).fetchone()[0]
        )
        actual_row_total = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                """
            ).fetchone()[0]
        )
        assert contradictory == 0
        assert duplicate_set_numbers == 0
        assert skipped > 0
        assert missing_rir > 0
        assert planned_set_total > actual_row_total

        measurement_types = {
            str(row[0])
            for row in conn.execute(
                """
                SELECT DISTINCT actual.measurement_type
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                """
            ).fetchall()
        }
        assert measurement_types == {"reps", "duration", "distance"}

        assert (
            int(
                conn.execute(
                    """
                SELECT COUNT(*)
                FROM workout_execution_sessions
                WHERE user_id IN (106, 107, 108)
                  AND workout_session_id IS NULL
                """
                ).fetchone()[0]
            )
            == 0
        )
        assert (
            int(
                conn.execute(
                    """
                SELECT COUNT(*)
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                  AND actual.measurement_type = 'reps'
                  AND actual.completed = 1
                  AND actual.workout_set_id IS NULL
                """
                ).fetchone()[0]
            )
            == 0
        )

        weights = [
            float(row[0])
            for row in conn.execute(
                """
                SELECT actual.actual_weight
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                  AND actual.actual_weight IS NOT NULL
                """
            ).fetchall()
        ]
        assert weights
        assert all(round(weight * 2) % 5 == 0 for weight in weights)

        recovery_nulls = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM daily_checkins
                WHERE user_id IN (106, 107, 108)
                  AND (
                    sleep_hours IS NULL
                    OR energy_level IS NULL
                    OR soreness_level IS NULL
                  )
                """
            ).fetchone()[0]
        )
        assert recovery_nulls == 0

        snapshot_nulls = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM food_entries
                WHERE user_id IN (106, 107, 108)
                  AND (
                    canonical_food_id IS NULL
                    OR calories IS NULL
                    OR protein_g IS NULL
                    OR carbs_g IS NULL
                    OR fat_g IS NULL
                  )
                """
            ).fetchone()[0]
        )
        assert snapshot_nulls == 0
    finally:
        conn.close()

    for persona in seed["personas"]:
        assert persona["training"]["partial_session_count"] > 0
        assert persona["training"]["explicit_skipped_set_count"] > 0
        assert persona["training"]["missing_rir_count"] > 0
        assert persona["nutrition"]["complete_days"] > 0
        assert persona["nutrition"]["partial_days"] > 0
        assert persona["nutrition"]["no_log_days"] > 0
        assert persona["recovery"]["omitted_days"] > 0
        assert len(persona["phase_windows"]) == 5


def test_stored_contract_has_independent_counts_dates_gaps_and_phase_anchors(
    seeded_v2,
) -> None:
    path, result = seeded_v2
    manifest_by_id = {
        int(persona["id"]): persona for persona in result.manifest["seed"]["personas"]
    }
    conn = _connect(path)
    try:
        for user_id in QA_USER_IDS:
            activity_bounds = conn.execute(
                """
                WITH activity_dates AS (
                    SELECT checkin_date AS activity_date
                    FROM daily_checkins
                    WHERE user_id = ?
                    UNION ALL
                    SELECT entry_date
                    FROM food_entries
                    WHERE user_id = ?
                    UNION ALL
                    SELECT substr(selected_at, 1, 10)
                    FROM workout_plan_instances
                    WHERE user_id = ?
                )
                SELECT MIN(activity_date), MAX(activity_date)
                FROM activity_dates
                """,
                (user_id, user_id, user_id),
            ).fetchone()
            assert tuple(activity_bounds) == (
                "2026-02-05",
                EXPECTED_LATEST_ACTIVITY[user_id],
            )
            assert (
                manifest_by_id[user_id]["latest_activity"]
                == EXPECTED_LATEST_ACTIVITY[user_id]
            )

        interruption = conn.execute(
            """
            SELECT COUNT(*),
                   MAX(CASE WHEN workout_date < '2026-05-04' THEN workout_date END),
                   MIN(CASE WHEN workout_date > '2026-05-24' THEN workout_date END)
            FROM workout_sessions
            WHERE user_id = 107
              AND (
                workout_date BETWEEN '2026-05-04' AND '2026-05-24'
                OR workout_date < '2026-05-04'
                OR workout_date > '2026-05-24'
              )
            """
        ).fetchone()
        gap_workout_count = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM workout_sessions
                WHERE user_id = 107
                  AND workout_date BETWEEN '2026-05-04' AND '2026-05-24'
                """
            ).fetchone()[0]
        )
        assert gap_workout_count == 0
        assert tuple(interruption)[1:] == ("2026-04-30", "2026-05-26")

        def actual_values(
            user_id: int,
            workout_date: str,
            exercise_name: str,
            column: str,
        ) -> tuple[float | int | None, ...]:
            allowed_columns = {
                "actual_weight",
                "actual_reps",
                "actual_duration_seconds",
                "actual_distance_meters",
            }
            assert column in allowed_columns
            rows = conn.execute(
                f"""
                SELECT actual.{column}
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                JOIN workout_plan_instances AS plan
                  ON plan.id = execution.workout_plan_instance_id
                WHERE plan.user_id = ?
                  AND substr(plan.selected_at, 1, 10) = ?
                  AND actual.exercise_name = ?
                ORDER BY actual.set_number, actual.id
                """,
                (user_id, workout_date, exercise_name),
            ).fetchall()
            return tuple(row[0] for row in rows)

        assert actual_values(
            106,
            "2026-05-29",
            "Dumbbell Bench Press",
            "actual_weight",
        ) == (65.0, 65.0, 65.0)
        assert actual_values(
            106,
            "2026-06-12",
            "Dumbbell Bench Press",
            "actual_weight",
        ) == (50.0, 50.0)
        assert actual_values(
            106,
            "2026-07-03",
            "Dumbbell Bench Press",
            "actual_weight",
        ) == (62.5, 62.5, 62.5)

        assert actual_values(
            107,
            "2026-02-10",
            "Dumbbell Bench Press",
            "actual_weight",
        ) == (35.0, 35.0, 35.0)
        assert actual_values(
            107,
            "2026-03-24",
            "Dumbbell Bench Press",
            "actual_weight",
        ) == (50.0, 50.0, 50.0)
        assert actual_values(
            107,
            "2026-07-14",
            "Dumbbell Bench Press",
            "actual_weight",
        ) == (50.0, 50.0, 50.0)

        assert actual_values(
            108,
            "2026-02-05",
            "Plank",
            "actual_duration_seconds",
        ) == (35, 40, 35)
        assert actual_values(
            108,
            "2026-07-03",
            "Farmer Carry",
            "actual_distance_meters",
        ) == (45.0, 45.0, 50.0)
        assert actual_values(
            108,
            "2026-07-03",
            "Farmer Carry",
            "actual_weight",
        ) == (60.0, 60.0, 60.0)
        assert actual_values(
            108,
            "2026-06-16",
            "Treadmill Walk",
            "actual_duration_seconds",
        ) == (900,)
        assert actual_values(
            108,
            "2026-07-19",
            "Romanian Deadlift",
            "actual_weight",
        ) == (80.0, 80.0, 80.0)

        measurement_types = {
            str(row[0])
            for row in conn.execute(
                """
                SELECT DISTINCT actual.measurement_type
                FROM workout_execution_set_actuals AS actual
                JOIN workout_execution_sessions AS execution
                  ON execution.id = actual.workout_execution_session_id
                WHERE execution.user_id IN (106, 107, 108)
                """
            ).fetchall()
        }
        assert measurement_types == {"reps", "duration", "distance"}

        for user_id, expected in EXPECTED_PARTIAL_COUNTS.items():
            partial_sessions = int(
                conn.execute(
                    """
                    WITH planned AS (
                        SELECT plan.id AS plan_id,
                               SUM(planned.sets) AS planned_sets
                        FROM workout_plan_instances AS plan
                        JOIN planned_workout_exercises AS planned
                          ON planned.workout_plan_instance_id = plan.id
                        WHERE plan.user_id = ?
                        GROUP BY plan.id
                    ),
                    completed AS (
                        SELECT execution.workout_plan_instance_id AS plan_id,
                               SUM(actual.completed) AS completed_sets
                        FROM workout_execution_sessions AS execution
                        JOIN workout_execution_set_actuals AS actual
                          ON actual.workout_execution_session_id = execution.id
                        WHERE execution.user_id = ?
                        GROUP BY execution.workout_plan_instance_id
                    )
                    SELECT COUNT(*)
                    FROM planned
                    LEFT JOIN completed USING (plan_id)
                    WHERE COALESCE(completed.completed_sets, 0) < planned.planned_sets
                    """,
                    (user_id, user_id),
                ).fetchone()[0]
            )
            skipped_sets = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM workout_execution_set_actuals AS actual
                    JOIN workout_execution_sessions AS execution
                      ON execution.id = actual.workout_execution_session_id
                    WHERE execution.user_id = ?
                      AND actual.completed = 0
                      AND actual.skipped = 1
                    """,
                    (user_id,),
                ).fetchone()[0]
            )
            missing_rir = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM workout_execution_set_actuals AS actual
                    JOIN workout_execution_sessions AS execution
                      ON execution.id = actual.workout_execution_session_id
                    WHERE execution.user_id = ?
                      AND actual.measurement_type = 'reps'
                      AND actual.completed = 1
                      AND actual.actual_rir IS NULL
                    """,
                    (user_id,),
                ).fetchone()[0]
            )
            assert {
                "partial_sessions": partial_sessions,
                "skipped_sets": skipped_sets,
                "missing_rir": missing_rir,
            } == expected
            assert (
                manifest_by_id[user_id]["training"]["partial_session_count"]
                == (expected["partial_sessions"])
            )
            assert (
                manifest_by_id[user_id]["training"]["explicit_skipped_set_count"]
                == expected["skipped_sets"]
            )
            assert (
                manifest_by_id[user_id]["training"]["missing_rir_count"]
                == (expected["missing_rir"])
            )

        unlogged_set_groups = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT planned.id
                    FROM planned_workout_exercises AS planned
                    JOIN workout_plan_instances AS plan
                      ON plan.id = planned.workout_plan_instance_id
                    LEFT JOIN workout_execution_set_actuals AS actual
                      ON actual.planned_workout_exercise_id = planned.id
                    WHERE plan.user_id IN (106, 107, 108)
                    GROUP BY planned.id
                    HAVING COUNT(actual.id) < planned.sets
                       AND COALESCE(SUM(actual.skipped), 0) = 0
                )
                """
            ).fetchone()[0]
        )
        assert unlogged_set_groups > 0

        recovery_gap_count = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM daily_checkins
                WHERE user_id = 107
                  AND checkin_date BETWEEN '2026-05-04' AND '2026-05-24'
                """
            ).fetchone()[0]
        )
        nutrition_gap_days = int(
            conn.execute(
                """
                SELECT COUNT(DISTINCT entry_date)
                FROM food_entries
                WHERE user_id = 107
                  AND entry_date BETWEEN '2026-05-04' AND '2026-05-24'
                """
            ).fetchone()[0]
        )
        complete_gap_days = int(
            conn.execute(
                """
                SELECT COUNT(DISTINCT entry_date)
                FROM food_entries
                WHERE user_id = 107
                  AND entry_date BETWEEN '2026-05-04' AND '2026-05-24'
                  AND notes LIKE '%day=complete.%'
                """
            ).fetchone()[0]
        )
        assert (recovery_gap_count, nutrition_gap_days, complete_gap_days) == (
            6,
            3,
            0,
        )
        assert (
            conn.execute(
                """
                SELECT SUM(calories)
                FROM food_entries
                WHERE user_id = 107 AND entry_date = '2026-05-05'
                """
            ).fetchone()[0]
            is None
        )
    finally:
        conn.close()


def test_stored_nutrition_is_varied_phase_aware_and_formula_coherent(
    seeded_v2,
    monkeypatch,
) -> None:
    path, result = seeded_v2
    monkeypatch.setattr(database, "DB_PATH", path)
    conn = _connect(path)
    try:
        rows = conn.execute(
            """
            SELECT user_id,
                   entry_date,
                   food_name_snapshot,
                   grams,
                   meal_type,
                   notes,
                   calories,
                   protein_g,
                   carbs_g,
                   fat_g
            FROM food_entries
            WHERE user_id IN (106, 107, 108)
            ORDER BY user_id, entry_date, created_at, id
            """
        ).fetchall()
        workout_dates = {
            (int(row["user_id"]), str(row["workout_date"]))
            for row in conn.execute(
                """
                SELECT user_id, workout_date
                FROM workout_sessions
                WHERE user_id IN (106, 107, 108)
                """
            ).fetchall()
        }
        first_last_weights: dict[int, tuple[float, float]] = {}
        for user_id in QA_USER_IDS:
            weight_rows = conn.execute(
                """
                SELECT body_weight
                FROM daily_checkins
                WHERE user_id = ?
                  AND body_weight IS NOT NULL
                ORDER BY checkin_date
                """,
                (user_id,),
            ).fetchall()
            first_last_weights[user_id] = (
                float(weight_rows[0][0]),
                float(weight_rows[-1][0]),
            )
    finally:
        conn.close()

    daily_rows: dict[tuple[int, str], list[sqlite3.Row]] = {}
    for row in rows:
        daily_rows.setdefault(
            (int(row["user_id"]), str(row["entry_date"])),
            [],
        ).append(row)

    complete_calories: dict[int, list[tuple[str, float]]] = {
        user_id: [] for user_id in QA_USER_IDS
    }
    complete_signatures: dict[int, set[tuple[tuple[object, ...], ...]]] = {
        user_id: set() for user_id in QA_USER_IDS
    }
    stored_day_counts: dict[int, dict[str, int]] = {}
    for user_id in QA_USER_IDS:
        user_days = {
            day: entries
            for (stored_user_id, day), entries in daily_rows.items()
            if stored_user_id == user_id
        }
        complete_days = {
            day: entries
            for day, entries in user_days.items()
            if all("day=complete." in str(row["notes"]) for row in entries)
        }
        partial_days = {
            day: entries
            for day, entries in user_days.items()
            if all("day=partial." in str(row["notes"]) for row in entries)
        }
        for day, entries in complete_days.items():
            calories = sum(float(row["calories"]) for row in entries)
            complete_calories[user_id].append((day, calories))
            complete_signatures[user_id].add(
                tuple(
                    (
                        str(row["food_name_snapshot"]),
                        float(row["grams"]),
                        str(row["meal_type"]),
                    )
                    for row in entries
                )
            )
        history_days = (
            date.fromisoformat(EXPECTED_LATEST_ACTIVITY[user_id]) - HISTORY_START
        ).days + 1
        stored_day_counts[user_id] = {
            "complete": len(complete_days),
            "partial": len(partial_days),
            "logged": len(user_days),
            "no_log": history_days - len(user_days),
        }
        assert stored_day_counts[user_id] == EXPECTED_NUTRITION_DAYS[user_id]

    assert {
        user_id: len(signatures) for user_id, signatures in complete_signatures.items()
    } == {106: 21, 107: 12, 108: 12}
    assert len({round(value, 3) for _day, value in complete_calories[106]}) > 6

    qa106_median = median(value for _day, value in complete_calories[106])
    targets, _approved = build_formula_derived_nutrition_targets(
        build_user_health_state(106),
        calculation_date=EXPECTED_LATEST_ACTIVITY[106],
    )
    assert targets.calorie_target_min is not None
    assert targets.calorie_target_max is not None
    target_midpoint = (targets.calorie_target_min + targets.calorie_target_max) / 2.0
    assert 2650.0 <= qa106_median <= 2750.0
    assert abs(qa106_median - target_midpoint) / target_midpoint <= 0.10
    assert first_last_weights[106] == pytest.approx((181.8, 184.1))

    qa107_partial_entry_counts = [
        len(entries)
        for (user_id, _day), entries in daily_rows.items()
        if user_id == 107
        and all("day=partial." in str(row["notes"]) for row in entries)
    ]
    assert qa107_partial_entry_counts == [1] * 24
    assert stored_day_counts[107]["no_log"] == 100

    qa108_training_calories = [
        value for day, value in complete_calories[108] if (108, day) in workout_dates
    ]
    qa108_rest_calories = [
        value
        for day, value in complete_calories[108]
        if (108, day) not in workout_dates
    ]
    assert median(qa108_training_calories) > median(qa108_rest_calories) + 200.0

    manifest_by_id = {
        int(persona["id"]): persona for persona in result.manifest["seed"]["personas"]
    }
    for user_id in QA_USER_IDS:
        nutrition_manifest = manifest_by_id[user_id]["nutrition"]
        assert (
            nutrition_manifest["complete_days"]
            == stored_day_counts[user_id]["complete"]
        )
        assert (
            nutrition_manifest["partial_days"] == stored_day_counts[user_id]["partial"]
        )
        assert nutrition_manifest["no_log_days"] == stored_day_counts[user_id]["no_log"]
        assert nutrition_manifest["complete_menu_signature_count"] == len(
            complete_signatures[user_id]
        )


def test_missing_canonical_nutrient_is_rejected_instead_of_zero_filled(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "missing-nutrient.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    conn = _connect(path)
    try:
        with conn:
            deleted = conn.execute(
                """
                DELETE FROM canonical_food_nutrients
                WHERE canonical_food_id = (
                    SELECT id
                    FROM canonical_foods
                    WHERE display_name = 'Banana'
                )
                  AND nutrient_name = 'Fat'
                """
            ).rowcount
    finally:
        conn.close()
    assert deleted == 1
    before_hash = _sha256(path)

    with pytest.raises(RuntimeError, match="missing nutrient snapshots: Fat"):
        run_realistic_longitudinal_qa_seed_v2(database_path=path)

    assert _sha256(path) == before_hash
    assert (
        _count(
            path,
            "SELECT COUNT(*) FROM users WHERE id IN (106, 107, 108)",
        )
        == 0
    )


def test_excluded_domains_remain_empty_for_v2_users(seeded_v2) -> None:
    path, _result = seeded_v2
    allowed = {
        "daily_checkins",
        "food_entries",
        "user_equipment_profiles",
        "workout_execution_sessions",
        "workout_plan_instances",
        "workout_sessions",
    }
    conn = _connect(path)
    try:
        tables = [
            str(row[0])
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        ]
        populated_excluded: dict[str, int] = {}
        for table_name in tables:
            columns = {
                str(row[1])
                for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
            }
            if "user_id" not in columns or table_name in allowed:
                continue
            count = int(
                conn.execute(
                    f'SELECT COUNT(*) FROM "{table_name}" '
                    "WHERE user_id IN (106, 107, 108)"
                ).fetchone()[0]
            )
            if count:
                populated_excluded[table_name] = count
        assert populated_excluded == {}
    finally:
        conn.close()


def test_fresh_database_determinism_and_owned_replacement(
    tmp_path,
    monkeypatch,
    seeded_v2,
) -> None:
    seeded_path, first_result = seeded_v2
    second_path = tmp_path / "second.db"
    monkeypatch.setattr(database, "DB_PATH", second_path)
    _prepare_database(second_path)
    second_result = run_realistic_longitudinal_qa_seed_v2(
        database_path=second_path,
        apply=True,
        confirm_user_ids="106,107,108",
    )

    assert first_result.manifest["seed"] == second_result.manifest["seed"]
    assert _count(
        seeded_path,
        "SELECT COUNT(*) FROM workout_execution_set_actuals "
        "WHERE workout_execution_session_id IN ("
        "SELECT id FROM workout_execution_sessions "
        "WHERE user_id IN (106, 107, 108))",
    ) == _count(
        second_path,
        "SELECT COUNT(*) FROM workout_execution_set_actuals "
        "WHERE workout_execution_session_id IN ("
        "SELECT id FROM workout_execution_sessions "
        "WHERE user_id IN (106, 107, 108))",
    )

    with pytest.raises(RuntimeError, match="already exists"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=second_path,
            apply=True,
            confirm_user_ids="106,107,108",
        )

    replaced = run_realistic_longitudinal_qa_seed_v2(
        database_path=second_path,
        apply=True,
        confirm_user_ids="106,107,108",
        replace_owned=True,
    )
    assert replaced.manifest["seed"] == second_result.manifest["seed"]
    assert replaced.proposed_operation == "replace-owned 106,107,108"


def _introduce_ownership_violation(path: Path, variant: str) -> None:
    conn = _connect(path)
    try:
        with conn:
            plan_106 = int(
                conn.execute(
                    """
                    SELECT id
                    FROM workout_plan_instances
                    WHERE user_id = 106
                    ORDER BY id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            plan_107 = int(
                conn.execute(
                    """
                    SELECT id
                    FROM workout_plan_instances
                    WHERE user_id = 107
                    ORDER BY id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            planned_106 = int(
                conn.execute(
                    """
                    SELECT planned.id
                    FROM planned_workout_exercises AS planned
                    JOIN workout_plan_instances AS plan
                      ON plan.id = planned.workout_plan_instance_id
                    WHERE plan.user_id = 106
                    ORDER BY planned.id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            planned_107 = int(
                conn.execute(
                    """
                    SELECT planned.id
                    FROM planned_workout_exercises AS planned
                    JOIN workout_plan_instances AS plan
                      ON plan.id = planned.workout_plan_instance_id
                    WHERE plan.user_id = 107
                    ORDER BY planned.id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            execution_106 = int(
                conn.execute(
                    """
                    SELECT id
                    FROM workout_execution_sessions
                    WHERE user_id = 106
                    ORDER BY id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            execution_107 = int(
                conn.execute(
                    """
                    SELECT id
                    FROM workout_execution_sessions
                    WHERE user_id = 107
                    ORDER BY id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            session_107 = int(
                conn.execute(
                    """
                    SELECT id
                    FROM workout_sessions
                    WHERE user_id = 107
                    ORDER BY id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            set_107 = int(
                conn.execute(
                    """
                    SELECT workout_set.id
                    FROM workout_sets AS workout_set
                    JOIN workout_sessions AS session
                      ON session.id = workout_set.workout_session_id
                    WHERE session.user_id = 107
                    ORDER BY workout_set.id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            actual_106 = int(
                conn.execute(
                    """
                    SELECT actual.id
                    FROM workout_execution_set_actuals AS actual
                    JOIN workout_execution_sessions AS execution
                      ON execution.id = actual.workout_execution_session_id
                    WHERE execution.user_id = 106
                    ORDER BY actual.id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )
            set_106 = int(
                conn.execute(
                    """
                    SELECT workout_set.id
                    FROM workout_sets AS workout_set
                    JOIN workout_sessions AS session
                      ON session.id = workout_set.workout_session_id
                    WHERE session.user_id = 106
                    ORDER BY workout_set.id
                    LIMIT 1
                    """
                ).fetchone()[0]
            )

            if variant == "planned_to_other_plan":
                conn.execute(
                    """
                    UPDATE planned_workout_exercises
                    SET workout_plan_instance_id = ?
                    WHERE id = ?
                    """,
                    (plan_107, planned_106),
                )
            elif variant == "execution_to_other_plan":
                other_plan = int(
                    conn.execute(
                        """
                        INSERT INTO workout_plan_instances (
                            user_id,
                            status,
                            scenario,
                            confidence,
                            title,
                            approved_workout_plan_json,
                            selected_at,
                            completed_at,
                            created_at,
                            updated_at
                        )
                        SELECT user_id,
                               status,
                               scenario,
                               confidence,
                               title,
                               approved_workout_plan_json,
                               selected_at,
                               completed_at,
                               created_at,
                               updated_at
                        FROM workout_plan_instances
                        WHERE id = ?
                        """,
                        (plan_107,),
                    ).lastrowid
                )
                conn.execute(
                    """
                    UPDATE workout_execution_sessions
                    SET workout_plan_instance_id = ?
                    WHERE id = ?
                    """,
                    (other_plan, execution_106),
                )
            elif variant == "execution_to_other_session":
                conn.execute(
                    """
                    UPDATE workout_execution_sessions
                    SET workout_session_id = ?
                    WHERE id = ?
                    """,
                    (session_107, execution_106),
                )
            elif variant == "actual_to_other_execution":
                conn.execute(
                    """
                    UPDATE workout_execution_set_actuals
                    SET workout_execution_session_id = ?
                    WHERE id = ?
                    """,
                    (execution_107, actual_106),
                )
            elif variant == "actual_to_other_planned":
                conn.execute(
                    """
                    UPDATE workout_execution_set_actuals
                    SET planned_workout_exercise_id = ?
                    WHERE id = ?
                    """,
                    (planned_107, actual_106),
                )
            elif variant == "actual_to_other_substitution":
                conn.execute(
                    """
                    UPDATE workout_execution_set_actuals
                    SET substitution_for_planned_exercise_id = ?
                    WHERE id = ?
                    """,
                    (planned_107, actual_106),
                )
            elif variant == "actual_to_other_session":
                conn.execute(
                    """
                    UPDATE workout_execution_set_actuals
                    SET workout_session_id = ?
                    WHERE id = ?
                    """,
                    (session_107, actual_106),
                )
            elif variant == "actual_to_other_set":
                conn.execute(
                    """
                    UPDATE workout_execution_set_actuals
                    SET workout_set_id = ?
                    WHERE id = ?
                    """,
                    (set_107, actual_106),
                )
            elif variant == "set_to_other_session":
                conn.execute(
                    """
                    UPDATE workout_sets
                    SET workout_session_id = ?
                    WHERE id = ?
                    """,
                    (session_107, set_106),
                )
            elif variant == "cross_user_execution":
                conn.execute("INSERT INTO users (id, name) VALUES (999, 'Cross User')")
                conn.execute(
                    """
                    UPDATE workout_execution_sessions
                    SET user_id = 999,
                        workout_plan_instance_id = ?
                    WHERE id = ?
                    """,
                    (plan_106, execution_106),
                )
            elif variant == "unknown_future_relation":
                conn.execute(
                    """
                    CREATE TABLE future_plan_attachments (
                        id INTEGER PRIMARY KEY,
                        workout_plan_instance_id INTEGER NOT NULL,
                        FOREIGN KEY (workout_plan_instance_id)
                            REFERENCES workout_plan_instances(id)
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO future_plan_attachments (
                        workout_plan_instance_id
                    )
                    VALUES (?)
                    """,
                    (plan_106,),
                )
            else:
                raise AssertionError(f"Unknown ownership variant: {variant}")
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("variant", "error_pattern"),
    [
        ("planned_to_other_plan", "cross-user attachment"),
        ("execution_to_other_plan", "cross-user attachment"),
        ("execution_to_other_session", "cross-user attachment"),
        ("actual_to_other_execution", "cross-user attachment"),
        ("actual_to_other_planned", "cross-user attachment"),
        ("actual_to_other_substitution", "cross-user attachment"),
        ("actual_to_other_session", "cross-user attachment"),
        ("actual_to_other_set", "cross-user attachment"),
        ("set_to_other_session", "cross-user attachment"),
        ("cross_user_execution", "cross-user attachment"),
        ("unknown_future_relation", "unrecognized indirect attachment"),
    ],
)
def test_owned_replacement_rejects_cross_user_and_unknown_relation_graphs_before_write(
    tmp_path,
    monkeypatch,
    seeded_v2,
    variant,
    error_pattern,
) -> None:
    seeded_path, _result = seeded_v2
    path = _copy_database(seeded_path, tmp_path / f"{variant}.db")
    _introduce_ownership_violation(path, variant)
    before_hash = _sha256(path)

    def fail_if_write_connection_opens(_path):
        raise AssertionError("write connection opened before ownership rejection")

    monkeypatch.setattr(seed_module, "_open_read_write", fail_if_write_connection_opens)
    with pytest.raises(RuntimeError, match=error_pattern):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107,108",
            replace_owned=True,
        )

    assert _sha256(path) == before_hash


def test_id_and_case_insensitive_name_collisions_are_refused(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "collisions.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    conn = _connect(path)
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (id, name) VALUES (107, 'Unrelated Person')"
            )
    finally:
        conn.close()
    with pytest.raises(RuntimeError, match="unrecognized name"):
        run_realistic_longitudinal_qa_seed_v2(database_path=path)

    conn = _connect(path)
    try:
        with conn:
            conn.execute("DELETE FROM users WHERE id = 107")
            conn.execute(
                "INSERT INTO users (id, name) VALUES (?, ?)",
                (999, PERSONA_BY_ID[108].name.lower()),
            )
    finally:
        conn.close()
    with pytest.raises(RuntimeError, match="Case-insensitive name collision"):
        run_realistic_longitudinal_qa_seed_v2(database_path=path)


_LEGACY_SESSION_DAY_OFFSETS = (
    176,
    167,
    159,
    151,
    143,
    136,
    128,
    119,
    112,
    104,
    96,
    88,
    81,
    73,
    66,
    58,
    50,
    43,
    35,
    28,
    20,
    13,
    6,
    0,
)
_LEGACY_BENCH_LOADS = (
    40.0,
    45.0,
    45.0,
    50.0,
    50.0,
    55.0,
    55.0,
    55.0,
    55.0,
    55.0,
    45.0,
    45.0,
    55.0,
    55.0,
    60.0,
    60.0,
    60.0,
    60.0,
    60.0,
    60.0,
    50.0,
    50.0,
    60.0,
    65.0,
)
_LEGACY_BENCH_RIRS = (
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    3,
    3,
    None,
    2,
    3,
    2,
    1,
    1,
    4,
    4,
    3,
    2,
)


def _legacy_fixture_exercises(session_index: int) -> tuple[dict, dict]:
    completed_sets = 2 if session_index == 8 else 3
    bench_rir = _LEGACY_BENCH_RIRS[session_index]
    bench = {
        "name": "Dumbbell Bench Press",
        "measurement_type": "reps",
        "planned_sets": 3,
        "reps_min": 8,
        "reps_max": 10,
        "target_duration_seconds": None,
        "target_distance_meters": None,
        "equipment": ("dumbbell", "adjustable_bench"),
        "actuals": tuple(
            {
                "reps": reps,
                "duration": None,
                "distance": None,
                "weight": _LEGACY_BENCH_LOADS[session_index],
                "rir": bench_rir,
            }
            for reps in (10, 9, 8)[:completed_sets]
        ),
    }

    occurrence = session_index // 4
    variant = session_index % 4
    if variant == 0:
        reps = 6 + occurrence
        conditioning = {
            "name": "Pull-Up",
            "measurement_type": "reps",
            "planned_sets": 3,
            "reps_min": 5,
            "reps_max": 10,
            "target_duration_seconds": None,
            "target_distance_meters": None,
            "equipment": ("bodyweight",),
            "actuals": tuple(
                {
                    "reps": actual_reps,
                    "duration": None,
                    "distance": None,
                    "weight": None,
                    "rir": rir,
                }
                for actual_reps, rir in (
                    (reps, 3),
                    (max(1, reps - 1), 2),
                    (max(1, reps - 2), 2),
                )
            ),
        }
    elif variant == 1:
        duration = 35 + occurrence * 5
        conditioning = {
            "name": "Plank",
            "measurement_type": "duration",
            "planned_sets": 3,
            "reps_min": None,
            "reps_max": None,
            "target_duration_seconds": duration,
            "target_distance_meters": None,
            "equipment": ("bodyweight", "exercise_mat"),
            "actuals": tuple(
                {
                    "reps": None,
                    "duration": actual_duration,
                    "distance": None,
                    "weight": None,
                    "rir": None,
                }
                for actual_duration in (duration, duration + 5, duration)
            ),
        }
    elif variant == 2:
        distance = 20.0 + occurrence * 5.0
        weight = 40.0 + occurrence * 5.0
        conditioning = {
            "name": "Farmer Carry",
            "measurement_type": "distance",
            "planned_sets": 3,
            "reps_min": None,
            "reps_max": None,
            "target_duration_seconds": None,
            "target_distance_meters": distance,
            "equipment": ("dumbbell",),
            "actuals": tuple(
                {
                    "reps": None,
                    "duration": None,
                    "distance": actual_distance,
                    "weight": weight,
                    "rir": None,
                }
                for actual_distance in (distance, distance, distance + 5.0)
            ),
        }
    else:
        distance = 800.0 + occurrence * 100.0
        conditioning = {
            "name": "Treadmill Walk",
            "measurement_type": "distance",
            "planned_sets": 1,
            "reps_min": None,
            "reps_max": None,
            "target_duration_seconds": None,
            "target_distance_meters": distance,
            "equipment": ("treadmill",),
            "actuals": (
                {
                    "reps": None,
                    "duration": None,
                    "distance": distance,
                    "weight": None,
                    "rir": None,
                },
            ),
        }
    return bench, conditioning


def _insert_exact_legacy_106(path: Path) -> None:
    conn = _connect(path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO users (
                    id,
                    name,
                    age,
                    starting_weight,
                    primary_goal,
                    activity_level
                )
                VALUES (
                    106,
                    ?,
                    36,
                    182.0,
                    'Build strength and conditioning',
                    'moderate'
                )
                """,
                (EXPECTED_LEGACY_QA106_NAME,),
            )
            required_names = {
                "Dumbbell Bench Press",
                "Pull-Up",
                "Plank",
                "Farmer Carry",
                "Treadmill Walk",
            }
            placeholders = ",".join("?" for _ in required_names)
            catalog_ids = {
                str(row["name"]): int(row["id"])
                for row in conn.execute(
                    f"""
                    SELECT id, name
                    FROM exercise_catalog_exercises
                    WHERE name IN ({placeholders})
                    """,
                    tuple(sorted(required_names)),
                ).fetchall()
            }
            assert set(catalog_ids) == required_names

            for session_index, day_offset in enumerate(_LEGACY_SESSION_DAY_OFFSETS):
                session_date = date(2026, 7, 20) - timedelta(days=day_offset)
                timestamp = datetime.combine(
                    session_date,
                    time(hour=18),
                    tzinfo=UTC,
                ).isoformat()
                exercises = _legacy_fixture_exercises(session_index)
                second_name = str(exercises[1]["name"])
                title = (
                    "Upper Body Strength"
                    if second_name in {"Pull-Up", "Plank"}
                    else "Strength and Conditioning"
                )
                approved_plan = {
                    "title": title,
                    "duration_minutes": 50,
                    "confidence": "High",
                    "exercises": [
                        {
                            "exercise_name": exercise["name"],
                            "catalog_exercise_id": catalog_ids[str(exercise["name"])],
                            "sets": exercise["planned_sets"],
                            "measurement_type": exercise["measurement_type"],
                        }
                        for exercise in exercises
                    ],
                }
                plan_id = int(
                    conn.execute(
                        """
                        INSERT INTO workout_plan_instances (
                            user_id,
                            status,
                            scenario,
                            confidence,
                            title,
                            approved_workout_plan_json,
                            selected_at,
                            completed_at,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            106,
                            'completed',
                            ?,
                            'High',
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?
                        )
                        """,
                        (
                            EXPECTED_LEGACY_QA106_SCENARIO,
                            title,
                            json.dumps(approved_plan, sort_keys=True),
                            timestamp,
                            timestamp,
                            timestamp,
                            timestamp,
                        ),
                    ).lastrowid
                )

                planned_ids: list[int] = []
                for exercise_order, exercise in enumerate(exercises, start=1):
                    is_reps = exercise["measurement_type"] == "reps"
                    planned_ids.append(
                        int(
                            conn.execute(
                                """
                                INSERT INTO planned_workout_exercises (
                                    workout_plan_instance_id,
                                    exercise_order,
                                    name,
                                    sets,
                                    measurement_type,
                                    reps_min,
                                    reps_max,
                                    target_duration_seconds,
                                    target_distance_meters,
                                    rir_min,
                                    rir_max,
                                    notes,
                                    equipment_required_json,
                                    catalog_exercise_id,
                                    created_at
                                )
                                VALUES (
                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                                )
                                """,
                                (
                                    plan_id,
                                    exercise_order,
                                    exercise["name"],
                                    exercise["planned_sets"],
                                    exercise["measurement_type"],
                                    exercise["reps_min"],
                                    exercise["reps_max"],
                                    exercise["target_duration_seconds"],
                                    exercise["target_distance_meters"],
                                    1 if is_reps else None,
                                    3 if is_reps else None,
                                    (
                                        "Use controlled form and record each "
                                        "completed set."
                                    ),
                                    json.dumps(exercise["equipment"]),
                                    catalog_ids[str(exercise["name"])],
                                    timestamp,
                                ),
                            ).lastrowid
                        )
                    )

                execution_id = int(
                    conn.execute(
                        """
                        INSERT INTO workout_execution_sessions (
                            workout_plan_instance_id,
                            user_id,
                            status,
                            started_at,
                            completed_at,
                            created_at,
                            updated_at
                        )
                        VALUES (?, 106, 'completed', ?, ?, ?, ?)
                        """,
                        (
                            plan_id,
                            timestamp,
                            timestamp,
                            timestamp,
                            timestamp,
                        ),
                    ).lastrowid
                )
                for planned_id, exercise in zip(
                    planned_ids,
                    exercises,
                    strict=True,
                ):
                    is_reps = exercise["measurement_type"] == "reps"
                    for set_number, actual in enumerate(
                        exercise["actuals"],
                        start=1,
                    ):
                        conn.execute(
                            """
                            INSERT INTO workout_execution_set_actuals (
                                workout_execution_session_id,
                                planned_workout_exercise_id,
                                exercise_name,
                                set_number,
                                planned_reps_min,
                                planned_reps_max,
                                measurement_type,
                                planned_duration_seconds,
                                planned_distance_meters,
                                planned_rir_min,
                                planned_rir_max,
                                actual_reps,
                                actual_duration_seconds,
                                actual_distance_meters,
                                actual_weight,
                                actual_rir,
                                completed,
                                skipped,
                                notes,
                                created_at,
                                updated_at
                            )
                            VALUES (
                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                1, 0, ?, ?, ?
                            )
                            """,
                            (
                                execution_id,
                                planned_id,
                                exercise["name"],
                                set_number,
                                exercise["reps_min"],
                                exercise["reps_max"],
                                exercise["measurement_type"],
                                exercise["target_duration_seconds"],
                                exercise["target_distance_meters"],
                                1 if is_reps else None,
                                3 if is_reps else None,
                                actual["reps"],
                                actual["duration"],
                                actual["distance"],
                                actual["weight"],
                                actual["rir"],
                                "Recorded during the completed workout.",
                                timestamp,
                                timestamp,
                            ),
                        )
    finally:
        conn.close()


def _insert_minimal_legacy_lookalike(path: Path) -> None:
    conn = _connect(path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO users (
                    id,
                    name,
                    age,
                    starting_weight,
                    primary_goal,
                    activity_level
                )
                VALUES (
                    106,
                    ?,
                    36,
                    182.0,
                    'Build strength and conditioning',
                    'moderate'
                )
                """,
                (EXPECTED_LEGACY_QA106_NAME,),
            )
            conn.execute(
                """
                INSERT INTO workout_plan_instances (
                    user_id,
                    status,
                    scenario,
                    confidence,
                    title,
                    approved_workout_plan_json,
                    selected_at,
                    completed_at,
                    created_at,
                    updated_at
                )
                VALUES (
                    106,
                    'completed',
                    ?,
                    'High',
                    'Legacy Performance History',
                    '{}',
                    '2026-07-20T18:00:00+00:00',
                    '2026-07-20T18:00:00+00:00',
                    '2026-07-20T18:00:00+00:00',
                    '2026-07-20T18:00:00+00:00'
                )
                """,
                (EXPECTED_LEGACY_QA106_SCENARIO,),
            )
    finally:
        conn.close()


def _mutate_exact_legacy_fixture(path: Path, variant: str) -> None:
    conn = _connect(path)
    try:
        with conn:
            if variant == "wrong_profile":
                conn.execute(
                    """
                    UPDATE users
                    SET primary_goal = 'strength_progression'
                    WHERE id = 106
                    """
                )
            elif variant == "wrong_plan_count":
                plan_id = int(
                    conn.execute(
                        """
                        SELECT id
                        FROM workout_plan_instances
                        WHERE user_id = 106
                        ORDER BY id
                        LIMIT 1
                        """
                    ).fetchone()[0]
                )
                conn.execute(
                    """
                    DELETE FROM workout_execution_set_actuals
                    WHERE workout_execution_session_id IN (
                        SELECT id
                        FROM workout_execution_sessions
                        WHERE workout_plan_instance_id = ?
                    )
                    """,
                    (plan_id,),
                )
                conn.execute(
                    """
                    DELETE FROM workout_execution_sessions
                    WHERE workout_plan_instance_id = ?
                    """,
                    (plan_id,),
                )
                conn.execute(
                    """
                    DELETE FROM planned_workout_exercises
                    WHERE workout_plan_instance_id = ?
                    """,
                    (plan_id,),
                )
                conn.execute(
                    "DELETE FROM workout_plan_instances WHERE id = ?",
                    (plan_id,),
                )
            elif variant == "missing_execution":
                execution_id = int(
                    conn.execute(
                        """
                        SELECT id
                        FROM workout_execution_sessions
                        WHERE user_id = 106
                        ORDER BY id
                        LIMIT 1
                        """
                    ).fetchone()[0]
                )
                conn.execute(
                    """
                    DELETE FROM workout_execution_set_actuals
                    WHERE workout_execution_session_id = ?
                    """,
                    (execution_id,),
                )
                conn.execute(
                    "DELETE FROM workout_execution_sessions WHERE id = ?",
                    (execution_id,),
                )
            elif variant == "wrong_exercise_count":
                planned_id = int(
                    conn.execute(
                        """
                        SELECT planned.id
                        FROM planned_workout_exercises AS planned
                        JOIN workout_plan_instances AS plan
                          ON plan.id = planned.workout_plan_instance_id
                        WHERE plan.user_id = 106
                        ORDER BY planned.id
                        LIMIT 1
                        """
                    ).fetchone()[0]
                )
                conn.execute(
                    """
                    DELETE FROM workout_execution_set_actuals
                    WHERE planned_workout_exercise_id = ?
                    """,
                    (planned_id,),
                )
                conn.execute(
                    "DELETE FROM planned_workout_exercises WHERE id = ?",
                    (planned_id,),
                )
            elif variant == "altered_exercise":
                conn.execute(
                    """
                    UPDATE planned_workout_exercises
                    SET name = 'Push-Up'
                    WHERE id = (
                        SELECT planned.id
                        FROM planned_workout_exercises AS planned
                        JOIN workout_plan_instances AS plan
                          ON plan.id = planned.workout_plan_instance_id
                        WHERE plan.user_id = 106
                        ORDER BY planned.id
                        LIMIT 1
                    )
                    """
                )
            elif variant == "altered_equipment":
                conn.execute(
                    """
                    UPDATE planned_workout_exercises
                    SET equipment_required_json = '["dumbbell"]'
                    WHERE id = (
                        SELECT planned.id
                        FROM planned_workout_exercises AS planned
                        JOIN workout_plan_instances AS plan
                          ON plan.id = planned.workout_plan_instance_id
                        WHERE plan.user_id = 106
                        ORDER BY planned.id
                        LIMIT 1
                    )
                    """
                )
            elif variant == "wrong_actual_count":
                conn.execute(
                    """
                    DELETE FROM workout_execution_set_actuals
                    WHERE id = (
                        SELECT actual.id
                        FROM workout_execution_set_actuals AS actual
                        JOIN workout_execution_sessions AS execution
                          ON execution.id = actual.workout_execution_session_id
                        WHERE execution.user_id = 106
                        ORDER BY actual.id
                        LIMIT 1
                    )
                    """
                )
            elif variant == "broken_link":
                planned_ids = [
                    int(row[0])
                    for row in conn.execute(
                        """
                        SELECT planned.id
                        FROM planned_workout_exercises AS planned
                        JOIN workout_plan_instances AS plan
                          ON plan.id = planned.workout_plan_instance_id
                        WHERE plan.user_id = 106
                        ORDER BY planned.id
                        LIMIT 2
                        """
                    ).fetchall()
                ]
                conn.execute(
                    """
                    UPDATE workout_execution_set_actuals
                    SET planned_workout_exercise_id = ?
                    WHERE id = (
                        SELECT id
                        FROM workout_execution_set_actuals
                        WHERE planned_workout_exercise_id = ?
                        ORDER BY id
                        LIMIT 1
                    )
                    """,
                    (planned_ids[1], planned_ids[0]),
                )
            elif variant == "extra_direct":
                conn.execute(
                    """
                    INSERT INTO daily_checkins (
                        user_id,
                        checkin_date,
                        sleep_hours,
                        energy_level,
                        soreness_level,
                        notes
                    )
                    VALUES (106, '2026-07-20', 7.0, 7, 3, 'unrelated row')
                    """
                )
            elif variant == "extra_indirect":
                source_id = int(
                    conn.execute(
                        """
                        SELECT planned.id
                        FROM planned_workout_exercises AS planned
                        JOIN workout_plan_instances AS plan
                          ON plan.id = planned.workout_plan_instance_id
                        WHERE plan.user_id = 106
                        ORDER BY planned.id
                        LIMIT 1
                        """
                    ).fetchone()[0]
                )
                conn.execute(
                    """
                    INSERT INTO planned_workout_exercises (
                        workout_plan_instance_id,
                        exercise_order,
                        name,
                        sets,
                        measurement_type,
                        reps_min,
                        reps_max,
                        target_duration_seconds,
                        target_distance_meters,
                        rir_min,
                        rir_max,
                        notes,
                        equipment_required_json,
                        catalog_exercise_id,
                        created_at
                    )
                    SELECT workout_plan_instance_id,
                           99,
                           name,
                           sets,
                           measurement_type,
                           reps_min,
                           reps_max,
                           target_duration_seconds,
                           target_distance_meters,
                           rir_min,
                           rir_max,
                           notes,
                           equipment_required_json,
                           catalog_exercise_id,
                           created_at
                    FROM planned_workout_exercises
                    WHERE id = ?
                    """,
                    (source_id,),
                )
            else:
                raise AssertionError(f"Unknown legacy mutation: {variant}")
    finally:
        conn.close()


def test_exact_legacy_106_requires_explicit_migration_and_migrates(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "legacy-exact.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    _insert_exact_legacy_106(path)
    before_hash = _sha256(path)

    with pytest.raises(RuntimeError, match="migrate-legacy-106"):
        run_realistic_longitudinal_qa_seed_v2(database_path=path)
    assert _sha256(path) == before_hash

    migrated = run_realistic_longitudinal_qa_seed_v2(
        database_path=path,
        apply=True,
        confirm_user_ids="106,107,108",
        migrate_legacy_106=True,
    )
    assert migrated.manifest["run"]["legacy_qa106_migrated"] is True
    assert (
        _count(
            path,
            "SELECT COUNT(*) FROM workout_plan_instances "
            "WHERE user_id = 106 AND scenario = ?",
            (EXPECTED_LEGACY_QA106_SCENARIO,),
        )
        == 0
    )
    assert (
        _count(
            path,
            "SELECT COUNT(*) FROM workout_plan_instances WHERE user_id = 106",
        )
        == EXPECTED_PERSONA_COUNTS[106]["workout_plan_instances"]
    )


def test_minimal_legacy_name_and_marker_lookalike_is_not_migratable(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "legacy-lookalike.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    _insert_minimal_legacy_lookalike(path)
    before_hash = _sha256(path)

    with pytest.raises(RuntimeError, match="exact fixture signature mismatch"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107,108",
            migrate_legacy_106=True,
        )
    assert _sha256(path) == before_hash


@pytest.mark.parametrize(
    "variant",
    [
        "wrong_profile",
        "wrong_plan_count",
        "missing_execution",
        "wrong_exercise_count",
        "altered_exercise",
        "altered_equipment",
        "wrong_actual_count",
        "broken_link",
        "extra_direct",
        "extra_indirect",
    ],
)
def test_near_match_legacy_fixtures_are_rejected_without_mutation(
    tmp_path,
    monkeypatch,
    variant,
) -> None:
    path = tmp_path / f"legacy-{variant}.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    _prepare_database(path)
    _insert_exact_legacy_106(path)
    _mutate_exact_legacy_fixture(path, variant)
    before_hash = _sha256(path)

    with pytest.raises(RuntimeError, match="exact fixture signature mismatch"):
        run_realistic_longitudinal_qa_seed_v2(
            database_path=path,
            apply=True,
            confirm_user_ids="106,107,108",
            migrate_legacy_106=True,
        )
    assert _sha256(path) == before_hash


def test_current_services_observe_phases_modalities_and_final_states(
    seeded_v2,
) -> None:
    path, _result = seeded_v2
    database.DB_PATH = path

    mixed = build_workout_exercise_history_analytics(
        user_id=108,
        lookback_days=365,
        exercise_limit=20,
        session_limit=400,
        end_date=HISTORY_END.isoformat(),
        include_set_details=False,
    )
    mixed_by_name = {exercise.exercise_name: exercise for exercise in mixed.exercises}
    assert {
        name: mixed_by_name[name].modality
        for name in (
            "Dumbbell Bench Press",
            "Pull-Up",
            "Plank",
            "Farmer Carry",
            "Treadmill Walk",
        )
    } == {
        "Dumbbell Bench Press": "externally_weighted",
        "Pull-Up": "bodyweight",
        "Plank": "timed",
        "Farmer Carry": "carry",
        "Treadmill Walk": "cardio",
    }
    for name in ("Plank", "Farmer Carry", "Treadmill Walk"):
        assert mixed_by_name[name].completed_session_count >= 10
        assert (
            sum(
                session.performance_metric is not None
                for session in mixed_by_name[name].recent_sessions
            )
            >= 8
        )

    selected = mixed_by_name["Farmer Carry"].recent_sessions[0]
    detail = build_workout_exercise_history_session_detail(
        user_id=108,
        session_key=selected.session_key,
        lookback_days=365,
        end_date=HISTORY_END.isoformat(),
    )
    assert detail is not None
    assert detail.has_set_details is True
    assert detail.measurement_type == "distance"
    assert detail.completed_sets

    fatigue = build_recovery_intelligence(
        user_id=106,
        target_date="2026-06-14",
    )
    rebound = build_recovery_intelligence(
        user_id=106,
        target_date="2026-07-22",
    )
    assert fatigue.fatigue_risk in {"high", "moderate"}
    assert rebound.fatigue_risk == "low"
    assert fatigue.readiness_level in {"low", "moderate"}
    assert rebound.readiness_level == "high"

    for user_id in QA_USER_IDS:
        latest = PERSONA_BY_ID[user_id].latest_activity.isoformat()
        trend = build_nutrition_trend_window(
            user_id=user_id,
            end_date=latest,
            window_days=28,
        )
        assert trend.complete_logging_day_count > 0
        assert trend.partial_logging_day_count > 0
        assert trend.no_log_day_count > 0
        assert trend.observations

        target_summary = build_target_vs_actual_nutrition_summary(
            user_id=user_id,
            target_date=latest,
        )
        assert target_summary.nutrition_actuals.entry_count >= 3
        assert target_summary.logging_completeness in {
            "complete_enough_for_guidance",
            "reasonably_complete",
        }
        assert target_summary.comparisons["calories"].actual is not None

        training = build_training_execution_summary(user_id)
        assert training.completed_execution_count == 5
        assert training.average_completion_percentage is not None
        assert training.execution_quality != "no_planned_execution_data"
        assert training.confidence in {"Low", "Moderate", "High"}

    interrupted_training = build_training_execution_summary(107)
    assert (
        interrupted_training.incomplete_logging_count > 0
        or interrupted_training.missing_actual_rir_count > 0
        or interrupted_training.skipped_exercise_count > 0
    )

    fatigue_feed = build_longitudinal_insight_feed(
        user_id=106,
        as_of_date="2026-06-14",
        max_insights=10,
    )
    final_106_feed = build_longitudinal_insight_feed(
        user_id=106,
        as_of_date=HISTORY_END,
        max_insights=10,
    )
    interrupted_feed = build_longitudinal_insight_feed(
        user_id=107,
        as_of_date=HISTORY_END,
        max_insights=10,
    )
    mixed_feed = build_longitudinal_insight_feed(
        user_id=108,
        as_of_date=HISTORY_END,
        max_insights=10,
    )
    assert any(
        insight.domain == "recovery" and insight.direction in {"worsening", "mixed"}
        for insight in fatigue_feed.insights
    )
    assert final_106_feed.insights
    assert interrupted_feed.insights
    assert mixed_feed.insights
    assert any(insight.domain == "training" for insight in mixed_feed.insights)

    for user_id in QA_USER_IDS:
        health_state = build_user_health_state(user_id)
        assert health_state.training_state.has_workout_data is True
        assert health_state.training_state.training_trend in {
            "Progressing",
            "Stable",
        }
        decision = build_coaching_decision(health_state)
        assert decision.scenario != "data_quality_limited"
    assert build_user_health_state(106).recovery_state.readiness_level == "High"
    assert build_user_health_state(108).recovery_state.readiness_level == "High"


def test_dataset_generation_is_fixed_without_global_randomness() -> None:
    first = build_seed_dataset()
    second = build_seed_dataset()

    assert first == second
    assert min(row.checkin_date for row in first.recovery) == HISTORY_START
    assert (
        max(
            workout.workout_date for workout in first.workouts if workout.user_id == 108
        )
        == HISTORY_END
    )
    assert SEED_MARKER == f"[{SEED_VERSION}]"
