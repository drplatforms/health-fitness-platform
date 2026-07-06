from __future__ import annotations

from pathlib import Path

import database
from services.recovery_service import get_recovery_checkin, save_recovery_checkin


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
