from __future__ import annotations

import json

import pytest

import database
from models.meal_idea_models import MealIdeaGenerationRequest
from services import meal_idea_service
from services.available_ingredient_service import add_available_ingredient
from services.food_normalization_service import (
    create_canonical_food,
    create_canonical_food_alias,
    create_canonical_food_nutrient,
    ensure_food_normalization_tables,
)
from services.food_preference_service import set_food_preference
from services.user_canonical_food_name_service import set_user_canonical_food_name


@pytest.fixture
def meal_idea_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "meal_ideas.db")
    database.initialize_database()
    ensure_food_normalization_tables()
    monkeypatch.setattr(
        meal_idea_service,
        "_remaining_nutrition_context",
        lambda user_id, target_date: {
            "date": target_date,
            "confidence": "Moderate",
            "nutrients": {"calories": {"remaining_to_max": 700}},
        },
    )


def _food(name: str, *, calories: float, protein: float, carbs: float, fat: float):
    food = create_canonical_food(name, "generic", default_grams=100)
    for nutrient_name, amount, unit in (
        ("Calories", calories, "kcal"),
        ("Protein", protein, "g"),
        ("Carbohydrates", carbs, "g"),
        ("Fat", fat, "g"),
    ):
        create_canonical_food_nutrient(food.id, nutrient_name, unit, amount)
    return food


def _raw_ideas(*ideas: dict) -> str:
    padded = [dict(idea) for idea in ideas]
    while padded and len(padded) < 3:
        copy = dict(padded[-1])
        copy["name"] = f"{copy['name']} Variation {len(padded) + 1}"
        padded.append(copy)
    return json.dumps(
        {
            "meals": [
                {
                    "name": idea["name"],
                    "meal_type": idea["meal_type"],
                    "items": [
                        {"food": item["name"], "grams": item["amount_grams"]}
                        for item in idea["ingredients"]
                    ],
                }
                for idea in padded
            ]
        }
    )


def _raw_openai_ideas(*ideas: dict) -> str:
    padded = [dict(idea) for idea in ideas]
    while padded and len(padded) < 3:
        copy = dict(padded[-1])
        copy["name"] = f"{copy['name']} Variation {len(padded) + 1}"
        padded.append(copy)
    return json.dumps({"ideas": padded})


def _idea(name: str, *ingredients: tuple[str, float], meal_type: str = "dinner"):
    return {
        "name": name,
        "meal_type": meal_type,
        "ingredients": [
            {"name": ingredient_name, "amount_grams": grams}
            for ingredient_name, grams in ingredients
        ],
    }


def _request(provider: str = "local", **overrides):
    values = {
        "provider": provider,
        "creative_steering": "surprise_me",
        "generation_nonce": "test-generation",
    }
    values.update(overrides)
    return MealIdeaGenerationRequest(**values)


def test_local_and_openai_selection_are_explicit_and_do_not_cross_call(
    meal_idea_db,
) -> None:
    chicken = _food("Selection Chicken", calories=200, protein=30, carbs=0, fat=8)
    rice = _food("Selection Rice", calories=130, protein=3, carbs=28, fat=1)
    local_raw = _raw_ideas(
        _idea("Selection Bowl", (chicken.display_name, 100), (rice.display_name, 150))
    )
    openai_raw = _raw_openai_ideas(
        _idea("Selection Bowl", (chicken.display_name, 100), (rice.display_name, 150))
    )
    calls: list[str] = []

    def local_generate(model, prompt, timeout, schema):
        del prompt, schema
        calls.append(f"local:{model}:{timeout:g}")
        return local_raw

    def openai_generate(model, prompt, timeout, schema):
        del prompt, schema
        calls.append(f"openai:{model}:{timeout:g}")
        return openai_raw

    local_result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request("local", model="hermes3:8b"),
        environ={},
        local_generate=local_generate,
        openai_generate=openai_generate,
    )
    assert local_result.provider == "local"
    assert local_result.model == "hermes3:8b"
    assert calls == ["local:hermes3:8b:999"]

    calls.clear()
    openai_result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request("openai", model="gpt-5.6-luna"),
        environ={},
        local_generate=local_generate,
        openai_generate=openai_generate,
    )
    assert openai_result.provider == "openai"
    assert openai_result.model == "gpt-5.6-luna"
    assert calls == ["openai:gpt-5.6-luna:60"]


def test_local_timeout_is_configurable_without_changing_openai_timeout(
    meal_idea_db,
) -> None:
    protein = _food("Timeout Protein", calories=190, protein=29, carbs=0, fat=7)
    side = _food("Timeout Side", calories=130, protein=3, carbs=28, fat=1)
    local_raw = _raw_ideas(
        _idea("Timeout Plate", (protein.display_name, 100), (side.display_name, 100))
    )
    openai_raw = _raw_openai_ideas(
        _idea("Timeout Plate", (protein.display_name, 100), (side.display_name, 100))
    )
    observed: list[tuple[str, float]] = []

    def capture_local(model, prompt, timeout, schema):
        del model, prompt, schema
        observed.append(("local", timeout))
        return local_raw

    def capture_openai(model, prompt, timeout, schema):
        del model, prompt, schema
        observed.append(("openai", timeout))
        return openai_raw

    meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request("local"),
        environ={"MEAL_IDEAS_LOCAL_TIMEOUT_SECONDS": "321"},
        local_generate=capture_local,
    )
    meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request("openai"),
        environ={"MEAL_IDEAS_LOCAL_TIMEOUT_SECONDS": "321"},
        openai_generate=capture_openai,
    )

    assert observed == [("local", 321.0), ("openai", 60.0)]


def test_selected_provider_failure_never_falls_back(meal_idea_db) -> None:
    calls: list[str] = []

    def failed_local(model, prompt, timeout, schema):
        del model, prompt, timeout, schema
        calls.append("local")
        raise RuntimeError("offline")

    def forbidden_openai(model, prompt, timeout, schema):
        del model, prompt, timeout, schema
        calls.append("openai")
        return "{}"

    with pytest.raises(meal_idea_service.MealIdeaProviderError) as exc_info:
        meal_idea_service.generate_meal_ideas(
            user_id=1,
            target_date="2026-07-21",
            request=_request("local"),
            local_generate=failed_local,
            openai_generate=forbidden_openai,
        )
    assert exc_info.value.code == "local_provider_failed"
    assert calls == ["local"]


def test_unconfigured_openai_does_not_call_local(meal_idea_db) -> None:
    local_called = False

    def forbidden_local(*args):
        nonlocal local_called
        del args
        local_called = True
        return "{}"

    with pytest.raises(meal_idea_service.MealIdeaProviderError) as exc_info:
        meal_idea_service.generate_meal_ideas(
            user_id=1,
            target_date="2026-07-21",
            request=_request("openai"),
            environ={},
            local_generate=forbidden_local,
        )
    assert exc_info.value.code == "openai_not_configured"
    assert local_called is False


def test_never_suggest_is_enforced_after_generation(meal_idea_db) -> None:
    excluded = _food("Excluded Eggplant", calories=25, protein=1, carbs=6, fat=0.2)
    chicken = _food("Safe Chicken", calories=190, protein=29, carbs=0, fat=7)
    rice = _food("Safe Rice", calories=130, protein=3, carbs=28, fat=1)
    set_food_preference(
        user_id=1,
        canonical_food_id=excluded.id,
        preference="never_suggest",
    )
    raw = _raw_ideas(
        _idea("Excluded Plate", (excluded.display_name, 150), (rice.display_name, 100)),
        _idea("Safe Plate", (chicken.display_name, 120), (rice.display_name, 150)),
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )

    assert [idea.name for idea in result.ideas] == [
        "Safe Plate",
        "Safe Plate Variation 3",
    ]
    assert result.rejected_concept_count == 1
    assert all(
        ingredient.canonical_food_id != excluded.id
        for idea in result.ideas
        for ingredient in idea.ingredients
    )


def test_user_signals_are_isolated_and_available_is_only_a_soft_flag(
    meal_idea_db,
) -> None:
    available = _food("User One Pantry Food", calories=100, protein=5, carbs=15, fat=3)
    outside = _food("Outside Pantry Food", calories=220, protein=20, carbs=10, fat=10)
    side = _food("Shared Side Food", calories=80, protein=2, carbs=18, fat=0)
    add_available_ingredient(user_id=1, canonical_food_id=available.id)
    raw = _raw_ideas(
        _idea(
            "Outside Pantry Meal", (outside.display_name, 100), (side.display_name, 100)
        )
    )
    prompts: dict[int, str] = {}

    for user_id in (1, 2):
        result = meal_idea_service.generate_meal_ideas(
            user_id=user_id,
            target_date="2026-07-21",
            request=_request(
                previous_idea_names=("Previous Bowl",),
                recent_generated_food_names=("Recently Generated Rice",),
            ),
            local_generate=lambda model, prompt, timeout, schema, uid=user_id: (
                prompts.__setitem__(uid, prompt) or raw
            ),
        )
        assert len(result.ideas) == 3
        assert result.ideas[0].available_ingredient_count == 0
        assert all(not item.is_available for item in result.ideas[0].ingredients)

    user_one_context = json.loads(prompts[1].split("CONTEXT:\n", 1)[1])
    user_two_context = json.loads(prompts[2].split("CONTEXT:\n", 1)[1])
    assert (
        available.display_name
        in user_one_context["optional_available_convenience"]["foods"]
    )
    assert (
        available.display_name
        not in user_two_context["optional_available_convenience"]["foods"]
    )
    assert (
        "not a candidate pool"
        in user_one_context["optional_available_convenience"]["meaning"]
    )
    assert user_one_context["recent_generated_foods_soft"] == [
        "Recently Generated Rice"
    ]
    assert user_one_context["recent_generated_idea_names_soft"] == ["Previous Bowl"]
    assert "it is normal for an idea to use no Available foods" in prompts[1]


def test_available_changes_do_not_change_the_rotating_catalog_sample(
    meal_idea_db,
    monkeypatch,
) -> None:
    monkeypatch.setattr(meal_idea_service, "MAX_LOCAL_PROMPT_CATALOG_FOODS", 2)
    foods = [
        _food(
            f"Rotating Catalog Food {index}",
            calories=100 + index,
            protein=5,
            carbs=15,
            fat=3,
        )
        for index in range(5)
    ]
    raw = _raw_ideas(
        _idea(
            "Catalog Universe Plate",
            (foods[0].display_name, 100),
            (foods[1].display_name, 100),
        )
    )
    contexts: list[dict] = []

    def generate(model, prompt, timeout, schema):
        del model, timeout, schema
        contexts.append(json.loads(prompt.split("CONTEXT:\n", 1)[1]))
        return raw

    request = _request(generation_nonce="same-catalog-rotation")
    meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=request,
        local_generate=generate,
    )
    add_available_ingredient(user_id=1, canonical_food_id=foods[-1].id)
    meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=request,
        local_generate=generate,
    )

    assert contexts[0]["catalog_food_names"] == contexts[1]["catalog_food_names"]
    assert contexts[0]["optional_available_convenience"]["foods"] == []
    assert contexts[1]["optional_available_convenience"]["foods"] == [
        foods[-1].display_name
    ]


def test_openai_context_keeps_available_and_recent_exposure_soft(
    meal_idea_db,
) -> None:
    available = _food("OpenAI Available Food", calories=95, protein=4, carbs=16, fat=2)
    outside = _food("OpenAI Outside Food", calories=210, protein=24, carbs=8, fat=9)
    side = _food("OpenAI Outside Side", calories=75, protein=2, carbs=16, fat=0.5)
    add_available_ingredient(user_id=1, canonical_food_id=available.id)
    raw = _raw_openai_ideas(
        _idea(
            "OpenAI Outside Plate",
            (outside.display_name, 100),
            (side.display_name, 100),
        )
    )
    captured_prompt = ""

    def generate(model, prompt, timeout, schema):
        nonlocal captured_prompt
        del model, timeout, schema
        captured_prompt = prompt
        return raw

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(
            "openai",
            previous_idea_names=("Recent Bowl",),
            recent_generated_food_names=("Recent Salmon",),
        ),
        environ={},
        openai_generate=generate,
    )

    prompt_context = json.loads(captured_prompt.split("GENERATION_CONTEXT:\n", 1)[1])
    assert prompt_context["optional_available_ingredient_convenience"] == {
        "foods": [available.display_name],
        "meaning": (
            "Optional foods already on hand. This is not a candidate pool, "
            "restriction, or optimization target."
        ),
    }
    assert prompt_context["recent_generated_foods_soft_repetition_signal"] == [
        "Recent Salmon"
    ]
    assert prompt_context["recent_generated_idea_names_soft_repetition_signal"] == [
        "Recent Bowl"
    ]
    assert "remaining_nutrition_context" not in prompt_context
    assert "not Meet My Macros" in captured_prompt
    assert "do not maximize overlap, do not build primarily from it" in captured_prompt
    assert result.ideas[0].available_ingredient_count == 0
    assert all(not item.is_available for item in result.ideas[0].ingredients)


def test_soft_preferences_remain_signals_not_exclusions(meal_idea_db) -> None:
    loved = _food("Loved Lentils", calories=115, protein=9, carbs=20, fat=0.4)
    liked = _food("Liked Tomato", calories=18, protein=1, carbs=4, fat=0.2)
    disliked = _food("Disliked Feta", calories=260, protein=14, carbs=4, fat=21)
    for food, preference in (
        (loved, "love"),
        (liked, "like"),
        (disliked, "dislike"),
    ):
        set_food_preference(
            user_id=1,
            canonical_food_id=food.id,
            preference=preference,
        )
    raw = _raw_ideas(
        _idea(
            "Soft Signal Bowl",
            (loved.display_name, 150),
            (liked.display_name, 100),
            (disliked.display_name, 30),
        )
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(intent="Please use feta"),
        local_generate=lambda *_: raw,
    )

    assert len(result.ideas) == 3
    assert {item.canonical_food_id for item in result.ideas[0].ingredients} == {
        loved.id,
        liked.id,
        disliked.id,
    }


def test_grounded_macros_come_from_catalog_values(meal_idea_db) -> None:
    protein = _food("Grounded Protein", calories=200, protein=30, carbs=10, fat=8)
    produce = _food("Grounded Produce", calories=40, protein=2, carbs=8, fat=0.5)
    raw = _raw_ideas(
        _idea(
            "Grounded Plate", (protein.display_name, 150), (produce.display_name, 200)
        )
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )
    meal = result.ideas[0]

    assert meal.calories == 380
    assert meal.protein_g == 49
    assert meal.carbs_g == 31
    assert meal.fat_g == 13


def test_normal_meal_ideas_do_not_load_or_prompt_with_remaining_macros(
    meal_idea_db,
    monkeypatch,
) -> None:
    protein = _food(
        "Independent Portion Protein", calories=200, protein=30, carbs=0, fat=8
    )
    side = _food("Independent Portion Side", calories=130, protein=3, carbs=28, fat=1)
    raw = _raw_ideas(
        _idea(
            "Independent Portion Plate",
            (protein.display_name, 100),
            (side.display_name, 100),
        )
    )
    captured_prompt = ""

    def forbidden_remaining_context(*_args, **_kwargs):
        raise AssertionError("Normal Meal Ideas must not load macro headroom.")

    def generate(model, prompt, timeout, schema):
        nonlocal captured_prompt
        del model, timeout, schema
        captured_prompt = prompt
        return raw

    monkeypatch.setattr(
        meal_idea_service,
        "_remaining_nutrition_context",
        forbidden_remaining_context,
    )
    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request("local"),
        local_generate=generate,
    )

    prompt_context = json.loads(captured_prompt.split("CONTEXT:\n", 1)[1])
    assert "nutrition" not in prompt_context
    assert "remaining_nutrition_context" not in prompt_context
    assert "not macro-target closure" in captured_prompt
    assert result.context_signals["nutrition_context_available"] is False
    assert result.ideas[0].ingredients[0].amount_grams == 100


def test_microscopic_meal_portions_are_rejected_after_catalog_grounding(
    meal_idea_db,
) -> None:
    protein = _food("Plausibility Protein", calories=200, protein=30, carbs=0, fat=8)
    side = _food("Plausibility Side", calories=130, protein=3, carbs=28, fat=1)
    raw = _raw_ideas(
        _idea("Microscopic Plate", (protein.display_name, 4), (side.display_name, 6)),
        _idea("Normal Plate", (protein.display_name, 120), (side.display_name, 150)),
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )

    assert [idea.name for idea in result.ideas] == [
        "Normal Plate",
        "Normal Plate Variation 3",
    ]
    assert result.rejected_concept_count == 1


def test_microscopic_named_core_ingredients_are_rejected_with_plausible_totals(
    meal_idea_db,
) -> None:
    chicken = _food("Chicken Breast", calories=165, protein=31, carbs=0, fat=3.6)
    pasta = _food("Cooked Pasta", calories=150, protein=5, carbs=30, fat=1)
    sauce = _food("Creamy Tomato Sauce", calories=200, protein=3, carbs=10, fat=16)
    raw = _raw_ideas(
        _idea(
            "Creamy Chicken Pasta",
            (chicken.display_name, 5),
            (pasta.display_name, 6),
            (sauce.display_name, 250),
        ),
        _idea(
            "Normal Chicken Pasta",
            (chicken.display_name, 120),
            (pasta.display_name, 180),
            (sauce.display_name, 40),
        ),
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )

    assert [idea.name for idea in result.ideas] == [
        "Normal Chicken Pasta",
        "Normal Chicken Pasta Variation 3",
    ]
    assert result.rejected_concept_count == 1


def test_small_seasoning_amounts_remain_valid_with_normal_core_portions(
    meal_idea_db,
) -> None:
    chicken = _food("Seasoned Chicken", calories=165, protein=31, carbs=0, fat=3.6)
    pasta = _food("Seasoned Pasta", calories=150, protein=5, carbs=30, fat=1)
    pepper = _food("Black Pepper", calories=250, protein=10, carbs=60, fat=3)
    raw = _raw_ideas(
        _idea(
            "Peppered Chicken Pasta",
            (chicken.display_name, 120),
            (pasta.display_name, 180),
            (pepper.display_name, 1),
        )
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )

    assert result.ideas[0].ingredients[-1].display_name == pepper.display_name
    assert result.ideas[0].ingredients[-1].amount_grams == 1


def test_dense_topping_uses_density_adjusted_floor_instead_of_core_floor(
    meal_idea_db,
) -> None:
    chicken = _food("Salad Chicken", calories=165, protein=31, carbs=0, fat=3.6)
    vegetables = _food(
        "Mixed Salad Vegetables", calories=50, protein=3, carbs=10, fat=0.5
    )
    croutons = _food("Whole Grain Croutons", calories=400, protein=10, carbs=65, fat=10)
    raw = _raw_ideas(
        _idea(
            "Chicken Salad with Crunch",
            (chicken.display_name, 120),
            (vegetables.display_name, 200),
            (croutons.display_name, 12),
        )
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )

    assert result.ideas[0].ingredients[-1].display_name == croutons.display_name
    assert result.ideas[0].ingredients[-1].amount_grams == 12


def test_excessive_single_meal_portions_are_rejected_with_meal_type_bounds(
    meal_idea_db,
) -> None:
    protein = _food("Bounded Protein", calories=220, protein=32, carbs=0, fat=9)
    side = _food("Bounded Side", calories=150, protein=4, carbs=30, fat=1)
    raw = _raw_ideas(
        _idea(
            "Excessive Dinner", (protein.display_name, 700), (side.display_name, 700)
        ),
        _idea("Bounded Dinner", (protein.display_name, 140), (side.display_name, 180)),
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )

    assert [idea.name for idea in result.ideas] == [
        "Bounded Dinner",
        "Bounded Dinner Variation 3",
    ]
    assert result.rejected_concept_count == 1


def test_local_normalization_keeps_valid_concepts_when_one_is_malformed(
    meal_idea_db,
) -> None:
    protein = _food("Normalization Protein", calories=180, protein=28, carbs=2, fat=7)
    side = _food("Normalization Side", calories=90, protein=3, carbs=19, fat=0.5)
    valid = _idea(
        "Valid Local Plate", (protein.display_name, 100), (side.display_name, 100)
    )
    raw_payload = json.loads(_raw_ideas(valid))
    raw_payload["meals"][1]["meal_type"] = "brunch"

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(model="qwen3:8b"),
        local_generate=lambda *_: json.dumps(raw_payload),
    )

    assert len(result.ideas) == 2
    assert result.rejected_concept_count == 1


def test_local_all_candidate_grounding_failure_names_the_stage(meal_idea_db) -> None:
    raw = _raw_ideas(
        _idea("Unknown Plate", ("Invented Protein", 100), ("Invented Side", 100))
    )

    with pytest.raises(meal_idea_service.MealIdeaProviderError) as exc_info:
        meal_idea_service.generate_meal_ideas(
            user_id=1,
            target_date="2026-07-21",
            request=_request(model="qwen3:8b"),
            local_generate=lambda *_: raw,
        )

    assert exc_info.value.code == "local_grounding_rejected"
    assert "unknown_ingredient=3" in exc_info.value.public_message


def test_custom_canonical_food_names_are_used_for_prompt_and_grounding(
    meal_idea_db,
) -> None:
    protein = _food("Original Protein Name", calories=180, protein=28, carbs=2, fat=7)
    side = _food("Custom Name Side", calories=90, protein=3, carbs=19, fat=0.5)
    set_user_canonical_food_name(
        user_id=1,
        canonical_food_id=protein.id,
        display_name="My House Protein",
    )
    raw = _raw_ideas(
        _idea("Custom Name Plate", ("My House Protein", 100), (side.display_name, 100))
    )
    captured_prompt = ""

    def generate(model, prompt, timeout, schema):
        nonlocal captured_prompt
        del model, timeout, schema
        captured_prompt = prompt
        return raw

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=generate,
    )

    assert "My House Protein" in captured_prompt
    assert result.ideas[0].ingredients[0].display_name == "My House Protein"


def test_primary_catalog_identity_wins_over_another_foods_matching_alias(
    meal_idea_db,
) -> None:
    familiar_food = _food(
        "Familiar Catalog Vegetable", calories=60, protein=2, carbs=12, fat=1
    )
    proposed_food = _food(
        "Exact Model Eggplant", calories=25, protein=1, carbs=6, fat=0.2
    )
    side = _food("Identity Side", calories=120, protein=4, carbs=24, fat=1)
    create_canonical_food_alias(
        familiar_food.id,
        proposed_food.display_name,
        priority=1,
    )
    raw = _raw_ideas(
        _idea(
            "Identity Plate",
            (proposed_food.display_name, 150),
            (side.display_name, 100),
        )
    )

    result = meal_idea_service.generate_meal_ideas(
        user_id=1,
        target_date="2026-07-21",
        request=_request(),
        local_generate=lambda *_: raw,
    )

    assert result.ideas[0].ingredients[0].canonical_food_id == proposed_food.id
    assert result.ideas[0].ingredients[0].display_name == proposed_food.display_name


@pytest.mark.parametrize("raw", ["not json", "{}", '{"meals": [{"name": "bad"}]}'])
def test_malformed_provider_responses_are_rejected(meal_idea_db, raw: str) -> None:
    with pytest.raises(meal_idea_service.MealIdeaProviderError) as exc_info:
        meal_idea_service.generate_meal_ideas(
            user_id=1,
            target_date="2026-07-21",
            request=_request(),
            local_generate=lambda *_: raw,
        )
    assert exc_info.value.code == "local_response_malformed"
