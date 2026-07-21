from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
)
from services.nutrition_service import add_canonical_food_entry


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "food_names.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    return TestClient(app)


def test_custom_food_name_is_user_scoped_searchable_and_resettable(
    tmp_path, monkeypatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    food = create_canonical_food(
        "Imported Product Description, Prepared According to Package",
        "branded",
        default_grams=100,
    )
    create_canonical_food_nutrient(food.id, "Calories", "kcal", 210)
    add_canonical_food_entry(
        user_id=1,
        canonical_food_id=food.id,
        grams=100,
        entry_date="2026-07-21",
    )
    client.put(f"/nutrition/1/available-ingredients/canonical/{food.id}")

    renamed = client.put(
        f"/nutrition/1/canonical-food-names/{food.id}",
        json={"display_name": "My Weekday Lunch"},
    )

    assert renamed.status_code == 200
    assert renamed.json()["food_name"] == {
        "canonical_food_id": food.id,
        "display_name": "My Weekday Lunch",
        "custom_display_name": "My Weekday Lunch",
        "original_display_name": (
            "Imported Product Description, Prepared According to Package"
        ),
    }

    custom_search = client.get(
        "/foods/canonical/search",
        params={"q": "weekday lunch", "user_id": 1},
    ).json()["results"]
    assert custom_search[0]["canonical_food_id"] == food.id
    assert custom_search[0]["display_name"] == "My Weekday Lunch"
    assert custom_search[0]["matched_on"] == "custom_display_name"

    original_search = client.get(
        "/foods/canonical/search",
        params={"q": "imported product", "user_id": 1},
    ).json()["results"]
    assert original_search[0]["display_name"] == "My Weekday Lunch"
    assert original_search[0]["original_display_name"].startswith("Imported Product")

    other_user_search = client.get(
        "/foods/canonical/search",
        params={"q": "weekday lunch", "user_id": 2},
    ).json()["results"]
    assert other_user_search == []

    newly_logged = client.post(
        "/nutrition/1/log-canonical",
        json={
            "canonical_food_id": food.id,
            "grams": 50,
            "entry_date": "2026-07-21",
        },
    )
    assert newly_logged.status_code == 200
    assert newly_logged.json()["display_name"] == "My Weekday Lunch"

    recent = client.get("/nutrition/1/recent-canonical-foods").json()["results"][0]
    client.put(f"/nutrition/1/pinned-foods/canonical/{food.id}")
    pinned = client.get("/nutrition/1/pinned-foods").json()["results"][0]
    available = client.get("/nutrition/1/available-ingredients").json()["results"][0]
    logged = client.get(
        "/nutrition/1/canonical-logs", params={"date": "2026-07-21"}
    ).json()["entries"][0]
    assert recent["display_name"] == "My Weekday Lunch"
    assert pinned["display_name"] == "My Weekday Lunch"
    assert available["display_name"] == "My Weekday Lunch"
    assert logged["food_name"] == "My Weekday Lunch"

    conn = database.get_connection()
    canonical_row = conn.execute(
        "SELECT display_name FROM canonical_foods WHERE id = ?", (food.id,)
    ).fetchone()
    conn.close()
    assert canonical_row["display_name"] == food.display_name

    reset = client.delete(f"/nutrition/1/canonical-food-names/{food.id}")
    assert reset.status_code == 200
    assert reset.json()["deleted"] is True
    restored = client.get(
        "/foods/canonical/search",
        params={"q": "imported product", "user_id": 1},
    ).json()["results"][0]
    assert restored["display_name"] == food.display_name
    assert restored["custom_display_name"] is None


def test_custom_food_name_validation_does_not_mutate_canonical_food(
    tmp_path, monkeypatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    food = create_canonical_food("Original Source Name", "generic")

    blank = client.put(
        f"/nutrition/1/canonical-food-names/{food.id}",
        json={"display_name": "   "},
    )
    too_long = client.put(
        f"/nutrition/1/canonical-food-names/{food.id}",
        json={"display_name": "x" * 121},
    )

    assert blank.status_code == 400
    assert too_long.status_code == 400
    conn = database.get_connection()
    row = conn.execute(
        "SELECT display_name FROM canonical_foods WHERE id = ?", (food.id,)
    ).fetchone()
    conn.close()
    assert row["display_name"] == "Original Source Name"
