from __future__ import annotations

from collections import Counter

import database
from services.food_normalization_service import (
    MEAL_GENERATION_READINESS_V1_FOODS,
    STARTER_CANONICAL_FOODS,
    create_canonical_food,
    get_nutrients_for_canonical_food,
    normalize_food_name,
    search_canonical_foods,
    seed_starter_canonical_foods,
)

EXPECTED_COVERAGE = {
    "proteins": {
        "Ground Lamb, Cooked",
        "Rainbow Trout, Cooked",
    },
    "grains_and_starches": {
        "All-Purpose Flour",
        "Whole Wheat Flour",
        "Yellow Cornmeal",
        "Cornstarch",
    },
    "beans_and_legumes": {
        "Great Northern Beans, Cooked",
        "Lima Beans, Cooked",
    },
    "vegetables_and_aromatics": {
        "Garlic",
        "Ginger Root, Raw",
        "Scallions, Raw",
        "Leeks",
    },
    "fruits": {
        "Lemon, Raw",
        "Lime, Raw",
        "Coconut Meat, Raw",
    },
    "dairy": {
        "Yogurt, Plain Whole Milk",
        "Heavy Cream",
        "Sour Cream",
        "Swiss Cheese",
    },
    "fats_nuts_and_seeds": {
        "Mixed Nuts, Dry Roasted, Unsalted",
        "Sesame Seeds",
    },
    "breads_and_wraps": {
        "Rye Bread",
        "Hamburger Bun",
        "Whole Wheat Tortilla",
    },
    "sauces_and_condiments": {
        "Balsamic Vinegar",
        "Apple Cider Vinegar",
        "Worcestershire Sauce",
        "Pesto Sauce",
    },
    "breakfast": {
        "Pancakes, Plain",
        "Waffles, Plain",
        "Hash Brown Potatoes",
        "Pork Breakfast Sausage, Cooked",
    },
    "snacks_desserts_and_baking": {
        "Fruit Jam",
        "Granulated Sugar",
        "Brown Sugar",
        "Cocoa Powder, Unsweetened",
        "Dark Chocolate, 70-85% Cacao",
        "Vanilla Ice Cream",
        "Graham Crackers",
        "Baking Powder",
        "Baking Soda",
        "Vanilla Extract",
    },
}


def _seed_test_db(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fitness_ai_test.db")
    database.initialize_database()


def test_meal_generation_readiness_v1_is_targeted_and_covers_each_focus_area():
    expected_names = set().union(*EXPECTED_COVERAGE.values())
    actual_names = {food["display_name"] for food in MEAL_GENERATION_READINESS_V1_FOODS}

    assert len(EXPECTED_COVERAGE) == 11
    assert len(MEAL_GENERATION_READINESS_V1_FOODS) == 42
    assert actual_names == expected_names


def test_meal_generation_readiness_v1_has_no_name_or_alias_collisions():
    milestone_names = {
        normalize_food_name(food["display_name"])
        for food in MEAL_GENERATION_READINESS_V1_FOODS
    }
    base_names = {
        normalize_food_name(food["display_name"])
        for food in STARTER_CANONICAL_FOODS
        if food not in MEAL_GENERATION_READINESS_V1_FOODS
    }
    milestone_aliases = [
        normalize_food_name(alias)
        for food in MEAL_GENERATION_READINESS_V1_FOODS
        for alias in food["aliases"]
    ]

    assert len(milestone_names) == len(MEAL_GENERATION_READINESS_V1_FOODS)
    assert milestone_names.isdisjoint(base_names)
    assert not milestone_names.intersection(milestone_aliases)
    assert all(count == 1 for count in Counter(milestone_aliases).values())
    assert base_names.isdisjoint(milestone_aliases)


def test_meal_generation_readiness_v1_is_searchable_and_source_grounded(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    seed_starter_canonical_foods()

    for definition in MEAL_GENERATION_READINESS_V1_FOODS:
        expected_name = definition["display_name"]
        results = search_canonical_foods(expected_name)
        assert results, expected_name
        assert results[0].canonical_food.display_name == expected_name
        assert "USDA FoodData Central SR Legacy fdc_id" in (
            results[0].canonical_food.notes or ""
        )

        nutrients = get_nutrients_for_canonical_food(results[0].canonical_food.id)
        nutrient_names = {nutrient.nutrient_name for nutrient in nutrients}
        assert nutrient_names >= {"Calories", "Protein", "Carbohydrate", "Fat"}
        assert {nutrient.source_policy for nutrient in nutrients} == {"direct_source"}
        assert {nutrient.confidence for nutrient in nutrients} == {"Moderate"}


def test_meal_generation_readiness_v1_seed_is_idempotent(tmp_path, monkeypatch):
    _seed_test_db(tmp_path, monkeypatch)

    first_seed = seed_starter_canonical_foods()
    second_seed = seed_starter_canonical_foods()

    assert len(first_seed) == len(STARTER_CANONICAL_FOODS)
    assert len(second_seed) == len(STARTER_CANONICAL_FOODS)
    assert {food.id for food in first_seed} == {food.id for food in second_seed}


def test_seed_updates_existing_same_name_generic_foods_in_place(
    tmp_path,
    monkeypatch,
):
    _seed_test_db(tmp_path, monkeypatch)
    existing_names = (
        "Whole Wheat Flour",
        "Garlic",
        "Leeks",
        "Heavy Cream",
        "Sour Cream",
    )
    existing_ids = {
        name: create_canonical_food(
            display_name=name,
            food_type="generic",
            default_unit="grams",
            default_grams=100.0,
            notes="Existing generic row.",
        ).id
        for name in existing_names
    }

    seed_starter_canonical_foods()

    conn = database.get_connection()
    for name, existing_id in existing_ids.items():
        rows = conn.execute(
            """
            SELECT id, notes
            FROM canonical_foods
            WHERE normalized_name = ? AND food_type = 'generic'
            """,
            (normalize_food_name(name),),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["id"] == existing_id
        assert "USDA FoodData Central SR Legacy fdc_id" in rows[0]["notes"]
    conn.close()
