from __future__ import annotations

import json

import database
from models.ai_run_models import AIProviderTextResult
from models.meal_instruction_models import (
    GroundedRecipeIngredient,
    MealInstructionGenerationRequest,
)
from services.meal_instruction_service import generate_cooking_instructions


def test_instruction_generation_accepts_snapshot_alias_and_requests_canonical_model(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "instruction_model.db")
    database.initialize_database()
    observed_models: list[str] = []

    def generate(model, prompt, timeout, schema):
        del prompt, timeout, schema
        observed_models.append(model)
        return AIProviderTextResult(
            text=json.dumps({"instructions": ["Cook the exact 100 g portion."]}),
            model="gpt-5.4-mini-2026-03-17",
            input_tokens=100,
            cached_input_tokens=20,
            output_tokens=30,
        )

    result = generate_cooking_instructions(
        user_id=1,
        request=MealInstructionGenerationRequest(
            provider="openai",
            model="gpt-5.4-mini-2026-03-17",
            meal_name="Snapshot Recipe",
            ingredients=(
                GroundedRecipeIngredient(
                    canonical_food_id=1,
                    personal_food_id=None,
                    display_name="Snapshot Ingredient",
                    amount_grams=100,
                ),
            ),
        ),
        environ={},
        openai_generate=generate,
    )

    assert observed_models == ["gpt-5.4-mini"]
    assert result.model == "gpt-5.4-mini-2026-03-17"
    assert result.telemetry.model == "gpt-5.4-mini-2026-03-17"
    assert result.telemetry.estimated_api_cost_usd is not None
