from database import get_connection

# -----------------------------
# Save Health Report
# -----------------------------


def save_health_report(user_id, report_text, model_summary=None):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO health_reports (
        user_id,
        report_text,
        model_summary
    )
    VALUES (?, ?, ?)
    """,
        (user_id, report_text, model_summary),
    )

    conn.commit()
    conn.close()


# -----------------------------
# Get Latest Health Report
# -----------------------------


def get_latest_health_report(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM health_reports
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT 1
    """,
        (user_id,),
    )

    report = cursor.fetchone()

    conn.close()

    return report


# -----------------------------
# Get Health Report History
# -----------------------------


def get_health_report_history(user_id, limit=10):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM health_reports
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    """,
        (user_id, limit),
    )

    reports = cursor.fetchall()

    conn.close()

    return reports
