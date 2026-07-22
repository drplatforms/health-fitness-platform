from __future__ import annotations

import json
import sqlite3

import pytest

import database
from models.ai_run_models import AIProviderTextResult
from models.meal_instruction_models import (
    GroundedRecipeIngredient,
    MealInstructionGenerationRequest,
)
from models.saved_meal_models import SavedMealItemInput, SavedMealMutationInput
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
)
from services.meal_instruction_service import (
    MealInstructionProviderError,
    generate_and_save_cooking_instructions,
    generate_cooking_instructions,
)
from services.nutrition_serving_unit_service import create_or_update_serving_unit
from services.saved_meal_service import (
    create_saved_meal,
    get_saved_meal,
    scale_saved_meal_recipe,
    update_saved_meal,
)


@pytest.fixture
def recipe_db(tmp_path, monkeypatch):
    db_path = tmp_path / "recipe_lifecycle.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.initialize_database()
    ensure_food_normalization_tables()
    return db_path


def _food(name: str, calories: float):
    food = create_canonical_food(name, "generic")
    for nutrient_name, amount in (
        ("Calories", calories),
        ("Protein", 20),
        ("Carbohydrates", 10),
        ("Fat", 5),
    ):
        create_canonical_food_nutrient(food.id, nutrient_name, "g", amount)
    return food


def test_schema_extension_is_additive_and_existing_meals_default_to_manual(
    recipe_db,
) -> None:
    database.initialize_database()
    conn = sqlite3.connect(recipe_db)
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(saved_meals)").fetchall()
    }
    conn.close()

    assert {
        "cooking_instructions_json",
        "instruction_telemetry_json",
        "source_type",
        "source_provider",
        "source_model",
    }.issubset(columns)
    food = _food("Legacy Recipe Food", 100)
    meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Existing Meal",
            items=(
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=food.id,
                    grams=100,
                ),
            ),
        ),
    )
    assert meal.source_type == "manual"
    assert meal.source_provider is None
    assert meal.source_model is None
    assert meal.cooking_instructions == ()


def test_pre_recipe_saved_meal_table_is_migrated_in_place(
    tmp_path, monkeypatch
) -> None:
    db_path = tmp_path / "legacy_saved_meals.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE saved_meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            default_meal_type TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, normalized_name)
        )
        """
    )
    conn.execute(
        """
        INSERT INTO saved_meals (user_id, display_name, normalized_name)
        VALUES (1, 'Legacy Recipe', 'legacy recipe')
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(database, "DB_PATH", db_path)

    database.initialize_database()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT source_type, source_provider, source_model, "
        "cooking_instructions_json, instruction_telemetry_json "
        "FROM saved_meals WHERE id = 1"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["source_type"] == "manual"
    assert row["source_provider"] is None
    assert row["source_model"] is None
    assert row["cooking_instructions_json"] is None
    assert row["instruction_telemetry_json"] is None


def test_ai_and_manual_creation_share_saved_meal_representation_and_exact_facts(
    recipe_db,
) -> None:
    food = _food("Grounded AI Chicken", 200)
    ai_meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Grounded AI Bowl",
            default_meal_type="dinner",
            items=(
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=food.id,
                    grams=137.25,
                ),
            ),
            cooking_instructions=("Cook the exact tracked chicken.",),
            source_type="ai",
            source_provider="openai",
            source_model="gpt-5.6-luna",
        ),
    )
    manual_meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Manual Bowl",
            items=(
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=food.id,
                    grams=90,
                ),
            ),
        ),
    )

    assert type(ai_meal) is type(manual_meal)
    assert ai_meal.items[0].canonical_food_id == food.id
    assert ai_meal.items[0].resolved_grams == 137.25
    assert ai_meal.source_type == "ai"
    assert ai_meal.cooking_instructions == ("Cook the exact tracked chicken.",)

    preserved = update_saved_meal(
        user_id=1,
        saved_meal_id=ai_meal.id,
        mutation=SavedMealMutationInput(
            display_name="Grounded AI Bowl Updated",
            default_meal_type="dinner",
            items=(
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=food.id,
                    grams=137.25,
                ),
            ),
        ),
    )
    assert preserved.source_type == "ai"
    assert preserved.source_provider == "openai"
    assert preserved.cooking_instructions == ai_meal.cooking_instructions


def test_instruction_generation_uses_exact_grounded_facts_without_mutating_them(
    recipe_db,
) -> None:
    chicken = _food("Instruction Chicken", 200)
    rice = _food("Instruction Rice", 130)
    ingredients = (
        GroundedRecipeIngredient(chicken.id, None, chicken.display_name, 125.5),
        GroundedRecipeIngredient(rice.id, None, rice.display_name, 88.25),
    )
    captured: dict[str, object] = {}

    def generate(model, prompt, timeout, schema):
        captured.update(model=model, prompt=prompt, timeout=timeout, schema=schema)
        return AIProviderTextResult(
            text=json.dumps(
                {
                    "instructions": [
                        "Cook the 125.5 g chicken.",
                        "Combine with the 88.25 g rice.",
                    ]
                }
            ),
            model="qwen3:8b",
            input_tokens=100,
            output_tokens=30,
        )

    result = generate_cooking_instructions(
        user_id=1,
        request=MealInstructionGenerationRequest(
            provider="local",
            model="qwen3:8b",
            meal_name="Exact Bowl",
            ingredients=ingredients,
        ),
        local_generate=generate,
    )

    prompt_facts = json.loads(str(captured["prompt"]).split("RECIPE_FACTS:\n", 1)[1])
    assert prompt_facts["grounded_ingredients"] == [
        {
            "amount_grams": 125.5,
            "canonical_food_id": chicken.id,
            "display_quantity": "4.5 oz (125.5 g)",
            "display_name": chicken.display_name,
            "personal_food_id": None,
        },
        {
            "amount_grams": 88.25,
            "canonical_food_id": rice.id,
            "display_quantity": "88.25 g",
            "display_name": rice.display_name,
            "personal_food_id": None,
        },
    ]
    assert ingredients[0].amount_grams == 125.5
    assert result.instructions == (
        "Cook the 125.5 g chicken.",
        "Combine with the 88.25 g rice.",
    )
    assert result.telemetry.input_tokens == 100
    assert result.telemetry.estimated_api_cost_usd == 0.0


def test_saved_instruction_generation_persists_and_replaces_matching_telemetry(
    recipe_db,
) -> None:
    food = _food("Persisted Instruction Food", 160)
    meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Persisted Recipe",
            items=(
                SavedMealItemInput(
                    food_type="canonical", canonical_food_id=food.id, grams=222.2
                ),
            ),
        ),
    )
    result, saved = generate_and_save_cooking_instructions(
        user_id=1,
        saved_meal_id=meal.id,
        provider="local",
        model="qwen3:8b",
        local_generate=lambda *_: AIProviderTextResult(
            text=json.dumps({"instructions": ["Cook the exact persisted ingredient."]}),
            model="qwen3:8b",
            input_tokens=80,
            output_tokens=24,
        ),
    )

    assert result.instructions == ("Cook the exact persisted ingredient.",)
    assert saved.cooking_instructions == result.instructions
    assert saved.instruction_telemetry == result.telemetry
    assert saved.items[0].canonical_food_id == food.id
    assert saved.items[0].resolved_grams == 222.2
    assert get_saved_meal(user_id=1, saved_meal_id=meal.id) == saved

    regenerated_result, regenerated = generate_and_save_cooking_instructions(
        user_id=1,
        saved_meal_id=meal.id,
        provider="local",
        model="qwen3:8b",
        local_generate=lambda *_: AIProviderTextResult(
            text=json.dumps(
                {"instructions": ["Bake the exact persisted ingredient until cooked."]}
            ),
            model="qwen3:8b",
            input_tokens=95,
            output_tokens=31,
        ),
    )

    assert regenerated.cooking_instructions == regenerated_result.instructions
    assert regenerated.instruction_telemetry == regenerated_result.telemetry
    assert regenerated.instruction_telemetry != saved.instruction_telemetry
    assert get_saved_meal(user_id=1, saved_meal_id=meal.id) == regenerated

    preserved = update_saved_meal(
        user_id=1,
        saved_meal_id=meal.id,
        mutation=SavedMealMutationInput(
            display_name=regenerated.display_name,
            cooking_instructions=regenerated.cooking_instructions,
            items=(
                SavedMealItemInput(
                    food_type="canonical", canonical_food_id=food.id, grams=222.2
                ),
            ),
        ),
    )
    assert preserved.instruction_telemetry == regenerated.instruction_telemetry

    manually_edited = update_saved_meal(
        user_id=1,
        saved_meal_id=meal.id,
        mutation=SavedMealMutationInput(
            display_name=regenerated.display_name,
            cooking_instructions=("Cook manually using the grounded ingredient.",),
            items=(
                SavedMealItemInput(
                    food_type="canonical", canonical_food_id=food.id, grams=222.2
                ),
            ),
        ),
    )
    assert manually_edited.instruction_telemetry is None


@pytest.mark.parametrize(
    "unsafe_step",
    (
        "Drizzle with olive oil before serving.",
        "Cook 200 g of the ingredient until done.",
    ),
)
def test_instruction_generation_rejects_untracked_additions_and_quantity_changes(
    recipe_db,
    unsafe_step,
) -> None:
    food = _food("Instruction Safety Food", 180)

    with pytest.raises(
        MealInstructionProviderError, match="untracked|changed a grounded"
    ):
        generate_cooking_instructions(
            user_id=1,
            request=MealInstructionGenerationRequest(
                provider="local",
                model="qwen3:8b",
                meal_name="Instruction Safety Recipe",
                ingredients=(
                    GroundedRecipeIngredient(food.id, None, food.display_name, 125),
                ),
            ),
            local_generate=lambda *_: json.dumps({"instructions": [unsafe_step]}),
        )


def test_instruction_failure_does_not_prevent_shared_meal_save(recipe_db) -> None:
    food = _food("Failure Safe Food", 120)

    def fail(*_args):
        raise RuntimeError("provider offline")

    with pytest.raises(MealInstructionProviderError):
        generate_cooking_instructions(
            user_id=1,
            request=MealInstructionGenerationRequest(
                provider="local",
                model="qwen3:8b",
                meal_name="Failure Safe Meal",
                ingredients=(
                    GroundedRecipeIngredient(food.id, None, food.display_name, 100),
                ),
            ),
            local_generate=fail,
        )

    saved = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Failure Safe Meal",
            items=(
                SavedMealItemInput(
                    food_type="canonical", canonical_food_id=food.id, grams=100
                ),
            ),
            source_type="ai",
            source_provider="local",
            source_model="qwen3:8b",
        ),
    )
    assert saved.cooking_instructions == ()


def test_recipe_scaling_is_deterministic_and_preserves_food_identity(
    recipe_db,
) -> None:
    food = _food("Scalable Recipe Food", 100)
    meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Scalable Recipe",
            items=(
                SavedMealItemInput(
                    food_type="canonical", canonical_food_id=food.id, grams=75.5
                ),
            ),
        ),
    )

    for multiplier in (1, 2, 3, 4):
        scaled = scale_saved_meal_recipe(
            user_id=1,
            saved_meal_id=meal.id,
            multiplier=multiplier,
        )
        ingredient = scaled["ingredients"][0]
        assert ingredient["canonical_food_id"] == food.id
        assert ingredient["amount_grams"] == 75.5 * multiplier
        assert scaled["current_macros"]["calories"] == 75.5 * multiplier
    assert (
        get_saved_meal(user_id=1, saved_meal_id=meal.id).items[0].resolved_grams == 75.5
    )


def test_recipe_scaling_recomputes_display_from_scaled_canonical_grams(
    recipe_db,
) -> None:
    food = _food("Scaled Cooked Rice", 130)
    create_or_update_serving_unit(
        canonical_food_id=food.id,
        unit_name="cup",
        unit_quantity=1,
        display_name="1 cup cooked rice",
        grams_default=185,
        grams_min=180,
        grams_max=190,
        confidence="High",
        source="test_catalog_measure",
    )
    meal = create_saved_meal(
        user_id=1,
        mutation=SavedMealMutationInput(
            display_name="Scaled Rice",
            items=(
                SavedMealItemInput(
                    food_type="canonical",
                    canonical_food_id=food.id,
                    grams=185,
                ),
            ),
        ),
    )

    expected = {
        1: "1 cup (185 g)",
        2: "2 cups (370 g)",
        3: "3 cups (555 g)",
        4: "4 cups (740 g)",
    }
    for multiplier, display_text in expected.items():
        scaled = scale_saved_meal_recipe(
            user_id=1,
            saved_meal_id=meal.id,
            multiplier=multiplier,
        )
        ingredient = scaled["ingredients"][0]
        assert ingredient["amount_grams"] == 185 * multiplier
        assert ingredient["quantity_display"]["canonical_grams"] == 185 * multiplier
        assert ingredient["quantity_display"]["display_text"] == display_text
        assert scaled["current_macros"]["calories"] == 130 * 1.85 * multiplier

    persisted = get_saved_meal(user_id=1, saved_meal_id=meal.id)
    assert persisted.items[0].resolved_grams == 185
    assert persisted.calories == 240.5
