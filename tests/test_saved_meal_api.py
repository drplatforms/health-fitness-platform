from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app
from models.personal_food_models import PersonalFoodRevisionInput
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
)
from services.personal_food_service import archive_personal_food, create_personal_food


@pytest.fixture
def saved_meal_api(tmp_path, monkeypatch):
    db_path = tmp_path / "saved_meal_api.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    ensure_food_normalization_tables()
    canonical = create_canonical_food("API Meal Chicken", "generic")
    for nutrient_name, amount in (
        ("Calories", 200),
        ("Protein", 30),
        ("Carbohydrates", 5),
        ("Fat", 8),
    ):
        create_canonical_food_nutrient(canonical.id, nutrient_name, "g", amount)
    personal = create_personal_food(
        user_id=1,
        revision_input=PersonalFoodRevisionInput(
            display_name="API Personal Sauce",
            input_basis="nutrition_label",
            serving_name="1 tbsp",
            serving_grams=15,
            calories=50,
            protein_g=1,
            carbs_g=4,
            fat_g=3,
        ),
    )
    with TestClient(app) as client:
        yield client, db_path, canonical, personal


def _payload(canonical_id: int, personal_id: int, name: str = "API Bowl"):
    return {
        "display_name": name,
        "default_meal_type": "dinner",
        "items": [
            {
                "food_type": "canonical",
                "canonical_food_id": canonical_id,
                "grams": 100,
            },
            {
                "food_type": "personal",
                "personal_food_id": personal_id,
                "personal_serving_quantity": 2,
            },
        ],
    }


def test_saved_meal_api_full_crud_archive_restore_and_log(saved_meal_api) -> None:
    client, db_path, canonical, personal = saved_meal_api
    create_response = client.post(
        "/nutrition/1/saved-meals",
        json=_payload(canonical.id, personal.id),
    )
    assert create_response.status_code == 200
    meal = create_response.json()["saved_meal"]
    assert meal["item_count"] == 2
    assert meal["current_macros"]["calories"] == 300

    list_response = client.get("/nutrition/1/saved-meals")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["results"]] == [meal["id"]]

    detail_response = client.get(f"/nutrition/1/saved-meals/{meal['id']}")
    assert detail_response.status_code == 200
    update_payload = _payload(canonical.id, personal.id, "Updated API Bowl")
    update_payload["default_meal_type"] = "lunch"
    update_payload["items"].reverse()
    update_payload["items"][0] = {
        "food_type": "personal",
        "personal_food_id": personal.id,
        "grams": 10,
    }
    update_response = client.patch(
        f"/nutrition/1/saved-meals/{meal['id']}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["saved_meal"]["display_name"] == "Updated API Bowl"
    assert update_response.json()["saved_meal"]["items"][0]["food_type"] == "personal"

    archive_response = client.post(f"/nutrition/1/saved-meals/{meal['id']}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["saved_meal"]["active"] is False
    blocked_log = client.post(
        f"/nutrition/1/saved-meals/{meal['id']}/log",
        json={"entry_date": "2026-07-16", "meal_type": "snack"},
    )
    assert blocked_log.status_code == 400

    restore_response = client.post(f"/nutrition/1/saved-meals/{meal['id']}/restore")
    assert restore_response.status_code == 200
    log_response = client.post(
        f"/nutrition/1/saved-meals/{meal['id']}/log",
        json={"entry_date": "2026-07-16"},
    )
    assert log_response.status_code == 200
    assert log_response.json()["logged_item_count"] == 2
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT entry_date, meal_type FROM food_entries ORDER BY id"
    ).fetchall()
    conn.close()
    assert rows == [("2026-07-16", "lunch"), ("2026-07-16", "lunch")]


def test_saved_meal_api_duplicate_missing_and_wrong_user_are_bounded(
    saved_meal_api,
) -> None:
    client, _, canonical, personal = saved_meal_api
    response = client.post(
        "/nutrition/1/saved-meals",
        json=_payload(canonical.id, personal.id, "Protein Bowl"),
    )
    meal_id = response.json()["saved_meal"]["id"]
    duplicate = client.post(
        "/nutrition/1/saved-meals",
        json=_payload(canonical.id, personal.id, " protein   bowl "),
    )
    assert duplicate.status_code == 409
    assert client.get("/nutrition/1/saved-meals/999999").status_code == 404
    assert client.get(f"/nutrition/2/saved-meals/{meal_id}").status_code == 404
    assert (
        client.patch(
            f"/nutrition/2/saved-meals/{meal_id}",
            json=_payload(canonical.id, personal.id, "Stolen"),
        ).status_code
        == 404
    )
    assert client.post(f"/nutrition/2/saved-meals/{meal_id}/archive").status_code == 404
    assert client.post(f"/nutrition/2/saved-meals/{meal_id}/restore").status_code == 404
    assert (
        client.post(
            f"/nutrition/2/saved-meals/{meal_id}/log",
            json={"entry_date": "2026-07-16", "meal_type": "lunch"},
        ).status_code
        == 404
    )


def test_saved_meal_api_rejects_invalid_identity_empty_and_cross_user_personal_food(
    saved_meal_api,
) -> None:
    client, _, canonical, _ = saved_meal_api
    other_personal = create_personal_food(
        user_id=2,
        revision_input=PersonalFoodRevisionInput(
            display_name="Other User Food",
            input_basis="per_100g",
            calories=100,
        ),
    )
    invalid_identity = client.post(
        "/nutrition/1/saved-meals",
        json={
            "display_name": "Bad Identity",
            "items": [
                {
                    "food_type": "canonical",
                    "canonical_food_id": canonical.id,
                    "personal_food_id": other_personal.id,
                    "grams": 10,
                }
            ],
        },
    )
    assert invalid_identity.status_code == 400
    empty = client.post(
        "/nutrition/1/saved-meals",
        json={"display_name": "Empty", "items": []},
    )
    assert empty.status_code == 400
    cross_user = client.post(
        "/nutrition/1/saved-meals",
        json={
            "display_name": "Cross User",
            "items": [
                {
                    "food_type": "personal",
                    "personal_food_id": other_personal.id,
                    "grams": 10,
                }
            ],
        },
    )
    assert cross_user.status_code == 400


def test_saved_meal_api_inactive_component_prevents_logging_without_partial_rows(
    saved_meal_api,
) -> None:
    client, db_path, canonical, personal = saved_meal_api
    response = client.post(
        "/nutrition/1/saved-meals",
        json=_payload(canonical.id, personal.id),
    )
    meal_id = response.json()["saved_meal"]["id"]
    archive_personal_food(user_id=1, personal_food_id=personal.id)
    detail = client.get(f"/nutrition/1/saved-meals/{meal_id}")
    assert detail.json()["saved_meal"]["validation_status"] == "invalid"
    log_response = client.post(
        f"/nutrition/1/saved-meals/{meal_id}/log",
        json={"entry_date": "2026-07-16"},
    )
    assert log_response.status_code == 400
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM food_entries").fetchone()[0] == 0
    conn.close()
