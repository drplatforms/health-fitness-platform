from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.daily_coach_natural_draft_audit_models import (
    AddressingPolicy,
    ApprovedCoachBrief,
    ClaimAuditResult,
    NaturalCoachDraft,
    NaturalDraftAuditRunResult,
    RepairAttemptResult,
)
from services.daily_coach_approved_brief_service import build_approved_coach_brief
from services.daily_coach_claim_audit_service import audit_extracted_draft_claims
from services.daily_coach_claim_extraction_service import (
    extract_claims_from_natural_draft,
)
from services.daily_coach_draft_repair_service import repair_natural_coach_draft_once
from services.daily_coach_natural_draft_service import write_natural_coach_draft
from services.daily_coach_prompt_lab_service import (
    list_daily_coach_prompt_lab_scenarios,
)
from services.daily_coach_value_narrative_service import PROVIDER_DETERMINISTIC

DEFAULT_NATURAL_DRAFT_AUDIT_OUTPUT_DIR = (
    "docs/provider_trials/daily_coach_natural_draft_claim_audit_v1"
)
SECRET_PATTERNS = ("bearer ", "openai_api_key", "api key", "sk-")
SUPPORTED_NATURAL_DRAFT_PROVIDERS = ("deterministic", "direct_ollama", "openai")


def list_daily_coach_natural_draft_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": scenario.scenario_id,
            "user_id": scenario.user_id,
            "target_date": scenario.target_date,
            "purpose": scenario.purpose,
            "expected_evaluation_focus": list(scenario.expected_evaluation_focus),
        }
        for scenario in list_daily_coach_prompt_lab_scenarios()
        if scenario.scenario_id
        in {
            "rich_nutrition_training_recovery",
            "stable_comparison",
            "training_present_nutrition_missing",
            "nutrition_present_training_missing",
            "data_quality_limited",
            "recovery_limited",
        }
    ]


def get_daily_coach_natural_draft_scenario(scenario_id: str) -> dict[str, Any]:
    for scenario in list_daily_coach_natural_draft_scenarios():
        if scenario["scenario_id"] == scenario_id:
            return scenario
    valid = ", ".join(
        item["scenario_id"] for item in list_daily_coach_natural_draft_scenarios()
    )
    raise ValueError(f"Unknown natural draft scenario: {scenario_id}. Valid: {valid}")


def run_daily_coach_natural_draft_audit_scenario(
    *,
    scenario_id: str,
    provider: str = PROVIDER_DETERMINISTIC,
    model: str | None = None,
    allow_live_provider: bool = False,
    output_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
    brief: ApprovedCoachBrief | None = None,
    draft: NaturalCoachDraft | None = None,
) -> NaturalDraftAuditRunResult:
    scenario = get_daily_coach_natural_draft_scenario(scenario_id)
    env = dict(os.environ if environ is None else environ)
    resolved_provider = _normalize_provider(provider)
    if resolved_provider not in SUPPORTED_NATURAL_DRAFT_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    if resolved_provider != PROVIDER_DETERMINISTIC and not allow_live_provider:
        result = _skipped_result(
            scenario, resolved_provider, model, "live_provider_not_allowed"
        )
        if output_dir:
            write_natural_draft_audit_artifacts(
                output_dir,
                [result],
                config={
                    "scenario_id": scenario_id,
                    "provider": resolved_provider,
                    "model": model,
                },
            )
        return result

    resolved_brief = brief or build_approved_coach_brief(
        user_id=int(scenario["user_id"]),
        target_date=str(scenario["target_date"]),
        scenario_id=scenario_id,
        addressing_policy=AddressingPolicy(),
    )
    try:
        resolved_draft = draft or write_natural_coach_draft(
            resolved_brief,
            provider=resolved_provider,
            model=model,
            allow_live_provider=allow_live_provider,
            environ=env,
        )
    except Exception as exc:  # noqa: BLE001 - dev runner records failure as fallback
        result = _skipped_result(scenario, resolved_provider, model, _safe_error(exc))
        if output_dir:
            write_natural_draft_audit_artifacts(
                output_dir,
                [result],
                config={
                    "scenario_id": scenario_id,
                    "provider": resolved_provider,
                    "model": model,
                },
            )
        return result

    extracted = tuple(extract_claims_from_natural_draft(resolved_draft, resolved_brief))
    audit = audit_extracted_draft_claims(extracted, resolved_brief)
    repair_result = RepairAttemptResult(
        attempted=False,
        provider=resolved_provider,  # type: ignore[arg-type]
        model=model,
    )
    final_copy = resolved_draft if audit.passed else None
    final_source = "draft_approved" if audit.passed else "deterministic_fallback"
    if not audit.passed and audit.repairable:
        repair_result = repair_natural_coach_draft_once(
            draft=resolved_draft,
            brief=resolved_brief,
            audit_result=audit,
            provider=resolved_provider,
            model=model,
            allow_live_provider=allow_live_provider,
            environ=env,
        )
        if repair_result.passed and repair_result.final_copy:
            final_copy = repair_result.final_copy
            final_source = "repair_approved"
    if final_copy is None:
        fallback = write_natural_coach_draft(
            resolved_brief, provider=PROVIDER_DETERMINISTIC
        )
        final_copy = fallback
        final_source = "deterministic_fallback"

    result = NaturalDraftAuditRunResult(
        scenario_id=scenario_id,
        user_id=int(scenario["user_id"]),
        date=str(scenario["target_date"]),
        provider=resolved_provider,  # type: ignore[arg-type]
        model=model,
        draft=resolved_draft,
        extracted_claims=extracted,
        audit_result=audit,
        repair_result=repair_result,
        final_copy=final_copy,
        final_source=final_source,  # type: ignore[arg-type]
        runtime_metadata={
            "developer_only": True,
            "normal_today_unchanged": True,
            "allow_live_provider": allow_live_provider,
            "claim_audit_passed_initially": audit.passed,
            "repair_attempted": repair_result.attempted,
        },
    )
    _assert_result_sanitized(result)
    if output_dir:
        write_natural_draft_audit_artifacts(
            output_dir,
            [result],
            config={
                "scenario_id": scenario_id,
                "provider": resolved_provider,
                "model": model,
            },
        )
    return result


def run_daily_coach_natural_draft_audit_matrix(
    *,
    scenarios: Sequence[str],
    provider: str,
    output_dir: Path,
    model: str | None = None,
    allow_live_provider: bool = False,
    environ: Mapping[str, str] | None = None,
) -> list[NaturalDraftAuditRunResult]:
    selected = list(scenarios) or ["rich_nutrition_training_recovery"]
    results = [
        run_daily_coach_natural_draft_audit_scenario(
            scenario_id=scenario_id,
            provider=provider,
            model=model,
            allow_live_provider=allow_live_provider,
            environ=environ,
        )
        for scenario_id in selected
    ]
    write_natural_draft_audit_artifacts(
        output_dir,
        results,
        config={
            "run_id": _build_run_id(provider),
            "scenarios": selected,
            "provider": provider,
            "model": model,
            "allow_live_provider": allow_live_provider,
        },
    )
    return results


def write_natural_draft_audit_artifacts(
    output_dir: Path,
    results: Sequence[NaturalDraftAuditRunResult],
    *,
    config: Mapping[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_config.json").write_text(
        json.dumps(dict(config), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    (output_dir / "approved_coach_brief_summary.md").write_text(
        _render_brief_summary(results), encoding="utf-8"
    )
    (output_dir / "natural_draft_output.md").write_text(
        _render_drafts(results), encoding="utf-8"
    )
    (output_dir / "claim_extraction_summary.json").write_text(
        json.dumps(
            [
                {
                    "scenario_id": result.scenario_id,
                    "claims": [claim.to_dict() for claim in result.extracted_claims],
                }
                for result in results
            ],
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (output_dir / "claim_audit_summary.md").write_text(
        _render_audit_summary(results), encoding="utf-8"
    )
    (output_dir / "repair_summary.md").write_text(
        _render_repair_summary(results), encoding="utf-8"
    )
    (output_dir / "final_approved_copy.md").write_text(
        _render_final_copy(results), encoding="utf-8"
    )
    _write_comparison_csv(output_dir / "comparison_table.csv", results)
    (output_dir / "comparison_table.md").write_text(
        _render_comparison_table(results), encoding="utf-8"
    )
    (output_dir / "validation_summary.md").write_text(
        _render_validation_summary(results), encoding="utf-8"
    )
    (output_dir / "scoring_template.md").write_text(
        _render_scoring_template(results), encoding="utf-8"
    )
    serialized = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output_dir.iterdir()
        if path.is_file()
    )
    if _contains_secretish_text(serialized):
        raise ValueError("Natural Draft Audit artifacts contain secret-like text.")
    if "raw_provider_output" in serialized:
        raise ValueError(
            "Natural Draft Audit default artifacts contain raw provider output."
        )


def _skipped_result(
    scenario: Mapping[str, Any], provider: str, model: str | None, reason: str
) -> NaturalDraftAuditRunResult:
    audit = ClaimAuditResult(
        passed=False,
        repairable=False,
        final_decision="fallback_required",
    )
    repair = RepairAttemptResult(
        attempted=False,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        fallback_reason=reason,
    )
    return NaturalDraftAuditRunResult(
        scenario_id=str(scenario["scenario_id"]),
        user_id=int(scenario["user_id"]),
        date=str(scenario["target_date"]),
        provider=provider,  # type: ignore[arg-type]
        model=model,
        draft=None,
        extracted_claims=(),
        audit_result=audit,
        repair_result=repair,
        final_copy=None,
        final_source="skipped",
        runtime_metadata={"skipped": True, "skip_reason": reason},
    )


def _render_brief_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Approved Coach Brief Summary",
        "",
        "This artifact summarizes scenario/date/provider only. It does not include raw DB rows.",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"User: {result.user_id}",
                f"Date: {result.date}",
                f"Provider: {result.provider}",
                f"Final source: {result.final_source}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_drafts(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Natural Draft Output",
        "",
        "Raw provider output is not included in this default artifact.",
        "",
    ]
    for result in results:
        lines.extend(
            [f"## {result.scenario_id}", f"Final source: {result.final_source}"]
        )
        if result.draft:
            lines.extend(
                [f"Draft headline: {result.draft.headline}", "", result.draft.body]
            )
        else:
            lines.append("(draft skipped or unavailable)")
        lines.append("")
    return "\n".join(lines)


def _render_audit_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Claim Audit Summary", ""]
    for result in results:
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"Passed: {result.audit_result.passed}",
                f"Decision: {result.audit_result.final_decision}",
                f"Findings: {len(result.audit_result.findings)}",
            ]
        )
        for finding in result.audit_result.findings:
            lines.append(
                f"- {finding.finding_type}: {finding.reason} Repairable={finding.repairable}"
            )
        lines.append("")
    return "\n".join(lines)


def _render_repair_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Repair Summary", ""]
    for result in results:
        repair = result.repair_result
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"Attempted: {repair.attempted}",
                f"Passed: {repair.passed}",
                f"Fallback reason: {repair.fallback_reason or 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_final_copy(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Final Approved Copy", ""]
    for result in results:
        lines.extend([f"## {result.scenario_id}", f"Source: {result.final_source}"])
        if result.final_copy:
            lines.extend(
                [f"### {result.final_copy.headline}", "", result.final_copy.body]
            )
        else:
            lines.append("(no final copy)")
        lines.append("")
    return "\n".join(lines)


def _write_comparison_csv(
    path: Path, results: Sequence[NaturalDraftAuditRunResult]
) -> None:
    rows = [_comparison_row(result) for result in results]
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _render_comparison_table(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Natural Draft Claim Audit Comparison Table",
        "",
        "| Scenario | Provider | Final source | Initial audit | Repair attempted | Findings |",
        "|---|---|---|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.scenario_id} | {result.provider} | {result.final_source} | {result.audit_result.passed} | {result.repair_result.attempted} | {len(result.audit_result.findings)} |"
        )
    return "\n".join(lines) + "\n"


def _render_validation_summary(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = ["# Natural Draft Claim Audit Validation Summary", ""]
    for result in results:
        lines.extend(
            [
                f"## {result.scenario_id}",
                f"Developer only: {result.runtime_metadata.get('developer_only', False)}",
                f"Normal Today unchanged: {result.runtime_metadata.get('normal_today_unchanged', True)}",
                f"Unsupported claims: {result.audit_result.unsupported_claim_count}",
                f"Food claims: {result.audit_result.food_claim_count}",
                f"Causal claims: {result.audit_result.causal_claim_count}",
                f"Addressing violations: {result.audit_result.addressing_violation_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_scoring_template(results: Sequence[NaturalDraftAuditRunResult]) -> str:
    lines = [
        "# Natural Draft + Claim Audit Scoring Template",
        "",
        "Score product voice after technical validation. Grounding must remain 5.",
        "",
        "| Scenario | Provider | Plainspoken voice | Action clarity | Food naturalness | Training clarity | Recovery clarity | Logic coherence | Grounding | Product readiness | Notes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.scenario_id} | {result.provider} |  |  |  |  |  |  |  |  |  |"
        )
    return "\n".join(lines) + "\n"


def _comparison_row(result: NaturalDraftAuditRunResult) -> dict[str, Any]:
    return {
        "scenario_id": result.scenario_id,
        "user_id": result.user_id,
        "date": result.date,
        "provider": result.provider,
        "model": result.model or "",
        "final_source": result.final_source,
        "initial_audit_passed": result.audit_result.passed,
        "repair_attempted": result.repair_result.attempted,
        "repair_passed": result.repair_result.passed,
        "finding_count": len(result.audit_result.findings),
        "unsupported_claim_count": result.audit_result.unsupported_claim_count,
        "causal_claim_count": result.audit_result.causal_claim_count,
        "addressing_violation_count": result.audit_result.addressing_violation_count,
    }


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower()


def _build_run_id(provider: str) -> str:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    return f"daily_coach_natural_draft_claim_audit_v1_{provider}_{timestamp.replace(':', '').replace('+', 'z')}"


def _contains_secretish_text(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in SECRET_PATTERNS)


def _assert_result_sanitized(result: NaturalDraftAuditRunResult) -> None:
    serialized = json.dumps(result.to_dict(), default=str).lower()
    if "raw_provider_output" in serialized:
        raise ValueError("Natural Draft Audit result contains raw provider output.")
    if _contains_secretish_text(serialized):
        raise ValueError("Natural Draft Audit result contains secret-like text.")


def _safe_error(exc: Exception) -> str:
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", str(exc).replace("\n", " ")[:180])
