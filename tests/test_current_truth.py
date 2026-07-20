from __future__ import annotations

import json
from pathlib import Path

from tools.current_truth import (
    GENERATED_VIEW_HEADER,
    current_truth_errors,
    render_current_truth,
    validate_current_truth,
    write_current_truth_view,
)


def valid_truth() -> dict:
    return {
        "schema_version": 1,
        "project_id": "fitness_ai",
        "canonical_repository": "drplatforms/health-fitness-platform",
        "canonical_branch": "main",
        "current_initiative": {
            "id": "anti-drift-and-hallucination-workflow",
            "name": "Anti-Drift and Hallucination Workflow Initiative",
            "status": "ACTIVE",
        },
        "active_milestone": {
            "id": "fixture-milestone",
            "name": "Fixture Milestone",
            "status": "IMPLEMENTATION_AUTHORIZED",
        },
        "implementation_authorization": {
            "status": "AUTHORIZED",
            "authority": "Architecture handoff",
            "scope": "Project-memory docs, tooling, and tests only",
        },
        "immediate_next_priority": {
            "id": "review-fixture-milestone",
            "name": "Review the fixture milestone",
            "status": "ACTIVE",
        },
        "active_correction_ids": ["CTK-AUTHORITY-DUPLICATION"],
        "strategic_source_paths": [
            "docs/project_memory/product_roadmap.md",
        ],
    }


def write_truth_tree(root: Path, truth: dict | None = None) -> dict:
    value = truth or valid_truth()
    for relative_path in value["strategic_source_paths"]:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("strategic source\n", encoding="utf-8")

    truth_path = root / "docs/project_memory/current_truth.json"
    truth_path.parent.mkdir(parents=True, exist_ok=True)
    truth_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return value


def test_valid_kernel_generates_exact_markdown_under_100_lines(tmp_path: Path) -> None:
    truth = write_truth_tree(tmp_path)

    output_path = write_current_truth_view(tmp_path)
    actual = output_path.read_text(encoding="utf-8")

    assert validate_current_truth(truth, tmp_path) == []
    assert actual == render_current_truth(truth)
    assert GENERATED_VIEW_HEADER in actual
    assert len(actual.splitlines()) < 100
    assert current_truth_errors(tmp_path) == []


def test_missing_required_field_fails_closed(tmp_path: Path) -> None:
    truth = write_truth_tree(tmp_path)
    del truth["active_milestone"]

    errors = validate_current_truth(truth, tmp_path)

    assert "Required field 'active_milestone' must be an object." in errors


def test_unsupported_schema_fails_closed(tmp_path: Path) -> None:
    truth = write_truth_tree(tmp_path)
    truth["schema_version"] = 99

    errors = validate_current_truth(truth, tmp_path)

    assert "Unsupported schema_version 99; expected 1." in errors


def test_unknown_authorization_status_fails_closed(tmp_path: Path) -> None:
    truth = write_truth_tree(tmp_path)
    truth["implementation_authorization"]["status"] = "PENDING"

    errors = validate_current_truth(truth, tmp_path)

    assert (
        "implementation_authorization.status must be AUTHORIZED or NOT_AUTHORIZED."
        in errors
    )


def test_no_implementation_status_requires_not_authorized(tmp_path: Path) -> None:
    truth = write_truth_tree(tmp_path)
    truth["active_milestone"]["status"] = "NO_IMPLEMENTATION_AUTHORIZED"

    errors = validate_current_truth(truth, tmp_path)

    assert (
        "NO_IMPLEMENTATION_AUTHORIZED must pair with "
        "implementation_authorization.status NOT_AUTHORIZED." in errors
    )


def test_active_status_requires_authorized(tmp_path: Path) -> None:
    truth = write_truth_tree(tmp_path)
    truth["active_milestone"]["status"] = "READY_FOR_ARCHITECTURE_REVIEW"
    truth["implementation_authorization"]["status"] = "NOT_AUTHORIZED"

    errors = validate_current_truth(truth, tmp_path)

    assert (
        "Active implementation and review milestone statuses must pair with "
        "implementation_authorization.status AUTHORIZED." in errors
    )


def test_missing_strategic_source_fails_closed(tmp_path: Path) -> None:
    truth = valid_truth()
    truth["strategic_source_paths"] = ["docs/project_memory/missing.md"]

    errors = validate_current_truth(truth, tmp_path)

    assert "Strategic source is missing: docs/project_memory/missing.md" in errors


def test_generated_markdown_drift_fails_closed(tmp_path: Path) -> None:
    write_truth_tree(tmp_path)
    output_path = write_current_truth_view(tmp_path)
    output_path.write_text("manual edit\n", encoding="utf-8")

    errors = current_truth_errors(tmp_path)

    assert "Generated-view warning is missing." in errors
    assert "Generated current-truth Markdown differs from the JSON kernel." in errors
