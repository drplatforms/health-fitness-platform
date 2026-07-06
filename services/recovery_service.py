from datetime import date, datetime

from database import get_connection

# =====================================
# Get Recent Recovery Metrics
# =====================================


def get_recent_recovery_metrics(user_id: int, limit: int = 7):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM daily_checkins
    WHERE user_id = ?
    ORDER BY checkin_date DESC, created_at DESC, id DESC
    LIMIT ?
    """,
        (user_id, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    avg_sleep = sum(row["sleep_hours"] for row in rows) / len(rows)
    avg_energy = sum(row["energy_level"] for row in rows) / len(rows)
    avg_soreness = sum(row["soreness_level"] for row in rows) / len(rows)

    valid_weights = [
        row["body_weight"]
        for row in rows
        if isinstance(row["body_weight"], int | float)
    ]
    latest_weight = valid_weights[0] if valid_weights else None
    oldest_weight = valid_weights[-1] if len(valid_weights) >= 2 else None
    weight_change = (
        round(latest_weight - oldest_weight, 1)
        if latest_weight is not None and oldest_weight is not None
        else None
    )

    return {
        "entries_analyzed": len(rows),
        "avg_sleep": round(avg_sleep, 1),
        "avg_energy": round(avg_energy, 1),
        "avg_soreness": round(avg_soreness, 1),
        "latest_weight": latest_weight,
        "weight_change": weight_change,
        "recent_notes": [row["notes"] for row in rows if row["notes"]],
    }


# =====================================
# Save Recovery Reports
# =====================================


def save_recovery_report(user_id: int, metrics, recommendation):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO recovery_reports (
        user_id,
        report_date,
        entries_analyzed,
        avg_sleep,
        avg_energy,
        avg_soreness,
        weight_change,
        recommendation
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            datetime.now().strftime("%Y-%m-%d"),
            metrics["entries_analyzed"],
            metrics["avg_sleep"],
            metrics["avg_energy"],
            metrics["avg_soreness"],
            metrics["weight_change"],
            recommendation,
        ),
    )

    conn.commit()
    conn.close()


# =====================================
# Get Recent Recovery Reports
# =====================================


def get_recent_recovery_reports(limit=5):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM recovery_reports
    ORDER BY created_at DESC
    LIMIT ?
    """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_recovery_checkin(user_id: int, target_date: str | None = None):
    checkin_date = target_date or date.today().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            checkin_date,
            body_weight,
            sleep_hours,
            energy_level,
            soreness_level,
            mood,
            notes,
            created_at
        FROM daily_checkins
        WHERE user_id = ?
          AND checkin_date = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (user_id, checkin_date),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "checkin_date": row["checkin_date"],
        "body_weight": row["body_weight"],
        "sleep_hours": row["sleep_hours"],
        "energy_level": row["energy_level"],
        "soreness_level": row["soreness_level"],
        "mood": row["mood"],
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


# =====================================
# Save Recovery Check-In
# =====================================


def save_recovery_checkin(
    user_id: int,
    body_weight: float | None,
    sleep_hours: float,
    energy_level: int,
    soreness_level: int,
    mood: str | None,
    notes: str | None,
    target_date: str | None = None,
) -> int:
    checkin_date = target_date or date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM daily_checkins
        WHERE user_id = ?
          AND checkin_date = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (user_id, checkin_date),
    )
    existing_row = cursor.fetchone()

    if existing_row is not None:
        checkin_id = int(existing_row["id"])
        cursor.execute(
            """
            UPDATE daily_checkins
            SET body_weight = ?,
                sleep_hours = ?,
                energy_level = ?,
                soreness_level = ?,
                mood = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                body_weight,
                sleep_hours,
                energy_level,
                soreness_level,
                mood,
                notes,
                checkin_id,
            ),
        )
    else:
        cursor.execute(
            """
            INSERT INTO daily_checkins (
                user_id,
                checkin_date,
                body_weight,
                sleep_hours,
                energy_level,
                soreness_level,
                mood,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                checkin_date,
                body_weight,
                sleep_hours,
                energy_level,
                soreness_level,
                mood,
                notes,
            ),
        )
        checkin_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return checkin_id
