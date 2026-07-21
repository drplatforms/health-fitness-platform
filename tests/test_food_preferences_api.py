from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_canonical_food,
    ensure_food_normalization_tables,
)


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "food_preferences.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    return TestClient(app)


def test_food_preferences_are_user_scoped_and_neutral_is_not_stored(
    tmp_path, monkeypatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    food = create_canonical_food("Roasted Chickpeas", "generic", default_grams=100)

    loved = client.put(
        f"/nutrition/1/food-preferences/canonical/{food.id}",
        json={"preference": "love"},
    )

    assert loved.status_code == 200
    assert loved.json()["food_preference"] == {
        "canonical_food_id": food.id,
        "preference": "love",
        "is_hard_exclusion": False,
    }
    assert client.get("/nutrition/2/food-preferences").json()["results"] == []
    user_one = client.get("/nutrition/1/food-preferences").json()["results"]
    assert len(user_one) == 1
    assert user_one[0]["canonical_food_id"] == food.id
    assert user_one[0]["preference"] == "love"

    neutral = client.put(
        f"/nutrition/1/food-preferences/canonical/{food.id}",
        json={"preference": "neutral"},
    )
    assert neutral.status_code == 200
    assert neutral.json()["food_preference"] == {
        "canonical_food_id": food.id,
        "preference": "neutral",
        "is_hard_exclusion": False,
    }
    assert client.get("/nutrition/1/food-preferences").json()["results"] == []

    conn = database.get_connection()
    stored_count = conn.execute(
        "SELECT COUNT(*) FROM user_canonical_food_preferences"
    ).fetchone()[0]
    conn.close()
    assert stored_count == 0


def test_only_never_suggest_is_a_hard_exclusion(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    foods = [
        create_canonical_food(f"Preference Food {index}", "generic")
        for index in range(4)
    ]
    states = ("love", "like", "dislike", "never_suggest")

    for food, state in zip(foods, states, strict=True):
        response = client.put(
            f"/nutrition/1/food-preferences/canonical/{food.id}",
            json={"preference": state},
        )
        assert response.status_code == 200
        assert response.json()["food_preference"]["is_hard_exclusion"] is (
            state == "never_suggest"
        )

    listed = client.get("/nutrition/1/food-preferences").json()["results"]
    hard_exclusions = [
        item["preference"] for item in listed if item["is_hard_exclusion"]
    ]
    assert hard_exclusions == ["never_suggest"]


def test_preference_listing_preserves_custom_name_and_canonical_identity(
    tmp_path, monkeypatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    food = create_canonical_food("Original Catalog Name", "generic")
    client.put(
        f"/nutrition/1/canonical-food-names/{food.id}",
        json={"display_name": "My Favorite Bowl"},
    )
    client.put(
        f"/nutrition/1/food-preferences/canonical/{food.id}",
        json={"preference": "like"},
    )

    preference = client.get("/nutrition/1/food-preferences").json()["results"][0]
    assert preference["canonical_food_id"] == food.id
    assert preference["display_name"] == "My Favorite Bowl"
    assert preference["custom_display_name"] == "My Favorite Bowl"
    assert preference["original_display_name"] == "Original Catalog Name"


def test_food_preference_validation_and_reset_errors(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    food = create_canonical_food("Valid Preference Food", "generic")

    invalid = client.put(
        f"/nutrition/1/food-preferences/canonical/{food.id}",
        json={"preference": "favorite"},
    )
    missing_food = client.put(
        "/nutrition/1/food-preferences/canonical/999999",
        json={"preference": "love"},
    )
    missing_user = client.get("/nutrition/999/food-preferences")

    assert invalid.status_code == 400
    assert missing_food.status_code == 404
    assert missing_user.status_code == 404

    reset = client.delete(f"/nutrition/1/food-preferences/canonical/{food.id}")
    assert reset.status_code == 200
    assert reset.json()["deleted"] is False
    assert reset.json()["preference"] == "neutral"
