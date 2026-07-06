from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import database
from services.food_normalization_service import ensure_food_normalization_tables
from services.usda_food_data_import_service import (
    import_usda_food_csv,
    import_usda_food_fdc_directory,
)

FIXTURE_PATH = Path("tests/fixtures/usda/sample_foods.csv")
FDC_FIXTURE_DIR = Path("tests/fixtures/usda/fdc_csv_minimal")
FDC_LOGGABLE_FIXTURE_DIR = Path("tests/fixtures/usda/fdc_csv_loggable_filter")


def _seed_test_db(tmp_path: Path, monkeypatch) -> Path:
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    return db_path


def test_raw_food_source_schema_expands_for_usda_metadata(
    tmp_path, monkeypatch
) -> None:
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE raw_food_source_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            source_record_id TEXT NOT NULL,
            raw_description TEXT NOT NULL,
            brand_name TEXT,
            food_category TEXT,
            source_payload_json TEXT,
            license TEXT,
            source_url TEXT,
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_name, source_record_id)
        )
        """
    )
    conn.commit()
    conn.close()

    ensure_food_normalization_tables()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(raw_food_source_records)")
    }
    conn.close()

    assert {
        "data_type",
        "gtin_upc",
        "serving_size",
        "serving_size_unit",
        "calories_per_100g",
        "protein_g_per_100g",
        "carbs_g_per_100g",
        "fat_g_per_100g",
        "import_batch",
    } <= columns


def test_importer_reads_fixture_and_preserves_fdc_id(tmp_path, monkeypatch) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    summary = import_usda_food_csv(FIXTURE_PATH, import_batch="fixture_batch_v0")

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 4
    assert summary.inserted_count == 4
    assert summary.updated_count == 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_name = ? AND source_record_id = ?
        """,
        ("USDA FoodData Central", "533294"),
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["raw_description"] == "Tuna, canned in water"
    assert row["data_type"] == "Branded"
    assert row["brand_name"] == "Sample Foods LLC"
    assert row["gtin_upc"] == "012345678905"
    assert row["serving_size"] == 56
    assert row["serving_size_unit"] == "g"
    assert row["calories_per_100g"] == 116
    assert row["protein_g_per_100g"] == 25.5
    assert row["carbs_g_per_100g"] == 0
    assert row["fat_g_per_100g"] == 0.8
    assert row["import_batch"] == "fixture_batch_v0"


def test_importer_handles_missing_optional_fields_safely(tmp_path, monkeypatch) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    import_usda_food_csv(FIXTURE_PATH)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("2710815",),
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["brand_name"] is None
    assert row["gtin_upc"] is None
    assert row["serving_size"] is None
    assert row["serving_size_unit"] is None


def test_fdc_directory_import_joins_macro_files_and_preserves_fdc_id(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    summary = import_usda_food_fdc_directory(
        FDC_FIXTURE_DIR,
        import_batch="fdc_fixture_batch_v0",
        include_data_types=["Foundation Foods", "Branded"],
    )

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 3
    assert summary.inserted_count == 3
    assert summary.updated_count == 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    tuna_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_name = ? AND source_record_id = ?
        """,
        ("USDA FoodData Central", "533294"),
    ).fetchone()
    apricot_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("2710815",),
    ).fetchone()
    conn.close()

    assert tuna_row is not None
    assert tuna_row["raw_description"] == "Tuna, canned in water"
    assert tuna_row["data_type"] == "Branded"
    assert tuna_row["brand_name"] == "Sample Foods LLC"
    assert tuna_row["gtin_upc"] == "012345678905"
    assert tuna_row["serving_size"] == 56
    assert tuna_row["serving_size_unit"] == "g"
    assert tuna_row["calories_per_100g"] == 116
    assert tuna_row["protein_g_per_100g"] == 25.5
    assert tuna_row["carbs_g_per_100g"] == 0
    assert tuna_row["fat_g_per_100g"] == 0.8
    assert tuna_row["import_batch"] == "fdc_fixture_batch_v0"

    assert apricot_row is not None
    assert apricot_row["brand_name"] is None
    assert apricot_row["gtin_upc"] is None
    assert apricot_row["serving_size"] is None
    assert apricot_row["serving_size_unit"] is None


def test_fdc_directory_import_handles_missing_optional_branded_metadata(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_without_branded"
    shutil.copytree(FDC_FIXTURE_DIR, fixture_copy)
    (fixture_copy / "branded_food.csv").unlink()

    summary = import_usda_food_fdc_directory(
        fixture_copy,
        include_data_types=["Foundation Foods", "Branded"],
    )

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    tuna_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("533294",),
    ).fetchone()
    conn.close()

    assert tuna_row is not None
    assert tuna_row["brand_name"] is None
    assert tuna_row["gtin_upc"] is None
    assert tuna_row["serving_size"] is None
    assert tuna_row["serving_size_unit"] is None


def test_rerunning_import_updates_existing_fdc_ids_without_duplicates(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    first = import_usda_food_csv(FIXTURE_PATH, import_batch="first_pass")
    second = import_usda_food_csv(FIXTURE_PATH, import_batch="second_pass")

    assert first.inserted_count == 4
    assert second.inserted_count == 0
    assert second.updated_count == 4

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM raw_food_source_records"
    ).fetchone()["count"]
    batch = conn.execute(
        """
        SELECT import_batch
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("2710832",),
    ).fetchone()["import_batch"]
    conn.close()

    assert count == 4
    assert batch == "second_pass"


def test_rerunning_fdc_directory_import_updates_existing_fdc_ids_without_duplicates(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    first = import_usda_food_fdc_directory(
        FDC_FIXTURE_DIR,
        import_batch="first_fdc",
        include_data_types=["Foundation Foods", "Branded"],
    )
    second = import_usda_food_fdc_directory(
        FDC_FIXTURE_DIR,
        import_batch="second_fdc",
        include_data_types=["Foundation Foods", "Branded"],
    )

    assert first.inserted_count == 3
    assert second.inserted_count == 0
    assert second.updated_count == 3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM raw_food_source_records"
    ).fetchone()["count"]
    batch = conn.execute(
        """
        SELECT import_batch
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("533294",),
    ).fetchone()["import_batch"]
    conn.close()

    assert count == 3
    assert batch == "second_fdc"


def test_fdc_directory_import_defaults_to_foundation_food_only(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    summary = import_usda_food_fdc_directory(
        FDC_LOGGABLE_FIXTURE_DIR,
        import_batch="foundation_only",
    )

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 3
    assert summary.inserted_count == 3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM raw_food_source_records"
    ).fetchone()["count"]
    imported_types = [
        row["data_type"]
        for row in conn.execute(
            """
            SELECT data_type
            FROM raw_food_source_records
            ORDER BY CAST(source_record_id AS INTEGER)
            """
        ).fetchall()
    ]
    apricot_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("2710815",),
    ).fetchone()
    sample_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("900001",),
    ).fetchone()
    conn.close()

    assert count == 3
    assert imported_types == ["foundation_food", "foundation_food", "foundation_food"]
    assert apricot_row is not None
    assert apricot_row["source_record_id"] == "2710815"
    assert sample_row is None
    payload = json.loads(apricot_row["source_payload_json"])
    assert payload["fdc_id"] == 2710815


def test_fdc_directory_import_override_can_include_non_default_review_rows(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    summary = import_usda_food_fdc_directory(
        FDC_LOGGABLE_FIXTURE_DIR,
        include_data_types=[
            "foundation_food",
            "sample_food",
            "sub_sample_food",
        ],
    )

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 5
    assert summary.inserted_count == 5

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    imported_ids = {
        row["source_record_id"]
        for row in conn.execute(
            "SELECT source_record_id FROM raw_food_source_records"
        ).fetchall()
    }
    market_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("900002",),
    ).fetchone()
    conn.close()

    assert imported_ids == {"900001", "900003", "2710815", "2710832", "2710833"}
    assert market_row is None


def test_fdc_directory_import_limit_applies_after_filtering(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    summary = import_usda_food_fdc_directory(FDC_LOGGABLE_FIXTURE_DIR, limit=2)

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 2
    assert summary.inserted_count == 2

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    imported_ids = [
        row["source_record_id"]
        for row in conn.execute(
            """
            SELECT source_record_id
            FROM raw_food_source_records
            ORDER BY CAST(source_record_id AS INTEGER)
            """
        ).fetchall()
    ]
    missing_macro_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("2710833",),
    ).fetchone()
    conn.close()

    assert imported_ids == ["2710815", "2710832"]
    assert missing_macro_row is None


def test_fdc_directory_import_preserves_missing_and_explicit_zero_macros(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    import_usda_food_fdc_directory(FDC_LOGGABLE_FIXTURE_DIR)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    zero_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("2710832",),
    ).fetchone()
    missing_macro_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("2710833",),
    ).fetchone()
    conn.close()

    assert zero_row is not None
    assert zero_row["calories_per_100g"] == 0
    assert zero_row["protein_g_per_100g"] == 0
    assert zero_row["carbs_g_per_100g"] == 0
    assert zero_row["fat_g_per_100g"] == 0

    assert missing_macro_row is not None
    assert missing_macro_row["calories_per_100g"] == 27
    assert missing_macro_row["protein_g_per_100g"] is None
    assert missing_macro_row["carbs_g_per_100g"] == 5.51
    assert missing_macro_row["fat_g_per_100g"] is None


def test_missing_required_columns_fail_fast(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    input_path = tmp_path / "bad_foods.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "fdc_id",
                "description",
                "data_type",
                "calories_per_100g",
                "protein_g_per_100g",
                "carbs_g_per_100g",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "fdc_id": "1",
                "description": "Broken Food",
                "data_type": "Foundation Foods",
                "calories_per_100g": "100",
                "protein_g_per_100g": "5",
                "carbs_g_per_100g": "10",
            }
        )

    try:
        import_usda_food_csv(input_path)
    except ValueError as exc:
        assert "missing required columns" in str(exc).lower()
        assert "fat_g_per_100g" in str(exc)
    else:
        raise AssertionError("Expected missing USDA required columns to fail.")


def test_duplicate_fdc_id_in_single_input_is_rejected(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    input_path = tmp_path / "duplicate_foods.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "fdc_id",
                "description",
                "data_type",
                "calories_per_100g",
                "protein_g_per_100g",
                "carbs_g_per_100g",
                "fat_g_per_100g",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "fdc_id": "1001",
                "description": "Food One",
                "data_type": "Foundation Foods",
                "calories_per_100g": "100",
                "protein_g_per_100g": "5",
                "carbs_g_per_100g": "10",
                "fat_g_per_100g": "1",
            }
        )
        writer.writerow(
            {
                "fdc_id": "1001",
                "description": "Food Two",
                "data_type": "Foundation Foods",
                "calories_per_100g": "120",
                "protein_g_per_100g": "6",
                "carbs_g_per_100g": "11",
                "fat_g_per_100g": "2",
            }
        )

    try:
        import_usda_food_csv(input_path)
    except ValueError as exc:
        assert "duplicate fdc_id 1001" in str(exc)
    else:
        raise AssertionError("Expected duplicate fdc_id rows to fail.")


def test_cli_help_is_available() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/import_usda_food_data.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Import either a simple USDA-style CSV file" in result.stdout
    assert "--fdc-dir" in result.stdout
    assert "--include-data-types" in result.stdout


def test_cli_imports_fixture_into_scratch_database(tmp_path: Path) -> None:
    db_path = tmp_path / "scratch" / "usda_import.db"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/import_usda_food_data.py",
            "--input",
            str(FIXTURE_PATH),
            "--db-path",
            str(db_path),
            "--import-batch",
            "cli_fixture_batch",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert db_path.exists()
    assert "USDA food import complete." in result.stdout
    assert "Rows inserted: 4" in result.stdout


def test_cli_imports_fdc_directory_into_scratch_database(tmp_path: Path) -> None:
    db_path = tmp_path / "scratch" / "usda_fdc_import.db"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/import_usda_food_data.py",
            "--fdc-dir",
            str(FDC_LOGGABLE_FIXTURE_DIR),
            "--db-path",
            str(db_path),
            "--import-batch",
            "cli_fdc_fixture_batch",
            "--include-data-types",
            "foundation_food,sample_food",
            "--limit",
            "2",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert db_path.exists()
    assert "USDA food import complete." in result.stdout
    assert "Rows processed: 2" in result.stdout
    assert "Rows inserted: 2" in result.stdout
