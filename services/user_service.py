from database import get_connection


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM users
    WHERE id = ?
    """,
        (user_id,),
    )

    row = cursor.fetchone()

    conn.close()

    return row


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM users
    ORDER BY name
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows
