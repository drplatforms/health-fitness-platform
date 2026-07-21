from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_canonical_food,
    ensure_food_normalization_tables,
)


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "available_ingredients.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    return TestClient(app)


def test_available_ingredients_are_user_scoped_idempotent_and_removable(
    tmp_path,
    monkeypatch,
) -> None:
    client = _client(tmp_path, monkeypatch)
    rice = create_canonical_food("Jasmine Rice", "grain")

    endpoint = f"/nutrition/1/available-ingredients/canonical/{rice.id}"
    first_add = client.put(endpoint)
    second_add = client.put(endpoint)

    assert first_add.status_code == 200
    assert second_add.status_code == 200
    ingredient = first_add.json()["available_ingredient"]
    assert ingredient == second_add.json()["available_ingredient"]
    assert ingredient["canonical_food_id"] == rice.id
    assert ingredient["display_name"] == "Jasmine Rice"

    user_one = client.get("/nutrition/1/available-ingredients")
    user_two = client.get("/nutrition/2/available-ingredients")
    assert [item["canonical_food_id"] for item in user_one.json()["results"]] == [
        rice.id
    ]
    assert user_two.json()["results"] == []

    removed = client.delete(endpoint)
    removed_again = client.delete(endpoint)
    assert removed.status_code == 200
    assert removed.json()["deleted"] is True
    assert removed_again.status_code == 200
    assert removed_again.json()["deleted"] is False
    assert client.get("/nutrition/1/available-ingredients").json()["results"] == []


def test_available_ingredients_support_large_alphabetized_collections(
    tmp_path,
    monkeypatch,
) -> None:
    client = _client(tmp_path, monkeypatch)
    foods = [
        create_canonical_food(f"Test Ingredient {index:02d}", "generic")
        for index in range(40, 0, -1)
    ]

    for food in foods:
        response = client.put(f"/nutrition/1/available-ingredients/canonical/{food.id}")
        assert response.status_code == 200

    results = client.get("/nutrition/1/available-ingredients").json()["results"]
    assert len(results) == 40
    assert [item["display_name"] for item in results] == sorted(
        item["display_name"] for item in results
    )
    assert all(
        set(item)
        == {
            "canonical_food_id",
            "display_name",
            "original_display_name",
            "custom_display_name",
            "food_type",
            "added_at",
        }
        for item in results
    )


def test_available_ingredient_endpoints_reject_missing_foods_or_users(
    tmp_path,
    monkeypatch,
) -> None:
    client = _client(tmp_path, monkeypatch)
    food = create_canonical_food("Garden Tomato", "produce")

    assert (
        client.put("/nutrition/1/available-ingredients/canonical/999999").status_code
        == 404
    )
    assert (
        client.put(
            f"/nutrition/999/available-ingredients/canonical/{food.id}"
        ).status_code
        == 404
    )
    assert client.get("/nutrition/999/available-ingredients").status_code == 404


def test_starter_groups_resolve_to_unique_existing_canonical_foods(
    tmp_path,
    monkeypatch,
) -> None:
    client = _client(tmp_path, monkeypatch)

    response = client.get("/foods/canonical/available-ingredient-starters")

    assert response.status_code == 200
    groups = response.json()["groups"]
    assert [group["title"] for group in groups] == [
        "Proteins",
        "Grains & starches",
        "Beans & legumes",
        "Dairy",
        "Produce",
        "Pantry basics",
        "Herbs & spices",
    ]
    assert all(group["items"] for group in groups)

    items = [item for group in groups for item in group["items"]]
    canonical_food_ids = [item["canonical_food_id"] for item in items]
    assert len(canonical_food_ids) == len(set(canonical_food_ids))

    selected_id = groups[0]["items"][0]["canonical_food_id"]
    added = client.put(f"/nutrition/1/available-ingredients/canonical/{selected_id}")
    assert added.status_code == 200
    assert added.json()["available_ingredient"]["canonical_food_id"] == selected_id
