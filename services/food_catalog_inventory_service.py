from __future__ import annotations

import csv
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FoodCatalogInventoryReport:
    database_path: str
    raw_count_by_source_name: dict[str, int]
    raw_count_by_data_type: dict[str, int]
    raw_count_by_food_category: dict[str, int]
    macro_coverage: dict[str, int]
    canonical_food_count: int
    canonical_source_link_count: int
    fdc_dir: str | None = None
    fdc_food_count_by_data_type: dict[str, int] = field(default_factory=dict)
    fdc_foundation_count_by_category: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _connect_readonly(database_path: str):
    path = Path(database_path)
    if not path.exists():
        return None
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn, table_name: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def _count_by_column(conn, table_name: str, column_name: str) -> dict[str, int]:
    if conn is None or not _table_exists(conn, table_name):
        return {}

    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT COALESCE({column_name}, '(missing)') AS value, COUNT(*) AS count
        FROM {table_name}
        GROUP BY COALESCE({column_name}, '(missing)')
        ORDER BY count DESC, value
        """
    )
    rows = cursor.fetchall()
    return {row["value"]: int(row["count"]) for row in rows}


def _scalar_count(conn, table_name: str) -> int:
    if conn is None or not _table_exists(conn, table_name):
        return 0

    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) AS count FROM {table_name}")
    return int(cursor.fetchone()["count"])


def _macro_coverage_counts(conn) -> dict[str, int]:
    if conn is None or not _table_exists(conn, "raw_food_source_records"):
        return {
            "total": 0,
            "any_macro": 0,
            "all_macros": 0,
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
        }

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(
                CASE
                    WHEN calories_per_100g IS NOT NULL
                      OR protein_g_per_100g IS NOT NULL
                      OR carbs_g_per_100g IS NOT NULL
                      OR fat_g_per_100g IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) AS any_macro,
            SUM(
                CASE
                    WHEN calories_per_100g IS NOT NULL
                     AND protein_g_per_100g IS NOT NULL
                     AND carbs_g_per_100g IS NOT NULL
                     AND fat_g_per_100g IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) AS all_macros,
            SUM(CASE WHEN calories_per_100g IS NOT NULL THEN 1 ELSE 0 END)
                AS calories,
            SUM(CASE WHEN protein_g_per_100g IS NOT NULL THEN 1 ELSE 0 END)
                AS protein,
            SUM(CASE WHEN carbs_g_per_100g IS NOT NULL THEN 1 ELSE 0 END)
                AS carbs,
            SUM(CASE WHEN fat_g_per_100g IS NOT NULL THEN 1 ELSE 0 END)
                AS fat
        FROM raw_food_source_records
        """
    )
    row = cursor.fetchone()
    return {
        "total": int(row["total"] or 0),
        "any_macro": int(row["any_macro"] or 0),
        "all_macros": int(row["all_macros"] or 0),
        "calories": int(row["calories"] or 0),
        "protein": int(row["protein"] or 0),
        "carbs": int(row["carbs"] or 0),
        "fat": int(row["fat"] or 0),
    }


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _category_description_by_id(fdc_dir: Path) -> dict[str, str]:
    rows = _read_csv_rows(fdc_dir / "food_category.csv")
    return {
        str(row.get("id", "")).strip(): str(row.get("description", "")).strip()
        for row in rows
        if str(row.get("id", "")).strip()
    }


def _fdc_counts(fdc_dir: Path) -> tuple[dict[str, int], dict[str, int]]:
    food_rows = _read_csv_rows(fdc_dir / "food.csv")
    category_by_id = _category_description_by_id(fdc_dir)
    data_type_counter: Counter[str] = Counter()
    foundation_category_counter: Counter[str] = Counter()

    for row in food_rows:
        data_type = str(row.get("data_type", "")).strip() or "(missing)"
        data_type_counter[data_type] += 1
        normalized_data_type = data_type.casefold().replace(" ", "_")
        if normalized_data_type not in {"foundation_food", "foundation_foods"}:
            continue

        category_id = str(row.get("food_category_id", "")).strip()
        category = (
            category_by_id.get(category_id)
            or str(row.get("food_category", "")).strip()
            or "(missing)"
        )
        foundation_category_counter[category] += 1

    return dict(data_type_counter), dict(foundation_category_counter)


def build_food_catalog_inventory_report(
    *,
    database_path: str,
    fdc_dir: str | Path | None = None,
) -> FoodCatalogInventoryReport:
    conn = _connect_readonly(database_path)

    raw_count_by_source_name = _count_by_column(
        conn,
        "raw_food_source_records",
        "source_name",
    )
    raw_count_by_data_type = _count_by_column(
        conn,
        "raw_food_source_records",
        "data_type",
    )
    raw_count_by_food_category = _count_by_column(
        conn,
        "raw_food_source_records",
        "food_category",
    )
    macro_coverage = _macro_coverage_counts(conn)
    fdc_food_count_by_data_type: dict[str, int] = {}
    fdc_foundation_count_by_category: dict[str, int] = {}
    notes: list[str] = []

    if fdc_dir is not None:
        fdc_path = Path(fdc_dir)
        fdc_food_count_by_data_type, fdc_foundation_count_by_category = _fdc_counts(
            fdc_path
        )
        foundation_count = sum(fdc_foundation_count_by_category.values())
        if macro_coverage["total"] == 0 and foundation_count > 0:
            notes.append(
                "FDC directory contains foundation_food rows, but the database has "
                "no raw_food_source_records. Import Foundation rows before bulk "
                "promotion."
            )
        elif raw_count_by_data_type.get("foundation_food", 0) == 0 and foundation_count:
            notes.append(
                "FDC directory contains foundation_food rows, but the database "
                "inventory has no imported foundation_food raw rows."
            )

    canonical_food_count = _scalar_count(conn, "canonical_foods")
    canonical_source_link_count = _scalar_count(conn, "food_source_links")
    if conn is not None:
        conn.close()

    return FoodCatalogInventoryReport(
        database_path=database_path,
        raw_count_by_source_name=raw_count_by_source_name,
        raw_count_by_data_type=raw_count_by_data_type,
        raw_count_by_food_category=raw_count_by_food_category,
        macro_coverage=macro_coverage,
        canonical_food_count=canonical_food_count,
        canonical_source_link_count=canonical_source_link_count,
        fdc_dir=str(Path(fdc_dir).resolve()) if fdc_dir is not None else None,
        fdc_food_count_by_data_type=fdc_food_count_by_data_type,
        fdc_foundation_count_by_category=fdc_foundation_count_by_category,
        notes=notes,
    )
