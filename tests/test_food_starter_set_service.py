from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    get_aliases_for_canonical_food,
    get_nutrients_for_canonical_food,
    search_canonical_foods,
)
from services.food_starter_set_definitions import STARTER_FOOD_DEFINITIONS
from services.food_starter_set_service import promote_canonical_food_starter_set
from services.nutrition_service import get_daily_canonical_food_macro_totals
from services.usda_food_data_import_service import USDA_SOURCE_NAME


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


def _seed_cooked_chicken() -> None:
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="100001",
        raw_description=(
            "Chicken, broilers or fryers, breast, meat only, cooked, roasted"
        ),
        data_type="foundation_food",
        calories_per_100g=165.0,
        protein_g_per_100g=31.0,
        carbs_g_per_100g=0.0,
        fat_g_per_100g=3.6,
    )


def test_starter_set_definition_is_reviewable() -> None:
    assert len(STARTER_FOOD_DEFINITIONS) >= 60

    display_names = {definition.display_name for definition in STARTER_FOOD_DEFINITIONS}
    assert {
        "Chicken breast",
        "Oatmeal",
        "Banana",
        "Grape tomatoes",
        "2% milk",
        "Hummus",
    }.issubset(display_names)

    for definition in STARTER_FOOD_DEFINITIONS:
        assert definition.display_name.strip()
        assert definition.aliases
        assert definition.search_terms
        assert definition.category.strip()


def test_high_confidence_source_record_promotes_with_aliases_provenance_and_macros(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _seed_cooked_chicken()

    report = promote_canonical_food_starter_set(limit=1)

    assert report.to_dict()["summary"] == {
        "matched": 1,
        "skipped_missing": 0,
        "skipped_ambiguous": 0,
        "skipped_raw_only": 0,
        "already_promoted": 0,
    }
    promoted = report.matched[0]
    assert promoted.display_name == "Chicken breast"
    assert promoted.canonical_food_id is not None
    assert promoted.canonical_display_name == "Chicken breast"
    assert promoted.source_name == USDA_SOURCE_NAME
    assert promoted.source_record_id == "100001"
    assert set(promoted.nutrients_synced) == {
        "Calories",
        "Protein",
        "Carbohydrate",
        "Fat",
    }

    aliases = {
        alias.alias
        for alias in get_aliases_for_canonical_food(promoted.canonical_food_id)
    }
    assert aliases >= {
        "chicken",
        "grilled chicken breast",
        ("Chicken, broilers or fryers, breast, meat only, cooked, roasted"),
    }

    nutrients = {
        nutrient.nutrient_name: nutrient.amount_per_100g
        for nutrient in get_nutrients_for_canonical_food(promoted.canonical_food_id)
    }
    assert nutrients == {
        "Calories": 165.0,
        "Protein": 31.0,
        "Carbohydrate": 0.0,
        "Fat": 3.6,
    }

    search_results = search_canonical_foods("grilled chicken breast")
    assert search_results[0].canonical_food.id == promoted.canonical_food_id


def test_starter_set_promotion_is_idempotent(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _seed_cooked_chicken()

    first = promote_canonical_food_starter_set(limit=1)
    second = promote_canonical_food_starter_set(limit=1)

    assert len(first.matched) == 1
    assert len(second.already_promoted) == 1
    assert (
        second.already_promoted[0].canonical_food_id
        == first.matched[0].canonical_food_id
    )
    assert _count_rows("canonical_foods") == 1
    assert _count_rows("food_source_links") == 1


def test_dry_run_reports_candidate_without_mutating_canonical_tables(
    tmp_path,
    monkeypatch,
) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _seed_cooked_chicken()

    report = promote_canonical_food_starter_set(dry_run=True, limit=1)

    assert report.dry_run is True
    assert len(report.matched) == 1
    assert report.matched[0].reason == "Dry run: candidate would be promoted."
    assert _count_rows("canonical_foods") == 0
    assert _count_rows("canonical_food_aliases") == 0
    assert _count_rows("canonical_food_nutrients") == 0
    assert _count_rows("food_source_links") == 0


def test_ambiguous_candidate_is_reported_not_promoted(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    _seed_cooked_chicken()
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="100002",
        raw_description=(
            "Chicken, broilers or fryers, breast, meat only, cooked, roasted"
        ),
        data_type="foundation_food",
        calories_per_100g=166.0,
        protein_g_per_100g=30.5,
        carbs_g_per_100g=0.0,
        fat_g_per_100g=3.7,
    )

    report = promote_canonical_food_starter_set(limit=1)

    assert len(report.skipped_ambiguous) == 1
    assert report.skipped_ambiguous[0].display_name == "Chicken breast"
    assert _count_rows("canonical_foods") == 0
    assert _count_rows("food_source_links") == 0


def test_missing_candidate_is_reported(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)

    report = promote_canonical_food_starter_set(limit=1)

    assert len(report.skipped_missing) == 1
    assert report.skipped_missing[0].display_name == "Chicken breast"
    assert report.skipped_missing[0].reason == (
        "No existing source record matched all search terms."
    )


def test_raw_chicken_only_is_reported_not_promoted(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="100003",
        raw_description="Chicken, breast, meat only, raw",
        data_type="foundation_food",
        calories_per_100g=120.0,
        protein_g_per_100g=22.5,
        carbs_g_per_100g=0.0,
        fat_g_per_100g=2.6,
    )

    report = promote_canonical_food_starter_set(limit=1)

    assert len(report.skipped_raw_only) == 1
    assert report.skipped_raw_only[0].display_name == "Chicken breast"
    assert _count_rows("canonical_foods") == 0
    assert _count_rows("food_source_links") == 0


def test_raw_produce_candidate_is_allowed(tmp_path, monkeypatch) -> None:
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name=USDA_SOURCE_NAME,
        source_record_id="321360",
        raw_description="Tomatoes, grape, raw",
        data_type="foundation_food",
        calories_per_100g=27.0,
        protein_g_per_100g=0.83,
        carbs_g_per_100g=5.51,
        fat_g_per_100g=0.63,
    )

    report = promote_canonical_food_starter_set(include_categories=("vegetables",))

    grape_tomatoes = [
        item for item in report.matched if item.display_name == "Grape tomatoes"
    ]
    assert len(grape_tomatoes) == 1
    assert grape_tomatoes[0].canonical_display_name == "Grape tomatoes"
    assert _count_rows("canonical_foods") == 1


def test_promoted_starter_food_is_searchable_and_loggable(
    tmp_path,
    monkeypatch,
) -> None:
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
    )

    report = promote_canonical_food_starter_set(
        include_categories=("dairy_fats_extras",)
    )
    hummus = next(item for item in report.matched if item.display_name == "Hummus")

    search_response = _client().get("/foods/canonical/search?q=commercial%20hummus")
    assert search_response.status_code == 200
    search_result = search_response.json()["results"][0]
    assert search_result["canonical_food_id"] == hummus.canonical_food_id
    assert search_result["display_name"] == "Hummus"
    assert search_result["source"] == {
        "source_name": USDA_SOURCE_NAME,
        "source_record_id": "321358",
    }

    log_response = _client().post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": hummus.canonical_food_id,
            "grams": 100,
            "entry_date": "2026-06-05",
        },
    )
    assert log_response.status_code == 200
    assert log_response.json()["nutrient_summary"] == {
        "calories": 229.0,
        "protein_g": 7.35,
        "carbohydrate_g": 14.9,
        "fat_g": 17.1,
    }
    assert get_daily_canonical_food_macro_totals(1, "2026-06-05") == {
        "entry_count": 1,
        "calories": 229.0,
        "protein_g": 7.35,
        "carbs_g": 14.9,
        "fat_g": 17.1,
    }


def test_starter_set_cli_help_is_available() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/promote_canonical_food_starter_set.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Promote high-confidence everyday canonical foods" in result.stdout
    assert "--db-path" in result.stdout
    assert "--dry-run" in result.stdout


def test_starter_set_cli_dry_run_writes_report_without_promoting(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = _seed_test_db(tmp_path, monkeypatch)
    _seed_cooked_chicken()
    report_path = tmp_path / "starter_set_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/promote_canonical_food_starter_set.py",
            "--db-path",
            str(db_path),
            "--dry-run",
            "--limit",
            "1",
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
    assert payload["summary"]["matched"] == 1

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
