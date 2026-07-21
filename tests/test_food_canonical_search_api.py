from __future__ import annotations

from fastapi.testclient import TestClient

import database
from api.main import app
from services.food_canonical_promotion_service import (
    promote_raw_source_record_to_canonical,
)
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    create_raw_food_source_record,
    ensure_food_normalization_tables,
    link_canonical_food_to_source,
)
from services.nutrition_service import add_food_entry, get_daily_nutrition


def _seed_test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()
    ensure_food_normalization_tables()


def _client() -> TestClient:
    return TestClient(app)


def test_search_endpoint_returns_seeded_canonical_chicken_match(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/foods/canonical/search?q=chicken breast")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["query"] == "chicken breast"
    assert payload["results"][0]["display_name"] == "Chicken breast"
    assert payload["results"][0]["matched_on"] in {"display_name", "alias"}
    assert payload["results"][0]["nutrient_summary"] == {
        "calories_per_100g": 165.0,
        "protein_g_per_100g": 31.0,
        "carbohydrate_g_per_100g": 0.0,
        "fat_g_per_100g": 3.6,
    }
    assert "raw_description" not in payload["results"][0]
    assert "source_payload_json" not in payload["results"][0]


def test_search_endpoint_returns_common_seeded_foods(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    expected_by_query = {
        "rice": "White Rice, Cooked",
        "egg": "Egg",
        "oats": "Oats, Dry",
        "tuna": "Tuna",
        "pasta": "Pasta, Cooked",
        "beans": "Black Beans, Cooked",
        "protein powder": "Whey Protein Powder, Generic",
        "peanut butter": "Peanut Butter",
        "ground turkey": "Turkey, Ground 93/7",
        "tortilla": "Tortilla, Flour",
        "greek yogurt": "Greek Yogurt, Plain",
        "egg whites": "Egg Whites",
        "ranch": "Ranch Dressing",
        "hummus": "Hummus",
    }

    for query, expected_name in expected_by_query.items():
        response = _client().get(f"/foods/canonical/search?q={query}")

        assert response.status_code == 200
        results = response.json()["results"]
        assert results
        assert results[0]["display_name"] == expected_name
        assert "nutrient_summary" in results[0]


def test_steak_search_preserves_tuna_steak_identity(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/foods/canonical/search?q=steak")

    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["display_name"] == "Sirloin Steak, Cooked"
    assert any(result["display_name"] == "Tuna steak" for result in results)
    assert all(result["display_name"] != "Tuna" for result in results)


def test_search_endpoint_returns_alias_match(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    create_canonical_food_alias(food.id, "boneless chicken", priority=5)

    response = _client().get("/foods/canonical/search?q=boneless chicken")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["display_name"] == "Chicken breast"
    assert result["matched_on"] == "alias"
    assert "boneless chicken" in result["aliases"]


def test_promoted_canonical_food_can_be_found_by_name_with_compact_source_summary(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    raw_record = create_raw_food_source_record(
        source_name="USDA FoodData Central",
        source_record_id="321358",
        raw_description="Hummus, commercial",
        data_type="foundation_food",
        calories_per_100g=229.0,
        protein_g_per_100g=7.35,
        carbs_g_per_100g=14.9,
        fat_g_per_100g=17.1,
        source_payload={"fdc_id": 321358},
    )
    promote_raw_source_record_to_canonical(
        raw_record.id,
        canonical_name="Hummus, commercial",
        aliases=["hummus"],
    )

    response = _client().get("/foods/canonical/search?q=hummus commercial")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["display_name"] == "Hummus"
    assert result["matched_on"] == "alias"
    assert result["source"] == {
        "source_name": "USDA FoodData Central",
        "source_record_id": "321358",
    }
    assert "source_payload_json" not in result
    assert "raw_description" not in result


def test_promoted_canonical_food_can_be_found_by_alias(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    raw_record = create_raw_food_source_record(
        source_name="USDA FoodData Central",
        source_record_id="321358",
        raw_description="Hummus, commercial",
        data_type="foundation_food",
        calories_per_100g=229.0,
        protein_g_per_100g=7.35,
        carbs_g_per_100g=14.9,
        fat_g_per_100g=17.1,
    )
    promote_raw_source_record_to_canonical(
        raw_record.id,
        canonical_name="Hummus, commercial",
        aliases=["commercial hummus"],
    )

    response = _client().get("/foods/canonical/search?q=commercial hummus")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["display_name"] == "Hummus"
    assert result["matched_on"] == "alias"
    assert "commercial hummus" in result["aliases"]


def test_higher_priority_canonical_food_ranks_first(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Chicken Breast, Raw, Skinless", "raw", search_priority=30)
    create_canonical_food(
        "Chicken Breast, Cooked, Skinless", "cooked", search_priority=10
    )

    response = _client().get("/foods/canonical/search?q=chicken breast")

    assert response.status_code == 200
    results = response.json()["results"]
    result_ids = [result["canonical_food_id"] for result in results]
    cooked_id = next(
        result["canonical_food_id"]
        for result in results
        if result["display_name"] == "Chicken breast"
        and result["food_type"] == "cooked"
    )
    raw_id = next(
        result["canonical_food_id"]
        for result in results
        if result["display_name"] == "Chicken breast, raw"
        and result["food_type"] == "raw"
    )
    assert result_ids.index(cooked_id) < result_ids.index(raw_id)


def test_raw_meat_is_deprioritized_for_default_search(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    raw_food = create_canonical_food(
        "Chicken Breast, Raw, Skinless",
        "raw",
        search_priority=1,
    )
    create_canonical_food_alias(raw_food.id, "raw chicken breast", priority=5)
    create_canonical_food(
        "Chicken Breast, Cooked, Skinless",
        "cooked",
        search_priority=100,
    )

    response = _client().get("/foods/canonical/search?q=chicken breast")

    assert response.status_code == 200
    results = response.json()["results"]
    result_ids = [result["canonical_food_id"] for result in results]
    cooked_id = next(
        result["canonical_food_id"]
        for result in results
        if result["display_name"] == "Chicken breast"
        and result["food_type"] == "cooked"
    )
    assert result_ids.index(cooked_id) < result_ids.index(raw_food.id)
    assert (
        next(
            result for result in results if result["canonical_food_id"] == raw_food.id
        )["display_name"]
        == "Chicken breast, raw"
    )


def test_explicit_raw_query_can_find_raw_meat(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    raw_food = create_canonical_food(
        "Chicken Breast, Raw, Skinless",
        "raw",
        search_priority=1,
    )
    create_canonical_food_alias(raw_food.id, "raw chicken breast", priority=5)
    create_canonical_food(
        "Chicken Breast, Cooked, Skinless",
        "cooked",
        search_priority=10,
    )

    response = _client().get("/foods/canonical/search?q=raw chicken breast")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["display_name"] == "Chicken breast, raw"
    assert result["canonical_food_id"] == raw_food.id


def test_raw_non_meat_food_is_not_deprioritized(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    raw_tomato = create_canonical_food(
        "Tomatoes, grape, raw",
        "raw",
        search_priority=1,
    )
    create_canonical_food(
        "Tomato Sauce",
        "prepared",
        search_priority=10,
    )

    response = _client().get("/foods/canonical/search?q=tomato")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["display_name"] == "Grape tomatoes"
    assert result["canonical_food_id"] == raw_tomato.id


def test_practical_oatmeal_alias_prefers_cooked_oatmeal(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    response = _client().get("/foods/canonical/search?q=oatmeal")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["display_name"] == "Oatmeal"
    assert result["food_type"] == "cooked"


def test_search_results_are_bounded_by_limit(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    for index in range(5):
        create_canonical_food(f"Test Food {index}", "generic", search_priority=index)

    response = _client().get("/foods/canonical/search?q=test&limit=2")

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_search_limit_is_capped_to_public_safe_maximum(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    for index in range(30):
        create_canonical_food(f"Search Food {index}", "generic", search_priority=index)

    response = _client().get("/foods/canonical/search?q=search&limit=100")

    assert response.status_code == 200
    assert len(response.json()["results"]) == 25


def test_inactive_foods_are_hidden_by_default(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Active Rice", "cooked", active=True, search_priority=10)
    create_canonical_food("Inactive Rice", "cooked", active=False, search_priority=1)

    response = _client().get("/foods/canonical/search?q=rice")

    assert response.status_code == 200
    names = [result["display_name"] for result in response.json()["results"]]
    assert "Active Rice" in names
    assert "Inactive Rice" not in names


def test_inactive_foods_can_be_requested_explicitly(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Inactive Rice", "cooked", active=False, search_priority=1)

    response = _client().get("/foods/canonical/search?q=rice&include_inactive=true")

    assert response.status_code == 200
    names = [result["display_name"] for result in response.json()["results"]]
    assert "Inactive Rice" in names


def test_raw_source_payloads_are_not_exposed(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    raw_record = create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="12345",
        raw_description="Chicken, source variant with verbose USDA description",
        source_payload={"private_raw_payload": True},
    )
    link_canonical_food_to_source(food.id, raw_record.id)

    response = _client().get(
        "/foods/canonical/search?q=chicken&include_source_links=true"
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert "source_payload_json" not in result
    assert "source_links" in result
    assert "source_payload_json" not in result["source_links"][0]
    assert result["source_links"][0]["source_name"] == "USDA FDC"


def test_raw_source_records_do_not_appear_as_default_user_facing_results(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    create_raw_food_source_record(
        source_name="USDA FDC",
        source_record_id="raw-1",
        raw_description="Chicken, breast, duplicate-looking raw source record",
    )
    create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")

    response = _client().get("/foods/canonical/search?q=chicken")

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert results[0]["display_name"] == "Chicken breast"
    assert all("raw_source_record_id" not in result for result in results)
    assert all("source_payload_json" not in result for result in results)


def test_nutrient_summary_is_included_only_when_nutrients_exist(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    plain_food = create_canonical_food("Plain Test Food", "generic")
    chicken = create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")
    create_canonical_food_nutrient(chicken.id, "Calories", "kcal", 165)
    create_canonical_food_nutrient(chicken.id, "Protein", "g", 31)
    create_canonical_food_nutrient(chicken.id, "Carbohydrate", "g", 0)
    create_canonical_food_nutrient(chicken.id, "Fat", "g", 3.6)

    chicken_response = _client().get("/foods/canonical/search?q=chicken")
    plain_response = _client().get("/foods/canonical/search?q=plain test")

    assert chicken_response.status_code == 200
    assert chicken_response.json()["results"][0]["nutrient_summary"] == {
        "calories_per_100g": 165.0,
        "protein_g_per_100g": 31.0,
        "carbohydrate_g_per_100g": 0.0,
        "fat_g_per_100g": 3.6,
    }
    assert plain_response.status_code == 200
    assert plain_response.json()["results"][0]["canonical_food_id"] == plain_food.id
    assert "nutrient_summary" not in plain_response.json()["results"][0]


def test_partial_missing_macro_values_are_not_forced_to_zero(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Partial Macro Food", "generic")
    create_canonical_food_nutrient(food.id, "Calories", "kcal", 27)
    create_canonical_food_nutrient(food.id, "Carbohydrate", "g", 5.51)

    response = _client().get("/foods/canonical/search?q=partial macro")

    assert response.status_code == 200
    assert response.json()["results"][0]["nutrient_summary"] == {
        "calories_per_100g": 27.0,
        "carbohydrate_g_per_100g": 5.51,
    }


def test_explicit_zero_macro_values_remain_zero(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    food = create_canonical_food("Zero Macro Food", "generic")
    create_canonical_food_nutrient(food.id, "Calories", "kcal", 0)
    create_canonical_food_nutrient(food.id, "Protein", "g", 0)
    create_canonical_food_nutrient(food.id, "Carbohydrate", "g", 0)
    create_canonical_food_nutrient(food.id, "Fat", "g", 0)

    response = _client().get("/foods/canonical/search?q=zero macro")

    assert response.status_code == 200
    assert response.json()["results"][0]["nutrient_summary"] == {
        "calories_per_100g": 0.0,
        "protein_g_per_100g": 0.0,
        "carbohydrate_g_per_100g": 0.0,
        "fat_g_per_100g": 0.0,
    }


def test_empty_or_short_query_is_safe_and_deterministic(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    empty_response = _client().get("/foods/canonical/search?q=")
    short_response = _client().get("/foods/canonical/search?q=a")

    assert empty_response.status_code == 200
    assert empty_response.json() == {"success": True, "query": "", "results": []}
    assert short_response.status_code == 400
    assert short_response.json()["detail"] == (
        "q must be at least 2 characters for canonical food search."
    )


def test_nonexistent_query_returns_success_with_empty_results(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)
    create_canonical_food("Chicken Breast, Cooked, Skinless", "cooked")

    response = _client().get("/foods/canonical/search?q=dragonfruit")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["results"] == []


def test_existing_nutrition_logging_remains_stable(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES ('Legacy Rice')")
    cursor.execute("SELECT id FROM foods WHERE name = 'Legacy Rice'")
    food_id = cursor.fetchone()["id"]
    cursor.execute("SELECT id FROM nutrients WHERE name = 'Carbohydrates'")
    carbohydrate_id = cursor.fetchone()["id"]
    cursor.execute(
        """
        INSERT INTO food_nutrients (food_id, nutrient_id, amount_per_100g)
        VALUES (?, ?, ?)
        """,
        (food_id, carbohydrate_id, 28.0),
    )
    conn.commit()
    conn.close()

    add_food_entry(user_id=1, food_id=food_id, grams=150)
    nutrition = get_daily_nutrition(user_id=1, entry_date="2026-06-05")

    if not nutrition:
        from datetime import datetime

        nutrition = get_daily_nutrition(
            user_id=1,
            entry_date=datetime.now().strftime("%Y-%m-%d"),
        )

    assert nutrition["Carbohydrates"]["amount"] == 42.0
    assert nutrition["Carbohydrates"]["unit"] == "g"
