import csv
from pathlib import Path

from services.exercise_catalog_service import (
    CURATED_EXERCISE_CATALOG,
    EXERCISE_CATALOG_EXPANSION_V2_BATCH_1,
)
from services.exercise_instruction_seed_data import EXERCISE_INSTRUCTION_SEEDS
from services.exercise_prescription_measurement_seed_data import (
    EXERCISE_PRESCRIPTION_MEASUREMENT_SEEDS,
)
from services.exercise_taxonomy_seed_data import EXERCISE_TAXONOMY_SEEDS
from services.exercise_visual_media_provider_manifest import (
    APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS,
)

EVIDENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "project_memory"
    / "catalogs"
    / "exercise_catalog_expansion_v2_batch_1_matrix.csv"
)


def _evidence_rows() -> list[dict[str, str]]:
    with EVIDENCE_PATH.open(encoding="utf-8", newline="") as evidence_file:
        return list(csv.DictReader(evidence_file))


def _split(value: str) -> list[str]:
    return value.split("|") if value else []


def test_batch_is_exactly_60_unique_entries_appended_after_the_existing_240():
    rows = _evidence_rows()
    batch_names = [entry.name for entry in EXERCISE_CATALOG_EXPANSION_V2_BATCH_1]

    assert len(CURATED_EXERCISE_CATALOG) == 300
    assert len(CURATED_EXERCISE_CATALOG[:240]) == 240
    assert len(EXERCISE_CATALOG_EXPANSION_V2_BATCH_1) == 60
    assert CURATED_EXERCISE_CATALOG[240:] == EXERCISE_CATALOG_EXPANSION_V2_BATCH_1
    assert [row["canonical_name"] for row in rows] == batch_names
    assert len(batch_names) == len(set(batch_names)) == 60
    assert not set(batch_names).intersection(
        entry.name for entry in CURATED_EXERCISE_CATALOG[:240]
    )


def test_batch_evidence_reconciles_catalog_taxonomy_measurement_and_instructions():
    rows = _evidence_rows()
    catalog_by_name = {
        entry.name: entry for entry in EXERCISE_CATALOG_EXPANSION_V2_BATCH_1
    }
    taxonomy_by_name = {
        seed.canonical_exercise_name: seed for seed in EXERCISE_TAXONOMY_SEEDS
    }
    measurement_by_name = {
        seed.canonical_exercise_name: seed
        for seed in EXERCISE_PRESCRIPTION_MEASUREMENT_SEEDS
    }

    assert len(EXERCISE_TAXONOMY_SEEDS) == 300
    assert len(EXERCISE_PRESCRIPTION_MEASUREMENT_SEEDS) == 300
    assert len(EXERCISE_INSTRUCTION_SEEDS) == 300

    for row in rows:
        name = row["canonical_name"]
        catalog_entry = catalog_by_name[name]
        taxonomy = taxonomy_by_name[name]
        measurement = measurement_by_name[name]

        assert catalog_entry.exercise_type == row["exercise_type"]
        assert catalog_entry.movement_pattern == row["movement_pattern"]
        assert catalog_entry.primary_muscle_groups == _split(row["primary_muscles"])
        assert catalog_entry.equipment_required == _split(row["equipment_required"])
        assert catalog_entry.difficulty == row["difficulty"]
        assert taxonomy.family_slug == row["family_slug"]
        assert taxonomy.base_movement_slug == row["base_movement_slug"]
        assert taxonomy.visual_identity_slug == row["visual_identity_slug"]
        assert taxonomy.taxonomy_status == "reviewed"
        assert measurement.default_measurement_type == row["default_measurement_type"]
        assert list(measurement.allowed_measurement_types) == _split(
            row["allowed_measurement_types"]
        )
        assert name in EXERCISE_INSTRUCTION_SEEDS


def test_batch_provider_evidence_retirement_keeps_ids_but_adds_no_mappings():
    rows = _evidence_rows()
    expansion_visuals = {row["visual_identity_slug"] for row in rows}
    mapping_visuals = {
        mapping.visual_identity_slug
        for mapping in APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS
    }

    assert len(rows) == 60
    assert len({row["provider_exercise_id"] for row in rows}) == 60
    assert len(expansion_visuals) == 60
    assert {row["provider_media_decision"] for row in rows} == {
        "provider_media_not_approved"
    }
    assert not expansion_visuals.intersection(mapping_visuals)
    assert {row["provider_source_endpoint"] for row in rows} == {
        "https://oss.exercisedb.dev/api/v1/exercises"
    }

    for row in rows:
        assert row["provider_media_reason"].strip()
        assert "GIF expansion was intentionally retired" in row["provider_media_reason"]
