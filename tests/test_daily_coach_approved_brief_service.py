from __future__ import annotations

from services.daily_coach_approved_brief_service import (
    build_approved_coach_brief,
    friendly_food_name,
)


def _value_context():
    return {
        "approved_value_claims": [
            {
                "key": "nutrition.protein.status",
                "label": "Protein status",
                "value": "below target",
                "display_allowed": True,
                "source": "target_vs_actual_summary",
            },
            {
                "key": "nutrition.food_suggestion.1.friendly_name",
                "label": "Food option",
                "value": "canned tuna",
                "display_allowed": True,
                "source": "approved_food_suggestions",
            },
            {
                "key": "training.rir_range",
                "label": "RIR range",
                "value": "2-4",
                "display_allowed": True,
                "source": "workout_plan",
            },
            {
                "key": "recovery.readiness_level",
                "label": "Readiness",
                "value": "High",
                "display_allowed": True,
                "source": "recovery_checkin",
            },
            {
                "key": "debug.raw_row",
                "label": "Debug",
                "value": "secret",
                "display_allowed": False,
            },
        ],
        "food_suggestion_copy_context": {
            "suggestions": [
                {
                    "canonical_name": "Tuna, Canned in Water",
                    "friendly_name": "canned tuna",
                    "macro_reason": "protein",
                    "claim_keys": {
                        "friendly_name": "nutrition.food_suggestion.1.friendly_name"
                    },
                }
            ]
        },
        "today_story": {
            "main_tension": "Training is appropriate, but nutrition is lagging.",
            "training_implication": "Do the planned workout without chasing max effort.",
            "recovery_implication": "Recovery looks good enough to train as planned.",
            "desired_coaching_move": "Train clean and handle the protein gap.",
        },
    }


class FakeSynthesis:
    recommended_focus = "Train clean and handle the protein gap."


def test_approved_coach_brief_builds_from_approved_context() -> None:
    brief = build_approved_coach_brief(
        user_id=102,
        target_date="2026-06-05",
        scenario_id="rich_nutrition_training_recovery",
        synthesis=FakeSynthesis(),
        value_context=_value_context(),
    )

    assert brief.brief_id.endswith("102:2026-06-05:rich_nutrition_training_recovery")
    assert brief.addressing_policy.allow_name is False
    assert "nutrition.protein.status" in brief.claim_registry
    assert "debug.raw_row" not in brief.claim_registry
    assert brief.approved_food_actions[0].friendly_name == "canned tuna"
    assert brief.approved_food_actions[0].canonical_name == "Tuna, Canned in Water"
    assert brief.approved_training_actions
    assert brief.approved_recovery_interpretations
    assert "medical claims" in brief.blocked_topics
    assert "food move" in brief.blocked_phrases
    assert "secret" not in str(brief.to_dict()).lower()


def test_friendly_food_name_maps_problematic_labels() -> None:
    assert friendly_food_name("Tuna, Canned in Water") == "canned tuna"
    assert friendly_food_name("Oats, Dry") == "oatmeal"
