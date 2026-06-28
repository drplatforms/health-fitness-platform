from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.daily_coach_prompt_lab_models import (
    DailyCoachFoodDisplayLanguage,
    DailyCoachPromptLabAddressingPolicy,
    DailyCoachPromptLabArtifactRow,
    DailyCoachPromptLabResult,
    DailyCoachPromptLabRunConfig,
    DailyCoachPromptLabSafetySummary,
    DailyCoachPromptLabScenario,
    DailyCoachPromptVariant,
)
from services.daily_coach_synthesis_service import build_daily_coach_synthesis
from services.daily_coach_value_narrative_service import (
    DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV,
    DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV,
    OLLAMA_BASE_URL_ENV,
    OPENAI_API_KEY_ENV,
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    build_daily_coach_value_aware_provider_context,
    build_daily_coach_value_narrative_from_synthesis,
)
from services.user_state_service import build_user_health_state

SUPPORTED_LAB_PROVIDERS = {
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
}
DEFAULT_OUTPUT_DIR = "docs/provider_trials/daily_coach_prompt_lab_voice_lab_v1"
SECRET_PATTERNS = ("bearer ", "openai_api_key", "api key", "sk-")

_REJECTED_VISIBLE_PHRASES = (
    "food move",
    "clean work",
    "make clean reps the win",
    "the win is",
    "useful move",
    "main lever",
    "support the work",
    "support the day",
    "nutrition support",
    "effort anchor",
    "planned effort range",
    "bigger nutrition overhaul",
    "rebuilding the whole plan",
    "if it fits your meals",
    "if it fits your day",
    "protein bump",
    "easy protein bump",
    "markers remain stable",
    "maintain the current direction",
    "progress gradually",
    "fatigue does not require backing off today",
    "tuna, canned in water",
)

_FOOD_DISPLAY_FIXTURES: tuple[DailyCoachFoodDisplayLanguage, ...] = (
    DailyCoachFoodDisplayLanguage(
        canonical_food_id=None,
        canonical_name="Oats, Dry",
        friendly_display_name="oatmeal",
        natural_action_phrase="have oatmeal",
        macro_gap_phrase="if you still need more calories",
        allowed_user_facing_names=("oatmeal",),
        blocked_user_facing_names=("Oats, Dry",),
    ),
    DailyCoachFoodDisplayLanguage(
        canonical_food_id=None,
        canonical_name="Tuna, Canned in Water",
        friendly_display_name="canned tuna",
        natural_action_phrase="add canned tuna",
        macro_gap_phrase="if you still need more protein",
        allowed_user_facing_names=("canned tuna",),
        blocked_user_facing_names=("Tuna, Canned in Water",),
    ),
    DailyCoachFoodDisplayLanguage(
        canonical_food_id=None,
        canonical_name="White Rice, Cooked",
        friendly_display_name="rice",
        natural_action_phrase="add rice",
        macro_gap_phrase="if you still need more calories",
        allowed_user_facing_names=("rice", "cooked rice"),
        blocked_user_facing_names=("White Rice, Cooked",),
    ),
    DailyCoachFoodDisplayLanguage(
        canonical_food_id=None,
        canonical_name="Chicken Breast, Cooked, Skinless",
        friendly_display_name="chicken breast",
        natural_action_phrase="add chicken breast",
        macro_gap_phrase="if you still need more protein",
        allowed_user_facing_names=("chicken breast",),
        blocked_user_facing_names=("Chicken Breast, Cooked, Skinless",),
    ),
    DailyCoachFoodDisplayLanguage(
        canonical_food_id=None,
        canonical_name="Greek Yogurt, Plain",
        friendly_display_name="Greek yogurt",
        natural_action_phrase="add Greek yogurt",
        macro_gap_phrase="if you still need more protein",
        allowed_user_facing_names=("Greek yogurt",),
        blocked_user_facing_names=("Greek Yogurt, Plain",),
    ),
)

PromptLabBuilder = Callable[
    [
        DailyCoachPromptLabScenario,
        DailyCoachPromptVariant,
        str,
        str | None,
        Mapping[str, str],
    ],
    Any,
]


def list_daily_coach_prompt_lab_scenarios() -> list[DailyCoachPromptLabScenario]:
    return list(_SCENARIOS)


def get_daily_coach_prompt_lab_scenario(
    scenario_id: str,
) -> DailyCoachPromptLabScenario:
    for scenario in _SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    valid = ", ".join(sorted(scenario.scenario_id for scenario in _SCENARIOS))
    raise ValueError(
        f"Unknown Daily Coach Prompt Lab scenario: {scenario_id}. Valid: {valid}"
    )


def list_daily_coach_prompt_lab_variants() -> list[DailyCoachPromptVariant]:
    return list(_VARIANTS)


def get_daily_coach_prompt_lab_variant(variant_id: str) -> DailyCoachPromptVariant:
    for variant in _VARIANTS:
        if variant.variant_id == variant_id:
            return variant
    valid = ", ".join(sorted(variant.variant_id for variant in _VARIANTS))
    raise ValueError(
        f"Unknown Daily Coach Prompt Lab variant: {variant_id}. Valid: {valid}"
    )


def list_food_display_language_fixtures() -> list[DailyCoachFoodDisplayLanguage]:
    return list(_FOOD_DISPLAY_FIXTURES)


def food_display_for_canonical_name(
    canonical_name: str,
) -> DailyCoachFoodDisplayLanguage | None:
    normalized = canonical_name.strip().lower()
    for fixture in _FOOD_DISPLAY_FIXTURES:
        if fixture.canonical_name.lower() == normalized:
            return fixture
    return None


def build_prompt_lab_context_package(
    scenario: DailyCoachPromptLabScenario,
    variant: DailyCoachPromptVariant,
) -> dict[str, Any]:
    """Build sanitized developer-only Prompt Lab instructions for value context injection."""

    return {
        "lab": "daily_coach_prompt_lab_voice_lab_v1",
        "scenario": scenario.to_dict(),
        "variant": variant.to_dict(),
        "addressing_policy": scenario.addressing_policy.to_dict(),
        "food_display_language": [
            fixture.to_dict() for fixture in _FOOD_DISPLAY_FIXTURES
        ],
        "plainspoken_instruction": "Say the actual action. Do not package it as a slogan.",
        "safety_boundaries": [
            "Use approved facts only.",
            "Every concrete value/status/food/range must be quote-backed.",
            "Do not invent serving sizes, timing, pairings, or meal plans.",
            "Do not use a personal name unless addressing_policy.allow_name is true.",
            "Do not use canonical food labels when a friendly display name exists.",
        ],
    }


def detect_rejected_plainspoken_phrases(text: str) -> list[str]:
    normalized = _normalize_text(text)
    return [phrase for phrase in _REJECTED_VISIBLE_PHRASES if phrase in normalized]


def addressing_policy_flags(
    text: str,
    policy: DailyCoachPromptLabAddressingPolicy,
) -> list[str]:
    flags: list[str] = []
    if not policy.allow_name and "dustin" in _normalize_text(text):
        flags.append("name_used:Dustin")
    if policy.allow_name and policy.preferred_name:
        return flags
    return flags


def food_display_language_flags(text: str) -> list[str]:
    flags: list[str] = []
    normalized = _normalize_text(text)
    for fixture in _FOOD_DISPLAY_FIXTURES:
        for blocked in fixture.blocked_user_facing_names:
            if blocked.lower() in normalized:
                flags.append(f"canonical_food_label_visible:{blocked}")
    return flags


def run_daily_coach_prompt_lab_matrix(
    *,
    scenarios: Sequence[str],
    variants: Sequence[str],
    provider: str,
    output_dir: Path,
    model: str | None = None,
    allow_live_provider: bool = False,
    include_deterministic_baseline: bool = False,
    write_scoring_template: bool = True,
    environ: Mapping[str, str] | None = None,
    narrative_builder: PromptLabBuilder | None = None,
) -> list[DailyCoachPromptLabResult]:
    env = dict(os.environ if environ is None else environ)
    resolved_provider = _normalize_provider(provider)
    if resolved_provider not in SUPPORTED_LAB_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    run_id = _build_run_id(resolved_provider)
    selected_scenarios = [
        get_daily_coach_prompt_lab_scenario(item) for item in scenarios
    ]
    selected_variants = [get_daily_coach_prompt_lab_variant(item) for item in variants]
    providers = [resolved_provider]
    if include_deterministic_baseline and resolved_provider != PROVIDER_DETERMINISTIC:
        providers.insert(0, PROVIDER_DETERMINISTIC)

    results: list[DailyCoachPromptLabResult] = []
    builder = narrative_builder or _run_existing_daily_coach_provider_path
    for scenario in selected_scenarios:
        for variant in selected_variants:
            for provider_name in providers:
                results.append(
                    _run_lab_case(
                        run_id=run_id,
                        scenario=scenario,
                        variant=variant,
                        provider=provider_name,
                        model=(
                            None if provider_name == PROVIDER_DETERMINISTIC else model
                        ),
                        allow_live_provider=allow_live_provider,
                        environ=env,
                        narrative_builder=builder,
                    )
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_artifacts(
        output_dir,
        run_id=run_id,
        config=DailyCoachPromptLabRunConfig(
            scenarios=tuple(scenarios),
            variants=tuple(variants),
            provider=resolved_provider,  # type: ignore[arg-type]
            model=model,
            allow_live_provider=allow_live_provider,
            include_deterministic_baseline=include_deterministic_baseline,
            write_scoring_template=write_scoring_template,
        ),
        scenarios=selected_scenarios,
        variants=selected_variants,
        results=results,
        write_scoring_template=write_scoring_template,
    )
    return results


def _run_lab_case(
    *,
    run_id: str,
    scenario: DailyCoachPromptLabScenario,
    variant: DailyCoachPromptVariant,
    provider: str,
    model: str | None,
    allow_live_provider: bool,
    environ: Mapping[str, str],
    narrative_builder: PromptLabBuilder,
) -> DailyCoachPromptLabResult:
    skip_reason = _provider_skip_reason(
        provider, allow_live_provider=allow_live_provider, env=environ
    )
    if skip_reason:
        return _skipped_result(run_id, scenario, variant, provider, model, skip_reason)

    env = dict(environ)
    env[DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV] = provider
    if model:
        env[DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV] = model

    try:
        provider_result = narrative_builder(scenario, variant, provider, model, env)
    except Exception as exc:  # noqa: BLE001 - lab rows should record failures, not crash matrix
        return _skipped_result(
            run_id,
            scenario,
            variant,
            provider,
            model,
            f"case_unavailable_or_builder_error:{_safe_error(exc)}",
        )

    public_payload = provider_result.to_public_dict()
    debug_payload = provider_result.to_debug_dict()
    approved = public_payload.get("approved_daily_coach_narrative")
    rendered = public_payload.get("rendered_narrative") or _render_approved(approved)
    runtime_metadata = _sanitize_mapping(debug_payload.get("runtime_metadata") or {})
    diagnostics = _diagnostics_for_output(rendered, approved, scenario)
    safety = DailyCoachPromptLabSafetySummary(
        parser_status=str(
            runtime_metadata.get("candidate_parse_status") or "not_attempted"
        ),
        validation_status=str(
            runtime_metadata.get("validation_status") or "not_attempted"
        ),
        fallback_used=bool(runtime_metadata.get("fallback_used")),
        unsupported_claim_flags=tuple(
            _safe_list(runtime_metadata.get("unsupported_claim_flags"))
        ),
        rejected_phrase_flags=tuple(diagnostics["rejected_phrase_flags"]),
        addressing_policy_flags=tuple(diagnostics["addressing_policy_flags"]),
        food_label_leakage_flags=tuple(diagnostics["food_label_leakage_flags"]),
        secret_leakage_detected=_contains_secretish_text(
            json.dumps(public_payload, default=str)
        ),
        raw_output_in_default_artifact="raw_provider_output" in public_payload,
    )
    result = DailyCoachPromptLabResult(
        run_id=run_id,
        scenario_id=scenario.scenario_id,
        variant_id=variant.variant_id,
        provider=provider,  # type: ignore[arg-type]
        model=str(runtime_metadata.get("selected_model") or model or "") or None,
        skipped=False,
        skip_reason=None,
        success=bool(public_payload.get("success")),
        rendered_output=str(rendered or ""),
        approved_narrative=approved if isinstance(approved, dict) else None,
        runtime_metadata=runtime_metadata,
        diagnostics=diagnostics,
        safety_summary=safety,
    )
    _assert_result_sanitized(result)
    return result


def _run_existing_daily_coach_provider_path(
    scenario: DailyCoachPromptLabScenario,
    variant: DailyCoachPromptVariant,
    provider: str,
    model: str | None,
    env: Mapping[str, str],
) -> Any:
    synthesis = build_daily_coach_synthesis(scenario.user_id)
    health_state = build_user_health_state(scenario.user_id)
    value_context = build_daily_coach_value_aware_provider_context(
        user_id=scenario.user_id,
        narrative_date=scenario.target_date,
        synthesis=synthesis,
        health_state=health_state,
    )
    value_context["prompt_lab"] = build_prompt_lab_context_package(scenario, variant)
    value_context["addressing_policy"] = scenario.addressing_policy.to_dict()
    value_context["food_display_language"] = [
        fixture.to_dict() for fixture in _FOOD_DISPLAY_FIXTURES
    ]
    return build_daily_coach_value_narrative_from_synthesis(
        synthesis,
        value_context=value_context,
        environ=env,
    )


def _write_artifacts(
    output_dir: Path,
    *,
    run_id: str,
    config: DailyCoachPromptLabRunConfig,
    scenarios: Sequence[DailyCoachPromptLabScenario],
    variants: Sequence[DailyCoachPromptVariant],
    results: Sequence[DailyCoachPromptLabResult],
    write_scoring_template: bool,
) -> None:
    (output_dir / "run_config.json").write_text(
        json.dumps(config.to_dict() | {"run_id": run_id}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "prompt_variant_summary.md").write_text(
        _render_variant_summary(variants), encoding="utf-8"
    )
    (output_dir / "scenario_matrix_summary.md").write_text(
        _render_scenario_summary(scenarios), encoding="utf-8"
    )
    (output_dir / "selected_outputs_by_variant.md").write_text(
        _render_selected_outputs(results), encoding="utf-8"
    )
    (output_dir / "validation_summary.md").write_text(
        _render_validation_summary(results), encoding="utf-8"
    )
    _write_comparison_csv(output_dir / "comparison_table.csv", results)
    (output_dir / "comparison_table.md").write_text(
        _render_comparison_markdown(results), encoding="utf-8"
    )
    if write_scoring_template:
        (output_dir / "scoring_template.md").write_text(
            _render_scoring_template(results), encoding="utf-8"
        )

    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output_dir.iterdir()
        if path.is_file()
    )
    if _contains_secretish_text(serialized):
        raise ValueError("Prompt Lab artifacts contain secret-like text.")
    if "raw_provider_output" in serialized:
        raise ValueError("Prompt Lab default artifacts contain raw provider output.")


def artifact_row_from_result(
    result: DailyCoachPromptLabResult,
) -> DailyCoachPromptLabArtifactRow:
    diagnostics = result.diagnostics
    return DailyCoachPromptLabArtifactRow(
        run_id=result.run_id,
        scenario_id=result.scenario_id,
        variant_id=result.variant_id,
        provider=result.provider,
        model=result.model,
        success=result.success,
        skipped=result.skipped,
        skip_reason=result.skip_reason,
        validation_status=result.safety_summary.validation_status,
        fallback_used=result.safety_summary.fallback_used,
        rejected_phrase_count=len(result.safety_summary.rejected_phrase_flags),
        addressing_policy_violation=bool(result.safety_summary.addressing_policy_flags),
        canonical_food_label_used=bool(result.safety_summary.food_label_leakage_flags),
        friendly_food_label_available=bool(_FOOD_DISPLAY_FIXTURES),
        friendly_food_label_used=bool(diagnostics.get("friendly_food_label_used")),
        food_gap_reason_used=bool(diagnostics.get("food_gap_reason_used")),
        food_condition_used=bool(diagnostics.get("food_condition_used")),
    )


def _diagnostics_for_output(
    rendered: str,
    approved: Any,
    scenario: DailyCoachPromptLabScenario,
) -> dict[str, Any]:
    approved_text = json.dumps(approved or {}, default=str)
    visible_text = f"{rendered}\n{approved_text}"
    rejected = detect_rejected_plainspoken_phrases(visible_text)
    addressing = addressing_policy_flags(visible_text, scenario.addressing_policy)
    food_flags = food_display_language_flags(visible_text)
    normalized = _normalize_text(visible_text)
    return {
        "plainspoken_phrase_flags": rejected,
        "rejected_phrase_flags": rejected,
        "rejected_phrase_count": len(rejected),
        "addressing_policy_flags": addressing,
        "addressing_policy_violation": bool(addressing),
        "name_used": "dustin" in normalized,
        "name_allowed": scenario.addressing_policy.allow_name,
        "food_label_leakage_flags": food_flags,
        "canonical_food_label_used": bool(food_flags),
        "friendly_food_label_available": bool(_FOOD_DISPLAY_FIXTURES),
        "friendly_food_label_used": any(
            allowed.lower() in normalized
            for fixture in _FOOD_DISPLAY_FIXTURES
            for allowed in fixture.allowed_user_facing_names
        ),
        "food_gap_reason_used": any(
            phrase in normalized
            for phrase in ["protein", "calories", "gap", "below target", "still short"]
        ),
        "food_condition_used": any(
            phrase in normalized
            for phrase in [
                "if you still need",
                "if protein",
                "if the gap",
                "still short",
            ]
        ),
        "slogan_like_phrase_flags": [
            phrase
            for phrase in ["the win is", "make clean reps the win", "clean work"]
            if phrase in normalized
        ],
        "manual_plainspoken_score": "",
        "manual_product_voice_score": "",
        "manual_food_action_score": "",
    }


def _skipped_result(
    run_id: str,
    scenario: DailyCoachPromptLabScenario,
    variant: DailyCoachPromptVariant,
    provider: str,
    model: str | None,
    skip_reason: str,
) -> DailyCoachPromptLabResult:
    safety = DailyCoachPromptLabSafetySummary()
    return DailyCoachPromptLabResult(
        run_id=run_id,
        scenario_id=scenario.scenario_id,
        variant_id=variant.variant_id,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        skipped=True,
        skip_reason=skip_reason,
        success=False,
        rendered_output="",
        approved_narrative=None,
        runtime_metadata={},
        diagnostics={"skip_reason": skip_reason},
        safety_summary=safety,
    )


def _render_variant_summary(variants: Sequence[DailyCoachPromptVariant]) -> str:
    lines = ["# Daily Coach Prompt Lab Variant Summary", ""]
    for variant in variants:
        lines.extend(
            [
                f"## {variant.variant_id}",
                f"Label: {variant.label}",
                f"Hypothesis: {variant.hypothesis}",
                "Prompt changes:",
            ]
        )
        lines.extend(f"- {item}" for item in variant.prompt_changes)
        lines.append("Context changes:")
        lines.extend(f"- {item}" for item in variant.context_changes)
        lines.append("Safety boundaries:")
        lines.extend(f"- {item}" for item in variant.safety_boundaries)
        lines.append("")
    return "\n".join(lines)


def _render_scenario_summary(scenarios: Sequence[DailyCoachPromptLabScenario]) -> str:
    lines = [
        "# Daily Coach Prompt Lab Scenario Matrix",
        "",
        "| Scenario | User | Date | Purpose | Focus |",
        "|---|---:|---|---|---|",
    ]
    for scenario in scenarios:
        focus = "; ".join(scenario.expected_evaluation_focus)
        lines.append(
            f"| {scenario.scenario_id} | {scenario.user_id} | {scenario.target_date} | {scenario.purpose} | {focus} |"
        )
    return "\n".join(lines) + "\n"


def _render_selected_outputs(results: Sequence[DailyCoachPromptLabResult]) -> str:
    lines = [
        "# Selected Outputs by Variant",
        "",
        "Raw provider output is not included in this default artifact.",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## {result.scenario_id} / {result.variant_id} / {result.provider}",
                f"Skipped: {result.skipped}",
                f"Success: {result.success}",
                f"Fallback used: {result.safety_summary.fallback_used}",
                f"Validation: {result.safety_summary.validation_status}",
                f"Rejected phrases: {', '.join(result.safety_summary.rejected_phrase_flags) or 'none'}",
                f"Addressing flags: {', '.join(result.safety_summary.addressing_policy_flags) or 'none'}",
                f"Food label flags: {', '.join(result.safety_summary.food_label_leakage_flags) or 'none'}",
                "",
                result.rendered_output or "(no rendered output)",
                "",
            ]
        )
    return "\n".join(lines)


def _render_validation_summary(results: Sequence[DailyCoachPromptLabResult]) -> str:
    lines = [
        "# Prompt Lab Validation Summary",
        "",
        "| Scenario | Variant | Provider | Skipped | Validation | Fallback | Rejected | Addressing | Food label |",
        "|---|---|---|---:|---|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            "| "
            f"{result.scenario_id} | {result.variant_id} | {result.provider} | "
            f"{result.skipped} | {result.safety_summary.validation_status} | "
            f"{result.safety_summary.fallback_used} | {len(result.safety_summary.rejected_phrase_flags)} | "
            f"{bool(result.safety_summary.addressing_policy_flags)} | "
            f"{bool(result.safety_summary.food_label_leakage_flags)} |"
        )
    return "\n".join(lines) + "\n"


def _write_comparison_csv(
    path: Path, results: Sequence[DailyCoachPromptLabResult]
) -> None:
    rows = [artifact_row_from_result(result).to_dict() for result in results]
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_comparison_markdown(results: Sequence[DailyCoachPromptLabResult]) -> str:
    lines = [
        "# Prompt Lab Comparison Table",
        "",
        "| Scenario | Variant | Provider | Success | Skipped | Validation | Rejected | Name flag | Food flag |",
        "|---|---|---|---:|---:|---|---:|---:|---:|",
    ]
    for result in results:
        row = artifact_row_from_result(result)
        lines.append(
            f"| {row.scenario_id} | {row.variant_id} | {row.provider} | {row.success} | {row.skipped} | {row.validation_status} | {row.rejected_phrase_count} | {row.addressing_policy_violation} | {row.canonical_food_label_used} |"
        )
    return "\n".join(lines) + "\n"


def _render_scoring_template(results: Sequence[DailyCoachPromptLabResult]) -> str:
    lines = [
        "# Daily Coach Prompt Lab Scoring Template",
        "",
        "Score each dimension 1-5. Grounding must be 5 for product acceptance.",
        "",
        "| Scenario | Variant | Provider | Plainspoken voice | Action clarity | Scenario specificity | Food naturalness | Training clarity | Recovery clarity | Phrase variety | Logic coherence | Grounding | Product readiness | Notes |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.scenario_id} | {result.variant_id} | {result.provider} |  |  |  |  |  |  |  |  |  |  |  |"
        )
    return "\n".join(lines) + "\n"


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower()


def _provider_skip_reason(
    provider: str, *, allow_live_provider: bool, env: Mapping[str, str]
) -> str | None:
    if provider == PROVIDER_DETERMINISTIC:
        return None
    if not allow_live_provider:
        return "live_provider_not_allowed"
    if provider == PROVIDER_OPENAI and not env.get(OPENAI_API_KEY_ENV):
        return "missing_api_key"
    if provider == PROVIDER_DIRECT_OLLAMA and not env.get(OLLAMA_BASE_URL_ENV):
        return "missing_OLLAMA_BASE_URL"
    return None


def _build_run_id(provider: str) -> str:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    return f"daily_coach_prompt_lab_voice_lab_v1_{provider}_{timestamp.replace(':', '').replace('+', 'z')}"


def _render_approved(approved: Any) -> str:
    if not isinstance(approved, dict):
        return ""
    fields = [
        "headline",
        "summary",
        "nutrition_note",
        "training_note",
        "recovery_note",
        "priority_action",
    ]
    return "\n".join(
        str(approved.get(field) or "") for field in fields if approved.get(field)
    )


def _safe_error(exc: Exception) -> str:
    message = str(exc).replace("\n", " ")[:240]
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", message)


def _sanitize_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key)
        if "raw" in key_text.lower():
            continue
        if "secret" in key_text.lower() or "api_key" in key_text.lower():
            continue
        sanitized[key_text] = value
    return sanitized


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _contains_secretish_text(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in SECRET_PATTERNS)


def _assert_result_sanitized(result: DailyCoachPromptLabResult) -> None:
    serialized = json.dumps(result.to_dict(), default=str).lower()
    if "raw_provider_output" in serialized:
        raise ValueError("Prompt Lab result contains raw provider output.")
    if _contains_secretish_text(serialized):
        raise ValueError("Prompt Lab result contains secret-like text.")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


_SCENARIOS: tuple[DailyCoachPromptLabScenario, ...] = (
    DailyCoachPromptLabScenario(
        scenario_id="rich_nutrition_training_recovery",
        user_id=102,
        target_date="2026-06-05",
        purpose="Rich context with food/action/training/recovery synthesis.",
        expected_evaluation_focus=(
            "food language",
            "training clarity",
            "recovery implication",
            "action clarity",
            "product voice",
        ),
    ),
    DailyCoachPromptLabScenario(
        scenario_id="stable_comparison",
        user_id=102,
        target_date="2026-06-27",
        purpose="Stable comparison case for regression across prompt iterations.",
        expected_evaluation_focus=(
            "avoid over-intervention",
            "plainspoken coaching",
            "useful but calm direction",
        ),
    ),
    DailyCoachPromptLabScenario(
        scenario_id="training_present_nutrition_missing",
        user_id=102,
        target_date="2026-06-03",
        purpose="Training logged, nutrition missing.",
        expected_evaluation_focus=(
            "avoid fake fueling claims",
            "ask for food logging naturally",
            "do not invent nutrition gaps",
            "do not sound scolding",
        ),
    ),
    DailyCoachPromptLabScenario(
        scenario_id="nutrition_present_training_missing",
        user_id=102,
        target_date="2026-06-06",
        purpose="Nutrition logged, training missing.",
        expected_evaluation_focus=(
            "keep read scoped",
            "ask for training details naturally",
            "do not pretend full-day training context exists",
        ),
    ),
    DailyCoachPromptLabScenario(
        scenario_id="data_quality_limited",
        user_id=105,
        target_date="2026-06-27",
        purpose="Limited-context behavior check.",
        expected_evaluation_focus=("limited-context wording", "avoid overclaiming"),
    ),
    DailyCoachPromptLabScenario(
        scenario_id="recovery_limited",
        user_id=101,
        target_date="2026-06-27",
        purpose="Recovery-limited behavior check.",
        expected_evaluation_focus=("safe recovery wording", "training caution"),
    ),
)

_VARIANTS: tuple[DailyCoachPromptVariant, ...] = (
    DailyCoachPromptVariant(
        variant_id="current_v5_baseline",
        label="Current v5 baseline",
        hypothesis="Use current v5 prompt/context as the regression control.",
        prompt_changes=(
            "No intentional prompt changes beyond lab addressing/diagnostics package.",
        ),
        context_changes=(
            "Attach lab scenario, addressing policy, and food display language diagnostics.",
        ),
        safety_boundaries=(
            "same parser",
            "same validator",
            "same deterministic fallback",
        ),
    ),
    DailyCoachPromptVariant(
        variant_id="minimal_examples",
        label="Minimal examples",
        hypothesis="Too many examples may cause template copying.",
        prompt_changes=(
            "Use fewer examples.",
            "Keep concise voice contract.",
        ),
        context_changes=("Keep approved context unchanged.",),
        safety_boundaries=("quote/value validation remains strict",),
    ),
    DailyCoachPromptVariant(
        variant_id="plainspoken_fewer_bans",
        label="Plainspoken fewer bans",
        hypothesis="Less negative instruction may improve naturalness while preserving hard safety bans.",
        prompt_changes=(
            "Keep user-rejected phrase bans.",
            "Reduce broader avoid lists.",
            "Emphasize say the actual action.",
        ),
        context_changes=("Keep v5 context package stable.",),
        safety_boundaries=("hard rejected phrases remain invalid",),
    ),
    DailyCoachPromptVariant(
        variant_id="food_action_focused",
        label="Food action focused",
        hypothesis="Food awkwardness is a display-language/context problem.",
        prompt_changes=(
            "Stronger food display contract.",
            "Require food + reason + backed condition.",
        ),
        context_changes=("Emphasize friendly labels and blocked canonical labels.",),
        safety_boundaries=("no invented serving/timing/pairing",),
    ),
    DailyCoachPromptVariant(
        variant_id="first_person_logging_guidance",
        label="First-person logging guidance",
        hypothesis="Some logging guidance may sound more natural in a direct coach voice.",
        prompt_changes=("Lab-only test of plainer coaching language.",),
        context_changes=("No product default change.",),
        safety_boundaries=("first-person is lab-only unless Architecture approves it",),
    ),
    DailyCoachPromptVariant(
        variant_id="higher_variation_same_validator",
        label="Higher variation, same validator",
        hypothesis="The model may write better if not boxed into sentence skeletons.",
        prompt_changes=(
            "Less rigid section phrasing.",
            "More language variation allowed.",
        ),
        context_changes=("No extra factual authority.",),
        safety_boundaries=("same schema", "same validator"),
    ),
    DailyCoachPromptVariant(
        variant_id="friendly_food_labels_only",
        label="Friendly food labels only",
        hypothesis="Food display labels may be a major blocker independent of prompt wording.",
        prompt_changes=("Keep v5 prompt mostly stable.",),
        context_changes=(
            "Replace canonical labels with friendly display names where possible.",
        ),
        safety_boundaries=("canonical labels remain traceability only",),
    ),
    DailyCoachPromptVariant(
        variant_id="canonical_vs_user_facing_food_separation",
        label="Canonical vs user-facing food separation",
        hypothesis="The provider needs a hard distinction between traceability labels and user-facing labels.",
        prompt_changes=("Explicitly distinguish canonical and visible food names.",),
        context_changes=(
            "Provide natural_action_phrase and blocked_user_facing_names.",
        ),
        safety_boundaries=("no giant catalog import", "no meal planning"),
    ),
)
