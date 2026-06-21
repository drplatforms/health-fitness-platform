
# Developer Delivery Workflow Script Safety Addendum v1

Status: implemented / ready for Architecture review

Branch: `feature/developer-delivery-workflow-script-safety-addendum-v1`

## Purpose

Add a docs/tooling addendum to the Developer Delivery Workflow Contract so future generated scripts do not silently create valid-but-wrong Git history.

## Why this exists

A recent sequencing issue showed that a clean working tree does not prove the correct milestone was merged. A branch can be clean while `main` contains only part of a feature's accepted work.

This milestone documents mandatory script safety gates, especially the merge ancestry check:

```text
git merge-base --is-ancestor <accepted-final-feature-commit> main
```

If that check fails after merge, scripts must stop before push, snapshot, or Linux pull.

## Scope

Docs/tooling only.

No app runtime behavior, provider behavior, Streamlit UI behavior, FastAPI route behavior, schema, persistence, report behavior, same-session approval, or model promotion changes are approved by this milestone.

## Files

- `docs/project_memory/developer_delivery_workflow_script_safety_addendum_v1.md`
- `docs/project_memory/developer_delivery_workflow_contract.md`
- `docs/project_memory/README.md`
- `docs/project_memory/current_state.md`
- current handoff docs
- `AGENTS.md`
- `tools/project_memory_check.py`
- `tests/test_project_memory_check.py`
