from __future__ import annotations

import hashlib
import json
import os
import random
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date as date_cls
from typing import Any

from database import get_connection
from models.meal_idea_models import (
    MEAL_IDEA_MEAL_TYPES,
    MEAL_IDEA_PROVIDERS,
    MEAL_IDEA_STEERING_OPTIONS,
    GroundedMealIdea,
    GroundedMealIngredient,
    MealIdeaGenerationRequest,
    MealIdeasResult,
    ProposedMealIdea,
    ProposedMealIngredient,
)
from services.available_ingredient_service import list_available_ingredients
from services.food_logging_recents_service import get_recent_canonical_foods
from services.food_normalization_service import (
    ensure_food_normalization_tables,
    normalize_food_name,
)
from services.food_preference_service import list_food_preferences
from services.meal_idea_model_service import (
    configured_meal_idea_model,
    validate_selected_meal_idea_model,
)
from services.nutrition_target_vs_actual_service import (
    build_target_vs_actual_nutrition_summary,
)
from services.provider_lifecycle_service import (
    normalize_ollama_model_name,
    resolve_ollama_base_url,
    resolve_provider_lifecycle_policy,
)
from services.user_canonical_food_name_service import (
    USER_CANONICAL_FOOD_NAMES_TABLE_NAME,
    ensure_user_canonical_food_name_schema,
)

MEAL_IDEAS_LOCAL_TIMEOUT_ENV = "MEAL_IDEAS_LOCAL_TIMEOUT_SECONDS"
MEAL_IDEAS_OPENAI_TIMEOUT_ENV = "MEAL_IDEAS_OPENAI_TIMEOUT_SECONDS"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_BASE_URL_ENV = "OPENAI_BASE_URL"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"

DEFAULT_LOCAL_TIMEOUT_SECONDS = 999.0
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
MAX_PROMPT_CATALOG_FOODS = 400
MAX_LOCAL_PROMPT_CATALOG_FOODS = 140
MAX_RETURNED_IDEAS = 4

ProviderGenerate = Callable[[str, str, float, dict[str, Any]], str]

_NUTRIENT_ALIASES = {
    "calorie": "calories",
    "calories": "calories",
    "energy": "calories",
    "protein": "protein_g",
    "carbohydrate": "carbs_g",
    "carbohydrates": "carbs_g",
    "carbs": "carbs_g",
    "total carbohydrate": "carbs_g",
    "fat": "fat_g",
    "total fat": "fat_g",
}
_REQUIRED_MACROS = ("calories", "protein_g", "carbs_g", "fat_g")

OPENAI_MEAL_IDEAS_PROVIDER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ideas"],
    "properties": {
        "ideas": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "meal_type", "ingredients"],
                "properties": {
                    "name": {"type": "string"},
                    "meal_type": {
                        "type": "string",
                        "enum": list(MEAL_IDEA_MEAL_TYPES),
                    },
                    "ingredients": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 10,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "amount_grams"],
                            "properties": {
                                "name": {"type": "string"},
                                "amount_grams": {
                                    "type": "number",
                                    "exclusiveMinimum": 0,
                                    "maximum": 1200,
                                },
                            },
                        },
                    },
                },
            },
        }
    },
}

LOCAL_MEAL_IDEAS_PROVIDER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["meals"],
    "properties": {
        "meals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "meal_type", "items"],
                "properties": {
                    "name": {"type": "string"},
                    "meal_type": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["food", "grams"],
                            "properties": {
                                "food": {"type": "string"},
                                "grams": {"type": "number"},
                            },
                        },
                    },
                },
            },
        }
    },
}


class MealIdeaError(ValueError):
    pass


class MealIdeaUserNotFoundError(MealIdeaError):
    pass


class MealIdeaProviderError(MealIdeaError):
    def __init__(self, code: str, public_message: str):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message


@dataclass(frozen=True)
class _CatalogFood:
    canonical_food_id: int
    display_name: str
    original_display_name: str
    search_priority: int
    aliases: tuple[str, ...]
    macros_per_100g: dict[str, float]

    @property
    def has_complete_macros(self) -> bool:
        return all(key in self.macros_per_100g for key in _REQUIRED_MACROS)

    @property
    def normalized_names(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                normalize_food_name(value)
                for value in (
                    self.display_name,
                    self.original_display_name,
                    *self.aliases,
                )
                if value.strip()
            )
        )


@dataclass(frozen=True)
class _GenerationContext:
    catalog: tuple[_CatalogFood, ...]
    available_ids: frozenset[int]
    preferences_by_id: dict[int, str]
    recent_ids: tuple[int, ...]
    nutrition: dict[str, Any]


def generate_meal_ideas(
    *,
    user_id: int,
    target_date: str,
    request: MealIdeaGenerationRequest,
    environ: Mapping[str, str] | None = None,
    local_generate: ProviderGenerate | None = None,
    openai_generate: ProviderGenerate | None = None,
) -> MealIdeasResult:
    """Generate creative concepts, then ground every displayed fact locally.

    Provider selection is explicit. Errors remain attached to the selected
    provider; this function never calls the other provider as a fallback.
    """

    _validate_generation_input(user_id, target_date, request)
    context = _build_generation_context(user_id=user_id, target_date=target_date)
    env = os.environ if environ is None else environ
    model, timeout_seconds, generate = _selected_provider_runtime(
        request.provider,
        request.model,
        env,
        local_generate=local_generate,
        openai_generate=openai_generate,
    )
    prompt = _build_prompt(
        user_id=user_id,
        target_date=target_date,
        request=request,
        context=context,
    )

    provider_schema = (
        LOCAL_MEAL_IDEAS_PROVIDER_SCHEMA
        if request.provider == "local"
        else OPENAI_MEAL_IDEAS_PROVIDER_SCHEMA
    )
    try:
        raw_output = generate(
            model,
            prompt,
            timeout_seconds,
            provider_schema,
        )
    except MealIdeaProviderError:
        raise
    except Exception as exc:
        provider_label = "Local" if request.provider == "local" else "OpenAI"
        raise MealIdeaProviderError(
            f"{request.provider}_provider_failed",
            f"{provider_label} could not generate meal ideas. Retry or switch providers.",
        ) from exc

    proposed, normalization_rejections, normalization_reasons = (
        _parse_provider_response(
            raw_output,
            provider=request.provider,
            model=model,
        )
    )
    grounded, grounding_reasons = _ground_proposed_ideas(
        proposed,
        context=context,
    )
    if not grounded:
        if request.provider == "local":
            raise MealIdeaProviderError(
                "local_grounding_rejected",
                _local_grounding_failure_message(
                    model=model,
                    normalization_reasons=normalization_reasons,
                    grounding_reasons=grounding_reasons,
                ),
            )
        provider_label = "Local" if request.provider == "local" else "OpenAI"
        raise MealIdeaProviderError(
            "meal_ideas_not_groundable",
            f"{provider_label} returned ideas that could not be matched reliably to your food catalog. Retry for a new set or switch providers.",
        )

    return MealIdeasResult(
        provider=request.provider,
        model=model,
        target_date=target_date,
        ideas=tuple(grounded[:MAX_RETURNED_IDEAS]),
        rejected_concept_count=(
            normalization_rejections + sum(grounding_reasons.values())
        ),
        context_signals={
            "usable_catalog_food_count": sum(
                food.has_complete_macros for food in context.catalog
            ),
            "available_ingredient_count": len(context.available_ids),
            "food_preference_count": len(context.preferences_by_id),
            "recent_food_count": len(context.recent_ids),
            "nutrition_context_available": bool(context.nutrition),
        },
    )


def _validate_generation_input(
    user_id: int,
    target_date: str,
    request: MealIdeaGenerationRequest,
) -> None:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise MealIdeaUserNotFoundError("User not found.")
    conn = get_connection()
    user_exists = conn.execute(
        "SELECT 1 FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if user_exists is None:
        raise MealIdeaUserNotFoundError("User not found.")
    try:
        date_cls.fromisoformat(target_date)
    except (TypeError, ValueError) as exc:
        raise MealIdeaError("target_date must use YYYY-MM-DD format.") from exc
    if request.provider not in MEAL_IDEA_PROVIDERS:
        raise MealIdeaError("provider must be local or openai.")
    if request.model is not None:
        try:
            validate_selected_meal_idea_model(request.provider, request.model)
        except ValueError as exc:
            raise MealIdeaError(str(exc)) from exc
    if request.creative_steering not in MEAL_IDEA_STEERING_OPTIONS:
        raise MealIdeaError("creative_steering is not supported.")
    if request.meal_type is not None and request.meal_type not in MEAL_IDEA_MEAL_TYPES:
        raise MealIdeaError("meal_type is not supported.")
    if request.intent is not None and len(request.intent.strip()) > 240:
        raise MealIdeaError("intent must be 240 characters or fewer.")
    if len(request.previous_idea_names) > 20 or any(
        len(name.strip()) > 100 for name in request.previous_idea_names
    ):
        raise MealIdeaError("previous_idea_names is too large.")
    if len(request.recent_generated_food_names) > 40 or any(
        len(name.strip()) > 120 for name in request.recent_generated_food_names
    ):
        raise MealIdeaError("recent_generated_food_names is too large.")


def _build_generation_context(*, user_id: int, target_date: str) -> _GenerationContext:
    catalog = _load_catalog(user_id=user_id)
    available = list_available_ingredients(user_id=user_id)
    preferences = list_food_preferences(user_id=user_id)
    recent = get_recent_canonical_foods(user_id=user_id, limit=20)
    return _GenerationContext(
        catalog=tuple(catalog),
        available_ids=frozenset(int(item["canonical_food_id"]) for item in available),
        preferences_by_id={
            int(item["canonical_food_id"]): str(item["preference"])
            for item in preferences
        },
        recent_ids=tuple(int(item["canonical_food_id"]) for item in recent),
        nutrition=_remaining_nutrition_context(user_id, target_date),
    )


def _load_catalog(*, user_id: int) -> list[_CatalogFood]:
    ensure_food_normalization_tables()
    ensure_user_canonical_food_name_schema()
    conn = get_connection()
    food_rows = conn.execute(
        f"""
        SELECT foods.id, foods.display_name AS original_display_name,
               COALESCE(names.display_name, foods.display_name) AS display_name,
               foods.search_priority
        FROM canonical_foods AS foods
        LEFT JOIN {USER_CANONICAL_FOOD_NAMES_TABLE_NAME} AS names
          ON names.canonical_food_id = foods.id AND names.user_id = ?
        WHERE foods.active = 1
        ORDER BY foods.search_priority, foods.id
        """,
        (user_id,),
    ).fetchall()
    nutrient_rows = conn.execute(
        """
        SELECT nutrients.canonical_food_id, nutrients.nutrient_name,
               nutrients.amount_per_100g
        FROM canonical_food_nutrients AS nutrients
        JOIN canonical_foods AS foods ON foods.id = nutrients.canonical_food_id
        WHERE foods.active = 1
        """
    ).fetchall()
    alias_rows = conn.execute(
        """
        SELECT aliases.canonical_food_id, aliases.alias
        FROM canonical_food_aliases AS aliases
        JOIN canonical_foods AS foods ON foods.id = aliases.canonical_food_id
        WHERE foods.active = 1
        ORDER BY aliases.priority, aliases.id
        """
    ).fetchall()
    conn.close()

    macros_by_id: dict[int, dict[str, float]] = {}
    for row in nutrient_rows:
        key = _NUTRIENT_ALIASES.get(str(row["nutrient_name"]).strip().lower())
        if key is not None:
            macros_by_id.setdefault(int(row["canonical_food_id"]), {})[key] = float(
                row["amount_per_100g"]
            )
    aliases_by_id: dict[int, list[str]] = {}
    for row in alias_rows:
        aliases_by_id.setdefault(int(row["canonical_food_id"]), []).append(
            str(row["alias"])
        )
    return [
        _CatalogFood(
            canonical_food_id=int(row["id"]),
            display_name=str(row["display_name"]),
            original_display_name=str(row["original_display_name"]),
            search_priority=int(row["search_priority"]),
            aliases=tuple(aliases_by_id.get(int(row["id"]), [])),
            macros_per_100g=macros_by_id.get(int(row["id"]), {}),
        )
        for row in food_rows
    ]


def _remaining_nutrition_context(user_id: int, target_date: str) -> dict[str, Any]:
    try:
        summary = build_target_vs_actual_nutrition_summary(user_id, target_date)
    except Exception:
        return {}

    nutrients: dict[str, Any] = {}
    for name, comparison in summary.comparisons.items():
        remaining_to_min = None
        remaining_to_max = None
        if comparison.comparison_available and comparison.actual is not None:
            if comparison.target_min is not None:
                remaining_to_min = round(comparison.target_min - comparison.actual, 1)
            if comparison.target_max is not None:
                remaining_to_max = round(comparison.target_max - comparison.actual, 1)
        nutrients[name] = {
            "logged": comparison.actual,
            "target_min": comparison.target_min,
            "target_max": comparison.target_max,
            "remaining_to_min": remaining_to_min,
            "remaining_to_max": remaining_to_max,
            "status": comparison.target_status,
            "comparison_available": comparison.comparison_available,
        }
    return {
        "date": summary.date,
        "logging_completeness": summary.logging_completeness,
        "confidence": summary.confidence,
        "nutrients": nutrients,
    }


def _build_prompt(
    *,
    user_id: int,
    target_date: str,
    request: MealIdeaGenerationRequest,
    context: _GenerationContext,
) -> str:
    if request.provider == "local":
        return _build_local_prompt(
            user_id=user_id,
            target_date=target_date,
            request=request,
            context=context,
        )
    return _build_openai_prompt(
        user_id=user_id,
        target_date=target_date,
        request=request,
        context=context,
    )


def _build_local_prompt(
    *,
    user_id: int,
    target_date: str,
    request: MealIdeaGenerationRequest,
    context: _GenerationContext,
) -> str:
    catalog_by_id = {food.canonical_food_id: food for food in context.catalog}
    usable_catalog = [food for food in context.catalog if food.has_complete_macros]
    prompt_catalog = _prompt_catalog_sample(
        usable_catalog,
        seed=_generation_seed(user_id, target_date, request),
        limit=MAX_LOCAL_PROMPT_CATALOG_FOODS,
    )

    def names_for_ids(ids: list[int] | tuple[int, ...] | frozenset[int]) -> list[str]:
        return [
            catalog_by_id[food_id].display_name
            for food_id in ids
            if food_id in catalog_by_id
        ]

    preferences = {
        state: names_for_ids(
            [
                food_id
                for food_id, value in context.preferences_by_id.items()
                if value == state
            ]
        )
        for state in ("love", "like", "dislike", "never_suggest")
    }
    compact_context = {
        "date": target_date,
        "direction": request.creative_steering,
        "meal_type": request.meal_type,
        "intent": request.intent,
        "catalog_food_names": [food.display_name for food in prompt_catalog],
        "full_usable_catalog_count": len(usable_catalog),
        "nutrition": context.nutrition,
        "preferences": preferences,
        "recent_logged_foods_soft": names_for_ids(context.recent_ids),
        "recent_generated_foods_soft": list(request.recent_generated_food_names),
        "recent_generated_idea_names_soft": list(request.previous_idea_names),
        "optional_available_convenience": {
            "foods": names_for_ids(context.available_ids),
            "meaning": (
                "Optional foods already on hand. This is not a candidate pool, "
                "restriction, or optimization target."
            ),
        },
    }
    return (
        "Create exactly 3 distinct meal ideas. Return JSON only.\n"
        "Use this shape: meals -> [{name, meal_type, items -> [{food, grams}]}].\n"
        "meal_type must be breakfast, lunch, dinner, snack, or dessert.\n"
        "Use 2 to 7 items per meal. food must be an exact catalog food name. "
        "grams must be a positive number. Do not include nutrition or instructions.\n"
        "Start from the full catalog and the requested direction, not from Available. "
        "Available is optional convenience context only: do not maximize overlap, and "
        "it is normal for an idea to use no Available foods. Love/like are small positive "
        "hints only. Dislike and recent exposure are small negative hints only. Repeat a "
        "recent food when it is genuinely appropriate; never force an incoherent swap. "
        "Never use never_suggest foods. Explicit intent overrides all soft hints but not "
        "never_suggest.\n"
        "The catalog list is a broad sample, not a restriction; familiar foods from "
        "the full catalog are allowed if you use their exact canonical name.\n"
        f"CONTEXT:\n{json.dumps(compact_context, ensure_ascii=False)}\n"
    )


def _build_openai_prompt(
    *,
    user_id: int,
    target_date: str,
    request: MealIdeaGenerationRequest,
    context: _GenerationContext,
) -> str:
    catalog_by_id = {food.canonical_food_id: food for food in context.catalog}
    usable_catalog = [food for food in context.catalog if food.has_complete_macros]
    prompt_catalog = _prompt_catalog_sample(
        usable_catalog,
        seed=_generation_seed(user_id, target_date, request),
        limit=MAX_PROMPT_CATALOG_FOODS,
    )

    def names_for_ids(ids: list[int] | tuple[int, ...] | frozenset[int]) -> list[str]:
        return [
            catalog_by_id[food_id].display_name
            for food_id in ids
            if food_id in catalog_by_id
        ]

    preferences: dict[str, list[str]] = {
        state: names_for_ids(
            [
                food_id
                for food_id, value in context.preferences_by_id.items()
                if value == state
            ]
        )
        for state in ("love", "like", "dislike", "never_suggest")
    }
    prompt_context = {
        "target_date": target_date,
        "creative_steering": request.creative_steering,
        "meal_type": request.meal_type,
        "user_intent": request.intent,
        "generation_nonce": request.generation_nonce,
        "catalog_examples_not_a_restriction": [
            {"name": food.display_name, "aliases": list(food.aliases[:2])}
            for food in prompt_catalog
        ],
        "usable_catalog_food_count": len(usable_catalog),
        "remaining_nutrition_context": context.nutrition,
        "food_preferences": preferences,
        "recent_logged_foods_soft_repetition_signal": names_for_ids(context.recent_ids),
        "recent_generated_foods_soft_repetition_signal": list(
            request.recent_generated_food_names
        ),
        "recent_generated_idea_names_soft_repetition_signal": list(
            request.previous_idea_names
        ),
        "optional_available_ingredient_convenience": {
            "foods": names_for_ids(context.available_ids),
            "meaning": (
                "Optional foods already on hand. This is not a candidate pool, "
                "restriction, or optimization target."
            ),
        },
    }
    return (
        "Generate 3 to 5 distinct, practical meal concepts as one raw JSON object. "
        "Return exactly the requested schema and no markdown or commentary.\n"
        "AI owns creative ideation only. Do not return calories, macros, health claims, "
        "or preparation prose. The application will calculate nutrition.\n"
        "Each ingredient must use the exact name of a real canonical catalog food and "
        "include a plausible amount_grams. Prefer names shown in catalog examples, but "
        "the full usable canonical catalog remains allowed; examples are a rotating, "
        "broad prompt sample rather than an ingredient restriction.\n"
        "Start from the full catalog and creative request, not from Available Ingredients. "
        "Available is optional convenience context only: do not maximize overlap, do not "
        "build primarily from it, and allow ideas that use none. Love and Like are small "
        "positive signals. Dislike is a small negative signal, never an exclusion.\n"
        "Never use any food listed under never_suggest. Recent generated foods, recent "
        "logged foods, and prior idea names should softly discourage repetition without "
        "forcing random substitutions or prohibiting a genuinely appropriate repeat. "
        "Explicit intent may override Love, Like, Dislike, or repetition signals, but "
        "never never_suggest.\n"
        "Make the concepts meaningfully different from one another. Do not optimize every "
        "idea toward the same macros or favored ingredients.\n\n"
        f"GENERATION_CONTEXT:\n{json.dumps(prompt_context, ensure_ascii=False)}\n"
    )


def _prompt_catalog_sample(
    foods: list[_CatalogFood],
    *,
    seed: int,
    limit: int,
) -> list[_CatalogFood]:
    if len(foods) <= limit:
        return foods
    rng = random.Random(seed)
    return rng.sample(foods, min(limit, len(foods)))


def _generation_seed(
    user_id: int, target_date: str, request: MealIdeaGenerationRequest
) -> int:
    material = "|".join(
        (
            str(user_id),
            target_date,
            request.generation_nonce or "",
            request.intent or "",
            request.creative_steering,
        )
    )
    return int(hashlib.sha256(material.encode("utf-8")).hexdigest()[:16], 16)


def _selected_provider_runtime(
    provider: str,
    requested_model: str | None,
    env: Mapping[str, str],
    *,
    local_generate: ProviderGenerate | None,
    openai_generate: ProviderGenerate | None,
) -> tuple[str, float, ProviderGenerate]:
    if provider == "local":
        model = validate_selected_meal_idea_model(
            provider,
            requested_model or configured_meal_idea_model(provider, environ=env),
        )
        timeout = _timeout(
            env.get(MEAL_IDEAS_LOCAL_TIMEOUT_ENV), DEFAULT_LOCAL_TIMEOUT_SECONDS
        )
        if local_generate is not None:
            return model, timeout, local_generate

        def generate(
            model_name: str, prompt: str, seconds: float, schema: dict[str, Any]
        ) -> str:
            return _call_local_provider(
                model_name,
                prompt,
                seconds,
                schema,
                base_url=env.get(OLLAMA_BASE_URL_ENV),
            )

        return model, timeout, generate

    if provider == "openai":
        model = validate_selected_meal_idea_model(
            provider,
            requested_model or configured_meal_idea_model(provider, environ=env),
        )
        timeout = _timeout(
            env.get(MEAL_IDEAS_OPENAI_TIMEOUT_ENV), DEFAULT_OPENAI_TIMEOUT_SECONDS
        )
        if openai_generate is not None:
            return model, timeout, openai_generate
        api_key = env.get(OPENAI_API_KEY_ENV)
        if not api_key:
            raise MealIdeaProviderError(
                "openai_not_configured",
                "OpenAI is not configured. Add an OpenAI API key or switch to Local.",
            )

        def generate(
            model_name: str, prompt: str, seconds: float, schema: dict[str, Any]
        ) -> str:
            return _call_openai_provider(
                model_name,
                prompt,
                seconds,
                schema,
                api_key=api_key,
                base_url=env.get(OPENAI_BASE_URL_ENV),
            )

        return model, timeout, generate

    raise MealIdeaError("provider must be local or openai.")


def _call_local_provider(
    model: str,
    prompt: str,
    timeout_seconds: float,
    schema: dict[str, Any],
    *,
    base_url: str | None,
) -> str:
    policy = resolve_provider_lifecycle_policy(
        provider_name="meal_ideas_local",
        model_name=model,
    )
    payload = {
        "model": normalize_ollama_model_name(model),
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": schema,
        "think": False,
        "keep_alive": policy.keep_alive_value,
        "options": {"temperature": 0.7},
    }
    endpoint = resolve_ollama_base_url(base_url=base_url).rstrip("/") + "/api/chat"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_detail = _bounded_ollama_error_body(exc)
        code = "local_model_not_found" if exc.code == 404 else "local_http_error"
        raise MealIdeaProviderError(
            code,
            f"Ollama returned HTTP {exc.code} for Local model {model}. {error_detail}",
        ) from exc
    except TimeoutError as exc:
        raise MealIdeaProviderError(
            "local_timeout",
            f"Local model {model} did not finish within {timeout_seconds:g} seconds. Retry or choose a faster Local model.",
        ) from exc
    except urllib.error.URLError as exc:
        raise MealIdeaProviderError(
            "local_connection_error",
            "Ollama could not be reached at the configured Local address.",
        ) from exc
    except OSError as exc:
        raise MealIdeaProviderError(
            "local_transport_error",
            f"The Local request for model {model} ended before a response was received.",
        ) from exc
    try:
        response_payload = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise MealIdeaProviderError(
            "local_invalid_http_response",
            f"Ollama returned a non-JSON response for Local model {model}.",
        ) from exc
    message = response_payload.get("message")
    raw_text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise MealIdeaProviderError(
            "local_empty_response",
            f"Ollama returned no structured content for Local model {model}.",
        )
    return raw_text


def _bounded_ollama_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
        detail = payload.get("error") if isinstance(payload, dict) else None
        message = detail if isinstance(detail, str) else raw
    except Exception:
        message = ""
    compact = " ".join(message.strip().split())[:240]
    return compact or "Check the selected model and Ollama logs."


def _call_openai_provider(
    model: str,
    prompt: str,
    timeout_seconds: float,
    schema: dict[str, Any],
    *,
    api_key: str,
    base_url: str | None,
) -> str:
    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url.rstrip("/")
    try:
        from openai import OpenAI

        client = OpenAI(**client_kwargs)
        response = client.responses.create(
            model=model,
            instructions="Return exact JSON only for the supplied meal-idea schema.",
            input=prompt,
            max_output_tokens=2200,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "meal_ideas_v1",
                    "schema": schema,
                    "strict": True,
                }
            },
            timeout=timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - SDK behavior is mocked in tests
        raise MealIdeaProviderError(
            "openai_provider_failed",
            "OpenAI could not generate meal ideas. Retry or switch providers.",
        ) from exc
    raw_text = _extract_openai_text(response)
    if not raw_text:
        raise MealIdeaProviderError(
            "openai_empty_response",
            "OpenAI returned an empty response. Retry or switch providers.",
        )
    return raw_text


def _extract_openai_text(response: Any) -> str | None:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    parts: list[str] = []
    output = getattr(response, "output", None)
    if isinstance(output, list):
        for item in output:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if isinstance(text, str):
                    parts.append(text)
    return "".join(parts).strip() or None


def _parse_provider_response(
    raw_output: str,
    *,
    provider: str,
    model: str,
) -> tuple[tuple[ProposedMealIdea, ...], int, dict[str, int]]:
    if provider == "local":
        return _parse_local_provider_response(raw_output, model=model)
    return _parse_openai_provider_response(raw_output)


def _parse_openai_provider_response(
    raw_output: str,
) -> tuple[tuple[ProposedMealIdea, ...], int, dict[str, int]]:
    try:
        payload = json.loads(raw_output)
        if not isinstance(payload, dict) or set(payload) != {"ideas"}:
            raise ValueError("response keys")
        raw_ideas = payload["ideas"]
        if not isinstance(raw_ideas, list) or not 3 <= len(raw_ideas) <= 5:
            raise ValueError("idea count")
        ideas: list[ProposedMealIdea] = []
        for raw_idea in raw_ideas:
            if not isinstance(raw_idea, dict) or set(raw_idea) != {
                "name",
                "meal_type",
                "ingredients",
            }:
                raise ValueError("idea shape")
            name = _required_text(raw_idea["name"], max_length=100)
            meal_type = _required_text(raw_idea["meal_type"], max_length=20).lower()
            if meal_type not in MEAL_IDEA_MEAL_TYPES:
                raise ValueError("meal type")
            raw_ingredients = raw_idea["ingredients"]
            if (
                not isinstance(raw_ingredients, list)
                or not 2 <= len(raw_ingredients) <= 10
            ):
                raise ValueError("ingredients")
            ingredients: list[ProposedMealIngredient] = []
            for raw_ingredient in raw_ingredients:
                if not isinstance(raw_ingredient, dict) or set(raw_ingredient) != {
                    "name",
                    "amount_grams",
                }:
                    raise ValueError("ingredient shape")
                ingredient_name = _required_text(raw_ingredient["name"], max_length=120)
                amount = raw_ingredient["amount_grams"]
                if isinstance(amount, bool) or not isinstance(amount, int | float):
                    raise ValueError("ingredient amount")
                amount = float(amount)
                if not 0 < amount <= 1200:
                    raise ValueError("ingredient amount range")
                ingredients.append(
                    ProposedMealIngredient(name=ingredient_name, amount_grams=amount)
                )
            ideas.append(
                ProposedMealIdea(
                    name=name,
                    meal_type=meal_type,
                    ingredients=tuple(ingredients),
                )
            )
        return tuple(ideas), 0, {}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise MealIdeaProviderError(
            "malformed_provider_response",
            "OpenAI returned a malformed meal-idea response. Retry or switch providers.",
        ) from exc


def _parse_local_provider_response(
    raw_output: str,
    *,
    model: str,
) -> tuple[tuple[ProposedMealIdea, ...], int, dict[str, int]]:
    try:
        payload = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError) as exc:
        raise _local_response_error(model, "invalid_json") from exc
    if not isinstance(payload, dict) or set(payload) != {"meals"}:
        raise _local_response_error(model, "invalid_root_shape")
    raw_meals = payload["meals"]
    if not isinstance(raw_meals, list) or not 1 <= len(raw_meals) <= 5:
        raise _local_response_error(model, "invalid_meal_count")

    ideas: list[ProposedMealIdea] = []
    rejection_reasons: dict[str, int] = {}
    for raw_meal in raw_meals:
        try:
            ideas.append(_normalize_local_meal(raw_meal))
        except (KeyError, TypeError, ValueError) as exc:
            reason = str(exc) or "invalid_concept"
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
    if not ideas:
        reason = max(rejection_reasons, key=rejection_reasons.get)  # type: ignore[arg-type]
        raise _local_response_error(model, reason)
    return tuple(ideas), sum(rejection_reasons.values()), rejection_reasons


def _normalize_local_meal(raw_meal: Any) -> ProposedMealIdea:
    if not isinstance(raw_meal, dict) or set(raw_meal) != {
        "name",
        "meal_type",
        "items",
    }:
        raise ValueError("invalid_concept_shape")
    name = _required_text(raw_meal["name"], max_length=100)
    meal_type = _required_text(raw_meal["meal_type"], max_length=20).lower()
    if meal_type not in MEAL_IDEA_MEAL_TYPES:
        raise ValueError("invalid_meal_type")
    raw_items = raw_meal["items"]
    if not isinstance(raw_items, list) or not 2 <= len(raw_items) <= 10:
        raise ValueError("invalid_item_count")
    ingredients: list[ProposedMealIngredient] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict) or set(raw_item) != {"food", "grams"}:
            raise ValueError("invalid_item_shape")
        food_name = _required_text(raw_item["food"], max_length=120)
        grams = raw_item["grams"]
        if isinstance(grams, bool) or not isinstance(grams, int | float):
            raise ValueError("invalid_grams")
        amount = float(grams)
        if not 0 < amount <= 1200:
            raise ValueError("invalid_grams")
        ingredients.append(ProposedMealIngredient(name=food_name, amount_grams=amount))
    return ProposedMealIdea(
        name=name,
        meal_type=meal_type,
        ingredients=tuple(ingredients),
    )


def _local_response_error(model: str, reason: str) -> MealIdeaProviderError:
    safe_reason = reason if reason.replace("_", "").isalnum() else "invalid_structure"
    return MealIdeaProviderError(
        "local_response_malformed",
        f"Local model {model} returned structured output that could not be normalized ({safe_reason}).",
    )


def _required_text(value: Any, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError("text required")
    resolved = " ".join(value.strip().split())
    if not resolved or len(resolved) > max_length:
        raise ValueError("invalid text")
    return resolved


def _ground_proposed_ideas(
    proposed: tuple[ProposedMealIdea, ...],
    *,
    context: _GenerationContext,
) -> tuple[list[GroundedMealIdea], dict[str, int]]:
    hard_exclusion_ids = {
        food_id
        for food_id, state in context.preferences_by_id.items()
        if state == "never_suggest"
    }
    grounded: list[GroundedMealIdea] = []
    rejection_reasons: dict[str, int] = {}
    for idea in proposed:
        ingredients: list[GroundedMealIngredient] = []
        seen_ids: set[int] = set()
        rejection_reason: str | None = None
        for proposed_ingredient in idea.ingredients:
            if any(
                _food_name_match_score(proposed_ingredient.name, food) >= 70
                for food in context.catalog
                if food.canonical_food_id in hard_exclusion_ids
            ):
                rejection_reason = "never_suggest"
                break
            food = _resolve_catalog_food(proposed_ingredient.name, context.catalog)
            if food is None:
                rejection_reason = "unknown_ingredient"
                break
            if not food.has_complete_macros:
                rejection_reason = "missing_catalog_nutrition"
                break
            if food.canonical_food_id in hard_exclusion_ids:
                rejection_reason = "never_suggest"
                break
            if food.canonical_food_id in seen_ids:
                rejection_reason = "duplicate_ingredient"
                break
            seen_ids.add(food.canonical_food_id)
            scale = proposed_ingredient.amount_grams / 100.0
            ingredients.append(
                GroundedMealIngredient(
                    canonical_food_id=food.canonical_food_id,
                    display_name=food.display_name,
                    amount_grams=round(proposed_ingredient.amount_grams, 1),
                    is_available=food.canonical_food_id in context.available_ids,
                    calories=round(food.macros_per_100g["calories"] * scale, 1),
                    protein_g=round(food.macros_per_100g["protein_g"] * scale, 1),
                    carbs_g=round(food.macros_per_100g["carbs_g"] * scale, 1),
                    fat_g=round(food.macros_per_100g["fat_g"] * scale, 1),
                )
            )
        if rejection_reason is not None or len(ingredients) < 2:
            reason = rejection_reason or "too_few_grounded_ingredients"
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
            continue
        grounded.append(
            GroundedMealIdea(
                name=idea.name,
                meal_type=idea.meal_type,
                ingredients=tuple(ingredients),
                calories=round(sum(item.calories for item in ingredients), 1),
                protein_g=round(sum(item.protein_g for item in ingredients), 1),
                carbs_g=round(sum(item.carbs_g for item in ingredients), 1),
                fat_g=round(sum(item.fat_g for item in ingredients), 1),
                available_ingredient_count=sum(
                    item.is_available for item in ingredients
                ),
            )
        )
    return grounded, rejection_reasons


def _local_grounding_failure_message(
    *,
    model: str,
    normalization_reasons: dict[str, int],
    grounding_reasons: dict[str, int],
) -> str:
    combined = {**normalization_reasons}
    for reason, count in grounding_reasons.items():
        combined[reason] = combined.get(reason, 0) + count
    summary = ", ".join(
        f"{reason}={count}" for reason, count in sorted(combined.items())
    )
    summary = summary[:260] or "no_groundable_concepts"
    return (
        f"Local model {model} returned meal concepts, but none passed catalog "
        f"grounding ({summary})."
    )


def _resolve_catalog_food(
    proposed_name: str,
    catalog: tuple[_CatalogFood, ...],
) -> _CatalogFood | None:
    query = normalize_food_name(proposed_name)
    primary_exact = [
        food
        for food in catalog
        if query
        in {
            normalize_food_name(food.display_name),
            normalize_food_name(food.original_display_name),
        }
    ]
    if primary_exact:
        return _unique_exact_food(primary_exact)

    alias_exact = [
        food
        for food in catalog
        if query in {normalize_food_name(alias) for alias in food.aliases}
    ]
    if alias_exact:
        return _unique_exact_food(alias_exact)

    scored: list[tuple[int, _CatalogFood]] = []
    for food in catalog:
        score = _food_name_match_score(query, food, query_is_normalized=True)
        if score >= 70:
            scored.append((score, food))
    if not scored:
        return None
    scored.sort(
        key=lambda item: (-item[0], item[1].search_priority, item[1].canonical_food_id)
    )
    best_score, best_food = scored[0]
    tied_ids = {food.canonical_food_id for score, food in scored if score == best_score}
    return best_food if len(tied_ids) == 1 else None


def _unique_exact_food(matches: list[_CatalogFood]) -> _CatalogFood | None:
    by_id = {food.canonical_food_id: food for food in matches}
    return next(iter(by_id.values())) if len(by_id) == 1 else None


def _food_name_match_score(
    proposed_name: str,
    food: _CatalogFood,
    *,
    query_is_normalized: bool = False,
) -> int:
    query = proposed_name if query_is_normalized else normalize_food_name(proposed_name)
    return max(
        (_name_match_score(query, name) for name in food.normalized_names),
        default=0,
    )


def _name_match_score(query: str, candidate: str) -> int:
    if query == candidate:
        return 100
    query_tokens = set(query.split())
    candidate_tokens = set(candidate.split())
    if min(len(query_tokens), len(candidate_tokens)) < 2:
        return 0
    overlap = len(query_tokens & candidate_tokens)
    if overlap < 2:
        return 0
    if query_tokens <= candidate_tokens or candidate_tokens <= query_tokens:
        return 88 - abs(len(query_tokens) - len(candidate_tokens))
    union = len(query_tokens | candidate_tokens)
    return round(100 * overlap / union) if union else 0


def _timeout(raw: str | None, default: float) -> float:
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default
