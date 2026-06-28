from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from services.daily_coach_prompt_lab_service import (
    addressing_policy_flags,
    artifact_row_from_result,
    build_prompt_lab_context_package,
    detect_rejected_plainspoken_phrases,
    food_display_for_canonical_name,
    food_display_language_flags,
    list_daily_coach_prompt_lab_scenarios,
    list_daily_coach_prompt_lab_variants,
    run_daily_coach_prompt_lab_matrix,
)


@dataclass
class FakeNarrative:
    source: str = "deterministic"
    quoted_values_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": "Plain Daily Coach",
            "summary": "You can train as planned today without turning it into a max-effort test.",
            "nutrition_note": "Add canned tuna if you still need more protein.",
            "training_note": "Prioritize clean reps and stop before the set turns into a grind.",
            "recovery_note": "Recovery looks good enough to train as planned.",
            "priority_action": "Do the planned session, log food honestly, and use canned tuna if protein is still short.",
            "confidence": "High",
            "source": self.source,
            "reason_codes": ["unit_test"],
            "limitations": [],
            "quoted_values_used": list(self.quoted_values_used),
        }


@dataclass
class FakeMetadata:
    provider: str = "deterministic"
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured_provider": self.provider,
            "selected_provider": self.provider,
            "configured_model": self.model,
            "selected_model": self.model,
            "provider_attempted": self.provider != "deterministic",
            "fallback_used": False,
            "fallback_reason": None,
            "candidate_parse_status": (
                "success" if self.provider != "deterministic" else "not_attempted"
            ),
            "candidate_validation_status": (
                "success" if self.provider != "deterministic" else "not_attempted"
            ),
            "validation_status": (
                "approved" if self.provider != "deterministic" else "not_attempted"
            ),
            "final_narrative_source": self.provider,
        }


class FakeResult:
    def __init__(self, provider: str, model: str | None) -> None:
        self.narrative = FakeNarrative(
            source=provider,
            quoted_values_used=[
                "recovery.readiness_level",
                "recovery.fatigue_risk",
                "nutrition.protein.status",
                "nutrition.food_suggestion.1.friendly_name",
            ],
        )
        self.metadata = FakeMetadata(provider=provider, model=model)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "success": True,
            "approved_daily_coach_narrative": self.narrative.to_dict(),
            "rendered_narrative": "\n".join(
                [
                    "Plain Daily Coach",
                    "Add canned tuna if you still need more protein.",
                    "Prioritize clean reps and stop before the set turns into a grind.",
                ]
            ),
        }

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            **self.to_public_dict(),
            "runtime_metadata": self.metadata.to_dict(),
            "provider_context_summary": {},
        }


def fake_builder(
    scenario, variant, provider: str, model: str | None, env: Mapping[str, str]
):
    assert scenario.scenario_id
    assert variant.variant_id
    assert env
    return FakeResult(provider=provider, model=model)


def test_prompt_lab_required_scenarios_and_variants_exist() -> None:
    scenario_ids = {
        scenario.scenario_id for scenario in list_daily_coach_prompt_lab_scenarios()
    }
    variant_ids = {
        variant.variant_id for variant in list_daily_coach_prompt_lab_variants()
    }

    assert {
        "rich_nutrition_training_recovery",
        "stable_comparison",
        "training_present_nutrition_missing",
        "nutrition_present_training_missing",
    } <= scenario_ids
    assert {
        "current_v5_baseline",
        "minimal_examples",
        "plainspoken_fewer_bans",
        "food_action_focused",
        "first_person_logging_guidance",
        "higher_variation_same_validator",
        "friendly_food_labels_only",
        "canonical_vs_user_facing_food_separation",
    } <= variant_ids


def test_prompt_lab_addressing_policy_defaults_to_no_name_usage() -> None:
    scenario = list_daily_coach_prompt_lab_scenarios()[0]

    assert scenario.addressing_policy.allow_name is False
    assert scenario.addressing_policy.preferred_name is None
    assert addressing_policy_flags(
        "Dustin, train today.", scenario.addressing_policy
    ) == ["name_used:Dustin"]
    assert (
        addressing_policy_flags("Train as planned today.", scenario.addressing_policy)
        == []
    )


def test_prompt_lab_food_display_language_maps_problematic_labels() -> None:
    assert (
        food_display_for_canonical_name("Oats, Dry").friendly_display_name == "oatmeal"
    )  # type: ignore[union-attr]
    assert (
        food_display_for_canonical_name("Tuna, Canned in Water").friendly_display_name
        == "canned tuna"
    )  # type: ignore[union-attr]
    assert (
        food_display_for_canonical_name("White Rice, Cooked").friendly_display_name
        == "rice"
    )  # type: ignore[union-attr]
    assert (
        food_display_for_canonical_name(
            "Chicken Breast, Cooked, Skinless"
        ).friendly_display_name
        == "chicken breast"
    )  # type: ignore[union-attr]
    assert (
        food_display_for_canonical_name("Greek Yogurt, Plain").friendly_display_name
        == "Greek yogurt"
    )  # type: ignore[union-attr]

    assert food_display_language_flags("Add Tuna, Canned in Water today.") == [
        "canonical_food_label_visible:Tuna, Canned in Water"
    ]


def test_prompt_lab_rejected_phrase_detection_catches_v5_failures() -> None:
    hits = detect_rejected_plainspoken_phrases(
        "The win is clean work plus one food move if it fits your meals."
    )

    assert "the win is" in hits
    assert "clean work" in hits
    assert "food move" in hits
    assert "if it fits your meals" in hits


def test_prompt_lab_context_package_is_sanitized_and_contains_required_layers() -> None:
    scenario = list_daily_coach_prompt_lab_scenarios()[0]
    variant = list_daily_coach_prompt_lab_variants()[0]
    package = build_prompt_lab_context_package(scenario, variant)

    assert package["lab"] == "daily_coach_prompt_lab_voice_lab_v1"
    assert package["addressing_policy"]["allow_name"] is False
    assert package["variant"]["variant_id"] == "current_v5_baseline"
    assert package["food_display_language"]
    assert "secret" not in str(package).lower()
    assert "api_key" not in str(package).lower()


def test_prompt_lab_deterministic_matrix_writes_sanitized_artifacts(
    tmp_path: Path,
) -> None:
    rows = run_daily_coach_prompt_lab_matrix(
        scenarios=["rich_nutrition_training_recovery"],
        variants=["current_v5_baseline", "food_action_focused"],
        provider="deterministic",
        output_dir=tmp_path,
        narrative_builder=fake_builder,
        environ={"PATH": "test"},
    )

    assert len(rows) == 2
    assert all(row.success for row in rows)
    assert all(not row.skipped for row in rows)
    assert (tmp_path / "prompt_variant_summary.md").exists()
    assert (tmp_path / "scenario_matrix_summary.md").exists()
    assert (tmp_path / "selected_outputs_by_variant.md").exists()
    assert (tmp_path / "scoring_template.md").exists()
    assert (tmp_path / "comparison_table.csv").exists()
    assert (tmp_path / "comparison_table.md").exists()
    assert (tmp_path / "validation_summary.md").exists()
    assert (tmp_path / "run_config.json").exists()
    combined = "\n".join(
        path.read_text() for path in tmp_path.iterdir() if path.is_file()
    )
    assert "raw_provider_output" not in combined
    assert "bearer " not in combined.lower()
    assert "api_key" not in combined.lower()


def test_prompt_lab_live_provider_skips_without_explicit_allow(tmp_path: Path) -> None:
    rows = run_daily_coach_prompt_lab_matrix(
        scenarios=["stable_comparison"],
        variants=["current_v5_baseline"],
        provider="openai",
        model="gpt-5.5",
        output_dir=tmp_path,
        allow_live_provider=False,
        narrative_builder=fake_builder,
        environ={},
    )

    assert rows[0].skipped is True
    assert rows[0].skip_reason == "live_provider_not_allowed"


def test_prompt_lab_openai_missing_key_records_safe_skip(tmp_path: Path) -> None:
    rows = run_daily_coach_prompt_lab_matrix(
        scenarios=["stable_comparison"],
        variants=["current_v5_baseline"],
        provider="openai",
        model="gpt-5.5",
        output_dir=tmp_path,
        allow_live_provider=True,
        narrative_builder=fake_builder,
        environ={},
    )

    assert rows[0].skipped is True
    assert rows[0].skip_reason == "missing_api_key"


def test_prompt_lab_artifact_row_records_diagnostics(tmp_path: Path) -> None:
    rows = run_daily_coach_prompt_lab_matrix(
        scenarios=["rich_nutrition_training_recovery"],
        variants=["current_v5_baseline"],
        provider="deterministic",
        output_dir=tmp_path,
        narrative_builder=fake_builder,
        environ={"PATH": "test"},
    )

    artifact_row = artifact_row_from_result(rows[0])

    assert artifact_row.scenario_id == "rich_nutrition_training_recovery"
    assert artifact_row.variant_id == "current_v5_baseline"
    assert artifact_row.friendly_food_label_available is True
    assert artifact_row.friendly_food_label_used is True
    assert artifact_row.food_gap_reason_used is True
    assert artifact_row.food_condition_used is True


def test_prompt_lab_value_prompt_context_package_does_not_require_dustin() -> None:
    from services.daily_coach_value_narrative_service import (
        build_daily_coach_value_narrative_prompt,
    )

    class FakeSynthesis:
        confidence = "High"

    scenario = list_daily_coach_prompt_lab_scenarios()[0]
    variant = list_daily_coach_prompt_lab_variants()[0]
    prompt = build_daily_coach_value_narrative_prompt(
        FakeSynthesis(),
        value_context={
            "daily_coach_synthesis": {},
            "approved_recovery": {},
            "approved_nutrition": {},
            "approved_training": {},
            "approved_limitations": [],
            "approved_reason_codes": [],
            "approved_value_claims": [],
            "prompt_lab": build_prompt_lab_context_package(scenario, variant),
            "addressing_policy": scenario.addressing_policy.to_dict(),
            "food_display_language": [],
        },
    )

    assert "talking to Dustin" not in prompt
    assert "ADDRESSING_POLICY" in prompt
    assert "PROMPT_LAB_CONTEXT_PACKAGE_DEVELOPER_ONLY" in prompt
