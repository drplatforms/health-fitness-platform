from __future__ import annotations

import database
from models.barcode_food_models import BarcodeFoodCandidate, ProviderLookupResult
from services.barcode_food_service import (
    materialize_barcode_food,
    normalize_barcode,
    resolve_barcode_food,
)
from services.food_normalization_service import (
    create_canonical_food,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    get_nutrients_for_canonical_food,
    link_canonical_food_to_source,
)
from services.nutrition_serving_unit_service import (
    get_active_serving_units_for_canonical_food,
)


class StubProvider:
    def __init__(self, result: ProviderLookupResult) -> None:
        self.result = result
        self.calls = 0

    def lookup(self, barcode):
        self.calls += 1
        return self.result


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _candidate(
    *,
    barcode: str = "036000291452",
    source_name: str = "USDA FoodData Central",
    source_record_id: str = "fdc-1",
    product_name: str = "Protein Bar",
    brand_name: str = "Brand A",
    serving_size: float | None = 50,
    serving_size_unit: str | None = "g",
) -> BarcodeFoodCandidate:
    return BarcodeFoodCandidate(
        source_name=source_name,
        source_record_id=source_record_id,
        barcode=barcode,
        normalized_gtin=normalize_barcode(barcode).normalized_gtin,
        product_name=product_name,
        brand_name=brand_name,
        calories_per_100g=250,
        protein_g_per_100g=20,
        carbs_g_per_100g=30,
        fat_g_per_100g=8,
        serving_size=serving_size,
        serving_size_unit=serving_size_unit,
        serving_label="1 bar" if serving_size_unit == "g" else None,
        source_payload={"bounded": True},
    )


def _raw_candidate(**overrides):
    candidate = _candidate(**overrides)
    return create_raw_food_source_record(
        source_name=candidate.source_name,
        source_record_id=candidate.source_record_id,
        raw_description=candidate.product_name,
        brand_name=candidate.brand_name,
        data_type="branded",
        gtin_upc=candidate.barcode,
        serving_size=candidate.serving_size,
        serving_size_unit=candidate.serving_size_unit,
        calories_per_100g=candidate.calories_per_100g,
        protein_g_per_100g=candidate.protein_g_per_100g,
        carbs_g_per_100g=candidate.carbs_g_per_100g,
        fat_g_per_100g=candidate.fat_g_per_100g,
        source_payload={
            **candidate.source_payload,
            "_barcode_serving_label": candidate.serving_label,
        },
    )


def test_barcode_normalization_preserves_equivalent_gtin_identity():
    upc = normalize_barcode("036000291452", "UPC_A")
    ean13 = normalize_barcode("0036000291452", "EAN_13")
    assert upc.normalized_gtin == ean13.normalized_gtin == "00036000291452"
    assert "036000291452" in upc.lookup_variants

    assert normalize_barcode("96385074", "EAN_8").normalized_gtin == "00000096385074"
    assert normalize_barcode("04252614", "UPC_E").lookup_variants[1] == "042100005264"
    assert (
        normalize_barcode("10012345000017", "GTIN_14").normalized_gtin
        == "10012345000017"
    )


def test_invalid_barcode_and_manual_ambiguity_are_rejected():
    assert resolve_barcode_food("036000291453").status == "invalid_barcode"
    assert resolve_barcode_food("425261", "UPC_E").status == "invalid_barcode"
    assert resolve_barcode_food("not-a-code").status == "invalid_barcode"


def test_local_linked_canonical_hit_skips_remote_providers(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_candidate()
    canonical = create_canonical_food("Locally Saved Bar", food_type="branded")
    link_canonical_food_to_source(canonical.id, raw.id)
    unavailable = StubProvider(ProviderLookupResult("unavailable", "unused"))

    result = resolve_barcode_food(
        "036000291452",
        usda_provider=unavailable,
        open_food_facts_provider=unavailable,
    )

    assert result.status == "resolved"
    assert result.provider == "local"
    assert result.canonical_food["canonical_food_id"] == canonical.id
    assert unavailable.calls == 0


def test_complete_local_raw_candidate_skips_remote_providers(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_candidate()
    unavailable = StubProvider(ProviderLookupResult("unavailable", "unused"))

    result = resolve_barcode_food(
        "036000291452",
        usda_provider=unavailable,
        open_food_facts_provider=unavailable,
    )

    assert result.status == "candidate"
    assert result.provider == "local_raw"
    assert result.candidate.raw_food_source_record_id == raw.id
    assert unavailable.calls == 0


def test_usda_fuzzy_miss_falls_back_to_off_and_caches_raw_candidate(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    usda = StubProvider(ProviderLookupResult("not_found", "USDA FoodData Central"))
    off = StubProvider(
        ProviderLookupResult(
            "found",
            "Open Food Facts",
            _candidate(source_name="Open Food Facts", source_record_id="036000291452"),
        )
    )

    first = resolve_barcode_food(
        "036000291452", usda_provider=usda, open_food_facts_provider=off
    )
    assert first.status == "candidate"
    assert first.provider == "Open Food Facts"
    assert first.candidate.raw_food_source_record_id is not None
    assert usda.calls == 1
    assert off.calls == 1

    must_not_run = StubProvider(ProviderLookupResult("unavailable", "unused"))
    second = resolve_barcode_food(
        "036000291452",
        usda_provider=must_not_run,
        open_food_facts_provider=must_not_run,
    )
    assert second.status == "candidate"
    assert second.provider == "local_raw"
    assert must_not_run.calls == 0


def test_provider_availability_and_incomplete_states_are_distinct(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    unavailable = StubProvider(ProviderLookupResult("unavailable", "provider"))
    result = resolve_barcode_food(
        "036000291452",
        usda_provider=unavailable,
        open_food_facts_provider=unavailable,
    )
    assert result.status == "provider_unavailable"

    incomplete = _candidate()
    incomplete = BarcodeFoodCandidate(**{**incomplete.__dict__, "fat_g_per_100g": None})
    result = resolve_barcode_food(
        "036000291452",
        usda_provider=StubProvider(
            ProviderLookupResult("incomplete", "USDA FoodData Central", incomplete)
        ),
        open_food_facts_provider=StubProvider(
            ProviderLookupResult("not_found", "Open Food Facts")
        ),
    )
    assert result.status == "incomplete"


def test_materialization_is_idempotent_and_creates_macros_link_and_gram_serving(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_candidate()
    expected = normalize_barcode(raw.gtin_upc).normalized_gtin

    first = materialize_barcode_food(raw.id, expected)
    second = materialize_barcode_food(raw.id, expected)

    assert first.status == second.status == "resolved"
    first_id = first.canonical_food["canonical_food_id"]
    assert second.canonical_food["canonical_food_id"] == first_id
    nutrients = {
        nutrient.nutrient_name: nutrient.amount_per_100g
        for nutrient in get_nutrients_for_canonical_food(first_id)
    }
    assert nutrients == {
        "Calories": 250.0,
        "Carbohydrate": 30.0,
        "Fat": 8.0,
        "Protein": 20.0,
    }
    serving_units = get_active_serving_units_for_canonical_food(first_id)
    assert len(serving_units) == 1
    assert serving_units[0].grams_default == 50
    assert serving_units[0].display_name == "1 bar"


def test_same_name_different_barcodes_never_merge_or_overwrite_macros(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    raw_a = _raw_candidate()
    raw_b = _raw_candidate(
        barcode="012345678905",
        source_record_id="fdc-2",
        brand_name="Brand B",
    )

    result_a = materialize_barcode_food(
        raw_a.id, normalize_barcode(raw_a.gtin_upc).normalized_gtin
    )
    result_b = materialize_barcode_food(
        raw_b.id, normalize_barcode(raw_b.gtin_upc).normalized_gtin
    )

    id_a = result_a.canonical_food["canonical_food_id"]
    id_b = result_b.canonical_food["canonical_food_id"]
    assert id_a != id_b
    assert (
        result_a.canonical_food["display_name"]
        != result_b.canonical_food["display_name"]
    )


def test_equivalent_barcode_from_second_source_reuses_one_canonical_food(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    usda = _raw_candidate()
    off = _raw_candidate(
        source_name="Open Food Facts",
        source_record_id="036000291452",
    )
    expected = normalize_barcode("036000291452").normalized_gtin

    first = materialize_barcode_food(usda.id, expected)
    second = materialize_barcode_food(off.id, expected)

    assert (
        first.canonical_food["canonical_food_id"]
        == second.canonical_food["canonical_food_id"]
    )
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT raw_food_source_record_id FROM food_source_links WHERE canonical_food_id = ?",
        (first.canonical_food["canonical_food_id"],),
    ).fetchall()
    conn.close()
    assert {row["raw_food_source_record_id"] for row in rows} == {usda.id, off.id}


def test_barcode_collision_returns_conflict_without_silent_choice(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    raw_a = _raw_candidate(source_record_id="source-a")
    raw_b = _raw_candidate(source_name="Open Food Facts", source_record_id="source-b")
    food_a = create_canonical_food("Collision A", food_type="branded")
    food_b = create_canonical_food("Collision B", food_type="branded")
    link_canonical_food_to_source(food_a.id, raw_a.id)
    link_canonical_food_to_source(food_b.id, raw_b.id)

    result = resolve_barcode_food("036000291452")

    assert result.status == "conflict"
    assert result.conflict_canonical_food_ids == (food_a.id, food_b.id)


def test_volume_only_serving_does_not_create_fake_gram_unit(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_candidate(serving_size=250, serving_size_unit="ml")

    result = materialize_barcode_food(
        raw.id, normalize_barcode(raw.gtin_upc).normalized_gtin
    )

    assert result.status == "resolved"
    assert (
        get_active_serving_units_for_canonical_food(
            result.canonical_food["canonical_food_id"]
        )
        == []
    )


def test_expected_gtin_mismatch_missing_raw_and_incomplete_raw_are_safe(
    tmp_path, monkeypatch
):
    _seed_test_db(tmp_path, monkeypatch)
    raw = _raw_candidate()
    assert (
        materialize_barcode_food(
            raw.id, normalize_barcode("012345678905").normalized_gtin
        ).status
        == "invalid_barcode"
    )
    assert (
        materialize_barcode_food(
            999999, normalize_barcode("036000291452").normalized_gtin
        ).status
        == "not_found"
    )

    conn = database.get_connection()
    conn.execute(
        "UPDATE raw_food_source_records SET fat_g_per_100g = NULL WHERE id = ?",
        (raw.id,),
    )
    conn.commit()
    conn.close()
    assert (
        materialize_barcode_food(
            raw.id, normalize_barcode("036000291452").normalized_gtin
        ).status
        == "incomplete"
    )
