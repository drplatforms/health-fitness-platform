from database import get_connection
from datetime import datetime

# -----------------------------
# Get All Foods
# -----------------------------


def get_foods():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM foods
    ORDER BY name
    """)

    foods = cursor.fetchall()

    results = []

    for food in foods:

        cursor.execute(
            """
        SELECT
            nutrients.name,
            nutrients.unit,
            food_nutrients.amount_per_100g

        FROM food_nutrients

        JOIN nutrients
            ON food_nutrients.nutrient_id = nutrients.id

        WHERE food_nutrients.food_id = ?
        """,
            (food["id"],),
        )

        nutrients_data = cursor.fetchall()

        nutrient_map = {}

        for nutrient in nutrients_data:
            nutrient_map[nutrient["name"]] = {
                "amount": nutrient["amount_per_100g"],
                "unit": nutrient["unit"],
            }

        results.append(
            {"id": food["id"], "name": food["name"], "nutrients": nutrient_map}
        )

    conn.close()

    return results


# -----------------------------
# Search Foods
# -----------------------------


def search_foods(search_term, limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM foods
    WHERE name LIKE ?
    ORDER BY name
    LIMIT ?
    """,
        (f"%{search_term}%", limit),
    )

    foods = cursor.fetchall()

    results = []

    for food in foods:

        cursor.execute(
            """
        SELECT
            nutrients.name,
            nutrients.unit,
            food_nutrients.amount_per_100g

        FROM food_nutrients

        JOIN nutrients
            ON food_nutrients.nutrient_id = nutrients.id

        WHERE food_nutrients.food_id = ?
        """,
            (food["id"],),
        )

        nutrients_data = cursor.fetchall()

        nutrient_map = {}

        for nutrient in nutrients_data:
            nutrient_map[nutrient["name"]] = {
                "amount": nutrient["amount_per_100g"],
                "unit": nutrient["unit"],
            }

        results.append(
            {"id": food["id"], "name": food["name"], "nutrients": nutrient_map}
        )

    conn.close()

    return results


# -----------------------------
# Add Food Entry
# -----------------------------


def add_food_entry(user_id, food_id, grams):
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
    INSERT INTO food_entries (
        user_id,
        food_id,
        grams,
        entry_date
    )
    VALUES (?, ?, ?, ?)
    """,
        (user_id, food_id, grams, today),
    )

    conn.commit()
    conn.close()


# -----------------------------
# Daily Nutrition Aggregation
# -----------------------------


def get_daily_nutrition(user_id, entry_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT
        nutrients.name,
        nutrients.unit,

        SUM(
            food_nutrients.amount_per_100g
            * food_entries.grams / 100.0
        ) AS total_amount

    FROM food_entries

    JOIN food_nutrients
        ON food_entries.food_id = food_nutrients.food_id

    JOIN nutrients
        ON food_nutrients.nutrient_id = nutrients.id

    WHERE
        food_entries.user_id = ?
        AND food_entries.entry_date = ?

    GROUP BY nutrients.id

    ORDER BY nutrients.name
    """,
        (user_id, entry_date),
    )

    rows = cursor.fetchall()

    conn.close()

    nutrition_totals = {}

    for row in rows:
        nutrition_totals[row["name"]] = {
            "amount": round(row["total_amount"], 1),
            "unit": row["unit"],
        }

    return nutrition_totals


# -----------------------------
# Nutrition Analysis
# -----------------------------


def get_nutrition_analysis(user_id):

    today = datetime.now().strftime("%Y-%m-%d")

    nutrition = get_daily_nutrition(user_id, today)

    return nutrition
