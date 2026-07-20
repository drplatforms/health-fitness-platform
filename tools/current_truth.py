"""Validate and render the authoritative operational current-truth kernel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
CURRENT_TRUTH_PATH = Path("docs/project_memory/current_truth.json")
GENERATED_VIEW_PATH = Path("docs/project_memory/current_truth.md")
GENERATED_VIEW_HEADER = (
    "GENERATED VIEW\n"
    "Authoritative source: docs/project_memory/current_truth.json\n"
    "Do not edit manually."
)
ACTIVE_MILESTONE_STATUSES = {
    "IMPLEMENTATION_AUTHORIZED",
    "IMPLEMENTATION_IN_PROGRESS",
    "READY_FOR_ARCHITECTURE_REVIEW",
    "NO_IMPLEMENTATION_AUTHORIZED",
}
IMPLEMENTATION_AUTHORIZATION_STATUSES = {"AUTHORIZED", "NOT_AUTHORIZED"}
AUTHORIZED_MILESTONE_STATUSES = ACTIVE_MILESTONE_STATUSES - {
    "NO_IMPLEMENTATION_AUTHORIZED"
}
REQUIRED_STRING_FIELDS = (
    "project_id",
    "canonical_repository",
    "canonical_branch",
)
REQUIRED_OBJECT_FIELDS = {
    "current_initiative": ("id", "name", "status"),
    "active_milestone": ("id", "name", "status"),
    "implementation_authorization": ("status", "authority", "scope"),
    "immediate_next_priority": ("id", "name", "status"),
}


def load_current_truth(project_root: Path | str = ".") -> dict[str, Any]:
    """Load the current-truth JSON object or raise a descriptive ValueError."""
    path = Path(project_root) / CURRENT_TRUTH_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(
            f"Current-truth kernel is missing: {CURRENT_TRUTH_PATH}"
        ) from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Current-truth kernel is invalid: {exc}") from exc

    if not isinstance(value, dict):
        raise ValueError("Current-truth kernel must be a JSON object.")
    return value


def validate_current_truth(value: object, project_root: Path | str = ".") -> list[str]:
    """Return deterministic validation errors for a current-truth value."""
    if not isinstance(value, dict):
        return ["Current-truth kernel must be a JSON object."]

    errors: list[str] = []
    schema_version = value.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        errors.append(
            f"Unsupported schema_version {schema_version!r}; expected {SCHEMA_VERSION}."
        )

    for field in REQUIRED_STRING_FIELDS:
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"Required field {field!r} must be a non-empty string.")

    for field, nested_fields in REQUIRED_OBJECT_FIELDS.items():
        nested = value.get(field)
        if not isinstance(nested, dict):
            errors.append(f"Required field {field!r} must be an object.")
            continue
        for nested_field in nested_fields:
            nested_value = nested.get(nested_field)
            if not isinstance(nested_value, str) or not nested_value.strip():
                errors.append(
                    f"Required field {field}.{nested_field} must be a non-empty string."
                )

    active_milestone = value.get("active_milestone")
    milestone_status: object = None
    if isinstance(active_milestone, dict):
        milestone_status = active_milestone.get("status")
        if (
            isinstance(milestone_status, str)
            and milestone_status not in ACTIVE_MILESTONE_STATUSES
        ):
            errors.append(
                "active_milestone.status must describe active implementation, not "
                "future, completed, accepted, or inactive work."
            )

    implementation_authorization = value.get("implementation_authorization")
    authorization_status: object = None
    if isinstance(implementation_authorization, dict):
        authorization_status = implementation_authorization.get("status")
        if (
            isinstance(authorization_status, str)
            and authorization_status not in IMPLEMENTATION_AUTHORIZATION_STATUSES
        ):
            errors.append(
                "implementation_authorization.status must be AUTHORIZED or "
                "NOT_AUTHORIZED."
            )

    if (
        milestone_status == "NO_IMPLEMENTATION_AUTHORIZED"
        and authorization_status != "NOT_AUTHORIZED"
    ):
        errors.append(
            "NO_IMPLEMENTATION_AUTHORIZED must pair with "
            "implementation_authorization.status NOT_AUTHORIZED."
        )
    elif (
        milestone_status in AUTHORIZED_MILESTONE_STATUSES
        and authorization_status != "AUTHORIZED"
    ):
        errors.append(
            "Active implementation and review milestone statuses must pair with "
            "implementation_authorization.status AUTHORIZED."
        )

    correction_ids = value.get("active_correction_ids")
    if not isinstance(correction_ids, list) or not all(
        isinstance(item, str) and item.strip() for item in correction_ids
    ):
        errors.append("active_correction_ids must be a list of non-empty strings.")

    strategic_paths = value.get("strategic_source_paths")
    if not isinstance(strategic_paths, list) or not strategic_paths:
        errors.append("strategic_source_paths must be a non-empty list of paths.")
    else:
        root = Path(project_root).resolve()
        for relative_path in strategic_paths:
            if not isinstance(relative_path, str) or not relative_path.strip():
                errors.append(
                    "strategic_source_paths entries must be non-empty strings."
                )
                continue
            candidate = Path(relative_path)
            if candidate.is_absolute() or ".." in candidate.parts:
                errors.append(
                    f"Strategic source must be a repository-relative path: {relative_path}"
                )
                continue
            if not (root / candidate).is_file():
                errors.append(f"Strategic source is missing: {relative_path}")

    return errors


def render_current_truth(value: dict[str, Any]) -> str:
    """Render the deterministic Markdown view for a validated kernel."""
    initiative = value["current_initiative"]
    milestone = value["active_milestone"]
    authorization = value["implementation_authorization"]
    next_priority = value["immediate_next_priority"]

    lines = [
        "# Current Truth",
        "",
        *GENERATED_VIEW_HEADER.splitlines(),
        "",
        "## Project",
        "",
        f"- Project ID: `{value['project_id']}`",
        f"- Canonical repository: `{value['canonical_repository']}`",
        f"- Canonical branch: `{value['canonical_branch']}`",
        "",
        "## Current initiative",
        "",
        f"- ID: `{initiative['id']}`",
        f"- Name: {initiative['name']}",
        f"- Status: `{initiative['status']}`",
        "",
        "## Active milestone",
        "",
        f"- ID: `{milestone['id']}`",
        f"- Name: {milestone['name']}",
        f"- Status: `{milestone['status']}`",
        "",
        "## Implementation authorization",
        "",
        f"- Status: `{authorization['status']}`",
        f"- Authority: {authorization['authority']}",
        f"- Scope: {authorization['scope']}",
        "",
        "## Immediate next priority",
        "",
        f"- ID: `{next_priority['id']}`",
        f"- Name: {next_priority['name']}",
        f"- Status: `{next_priority['status']}`",
        "",
        "## Active correction IDs",
        "",
    ]
    correction_ids = value["active_correction_ids"]
    lines.extend(f"- `{correction_id}`" for correction_id in correction_ids)
    if not correction_ids:
        lines.append("- None.")

    lines.extend(["", "## Strategic sources", ""])
    lines.extend(f"- `{path}`" for path in value["strategic_source_paths"])
    return "\n".join(lines) + "\n"


def current_truth_errors(project_root: Path | str = ".") -> list[str]:
    """Return kernel and generated-view consistency errors."""
    try:
        value = load_current_truth(project_root)
    except ValueError as exc:
        return [str(exc)]

    errors = validate_current_truth(value, project_root)
    if errors:
        return errors

    view_path = Path(project_root) / GENERATED_VIEW_PATH
    try:
        actual = view_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"Generated current-truth view is missing: {GENERATED_VIEW_PATH}"]
    except (OSError, UnicodeDecodeError) as exc:
        return [f"Generated current-truth view is invalid: {exc}"]

    expected = render_current_truth(value)
    if GENERATED_VIEW_HEADER not in actual:
        errors.append("Generated-view warning is missing.")
    if actual != expected:
        errors.append("Generated current-truth Markdown differs from the JSON kernel.")
    return errors


def write_current_truth_view(project_root: Path | str = ".") -> Path:
    """Validate the kernel and write its generated Markdown view."""
    value = load_current_truth(project_root)
    errors = validate_current_truth(value, project_root)
    if errors:
        raise ValueError("\n".join(errors))

    path = Path(project_root) / GENERATED_VIEW_PATH
    path.write_text(render_current_truth(value), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or render the authoritative current-truth kernel."
    )
    parser.add_argument("command", choices=("check", "write"))
    parser.add_argument("--project-root", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "write":
        try:
            path = write_current_truth_view(args.project_root)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        print(f"Wrote {path}")
        return 0

    errors = current_truth_errors(args.project_root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("Current truth check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
