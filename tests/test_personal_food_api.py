from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import database
from api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "personal_food_api.db")
    database.initialize_database()
    return TestClient(app)


def _create_payload(name: str = "My Label Food", calories: float = 120):
    return {
        "display_name": name,
        "brand_name": "Test Brand",
        "input_basis": "nutrition_label",
        "serving_name": "1 package",
        "serving_grams": 40,
        "calories": calories,
        "protein_g": 10,
        "carbs_g": None,
        "fat_g": 2,
        "source_note": "Package label",
    }


def test_personal_food_crud_search_restore_and_log_contract(client) -> None:
    created_response = client.post(
        "/nutrition/1/personal-foods",
        json=_create_payload(),
    )
    assert created_response.status_code == 200
    created = created_response.json()["personal_food"]
    personal_food_id = created["id"]
    assert "legacy_food_id" not in json.dumps(created)

    listed = client.get("/nutrition/1/personal-foods").json()["results"]
    assert [item["id"] for item in listed] == [personal_food_id]
    searched = client.get(
        "/nutrition/1/personal-foods/search",
        params={"q": "label"},
    ).json()["results"]
    assert [item["id"] for item in searched] == [personal_food_id]
    fetched = client.get(f"/nutrition/1/personal-foods/{personal_food_id}").json()[
        "personal_food"
    ]
    assert fetched["display_name"] == "My Label Food"

    revised_response = client.patch(
        f"/nutrition/1/personal-foods/{personal_food_id}",
        json=_create_payload("Renamed Label Food", calories=150),
    )
    assert revised_response.status_code == 200
    revised = revised_response.json()["personal_food"]
    assert revised["current_revision"]["revision_number"] == 2

    logged_response = client.post(
        "/nutrition/1/log-personal",
        json={
            "personal_food_id": personal_food_id,
            "serving_quantity": 2,
            "entry_date": "2026-07-14",
            "meal_type": "dinner",
        },
    )
    assert logged_response.status_code == 200
    logged = logged_response.json()
    assert logged["grams"] == 80
    assert logged["nutrient_summary"]["calories"] == 300
    assert "legacy_food" not in json.dumps(logged)

    archived = client.delete(f"/nutrition/1/personal-foods/{personal_food_id}").json()[
        "personal_food"
    ]
    assert archived["active"] is False
    assert client.get("/nutrition/1/personal-foods").json()["results"] == []
    assert (
        client.post(
            "/nutrition/1/log-personal",
            json={"personal_food_id": personal_food_id, "grams": 10},
        ).status_code
        == 400
    )
    restored = client.post(
        f"/nutrition/1/personal-foods/{personal_food_id}/restore"
    ).json()["personal_food"]
    assert restored["active"] is True
    grams_log = client.post(
        "/nutrition/1/log-personal",
        json={"personal_food_id": personal_food_id, "grams": 10},
    ).json()
    assert "serving_quantity" not in grams_log
    assert "meal_type" not in grams_log


def test_cross_user_personal_food_operations_do_not_disclose_identity(client) -> None:
    created = client.post(
        "/nutrition/1/personal-foods",
        json=_create_payload("Private Food"),
    ).json()["personal_food"]
    personal_food_id = created["id"]
    assert client.get("/nutrition/2/personal-foods").json()["results"] == []
    assert (
        client.get(
            "/nutrition/2/personal-foods/search", params={"q": "private"}
        ).json()["results"]
        == []
    )
    assert (
        client.get(f"/nutrition/2/personal-foods/{personal_food_id}").status_code == 404
    )
    assert (
        client.patch(
            f"/nutrition/2/personal-foods/{personal_food_id}",
            json=_create_payload("Stolen Food"),
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/nutrition/2/personal-foods/{personal_food_id}").status_code
        == 404
    )
    assert (
        client.post(
            "/nutrition/2/log-personal",
            json={"personal_food_id": personal_food_id, "grams": 10},
        ).status_code
        == 404
    )


def test_internal_legacy_food_rows_are_hidden_from_global_search(client) -> None:
    client.post("/nutrition/1/personal-foods", json=_create_payload("Hidden Food"))
    response = client.get(
        "/foods/search",
        params={"query": "Internal Personal Food"},
    )
    assert response.status_code == 200
    assert response.json()["foods"] == []


def test_personal_food_api_returns_public_safe_validation_errors(client) -> None:
    invalid = client.post(
        "/nutrition/1/personal-foods",
        json={
            "display_name": "Invalid",
            "input_basis": "nutrition_label",
            "serving_grams": 0,
            "calories": 100,
        },
    )
    assert invalid.status_code == 400
    assert "serving_grams" in invalid.json()["detail"]
    duplicate_payload = _create_payload("Duplicate Food")
    assert (
        client.post("/nutrition/1/personal-foods", json=duplicate_payload).status_code
        == 200
    )
    duplicate = client.post("/nutrition/1/personal-foods", json=duplicate_payload)
    assert duplicate.status_code == 409


@pytest.mark.parametrize(
    ("field_name", "boolean_value"),
    (
        ("serving_grams", True),
        ("calories", True),
        ("protein_g", False),
        ("carbs_g", True),
        ("fat_g", False),
    ),
)
def test_create_rejects_boolean_numeric_fields_without_partial_rows(
    client,
    field_name,
    boolean_value,
) -> None:
    before = _personal_persistence_counts()
    payload = _create_payload("Boolean Create")
    payload[field_name] = boolean_value
    response = client.post("/nutrition/1/personal-foods", json=payload)
    assert response.status_code == 422
    assert _personal_persistence_counts() == before


@pytest.mark.parametrize(
    ("field_name", "boolean_value"),
    (
        ("serving_grams", True),
        ("calories", True),
        ("protein_g", False),
        ("carbs_g", True),
        ("fat_g", False),
    ),
)
def test_revision_rejects_boolean_numeric_fields_without_partial_rows(
    client,
    field_name,
    boolean_value,
) -> None:
    created = client.post(
        "/nutrition/1/personal-foods",
        json=_create_payload("Boolean Revision"),
    ).json()["personal_food"]
    before = _personal_persistence_counts()
    payload = _create_payload("Boolean Revision")
    payload[field_name] = boolean_value
    response = client.patch(
        f"/nutrition/1/personal-foods/{created['id']}",
        json=payload,
    )
    assert response.status_code == 422
    assert _personal_persistence_counts() == before


@pytest.mark.parametrize(
    "field_name",
    (
        "personal_food_id",
        "grams",
        "serving_quantity",
    ),
)
def test_log_rejects_boolean_numeric_fields_without_food_entry(
    client,
    field_name,
) -> None:
    created = client.post(
        "/nutrition/1/personal-foods",
        json=_create_payload("Boolean Log"),
    ).json()["personal_food"]
    payload = {"personal_food_id": created["id"], "grams": 10}
    if field_name == "serving_quantity":
        payload = {"personal_food_id": created["id"], "serving_quantity": True}
    else:
        payload[field_name] = True
    before = _personal_persistence_counts()
    response = client.post("/nutrition/1/log-personal", json=payload)
    assert response.status_code == 422
    assert _personal_persistence_counts() == before


def test_personal_food_api_accepts_normal_integer_and_float_numeric_inputs(
    client,
) -> None:
    payload = _create_payload("Normal Numeric Input", calories=120.5)
    payload["serving_grams"] = 32.5
    created_response = client.post("/nutrition/1/personal-foods", json=payload)
    assert created_response.status_code == 200
    personal_food_id = created_response.json()["personal_food"]["id"]
    logged_response = client.post(
        "/nutrition/1/log-personal",
        json={"personal_food_id": personal_food_id, "grams": 12.5},
    )
    assert logged_response.status_code == 200
    assert logged_response.json()["grams"] == 12.5


def test_personal_food_api_rejects_resolved_serving_underflow_without_entry(
    client,
) -> None:
    created_response = client.post(
        "/nutrition/1/personal-foods",
        json={
            "display_name": "API Tiny Serving",
            "input_basis": "nutrition_label",
            "serving_name": "tiny serving",
            "serving_grams": 1e-300,
            "calories": 1e-300,
        },
    )
    assert created_response.status_code == 200
    personal_food_id = created_response.json()["personal_food"]["id"]
    before = _personal_persistence_counts()

    response = client.post(
        "/nutrition/1/log-personal",
        json={
            "personal_food_id": personal_food_id,
            "serving_quantity": 1e-300,
        },
    )
    assert response.status_code == 400
    assert "resolved_grams" in response.json()["detail"]
    assert _personal_persistence_counts() == before


@pytest.mark.parametrize("overflow_field", ("calories", "protein_g"))
def test_personal_food_api_rejects_snapshot_overflow_without_entry(
    client,
    overflow_field,
) -> None:
    payload = {
        "display_name": f"API Snapshot Overflow {overflow_field}",
        "input_basis": "per_100g",
        overflow_field: 1e308,
    }
    created = client.post("/nutrition/1/personal-foods", json=payload)
    assert created.status_code == 200
    personal_food_id = created.json()["personal_food"]["id"]
    before = _personal_persistence_counts()
    response = client.post(
        "/nutrition/1/log-personal",
        json={"personal_food_id": personal_food_id, "grams": 5_000},
    )
    assert response.status_code == 400
    assert "finite non-negative" in response.json()["detail"]
    assert _personal_persistence_counts() == before


def test_personal_log_list_update_and_delete_api_contract(client) -> None:
    created = client.post(
        "/nutrition/1/personal-foods",
        json=_create_payload("API Logged Food", calories=120),
    ).json()["personal_food"]
    logged = client.post(
        "/nutrition/1/log-personal",
        json={
            "personal_food_id": created["id"],
            "serving_quantity": 1,
            "entry_date": "2026-07-14",
            "meal_type": "lunch",
        },
    ).json()
    client.patch(
        f"/nutrition/1/personal-foods/{created['id']}",
        json=_create_payload("API Logged Food Revised", calories=300),
    )

    listed_response = client.get(
        "/nutrition/1/personal-logs",
        params={"date": "2026-07-14"},
    )
    assert listed_response.status_code == 200
    listed = listed_response.json()["entries"]
    assert len(listed) == 1
    assert listed[0]["food_type"] == "personal"
    assert listed[0]["personal_food_revision_id"] == logged["personal_food_revision_id"]
    assert listed[0]["food_name"] == "API Logged Food"
    assert listed[0]["carbs_g"] is None
    assert "legacy_food_id" not in json.dumps(listed[0])

    updated_response = client.patch(
        f"/nutrition/1/personal-logs/{logged['logged_food_entry_id']}",
        json={
            "serving_quantity": 2,
            "meal_type": "dinner",
            "entry_date": "2026-07-14",
        },
    )
    assert updated_response.status_code == 200
    updated = updated_response.json()["entry"]
    assert updated["grams"] == 80
    assert updated["calories"] == 240
    assert updated["meal_type"] == "dinner"
    assert updated["food_name"] == "API Logged Food"

    deleted_response = client.delete(
        f"/nutrition/1/personal-logs/{logged['logged_food_entry_id']}",
        params={"date": "2026-07-14"},
    )
    assert deleted_response.status_code == 200
    assert deleted_response.json()["deleted"] is True
    assert (
        client.get(
            "/nutrition/1/personal-logs",
            params={"date": "2026-07-14"},
        ).json()["entries"]
        == []
    )


def test_personal_log_api_does_not_disclose_cross_user_or_wrong_date(client) -> None:
    created = client.post(
        "/nutrition/1/personal-foods",
        json=_create_payload("API Private Log"),
    ).json()["personal_food"]
    logged = client.post(
        "/nutrition/1/log-personal",
        json={
            "personal_food_id": created["id"],
            "grams": 20,
            "entry_date": "2026-07-14",
        },
    ).json()
    entry_id = logged["logged_food_entry_id"]

    assert (
        client.get(
            "/nutrition/2/personal-logs",
            params={"date": "2026-07-14"},
        ).json()["entries"]
        == []
    )
    assert (
        client.patch(
            f"/nutrition/2/personal-logs/{entry_id}",
            json={"grams": 30},
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/nutrition/1/personal-logs/{entry_id}",
            params={"date": "2026-07-15"},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            "/nutrition/1/personal-logs/999999",
            json={"grams": 30},
        ).status_code
        == 404
    )


@pytest.mark.parametrize("field_name", ("grams", "serving_quantity"))
def test_personal_log_update_api_rejects_boolean_amounts_without_mutation(
    client,
    field_name,
) -> None:
    created = client.post(
        "/nutrition/1/personal-foods",
        json=_create_payload("API Boolean Log Update"),
    ).json()["personal_food"]
    logged = client.post(
        "/nutrition/1/log-personal",
        json={"personal_food_id": created["id"], "grams": 20},
    ).json()
    before = _personal_persistence_counts()

    response = client.patch(
        f"/nutrition/1/personal-logs/{logged['logged_food_entry_id']}",
        json={field_name: True},
    )

    assert response.status_code == 422
    assert _personal_persistence_counts() == before


def _personal_persistence_counts() -> dict[str, int]:
    conn = database.get_connection()
    try:
        return {
            "personal_foods": conn.execute(
                "SELECT COUNT(*) FROM personal_foods"
            ).fetchone()[0],
            "personal_food_revisions": conn.execute(
                "SELECT COUNT(*) FROM personal_food_revisions"
            ).fetchone()[0],
            "internal_foods": conn.execute(
                "SELECT COUNT(*) FROM foods WHERE name LIKE 'Internal Personal Food:%'"
            ).fetchone()[0],
            "food_nutrients": conn.execute(
                "SELECT COUNT(*) FROM food_nutrients"
            ).fetchone()[0],
            "food_entries": conn.execute(
                "SELECT COUNT(*) FROM food_entries"
            ).fetchone()[0],
        }
    finally:
        conn.close()
