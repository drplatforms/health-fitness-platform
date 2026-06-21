
# Developer Delivery Workflow Script Safety Addendum v1 Review

Status: ready for Architecture review

Proposed final status: `DEVELOPER_DELIVERY_WORKFLOW_SCRIPT_SAFETY_ADDENDUM_V1_ACCEPTED`

## Summary

Added a script-safety addendum to the Developer Delivery Workflow Contract.

The addendum documents phase-separated scripts, mandatory preflight checks, patch application checks, validation gates, explicit staging, merge commit ancestry verification, post-merge validation, snapshot fallback rules, and workflow anti-patterns.

## Key safety rule

Every merge script must verify that the accepted final feature commit is an ancestor of `main` after merge:

```text
git merge-base --is-ancestor <accepted-final-feature-commit> main
```

If the check fails, scripts must stop before push, snapshot, or Linux pull.

## Boundary confirmation

- Docs/tooling only.
- No runtime behavior changed.
- No provider behavior changed.
- No Streamlit UI behavior changed.
- No FastAPI route behavior changed.
- No database/schema changes.
- No persistence changes.
- No report behavior changes.
- No same-session approval added.
- No model promotion.
- No provider default change.
- No RAG/vector/MoE/MCP implementation.
- No frontend/deployment changes.
- `qa_artifacts/` must not be committed.

## Validation expectation

- `git diff --check`
- `python -m py_compile tools/project_memory_check.py`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_assistant.py memory-check`
- `python tools/dev_assistant.py stale-doc-check`
