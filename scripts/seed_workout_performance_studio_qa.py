"""Compatibility entry point for the canonical realistic QA106 history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import database
from scripts.seed_realistic_longitudinal_qa_v2 import (
    CANONICAL_FOOD_NAMES,
    HISTORY_END,
    LEGACY_QA106_NAME,
    LEGACY_QA106_SCENARIO,
    PERSONA_BY_ID,
    seed_qa106_compatibility_in_connection,
)
from services.exercise_catalog_service import (
    seed_exercise_catalog,
    seed_exercise_prescription_measurements,
)
from services.food_normalization_service import ensure_starter_canonical_foods_seeded
from services.workout_plan_persistence_service import (
    ensure_workout_plan_persistence_tables,
)

PERFORMANCE_STUDIO_USER_ID = 106
PERFORMANCE_STUDIO_USER_NAME = LEGACY_QA106_NAME
PERFORMANCE_STUDIO_SCENARIO = LEGACY_QA106_SCENARIO
DEFAULT_END_DATE = HISTORY_END


@dataclass(frozen=True)
class SeededPerformanceStudioQA:
    user_id: int
    completed_workout_count: int
    actual_set_count: int
    first_session_date: str
    last_session_date: str


def _legacy_nutrient_name(nutrient_name: str) -> str:
    return {
        "Calories": "Calories",
        "Protein": "Protein",
        "Carbohydrate": "Carbohydrates",
        "Fat": "Fat",
    }.get(nutrient_name, nutrient_name)


def _ensure_compatibility_food_mirrors(conn) -> None:
    """Prepare current canonical logging mirrors for the legacy entry point.

    The v2 CLI never does this: it only verifies prerequisites. The compatibility
    wrapper retains the old script's bootstrap behavior so it remains runnable
    against a freshly initialized disposable database.
    """

    placeholders = ",".join("?" for _ in CANONICAL_FOOD_NAMES)
    canonical_rows = conn.execute(
        f"""
        SELECT id, display_name
        FROM canonical_foods
        WHERE active = 1
          AND display_name IN ({placeholders})
        """,
        CANONICAL_FOOD_NAMES,
    ).fetchall()
    found_names = {str(row["display_name"]) for row in canonical_rows}
    missing = sorted(set(CANONICAL_FOOD_NAMES) - found_names)
    if missing:
        raise RuntimeError(
            "Missing canonical foods required by QA106 compatibility: "
            + ", ".join(missing)
        )

    for canonical_row in canonical_rows:
        display_name = str(canonical_row["display_name"])
        legacy_name = f"Canonical: {display_name}"
        conn.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (legacy_name,))
        legacy_food_id = int(
            conn.execute(
                "SELECT id FROM foods WHERE name = ?",
                (legacy_name,),
            ).fetchone()["id"]
        )
        conn.execute(
            "DELETE FROM food_nutrients WHERE food_id = ?",
            (legacy_food_id,),
        )
        nutrient_rows = conn.execute(
            """
            SELECT nutrient_name, nutrient_unit, amount_per_100g
            FROM canonical_food_nutrients
            WHERE canonical_food_id = ?
            """,
            (int(canonical_row["id"]),),
        ).fetchall()
        for nutrient_row in nutrient_rows:
            legacy_nutrient_name = _legacy_nutrient_name(
                str(nutrient_row["nutrient_name"])
            )
            conn.execute(
                "INSERT OR IGNORE INTO nutrients (name, unit) VALUES (?, ?)",
                (legacy_nutrient_name, str(nutrient_row["nutrient_unit"])),
            )
            nutrient_id = int(
                conn.execute(
                    "SELECT id FROM nutrients WHERE name = ?",
                    (legacy_nutrient_name,),
                ).fetchone()["id"]
            )
            conn.execute(
                """
                INSERT INTO food_nutrients (
                    food_id,
                    nutrient_id,
                    amount_per_100g
                )
                VALUES (?, ?, ?)
                """,
                (
                    legacy_food_id,
                    nutrient_id,
                    float(nutrient_row["amount_per_100g"]),
                ),
            )


def seed_workout_performance_studio_qa(
    *,
    end_date: date = DEFAULT_END_DATE,
) -> SeededPerformanceStudioQA:
    """Seed only QA106 through the canonical v2 generator.

    This compatibility function keeps the historical import and command entry
    point. New three-persona database operations should use
    ``seed_realistic_longitudinal_qa_v2.py`` instead.
    """

    database.initialize_database()
    ensure_workout_plan_persistence_tables()
    ensure_starter_canonical_foods_seeded()
    seed_exercise_catalog()
    seed_exercise_prescription_measurements()

    conn = database.get_connection()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")
        _ensure_compatibility_food_mirrors(conn)
        result = seed_qa106_compatibility_in_connection(
            conn,
            end_date=end_date,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return SeededPerformanceStudioQA(
        user_id=int(result["user_id"]),
        completed_workout_count=int(result["completed_workout_count"]),
        actual_set_count=int(result["actual_set_count"]),
        first_session_date=str(result["first_session_date"]),
        last_session_date=str(result["last_session_date"]),
    )


if __name__ == "__main__":
    seeded = seed_workout_performance_studio_qa()
    print(
        f"Seeded {seeded.completed_workout_count} completed workouts for "
        f"{PERSONA_BY_ID[106].name} (user {seeded.user_id})."
    )
