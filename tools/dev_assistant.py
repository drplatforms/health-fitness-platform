"""Developer workflow assistant for AI Health Coach.

This script is intentionally read-only. It summarizes local Git state and
suggests safe next actions without modifying files, committing, or pushing.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def run_command(command: list[str]) -> CommandResult:
    """Run a shell command and capture output."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    return CommandResult(
        command=command,
        returncode=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def get_output(command: list[str], fallback: str = "Unavailable") -> str:
    result = run_command(command)

    if result.returncode != 0:
        return fallback

    return result.stdout or fallback


def get_current_branch() -> str:
    return get_output(["git", "branch", "--show-current"])


def get_latest_commit() -> str:
    return get_output(["git", "log", "-1", "--oneline", "--decorate"])


def get_recent_commits() -> str:
    return get_output(["git", "log", "--oneline", "--decorate", "-7"])


def get_short_status() -> str:
    return get_output(["git", "status", "--short"], fallback="")


def get_full_status() -> str:
    return get_output(["git", "status"])


def get_diff_stat() -> str:
    return get_output(["git", "diff", "--stat"], fallback="")


def get_staged_diff_stat() -> str:
    return get_output(["git", "diff", "--cached", "--stat"], fallback="")


def get_upstream_status() -> str:
    return get_output(["git", "status", "-sb"])


def recommend_next_action(short_status: str, upstream_status: str) -> str:
    if short_status:
        return (
            "Working tree has changes. Recommended next step:\n"
            "1. Review changes with: git status\n"
            "2. Review summary with: git diff --stat\n"
            "3. Run checks before committing: pre-commit run --all-files"
        )

    if "ahead" in upstream_status and "behind" in upstream_status:
        return (
            "Branch is both ahead and behind its upstream. Recommended next step:\n"
            "1. Stop and inspect carefully.\n"
            "2. Run: git status\n"
            "3. Ask for help before pulling, rebasing, or pushing."
        )

    if "ahead" in upstream_status:
        return (
            "Branch has local commits not pushed yet. Recommended next step:\n"
            "1. Push the branch.\n"
            "2. Open or update the pull request."
        )

    if "behind" in upstream_status:
        return (
            "Branch is behind its upstream. Recommended next step:\n"
            "1. Pull latest changes with: git pull\n"
            "2. Re-run tests/checks after pulling."
        )

    return (
        "Working tree is clean. Recommended next step:\n"
        "1. Start a new feature branch, or\n"
        "2. Continue work on this branch, or\n"
        "3. Generate a milestone handoff."
    )


def main() -> None:
    branch = get_current_branch()
    latest_commit = get_latest_commit()
    recent_commits = get_recent_commits()
    short_status = get_short_status()
    full_status = get_full_status()
    diff_stat = get_diff_stat()
    staged_diff_stat = get_staged_diff_stat()
    upstream_status = get_upstream_status()
    next_action = recommend_next_action(short_status, upstream_status)

    print_section("AI Health Coach — Developer Workflow Assistant")

    print(f"Branch:\n{branch}")
    print()
    print(f"Latest commit:\n{latest_commit}")

    print_section("Git upstream/status summary")
    print(upstream_status)

    print_section("Working tree")
    if short_status:
        print(short_status)
    else:
        print("Clean — no uncommitted changes.")

    print_section("Unstaged diff summary")
    if diff_stat:
        print(diff_stat)
    else:
        print("No unstaged diff.")

    print_section("Staged diff summary")
    if staged_diff_stat:
        print(staged_diff_stat)
    else:
        print("No staged diff.")

    print_section("Recent commits")
    print(recent_commits)

    print_section("Suggested next action")
    print(next_action)

    print_section("Full git status")
    print(full_status)


if __name__ == "__main__":
    main()
