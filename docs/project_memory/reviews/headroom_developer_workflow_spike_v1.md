# Headroom Developer Workflow Spike v1

Status: `HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_IMPLEMENTED_PENDING_REVIEW`

## Purpose

Evaluate Headroom as a developer-workflow-only compression tool for AI Health Coach handoffs, context packs, QA logs, diffs, pytest output, helper prompts, and milestone summaries.

## Boundary

This spike is developer workflow only.

No changes were made to:

- FastAPI runtime
- Streamlit runtime
- provider runtime
- provider prompts
- model-facing health context
- validation schemas
- nutrition/training/report contracts
- persistence
- database behavior
- user-facing UI
- app dependencies required for pytest
- deterministic fallback behavior
- Claude workflow

Compressed output is convenience context only. It is not source of truth.

## What was tested

The spike generated local-only source artifacts under:

``text
qa_artifacts/headroom_spike_v1/original/
``

It generated local-only compressed baseline artifacts under:

``text
qa_artifacts/headroom_spike_v1/compressed/
``

The local baseline compressor is not Headroom. It was used only to create a comparison/control set and prove the workflow can keep generated artifacts out of git.

## Inputs used

- Dev Assistant status output
- Codex context pack
- Aider context pack
- Copilot context pack
- QA plan
- Git diff stat
- Git diff name-only
- Focused pytest output

## Size comparison

| Case | Original chars | Compressed chars | Reduction | Compression | Safety | Usefulness | Accuracy | Result |
|---|---:|---:|---:|---|---:|---:|---:|---|
| context_pack_aider | 2275 | 947 | 58.4% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |
| context_pack_codex | 2275 | 961 | 57.8% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |
| context_pack_copilot | 2277 | 947 | 58.4% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |
| dev_assistant_status | 10120 | 3148 | 68.9% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |
| git_diff_name_only | 0 | 1 | 0% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |
| git_diff_stat | 0 | 1 | 0% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |
| pytest_project_memory_check | 100 | 18 | 82% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |
| qa_plan | 1081 | 799 | 26.1% | Baseline only | 5 | 3 | 4 | Needs real Headroom comparison |

## Safety findings

The baseline compression preserved the developer-workflow boundary because it did not touch app runtime code or source-of-truth docs.

Critical boundaries preserved:

- Backend remains source of truth.
- Deterministic fallback remains default.
- Provider paths remain opt-in/debug/manual unless explicitly approved.
- Headroom is not introduced as a runtime dependency.
- Headroom is not used on provider prompts or model-facing health facts.
- Codex remains optional/scoped.
- Claude remains out of scope.

## Accuracy findings

The deterministic baseline did not invent files, commits, test results, or provider behavior.

However, because this run did not execute real Headroom, it cannot prove Headroom accuracy yet.

## Lost-boundary findings

No repo boundary was changed.

Generated artifacts stayed under `qa_artifacts/` and are locally ignored through `.git/info/exclude`.

## Recommendation

Current recommendation:

`HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_OPTIONAL_ONLY_PENDING_REAL_HEADROOM_RUN`

Reason:

- The workflow is safe.
- Local artifact handling is safe.
- Context-pack compression is potentially useful.
- But this run used a deterministic local baseline, not actual Headroom output.
- Architecture should require one real Headroom output comparison before adopting it as a default developer workflow step.

## Recommended allowed uses if real Headroom passes

- compress long Architecture-to-Backend handoffs
- compress Supercharger context packs into handoff capsules
- compress QA logs for review
- compress pytest output for quick triage
- compress git diff/file summaries
- compress Codex/OpenAI helper prompts for small scoped tasks
- compress milestone closeout summaries

## Recommended forbidden uses

- FastAPI runtime
- Streamlit runtime
- provider runtime
- provider prompts
- model-facing health context
- validation schemas
- nutrition/training/report contracts
- food/exercise catalog truth
- user health facts
- persisted source-of-truth docs
- tests requiring Headroom
- app dependencies required for pytest
- replacing backend truth with compressed text
- replacing project memory with compressed text
- Claude workflow

## Validation

Required validation:

``powershell
git diff --check
scripts/dev_commit_check.ps1 -Mode code
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
pytest tests/test_project_memory_check.py -q
pytest tests/test_daily_coach_narrative_preview_route.py -q
pytest tests/test_daily_coach_narrative_preview_service.py -q
pytest tests/test_daily_next_action_service.py -q
pytest tests/test_report_persistence_boundary.py -q
pytest tests/test_full_report_section_registry.py -q
``

## Final status recommendation

Do not mark full Headroom adoption yet.

Recommended current status:

`HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_OPTIONAL_ONLY_PENDING_REAL_HEADROOM_RUN`

If Architecture wants this closed now, close as:

`HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_OPTIONAL_ONLY`

If Architecture requires real Headroom output before closure, keep as:

`HEADROOM_DEVELOPER_WORKFLOW_SPIKE_V1_IMPLEMENTED_PENDING_REVIEW`
