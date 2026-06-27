# Next Milestone — Daily Coach Narrative Provider Trial Matrix v1

Current backend milestone: Daily Coach Narrative Provider Trial Matrix v1.

Owner: Backend Development / Data Layer.

Secondary owner: Agent Engineering for provider/runtime comparison review.

Status: authorized for backend implementation.

Requested final status: `DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.

## Current accepted baseline

Current source of truth: `main`.

Required source main commit: `a6cd8d0`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_a6cd8d0_daily-coach-narrative-approved-value-quote-validation-v1.zip`.

Previous status: `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED_AND_MERGED`.

Previous QA status: `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_QA_V1_PASS`.

## Implementation focus

Add provider trial matrix tooling for Daily Coach value-aware narrative comparison:

- run deterministic baseline cases;
- skip live providers unless `--allow-live-providers` is explicit;
- allow direct_ollama/openai trial rows when explicitly enabled and configured;
- write sanitized JSONL output;
- write markdown summary output;
- write selected approved/rendered output comparisons;
- record fallback, parse, validation, final source, latency, and quoted values;
- preserve user 102 / 2026-06-27 as the recovery-truth regression case when requested.

## QA expectation

QA class: CLASS 2 / CLASS 5 HYBRID.

Recommended QA: focused tooling, provider-safety, and no-live-provider regression tests.

Not required:

- full Streamlit workflow QA;
- live OpenAI calls in tests;
- live Ollama calls in tests;
- provider promotion;
- persistence or UI changes.

## Post-acceptance routing

After Architecture acceptance, route focused QA for the trial matrix tool and optionally run a manual sanitized provider trial matrix.

Potential follow-up: Daily Coach Narrative Provider Runtime Trial QA v1 or OpenAI/direct_ollama comparison review.


## Historical continuity anchors — reference-only

- Daily Coach Async Provider Runtime Design v1
- Deterministic fallback remains mandatory
- AI candidate output must be parsed and validated before user display
- Backend facts remain the source of truth

## Historical continuity anchors — additional reference-only preservation

- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET
