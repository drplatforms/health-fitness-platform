"""Run a sanitized Daily Coach Narrative provider trial matrix.

This tool is developer/Architecture evaluation tooling only. It compares the
existing Daily Coach value-aware narrative path across selected providers without
changing product defaults, persisting narratives, or exposing raw provider
output. Live providers are skipped unless explicitly enabled.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.daily_coach_value_narrative_service import (  # noqa: E402
    DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV,
    DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV,
    OLLAMA_BASE_URL_ENV,
    OPENAI_API_KEY_ENV,
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
    build_configured_daily_coach_value_narrative,
)

SUPPORTED_PROVIDERS = {
    PROVIDER_DETERMINISTIC,
    PROVIDER_DIRECT_OLLAMA,
    PROVIDER_OPENAI,
}
DEFAULT_OUTPUT_DIR = (
    "docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1"
)
DEFAULT_CASE_LABELS = {
    101: "recovery_limited",
    102: "aligned_managed_recovery_truth_regression",
    103: "nutrition_training_mismatch",
    104: "improving_after_deload",
    105: "data_quality_limited",
}
ENV_KEYS_TO_RESTORE = [
    DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV,
    DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV,
]
FORBIDDEN_OUTPUT_TOKENS = [
    "raw provider output",
    "raw_provider_output",
    "bearer ",
]


@dataclass(frozen=True)
class TrialMatrixCase:
    user_id: int
    trial_date: str
    provider: str
    model: str | None
    case_label: str


@dataclass(frozen=True)
class TrialMatrixRow:
    run_id: str
    timestamp: str
    user_id: int
    date: str
    provider: str
    model: str | None
    case_label: str
    success: bool
    skipped: bool
    skip_reason: str | None
    latency_ms: int | None
    approved_daily_coach_narrative: dict[str, Any] | None
    rendered_narrative: str | None
    runtime_metadata: dict[str, Any]
    provider_context_summary: dict[str, Any]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


NarrativeBuilder = Callable[..., Any]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Daily Coach Narrative provider trial matrix tooling."
    )
    parser.add_argument("--users", nargs="+", type=int, required=True)
    parser.add_argument("--date", required=True, help="Trial date in YYYY-MM-DD form.")
    parser.add_argument(
        "--providers",
        nargs="+",
        required=True,
        choices=sorted(SUPPORTED_PROVIDERS),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--models",
        nargs="*",
        default=[],
        help=(
            "Optional provider=model overrides, e.g. "
            "direct_ollama=ollama/qwen2.5:3b openai=gpt-4.1-mini."
        ),
    )
    parser.add_argument("--timeout-seconds", type=float, default=None)
    parser.add_argument("--allow-live-providers", action="store_true")
    parser.add_argument("--include-debug", action="store_true")
    parser.add_argument("--jsonl", action="store_true", default=True)
    parser.add_argument("--no-jsonl", action="store_false", dest="jsonl")
    parser.add_argument("--markdown", action="store_true", default=True)
    parser.add_argument("--no-markdown", action="store_false", dest="markdown")
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--label", default="daily_coach_narrative_provider_trial")
    return parser.parse_args(argv)


def run_trial_matrix(
    *,
    users: list[int],
    trial_date: str,
    providers: list[str],
    output_dir: Path,
    model_overrides: Mapping[str, str] | None = None,
    allow_live_providers: bool = False,
    include_debug: bool = False,
    max_cases: int | None = None,
    label: str = "daily_coach_narrative_provider_trial",
    narrative_builder: NarrativeBuilder = build_configured_daily_coach_value_narrative,
    environ: Mapping[str, str] | None = None,
    write_jsonl: bool = True,
    write_markdown: bool = True,
) -> list[TrialMatrixRow]:
    """Run the configured trial matrix and write sanitized artifacts."""

    env = dict(environ or os.environ)
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_id = f"{_slug(label)}_{timestamp.replace(':', '').replace('+', 'z')}"
    rows: list[TrialMatrixRow] = []

    cases = _build_cases(
        users=users,
        trial_date=trial_date,
        providers=providers,
        model_overrides=model_overrides or {},
    )
    if max_cases is not None:
        cases = cases[: max(0, max_cases)]

    for case in cases:
        rows.append(
            _run_case(
                case,
                run_id=run_id,
                timestamp=timestamp,
                allow_live_providers=allow_live_providers,
                include_debug=include_debug,
                narrative_builder=narrative_builder,
                base_environ=env,
            )
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    if write_jsonl:
        _write_jsonl(output_dir / "trial_matrix.jsonl", rows)
    if write_markdown:
        (output_dir / "trial_matrix_summary.md").write_text(
            render_summary_markdown(rows, allow_live_providers=allow_live_providers),
            encoding="utf-8",
        )
        (output_dir / "selected_outputs.md").write_text(
            render_selected_outputs_markdown(rows),
            encoding="utf-8",
        )
    return rows


def _build_cases(
    *,
    users: list[int],
    trial_date: str,
    providers: list[str],
    model_overrides: Mapping[str, str],
) -> list[TrialMatrixCase]:
    cases: list[TrialMatrixCase] = []
    for user_id in users:
        label = DEFAULT_CASE_LABELS.get(user_id, f"user_{user_id}")
        for provider in providers:
            model = model_overrides.get(provider)
            cases.append(
                TrialMatrixCase(
                    user_id=user_id,
                    trial_date=trial_date,
                    provider=provider,
                    model=model,
                    case_label=label,
                )
            )
    return cases


def _run_case(
    case: TrialMatrixCase,
    *,
    run_id: str,
    timestamp: str,
    allow_live_providers: bool,
    include_debug: bool,
    narrative_builder: NarrativeBuilder,
    base_environ: Mapping[str, str],
) -> TrialMatrixRow:
    live_skip_reason = _live_provider_skip_reason(
        case.provider,
        allow_live_providers=allow_live_providers,
        env=base_environ,
    )
    if live_skip_reason:
        return _skipped_row(case, run_id, timestamp, live_skip_reason)

    env_updates = {DAILY_COACH_VALUE_NARRATIVE_PROVIDER_ENV: case.provider}
    if case.model:
        env_updates[DAILY_COACH_VALUE_NARRATIVE_MODEL_ENV] = case.model

    start = time.perf_counter()
    with _patched_environ(env_updates):
        try:
            result = narrative_builder(case.user_id, target_date=case.trial_date)
        except Exception as exc:  # noqa: BLE001 - trial tool must not crash matrix
            latency_ms = int((time.perf_counter() - start) * 1000)
            return _skipped_row(
                case,
                run_id,
                timestamp,
                f"case_unavailable_or_builder_error: {_safe_exception(exc)}",
                latency_ms=latency_ms,
            )

    latency_ms = int((time.perf_counter() - start) * 1000)
    debug_payload = result.to_debug_dict()
    public_payload = result.to_public_dict()
    runtime_metadata = dict(debug_payload.get("runtime_metadata") or {})
    provider_context_summary = (
        dict(debug_payload.get("provider_context_summary") or {})
        if include_debug
        else {}
    )
    approved = public_payload.get("approved_daily_coach_narrative")
    rendered = public_payload.get("rendered_narrative")

    row = TrialMatrixRow(
        run_id=run_id,
        timestamp=timestamp,
        user_id=case.user_id,
        date=case.trial_date,
        provider=case.provider,
        model=str(runtime_metadata.get("selected_model") or case.model or ""),
        case_label=case.case_label,
        success=bool(public_payload.get("success")),
        skipped=False,
        skip_reason=None,
        latency_ms=latency_ms,
        approved_daily_coach_narrative=(
            approved if isinstance(approved, dict) else None
        ),
        rendered_narrative=(rendered if isinstance(rendered, str) else None),
        runtime_metadata=_sanitize_runtime_metadata(runtime_metadata),
        provider_context_summary=provider_context_summary,
    )
    _assert_row_is_public_safe(row)
    return row


def _live_provider_skip_reason(
    provider: str,
    *,
    allow_live_providers: bool,
    env: Mapping[str, str],
) -> str | None:
    if provider == PROVIDER_DETERMINISTIC:
        return None
    if not allow_live_providers:
        return "live_provider_not_allowed"
    if provider == PROVIDER_OPENAI and not env.get(OPENAI_API_KEY_ENV):
        return "missing_OPENAI_API_KEY"
    if provider == PROVIDER_DIRECT_OLLAMA and not env.get(OLLAMA_BASE_URL_ENV):
        return "missing_OLLAMA_BASE_URL"
    return None


def _skipped_row(
    case: TrialMatrixCase,
    run_id: str,
    timestamp: str,
    reason: str,
    *,
    latency_ms: int | None = None,
) -> TrialMatrixRow:
    return TrialMatrixRow(
        run_id=run_id,
        timestamp=timestamp,
        user_id=case.user_id,
        date=case.trial_date,
        provider=case.provider,
        model=case.model,
        case_label=case.case_label,
        success=False,
        skipped=True,
        skip_reason=reason,
        latency_ms=latency_ms,
        approved_daily_coach_narrative=None,
        rendered_narrative=None,
        runtime_metadata={"selected_provider": case.provider, "skip_reason": reason},
        provider_context_summary={},
    )


@contextmanager
def _patched_environ(updates: Mapping[str, str]):
    old_values = {key: os.environ.get(key) for key in ENV_KEYS_TO_RESTORE}
    try:
        for key, value in updates.items():
            os.environ[key] = value
        yield
    finally:
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _sanitize_runtime_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(metadata)
    for forbidden_key in ["raw_output", "raw_provider_output", "raw_output_preview"]:
        sanitized.pop(forbidden_key, None)
    return sanitized


def _assert_row_is_public_safe(row: TrialMatrixRow) -> None:
    text = json.dumps(row.to_dict(), sort_keys=True, default=str).lower()
    for token in FORBIDDEN_OUTPUT_TOKENS:
        if token in text:
            raise ValueError(f"Forbidden output token detected: {token}")
    if os.getenv(OPENAI_API_KEY_ENV) and os.getenv(OPENAI_API_KEY_ENV) in text:
        raise ValueError("OpenAI API key leaked into trial output")


def _write_jsonl(path: Path, rows: list[TrialMatrixRow]) -> None:
    lines = [json.dumps(row.to_dict(), sort_keys=True, default=str) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def render_summary_markdown(
    rows: list[TrialMatrixRow],
    *,
    allow_live_providers: bool,
) -> str:
    lines = [
        "# Daily Coach Narrative Provider Trial Matrix v1",
        "",
        "Generated by `tools/run_daily_coach_provider_trial_matrix.py`.",
        "",
        f"Live providers allowed: `{allow_live_providers}`.",
        "",
        "Deterministic remains the product default. This artifact is evaluation output only.",
        "",
        "## Comparison table",
        "",
        "| user_id | date | case_label | provider | model | final_source | fallback_used | fallback_reason | parse_status | validation_status | quote_validation_status | latency_ms | quoted_values_used | recovery_parity | training_parity | nutrition_parity | value_quote_accuracy | copy_quality_notes | usefulness_notes |",
        "|---:|---|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        metadata = row.runtime_metadata
        approved = row.approved_daily_coach_narrative or {}
        quoted = approved.get("quoted_values_used") or []
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.user_id),
                    row.date,
                    _md(row.case_label),
                    _md(row.provider),
                    _md(row.model or ""),
                    _md(str(metadata.get("final_narrative_source") or "skipped")),
                    _md(
                        str(
                            metadata.get("fallback_used")
                            if not row.skipped
                            else "skipped"
                        )
                    ),
                    _md(str(metadata.get("fallback_reason") or row.skip_reason or "")),
                    _md(str(metadata.get("candidate_parse_status") or "skipped")),
                    _md(str(metadata.get("validation_status") or "skipped")),
                    _md(_quote_validation_status(row)),
                    str(row.latency_ms if row.latency_ms is not None else ""),
                    _md(", ".join(str(item) for item in quoted)),
                    _md(_default_parity_note(row, "recovery")),
                    _md(_default_parity_note(row, "training")),
                    _md(_default_parity_note(row, "nutrition")),
                    _md(_quote_accuracy_note(row)),
                    "",
                    "",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Rubric",
            "",
            "- Schema adherence: passed, failed, or fallback based on parse/validation metadata.",
            "- Quote/value safety: all quoted values approved, invalid quote fallback, or no values quoted.",
            "- Recovery parity: matches backend recovery context, vague but not wrong, or contradicted/fallback.",
            "- Training parity: matches workout/training context, vague but not wrong, or contradicted/fallback.",
            "- Nutrition parity: matches actuals/gaps/suggestions context, vague but not wrong, or contradicted/fallback.",
            "- Coaching usefulness: strong, acceptable, weak, or fallback after manual review.",
            "- Tone: motivating, neutral, awkward, or unsafe/fallback after manual review.",
            "- Latency: recorded in milliseconds.",
            "",
            "## Expected findings template",
            "",
            "1. Did deterministic remain stable?",
            "2. Did direct_ollama complete any cases without fallback?",
            "3. Did openai complete any cases without fallback?",
            "4. Which provider had the best copy?",
            "5. Which provider had the best quote/value discipline?",
            "6. Which provider had the best recovery/training/nutrition synthesis?",
            "7. Which provider had the worst latency?",
            "8. Which provider fell back most often?",
            "9. Did any provider attempt invented values?",
            "10. Did any provider trigger quote/value validation?",
            "11. Is OpenAI worth continuing as preferred hosted synthesis provider?",
            "12. Is direct_ollama still useful as offline developer mode?",
            "13. Should deterministic remain default? Expected answer: yes.",
            "14. Should any provider become default now? Expected answer: no.",
            "",
            "## Manual review notes",
            "",
            "- copy_quality_notes:",
            "- usefulness_notes:",
            "- preferred_provider_for_case:",
            "- concern_flags:",
        ]
    )
    return "\n".join(lines) + "\n"


def render_selected_outputs_markdown(rows: list[TrialMatrixRow]) -> str:
    selected = [row for row in rows if row.user_id == 102 and row.date == "2026-06-27"]
    if not selected:
        selected = rows[: min(6, len(rows))]
    lines = [
        "# Selected Daily Coach Narrative Outputs",
        "",
        "Only approved narratives and deterministic rendered narratives are shown.",
        "Provider raw text is intentionally excluded.",
        "",
    ]
    for row in selected:
        lines.extend(
            [
                f"## User {row.user_id} — {row.date} — {row.provider}",
                "",
                f"Case label: `{row.case_label}`",
                "",
                f"Skipped: `{row.skipped}`",
                "",
            ]
        )
        if row.skip_reason:
            lines.extend([f"Skip reason: `{row.skip_reason}`", ""])
            continue
        lines.extend(
            [
                "### Approved narrative",
                "",
                "```json",
                json.dumps(
                    row.approved_daily_coach_narrative or {},
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                "```",
                "",
                "### Rendered narrative",
                "",
                row.rendered_narrative or "",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def _quote_validation_status(row: TrialMatrixRow) -> str:
    if row.skipped:
        return "skipped"
    metadata = row.runtime_metadata
    validation_errors = metadata.get("validation_errors") or []
    if any(
        "quote" in str(error).lower() or "value" in str(error).lower()
        for error in validation_errors
    ):
        return "quote_validation_failed"
    if metadata.get("fallback_used") is True:
        return "fallback_no_quote_failure_recorded"
    return "passed_or_not_applicable"


def _default_parity_note(row: TrialMatrixRow, domain: str) -> str:
    if row.skipped:
        return "skipped"
    if row.runtime_metadata.get("fallback_used"):
        return "fallback"
    narrative = row.approved_daily_coach_narrative or {}
    text = " ".join(str(value) for value in narrative.values()).lower()
    if domain in text:
        return "mentions_context"
    return "manual_review"


def _quote_accuracy_note(row: TrialMatrixRow) -> str:
    if row.skipped:
        return "skipped"
    quoted = (row.approved_daily_coach_narrative or {}).get("quoted_values_used") or []
    if row.runtime_metadata.get("fallback_used"):
        return "fallback"
    if quoted:
        return "declared_quotes_present"
    return "no_values_quoted"


def parse_model_overrides(values: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError("--models entries must use provider=model syntax")
        provider, model = raw.split("=", 1)
        provider = provider.strip().lower()
        model = model.strip()
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported model override provider: {provider}")
        if not model:
            raise ValueError(f"Empty model override for provider: {provider}")
        overrides[provider] = model
    return overrides


def _safe_exception(exc: Exception) -> str:
    text = str(exc) or exc.__class__.__name__
    for token in [os.getenv(OPENAI_API_KEY_ENV) or ""]:
        if token:
            text = text.replace(token, "<redacted>")
    return text[:240]


def _slug(value: str) -> str:
    allowed = [char.lower() if char.isalnum() else "_" for char in value]
    slug = "".join(allowed).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "trial"


def _md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows = run_trial_matrix(
        users=args.users,
        trial_date=args.date,
        providers=args.providers,
        output_dir=Path(args.output_dir),
        model_overrides=parse_model_overrides(args.models),
        allow_live_providers=args.allow_live_providers,
        include_debug=args.include_debug,
        max_cases=args.max_cases,
        label=args.label,
        write_jsonl=args.jsonl,
        write_markdown=args.markdown,
    )
    print(f"Wrote Daily Coach provider trial matrix to {args.output_dir}")
    print(f"Rows: {len(rows)}")
    skipped = sum(1 for row in rows if row.skipped)
    if skipped:
        print(f"Skipped rows: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
