from datetime import date, datetime

from database import get_connection

RECOVERY_SCALE_MIN = 1
RECOVERY_SCALE_MAX = 5
PAIN_CONCERN_VALUES = {"none", "mild", "significant"}
PAIN_AREA_VALUES = {
    "neck",
    "shoulder",
    "elbow",
    "wrist_hand",
    "upper_back",
    "lower_back",
    "hip",
    "knee",
    "ankle_foot",
    "other",
}

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
        "latest_sleep_quality": rows[0]["sleep_quality"],
        "latest_stress_level": rows[0]["stress_level"],
        "latest_training_motivation": rows[0]["training_motivation"],
        "latest_pain_concern": rows[0]["pain_concern"],
        "latest_pain_area": rows[0]["pain_area"],
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
            sleep_quality,
            energy_level,
            soreness_level,
            stress_level,
            training_motivation,
            pain_concern,
            pain_area,
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

    return _checkin_from_row(row)


def get_recent_recovery_checkins(user_id: int, limit: int = 7) -> list[dict]:
    resolved_limit = max(1, min(int(limit), 30))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            checkin.id,
            checkin.user_id,
            checkin.checkin_date,
            checkin.body_weight,
            checkin.sleep_hours,
            checkin.sleep_quality,
            checkin.energy_level,
            checkin.soreness_level,
            checkin.stress_level,
            checkin.training_motivation,
            checkin.pain_concern,
            checkin.pain_area,
            checkin.mood,
            checkin.notes,
            checkin.created_at
        FROM daily_checkins AS checkin
        WHERE checkin.user_id = ?
          AND checkin.id = (
              SELECT latest.id
              FROM daily_checkins AS latest
              WHERE latest.user_id = checkin.user_id
                AND latest.checkin_date = checkin.checkin_date
              ORDER BY latest.created_at DESC, latest.id DESC
              LIMIT 1
          )
        ORDER BY checkin.checkin_date DESC, checkin.created_at DESC, checkin.id DESC
        LIMIT ?
        """,
        (user_id, resolved_limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [_checkin_from_row(row) for row in rows]


def _checkin_from_row(row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "checkin_date": row["checkin_date"],
        "body_weight": row["body_weight"],
        "sleep_hours": row["sleep_hours"],
        "sleep_quality": row["sleep_quality"],
        "energy_level": row["energy_level"],
        "soreness_level": row["soreness_level"],
        "stress_level": row["stress_level"],
        "training_motivation": row["training_motivation"],
        "pain_concern": row["pain_concern"],
        "pain_area": row["pain_area"],
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
    sleep_quality: int | None = None,
    stress_level: int | None = None,
    training_motivation: int | None = None,
    pain_concern: str | None = None,
    pain_area: str | None = None,
) -> int:
    _validate_optional_scale("sleep_quality", sleep_quality)
    _validate_optional_scale("stress_level", stress_level)
    _validate_optional_scale("training_motivation", training_motivation)
    pain_concern = _normalize_optional_token(pain_concern)
    pain_area = _normalize_optional_token(pain_area)
    if pain_concern is not None and pain_concern not in PAIN_CONCERN_VALUES:
        raise ValueError("pain_concern must be none, mild, or significant.")
    if pain_area is not None and pain_area not in PAIN_AREA_VALUES:
        raise ValueError("pain_area contains an unsupported value.")
    if pain_area is not None and pain_concern not in {"mild", "significant"}:
        raise ValueError("pain_area requires a mild or significant pain_concern.")

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
                sleep_quality = ?,
                energy_level = ?,
                soreness_level = ?,
                stress_level = ?,
                training_motivation = ?,
                pain_concern = ?,
                pain_area = ?,
                mood = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                body_weight,
                sleep_hours,
                sleep_quality,
                energy_level,
                soreness_level,
                stress_level,
                training_motivation,
                pain_concern,
                pain_area,
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
                sleep_quality,
                energy_level,
                soreness_level,
                stress_level,
                training_motivation,
                pain_concern,
                pain_area,
                mood,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                checkin_date,
                body_weight,
                sleep_hours,
                sleep_quality,
                energy_level,
                soreness_level,
                stress_level,
                training_motivation,
                pain_concern,
                pain_area,
                mood,
                notes,
            ),
        )
        checkin_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return checkin_id


def _validate_optional_scale(name: str, value: int | None) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer when present.")
    if value < RECOVERY_SCALE_MIN or value > RECOVERY_SCALE_MAX:
        raise ValueError(
            f"{name} must be between {RECOVERY_SCALE_MIN} and {RECOVERY_SCALE_MAX}."
        )


def _normalize_optional_token(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return normalized or None
