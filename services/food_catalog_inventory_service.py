from __future__ import annotations

import csv
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from services.usda_food_data_import_service import (
    GENERIC_FDC_DATA_TYPES,
    normalize_fdc_data_type_key,
)


@dataclass(frozen=True)
class FoodCatalogInventoryReport:
    database_path: str
    raw_count_by_source_name: dict[str, int]
    raw_count_by_data_type: dict[str, int]
    raw_count_by_food_category: dict[str, int]
    macro_coverage: dict[str, int]
    macro_coverage_by_data_type: dict[str, dict[str, int]]
    canonical_food_count: int
    canonical_source_link_count: int
    fdc_dir: str | None = None
    fdc_food_count_by_data_type: dict[str, int] = field(default_factory=dict)
    fdc_category_count_by_data_type: dict[str, dict[str, int]] = field(
        default_factory=dict
    )
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


def _macro_coverage_counts_by_data_type(
    conn,
) -> dict[str, dict[str, int]]:
    if conn is None or not _table_exists(conn, "raw_food_source_records"):
        return {}

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            COALESCE(data_type, '(missing)') AS data_type,
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
        GROUP BY COALESCE(data_type, '(missing)')
        ORDER BY data_type
        """
    )
    return {
        row["data_type"]: {
            "total": int(row["total"] or 0),
            "any_macro": int(row["any_macro"] or 0),
            "all_macros": int(row["all_macros"] or 0),
            "calories": int(row["calories"] or 0),
            "protein": int(row["protein"] or 0),
            "carbs": int(row["carbs"] or 0),
            "fat": int(row["fat"] or 0),
        }
        for row in cursor.fetchall()
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


def _wweia_category_description_by_code(fdc_dir: Path) -> dict[str, str]:
    rows = _read_csv_rows(fdc_dir / "wweia_food_category.csv")
    return {
        str(row.get("wweia_food_category_code", "")).strip(): str(
            row.get("wweia_food_category_description", "")
        ).strip()
        for row in rows
        if str(row.get("wweia_food_category_code", "")).strip()
    }


def _survey_category_by_fdc_id(
    fdc_dir: Path,
    selected_fdc_ids: set[str],
) -> dict[str, str]:
    survey_path = fdc_dir / "survey_fndds_food.csv"
    if not survey_path.exists() or not selected_fdc_ids:
        return {}

    category_by_code = _wweia_category_description_by_code(fdc_dir)
    category_by_fdc_id: dict[str, str] = {}
    with survey_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            fdc_id = str(row.get("fdc_id", "")).strip()
            if fdc_id not in selected_fdc_ids:
                continue
            category_number = str(row.get("wweia_category_number", "")).strip()
            category = category_by_code.get(category_number)
            if category:
                category_by_fdc_id[fdc_id] = category
    return category_by_fdc_id


def _fdc_counts(
    fdc_dir: Path,
) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    food_path = fdc_dir / "food.csv"
    category_counters = {data_type: Counter() for data_type in GENERIC_FDC_DATA_TYPES}
    if not food_path.exists():
        return {}, {data_type: {} for data_type in GENERIC_FDC_DATA_TYPES}

    category_by_id = _category_description_by_id(fdc_dir)
    data_type_counter: Counter[str] = Counter()
    survey_fdc_ids: list[str] = []

    with food_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_data_type = str(row.get("data_type", "")).strip()
            data_type = normalize_fdc_data_type_key(source_data_type) or "(missing)"
            data_type_counter[data_type] += 1
            if data_type in {"foundation_food", "sr_legacy_food"}:
                category_id = str(row.get("food_category_id", "")).strip()
                category = (
                    category_by_id.get(category_id)
                    or str(row.get("food_category", "")).strip()
                    or "(missing)"
                )
                category_counters[data_type][category] += 1
            elif data_type == "survey_fndds_food":
                survey_fdc_ids.append(str(row.get("fdc_id", "")).strip())

    survey_category_by_fdc_id = _survey_category_by_fdc_id(
        fdc_dir,
        set(survey_fdc_ids),
    )
    for fdc_id in survey_fdc_ids:
        category_counters["survey_fndds_food"][
            survey_category_by_fdc_id.get(fdc_id, "(missing)")
        ] += 1

    return dict(data_type_counter), {
        data_type: dict(category_counters[data_type])
        for data_type in GENERIC_FDC_DATA_TYPES
    }


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
    macro_coverage_by_data_type = _macro_coverage_counts_by_data_type(conn)
    fdc_food_count_by_data_type: dict[str, int] = {}
    fdc_category_count_by_data_type: dict[str, dict[str, int]] = {
        data_type: {} for data_type in GENERIC_FDC_DATA_TYPES
    }
    fdc_foundation_count_by_category: dict[str, int] = {}
    notes: list[str] = []

    if fdc_dir is not None:
        fdc_path = Path(fdc_dir)
        fdc_food_count_by_data_type, fdc_category_count_by_data_type = _fdc_counts(
            fdc_path
        )
        fdc_foundation_count_by_category = fdc_category_count_by_data_type[
            "foundation_food"
        ]
        generic_fdc_count = sum(
            fdc_food_count_by_data_type.get(data_type, 0)
            for data_type in GENERIC_FDC_DATA_TYPES
        )
        if macro_coverage["total"] == 0 and generic_fdc_count > 0:
            notes.append(
                "FDC directory contains generic USDA rows, but the database has no "
                "raw_food_source_records. Import the generic source profile before "
                "source-specific review or promotion."
            )
        else:
            for data_type in GENERIC_FDC_DATA_TYPES:
                if (
                    fdc_food_count_by_data_type.get(data_type, 0) > 0
                    and raw_count_by_data_type.get(data_type, 0) == 0
                ):
                    notes.append(
                        f"FDC directory contains {data_type} rows, but the database "
                        f"inventory has no imported {data_type} raw rows."
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
        macro_coverage_by_data_type=macro_coverage_by_data_type,
        canonical_food_count=canonical_food_count,
        canonical_source_link_count=canonical_source_link_count,
        fdc_dir=str(Path(fdc_dir).resolve()) if fdc_dir is not None else None,
        fdc_food_count_by_data_type=fdc_food_count_by_data_type,
        fdc_category_count_by_data_type=fdc_category_count_by_data_type,
        fdc_foundation_count_by_category=fdc_foundation_count_by_category,
        notes=notes,
    )
