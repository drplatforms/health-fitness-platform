# Project Continuity Bootstrap — Daily Coach Provider Trial Diagnostics v1

Current source of truth: `main` at `a6cd8d0` plus Daily Coach Narrative Provider Trial Matrix v1 tooling at `4641c91`.

Active milestone: `Daily Coach Provider Trial Diagnostics v1`.

Architecture status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_APPROVED_FOR_BACKEND`.

## Current work

Add diagnostics to `tools/run_daily_coach_provider_trial_matrix.py` so provider failures can be understood without changing product behavior.

Implemented/targeted diagnostics:

- explicit local raw-provider-output diagnostic mode;
- normal artifact sanitization remains default;
- safe OpenAI config/key presence metadata;
- provider error type classification;
- optional Ollama unload cleanup metadata;
- tests proving no live OpenAI/Ollama calls are required.

## Standing boundaries

Do not make OpenAI or direct_ollama default. Do not change normal Daily Coach endpoints. Do not relax parser/validator/quote-value safety. Do not commit raw provider outputs or secrets. Do not add Streamlit controls, persistence, RAG, multi-agent orchestration, nutrition/workout/recovery/report behavior changes, or schema changes.
