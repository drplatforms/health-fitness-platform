from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import database
import services.usda_food_data_import_service as usda_import_service
from services.food_normalization_service import (
    create_canonical_food,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    link_canonical_food_to_source,
)
from services.usda_food_data_import_service import (
    import_usda_food_csv,
    import_usda_food_fdc_directory,
    normalize_fdc_data_type_key,
)

FIXTURE_PATH = Path("tests/fixtures/usda/sample_foods.csv")
FDC_FIXTURE_DIR = Path("tests/fixtures/usda/fdc_csv_minimal")
FDC_LOGGABLE_FIXTURE_DIR = Path("tests/fixtures/usda/fdc_csv_loggable_filter")
FDC_GENERIC_FIXTURE_DIR = Path("tests/fixtures/usda/fdc_csv_generic")


def _write_wweia_category_rows(
    fixture_dir: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    with (fixture_dir / "wweia_food_category.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
    assert tuna_row["data_type"] == "branded_food"
    assert tuna_row["brand_name"] == "Sample Foods LLC"
    assert tuna_row["gtin_upc"] == "012345678905"
    assert tuna_row["serving_size"] == 56
    assert tuna_row["serving_size_unit"] == "g"
    assert tuna_row["food_category"] == "Finfish and Shellfish Products"
    assert tuna_row["calories_per_100g"] == 116
    assert tuna_row["protein_g_per_100g"] == 25.5
    assert tuna_row["carbs_g_per_100g"] == 0
    assert tuna_row["fat_g_per_100g"] == 0.8
    assert tuna_row["import_batch"] == "fdc_fixture_batch_v0"
    tuna_payload = json.loads(tuna_row["source_payload_json"])
    assert tuna_payload["source_data_type"] == "Branded"
    assert tuna_payload["normalized_data_type"] == "branded_food"

    assert apricot_row is not None
    assert apricot_row["food_category"] == "Fruits and Fruit Juices"
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


def test_fdc_directory_import_defaults_to_generic_source_profile(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    summary = import_usda_food_fdc_directory(
        FDC_GENERIC_FIXTURE_DIR,
        import_batch="generic_default",
    )

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 5
    assert summary.inserted_count == 5
    assert summary.processed_count_by_data_type == {
        "foundation_food": 1,
        "sr_legacy_food": 2,
        "survey_fndds_food": 2,
    }

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM raw_food_source_records"
    ).fetchone()["count"]
    imported_types = {
        row["data_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT data_type, COUNT(*) AS count
            FROM raw_food_source_records
            GROUP BY data_type
            """
        ).fetchall()
    }
    foundation_row = conn.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_record_id = ?
        """,
        ("100001",),
    ).fetchone()
    excluded_ids = {
        row["source_record_id"]
        for row in conn.execute(
            """
            SELECT source_record_id
            FROM raw_food_source_records
            WHERE source_record_id IN ('100006', '100007')
            """
        ).fetchall()
    }
    conn.close()

    assert count == 5
    assert imported_types == {
        "foundation_food": 1,
        "sr_legacy_food": 2,
        "survey_fndds_food": 2,
    }
    assert foundation_row is not None
    assert foundation_row["food_category"] == "Synthetic Fruits Category"
    assert excluded_ids == set()
    payload = json.loads(foundation_row["source_payload_json"])
    assert payload["fdc_id"] == 100001
    assert payload["source_data_type"] == "Foundation Foods"
    assert payload["normalized_data_type"] == "foundation_food"


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("Foundation Foods", "foundation_food"),
        ("Foundation Food", "foundation_food"),
        ("foundation_foods", "foundation_food"),
        ("SR Legacy", "sr_legacy_food"),
        ("sr_legacy_food", "sr_legacy_food"),
        ("Survey (FNDDS)", "survey_fndds_food"),
        ("Survey Foods (FNDDS)", "survey_fndds_food"),
        ("FNDDS", "survey_fndds_food"),
        ("survey_fndds_food", "survey_fndds_food"),
        ("Sample Food", "sample_food"),
    ],
)
def test_known_fdc_data_type_aliases_normalize_to_stable_keys(
    alias,
    expected,
) -> None:
    assert normalize_fdc_data_type_key(alias) == expected


def test_fdc_directory_streams_large_tables_and_skips_default_branded_metadata(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    eager_loader = usda_import_service._load_csv_rows

    def reject_large_table_materialization(input_path):
        if Path(input_path).name in {"food.csv", "food_nutrient.csv"}:
            raise AssertionError("Large FDC tables must be streamed.")
        return eager_loader(input_path)

    def reject_default_branded_load(*args, **kwargs):
        raise AssertionError("Default generic import must not load branded metadata.")

    monkeypatch.setattr(
        usda_import_service,
        "_load_csv_rows",
        reject_large_table_materialization,
    )
    monkeypatch.setattr(
        usda_import_service,
        "_load_branded_food_rows",
        reject_default_branded_load,
    )

    summary = import_usda_food_fdc_directory(FDC_GENERIC_FIXTURE_DIR)

    assert summary.database_path == str(db_path)
    assert summary.total_rows == 5


def test_generic_import_preserves_zero_missing_and_filtered_macro_rows(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    import_usda_food_fdc_directory(FDC_GENERIC_FIXTURE_DIR)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    zero_row = conn.execute(
        "SELECT * FROM raw_food_source_records WHERE source_record_id = '100003'"
    ).fetchone()
    missing_row = conn.execute(
        "SELECT * FROM raw_food_source_records WHERE source_record_id = '100005'"
    ).fetchone()
    conn.close()

    assert zero_row is not None
    assert zero_row["calories_per_100g"] == 0
    assert zero_row["protein_g_per_100g"] == 0
    assert zero_row["carbs_g_per_100g"] == 0
    assert zero_row["fat_g_per_100g"] == 0
    assert missing_row is not None
    assert missing_row["calories_per_100g"] == 80
    assert missing_row["protein_g_per_100g"] is None
    assert missing_row["carbs_g_per_100g"] == 15
    assert missing_row["fat_g_per_100g"] is None


def test_fndds_metadata_uses_wweia_category_and_preserves_provenance(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    import_usda_food_fdc_directory(FDC_GENERIC_FIXTURE_DIR)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    fndds_row = conn.execute(
        "SELECT * FROM raw_food_source_records WHERE source_record_id = '100004'"
    ).fetchone()
    sr_row = conn.execute(
        "SELECT * FROM raw_food_source_records WHERE source_record_id = '100002'"
    ).fetchone()
    conn.close()

    assert fndds_row is not None
    assert fndds_row["data_type"] == "survey_fndds_food"
    assert fndds_row["food_category"] == "Synthetic Mixed Dishes Category"
    fndds_payload = json.loads(fndds_row["source_payload_json"])
    assert fndds_payload["source_data_type"] == "Survey (FNDDS)"
    assert fndds_payload["normalized_data_type"] == "survey_fndds_food"
    assert fndds_payload["food_code"] == "90010000"
    assert fndds_payload["wweia_category_number"] == "1002"
    assert fndds_payload["wweia_food_category_code"] == "1002"
    assert "wweia_food_category" not in fndds_payload

    assert sr_row is not None
    assert sr_row["food_category"] == "Synthetic Grains Category"


def test_fndds_wweia_documented_code_header_remains_supported(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_documented_wweia_header"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    _write_wweia_category_rows(
        fixture_copy,
        ["wweia_food_category_code", "wweia_food_category_description"],
        [
            {
                "wweia_food_category_code": "1002",
                "wweia_food_category_description": "Synthetic Mixed Dishes Category",
            },
            {
                "wweia_food_category_code": "2004",
                "wweia_food_category_description": "Synthetic Beverages Category",
            },
        ],
    )

    import_usda_food_fdc_directory(fixture_copy)

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT food_category FROM raw_food_source_records WHERE source_record_id = '100004'"
    ).fetchone()
    conn.close()
    assert row == ("Synthetic Mixed Dishes Category",)


def test_fndds_wweia_dual_matching_headers_use_stable_payload_key(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_dual_matching_wweia_headers"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    _write_wweia_category_rows(
        fixture_copy,
        [
            "wweia_food_category_code",
            "wweia_food_category",
            "wweia_food_category_description",
        ],
        [
            {
                "wweia_food_category_code": "1002",
                "wweia_food_category": "1002",
                "wweia_food_category_description": "Synthetic Mixed Dishes Category",
            },
            {
                "wweia_food_category_code": "2004",
                "wweia_food_category": "2004",
                "wweia_food_category_description": "Synthetic Beverages Category",
            },
        ],
    )

    import_usda_food_fdc_directory(fixture_copy)

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT source_payload_json FROM raw_food_source_records WHERE source_record_id = '100004'"
    ).fetchone()
    conn.close()
    assert row is not None
    payload = json.loads(row[0])
    assert payload["wweia_food_category_code"] == "1002"
    assert "wweia_food_category" not in payload


def test_fndds_wweia_dual_headers_use_non_empty_value(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_dual_wweia_empty_documented"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    _write_wweia_category_rows(
        fixture_copy,
        [
            "wweia_food_category_code",
            "wweia_food_category",
            "wweia_food_category_description",
        ],
        [
            {
                "wweia_food_category_code": "",
                "wweia_food_category": "1002",
                "wweia_food_category_description": "Synthetic Mixed Dishes Category",
            },
            {
                "wweia_food_category_code": "2004",
                "wweia_food_category": "",
                "wweia_food_category_description": "Synthetic Beverages Category",
            },
        ],
    )

    import_usda_food_fdc_directory(fixture_copy)

    conn = sqlite3.connect(db_path)
    categories = {
        row[0]
        for row in conn.execute(
            "SELECT food_category FROM raw_food_source_records WHERE data_type = 'survey_fndds_food'"
        ).fetchall()
    }
    conn.close()
    assert categories == {
        "Synthetic Mixed Dishes Category",
        "Synthetic Beverages Category",
    }


def test_fndds_wweia_dual_header_conflict_fails_clearly(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_conflicting_wweia_headers"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    _write_wweia_category_rows(
        fixture_copy,
        [
            "wweia_food_category_code",
            "wweia_food_category",
            "wweia_food_category_description",
        ],
        [
            {
                "wweia_food_category_code": "1002",
                "wweia_food_category": "9999",
                "wweia_food_category_description": "Synthetic Mixed Dishes Category",
            },
        ],
    )

    with pytest.raises(ValueError, match="conflicting WWEIA category code values"):
        import_usda_food_fdc_directory(fixture_copy)


def test_fndds_wweia_missing_code_headers_name_both_options(
    tmp_path, monkeypatch
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_missing_wweia_headers"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    _write_wweia_category_rows(
        fixture_copy,
        ["unexpected_code", "wweia_food_category_description"],
        [
            {
                "unexpected_code": "1002",
                "wweia_food_category_description": "Synthetic Mixed Dishes Category",
            },
        ],
    )

    with pytest.raises(ValueError) as exc_info:
        import_usda_food_fdc_directory(fixture_copy)

    assert "wweia_food_category_code" in str(exc_info.value)
    assert "wweia_food_category" in str(exc_info.value)


def test_fndds_wweia_blank_resolved_code_fails_clearly(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_blank_wweia_code"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    _write_wweia_category_rows(
        fixture_copy,
        ["wweia_food_category", "wweia_food_category_description"],
        [
            {
                "wweia_food_category": "",
                "wweia_food_category_description": "Synthetic Mixed Dishes Category",
            },
        ],
    )

    with pytest.raises(ValueError, match="wweia_food_category_code is required"):
        import_usda_food_fdc_directory(fixture_copy)


def test_fndds_wweia_duplicate_resolved_code_remains_rejected(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_duplicate_wweia_code"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    _write_wweia_category_rows(
        fixture_copy,
        ["wweia_food_category", "wweia_food_category_description"],
        [
            {
                "wweia_food_category": "1002",
                "wweia_food_category_description": "Synthetic Mixed Dishes Category",
            },
            {
                "wweia_food_category": "1002",
                "wweia_food_category_description": "Synthetic Duplicate Category",
            },
        ],
    )

    with pytest.raises(ValueError, match="duplicate WWEIA category code 1002"):
        import_usda_food_fdc_directory(fixture_copy)


def test_fndds_import_handles_missing_optional_metadata_safely(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    fixture_copy = tmp_path / "fdc_generic_without_fndds_metadata"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    (fixture_copy / "survey_fndds_food.csv").unlink()

    import_usda_food_fdc_directory(fixture_copy)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM raw_food_source_records WHERE source_record_id = '100004'"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row["food_category"] is None
    payload = json.loads(row["source_payload_json"])
    assert "food_code" not in payload
    assert "wweia_category_number" not in payload
    assert "wweia_food_category_code" not in payload


def test_generic_limit_applies_after_filtering_across_source_profile(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    summary = import_usda_food_fdc_directory(FDC_GENERIC_FIXTURE_DIR, limit=3)

    assert summary.database_path == str(db_path)
    assert summary.processed_count_by_data_type == {
        "foundation_food": 1,
        "sr_legacy_food": 1,
        "survey_fndds_food": 1,
    }
    conn = sqlite3.connect(db_path)
    imported_ids = {
        row[0]
        for row in conn.execute(
            "SELECT source_record_id FROM raw_food_source_records"
        ).fetchall()
    }
    conn.close()
    assert imported_ids == {"100001", "100002", "100004"}


def test_rerunning_generic_import_updates_without_duplicates(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    first = import_usda_food_fdc_directory(
        FDC_GENERIC_FIXTURE_DIR,
        import_batch="generic_first",
    )
    second = import_usda_food_fdc_directory(
        FDC_GENERIC_FIXTURE_DIR,
        import_batch="generic_second",
    )

    assert first.inserted_count == 5
    assert second.inserted_count == 0
    assert second.updated_count == 5
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM raw_food_source_records").fetchone()[0]
    batches = {
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT import_batch FROM raw_food_source_records"
        ).fetchall()
    }
    conn.close()
    assert count == 5
    assert batches == {"generic_second"}


def test_successful_generic_import_does_not_mutate_canonical_tables(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    existing_raw = create_raw_food_source_record(
        source_name="Manual QA Source",
        source_record_id="canonical-source",
        raw_description="Existing synthetic canonical source row",
    )
    canonical = create_canonical_food("Existing Synthetic Linked Food")
    link_canonical_food_to_source(canonical.id, existing_raw.id)

    import_usda_food_fdc_directory(FDC_GENERIC_FIXTURE_DIR)

    conn = sqlite3.connect(db_path)
    canonical_count = conn.execute("SELECT COUNT(*) FROM canonical_foods").fetchone()[0]
    link_rows = conn.execute(
        "SELECT canonical_food_id, raw_food_source_record_id FROM food_source_links"
    ).fetchall()
    conn.close()
    assert canonical_count == 1
    assert link_rows == [(canonical.id, existing_raw.id)]


def test_generic_validation_failure_leaves_raw_and_canonical_rows_unchanged(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    existing_raw = create_raw_food_source_record(
        source_name="Manual QA Source",
        source_record_id="existing-source",
        raw_description="Existing synthetic source row",
    )
    canonical = create_canonical_food("Existing Synthetic Canonical Food")
    link_canonical_food_to_source(canonical.id, existing_raw.id)
    fixture_copy = tmp_path / "fdc_generic_invalid"
    shutil.copytree(FDC_GENERIC_FIXTURE_DIR, fixture_copy)
    food_path = fixture_copy / "food.csv"
    rows = list(csv.DictReader(food_path.read_text(encoding="utf-8").splitlines()))
    rows[-1]["description"] = ""
    with food_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="description is required"):
        import_usda_food_fdc_directory(fixture_copy)

    conn = sqlite3.connect(db_path)
    raw_rows = conn.execute(
        "SELECT source_name, source_record_id FROM raw_food_source_records"
    ).fetchall()
    canonical_count = conn.execute("SELECT COUNT(*) FROM canonical_foods").fetchone()[0]
    link_count = conn.execute("SELECT COUNT(*) FROM food_source_links").fetchone()[0]
    conn.close()
    assert raw_rows == [("Manual QA Source", "existing-source")]
    assert canonical_count == 1
    assert link_count == 1


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
    assert zero_row["food_category"] == "Spices and Herbs"
    assert zero_row["calories_per_100g"] == 0
    assert zero_row["protein_g_per_100g"] == 0
    assert zero_row["carbs_g_per_100g"] == 0
    assert zero_row["fat_g_per_100g"] == 0

    assert missing_macro_row is not None
    assert missing_macro_row["food_category"] == "Vegetables and Vegetable Products"
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
    normalized_help = " ".join(result.stdout.split())
    assert "foundation_food, sr_legacy_food, and survey_fndds_food" in normalized_help


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
    assert "Rows processed [foundation_food]" in result.stdout
    assert "Rows processed [sample_food]" in result.stdout


def test_cli_default_imports_all_generic_data_types(tmp_path: Path) -> None:
    db_path = tmp_path / "scratch" / "usda_generic_import.db"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/import_usda_food_data.py",
            "--fdc-dir",
            str(FDC_GENERIC_FIXTURE_DIR),
            "--db-path",
            str(db_path),
            "--import-batch",
            "cli_generic_fixture_batch",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Rows processed: 5" in result.stdout
    assert "Rows processed [foundation_food]: 1" in result.stdout
    assert "Rows processed [sr_legacy_food]: 2" in result.stdout
    assert "Rows processed [survey_fndds_food]: 2" in result.stdout
