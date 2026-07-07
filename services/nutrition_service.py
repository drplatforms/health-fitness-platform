from __future__ import annotations

from datetime import date, datetime
from typing import Any

from database import get_connection
from models.food_normalization_models import CanonicalFood, CanonicalFoodNutrient
from services.food_normalization_service import (
    get_canonical_food,
    get_nutrients_for_canonical_food,
)

# -----------------------------
# Canonical Food Logging Errors
# -----------------------------


class CanonicalFoodLoggingError(ValueError):
    """Base class for public-safe canonical food logging failures."""


class CanonicalFoodNotFoundError(CanonicalFoodLoggingError):
    """Raised when a canonical food ID does not exist."""


class CanonicalFoodInactiveError(CanonicalFoodLoggingError):
    """Raised when a canonical food exists but is not active for logging."""


class CanonicalFoodNutrientsUnavailableError(CanonicalFoodLoggingError):
    """Raised when a canonical food has no usable nutrient rows."""


def _today_iso() -> str:
    return date.today().isoformat()


def _resolve_entry_date(entry_date: str | None = None) -> str:
    if entry_date is None:
        return _today_iso()
    try:
        return date.fromisoformat(entry_date).isoformat()
    except ValueError as exc:
        raise ValueError("entry_date must use YYYY-MM-DD format.") from exc


def _validate_positive_grams(grams: float) -> float:
    try:
        resolved_grams = float(grams)
    except (TypeError, ValueError) as exc:
        raise ValueError("grams must be a positive number.") from exc

    if resolved_grams <= 0:
        raise ValueError("grams must be greater than 0.")
    return resolved_grams


def _optional_text(value: str | None) -> str | None:
    normalized = " ".join(str(value or "").strip().split())
    return normalized or None


def _legacy_canonical_food_name(canonical_food: CanonicalFood) -> str:
    return f"Canonical: {canonical_food.display_name}"


def _legacy_nutrient_name(nutrient_name: str) -> str:
    normalized = " ".join(nutrient_name.strip().lower().replace("_", " ").split())
    legacy_names = {
        "calorie": "Calories",
        "calories": "Calories",
        "energy": "Calories",
        "protein": "Protein",
        "carbohydrate": "Carbohydrates",
        "carbohydrates": "Carbohydrates",
        "carbs": "Carbohydrates",
        "total carbohydrate": "Carbohydrates",
        "fat": "Fat",
        "total fat": "Fat",
        "fiber": "Fiber",
        "sugar": "Sugar",
        "sodium": "Sodium",
        "potassium": "Potassium",
        "magnesium": "Magnesium",
        "calcium": "Calcium",
        "iron": "Iron",
        "vitamin c": "Vitamin C",
        "vitamin d": "Vitamin D",
        "vitamin b12": "Vitamin B12",
        "zinc": "Zinc",
    }
    return legacy_names.get(normalized, nutrient_name.strip())


def _get_or_create_legacy_food_id(food_name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (food_name,))
    cursor.execute("SELECT id FROM foods WHERE name = ?", (food_name,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return int(row["id"])


def _get_or_create_nutrient_id(nutrient_name: str, nutrient_unit: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    nutrient_id = _get_or_create_nutrient_id_with_cursor(
        cursor,
        nutrient_name,
        nutrient_unit,
    )
    conn.commit()
    conn.close()
    return nutrient_id


def _get_or_create_nutrient_id_with_cursor(
    cursor,
    nutrient_name: str,
    nutrient_unit: str,
) -> int:
    legacy_name = _legacy_nutrient_name(nutrient_name)
    cursor.execute(
        """
        INSERT OR IGNORE INTO nutrients (name, unit)
        VALUES (?, ?)
        """,
        (legacy_name, nutrient_unit),
    )
    cursor.execute("SELECT id FROM nutrients WHERE name = ?", (legacy_name,))
    row = cursor.fetchone()
    return int(row["id"])


def _sync_legacy_food_nutrients(
    legacy_food_id: int,
    canonical_nutrients: list[CanonicalFoodNutrient],
) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_nutrients WHERE food_id = ?", (legacy_food_id,))

    for nutrient in canonical_nutrients:
        nutrient_id = _get_or_create_nutrient_id_with_cursor(
            cursor,
            nutrient.nutrient_name,
            nutrient.nutrient_unit,
        )
        cursor.execute(
            """
            INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
            VALUES (?, ?, ?)
            """,
            (legacy_food_id, nutrient_id, nutrient.amount_per_100g),
        )

    conn.commit()
    conn.close()


def _nutrient_summary_for_logged_grams(
    canonical_nutrients: list[CanonicalFoodNutrient],
    grams: float,
    *,
    precision: int = 3,
) -> dict[str, float]:
    summary_keys = {
        "calories": "calories",
        "calorie": "calories",
        "energy": "calories",
        "protein": "protein_g",
        "carbohydrate": "carbohydrate_g",
        "carbohydrates": "carbohydrate_g",
        "carbs": "carbohydrate_g",
        "total carbohydrate": "carbohydrate_g",
        "fat": "fat_g",
        "total fat": "fat_g",
    }

    summary: dict[str, float] = {}
    for nutrient in canonical_nutrients:
        key = summary_keys.get(nutrient.nutrient_name.strip().lower())
        if key is None:
            continue
        summary[key] = round(
            float(nutrient.amount_per_100g) * grams / 100.0,
            precision,
        )
    return summary


def _canonical_food_log_response(
    *,
    food_entry_id: int,
    canonical_food: CanonicalFood,
    grams: float,
    logged_date: str,
    canonical_nutrients: list[CanonicalFoodNutrient],
    nutrient_summary: dict[str, float] | None = None,
    meal_type: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "logged_food_entry_id": food_entry_id,
        "canonical_food_id": canonical_food.id,
        "display_name": canonical_food.display_name,
        "grams": grams,
        "logged_date": logged_date,
    }

    if nutrient_summary is None:
        nutrient_summary = _nutrient_summary_for_logged_grams(
            canonical_nutrients,
            grams,
        )
    if nutrient_summary:
        response["nutrient_summary"] = nutrient_summary
    if meal_type is not None:
        response["meal_type"] = meal_type
    if notes is not None:
        response["notes"] = notes

    return response


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


def add_food_entry(
    user_id,
    food_id,
    grams,
    entry_date: str | None = None,
    *,
    canonical_food_id: int | None = None,
    meal_type: str | None = None,
    notes: str | None = None,
    calories: float | None = None,
    protein_g: float | None = None,
    carbs_g: float | None = None,
    fat_g: float | None = None,
) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    resolved_grams = _validate_positive_grams(grams)
    resolved_date = _resolve_entry_date(entry_date)

    cursor.execute(
        """
    INSERT INTO food_entries (
        user_id,
        food_id,
        grams,
        canonical_food_id,
        meal_type,
        notes,
        calories,
        protein_g,
        carbs_g,
        fat_g,
        entry_date
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            food_id,
            resolved_grams,
            canonical_food_id,
            _optional_text(meal_type),
            _optional_text(notes),
            calories,
            protein_g,
            carbs_g,
            fat_g,
            resolved_date,
        ),
    )
    entry_id = int(cursor.lastrowid)

    conn.commit()
    conn.close()

    return entry_id


def add_canonical_food_entry(
    user_id: int,
    canonical_food_id: int,
    grams: float,
    entry_date: str | None = None,
    meal_type: str | None = None,
    notes: str | None = None,
    *,
    nutrient_summary_precision: int = 3,
) -> dict[str, Any]:
    """Log an app-facing canonical food through backend-owned write-through.

    Canonical foods are mirrored into the existing legacy food/nutrient tables so
    existing nutrition actuals and target-vs-actual services keep reading the
    same food_entries path. Missing canonical nutrients are not invented or
    coerced to zero; only existing canonical nutrient rows are mirrored.
    """

    resolved_grams = _validate_positive_grams(grams)
    resolved_date = _resolve_entry_date(entry_date)
    canonical_food = get_canonical_food(canonical_food_id)

    if canonical_food is None:
        raise CanonicalFoodNotFoundError("Canonical food not found.")
    if not canonical_food.active:
        raise CanonicalFoodInactiveError("Canonical food is inactive.")

    canonical_nutrients = get_nutrients_for_canonical_food(canonical_food_id)
    if not canonical_nutrients:
        raise CanonicalFoodNutrientsUnavailableError(
            "Canonical food has no nutrient rows available for logging."
        )

    legacy_food_id = _get_or_create_legacy_food_id(
        _legacy_canonical_food_name(canonical_food)
    )
    _sync_legacy_food_nutrients(legacy_food_id, canonical_nutrients)
    nutrient_summary = _nutrient_summary_for_logged_grams(
        canonical_nutrients,
        resolved_grams,
        precision=nutrient_summary_precision,
    )
    food_entry_id = add_food_entry(
        user_id=user_id,
        food_id=legacy_food_id,
        grams=resolved_grams,
        entry_date=resolved_date,
        canonical_food_id=canonical_food.id,
        meal_type=meal_type,
        notes=notes,
        calories=nutrient_summary.get("calories"),
        protein_g=nutrient_summary.get("protein_g"),
        carbs_g=nutrient_summary.get("carbohydrate_g"),
        fat_g=nutrient_summary.get("fat_g"),
    )

    return _canonical_food_log_response(
        food_entry_id=food_entry_id,
        canonical_food=canonical_food,
        grams=resolved_grams,
        logged_date=resolved_date,
        canonical_nutrients=canonical_nutrients,
        nutrient_summary=nutrient_summary,
        meal_type=_optional_text(meal_type),
        notes=_optional_text(notes),
    )


def get_daily_canonical_food_macro_totals(
    user_id: int,
    entry_date: str,
) -> dict[str, float | int | None]:
    resolved_date = _resolve_entry_date(entry_date)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS entry_count,
            SUM(calories) AS total_calories,
            SUM(protein_g) AS total_protein_g,
            SUM(carbs_g) AS total_carbs_g,
            SUM(fat_g) AS total_fat_g,
            COUNT(calories) AS calories_count,
            COUNT(protein_g) AS protein_count,
            COUNT(carbs_g) AS carbs_count,
            COUNT(fat_g) AS fat_count
        FROM food_entries
        WHERE user_id = ?
          AND entry_date = ?
          AND canonical_food_id IS NOT NULL
        """,
        (user_id, resolved_date),
    )
    row = cursor.fetchone()
    conn.close()

    entry_count = int(row["entry_count"] or 0)

    def _resolve_total(total_key: str, count_key: str) -> float | None:
        known_count = int(row[count_key] or 0)
        if entry_count == 0:
            return 0.0
        if known_count == 0:
            return None
        return round(float(row[total_key]), 3)

    return {
        "entry_count": entry_count,
        "calories": _resolve_total("total_calories", "calories_count"),
        "protein_g": _resolve_total("total_protein_g", "protein_count"),
        "carbs_g": _resolve_total("total_carbs_g", "carbs_count"),
        "fat_g": _resolve_total("total_fat_g", "fat_count"),
    }


def get_daily_canonical_food_logs(
    user_id: int,
    entry_date: str,
) -> list[dict[str, Any]]:
    resolved_date = _resolve_entry_date(entry_date)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            food_entries.id AS entry_id,
            food_entries.canonical_food_id,
            COALESCE(
                canonical_foods.display_name,
                REPLACE(foods.name, 'Canonical: ', '')
            ) AS food_name,
            food_entries.grams,
            food_entries.meal_type,
            food_entries.calories,
            food_entries.protein_g,
            food_entries.carbs_g,
            food_entries.fat_g
        FROM food_entries
        LEFT JOIN canonical_foods
            ON canonical_foods.id = food_entries.canonical_food_id
        LEFT JOIN foods
            ON foods.id = food_entries.food_id
        WHERE food_entries.user_id = ?
          AND food_entries.entry_date = ?
          AND food_entries.canonical_food_id IS NOT NULL
        ORDER BY food_entries.created_at, food_entries.id
        """,
        (user_id, resolved_date),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "entry_id": int(row["entry_id"]),
            "canonical_food_id": int(row["canonical_food_id"]),
            "food_name": row["food_name"],
            "grams": row["grams"],
            "meal_type": row["meal_type"],
            "calories": row["calories"],
            "protein_g": row["protein_g"],
            "carbs_g": row["carbs_g"],
            "fat_g": row["fat_g"],
        }
        for row in rows
    ]


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
