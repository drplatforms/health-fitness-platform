from __future__ import annotations

from pathlib import Path

from tools.project_memory_check import (
    REQUIRED_FILES,
    has_failures,
    run_project_memory_check,
    summarize_results,
)


def write_required_project_memory(root: Path) -> None:
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        text = "placeholder\n"
        if relative_path == "AGENTS.md":
            text = (
                "docs/project_memory\n"
                "Backend owns facts\n"
                "Deterministic fallback remains the default\n"
                "Do not add `CLAUDE.md`\n"
            )
        elif relative_path == ".github/copilot-instructions.md":
            text = (
                "Backend owns facts\n"
                "Preserve deterministic fallback behavior\n"
                "Do not add Claude workflow files\n"
            )
        elif relative_path == "docs/project_memory/agent_workflow.md":
            text = "ChatGPT\nCodex\nDev Assistant\nClaude\nOut of scope\n"
        elif relative_path == "docs/project_memory/development_workflow.md":
            text = (
                "OLLAMA_BASE_URL\n"
                "Windows owns source-of-truth repo work\n"
                "Linux owns runtime/staging QA\n"
            )
        path.write_text(text, encoding="utf-8")


def test_project_memory_check_passes_when_required_docs_exist(tmp_path: Path) -> None:
    write_required_project_memory(tmp_path)

    results = run_project_memory_check(tmp_path)
    summary = summarize_results(results)

    assert not has_failures(results)
    assert summary["FAIL"] == 0
    assert any(result.path == "AGENTS.md" for result in results)


def test_project_memory_check_fails_when_required_doc_is_missing(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/current_state.md").unlink()

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL"
        and result.path == "docs/project_memory/current_state.md"
        for result in results
    )


def test_project_memory_check_fails_if_claude_file_exists(tmp_path: Path) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("not allowed\n", encoding="utf-8")

    results = run_project_memory_check(tmp_path)

    assert has_failures(results)
    assert any(
        result.status == "FAIL" and result.path == "CLAUDE.md" for result in results
    )


def test_project_memory_check_warns_on_stale_current_state_marker(
    tmp_path: Path,
) -> None:
    write_required_project_memory(tmp_path)
    (tmp_path / "docs/project_memory/current_state.md").write_text(
        "Latest accepted milestone\n\n"
        "`Daily Coach Narrative Developer Preview v1`\n",
        encoding="utf-8",
    )

    results = run_project_memory_check(tmp_path)

    assert any(
        result.status == "WARN"
        and result.path == "docs/project_memory/current_state.md"
        and "Possible stale milestone wording" in result.message
        for result in results
    )
