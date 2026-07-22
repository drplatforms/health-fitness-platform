from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Mapping
from time import perf_counter
from typing import Any

from database import get_connection
from models.ai_run_models import AIProviderTextResult
from models.meal_instruction_models import (
    GroundedRecipeIngredient,
    MealInstructionGenerationRequest,
    MealInstructionResult,
)
from services.ai_run_telemetry_service import normalize_ai_run_telemetry
from services.meal_idea_model_service import (
    configured_meal_idea_model,
    validate_selected_meal_idea_model,
)
from services.meal_idea_service import (
    DEFAULT_LOCAL_TIMEOUT_SECONDS,
    DEFAULT_OPENAI_TIMEOUT_SECONDS,
    MEAL_IDEAS_LOCAL_TIMEOUT_ENV,
    MEAL_IDEAS_OPENAI_TIMEOUT_ENV,
    OLLAMA_BASE_URL_ENV,
    OPENAI_API_KEY_ENV,
    OPENAI_BASE_URL_ENV,
    MealIdeaProviderError,
    _call_local_provider,
    _call_openai_provider,
    _timeout,
)
from services.measurement_display_service import present_food_quantity
from services.saved_meal_service import (
    get_saved_meal,
    set_saved_meal_cooking_instructions,
)

MAX_INSTRUCTION_INGREDIENTS = 50
MAX_INSTRUCTION_STEPS = 20

InstructionGenerate = Callable[
    [str, str, float, dict[str, Any]], str | AIProviderTextResult
]

COOKING_INSTRUCTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["instructions"],
    "properties": {
        "instructions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 20,
            "items": {"type": "string"},
        }
    },
}


class MealInstructionError(ValueError):
    pass


class MealInstructionUserNotFoundError(MealInstructionError):
    pass


class MealInstructionProviderError(MealInstructionError):
    def __init__(self, code: str, public_message: str):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message


def generate_cooking_instructions(
    *,
    user_id: int,
    request: MealInstructionGenerationRequest,
    environ: Mapping[str, str] | None = None,
    local_generate: InstructionGenerate | None = None,
    openai_generate: InstructionGenerate | None = None,
) -> MealInstructionResult:
    _assert_user(user_id)
    normalized_request = _normalize_request(request)
    env = os.environ if environ is None else environ
    model, timeout_seconds, generate = _selected_instruction_provider(
        normalized_request.provider,
        normalized_request.model,
        env,
        local_generate=local_generate,
        openai_generate=openai_generate,
    )
    prompt = _build_instruction_prompt(normalized_request)
    started = perf_counter()
    try:
        provider_output = generate(
            model,
            prompt,
            timeout_seconds,
            COOKING_INSTRUCTIONS_SCHEMA,
        )
    except MealInstructionProviderError:
        raise
    except MealIdeaProviderError as exc:
        raise MealInstructionProviderError(
            exc.code,
            "Cooking instructions could not be generated. Retry or switch providers.",
        ) from exc
    except Exception as exc:
        raise MealInstructionProviderError(
            f"{normalized_request.provider}_provider_failed",
            "Cooking instructions could not be generated. Retry or switch providers.",
        ) from exc
    raw_output, telemetry = normalize_ai_run_telemetry(
        provider=normalized_request.provider,
        requested_model=model,
        runtime_seconds=perf_counter() - started,
        provider_result=provider_output,
    )
    instructions = _parse_instruction_response(raw_output)
    _validate_instruction_grounding(
        instructions,
        normalized_request.ingredients,
    )
    return MealInstructionResult(
        provider=normalized_request.provider,
        model=telemetry.model,
        instructions=instructions,
        telemetry=telemetry,
    )


def generate_and_save_cooking_instructions(
    *,
    user_id: int,
    saved_meal_id: int,
    provider: str,
    model: str | None,
    environ: Mapping[str, str] | None = None,
    local_generate: InstructionGenerate | None = None,
    openai_generate: InstructionGenerate | None = None,
) -> tuple[MealInstructionResult, Any]:
    meal = get_saved_meal(user_id=user_id, saved_meal_id=saved_meal_id)
    result = generate_cooking_instructions(
        user_id=user_id,
        request=MealInstructionGenerationRequest(
            provider=provider,
            model=model,
            meal_name=meal.display_name,
            ingredients=tuple(
                GroundedRecipeIngredient(
                    canonical_food_id=item.canonical_food_id,
                    personal_food_id=item.personal_food_id,
                    display_name=item.display_name,
                    amount_grams=item.resolved_grams,
                )
                for item in meal.items
            ),
        ),
        environ=environ,
        local_generate=local_generate,
        openai_generate=openai_generate,
    )
    saved_meal = set_saved_meal_cooking_instructions(
        user_id=user_id,
        saved_meal_id=saved_meal_id,
        instructions=result.instructions,
        telemetry=result.telemetry,
    )
    return result, saved_meal


def _selected_instruction_provider(
    provider: str,
    requested_model: str | None,
    env: Mapping[str, str],
    *,
    local_generate: InstructionGenerate | None,
    openai_generate: InstructionGenerate | None,
) -> tuple[str, float, InstructionGenerate]:
    model = validate_selected_meal_idea_model(
        provider,
        requested_model or configured_meal_idea_model(provider, environ=env),
    )
    if provider == "local":
        timeout = _timeout(
            env.get(MEAL_IDEAS_LOCAL_TIMEOUT_ENV), DEFAULT_LOCAL_TIMEOUT_SECONDS
        )
        if local_generate is not None:
            return model, timeout, local_generate

        def generate(
            model_name: str, prompt: str, seconds: float, schema: dict[str, Any]
        ) -> str | AIProviderTextResult:
            return _call_local_provider(
                model_name,
                prompt,
                seconds,
                schema,
                base_url=env.get(OLLAMA_BASE_URL_ENV),
                with_metadata=True,
                temperature=0.2,
            )

        return model, timeout, generate

    if provider == "openai":
        timeout = _timeout(
            env.get(MEAL_IDEAS_OPENAI_TIMEOUT_ENV), DEFAULT_OPENAI_TIMEOUT_SECONDS
        )
        if openai_generate is not None:
            return model, timeout, openai_generate
        api_key = env.get(OPENAI_API_KEY_ENV)
        if not api_key:
            raise MealInstructionProviderError(
                "openai_not_configured",
                "OpenAI is not configured. Add an OpenAI API key or switch to Local.",
            )

        def generate(
            model_name: str, prompt: str, seconds: float, schema: dict[str, Any]
        ) -> str | AIProviderTextResult:
            return _call_openai_provider(
                model_name,
                prompt,
                seconds,
                schema,
                api_key=api_key,
                base_url=env.get(OPENAI_BASE_URL_ENV),
                with_metadata=True,
                task_instructions=(
                    "Return exact JSON only. Explain how to cook the supplied exact "
                    "grounded recipe without changing its tracked ingredients."
                ),
                schema_name="grounded_cooking_instructions_v1",
                max_output_tokens=1400,
            )

        return model, timeout, generate
    raise MealInstructionError("provider must be local or openai.")


def _normalize_request(
    request: MealInstructionGenerationRequest,
) -> MealInstructionGenerationRequest:
    provider = str(request.provider).strip().lower()
    if provider not in {"local", "openai"}:
        raise MealInstructionError("provider must be local or openai.")
    try:
        model = (
            validate_selected_meal_idea_model(provider, request.model)
            if request.model is not None
            else None
        )
    except ValueError as exc:
        raise MealInstructionError(str(exc)) from exc
    meal_name = " ".join(str(request.meal_name).strip().split())
    if not meal_name or len(meal_name) > 120:
        raise MealInstructionError("meal_name must be between 1 and 120 characters.")
    if not 1 <= len(request.ingredients) <= MAX_INSTRUCTION_INGREDIENTS:
        raise MealInstructionError(
            "A grounded recipe must contain 1 to 50 ingredients."
        )
    normalized_ingredients = tuple(
        _normalize_ingredient(ingredient) for ingredient in request.ingredients
    )
    return MealInstructionGenerationRequest(
        provider=provider,
        model=model,
        meal_name=meal_name,
        ingredients=normalized_ingredients,
    )


def _normalize_ingredient(
    ingredient: GroundedRecipeIngredient,
) -> GroundedRecipeIngredient:
    name = " ".join(str(ingredient.display_name).strip().split())
    if not name or len(name) > 120:
        raise MealInstructionError(
            "Ingredient names must be between 1 and 120 characters."
        )
    amount = ingredient.amount_grams
    if isinstance(amount, bool) or not isinstance(amount, int | float):
        raise MealInstructionError("Ingredient amounts must be positive numbers.")
    normalized_amount = float(amount)
    if not 0 < normalized_amount <= 5000:
        raise MealInstructionError(
            "Ingredient amounts must be greater than 0 and at most 5000 grams."
        )
    if (ingredient.canonical_food_id is None) == (ingredient.personal_food_id is None):
        raise MealInstructionError(
            "Each ingredient must have exactly one canonical or personal food identity."
        )
    return GroundedRecipeIngredient(
        canonical_food_id=ingredient.canonical_food_id,
        personal_food_id=ingredient.personal_food_id,
        display_name=name,
        amount_grams=round(normalized_amount, 4),
    )


def _build_instruction_prompt(request: MealInstructionGenerationRequest) -> str:
    recipe_facts = {
        "meal_name": request.meal_name,
        "grounded_ingredients": [
            {
                "canonical_food_id": ingredient.canonical_food_id,
                "personal_food_id": ingredient.personal_food_id,
                "display_name": ingredient.display_name,
                "amount_grams": ingredient.amount_grams,
                "display_quantity": present_food_quantity(
                    canonical_food_id=ingredient.canonical_food_id,
                    grams=ingredient.amount_grams,
                ).display_text,
            }
            for ingredient in request.ingredients
        ],
    }
    return (
        "Write concise numbered cooking instructions for the exact grounded recipe "
        "below. The ingredient identities and gram quantities are immutable facts. "
        "Do not replace foods, change quantities, invent nutrition, or add calorically "
        "meaningful oil, butter, sugar, sauces, cheese, or other ingredients. Water and "
        "clearly optional non-caloric basic seasonings may be suggested, but label them "
        "optional and do not imply they are tracked. Return only the schema JSON.\n"
        f"RECIPE_FACTS:\n{json.dumps(recipe_facts, ensure_ascii=True, sort_keys=True)}"
    )


def _parse_instruction_response(raw_output: str) -> tuple[str, ...]:
    try:
        payload = json.loads(raw_output)
        if not isinstance(payload, dict) or set(payload) != {"instructions"}:
            raise ValueError("response shape")
        raw_steps = payload["instructions"]
        if (
            not isinstance(raw_steps, list)
            or not 1 <= len(raw_steps) <= MAX_INSTRUCTION_STEPS
        ):
            raise ValueError("instruction count")
        steps: list[str] = []
        for raw_step in raw_steps:
            if not isinstance(raw_step, str):
                raise ValueError("instruction type")
            step = " ".join(raw_step.strip().split())
            if not step or len(step) > 500:
                raise ValueError("instruction length")
            steps.append(step)
        return tuple(steps)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise MealInstructionProviderError(
            "malformed_instruction_response",
            "The selected model returned malformed cooking instructions. Retry or switch providers.",
        ) from exc


def _validate_instruction_grounding(
    instructions: tuple[str, ...],
    ingredients: tuple[GroundedRecipeIngredient, ...],
) -> None:
    tracked_names = " ".join(
        ingredient.display_name.casefold() for ingredient in ingredients
    )
    tracked_amounts = tuple(ingredient.amount_grams for ingredient in ingredients)
    caloric_additions = (
        "oil",
        "butter",
        "sugar",
        "honey",
        "syrup",
        "sauce",
        "cheese",
        "cream",
        "mayonnaise",
        "dressing",
    )
    addition_actions = (
        r"\b(?:add|drizzle|mix in|stir in|top with|serve with|coat with|"
        r"cook in|fry in)\b[^.]{{0,80}}\b{ingredient}\b"
    )
    for instruction in instructions:
        lowered = instruction.casefold()
        for ingredient_name in caloric_additions:
            if ingredient_name in tracked_names:
                continue
            if re.search(
                addition_actions.format(ingredient=re.escape(ingredient_name)),
                lowered,
            ):
                raise MealInstructionProviderError(
                    "unsafe_instruction_response",
                    "The selected model tried to add an untracked caloric ingredient. Retry or switch providers.",
                )
        for amount_text in re.findall(r"\b(\d+(?:\.\d+)?)\s*g(?:rams?)?\b", lowered):
            mentioned_amount = float(amount_text)
            if any(
                abs(mentioned_amount - amount) <= 0.05 for amount in tracked_amounts
            ):
                continue
            is_optional_basic_seasoning = (
                mentioned_amount <= 5
                and "optional" in lowered
                and any(
                    seasoning in lowered
                    for seasoning in ("salt", "pepper", "seasoning", "spice")
                )
            )
            if not is_optional_basic_seasoning:
                raise MealInstructionProviderError(
                    "unsafe_instruction_response",
                    "The selected model changed a grounded ingredient quantity. Retry or switch providers.",
                )


def _assert_user(user_id: int) -> None:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise MealInstructionUserNotFoundError("User not found.")
    conn = get_connection()
    try:
        row = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise MealInstructionUserNotFoundError("User not found.")
