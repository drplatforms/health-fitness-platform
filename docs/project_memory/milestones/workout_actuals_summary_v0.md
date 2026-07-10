# Workout Actuals Summary v0

Current source of truth: `feature/workout-actuals-summary-v0`.

Base branch: `main` at `5378cd9 Merge workout set logging defaults polish v0.1.1`.

Status:

```text
WORKOUT_ACTUALS_SUMMARY_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

## Purpose

Add a compact, read-only per-exercise view of workout execution beneath the existing aggregate Execution Summary.

## Implemented Scope

- Each planned exercise shows its display name, completed non-skipped logged-set count, planned-set count, and accessible set-completion dots.
- Completion labels distinguish complete, not started, remaining sets, limited data, and extra logged sets without judgmental or prescriptive language.
- Average actual RIR is calculated per exercise from logged sets that contain RIR data and maps to hard, moderate, easy, or limited-data effort labels.
- Rep status compares logged actual reps with the planned exercise range and reports on-target, mixed, below-range, above-range, or no-logged-reps states.
- Substitution-linked actual sets remain attributed to the original planned exercise while showing the active replacement exercise name.
- Extra logged sets preserve the planned dot count and add a compact extra-set indicator.
- Existing actual-set create, edit, cancel, and delete paths continue to drive the visible summary through existing frontend state and backend summary refresh behavior.

## Boundaries Preserved

- The implementation is frontend-only and introduces no backend route, service, schema, persistence, or database changes.
- Planned workout snapshots remain immutable.
- Actual set entry remains user-controlled and backend-validated.
- Progression history remains read-only.
- No automatic progression, load suggestion, recommendation, deload, periodization, workout generation, nutrition, provider, RAG, embeddings, vector search, or agent orchestration behavior was added.

## Validation Completed

- Workout persistence and progression-history slice: `91 passed`.
- Workout planning, route, view, rotation, and sizing slice: `128 passed`.
- `npm run lint` passed.
- `npm run build` passed, including TypeScript and production route generation.
- `git diff --check` passed.
- Browser smoke passed against `tmp/workout_actuals_summary_smoke.db`; the real `fitness_ai.db` was not mutated.
- Browser coverage included complete, partial, and not-started exercise states; accessible logged/planned dot labels; RIR and rep-range status updates; edit, cancel, save, and delete behavior; completion review; no prohibited progression/deload language; no console errors; and a 390px-wide layout without horizontal overflow.
