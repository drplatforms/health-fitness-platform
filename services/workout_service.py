from database import get_connection


# -----------------------------
# Exercise Search
# -----------------------------

def search_exercises(search_term):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM exercises
    WHERE name LIKE ?
    ORDER BY name
    """, (f"%{search_term}%",))

    rows = cursor.fetchall()

    conn.close()

    return rows


# -----------------------------
# Get All Exercises
# -----------------------------

def get_exercises():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM exercises
    ORDER BY name
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# -----------------------------
# Create Workout Session
# -----------------------------

def create_workout_session(
    user_id,
    workout_name,
    duration_minutes,
    notes=None
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO workout_sessions (
        user_id,
        workout_name,
        duration_minutes,
        notes
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        workout_name,
        duration_minutes,
        notes
    ))

    session_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return session_id


# -----------------------------
# Add Workout Set
# -----------------------------

def add_workout_set(
    workout_session_id,
    exercise_id,
    set_number,
    reps,
    weight,
    rir=None
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO workout_sets (
        workout_session_id,
        exercise_id,
        set_number,
        reps,
        weight,
        rir
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        workout_session_id,
        exercise_id,
        set_number,
        reps,
        weight,
        rir
    ))

    conn.commit()
    conn.close()


# -----------------------------
# Get Recent Workouts
# -----------------------------

def get_recent_workouts(
    user_id,
    limit=5
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM workout_sessions
    WHERE user_id = ?
    ORDER BY workout_date DESC
    LIMIT ?
    """, (
        user_id,
        limit
    ))

    sessions = cursor.fetchall()

    workouts = []

    for session in sessions:

        cursor.execute("""
        SELECT
            ws.*,
            e.name
        FROM workout_sets ws
        JOIN exercises e
            ON ws.exercise_id = e.id
        WHERE ws.workout_session_id = ?
        ORDER BY ws.set_number
        """, (session["id"],))

        sets = cursor.fetchall()

        workouts.append({
            "session": session,
            "sets": sets
        })

    conn.close()

    return workouts