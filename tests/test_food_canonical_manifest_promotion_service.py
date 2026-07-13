from __future__ import annotations

import hashlib
import json
import sys

import pytest

import database
import scripts.promote_canonical_food_manifest as manifest_cli
import services.food_canonical_manifest_promotion_service as manifest_service
from database import get_connection, initialize_database
from services.food_canonical_manifest_promotion_service import (
    execute_manifest,
    load_manifest,
)
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
    link_canonical_food_to_source,
)

SOURCE_NAME = "USDA FoodData Central"
DATA_TYPE = "sr_legacy_food"
CATEGORY = "Cereal Grains and Pasta"


def _raw_row(
    source_record_id: str = "manifest-1",
    raw_description: str = "Arrowroot flour",
    *,
    calories: float | None = 357.0,
    protein: float | None = 0.3,
    carbs: float | None = 88.15,
    fat: float | None = 0.1,
) -> dict[str, object]:
    return {
        "source_record_id": source_record_id,
        "raw_description": raw_description,
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
    }


def _seed_raw(tmp_path, monkeypatch, *rows: dict[str, object]) -> None:
    db_path = tmp_path / "manifest_test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    initialize_database()
    ensure_food_normalization_tables()
    resolved_rows = rows or (_raw_row(),)
    conn = get_connection()
    conn.executemany(
        """INSERT INTO raw_food_source_records (
        source_name, source_record_id, raw_description, data_type, food_category,
        calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                SOURCE_NAME,
                row["source_record_id"],
                row["raw_description"],
                DATA_TYPE,
                CATEGORY,
                row["calories"],
                row["protein"],
                row["carbs"],
                row["fat"],
            )
            for row in resolved_rows
        ],
    )
    conn.commit()
    conn.close()


def _manifest_item(
    *,
    sequence: int = 1,
    source_record_id: str = "manifest-1",
    raw_description: str = "Arrowroot flour",
    canonical_display_name: str = "Arrowroot Flour",
    aliases: list[str] | None = None,
    action: str = "CREATE_NET_NEW_CANONICAL_FOOD",
    calories: float | None = 357.0,
    protein: float | None = 0.3,
    carbs: float | None = 88.15,
    fat: float | None = 0.1,
) -> dict[str, object]:
    return {
        "sequence": sequence,
        "proposed_action": action,
        "source_name": SOURCE_NAME,
        "data_type": DATA_TYPE,
        "source_record_id": source_record_id,
        "raw_description": raw_description,
        "food_category": CATEGORY,
        "canonical_display_name": canonical_display_name,
        "normalized_name": canonical_display_name.casefold(),
        "aliases": aliases if aliases is not None else [raw_description],
        "calories_per_100g": calories,
        "protein_g_per_100g": protein,
        "carbs_g_per_100g": carbs,
        "fat_g_per_100g": fat,
    }


def _write_manifest(path, items: list[dict[str, object]]) -> str:
    path.write_text(json.dumps({"items": items}), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table_counts() -> dict[str, int]:
    conn = get_connection()
    counts = {
        table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in (
            "canonical_foods",
            "canonical_food_aliases",
            "canonical_food_nutrients",
            "food_source_links",
            "food_entries",
            "raw_food_source_records",
        )
    }
    conn.close()
    return counts


def _linked_canonical(
    *,
    raw_id: int,
    nutrient_values: dict[str, float],
) -> None:
    food = create_canonical_food("Arrowroot Flour")
    for nutrient_name, value in nutrient_values.items():
        create_canonical_food_nutrient(
            food.id,
            nutrient_name,
            "kcal" if nutrient_name == "Calories" else "g",
            value,
        )
    link_canonical_food_to_source(food.id, raw_id)


def test_cli_rejects_real_database_before_initialization(tmp_path, monkeypatch) -> None:
    real_database_path = tmp_path / "fitness_ai.db"
    monkeypatch.setattr(manifest_service, "REAL_DATABASE_PATH", real_database_path)
    calls: list[str] = []
    monkeypatch.setattr(
        manifest_cli, "initialize_database", lambda: calls.append("initialize")
    )
    monkeypatch.setattr(
        manifest_cli,
        "ensure_food_normalization_tables",
        lambda: calls.append("ensure"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "promote_canonical_food_manifest.py",
            "--db-path",
            str(real_database_path),
            "--manifest-path",
            str(tmp_path / "manifest.json"),
            "--expected-sha256",
            "0" * 64,
            "--expected-item-count",
            "1",
            "--report-path",
            str(tmp_path / "report.json"),
        ],
    )

    with pytest.raises(ValueError, match="real fitness_ai.db"):
        manifest_cli.main()

    assert calls == []


def test_manifest_promotion_is_idempotent(tmp_path, monkeypatch) -> None:
    _seed_raw(tmp_path, monkeypatch)
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(manifest_path, [_manifest_item()])

    first = execute_manifest(
        manifest_path, expected_sha256=digest, expected_item_count=1
    )
    second = execute_manifest(
        manifest_path, expected_sha256=digest, expected_item_count=1
    )

    assert first["summary"] == {
        "ALIGNED_NO_OP": 0,
        "ALIGNED_IDEMPOTENT": 0,
        "PROMOTED": 1,
    }
    assert second["summary"] == {
        "ALIGNED_NO_OP": 0,
        "ALIGNED_IDEMPOTENT": 1,
        "PROMOTED": 0,
    }
    assert first["post_table_counts"]["canonical_foods"] == 1
    assert second["post_table_counts"] == first["post_table_counts"]


@pytest.mark.parametrize("collision_kind", ["canonical_name", "canonical_alias"])
def test_manifest_alias_collision_with_existing_catalog_is_blocked(
    tmp_path, monkeypatch, collision_kind
) -> None:
    _seed_raw(tmp_path, monkeypatch)
    reserved_alias = "Reserved catalog term"
    existing = create_canonical_food("Existing Food")
    if collision_kind == "canonical_name":
        existing = create_canonical_food(reserved_alias)
    else:
        create_canonical_food_alias(existing.id, reserved_alias)
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(manifest_path, [_manifest_item(aliases=[reserved_alias])])

    with pytest.raises(ValueError, match="collision"):
        execute_manifest(manifest_path, expected_sha256=digest, expected_item_count=1)


def test_manifest_rejects_cross_item_duplicate_aliases(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest_path,
        [
            _manifest_item(aliases=["Shared alias"]),
            _manifest_item(
                sequence=2,
                source_record_id="manifest-2",
                raw_description="Millet flour",
                canonical_display_name="Millet Flour",
                aliases=["shared ALIAS"],
            ),
        ],
    )

    with pytest.raises(ValueError, match="shared by different items"):
        load_manifest(manifest_path, expected_sha256=digest, expected_item_count=2)


def test_manifest_rejects_alias_equal_to_another_canonical_name(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest_path,
        [
            _manifest_item(aliases=["Millet Flour"]),
            _manifest_item(
                sequence=2,
                source_record_id="manifest-2",
                raw_description="Millet flour",
                canonical_display_name="Millet Flour",
            ),
        ],
    )

    with pytest.raises(ValueError, match="another item's canonical name"):
        load_manifest(manifest_path, expected_sha256=digest, expected_item_count=2)


def test_manifest_rejects_duplicate_aliases_within_item(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest_path,
        [_manifest_item(aliases=["Arrowroot starch", "arrowroot STARCH"])],
    )

    with pytest.raises(ValueError, match="duplicate aliases"):
        load_manifest(manifest_path, expected_sha256=digest, expected_item_count=1)


def test_alignment_rejects_source_null_canonical_present_macro(
    tmp_path, monkeypatch
) -> None:
    _seed_raw(tmp_path, monkeypatch, _raw_row(calories=None))
    _linked_canonical(
        raw_id=1,
        nutrient_values={
            "Calories": 357.0,
            "Protein": 0.3,
            "Carbohydrate": 88.15,
            "Fat": 0.1,
        },
    )
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest_path,
        [_manifest_item(action="VERIFY_ALREADY_LINKED_NO_OP", calories=None)],
    )

    with pytest.raises(ValueError, match="macros are not aligned"):
        execute_manifest(manifest_path, expected_sha256=digest, expected_item_count=1)


def test_alignment_rejects_source_present_canonical_absent_macro(
    tmp_path, monkeypatch
) -> None:
    _seed_raw(tmp_path, monkeypatch)
    _linked_canonical(
        raw_id=1,
        nutrient_values={"Protein": 0.3, "Carbohydrate": 88.15, "Fat": 0.1},
    )
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest_path,
        [_manifest_item(action="VERIFY_ALREADY_LINKED_NO_OP")],
    )

    with pytest.raises(ValueError, match="macros are not aligned"):
        execute_manifest(manifest_path, expected_sha256=digest, expected_item_count=1)


def test_final_item_mismatch_causes_zero_earlier_writes(tmp_path, monkeypatch) -> None:
    _seed_raw(
        tmp_path,
        monkeypatch,
        _raw_row(),
        _raw_row("manifest-2", "Millet flour"),
    )
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(
        manifest_path,
        [
            _manifest_item(),
            _manifest_item(
                sequence=2,
                source_record_id="manifest-2",
                raw_description="Incorrect final evidence",
                canonical_display_name="Millet Flour",
            ),
        ],
    )
    calls: list[int] = []
    monkeypatch.setattr(
        manifest_service,
        "promote_raw_source_record_to_canonical",
        lambda raw_id, **kwargs: calls.append(raw_id),
    )
    before = _table_counts()

    with pytest.raises(ValueError, match="Raw source evidence mismatch"):
        execute_manifest(manifest_path, expected_sha256=digest, expected_item_count=2)

    assert calls == []
    assert _table_counts() == before


def test_manifest_rejects_bad_sha_and_non_contiguous_sequences(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    digest = _write_manifest(manifest_path, [_manifest_item(sequence=2)])

    with pytest.raises(ValueError, match="SHA-256"):
        load_manifest(manifest_path, expected_sha256="0" * 64)
    with pytest.raises(ValueError, match="contiguous"):
        load_manifest(manifest_path, expected_sha256=digest)
