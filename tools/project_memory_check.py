"""Read-only project-memory consistency checks for AI Health Coach."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemoryCheckResult:
    status: str
    path: str
    message: str


REQUIRED_FILES = [
    "AGENTS.md",
    ".github/copilot-instructions.md",
    "docs/project_memory/current_state.md",
    "docs/project_memory/product_vision.md",
    "docs/project_memory/architecture_principles.md",
    "docs/project_memory/backend_truth_contract.md",
    "docs/project_memory/ai_boundaries.md",
    "docs/project_memory/section_registry_summary.md",
    "docs/project_memory/open_questions.md",
    "docs/project_memory/development_workflow.md",
    "docs/project_memory/agent_workflow.md",
]

STALE_MARKERS = {
    "docs/project_memory/current_state.md": [
        "Latest accepted milestone\n\n`Daily Coach Narrative Developer Preview v1`",
        "Current implementation milestone\n\n`Daily Coach Narrative Async Today Preview Design v1`",
    ],
}

REQUIRED_PHRASES = {
    "AGENTS.md": [
        "docs/project_memory",
        "Backend owns facts",
        "Deterministic fallback remains the default",
        "Do not add `CLAUDE.md`",
    ],
    ".github/copilot-instructions.md": [
        "Backend owns facts",
        "Preserve deterministic fallback behavior",
        "Do not add Claude workflow files",
    ],
    "docs/project_memory/agent_workflow.md": [
        "ChatGPT",
        "Codex",
        "Dev Assistant",
        "Claude",
        "Out of scope",
    ],
    "docs/project_memory/development_workflow.md": [
        "OLLAMA_BASE_URL",
        "Windows owns source-of-truth repo work",
        "Linux owns runtime/staging QA",
    ],
}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def run_project_memory_check(project_root: Path | str = ".") -> list[MemoryCheckResult]:
    """Return PASS/WARN/FAIL project-memory consistency results."""
    root = Path(project_root)
    results: list[MemoryCheckResult] = []

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if path.exists():
            results.append(
                MemoryCheckResult("PASS", relative_path, "Required file exists.")
            )
        else:
            results.append(
                MemoryCheckResult("FAIL", relative_path, "Required file is missing.")
            )

    claude_path = root / "CLAUDE.md"
    if claude_path.exists():
        results.append(
            MemoryCheckResult(
                "FAIL",
                "CLAUDE.md",
                "Claude-specific workflow file is out of scope for this project.",
            )
        )
    else:
        results.append(
            MemoryCheckResult("PASS", "CLAUDE.md", "Claude workflow file absent.")
        )

    for relative_path, phrases in REQUIRED_PHRASES.items():
        path = root / relative_path
        if not path.exists():
            continue
        text = _read_text(path)
        for phrase in phrases:
            if phrase in text:
                results.append(
                    MemoryCheckResult(
                        "PASS", relative_path, f"Contains required phrase: {phrase}"
                    )
                )
            else:
                results.append(
                    MemoryCheckResult(
                        "WARN", relative_path, f"Missing expected phrase: {phrase}"
                    )
                )

    for relative_path, markers in STALE_MARKERS.items():
        path = root / relative_path
        if not path.exists():
            continue
        text = _read_text(path)
        for marker in markers:
            if marker in text:
                results.append(
                    MemoryCheckResult(
                        "WARN",
                        relative_path,
                        f"Possible stale milestone wording found: {marker}",
                    )
                )

    return results


def format_results(results: list[MemoryCheckResult]) -> str:
    lines = ["Project memory check results:"]
    for result in results:
        lines.append(f"[{result.status}] {result.path} — {result.message}")
    summary = summarize_results(results)
    lines.append("")
    lines.append(
        "Summary: "
        f"PASS={summary['PASS']} WARN={summary['WARN']} FAIL={summary['FAIL']}"
    )
    return "\n".join(lines)


def summarize_results(results: list[MemoryCheckResult]) -> dict[str, int]:
    return {
        "PASS": sum(result.status == "PASS" for result in results),
        "WARN": sum(result.status == "WARN" for result in results),
        "FAIL": sum(result.status == "FAIL" for result in results),
    }


def has_failures(results: list[MemoryCheckResult]) -> bool:
    return any(result.status == "FAIL" for result in results)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run read-only AI Health Coach project-memory checks."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root to inspect. Defaults to current directory.",
    )
    args = parser.parse_args()

    results = run_project_memory_check(args.project_root)
    print(format_results(results))
    return 1 if has_failures(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
