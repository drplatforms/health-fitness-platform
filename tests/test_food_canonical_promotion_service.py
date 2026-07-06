from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import database
from services.food_canonical_promotion_service import (
    list_promotable_raw_food_source_records,
    promote_raw_source_record_to_canonical,
)
from services.food_normalization_service import (
    create_canonical_food,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    get_aliases_for_canonical_food,
    get_nutrients_for_canonical_food,
)
from services.usda_food_data_import_service import USDA_SOURCE_NAME


def _seed_test_db(tmp_path, monkeypatch) -> Path:
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    ensure_food_normalization_tables()
    return db_path


def test_review_helper_defaults_to_foundation_food_only(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321358",
        raw_description="Hummus, commercial",
        data_type="foundation_food",
        calories_per_100g=229.0,
        protein_g_per_100g=7.35,
        carbs_g_per_100g=14.9,
        fat_g_per_100g=17.1,
        import_batch="foundation_batch",
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="900001",
        raw_description="Review sample food",
        data_type="sample_food",
        import_batch="foundation_batch",
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="900002",
        raw_description="Review market acquisition",
        data_type="market_acquisition",
        import_batch="foundation_batch",
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="900003",
        raw_description="Review sub sample food",
        data_type="sub_sample_food",
        import_batch="foundation_batch",
    )

    results = list_promotable_raw_food_source_records(
        import_batch="foundation_batch",
    )

    assert [item.source_record_id for item in results] == ["321358"]
    assert results[0].data_type == "foundation_food"
    assert results[0].has_macro_data is True


def test_review_helper_can_include_nondefault_review_data_types(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321358",
        raw_description="Hummus, commercial",
        data_type="foundation_food",
        import_batch="review_batch",
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="900001",
        raw_description="Review sample food",
        data_type="sample_food",
        import_batch="review_batch",
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="900003",
        raw_description="Review sub sample food",
        data_type="sub_sample_food",
        import_batch="review_batch",
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="900002",
        raw_description="Review market acquisition",
        data_type="market_acquisition",
        import_batch="review_batch",
    )

    results = list_promotable_raw_food_source_records(
        import_batch="review_batch",
        include_data_types=["foundation_food", "sample_food", "sub_sample_food"],
    )

    assert {item.source_record_id for item in results} == {
        "321358",
        "900001",
        "900003",
    }
    assert all(item.data_type != "market_acquisition" for item in results)


def test_review_helper_can_require_macro_data(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321505",
        raw_description="Salt, table, iodized",
        data_type="foundation_food",
        import_batch="macro_batch",
        calories_per_100g=None,
        protein_g_per_100g=None,
        carbs_g_per_100g=None,
        fat_g_per_100g=None,
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321360",
        raw_description="Tomatoes, grape, raw",
        data_type="foundation_food",
        import_batch="macro_batch",
        calories_per_100g=27.0,
        protein_g_per_100g=0.83,
        carbs_g_per_100g=5.51,
        fat_g_per_100g=0.63,
    )

    results = list_promotable_raw_food_source_records(
        import_batch="macro_batch",
        require_macro_data=True,
    )

    assert [item.source_record_id for item in results] == ["321360"]
    assert results[0].has_macro_data is True


def test_promotion_creates_canonical_food_nutrients_source_link_and_aliases(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    raw_record = create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321358",
        raw_description="Hummus, commercial",
        data_type="foundation_food",
        calories_per_100g=229.0,
        protein_g_per_100g=7.35,
        carbs_g_per_100g=14.9,
        fat_g_per_100g=17.1,
        source_payload={"fdc_id": 321358},
    )

    result = promote_raw_source_record_to_canonical(
        raw_record.id,
        canonical_name="Hummus, commercial",
        aliases=["hummus", "commercial hummus"],
    )

    assert result.canonical_food.display_name == "Hummus, commercial"
    assert result.source_identity.source_name == USDA_SOURCE_NAME
    assert result.source_identity.source_record_id == "321358"
    assert result.source_identity.raw_food_source_record_id == raw_record.id

    aliases = get_aliases_for_canonical_food(result.canonical_food.id)
    assert {alias.alias for alias in aliases} >= {"hummus", "commercial hummus"}

    nutrients = get_nutrients_for_canonical_food(result.canonical_food.id)
    nutrient_amounts = {
        nutrient.nutrient_name: nutrient.amount_per_100g for nutrient in nutrients
    }
    assert nutrient_amounts == {
        "Calories": 229.0,
        "Protein": 7.35,
        "Carbohydrate": 14.9,
        "Fat": 17.1,
    }


def test_promotion_is_idempotent_and_reuses_existing_canonical_food(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    existing_canonical = create_canonical_food("Hummus, commercial", "generic")
    raw_record = create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321358",
        raw_description="Hummus, commercial",
        data_type="foundation_food",
        calories_per_100g=229.0,
        protein_g_per_100g=7.35,
        carbs_g_per_100g=14.9,
        fat_g_per_100g=17.1,
    )

    first = promote_raw_source_record_to_canonical(
        raw_record.id,
        aliases=["hummus"],
    )
    second = promote_raw_source_record_to_canonical(
        raw_record.id,
        aliases=["hummus", "hummus dip"],
    )

    assert first.canonical_food.id == existing_canonical.id
    assert second.canonical_food.id == existing_canonical.id

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM canonical_foods")
    canonical_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) AS count FROM food_source_links")
    source_link_count = cursor.fetchone()["count"]
    conn.close()

    assert canonical_count == 1
    assert source_link_count == 1
    aliases = get_aliases_for_canonical_food(existing_canonical.id)
    assert {alias.alias for alias in aliases} >= {"hummus", "hummus dip"}


def test_promotion_preserves_missing_and_explicit_zero_macros(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    zero_record = create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321505",
        raw_description="Salt, table, iodized",
        data_type="foundation_food",
        calories_per_100g=0.0,
        protein_g_per_100g=0.0,
        carbs_g_per_100g=0.0,
        fat_g_per_100g=0.0,
    )
    missing_record = create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321360",
        raw_description="Tomatoes, grape, raw",
        data_type="foundation_food",
        calories_per_100g=27.0,
        protein_g_per_100g=None,
        carbs_g_per_100g=5.51,
        fat_g_per_100g=None,
    )

    zero_result = promote_raw_source_record_to_canonical(zero_record.id)
    missing_result = promote_raw_source_record_to_canonical(missing_record.id)

    zero_nutrients = {
        nutrient.nutrient_name: nutrient.amount_per_100g
        for nutrient in get_nutrients_for_canonical_food(zero_result.canonical_food.id)
    }
    missing_nutrients = {
        nutrient.nutrient_name: nutrient.amount_per_100g
        for nutrient in get_nutrients_for_canonical_food(
            missing_result.canonical_food.id
        )
    }

    assert zero_nutrients == {
        "Calories": 0.0,
        "Protein": 0.0,
        "Carbohydrate": 0.0,
        "Fat": 0.0,
    }
    assert missing_nutrients == {
        "Calories": 27.0,
        "Carbohydrate": 5.51,
    }


def test_cli_help_is_available() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/promote_usda_raw_food.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Promote one USDA raw food source record" in result.stdout
    assert "--db-path" in result.stdout


def test_cli_promotes_raw_source_record_into_scratch_database(tmp_path: Path) -> None:
    db_path = tmp_path / "scratch" / "promotion.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    database.DB_PATH = db_path
    database.initialize_database()
    ensure_food_normalization_tables()
    raw_record = create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321358",
        raw_description="Hummus, commercial",
        data_type="foundation_food",
        calories_per_100g=229.0,
        protein_g_per_100g=7.35,
        carbs_g_per_100g=14.9,
        fat_g_per_100g=17.1,
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/promote_usda_raw_food.py",
            "--db-path",
            str(db_path),
            "--source-record-id",
            str(raw_record.id),
            "--canonical-name",
            "Hummus, commercial",
            "--alias",
            "hummus",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Raw USDA source promotion complete." in result.stdout

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    canonical_count = conn.execute(
        "SELECT COUNT(*) AS count FROM canonical_foods"
    ).fetchone()["count"]
    source_link_count = conn.execute(
        "SELECT COUNT(*) AS count FROM food_source_links"
    ).fetchone()["count"]
    conn.close()

    assert canonical_count == 1
    assert source_link_count == 1
