from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from services.qa_seed_data_verification_service import (
    QASeedVerificationError,
    render_qa_seed_verification_report,
    verify_qa_seed_data,
)


def create_fixture_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE daily_checkins (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            notes TEXT
        );
        CREATE TABLE food_entries (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            grams REAL NOT NULL,
            entry_date TEXT NOT NULL
        );
        CREATE TABLE workout_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            workout_date TEXT NOT NULL
        );
        CREATE TABLE workout_plan_instances (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            scenario TEXT NOT NULL,
            confidence TEXT NOT NULL,
            title TEXT NOT NULL,
            approved_workout_plan_json TEXT NOT NULL,
            selected_at TEXT,
            created_at TEXT
        );
        CREATE TABLE planned_workout_exercises (
            id INTEGER PRIMARY KEY,
            workout_plan_instance_id INTEGER NOT NULL,
            exercise_order INTEGER NOT NULL,
            name TEXT NOT NULL,
            sets INTEGER NOT NULL,
            reps_min INTEGER NOT NULL,
            reps_max INTEGER NOT NULL,
            rir_min INTEGER NOT NULL,
            rir_max INTEGER NOT NULL,
            notes TEXT NOT NULL,
            equipment_required_json TEXT NOT NULL
        );
        CREATE TABLE workout_execution_sessions (
            id INTEGER PRIMARY KEY,
            workout_plan_instance_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            workout_session_id INTEGER,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT
        );
        CREATE TABLE workout_execution_set_actuals (
            id INTEGER PRIMARY KEY,
            workout_execution_session_id INTEGER NOT NULL,
            workout_session_id INTEGER,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            skipped INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT
        );
        """)
    conn.executemany(
        "INSERT INTO users (id, name) VALUES (?, ?)",
        [
            (101, "QA 101"),
            (102, "QA 102"),
            (105, "QA 105"),
        ],
    )

    for offset, day in enumerate(range(8, 15), start=1):
        checkin_date = f"2026-06-{day:02d}"
        conn.execute(
            """
            INSERT INTO daily_checkins (user_id, checkin_date, notes)
            VALUES (?, ?, ?)
            """,
            (102, checkin_date, "private check-in note must not appear"),
        )
        conn.execute(
            """
            INSERT INTO food_entries (user_id, food_id, grams, entry_date)
            VALUES (?, ?, ?, ?)
            """,
            (102, 1, 100.0 + offset, checkin_date),
        )

    for session_id, day in enumerate((8, 10, 12), start=1):
        workout_date = f"2026-06-{day:02d}"
        plan_id = session_id
        execution_id = session_id
        conn.execute(
            "INSERT INTO workout_sessions (id, user_id, workout_date) VALUES (?, ?, ?)",
            (session_id, 102, workout_date),
        )
        conn.execute(
            """
            INSERT INTO workout_plan_instances (
                id, user_id, status, scenario, confidence, title,
                approved_workout_plan_json, selected_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                102,
                "approved",
                "fixture",
                "high",
                "Fixture Plan",
                "{}",
                workout_date,
                workout_date,
            ),
        )
        conn.execute(
            """
            INSERT INTO planned_workout_exercises (
                workout_plan_instance_id, exercise_order, name, sets, reps_min,
                reps_max, rir_min, rir_max, notes, equipment_required_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (plan_id, 1, "Goblet Squat", 3, 8, 12, 1, 3, "private", "[]"),
        )
        conn.execute(
            """
            INSERT INTO workout_execution_sessions (
                id, workout_plan_instance_id, user_id, status,
                workout_session_id, started_at, completed_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                plan_id,
                102,
                "completed",
                session_id,
                f"{workout_date}T10:00:00",
                f"{workout_date}T11:00:00",
                f"{workout_date}T09:00:00",
            ),
        )
        for set_number in (1, 2):
            conn.execute(
                """
                INSERT INTO workout_execution_set_actuals (
                    workout_execution_session_id, workout_session_id,
                    exercise_name, set_number, completed, skipped, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    session_id,
                    "Goblet Squat",
                    set_number,
                    1,
                    0,
                    "private set note must not appear",
                    f"{workout_date}T10:10:00",
                ),
            )

    conn.execute(
        """
        INSERT INTO daily_checkins (user_id, checkin_date, notes)
        VALUES (?, ?, ?)
        """,
        (105, "2026-06-09", "private sparse note must not appear"),
    )
    conn.commit()
    conn.close()


def test_missing_db_returns_safe_failure(tmp_path: Path) -> None:
    report = verify_qa_seed_data(db_path=tmp_path / "missing.db")

    assert report.success is False
    assert report.database_source["database_exists"] is False
    assert report.summary["global_diagnosis"] == "wrong_db_suspected"
    assert "Database file was not found" in " ".join(report.warnings)


def test_empty_db_returns_no_qa_users(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.commit()
    conn.close()

    report = verify_qa_seed_data(db_path=db_path)

    assert report.success is True
    assert report.summary["users_present"] == 0
    assert report.summary["global_diagnosis"] == "wrong_db_suspected"


def test_users_and_selected_range_counts_are_detected(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.db"
    create_fixture_db(db_path)

    report = verify_qa_seed_data(
        db_path=db_path,
        user_ids=(101, 102, 105),
        start_date="2026-06-08",
        end_date="2026-06-14",
    )
    user_102 = next(user for user in report.users if user.user_id == 102)

    assert user_102.user_exists is True
    assert user_102.global_bounds["recovery"].row_count == 7
    assert user_102.global_bounds["recovery"].min_date == "2026-06-08"
    assert user_102.selected_range_counts["nutrition"].row_count == 7
    assert user_102.selected_range_counts["nutrition"].distinct_logged_days == 7
    assert user_102.selected_range_counts["workout_sessions"].row_count == 3
    assert (
        user_102.selected_range_counts["workout_execution_sessions"].completed_count
        == 3
    )
    assert user_102.selected_range_counts["actual_sets"].row_count == 6
    assert user_102.data_quality_label == "strong"
    assert "usable_for_weekly_summary" in user_102.diagnosis_codes


def test_sparse_user_is_limited_or_insufficient(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.db"
    create_fixture_db(db_path)

    report = verify_qa_seed_data(
        db_path=db_path,
        user_ids=(105,),
        start_date="2026-06-08",
        end_date="2026-06-14",
    )
    user_105 = report.users[0]

    assert user_105.user_exists is True
    assert user_105.selected_range_counts["recovery"].row_count == 1
    assert user_105.data_quality_label == "limited"
    assert "insufficient_for_weekly_summary" in user_105.diagnosis_codes


def test_range_outside_bounds_is_classified(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.db"
    create_fixture_db(db_path)

    report = verify_qa_seed_data(
        db_path=db_path,
        user_ids=(102,),
        start_date="2026-01-01",
        end_date="2026-01-07",
    )
    user_102 = report.users[0]

    assert user_102.selected_range_counts["recovery"].row_count == 0
    assert "selected_range_out_of_bounds" in user_102.diagnosis_codes


def test_invalid_date_range_is_rejected_safely(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.db"
    create_fixture_db(db_path)

    with pytest.raises(QASeedVerificationError):
        verify_qa_seed_data(
            db_path=db_path,
            start_date="2026-06-14",
            end_date="2026-06-08",
        )


def test_renderer_does_not_expose_raw_rows_notes_or_secrets(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.db"
    create_fixture_db(db_path)

    report = verify_qa_seed_data(db_path=db_path)
    output = render_qa_seed_verification_report(report)
    combined = repr(report) + output

    assert "private check-in note" not in combined
    assert "private set note" not in combined
    assert "SECRET" not in combined
    assert "API_KEY" not in combined
    assert "traceback" not in combined.lower()


def test_cli_runs_against_fixture_db(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.db"
    create_fixture_db(db_path)

    result = subprocess.run(
        [
            sys.executable,
            "tools/dev_qa_seed_data_verification.py",
            "--db-path",
            str(db_path),
            "--start-date",
            "2026-06-08",
            "--end-date",
            "2026-06-14",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "QA Seed Data Verification" in result.stdout
    assert "User 102 - aligned_managed" in result.stdout
    assert "strong_for_weekly_summary" in result.stdout


def test_service_does_not_import_or_call_provider_runtime() -> None:
    source = Path("services/qa_seed_data_verification_service.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "ollama" not in lowered
    assert "crewai" not in lowered
    assert "qwen" not in lowered
    assert "provider_runtime" not in lowered


def test_service_performs_no_database_writes() -> None:
    source = Path("services/qa_seed_data_verification_service.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "insert " not in lowered
    assert "update " not in lowered
    assert "delete " not in lowered
    assert "replace " not in lowered
    assert "create table" not in lowered
