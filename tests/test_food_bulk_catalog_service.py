from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_bulk_catalog_service import promote_canonical_food_bulk_catalog
from services.food_catalog_inventory_service import (
    build_food_catalog_inventory_report,
)
from services.food_normalization_service import (
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    normalize_food_name,
    search_canonical_foods,
)
from services.nutrition_service import get_daily_canonical_food_macro_totals
from services.usda_food_data_import_service import USDA_SOURCE_NAME

FDC_FIXTURE_DIR = Path("tests/fixtures/usda/fdc_csv_minimal")


def _seed_test_db(tmp_path, monkeypatch) -> Path:
    db_path = tmp_path / "fitness_ai_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    ensure_food_normalization_tables()
    return db_path


def _client() -> TestClient:
    return TestClient(app)


def _count_rows(table_name: str) -> int:
    conn = database.get_connection()
    count = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()[
        "count"
    ]
    conn.close()
    return int(count)


def _create_foundation_raw(
    *,
    source_record_id: str,
    raw_description: str,
    food_category: str,
    calories: float | None = 100.0,
    protein: float | None = 1.0,
    carbs: float | None = 1.0,
    fat: float | None = 1.0,
):
    return create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id=source_record_id,
        raw_description=raw_description,
        data_type="foundation_food",
        food_category=food_category,
        calories_per_100g=calories,
        protein_g_per_100g=protein,
        carbs_g_per_100g=carbs,
        fat_g_per_100g=fat,
    )


def test_inventory_report_counts_database_and_fdc_directory(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="2710815",
        raw_description="Apricot, with skin, raw",
        food_category="Fruits and Fruit Juices",
    )
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="900001",
        raw_description="Review sample food row",
        data_type="sample_food",
        food_category="Fruits and Fruit Juices",
    )

    report = build_food_catalog_inventory_report(
        database_path=str(db_path),
        fdc_dir=FDC_FIXTURE_DIR,
    )
    payload = report.to_dict()

    assert payload["raw_count_by_source_name"] == {USDA_SOURCE_NAME: 2}
    assert payload["raw_count_by_data_type"] == {
        "foundation_food": 1,
        "sample_food": 1,
    }
    assert payload["raw_count_by_food_category"] == {"Fruits and Fruit Juices": 2}
    assert payload["macro_coverage"]["any_macro"] == 1
    assert payload["canonical_food_count"] == 0
    assert payload["canonical_source_link_count"] == 0
    assert payload["fdc_food_count_by_data_type"] == {
        "Foundation Foods": 2,
        "Branded": 1,
    }
    assert payload["fdc_foundation_count_by_category"] == {"Fruits and Fruit Juices": 2}


def test_inventory_report_explains_empty_db_with_fdc_foundation_rows(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)

    report = build_food_catalog_inventory_report(
        database_path=str(db_path),
        fdc_dir=FDC_FIXTURE_DIR,
    )

    assert report.macro_coverage["total"] == 0
    assert report.fdc_foundation_count_by_category == {"Fruits and Fruit Juices": 2}
    assert report.notes == [
        "FDC directory contains foundation_food rows, but the database has "
        "no raw_food_source_records. Import Foundation rows before bulk promotion."
    ]


def test_bulk_catalog_dry_run_does_not_mutate_canonical_tables(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="2710815",
        raw_description="Apricot, with skin, raw",
        food_category="Fruits and Fruit Juices",
    )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert len(report.promoted) == 1
    assert report.promoted[0].canonical_display_name == "Apricot"
    assert report.promoted[0].reason == "Dry run: candidate would be promoted."
    assert _count_rows("canonical_foods") == 0
    assert _count_rows("canonical_food_aliases") == 0
    assert _count_rows("canonical_food_nutrients") == 0
    assert _count_rows("food_source_links") == 0


def test_safe_produce_and_raw_produce_promote(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="321360",
        raw_description="Tomatoes, grape, raw",
        food_category="Vegetables and Vegetable Products",
        calories=27.0,
        protein=0.83,
        carbs=5.51,
        fat=0.63,
    )

    report = promote_canonical_food_bulk_catalog()

    assert len(report.promoted) == 1
    assert report.promoted[0].canonical_display_name == "Grape tomatoes"
    assert _count_rows("canonical_foods") == 1
    search_results = search_canonical_foods("tomatoes grape")
    assert search_results[0].canonical_food.display_name == "Grape tomatoes"


def test_safe_dairy_foundation_row_promotes_with_curated_name(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="100100",
        raw_description="Milk, reduced fat, fluid, 2% milkfat, with added vitamin A",
        food_category="Dairy and Egg Products",
        calories=50.0,
        protein=3.3,
        carbs=4.8,
        fat=2.0,
    )

    report = promote_canonical_food_bulk_catalog()

    assert len(report.promoted) == 1
    assert report.promoted[0].canonical_display_name == "2% milk"
    assert "reduced fat milk" in report.promoted[0].aliases
    assert search_canonical_foods("two percent milk")[
        0
    ].canonical_food.display_name == ("2% milk")


def test_cooked_and_canned_meat_or_fish_promotes(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="200200",
        raw_description="Fish, tuna, light, canned in water, drained solids",
        food_category="Finfish and Shellfish Products",
        calories=116.0,
        protein=25.5,
        carbs=0.0,
        fat=0.8,
    )

    report = promote_canonical_food_bulk_catalog()

    assert len(report.promoted) == 1
    assert report.promoted[0].canonical_display_name == "Tuna"
    assert "canned tuna" in report.promoted[0].aliases


def test_raw_meat_fowl_or_fish_is_skipped(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="300300",
        raw_description="Chicken, ground, with additives, raw",
        food_category="Poultry Products",
        calories=143.0,
        protein=17.4,
        carbs=0.0,
        fat=8.1,
    )

    report = promote_canonical_food_bulk_catalog()

    assert len(report.skipped_unsafe_raw) == 1
    assert report.skipped_unsafe_raw[0].raw_description.endswith("raw")
    assert _count_rows("canonical_foods") == 0


def test_category_filters_work(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="400400",
        raw_description="Apricot, with skin, raw",
        food_category="Fruits and Fruit Juices",
    )
    _create_foundation_raw(
        source_record_id="400401",
        raw_description="Carrots, raw",
        food_category="Vegetables and Vegetable Products",
    )

    report = promote_canonical_food_bulk_catalog(
        dry_run=True,
        include_categories=("Vegetables and Vegetable Products",),
    )

    assert [item.canonical_display_name for item in report.promoted] == ["Carrots"]
    assert len(report.skipped_category) == 1
    assert report.skipped_category[0].raw_description == "Apricot, with skin, raw"


def test_duplicate_canonical_display_names_are_skipped_safely(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="500500",
        raw_description="Tomatoes, grape, raw",
        food_category="Vegetables and Vegetable Products",
    )
    _create_foundation_raw(
        source_record_id="500501",
        raw_description="Tomato, grape, raw",
        food_category="Vegetables and Vegetable Products",
    )

    report = promote_canonical_food_bulk_catalog()

    assert len(report.skipped_duplicate_name) == 2
    assert {item.canonical_display_name for item in report.skipped_duplicate_name} == {
        "Grape tomatoes"
    }
    assert _count_rows("canonical_foods") == 0


def test_flour_variants_keep_meaningful_qualifiers(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for index, description in enumerate(
        (
            "Flour, almond",
            "Flour, coconut",
            "Flour, whole wheat",
            "Flour, bread, white",
            "Flour, rice, brown",
        ),
        start=1,
    ):
        _create_foundation_raw(
            source_record_id=f"flour-{index}",
            raw_description=description,
            food_category="Cereal Grains and Pasta",
        )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert {item.canonical_display_name for item in report.promoted} == {
        "Almond flour",
        "Coconut flour",
        "Whole wheat flour",
        "Bread flour",
        "Brown rice flour",
    }
    assert report.skipped_duplicate_name == []


def test_cheese_variants_keep_meaningful_qualifiers(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for index, description in enumerate(
        (
            "Cheese, cheddar",
            "Cheese, mozzarella",
            "Cheese, parmesan",
            "Cheese, feta",
        ),
        start=1,
    ):
        _create_foundation_raw(
            source_record_id=f"cheese-{index}",
            raw_description=description,
            food_category="Dairy and Egg Products",
        )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert {item.canonical_display_name for item in report.promoted} == {
        "Cheddar cheese",
        "Mozzarella cheese",
        "Parmesan cheese",
        "Feta cheese",
    }
    assert report.skipped_duplicate_name == []


def test_rice_variants_keep_meaningful_qualifiers(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for index, description in enumerate(
        (
            "Rice, brown",
            "Rice, white",
            "Rice, black",
        ),
        start=1,
    ):
        _create_foundation_raw(
            source_record_id=f"rice-{index}",
            raw_description=description,
            food_category="Cereal Grains and Pasta",
        )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert {item.canonical_display_name for item in report.promoted} == {
        "Brown rice",
        "White rice",
        "Black rice",
    }
    assert report.skipped_duplicate_name == []


def test_tomato_variants_keep_meaningful_qualifiers(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for index, description in enumerate(
        (
            "Tomato, paste",
            "Tomato, puree",
            "Tomato, sauce",
            "Tomato, roma, raw",
        ),
        start=1,
    ):
        _create_foundation_raw(
            source_record_id=f"tomato-{index}",
            raw_description=description,
            food_category="Vegetables and Vegetable Products",
        )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert {item.canonical_display_name for item in report.promoted} == {
        "Tomato paste",
        "Tomato puree",
        "Tomato sauce",
        "Roma tomato",
    }
    assert report.skipped_duplicate_name == []


def test_common_bread_butter_cream_oil_qualifiers_are_preserved(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    rows = [
        ("butter-1", "Butter, salted", "Dairy and Egg Products"),
        ("butter-2", "Butter, unsalted", "Dairy and Egg Products"),
        ("cream-1", "Cream, heavy", "Dairy and Egg Products"),
        ("cream-2", "Cream, sour", "Dairy and Egg Products"),
        ("bread-1", "Bread, white", "Baked Products"),
        ("bread-2", "Bread, whole-wheat", "Baked Products"),
        ("oil-1", "Oil, coconut", "Fats and Oils"),
        ("oil-2", "Oil, olive", "Fats and Oils"),
    ]
    for source_record_id, description, category in rows:
        _create_foundation_raw(
            source_record_id=source_record_id,
            raw_description=description,
            food_category=category,
        )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert {item.canonical_display_name for item in report.promoted} == {
        "Salted butter",
        "Unsalted butter",
        "Heavy cream",
        "Sour cream",
        "White bread",
        "Whole wheat bread",
        "Coconut oil",
        "Olive oil",
    }
    assert report.skipped_duplicate_name == []


def test_identical_duplicate_berries_can_still_be_skipped(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    for source_record_id in ("berry-1", "berry-2"):
        _create_foundation_raw(
            source_record_id=source_record_id,
            raw_description="Blackberries, raw",
            food_category="Fruits and Fruit Juices",
            calories=43.0,
            protein=1.4,
            carbs=9.6,
            fat=0.5,
        )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert report.promoted == []
    assert len(report.skipped_duplicate_name) == 2
    assert {item.canonical_display_name for item in report.skipped_duplicate_name} == {
        "Blackberries"
    }


def test_materially_different_same_name_rows_get_more_specific_names(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="berry-raw",
        raw_description="Blackberries, raw",
        food_category="Fruits and Fruit Juices",
        calories=43.0,
        protein=1.4,
        carbs=9.6,
        fat=0.5,
    )
    _create_foundation_raw(
        source_record_id="berry-canned",
        raw_description="Blackberries, canned, heavy syrup",
        food_category="Fruits and Fruit Juices",
        calories=92.0,
        protein=1.0,
        carbs=23.0,
        fat=0.2,
    )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert {item.canonical_display_name for item in report.promoted} == {
        "Raw Blackberries",
        "Canned Blackberries",
    }
    assert report.skipped_duplicate_name == []


def test_anchovies_in_olive_oil_do_not_become_olive_oil(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="anchovy-1",
        raw_description="Anchovies, canned in olive oil",
        food_category="Finfish and Shellfish Products",
        calories=210.0,
        protein=28.9,
        carbs=0.0,
        fat=9.7,
    )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert len(report.promoted) == 1
    assert report.promoted[0].canonical_display_name == "Canned anchovies"
    assert "anchovies" in {
        normalize_food_name(alias) for alias in report.promoted[0].aliases
    }
    assert report.promoted[0].canonical_display_name != "Olive oil"


def test_representative_dry_run_promoted_count_improves_with_qualifier_curation(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    rows = [
        ("flour-1", "Flour, almond", "Cereal Grains and Pasta"),
        ("flour-2", "Flour, coconut", "Cereal Grains and Pasta"),
        ("flour-3", "Flour, whole wheat", "Cereal Grains and Pasta"),
        ("cheese-1", "Cheese, cheddar", "Dairy and Egg Products"),
        ("cheese-2", "Cheese, mozzarella", "Dairy and Egg Products"),
        ("cheese-3", "Cheese, feta", "Dairy and Egg Products"),
        ("rice-1", "Rice, brown", "Cereal Grains and Pasta"),
        ("rice-2", "Rice, white", "Cereal Grains and Pasta"),
        ("tomato-1", "Tomato, paste", "Vegetables and Vegetable Products"),
        ("tomato-2", "Tomato, puree", "Vegetables and Vegetable Products"),
        ("tomato-3", "Tomato, roma, raw", "Vegetables and Vegetable Products"),
        ("butter-1", "Butter, salted", "Dairy and Egg Products"),
        ("butter-2", "Butter, unsalted", "Dairy and Egg Products"),
        ("cream-1", "Cream, heavy", "Dairy and Egg Products"),
        ("cream-2", "Cream, sour", "Dairy and Egg Products"),
        ("bread-1", "Bread, white", "Baked Products"),
        ("bread-2", "Bread, whole-wheat", "Baked Products"),
        ("oil-1", "Oil, coconut", "Fats and Oils"),
        ("oil-2", "Oil, olive", "Fats and Oils"),
        ("berry-1", "Blackberries, raw", "Fruits and Fruit Juices"),
        ("berry-2", "Blackberries, raw", "Fruits and Fruit Juices"),
    ]
    for source_record_id, description, category in rows:
        _create_foundation_raw(
            source_record_id=source_record_id,
            raw_description=description,
            food_category=category,
        )

    report = promote_canonical_food_bulk_catalog(dry_run=True)

    assert len(report.promoted) >= 19
    assert len(report.skipped_duplicate_name) == 2
    assert {item.canonical_display_name for item in report.skipped_duplicate_name} == {
        "Blackberries"
    }


def test_bulk_promotion_is_idempotent(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="600600",
        raw_description="Apricot, with skin, raw",
        food_category="Fruits and Fruit Juices",
    )

    first = promote_canonical_food_bulk_catalog()
    second = promote_canonical_food_bulk_catalog()

    assert len(first.promoted) == 1
    assert len(second.already_promoted) == 1
    assert (
        second.already_promoted[0].canonical_food_id
        == first.promoted[0].canonical_food_id
    )
    assert _count_rows("canonical_foods") == 1
    assert _count_rows("food_source_links") == 1


def test_bulk_promoted_food_is_searchable_and_loggable(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="700700",
        raw_description="Oil, olive, extra virgin",
        food_category="Fats and Oils",
        calories=884.0,
        protein=0.0,
        carbs=0.0,
        fat=100.0,
    )

    report = promote_canonical_food_bulk_catalog()
    promoted = report.promoted[0]

    search_results = search_canonical_foods("extra virgin olive oil")
    assert search_results[0].canonical_food.id == promoted.canonical_food_id
    assert search_results[0].canonical_food.display_name == "Olive oil"

    response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": promoted.canonical_food_id,
            "grams": 10,
            "entry_date": "2026-06-05",
        },
    )

    assert response.status_code == 200
    assert response.json()["nutrient_summary"] == {
        "calories": 88.4,
        "protein_g": 0.0,
        "carbohydrate_g": 0.0,
        "fat_g": 10.0,
    }
    assert get_daily_canonical_food_macro_totals(1, "2026-06-05") == {
        "entry_count": 1,
        "calories": 88.4,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 10.0,
    }


def test_inventory_cli_writes_report(tmp_path: Path) -> None:
    db_path = tmp_path / "inventory.db"
    report_path = tmp_path / "inventory_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_usda_food_catalog_sources.py",
            "--db-path",
            str(db_path),
            "--fdc-dir",
            str(FDC_FIXTURE_DIR),
            "--report-path",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "USDA food catalog source inventory complete." in result.stdout
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["fdc_foundation_count_by_category"] == {"Fruits and Fruit Juices": 2}
    assert payload["notes"]


def test_bulk_catalog_cli_dry_run_writes_report_without_promoting(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    _create_foundation_raw(
        source_record_id="800800",
        raw_description="Apricot, with skin, raw",
        food_category="Fruits and Fruit Juices",
    )
    report_path = tmp_path / "bulk_catalog_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/promote_canonical_food_bulk_catalog.py",
            "--db-path",
            str(db_path),
            "--dry-run",
            "--report-path",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Dry run: True" in result.stdout
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["promoted"] == 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    canonical_count = conn.execute(
        "SELECT COUNT(*) AS count FROM canonical_foods"
    ).fetchone()["count"]
    source_link_count = conn.execute(
        "SELECT COUNT(*) AS count FROM food_source_links"
    ).fetchone()["count"]
    conn.close()

    assert canonical_count == 0
    assert source_link_count == 0
