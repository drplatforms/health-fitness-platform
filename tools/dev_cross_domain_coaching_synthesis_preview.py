# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.cross_domain_coaching_preview_models import (  # noqa: E402
    CrossDomainCoachingPreviewResult,
)
from models.daily_coach_natural_draft_audit_models import (
    ApprovedCoachBrief,  # noqa: E402
)
from services.cross_domain_coaching_evidence_service import (  # noqa: E402
    build_cross_domain_coaching_context_for_user,
)
from services.cross_domain_coaching_preview_service import (  # noqa: E402
    build_narrative_provider_input,
    build_specialist_provider_input,
    run_cross_domain_coaching_preview,
)

DEFAULT_ASSESSMENT_PROMPT_FILE = (
    "docs/provider_trials/cross_domain_specialist_assessment_prompt_v1.md"
)
DEFAULT_NARRATIVE_PROMPT_FILE = (
    "docs/provider_trials/cross_domain_narrative_prompt_v1.md"
)
_SECRET_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]+")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Developer-only two-call cross-domain coaching synthesis preview. "
            "It does not persist output or expose a product surface."
        )
    )
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--target-date", required=True)
    providers = ("mock", "openai", "direct_ollama")
    parser.add_argument("--assessment-provider", choices=providers, required=True)
    parser.add_argument("--assessment-model", required=True)
    parser.add_argument("--narrative-provider", choices=providers)
    parser.add_argument("--narrative-model")
    parser.add_argument(
        "--assessment-prompt-file", default=DEFAULT_ASSESSMENT_PROMPT_FILE
    )
    parser.add_argument(
        "--narrative-prompt-file", default=DEFAULT_NARRATIVE_PROMPT_FILE
    )
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional artifact directory. No files are written when omitted.",
    )
    parser.add_argument("--show-evidence", action="store_true")
    args = parser.parse_args(argv)

    assessment_prompt = _read_prompt(args.assessment_prompt_file)
    narrative_prompt = _read_prompt(args.narrative_prompt_file)
    narrative_provider = args.narrative_provider or args.assessment_provider
    narrative_model = args.narrative_model or args.assessment_model
    result, approved_brief, assessment_input, narrative_input = run_preview(
        user_id=args.user_id,
        target_date=args.target_date,
        assessment_provider=args.assessment_provider,
        assessment_model=args.assessment_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        assessment_prompt=assessment_prompt,
        narrative_prompt=narrative_prompt,
        timeout_seconds=args.timeout_seconds,
    )
    print_preview(
        result=result,
        approved_brief=approved_brief,
        show_evidence=args.show_evidence,
    )
    if args.output_dir:
        write_preview_artifacts(
            output_dir=Path(args.output_dir),
            result=result,
            assessment_provider_input=assessment_input,
            narrative_provider_input=narrative_input,
            run_config={
                "developer_preview_only": True,
                "persistence_allowed": False,
                "product_surface_allowed": False,
                "assessment_provider": args.assessment_provider,
                "assessment_model": args.assessment_model,
                "narrative_provider": narrative_provider,
                "narrative_model": narrative_model,
                "user_id": args.user_id,
                "target_date": args.target_date,
                "assessment_prompt_file": args.assessment_prompt_file,
                "narrative_prompt_file": args.narrative_prompt_file,
                "timeout_seconds": args.timeout_seconds,
            },
        )
    return 0


def run_preview(
    *,
    user_id: int,
    target_date: str,
    assessment_provider: str,
    assessment_model: str,
    narrative_provider: str,
    narrative_model: str,
    assessment_prompt: str,
    narrative_prompt: str,
    timeout_seconds: float,
) -> tuple[CrossDomainCoachingPreviewResult, ApprovedCoachBrief, str, str | None]:
    """Run one isolated preview without writing artifacts or changing user data."""

    evidence_packet, approved_brief = build_cross_domain_coaching_context_for_user(
        user_id=user_id,
        target_date=target_date,
    )
    result = run_cross_domain_coaching_preview(
        evidence_packet=evidence_packet,
        approved_brief=approved_brief,
        assessment_provider=assessment_provider,
        assessment_model=assessment_model,
        narrative_provider=narrative_provider,
        narrative_model=narrative_model,
        assessment_prompt=assessment_prompt,
        narrative_prompt=narrative_prompt,
        timeout_seconds=timeout_seconds,
    )
    assessment_input = build_specialist_provider_input(
        assessment_prompt, result.assessment_context
    )
    narrative_input = None
    if result.semantic_narrative_context:
        narrative_input = build_narrative_provider_input(
            narrative_prompt,
            semantic_narrative_context=result.semantic_narrative_context,
        )
    return result, approved_brief, assessment_input, narrative_input


def print_preview(
    *,
    result: CrossDomainCoachingPreviewResult,
    approved_brief: ApprovedCoachBrief,
    show_evidence: bool,
) -> None:
    print("=== Cross-Domain Coaching Synthesis Preview ===")
    print("Repository/runtime metadata")
    print(f"user_id: {result.user_id}")
    print(f"target_date: {result.target_date}")
    print(f"assessment_provider: {result.assessment_provider}")
    print(f"assessment_model: {result.assessment_model}")
    print(f"narrative_provider: {result.narrative_provider}")
    print(f"narrative_model: {result.narrative_model}")
    print(f"provider_call_count: {result.provider_call_count}")
    print("Current deterministic synthesis")
    print(f"scenario: {result.evidence_packet.scenario}")
    print(f"today_intent: {approved_brief.today_intent}")
    print("Evidence summary")
    print("full evidence")
    for domain, facts in result.evidence_packet.domain_evidence.items():
        print(f"{domain}: {len(facts)} facts")
    print("provider-facing assessment context")
    for domain, facts in result.assessment_context.domain_evidence.items():
        print(f"{domain}: {len(facts)} facts")
    if show_evidence:
        print(_json(result.evidence_packet.to_dict()))
    _print_specialist_domain("Recovery specialist", result, "recovery")
    _print_specialist_domain("Nutrition specialist", result, "nutrition")
    _print_specialist_domain("Training specialist", result, "training")
    print("Cross-domain tensions")
    print(
        _json(
            [
                item.to_dict()
                for item in result.specialist_assessment.cross_domain_tensions
            ]
            if result.specialist_assessment
            else []
        )
    )
    print("Deterministic resolution")
    print(_json(result.resolved_brief.to_dict() if result.resolved_brief else None))
    print("Narrative confidence policy")
    print(
        _json(
            result.narrative_confidence_policy.to_dict()
            if result.narrative_confidence_policy
            else None
        )
    )
    print("Natural narrative")
    print(_json(result.narrative_draft.to_dict() if result.narrative_draft else None))
    print("Claim audit")
    print(
        _json(
            result.claim_audit_result.to_dict() if result.claim_audit_result else None
        )
    )
    print("Confidence coherence audit")
    print(
        _json(
            result.confidence_coherence_audit_result.to_dict()
            if result.confidence_coherence_audit_result
            else None
        )
    )
    print("Product voice audit")
    print(
        _json(
            result.product_voice_audit_result.to_dict()
            if result.product_voice_audit_result
            else None
        )
    )
    print("Final preview disposition")
    print(result.disposition)
    if result.error_type:
        print(f"error_type: {result.error_type}")
        print(f"error_message: {result.error_message}")


def write_preview_artifacts(
    *,
    output_dir: Path,
    result: CrossDomainCoachingPreviewResult,
    assessment_provider_input: str,
    narrative_provider_input: str | None,
    run_config: dict[str, Any],
) -> None:
    """Write optional sanitized developer artifacts and nothing else."""

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "run_config.json", run_config)
    _write_json(output_dir / "evidence_packet.json", result.evidence_packet.to_dict())
    _write_json(
        output_dir / "assessment_context.json",
        result.assessment_context.to_dict(),
    )
    _write_text(output_dir / "assessment_provider_input.txt", assessment_provider_input)
    _write_text(
        output_dir / "assessment_raw_output.txt", result.specialist_raw_output or ""
    )
    _write_json(
        output_dir / "assessment_parsed.json",
        result.specialist_assessment.to_dict()
        if result.specialist_assessment
        else None,
    )
    _write_json(
        output_dir / "resolved_brief.json",
        result.resolved_brief.to_dict() if result.resolved_brief else None,
    )
    _write_json(
        output_dir / "semantic_narrative_context.json",
        result.semantic_narrative_context,
    )
    _write_text(
        output_dir / "narrative_provider_input.txt", narrative_provider_input or ""
    )
    _write_text(
        output_dir / "narrative_raw_output.txt", result.narrative_raw_output or ""
    )
    _write_json(
        output_dir / "claim_audit.json",
        result.claim_audit_result.to_dict() if result.claim_audit_result else None,
    )
    _write_json(
        output_dir / "confidence_coherence_audit.json",
        (
            result.confidence_coherence_audit_result.to_dict()
            if result.confidence_coherence_audit_result
            else None
        ),
    )
    _write_json(
        output_dir / "product_voice_audit.json",
        (
            result.product_voice_audit_result.to_dict()
            if result.product_voice_audit_result
            else None
        ),
    )
    _write_text(
        output_dir / "preview_summary.md", build_preview_summary_markdown(result)
    )


def build_preview_summary_markdown(result: CrossDomainCoachingPreviewResult) -> str:
    confidence_policy = result.narrative_confidence_policy
    coherence_audit = result.confidence_coherence_audit_result
    lines = [
        "# Cross-Domain Coaching Synthesis Preview",
        "",
        f"- Disposition: `{result.disposition}`",
        f"- Assessment provider: `{result.assessment_provider}`",
        f"- Assessment model: `{result.assessment_model}`",
        f"- Narrative provider: `{result.narrative_provider}`",
        f"- Narrative model: `{result.narrative_model}`",
        f"- Provider calls: `{result.provider_call_count}`",
        f"- Scenario: `{result.evidence_packet.scenario}`",
        "- Full evidence facts: "
        + str(
            sum(len(facts) for facts in result.evidence_packet.domain_evidence.values())
        ),
        "- Assessment-context facts: "
        + str(
            sum(
                len(facts)
                for facts in result.assessment_context.domain_evidence.values()
            )
        ),
        f"- Resolved confidence: `{confidence_policy.resolved_confidence if confidence_policy else 'n/a'}`",
        "- Material limitations: "
        + str(len(confidence_policy.material_limitations) if confidence_policy else 0),
        "- Source-data gaps preserved: "
        + str(
            confidence_policy.source_data_gaps_preserved if confidence_policy else False
        ),
        "- Certainty violations: "
        + str(coherence_audit.certainty_violation_count if coherence_audit else 0),
        "- Confidence-coherence decision: "
        + f"`{coherence_audit.decision if coherence_audit else 'not_run'}`",
        "",
    ]
    if result.narrative_draft:
        lines.extend(
            [
                f"## {result.narrative_draft.headline}",
                "",
                result.narrative_draft.body,
                "",
            ]
        )
    return "\n".join(lines)


def _print_specialist_domain(
    heading: str,
    result: CrossDomainCoachingPreviewResult,
    domain: str,
) -> None:
    print(heading)
    assessment = result.specialist_assessment
    print(_json(assessment.for_domain(domain).to_dict() if assessment else None))


def _read_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(_sanitize_value(payload), indent=2, sort_keys=True))


def _write_text(path: Path, value: str) -> None:
    path.write_text(_sanitize_text(value), encoding="utf-8")


def _json(value: Any) -> str:
    return json.dumps(_sanitize_value(value), indent=2, sort_keys=True)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _sanitize_text(value: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    sanitized = value.replace(api_key, "[redacted]") if api_key else value
    return _SECRET_PATTERN.sub("[redacted]", sanitized)


if __name__ == "__main__":
    raise SystemExit(main())
