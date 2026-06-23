# Weekly Coach Summary Developer Mode Inspection v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

Proposed final status: WEEKLY_COACH_SUMMARY_DEVELOPER_MODE_INSPECTION_V1_ACCEPTED

Branch: feature/weekly-coach-summary-developer-mode-inspection-v1

## Purpose

Expose the deterministic Weekly Coach Summary service shell inside the Streamlit app through Developer Mode only.

This milestone lets the user inspect the first meaningful deterministic weekly summary inside the app without creating a public/default feature.

## Scope

Implemented:

- Developer Mode-only Weekly Coach Summary Preview panel in `ui/streamlit_app.py`.
- Scenario selector for bounded fixture/demo input.
- Explicit button-driven summary generation.
- Deterministic `ApprovedWeeklyCoachSummary` rendering.
- Deterministic fallback scenario rendering.
- Safe metadata display: source, confidence, public_safe, displayable, reason_codes, and limitations.
- Source/structure tests for Developer Mode gating and boundary preservation.
- Project memory updates.

## Boundaries

Confirmed:

- no public/default Weekly Coach Summary display
- no normal Today Weekly Coach Summary display
- no automatic generation
- no generation on page load
- no persistence schema
- no database migration
- no API endpoint
- no provider runtime
- no Ollama call
- no CrewAI call
- no qwen2.5:3b call
- no qwen3/qwen3:32b promotion
- no worker, queue, scheduler, polling, or background process
- no async job record creation
- no raw provider output display
- no rejected provider output display
- no prompt/raw context/scratchpad display

## Developer Mode behavior

Developer Mode now includes:

- `Developer Mode: Weekly Coach Summary Preview`
- scenario selector
- `Generate deterministic weekly summary preview` button
- readable approved summary sections
- deterministic fallback inspection
- safe metadata and sanitized reason codes/limitations

The panel is hidden unless Developer Mode is enabled.

## Validation

Required validation:

- `pytest tests/test_weekly_coach_summary_models.py -q`
- `pytest tests/test_weekly_coach_summary_service.py -q`
- `pytest tests/test_streamlit_weekly_coach_summary_developer_mode.py -q`
- `pytest tests/test_project_memory_check.py -q`
- `python tools/dev_weekly_coach_summary_preview.py`
- project memory checks
- `scripts/dev_commit_check.ps1 -Mode code`
- manual Streamlit smoke after Linux pull/restart

## Next likely milestone

Weekly Coach Summary Async Persistence Design v1.

Developer Mode inspection proves the deterministic output is useful in-app. The next playbook-aligned step is designing safe persistence for approved summaries and sanitized lifecycle metadata before any public/default UI or provider runtime work.
