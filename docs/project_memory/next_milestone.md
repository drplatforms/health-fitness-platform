# Next Milestone — Daily Coach Provider Trial Diagnostics v1

Owner: Backend Development / Provider Runtime / Agent Engineering.

Source baseline: `main` at `a6cd8d0` plus Daily Coach Narrative Provider Trial Matrix v1 tooling at `4641c91`.

Recommended branch: `feature/daily-coach-provider-trial-diagnostics-v1`.

Requested final status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_ACCEPTED`.

## Goal

Improve Daily Coach provider trial diagnostics without changing product runtime behavior.

## Scope

- Add explicit local raw-provider-output diagnostic mode, off by default.
- Keep normal JSONL/Markdown artifacts sanitized.
- Add safe OpenAI key/config diagnostics without exposing secret values.
- Classify provider failures more clearly than generic failure where metadata allows.
- Add optional Ollama unload cleanup support for trial matrix runs.
- Record cleanup failures as warnings/safe metadata, not provider-quality failures.
- Preserve deterministic default and opt-in provider behavior.

## Non-goals

- No provider default changes.
- No Streamlit provider controls.
- No normal endpoint behavior changes.
- No parser/validator/quote-value relaxation.
- No provider narrative persistence.
- No nutrition/workout/recovery/report changes.
- No live provider calls in tests.
- No raw provider diagnostics or secrets committed.
