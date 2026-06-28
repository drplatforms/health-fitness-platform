from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DailyCoachPromptLabProvider = Literal["deterministic", "direct_ollama", "openai"]


@dataclass(frozen=True)
class DailyCoachPromptLabAddressingPolicy:
    allow_name: bool = False
    preferred_name: str | None = None
    default_reference: str = "the user"
    visible_name_usage: str = "forbidden_unless_explicitly_approved"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachFoodDisplayLanguage:
    canonical_food_id: int | None
    canonical_name: str
    friendly_display_name: str
    natural_action_phrase: str
    macro_gap_phrase: str
    allowed_user_facing_names: tuple[str, ...] = field(default_factory=tuple)
    blocked_user_facing_names: tuple[str, ...] = field(default_factory=tuple)
    serving_phrase: str | None = None
    serving_phrase_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachPromptLabScenario:
    scenario_id: str
    user_id: int
    target_date: str
    purpose: str
    expected_evaluation_focus: tuple[str, ...]
    addressing_policy: DailyCoachPromptLabAddressingPolicy = field(
        default_factory=DailyCoachPromptLabAddressingPolicy
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["addressing_policy"] = self.addressing_policy.to_dict()
        return payload


@dataclass(frozen=True)
class DailyCoachPromptVariant:
    variant_id: str
    label: str
    hypothesis: str
    prompt_changes: tuple[str, ...] = field(default_factory=tuple)
    context_changes: tuple[str, ...] = field(default_factory=tuple)
    safety_boundaries: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachPromptLabRunConfig:
    scenarios: tuple[str, ...]
    variants: tuple[str, ...]
    provider: DailyCoachPromptLabProvider
    model: str | None = None
    allow_live_provider: bool = False
    include_deterministic_baseline: bool = False
    write_scoring_template: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachPromptLabManualScores:
    plainspoken_voice: str = ""
    action_clarity: str = ""
    scenario_specificity: str = ""
    food_naturalness: str = ""
    training_clarity: str = ""
    recovery_clarity: str = ""
    phrase_variety: str = ""
    logic_coherence: str = ""
    grounding: str = ""
    product_readiness: str = ""
    what_worked: str = ""
    what_failed: str = ""
    phrase_to_ban: str = ""
    phrase_to_prefer: str = ""
    food_language_notes: str = ""
    scenario_logic_notes: str = ""
    qa_decision: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachPromptLabSafetySummary:
    parser_status: str = "not_attempted"
    validation_status: str = "not_attempted"
    fallback_used: bool = False
    unsupported_claim_flags: tuple[str, ...] = field(default_factory=tuple)
    rejected_phrase_flags: tuple[str, ...] = field(default_factory=tuple)
    addressing_policy_flags: tuple[str, ...] = field(default_factory=tuple)
    food_label_leakage_flags: tuple[str, ...] = field(default_factory=tuple)
    secret_leakage_detected: bool = False
    raw_output_in_default_artifact: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyCoachPromptLabResult:
    run_id: str
    scenario_id: str
    variant_id: str
    provider: DailyCoachPromptLabProvider
    model: str | None
    skipped: bool
    skip_reason: str | None
    success: bool
    rendered_output: str
    approved_narrative: dict[str, Any] | None
    runtime_metadata: dict[str, Any]
    diagnostics: dict[str, Any]
    safety_summary: DailyCoachPromptLabSafetySummary
    manual_scores: DailyCoachPromptLabManualScores = field(
        default_factory=DailyCoachPromptLabManualScores
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["safety_summary"] = self.safety_summary.to_dict()
        payload["manual_scores"] = self.manual_scores.to_dict()
        return payload


@dataclass(frozen=True)
class DailyCoachPromptLabArtifactRow:
    run_id: str
    scenario_id: str
    variant_id: str
    provider: DailyCoachPromptLabProvider
    model: str | None
    success: bool
    skipped: bool
    skip_reason: str | None
    validation_status: str
    fallback_used: bool
    rejected_phrase_count: int
    addressing_policy_violation: bool
    canonical_food_label_used: bool
    friendly_food_label_available: bool
    friendly_food_label_used: bool
    food_gap_reason_used: bool
    food_condition_used: bool
    manual_scores: DailyCoachPromptLabManualScores = field(
        default_factory=DailyCoachPromptLabManualScores
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["manual_scores"] = self.manual_scores.to_dict()
        return payload
