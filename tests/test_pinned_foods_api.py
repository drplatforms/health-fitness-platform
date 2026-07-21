from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    search_canonical_foods,
    seed_starter_canonical_foods,
)
from services.nutrition_service import add_canonical_food_entry


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "pinned_foods.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    seed_starter_canonical_foods()
    return TestClient(app)


def _canonical_food_id(search_term: str) -> int:
    results = search_canonical_foods(search_term, limit=1)
    assert results
    return int(results[0].canonical_food.id)


def test_pinned_foods_are_user_scoped_idempotent_and_excluded_from_recents(
    tmp_path,
    monkeypatch,
) -> None:
    client = _client(tmp_path, monkeypatch)
    chicken_id = _canonical_food_id("chicken breast")
    banana_id = _canonical_food_id("banana")
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=chicken_id,
        grams=150,
        entry_date="2026-07-20",
    )
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=banana_id,
        grams=118,
        entry_date="2026-07-19",
    )

    endpoint = f"/nutrition/1/pinned-foods/canonical/{chicken_id}"
    assert client.put(endpoint).status_code == 200
    assert client.put(endpoint).status_code == 200

    pinned = client.get("/nutrition/1/pinned-foods").json()["results"]
    assert len(pinned) == 1
    assert pinned[0]["canonical_food_id"] == chicken_id
    assert pinned[0]["food_type"] == "canonical"
    assert pinned[0]["nutrient_summary"]["protein_g_per_100g"] > 0
    assert client.get("/nutrition/2/pinned-foods").json()["results"] == []

    recent = client.get("/nutrition/1/recent-canonical-foods").json()["results"]
    assert [item["canonical_food_id"] for item in recent] == [banana_id]

    deleted = client.delete(endpoint)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    restored_recent = client.get("/nutrition/1/recent-canonical-foods").json()[
        "results"
    ]
    assert [item["canonical_food_id"] for item in restored_recent] == [
        banana_id,
        chicken_id,
    ]


def test_personal_food_pin_uses_owned_identity_and_current_revision(
    tmp_path,
    monkeypatch,
) -> None:
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/nutrition/1/personal-foods",
        json={
            "display_name": "My Yogurt",
            "input_basis": "nutrition_label",
            "serving_name": "cup",
            "serving_grams": 170,
            "calories": 120,
            "protein_g": 15,
            "carbs_g": 8,
            "fat_g": 2,
        },
    ).json()["personal_food"]
    personal_food_id = created["id"]

    pinned_response = client.put(
        f"/nutrition/1/pinned-foods/personal/{personal_food_id}"
    )
    assert pinned_response.status_code == 200
    pinned = pinned_response.json()["pinned_food"]
    assert pinned["personal_food_id"] == personal_food_id
    assert pinned["display_name"] == "My Yogurt"
    assert pinned["serving_name"] == "cup"
    assert pinned["serving_grams"] == 170
    assert pinned["nutrient_summary"]["protein_g_per_100g"] > 0

    assert (
        client.put(f"/nutrition/2/pinned-foods/personal/{personal_food_id}").status_code
        == 404
    )


def test_pinned_food_endpoints_reject_invalid_or_missing_foods(
    tmp_path,
    monkeypatch,
) -> None:
    client = _client(tmp_path, monkeypatch)

    assert client.put("/nutrition/1/pinned-foods/other/1").status_code == 400
    assert client.put("/nutrition/1/pinned-foods/canonical/999999").status_code == 404
    assert client.get("/nutrition/999/pinned-foods").status_code == 404
