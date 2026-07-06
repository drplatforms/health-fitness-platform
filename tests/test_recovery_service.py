from __future__ import annotations

from pathlib import Path

import database
from services.recovery_service import (
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
