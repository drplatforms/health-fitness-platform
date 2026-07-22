from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import database
from services.recovery_service import (
    get_recent_recovery_checkins,
    get_recent_recovery_metrics,
    get_recovery_checkin,
    save_recovery_checkin,
)


def test_save_recovery_checkin_updates_existing_day(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()

    first_id = save_recovery_checkin(
        user_id=1,
        target_date="2026-07-05",
        body_weight=None,
        sleep_hours=6.5,
        energy_level=5,
        soreness_level=4,
        mood="managed",
        notes="General notes: Initial save.",
    )
    second_id = save_recovery_checkin(
        user_id=1,
        target_date="2026-07-05",
        body_weight=None,
        sleep_hours=7.5,
        energy_level=7,
        soreness_level=3,
        mood="low",
        notes="Pain/restriction: Mild knee stiffness.",
    )

    assert second_id == first_id

    conn = database.get_connection()
    try:
        count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM daily_checkins
            WHERE user_id = ? AND checkin_date = ?
            """,
            (1, "2026-07-05"),
        ).fetchone()["count"]
    finally:
        conn.close()

    assert count == 1

    checkin = get_recovery_checkin(1, "2026-07-05")
    assert checkin is not None
    assert checkin["sleep_hours"] == 7.5
    assert checkin["energy_level"] == 7
    assert checkin["soreness_level"] == 3
    assert checkin["mood"] == "low"


def test_save_recovery_checkin_persists_body_weight_when_supplied(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()

    save_recovery_checkin(
        user_id=1,
        target_date="2026-07-06",
        body_weight=191.4,
        sleep_hours=8.0,
        energy_level=8,
        soreness_level=2,
        mood="low",
        notes="General notes: Feeling solid.",
    )

    checkin = get_recovery_checkin(1, "2026-07-06")

    assert checkin is not None
    assert checkin["body_weight"] == 191.4
    assert checkin["sleep_hours"] == 8.0


def test_structured_recovery_signals_persist_with_nullable_unknowns(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()

    save_recovery_checkin(
        user_id=1,
        target_date="2026-07-07",
        body_weight=None,
        sleep_hours=7.5,
        sleep_quality=2,
        energy_level=7,
        soreness_level=3,
        stress_level=4,
        training_motivation=2,
        pain_concern="mild",
        pain_area="shoulder",
        mood="steady",
        notes=None,
    )
    save_recovery_checkin(
        user_id=2,
        target_date="2026-07-07",
        body_weight=None,
        sleep_hours=8.0,
        energy_level=8,
        soreness_level=2,
        mood=None,
        notes=None,
    )

    structured = get_recovery_checkin(1, "2026-07-07")
    unknown = get_recovery_checkin(2, "2026-07-07")

    assert structured is not None
    assert structured["sleep_quality"] == 2
    assert structured["stress_level"] == 4
    assert structured["training_motivation"] == 2
    assert structured["pain_concern"] == "mild"
    assert structured["pain_area"] == "shoulder"
    metrics = get_recent_recovery_metrics(1)
    assert metrics is not None
    assert metrics["latest_sleep_quality"] == 2
    assert metrics["latest_stress_level"] == 4
    assert metrics["latest_training_motivation"] == 2
    assert metrics["latest_pain_concern"] == "mild"
    assert metrics["latest_pain_area"] == "shoulder"
    assert unknown is not None
    assert unknown["sleep_quality"] is None
    assert unknown["stress_level"] is None
    assert unknown["training_motivation"] is None
    assert unknown["pain_concern"] is None
    assert unknown["pain_area"] is None


def test_recent_recovery_history_is_user_scoped(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()

    for user_id in (1, 2):
        for day in ("2026-07-06", "2026-07-07"):
            save_recovery_checkin(
                user_id=user_id,
                target_date=day,
                body_weight=None,
                sleep_hours=7.0,
                energy_level=6,
                soreness_level=4,
                mood=None,
                notes=None,
            )

    history = get_recent_recovery_checkins(1)

    assert [item["checkin_date"] for item in history] == [
        "2026-07-07",
        "2026-07-06",
    ]
    assert {item["user_id"] for item in history} == {1}


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("sleep_quality", 0),
        ("stress_level", 6),
        ("training_motivation", 0),
    ],
)
def test_structured_recovery_scales_are_bounded(
    monkeypatch, tmp_path, field_name, value
) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()
    kwargs = {
        "user_id": 1,
        "target_date": "2026-07-07",
        "body_weight": None,
        "sleep_hours": 7.0,
        "energy_level": 6,
        "soreness_level": 4,
        "mood": None,
        "notes": None,
        field_name: value,
    }

    with pytest.raises(ValueError, match="between 1 and 5"):
        save_recovery_checkin(**kwargs)


def test_daily_checkin_schema_upgrade_preserves_historical_rows(
    monkeypatch, tmp_path
) -> None:
    db_path = Path(tmp_path) / "legacy_fitness_ai.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            body_weight REAL,
            sleep_hours REAL,
            energy_level INTEGER,
            soreness_level INTEGER,
            mood TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT INTO daily_checkins (
            user_id, checkin_date, sleep_hours, energy_level, soreness_level
        )
        VALUES (1, '2026-01-01', 7.0, 6, 4)
        """
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    historical = get_recovery_checkin(1, "2026-01-01")

    assert historical is not None
    assert historical["sleep_hours"] == 7.0
    assert historical["sleep_quality"] is None
    assert historical["stress_level"] is None
    assert historical["training_motivation"] is None
    assert historical["pain_concern"] is None
    assert historical["pain_area"] is None

    conn = database.get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO daily_checkins (
                user_id,
                checkin_date,
                sleep_hours,
                energy_level,
                soreness_level,
                pain_concern,
                pain_area
            )
            VALUES (1, '2026-01-02', 7.0, 6, 4, 'none', 'knee')
            """
        )
    conn.close()


def test_get_recent_recovery_metrics_ignores_null_body_weight(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()

    save_recovery_checkin(
        user_id=103,
        target_date="2026-07-04",
        body_weight=190.0,
        sleep_hours=7.5,
        energy_level=7,
        soreness_level=3,
        mood="managed",
        notes=None,
    )
    save_recovery_checkin(
        user_id=103,
        target_date="2026-07-05",
        body_weight=None,
        sleep_hours=8.0,
        energy_level=8,
        soreness_level=2,
        mood="low",
        notes=None,
    )

    metrics = get_recent_recovery_metrics(103)

    assert metrics is not None
    assert metrics["latest_weight"] == 190.0
    assert metrics["weight_change"] is None


def test_get_recent_recovery_metrics_uses_only_valid_numeric_body_weights(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(database, "DB_PATH", Path(tmp_path) / "fitness_ai_test.db")
    database.initialize_database()

    save_recovery_checkin(
        user_id=103,
        target_date="2026-07-04",
        body_weight=188.0,
        sleep_hours=7.0,
        energy_level=6,
        soreness_level=4,
        mood="managed",
        notes=None,
    )
    save_recovery_checkin(
        user_id=103,
        target_date="2026-07-05",
        body_weight=None,
        sleep_hours=7.5,
        energy_level=7,
        soreness_level=3,
        mood="managed",
        notes=None,
    )
    save_recovery_checkin(
        user_id=103,
        target_date="2026-07-06",
        body_weight=190.5,
        sleep_hours=8.0,
        energy_level=8,
        soreness_level=2,
        mood="low",
        notes=None,
    )

    metrics = get_recent_recovery_metrics(103)

    assert metrics is not None
    assert metrics["latest_weight"] == 190.5
    assert metrics["weight_change"] == 2.5
