# Daily Coach Narrative Provider Trial Matrix v1

Status: backend implementation in progress.

Requested final status: `DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.

## Baseline

Current source of truth: `main` at `a6cd8d0`.

Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-27_a6cd8d0_daily-coach-narrative-approved-value-quote-validation-v1.zip`.

Previous accepted statuses:

- `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED_AND_QA_PASSED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED_AND_MERGED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_QA_V1_PASS`

## Purpose

Add repeatable evaluation tooling for Daily Coach value-aware narrative providers.

The matrix compares deterministic, direct_ollama, and openai over the same approved Daily Coach contexts without changing product defaults.

## Tooling

Added:

- `tools/run_daily_coach_provider_trial_matrix.py`
- `tests/test_daily_coach_provider_trial_matrix.py`
- `docs/provider_trials/daily_coach_narrative_provider_trial_matrix_v1.md`

The tool writes:

- `trial_matrix.jsonl`
- `trial_matrix_summary.md`
- `selected_outputs.md`

Generated trial outputs are local/evaluation artifacts and should be reviewed before committing.

## Safety boundaries

- deterministic remains default;
- direct_ollama remains opt-in;
- openai remains opt-in;
- live providers require `--allow-live-providers`;
- automated tests do not call live OpenAI or Ollama;
- raw provider output is not written;
- API keys/secrets are not written;
- provider narratives are not persisted;
- Streamlit provider controls are not added;
- parser/validator/fallback semantics are unchanged;
- approved value quote validation remains mandatory.

## Validation expectation

Focused validation:

- targeted Ruff/Black on the tool and tests;
- trial matrix tests;
- existing Daily Coach value narrative service/API tests;
- DailyCoachSynthesis tests;
- API smoke tests;
- project memory tests/checks;
- Streamlit compile check.
