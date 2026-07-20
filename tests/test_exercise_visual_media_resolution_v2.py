import csv
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

import database
from services import exercise_catalog_service
from services import exercise_visual_media_service as visual_media_service
from services.exercise_catalog_service import (
    clear_exercise_catalog_cache,
    get_exercise_catalog,
    get_exercise_taxonomy,
    seed_exercise_form_media,
    seed_exercise_taxonomy,
)
from services.exercise_visual_media_provider_manifest import (
    APPROVED_ASCENDAPI_FREE_V1_MAPPINGS_BY_VISUAL_IDENTITY,
    APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS,
    ASCENDAPI_FREE_V1_SOURCE_ENDPOINT,
    SHARED_LOCAL_VISUAL_IDENTITY_OWNERS,
)


@pytest.fixture(autouse=True)
def pytest_owned_database(tmp_path, monkeypatch):
    test_db = tmp_path / "fitness_ai_visual_media_v2_test.db"
    canonical_db = Path(database.__file__).resolve().parent / "fitness_ai.db"
    assert test_db.resolve() != canonical_db.resolve()

    monkeypatch.setattr(database, "DB_PATH", test_db)
    monkeypatch.delenv("EXERCISE_VISUAL_MEDIA_PROVIDER", raising=False)
    clear_exercise_catalog_cache()
    yield test_db
    clear_exercise_catalog_cache()


def _seed_visual_media_runtime():
    database.initialize_database()
    seed_exercise_taxonomy()
    seed_exercise_form_media()


def _catalog_id(name: str) -> int:
    entry = next(entry for entry in get_exercise_catalog() if entry.name == name)
    assert entry.id is not None
    return entry.id


def _configure_ascendapi_free_v1(monkeypatch):
    monkeypatch.setenv("EXERCISE_VISUAL_MEDIA_PROVIDER", "ascendapi_free_v1")


def _complete_rows(table_name: str) -> tuple[tuple[str, ...], list[tuple]]:
    with sqlite3.connect(database.DB_PATH) as conn:
        columns = tuple(
            row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")')
        )
        rows = conn.execute(f'SELECT * FROM "{table_name}" ORDER BY rowid').fetchall()
    return columns, rows


def _shared_local_catalog_state() -> dict[str, tuple[tuple[str, ...], list[tuple]]]:
    return {
        table_name: _complete_rows(table_name)
        for table_name in (
            "exercise_catalog_exercises",
            "exercise_equipment_requirements",
            "exercise_catalog_taxonomy",
        )
    }


def test_reviewed_manifest_is_exact_provider_allowlist():
    assert (
        ASCENDAPI_FREE_V1_SOURCE_ENDPOINT
        == "https://oss.exercisedb.dev/api/v1/exercises"
    )
    assert len(APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS) == 46
    assert len(APPROVED_ASCENDAPI_FREE_V1_MAPPINGS_BY_VISUAL_IDENTITY) == 46
    assert len(SHARED_LOCAL_VISUAL_IDENTITY_OWNERS) == 3
    assert {
        mapping.provider for mapping in APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS
    } == {"ascendapi_free_v1"}
    assert all(
        mapping.animated_media_url.startswith("https://static.exercisedb.dev/media/")
        and mapping.animated_media_url.endswith(".gif")
        and mapping.review_provenance
        for mapping in APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS
    )


def test_provider_manifest_matches_only_accepted_reassessment_rows():
    evidence_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "project_memory"
        / "spikes"
        / "ascendapi_structured_coverage_reassessment_matrix_v1.csv"
    )
    with evidence_path.open(encoding="utf-8", newline="") as evidence_file:
        approved_evidence = {
            row["visual_identity_slug"]: (
                row["provider_name"],
                row["provider_exercise_id"],
                row["provider_gif_url"],
            )
            for row in csv.DictReader(evidence_file)
            if row["structured_status"] == "ascendapi_approved_exact"
        }

    expansion_evidence_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "project_memory"
        / "catalogs"
        / "exercise_catalog_expansion_v2_batch_1_matrix.csv"
    )
    with expansion_evidence_path.open(encoding="utf-8", newline="") as evidence_file:
        expansion_rows = list(csv.DictReader(evidence_file))

    assert len(expansion_rows) == 60
    assert {row["provider_media_decision"] for row in expansion_rows} == {
        "provider_media_not_approved"
    }
    assert not {row["visual_identity_slug"] for row in expansion_rows}.intersection(
        approved_evidence
    )

    assert {
        mapping.visual_identity_slug: (
            mapping.provider_exercise_name,
            mapping.provider_exercise_id,
            mapping.animated_media_url,
        )
        for mapping in APPROVED_ASCENDAPI_FREE_V1_MEDIA_MAPPINGS
    } == approved_evidence


def test_direct_local_media_outranks_provider_without_provider_lookup(monkeypatch):
    _seed_visual_media_runtime()
    _configure_ascendapi_free_v1(monkeypatch)
    push_up_id = _catalog_id("Push-Up")

    def unexpected_provider_lookup():
        raise AssertionError("direct local media must not initialize a provider")

    monkeypatch.setattr(
        visual_media_service,
        "get_configured_visual_media_provider",
        unexpected_provider_lookup,
    )

    result = visual_media_service.resolve_exercise_visual_media(push_up_id)

    assert result.resolution.resolution_mode == "direct_local"
    assert result.resolution.source_catalog_exercise_id == push_up_id
    assert [item.media_type for item in result.media] == [
        "static_image",
        "static_image",
    ]


@pytest.mark.parametrize(
    ("requested_name", "source_name", "visual_identity_slug"),
    (
        ("Tempo Push-Up", "Push-Up", "visual_push_up"),
        ("Dumbbell Tempo Goblet Squat", "Goblet Squat", "visual_goblet_squat"),
        ("Treadmill Recovery Walk", "Treadmill Walk", "visual_treadmill_walk"),
    ),
)
def test_exact_shared_local_visual_identity_resolution_prevents_provider_lookup(
    monkeypatch,
    requested_name,
    source_name,
    visual_identity_slug,
):
    _seed_visual_media_runtime()
    requested_id = _catalog_id(requested_name)
    source_id = _catalog_id(source_name)
    assert (
        get_exercise_taxonomy(requested_id).visual_identity_slug == visual_identity_slug
    )
    assert get_exercise_taxonomy(source_id).visual_identity_slug == visual_identity_slug

    catalog_state_before = _shared_local_catalog_state()
    clear_exercise_catalog_cache()
    monkeypatch.setattr(
        exercise_catalog_service,
        "seed_exercise_catalog",
        lambda: pytest.fail("shared-local resolution must not seed the catalog"),
    )
    monkeypatch.setattr(
        visual_media_service,
        "get_configured_visual_media_provider",
        lambda: pytest.fail("shared local media must not initialize a provider"),
    )
    result = visual_media_service.resolve_exercise_visual_media(requested_id)

    assert result.resolution.resolution_mode == "shared_local_visual_identity"
    assert result.resolution.requested_catalog_exercise_id == requested_id
    assert result.resolution.source_catalog_exercise_id == source_id
    assert {item.source_catalog_exercise_id for item in result.media} == {source_id}
    assert {item.media_type for item in result.media} == {"static_image"}
    assert _shared_local_catalog_state() == catalog_state_before


def test_ambiguous_shared_local_direct_media_owners_fail_explicitly():
    _seed_visual_media_runtime()
    requested_id = _catalog_id("Tempo Push-Up")
    source_id = _catalog_id("Push-Up")
    ambiguous_owner_id = next(
        entry.id
        for entry in get_exercise_catalog()
        if entry.id is not None
        and entry.id != source_id
        and visual_media_service.get_exercise_form_media(entry.id)
    )

    with sqlite3.connect(database.DB_PATH) as conn:
        conn.execute(
            """
            UPDATE exercise_catalog_taxonomy
            SET visual_identity_slug = ?
            WHERE exercise_id = ?
            """,
            ("visual_push_up", ambiguous_owner_id),
        )

    with pytest.raises(
        ValueError,
        match="Multiple direct local-media owners found for shared visual identity",
    ):
        visual_media_service.resolve_exercise_visual_media(requested_id)


def test_configured_free_v1_mapping_needs_no_key_and_normalizes_animated_media(
    monkeypatch,
):
    _seed_visual_media_runtime()
    _configure_ascendapi_free_v1(monkeypatch)

    result = visual_media_service.resolve_exercise_visual_media(
        _catalog_id("Back Squat")
    )

    assert result.resolution.resolution_mode == "provider"
    assert result.resolution.source_type == "remote_provider"
    assert result.resolution.provider == "ascendapi_free_v1"
    assert result.resolution.provider_exercise_id == "DhMl549"
    assert result.resolution.source_catalog_exercise_id is None
    assert len(result.media) == 1
    item = result.media[0]
    assert item.media_key == "ascendapi_free_v1:DhMl549"
    assert item.media_type == "animated_image"
    assert item.role == "movement_demo"
    assert item.url == "https://static.exercisedb.dev/media/DhMl549.gif"
    assert item.source_type == "remote_provider"
    assert item.attribution == (
        "Animated demonstration provided by ExerciseDB / AscendAPI Free V1."
    )
    assert "non-commercial prototype phase" in item.provenance
    assert "monetized or SaaS launch" in item.provenance


def test_missing_configuration_and_provider_failure_degrade_to_text_only(monkeypatch):
    _seed_visual_media_runtime()
    back_squat_id = _catalog_id("Back Squat")

    assert (
        visual_media_service.resolve_exercise_visual_media(
            back_squat_id
        ).resolution.resolution_mode
        == "none"
    )

    monkeypatch.setenv("EXERCISE_VISUAL_MEDIA_PROVIDER", "ascendapi")
    assert (
        visual_media_service.resolve_exercise_visual_media(
            back_squat_id
        ).resolution.resolution_mode
        == "none"
    )

    _configure_ascendapi_free_v1(monkeypatch)
    monkeypatch.setattr(
        visual_media_service.AscendApiFreeV1VisualMediaAdapter,
        "resolve",
        lambda *_: (_ for _ in ()).throw(OSError("provider unavailable")),
    )
    failed_result = visual_media_service.resolve_exercise_visual_media(back_squat_id)

    assert failed_result.media == []
    assert failed_result.resolution.resolution_mode == "none"
    assert failed_result.resolution.visual_identity_slug == "visual_back_squat"


def test_unapproved_or_materially_distinct_identity_never_initializes_provider(
    monkeypatch,
):
    _seed_visual_media_runtime()
    _configure_ascendapi_free_v1(monkeypatch)
    band_biceps_curl_id = _catalog_id("Band Biceps Curl")

    monkeypatch.setattr(
        visual_media_service,
        "get_configured_visual_media_provider",
        lambda: pytest.fail("unapproved identity must not initialize a provider"),
    )
    result = visual_media_service.resolve_exercise_visual_media(band_biceps_curl_id)

    assert result.media == []
    assert result.resolution.resolution_mode == "none"
    assert result.resolution.visual_identity_slug not in (
        APPROVED_ASCENDAPI_FREE_V1_MAPPINGS_BY_VISUAL_IDENTITY
    )


def test_configured_provider_coverage_reconciles_exactly():
    _seed_visual_media_runtime()
    entries = get_exercise_catalog()
    assert len(entries) == 300
    assert (
        len(
            {
                get_exercise_taxonomy(entry.id).visual_identity_slug
                for entry in entries
                if entry.id is not None
            }
        )
        == 291
    )

    previous_provider = visual_media_service.get_configured_visual_media_provider
    visual_media_service.get_configured_visual_media_provider = lambda: (
        visual_media_service.AscendApiFreeV1VisualMediaAdapter()
    )
    try:
        results = [
            visual_media_service.resolve_exercise_visual_media(entry.id)
            for entry in entries
            if entry.id is not None
        ]
    finally:
        visual_media_service.get_configured_visual_media_provider = previous_provider

    counts = Counter(result.resolution.resolution_mode for result in results)
    assert counts == {
        "direct_local": 83,
        "shared_local_visual_identity": 3,
        "provider": 52,
        "none": 162,
    }
    assert sum(bool(result.media) for result in results) == 138
