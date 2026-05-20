from services.nutrition_service import (
    get_foods,
    add_food_entry,
    get_daily_nutrition,
    search_foods,
)

from services.workout_service import (
    search_exercises,
    create_workout_session,
    add_workout_set,
    get_recent_workouts,
)


from datetime import datetime

from database import get_connection, initialize_database
from services.recovery_service import get_recent_recovery_reports


def add_daily_checkin():
    conn = get_connection()
    cursor = conn.cursor()

    print("\n=== Daily Fitness Check-In ===\n")

    user_id = int(input("User ID: "))
    body_weight = float(input("Body weight: "))
    sleep_hours = float(input("Hours slept: "))
    energy_level = int(input("Energy level (1-10): "))
    soreness_level = int(input("Soreness level (1-10): "))
    mood = input("Mood: ")
    notes = input("Notes: ")

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
            datetime.now().strftime("%Y-%m-%d"),
            body_weight,
            sleep_hours,
            energy_level,
            soreness_level,
            mood,
            notes,
        ),
    )

    conn.commit()
    conn.close()

    print("\nCheck-in saved.\n")


def show_checkins():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM daily_checkins
    ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    print("\n=== Previous Check-Ins ===\n")

    for row in rows:
        print(f"""
Date: {row['checkin_date']}
Weight: {row['body_weight']}
Sleep: {row['sleep_hours']}
Energy: {row['energy_level']}
Soreness: {row['soreness_level']}
Mood: {row['mood']}
Notes: {row['notes']}
---------------------------
""")

    conn.close()


def analyze_recent_checkins():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM daily_checkins
    ORDER BY created_at DESC
    LIMIT 7
    """)

    rows = cursor.fetchall()
    conn.close()

    avg_sleep = sum(row["sleep_hours"] for row in rows) / len(rows)
    avg_energy = sum(row["energy_level"] for row in rows) / len(rows)
    avg_soreness = sum(row["soreness_level"] for row in rows) / len(rows)

    latest_weight = rows[0]["body_weight"]
    oldest_weight = rows[-1]["body_weight"]
    weight_change = latest_weight - oldest_weight

    print("\n=== Recent Check-In Analysis ===\n")


def show_recovery_reports():
    rows = get_recent_recovery_reports()

    if not rows:
        print("\nNo recovery reports found.\n")
        return

    print("\n=== Recent Recovery Reports ===\n")

    for row in rows:
        print(f"""
Date: {row['report_date']}
Entries analyzed: {row['entries_analyzed']}
Avg sleep: {row['avg_sleep']}
Avg energy: {row['avg_energy']}
Avg soreness: {row['avg_soreness']}
Weight change: {row['weight_change']} lbs

Recommendation:
{row['recommendation']}
---------------------------
""")


def show_foods():
    foods = get_foods()

    print("\n=== Available Foods ===\n")

    for food in foods:

        print(f"ID: {food['id']}")
        print(f"Name: {food['name']}")

        print("\nNutrients:")

        for nutrient_name, nutrient_data in food["nutrients"].items():

            print(
                f"- {nutrient_name}: "
                f"{nutrient_data['amount']} "
                f"{nutrient_data['unit']}"
            )

        print("\n---------------------------\n")


def search_for_food():
    search_term = input("Search food: ")

    results = search_foods(search_term)

    if not results:
        print("\nNo foods found.\n")
        return

    print("\n=== Search Results ===\n")

    for food in results:

        print(f"ID: {food['id']}")
        print(f"Name: {food['name']}")

        print("\nNutrients:")

        for nutrient_name, nutrient_data in food["nutrients"].items():

            print(
                f"- {nutrient_name}: "
                f"{nutrient_data['amount']} "
                f"{nutrient_data['unit']}"
            )

        print("\n---------------------------\n")


def show_daily_nutrition():
    user_id = int(input("User ID: "))
    entry_date = input("Date (YYYY-MM-DD): ")

    nutrition = get_daily_nutrition(user_id, entry_date)

    if not nutrition:
        print("\nNo nutrition data found.\n")
        return

    print("\n=== Daily Nutrition Totals ===\n")

    for nutrient_name, nutrient_data in nutrition.items():

        print(
            f"{nutrient_name}: "
            f"{nutrient_data['amount']} "
            f"{nutrient_data['unit']}"
        )

    print()


def log_food():
    user_id = int(input("User ID: "))

    search_term = input("Search food: ")

    results = search_foods(search_term)

    if not results:
        print("\nNo foods found.\n")
        return

    print("\n=== Search Results ===\n")

    for food in results:

        print(f"ID: {food['id']}")
        print(f"Name: {food['name']}")

        print("\nNutrients:")

        for nutrient_name, nutrient_data in food["nutrients"].items():

            print(
                f"- {nutrient_name}: "
                f"{nutrient_data['amount']} "
                f"{nutrient_data['unit']}"
            )

        print("\n---------------------------\n")

    food_id = int(input("Choose Food ID: "))

    grams = float(input("Grams consumed: "))

    add_food_entry(user_id, food_id, grams)

    print("\nFood logged successfully.\n")


def log_workout():
    user_id = int(input("User ID: "))
    workout_name = input("Workout name: ")
    duration_minutes = input("Duration minutes (optional): ")
    notes = input("Workout notes (optional): ")

    duration_minutes = int(duration_minutes) if duration_minutes else None
    notes = notes if notes else None

    session_id = create_workout_session(
        user_id=user_id,
        workout_name=workout_name,
        duration_minutes=duration_minutes,
        notes=notes,
    )

    print(f"\nWorkout session created. Session ID: {session_id}\n")

    while True:
        search_term = input("Search exercise or type 'done': ")

        if search_term.lower() == "done":
            break

        results = search_exercises(search_term)

        if not results:
            print("\nNo exercises found.\n")
            continue

        print("\n=== Exercise Results ===\n")

        for exercise in results:
            print(f"""
ID: {exercise['id']}
Name: {exercise['name']}
Muscle Group: {exercise['muscle_group']}
Movement Type: {exercise['movement_type']}
Equipment: {exercise['equipment']}
---------------------------
""")

        exercise_id = int(input("Choose Exercise ID: "))
        set_number = int(input("Set number: "))
        reps = int(input("Reps: "))
        weight = float(input("Weight: "))
        rir_input = input("RIR / reps in reserve (optional): ")

        rir = int(rir_input) if rir_input else None

        add_workout_set(
            workout_session_id=session_id,
            exercise_id=exercise_id,
            set_number=set_number,
            reps=reps,
            weight=weight,
            rir=rir,
        )

        print("\nSet logged.\n")

    print("\nWorkout complete.\n")


def show_recent_workouts():
    user_id = int(input("User ID: "))

    workouts = get_recent_workouts(user_id)

    if not workouts:
        print("\nNo workouts found.\n")
        return

    print("\n=== Recent Workouts ===\n")

    for workout in workouts:
        session = workout["session"]

        print(f"""
Workout: {session['workout_name']}
Date: {session['workout_date']}
Duration: {session['duration_minutes']}
Notes: {session['notes']}
""")

        for set_data in workout["sets"]:
            print(
                f"- {set_data['name']} | "
                f"Set {set_data['set_number']}: "
                f"{set_data['reps']} reps x {set_data['weight']} lbs"
                + (f" | RIR {set_data['rir']}" if set_data["rir"] is not None else "")
            )

        print("\n---------------------------\n")


if __name__ == "__main__":
    initialize_database()

while True:
    print("""
    1. Add Daily Check-In
    2. View Check-Ins
    3. Analyze Recent Check-Ins
    4. View Recovery Reports
    5. View Foods
    6. Log Food
    7. View Daily Nutrition
    8. Search Foods
    9. Log Workout
    10. View Recent Workouts
    11. Exit
    """)

    choice = input("Choose an option: ")

    if choice == "1":
        add_daily_checkin()

    elif choice == "2":
        show_checkins()

    elif choice == "3":
        analyze_recent_checkins()

    elif choice == "4":
        show_recovery_reports()

    elif choice == "5":
        show_foods()

    elif choice == "6":
        log_food()

    elif choice == "7":
        show_daily_nutrition()

    elif choice == "8":
        search_for_food()

    elif choice == "9":
        log_workout()

    elif choice == "10":
        show_recent_workouts()

    elif choice == "11":
        print("Goodbye.")
        break

    else:
        print("Invalid option.")
