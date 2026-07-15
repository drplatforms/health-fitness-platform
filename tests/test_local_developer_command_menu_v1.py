from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_PATH = ROOT / "scripts" / "fitness_commands.ps1"
INSTALLER_PATH = ROOT / "scripts" / "install_fitness_commands_profile.ps1"
MENU_DOC_PATH = ROOT / "docs" / "project_memory" / "local_developer_command_menu.md"
WORKFLOW_PATH = ROOT / "docs" / "project_memory" / "current_workflow_contract.md"
PROJECT_STATE_PATH = ROOT / "docs" / "project_memory" / "project_state.json"


@pytest.fixture(scope="module")
def commands() -> str:
    return COMMANDS_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def installer() -> str:
    return INSTALLER_PATH.read_text(encoding="utf-8")


def function_body(source: str, name: str) -> str:
    match = re.search(
        rf"(?ims)^function\s+{re.escape(name)}\s*\{{(?P<body>.*?)(?=^function\s+|\Z)",
        source,
    )
    assert match, f"missing function {name}"
    return match.group("body")


def test_repo_owned_scripts_exist() -> None:
    assert COMMANDS_PATH.is_file()
    assert INSTALLER_PATH.is_file()


def test_primary_command_contract_is_complete(commands: str) -> None:
    required = {
        "fitness",
        "fhelp",
        "cdf",
        "cdff",
        "fapi",
        "fkillapi",
        "ffront",
        "ffrontbuild",
        "fvalidatefront",
        "fkillfront",
        "fnext",
        "fnextfg",
        "fstart",
        "frestart",
        "fports",
        "fopen",
        "app",
        "wapp",
        "wstatus",
        "wstop",
        "fsnap",
        "fbranch",
        "fmerge",
        "fmem",
        "fdoctor",
    }
    for name in required:
        assert re.search(rf"(?im)^function\s+{re.escape(name)}\s*\{{", commands)


def test_canonical_functions_are_defined_exactly_once(commands: str) -> None:
    names = re.findall(r"(?im)^function\s+([\w-]+)\s*\{", commands)
    duplicates = sorted({name for name in names if names.count(name) > 1})
    assert duplicates == []
    assert names.count("Get-FitnessWindowsPython") == 1


def test_paths_snapshot_location_and_brand_are_current(commands: str) -> None:
    assert "Health & Fitness Platform" in commands
    assert "C:\\projects\\fitness_ai" in commands
    assert "C:\\projects\\fitness_ai_external\\snapshots" in commands
    assert "~/projects/fitness-ai-platform" in commands
    assert "AI Health Coach" not in commands


def test_primary_ports_and_product_url_are_current(commands: str) -> None:
    assert "FitnessApiPort = 8000" in commands
    assert "FitnessFrontendPort" in commands and "3100" in commands
    assert "FitnessNextDevPort" in commands and "3000" in commands
    assert "http://127.0.0.1:$script:FitnessFrontendPort" in commands
    assert '"--host", "127.0.0.1"' in function_body(commands, "fapi")
    assert "api.main:app" in function_body(commands, "fapi")
    assert "apps.api.app.main:app" not in commands
    ports = function_body(commands, "fports")
    assert "FastAPI (primary)" in ports
    assert "Next.js production (primary)" in ports
    assert "Next.js development (optional)" in ports
    assert "11434" in ports
    assert "8501" not in ports


def test_app_starts_only_the_primary_windows_runtime(commands: str) -> None:
    app = function_body(commands, "app")
    start = function_body(commands, "fstart")
    assert "fstart" in app
    assert "fapi" in start and "ffront" in start
    forbidden = ("ssh", "streamlit", "lpull", "lrestart", "lupdate")
    assert not any(term in (app + start).lower() for term in forbidden)


def test_production_frontend_commands_have_distinct_semantics(commands: str) -> None:
    front = function_body(commands, "ffront")
    build = function_body(commands, "ffrontbuild")
    validate = function_body(commands, "fvalidatefront")
    assert 'Join-Path $script:FitnessFrontendDir ".next"' in front
    assert "npm run start" in front and "FitnessFrontendPort" in front
    assert "npm run build" in build and "ffront" in build
    assert "npm run lint" in validate and "npm run build" in validate
    assert "Start-Process" not in validate and "ffront" not in validate


def test_next_development_server_is_explicitly_optional(commands: str) -> None:
    next_background = function_body(commands, "fnext")
    next_foreground = function_body(commands, "fnextfg")
    assert "npm run dev" in next_background
    assert "Start-Process" in next_background
    assert "optional" in next_background.lower()
    assert "npm run dev" in next_foreground
    assert "Start-Process" not in next_foreground


def test_runtime_stop_helpers_verify_listener_ownership(commands: str) -> None:
    ownership = function_body(commands, "Stop-FitnessOwnedListener")
    assert "Get-NetTCPConnection" in ownership
    assert "OwningProcess" in ownership
    assert "Get-FitnessProcessChain" in ownership
    assert "FitnessWindowsRepo" in ownership
    assert "ExpectedCommandPattern" in ownership
    assert "Refusing to stop" in ownership
    assert "Stop-Process" in ownership
    for name in ("fkillapi", "fkillfront", "fkillnext"):
        body = function_body(commands, name)
        assert "Stop-FitnessOwnedListener" in body
        assert "ExpectedCommandPattern" in body
    assert "api\\.main:app" in function_body(commands, "fkillapi")
    assert "next-server" in function_body(commands, "fkillfront")
    assert "run\\s+dev" in function_body(commands, "fkillnext")


def test_primary_runtime_commands_refuse_duplicate_listeners(commands: str) -> None:
    guard = function_body(commands, "Assert-FitnessPortAvailable")
    assert "Get-NetTCPConnection" in guard
    assert "already listening" in guard
    for name in ("fapi", "ffront", "fnext", "fnextfg"):
        assert "Assert-FitnessPortAvailable" in function_body(commands, name)


def test_snapshot_requires_clean_main_and_external_directory(commands: str) -> None:
    snapshot = function_body(commands, "fsnap")
    assert "Assert-FitnessCleanTree" in snapshot
    assert '(Get-FitnessBranch) -ne "main"' in snapshot
    assert "FitnessSnapshotDir" in snapshot
    assert "git archive" in snapshot
    assert "fitness_ai_snapshot_${date}_${commit}_main_${Slug}.zip" in snapshot
    assert "git add" not in snapshot


def test_gacp_preserves_explicit_staging_and_refuses_main(commands: str) -> None:
    commit = function_body(commands, "gacp")
    assert "git add" not in commit
    assert "No files are staged automatically" in commit
    assert "AllowMain" in commit
    assert '$branch -eq "main" -and -not $AllowMain' in commit
    assert "Refusing to commit on main" in commit


def test_fpull_and_fbranch_require_current_clean_main(commands: str) -> None:
    pull = function_body(commands, "fpull")
    for phrase in (
        "Assert-FitnessCleanTree",
        "fetch origin --prune",
        "switch main",
        "pull --ff-only origin main",
        "Assert-FitnessMainMatchesOrigin",
    ):
        assert phrase in pull
    assert "fpull" in function_body(commands, "gsync")

    branch = function_body(commands, "fbranch")
    for phrase in (
        "fetch origin --prune",
        "switch main",
        "pull --ff-only origin main",
        "Assert-FitnessMainMatchesOrigin",
        "Assert-FitnessCleanTree",
        "switch -c $Name",
    ):
        assert phrase in branch


def test_fmerge_requires_exact_accepted_commit_ancestry(commands: str) -> None:
    merge = function_body(commands, "fmerge")
    assert "AcceptedFinalCommit" in merge
    assert "fetch origin --prune" in merge
    assert "pull --ff-only origin main" in merge
    assert "Assert-FitnessMainMatchesOrigin" in merge
    assert "merge --no-ff $FeatureBranch" in merge
    assert "git merge-base --is-ancestor" in merge
    assert "git merge-base --is-ancestor $AcceptedFinalCommit main" in merge
    assert "git merge-base --is-ancestor $FeatureBranch main" not in merge
    assert "do not push or snapshot" in merge


def test_fsweep_is_artifact_contamination_scan(commands: str) -> None:
    sweep = function_body(commands, "fsweep")
    assert "git grep -n -E" in sweep
    for marker in (
        '"content" + "Reference"',
        '"oai" + "cite"',
        '"file" + "cite"',
        '"tool" + "cite"',
        '"turn[0-9]+',
        '"<paste latest commit>"',
        '"<paste snapshot filename>"',
    ):
        assert marker in sweep
    assert "git branch --merged main" not in sweep
    assert "git branch --merged main" in function_body(commands, "fbranches")


def test_gcheck_runs_meaningful_repository_validation(commands: str) -> None:
    check = function_body(commands, "gcheck")
    for phrase in (
        "git diff --check",
        "scripts\\dev_commit_check.ps1",
        "tools\\project_memory_check.py",
        "tests\\test_project_memory_check.py",
        "memory-check",
        "stale-doc-check",
    ):
        assert phrase in check
    assert "git status --short --untracked-files=all" in check


def test_fmem_runs_full_current_memory_workflow(commands: str) -> None:
    memory = function_body(commands, "fmem")
    for phrase in (
        "tools\\project_memory_check.py",
        "memory-check",
        "stale-doc-check",
        "continuity-brief",
        "tests\\test_project_memory_check.py",
    ):
        assert phrase in memory


def test_linux_helpers_are_secondary_and_not_streamlit_runtime(commands: str) -> None:
    for name in ("lpull", "lstatus", "lsetup", "lvalidate", "lollama", "lsh"):
        assert re.search(rf"(?im)^function\s+{name}\s*\{{", commands)
    assert "Secondary Linux helpers" in commands
    assert "Linux is optional validation/runtime/demo infrastructure" in commands
    assert "streamlit run" not in commands.lower()
    assert "FITNESS_LINUX_STREAMLIT" not in commands


def test_installer_is_safe_idempotent_and_explicit(installer: str) -> None:
    assert "Health & Fitness Platform command menu" in installer
    assert "ProfilePath = $PROFILE" in installer
    assert "ReplaceProfileWithThinLoader" in installer
    assert "Copy-Item" in installer
    assert "backup." in installer
    assert "managedPatterns" in installer
    assert "Existing non-managed profile content was preserved" in installer
    assert (
        "AI Health Coach command menu" in installer
    )  # recognized migration marker only


def test_installer_preserves_content_by_default_and_can_opt_in_to_thin_loader(
    tmp_path: Path,
) -> None:
    profile = tmp_path / "Microsoft.PowerShell_profile.ps1"
    profile.write_text("function Keep-Me { 'keep' }\n", encoding="utf-8")
    command = [
        "pwsh",
        "-NoProfile",
        "-File",
        str(INSTALLER_PATH),
        "-ProfilePath",
        str(profile),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    installed = profile.read_text(encoding="utf-8-sig")
    assert "function Keep-Me" in installed
    assert installed.count("# >>> Health & Fitness Platform command menu >>>") == 1
    assert list(tmp_path.glob("Microsoft.PowerShell_profile.ps1.backup.*"))

    subprocess.run(
        [*command, "-ReplaceProfileWithThinLoader"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    simplified = profile.read_text(encoding="utf-8-sig")
    assert "function Keep-Me" not in simplified
    assert simplified.count("# >>> Health & Fitness Platform command menu >>>") == 1


def test_current_docs_match_command_semantics() -> None:
    menu = MENU_DOC_PATH.read_text(encoding="utf-8")
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    for text in (menu, workflow):
        assert "Health & Fitness Platform" in text
        assert "C:\\projects\\fitness_ai" in text
        assert "http://127.0.0.1:3100" in text
        assert "C:\\projects\\fitness_ai_external\\snapshots" in text
        assert "Streamlit is legacy/developer-only" in text
    assert "Linux sync is optional" in workflow
    assert "-ReplaceProfileWithThinLoader" in menu


def test_project_state_current_pointers_match_active_milestone() -> None:
    state = json.loads(PROJECT_STATE_PATH.read_text(encoding="utf-8"))
    assert state["project"]["name"] == "Health & Fitness Platform"
    assert state["project"]["repo"] == "health-fitness-platform"
    assert state["project"]["platform_repo"] == "health-fitness-platform"
    assert state["current_baseline"]["latest_accepted_commit"] == "c8349e0"
    assert (
        state["active_roadmap"]["current_authorized_milestone"]
        == "Project Memory + Developer Workflow Canonicalization v1"
    )
    assert (
        state["requested_backend_status"]
        == "NO_APPLICATION_BACKEND_MILESTONE_AUTHORIZED"
    )
    assert (
        state["status"]["active_backend_status"]
        == "NO_APPLICATION_BACKEND_MILESTONE_AUTHORIZED"
    )
    assert (
        state["status"]["active_project_memory_status"]
        == "PROJECT_MEMORY_DEVELOPER_WORKFLOW_CANONICALIZATION_V1_IN_PROGRESS"
    )
    assert (
        "fresh Architecture chat"
        in state["architecture_direction"]["next_center_of_gravity"]
    )


def test_current_command_layer_contains_no_secrets_or_external_citations(
    commands: str, installer: str
) -> None:
    combined = commands + installer
    assert not re.search(r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]+", combined)
    assert "http://" not in installer and "https://" not in installer
