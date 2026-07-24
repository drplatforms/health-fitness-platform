from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_PATH = ROOT / "scripts" / "fitness_commands.ps1"
FRONTEND_PACKAGE_PATH = ROOT / "frontend" / "package.json"
REMOTE_VALIDATOR_PATH = ROOT / "frontend" / "scripts" / "validate-remote-access.mjs"


def _function_body(source: str, name: str) -> str:
    match = re.search(
        rf"(?im)^function\s+{re.escape(name)}\s*\{{",
        source,
    )
    assert match is not None, f"Missing PowerShell function {name}"
    depth = 0
    for index in range(match.end() - 1, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start() : index + 1]
    raise AssertionError(f"Unterminated PowerShell function {name}")


def test_normal_launchers_are_loopback_only_and_shared_mode_is_explicit() -> None:
    commands = COMMANDS_PATH.read_text(encoding="utf-8")
    package = json.loads(FRONTEND_PACKAGE_PATH.read_text(encoding="utf-8"))
    scripts = package["scripts"]

    assert '"--host", "127.0.0.1"' in _function_body(commands, "fapi")
    assert "--hostname 127.0.0.1" in scripts["dev"]
    assert "--hostname 127.0.0.1" in scripts["start"]
    assert "--hostname 0.0.0.0" in scripts["dev:shared"]
    assert "--hostname 0.0.0.0" in scripts["start:shared"]
    assert "--require-remote" in scripts["predev:shared"]
    assert "--require-remote" in scripts["prestart:shared"]

    for name in ("ffront", "ffrontbuild", "fnext", "fnextfg", "fstart", "app"):
        body = _function_body(commands, name)
        assert "[switch]$Shared" in body
        assert "--hostname 0.0.0.0" not in body

    resolver = _function_body(commands, "Resolve-FitnessFrontendBindAddress")
    assert "Assert-FitnessRemoteAccessConfiguration" in resolver
    assert "-RequireEnabled:$Shared" in resolver
    assert 'if ($Shared) { return "0.0.0.0" }' in resolver


def test_shared_launcher_configuration_fails_closed_without_leaking_secrets() -> None:
    commands = COMMANDS_PATH.read_text(encoding="utf-8")
    guard = _function_body(commands, "Assert-FitnessRemoteAccessConfiguration")
    banner = _function_body(commands, "Write-FitnessFrontendSecurityBanner")

    for name in (
        "FITNESS_REMOTE_ACCESS_ENABLED",
        "FITNESS_BASIC_AUTH_USER",
        "FITNESS_BASIC_AUTH_PASSWORD",
        "FITNESS_PUBLIC_ORIGIN",
    ):
        assert name in guard
    assert 'Scheme -ne "https"' in guard
    assert "PathAndQuery" in guard
    assert "SHARED MODE" in banner
    assert "do not expose this as a public or multi-user service" in banner
    assert "FITNESS_BASIC_AUTH_PASSWORD" not in banner


def test_remote_validator_covers_build_start_and_shared_commands() -> None:
    package = json.loads(FRONTEND_PACKAGE_PATH.read_text(encoding="utf-8"))
    scripts = package["scripts"]

    assert scripts["prebuild"] == "node scripts/validate-remote-access.mjs"
    assert scripts["prestart"] == "node scripts/validate-remote-access.mjs"
    assert scripts["predev"] == "node scripts/validate-remote-access.mjs"

    local = _run_remote_validator({"FITNESS_REMOTE_ACCESS_ENABLED": "false"})
    assert local.returncode == 0

    missing = _run_remote_validator({"FITNESS_REMOTE_ACCESS_ENABLED": "true"})
    assert missing.returncode == 1
    assert "incomplete or invalid" in missing.stderr

    private_sentinel = "PRIVATE_PASSWORD_SENTINEL"
    valid = _run_remote_validator(
        {
            "FITNESS_REMOTE_ACCESS_ENABLED": "true",
            "FITNESS_BASIC_AUTH_USER": "private-user",
            "FITNESS_BASIC_AUTH_PASSWORD": private_sentinel,
            "FITNESS_PUBLIC_ORIGIN": "https://fitness.example.internal",
        }
    )
    assert valid.returncode == 0
    assert private_sentinel not in valid.stdout
    assert private_sentinel not in valid.stderr

    shared_without_remote = _run_remote_validator(
        {"FITNESS_REMOTE_ACCESS_ENABLED": "false"},
        "--require-remote",
    )
    assert shared_without_remote.returncode == 1


def test_environment_and_caddy_guidance_define_private_single_user_topology() -> None:
    root_environment = (ROOT / ".env.example").read_text(encoding="utf-8")
    frontend_environment = (ROOT / "frontend" / ".env.local.example").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "readme.md").read_text(encoding="utf-8")
    normalized_readme = " ".join(readme.split())

    for source in (root_environment, frontend_environment):
        assert "FITNESS_REMOTE_ACCESS_ENABLED=false" in source
        assert "FITNESS_BASIC_AUTH_USER=" in source
        assert "FITNESS_BASIC_AUTH_PASSWORD=" in source
        assert "FITNESS_PUBLIC_ORIGIN=" in source

    assert "reverse_proxy 127.0.0.1:3100" in readme
    assert "Do not proxy port `8000`" in readme
    assert "not public-Internet or multi-user SaaS authentication" in normalized_readme


def _run_remote_validator(
    values: dict[str, str],
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    for name in (
        "FITNESS_REMOTE_ACCESS_ENABLED",
        "FITNESS_BASIC_AUTH_USER",
        "FITNESS_BASIC_AUTH_PASSWORD",
        "FITNESS_PUBLIC_ORIGIN",
    ):
        environment.pop(name, None)
    environment.update(values)
    return subprocess.run(
        ["node", str(REMOTE_VALIDATOR_PATH), *arguments],
        cwd=ROOT / "frontend",
        env=environment,
        capture_output=True,
        check=False,
        text=True,
    )
