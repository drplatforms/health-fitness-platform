from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from tools import project_memory_check


def load_dev_assistant():
    module_path = Path("tools/dev_assistant.py")
    spec = importlib.util.spec_from_file_location("dev_assistant", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["dev_assistant"] = module
    spec.loader.exec_module(module)
    return module


def run_dev_assistant(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/dev_assistant.py", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_session_brief_command_is_discoverable() -> None:
    result = run_dev_assistant("--help")

    assert result.returncode == 0
    assert "session-brief" in result.stdout

    result = run_dev_assistant("session-brief", "--help")

    assert result.returncode == 0
    assert "--out" in result.stdout


def test_session_brief_writes_utf8_output(tmp_path: Path) -> None:
    dev_assistant = load_dev_assistant()
    output_path = tmp_path / "session_brief.txt"

    dev_assistant.write_session_brief(
        str(output_path),
        milestone="Supercharger v1.1 - Session Brief Command",
    )

    assert output_path.exists()

    output = output_path.read_text(encoding="utf-8")

    required_sections = [
        "Health & Fitness Platform",
        "Git Status",
        "Recent Commits",
        "Dev Assistant Status",
        "Memory Check",
        "Stale Doc Check",
        "Suggested Next Action",
        "Snapshot Command",
        "Optional Linux Sync",
    ]

    for section in required_sections:
        assert section in output

    assert "Supercharger v1.1 - Session Brief Command" in output


def test_session_brief_avoids_known_bad_characters(tmp_path: Path) -> None:
    dev_assistant = load_dev_assistant()
    output_path = tmp_path / "session_brief.txt"

    dev_assistant.write_session_brief(str(output_path))

    output = output_path.read_text(encoding="utf-8")

    assert "ù" not in output
    assert "\f" not in output


def test_session_brief_does_not_mutate_source_files(tmp_path: Path) -> None:
    dev_assistant = load_dev_assistant()
    source_files = [
        Path("tools/dev_assistant.py"),
        Path("docs/project_memory/development_workflow.md"),
    ]
    before = {path: path.read_bytes() for path in source_files}

    output_path = tmp_path / "session_brief.txt"
    dev_assistant.write_session_brief(str(output_path))

    assert output_path.exists()

    after = {path: path.read_bytes() for path in source_files}
    assert after == before


def test_continuity_brief_uses_current_identity_runtime_and_workflow() -> None:
    dev_assistant = load_dev_assistant()

    output = dev_assistant.generate_continuity_brief()

    required = [
        "Project: Health & Fitness Platform / health-fitness-platform",
        "Latest accepted commit: c8349e0",
        "Project Memory + Developer Workflow Canonicalization v1",
        "FastAPI on 8000 plus production Next.js on 3100",
        "http://127.0.0.1:3100",
        "Secondary/back-burner optional validation",
        "AI-written daily coaching prose is paused indefinitely",
        "Use medium phases",
        "docs/project_memory/current_workflow_contract.md",
    ]
    for phrase in required:
        assert phrase in output

    assert "Authority hierarchy" in output
    assert "Canonical source hierarchy" in output
    assert "qwen" not in output.lower()
    assert "Daily Coach async boundary" not in output


def test_generic_defaults_and_source_docs_are_current() -> None:
    dev_assistant = load_dev_assistant()

    assert dev_assistant.DEFAULT_BASE_BRANCHES == ["main", "origin/main"]
    assert "AGENTS.md" in dev_assistant.SOURCE_OF_TRUTH_DOCS
    assert "docs/project_memory/current_workflow_contract.md" in (
        dev_assistant.SOURCE_OF_TRUTH_DOCS
    )
    assert "docs/project_memory/project_continuity_bootstrap.md" not in (
        dev_assistant.SOURCE_OF_TRUTH_DOCS
    )
    assert not any(
        path.startswith("docs/project_memory/handoffs/")
        for path in dev_assistant.SOURCE_OF_TRUTH_DOCS
    )
    assert (
        "docs/project_memory/milestones/project_memory_developer_workflow_canonicalization_v1.md"
        in dev_assistant.get_source_of_truth_docs()
    )


def test_generic_test_recommendations_are_risk_based() -> None:
    dev_assistant = load_dev_assistant()

    safety_text = "\n".join(dev_assistant.FOCUSED_SAFETY_TESTS)
    assert "Daily Coach" not in safety_text
    assert "pre-commit run --all-files" not in safety_text

    frontend = dev_assistant.recommend_tests(["frontend/src/app/page.tsx"])
    assert "cd frontend && npm run lint" in frontend
    assert "cd frontend && npm run build" in frontend
    assert any("127.0.0.1:3100" in item for item in frontend)
    assert "pytest -q" not in frontend

    legacy_ui = dev_assistant.recommend_tests(["ui/app.py"])
    assert any("Legacy UI/developer tooling" in item for item in legacy_ui)
    assert not any("Streamlit" in item for item in legacy_ui)


def test_routing_distinguishes_active_frontend_from_legacy_ui() -> None:
    dev_assistant = load_dev_assistant()

    assert dev_assistant.suggest_recipient_chat(["frontend/src/app/page.tsx"]) == (
        "Frontend"
    )
    assert dev_assistant.suggest_recipient_chat(["ui/app.py"]) == (
        "Legacy UI / Developer Tooling"
    )


def test_runtime_restart_is_windows_nextjs_first() -> None:
    dev_assistant = load_dev_assistant()

    output = dev_assistant.generate_runtime_restart_commands()
    lowered = output.lower()

    for command in ["cdf", "fkillapi", "fkillfront", "fapi", "ffront"]:
        assert command in output
    assert "127.0.0.1:3100" in output
    assert "port 3000" in output
    for forbidden in ["ollama", "qwen", "provider", "streamlit"]:
        assert forbidden not in lowered

    help_result = run_dev_assistant("runtime-restart", "--help")
    assert help_result.returncode == 0
    assert "--ollama-base-url" not in help_result.stdout


def test_agent_prompt_and_context_pack_use_current_contracts() -> None:
    dev_assistant = load_dev_assistant()

    prompt = dev_assistant.generate_agent_prompt("codex", "Example Milestone v1")
    assert "Health & Fitness Platform" in prompt
    assert "Backend owns facts" in prompt
    assert "targeted validation" in prompt
    assert "fitness_ai.db" in prompt
    assert "qwen" not in prompt.lower()
    assert "ollama" not in prompt.lower()

    context = dev_assistant.generate_context_pack("codex", "Example Milestone v1")
    assert "Canonical Windows environment" in context
    assert "Production Next.js: http://127.0.0.1:3100" in context
    assert "Linux at ~/projects/fitness-ai-platform is optional" in context
    assert "Streamlit is legacy/developer-only" in context
    assert "OLLAMA_BASE_URL" not in context


def test_qa_plan_is_generic_and_risk_based() -> None:
    dev_assistant = load_dev_assistant()

    output = dev_assistant.generate_qa_plan("Example Milestone v1")

    assert "Risk-based validation" in output
    assert "active handoff" in output
    assert "production-mode browser smoke" in output
    assert "provider defaults" not in output.lower()
    assert "raw provider" not in output.lower()
    assert "pre-commit run --all-files" not in output
    assert "pytest -q" not in output


def test_next_milestone_requires_roadmap_and_fresh_architecture_selection() -> None:
    text = Path("docs/project_memory/next_milestone.md").read_text(encoding="utf-8")
    top = text.split("# Historical Next Milestone", maxsplit=1)[0]

    assert "Project Memory + Developer Workflow Canonicalization v1" in top
    assert "user provide the rough current product roadmap" in top
    assert "fresh Architecture chat" in top
    assert "select the next narrow product milestone" in top
    assert "No next product milestone is authorized" in top
    assert "candidate only after" in top

    state = json.loads(
        Path("docs/project_memory/project_state.json").read_text(encoding="utf-8")
    )
    recommendation = state["active_roadmap"][
        "recommended_next_milestone_after_acceptance"
    ]
    assert "rough current product roadmap" in recommendation
    assert "fresh Architecture chat" in recommendation
    assert "Exercise Instruction" not in recommendation


def test_checker_no_longer_pins_obsolete_current_pointer_phrases() -> None:
    assert "docs/project_memory/project_continuity_bootstrap.md" not in (
        project_memory_check.REQUIRED_PHRASES
    )
    for path in [
        "docs/project_memory/handoffs/architecture_handoff_current.md",
        "docs/project_memory/handoffs/backend_handoff_current.md",
        "docs/project_memory/handoffs/qa_handoff_current.md",
    ]:
        assert path not in project_memory_check.REQUIRED_PHRASES

    current_state_phrases = project_memory_check.REQUIRED_PHRASES[
        "docs/project_memory/current_state.md"
    ]
    assert "Health & Fitness Platform" in current_state_phrases
    assert "Linux is the canonical" not in current_state_phrases
    assert "Local Command Menu App Runtime Correction v1" not in current_state_phrases
