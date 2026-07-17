# Workout Session Memory v1

## Status

Architecture accepted on `feature/workout-session-memory-v1` after source review and feature-branch user production smoke.

Architecture acceptance: `WORKOUT_SESSION_MEMORY_V1_ARCHITECTURE_ACCEPTED`. No subsequent milestone is implementation-authorized by this acceptance.

## Baseline

- Canonical main: `c9c6d22`
- Prior accepted Exercise History feature commit: `a909467`
- Feature branch: `feature/workout-session-memory-v1`
- Handoff: `C:/Users/drdre/Downloads/workout-session-memory-v1-codex-handoff.md`

## Delivered behavior

- Persist one bounded, user-owned memory per stable exercise identity.
- Prefer `catalog:<exercise_id>` identity when catalog identity is available.
- Use `name:<normalized_name>` only when catalog identity is unavailable.
- Resolve catalog identity first, use conservative name fallback, refuse ambiguous promotion, and promote only when the fallback can be mapped safely.
- Resolve bounded batches for the visible preview or active-workout exercise set.
- Create, edit, and explicitly delete memories through the workout-plan API and the Next.js proxy.
- Render a compact read-only memory with an inline editor in workout preview and active execution.
- Keep memory separate from Notes on logged sets, completed workout history, progression decisions, and recommendations.
- Resolve the effective substituted exercise so the original and replacement do not share memory accidentally.
- Reset transient memory state across user, date, view, preview-version, and exercise-identity changes.
- Suppress current memory controls and content on historical workout dates.
- Preserve selected substitutions when starting a workout and preserve unsaved set inputs while substitution or memory UI changes.
- Seed deterministic longitudinal QA memories for catalog-backed and name-fallback cases.

## Persistence and contracts

- Dedicated table: `workout_exercise_memories`
- Unique ownership key: `(user_id, identity_key)`
- Identity forms: `catalog:<id>` and `name:<normalized name>`
- Memory text maximum: 500 characters
- Batch resolution maximum: 24 exercises
- Exercise name maximum: 200 characters
- Mutation failures use explicit validation, not-found, and conflict semantics.

## Validation evidence

- New service and API tests: 23 passed.
- Official longitudinal QA seed tests: 6 passed.
- Frontend memory API helper tests: 4 passed.
- Combined workout memory, persistence, progression, history, and analytics regression slice: 141 passed.
- Substitution service and persistence regression slice: 44 passed.
- Ruff lint and format checks passed for touched Python files.
- Frontend lint passed.
- Frontend production build passed and included `/api/workout-exercise-memories`.
- Production browser smoke passed against a disposable database copy on desktop and 390x844 mobile, in Light and Dark themes, with no console warnings/errors or horizontal overflow.
- Browser smoke covered create/edit/delete/refresh persistence, effective substituted identity, unsaved set preservation, user isolation, preview-version isolation, historical suppression, and selected-substitution preservation on workout start.
- The in-app automation wrapper focused native buttons but did not dispatch keyboard activation; native button, textbox, and label semantics were verified. Mouse activation covered all mutations.
- Controlled SHA-256 checks confirmed the real `fitness_ai.db` was unchanged during automated validation; final closeout rechecks this after smoke cleanup.

## Non-goals preserved

- No AI/provider integration, RAG, embeddings, or runtime agent orchestration.
- No recommendation, progression, workout-generation, or recovery-decision changes.
- No memory inference from history or set notes.
- No copying memory into completed logs or historical analytics.
- No dependency additions or unrelated refactors.

## Review gate

Architecture should review identity promotion, ambiguity behavior, user/date/variation isolation, substitution semantics, historical suppression, and the dedicated persistence boundary before accepting this milestone.
