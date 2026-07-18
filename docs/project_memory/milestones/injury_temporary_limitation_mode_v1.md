# Injury / Temporary Limitation Mode v1

Status: IMPLEMENTATION CANDIDATE — architecture acceptance pending

## Scope

This milestone adds an optional, user-controlled temporary workout limitation profile. The backend remains authoritative for validation, workout constraints, generation, substitution eligibility, stale-preview safety, and workout-start safety. The user explicitly creates, edits, or clears the profile; no limitation is inferred from free text or silently applied.

## Behavior

- At most one current temporary limitation is stored per user.
- A limitation may describe affected body regions, but only explicit restricted movement patterns and excluded catalog exercise IDs act as hard workout constraints.
- A hard restriction is required before saving.
- Expiration is passive: expired records no longer affect reads, generation, substitution, preview validation, or workout start.
- Generation and provider candidate slices exclude restricted movements and catalog exercise IDs.
- Deterministic fallback selects only eligible catalog exercises.
- Under active temporary limitations, duplicate fallback selections are repaired
  with a unique eligible catalog exercise, preferring the same movement pattern.
  If no unique compatible workout can be built, preview returns a deliberate
  user-safe unavailable response instead of duplicate-plan validation failure.
- Substitution candidates and substitution application are revalidated against the current limitation.
- A persisted preview that becomes stale is rejected at selection time.
- A selected plan that becomes incompatible is rejected at workout start, using the effective active substitution identity when present.
- Unexpected start-time conflict lookup failures propagate and leave the plan
  selected; they are never treated as no conflict.
- Conflict warnings follow the authoritative current-day workout state, so expired prior selections are not presented as current conflicts.
- Successful substitutions refresh only the limitation conflict summary, so an
  allowed replacement clears its warning without a page reload.
- Historical completed workout rendering is unchanged.

## Persistence and API

- Additive table: `user_temporary_workout_limitations`.
- Current-profile API: `GET`, `PUT`, and `DELETE /users/{user_id}/temporary-workout-limitation`.
- Exercise-catalog search is exposed to the frontend through the existing catalog data via a same-origin route.
- The existing `fitness_ai.db` is not migrated or mutated by automated validation or browser smoke.

## UI

The current-workout experience includes a compact Set/Edit/Clear card with optional affected-region descriptions, explicit movement restrictions, catalog-exercise search, and bounded or until-cleared duration choices. Active limitations show a compact summary and current-plan conflicts. The UI is absent from historical workout views.

## Implementation files

- `models/temporary_workout_limitation_models.py`
- `models/workout_constraint_models.py`
- `services/temporary_workout_limitation_service.py`
- `services/workout_constraint_service.py`
- `services/workout_plan_service.py`
- `services/exercise_substitution_service.py`
- `services/workout_plan_persistence_service.py`
- `api/routes/workout_plans.py`
- `frontend/src/app/api/temporary-workout-limitation/route.ts`
- `frontend/src/app/api/exercise-catalog/route.ts`
- `frontend/src/lib/temporaryWorkoutLimitation.ts`
- `frontend/src/components/TemporaryWorkoutLimitationCard.tsx`
- `frontend/src/components/WorkoutPreviewExperience.tsx`
- focused backend and frontend helper tests

## Validation evidence

- Focused temporary-limitation service tests pass, including passive expiry, validation, generation constraints, substitution filtering, stale-preview rejection, start rejection, active-substitution identity, and stale current-plan warning behavior.
- Architecture correction coverage verifies core-anti-rotation restriction
  generation remains unique, an over-restrictive limitation returns the safe
  unavailable response, and conflict-query failures cannot start a plan.
- Existing workout generation, selection, rotation, sizing, substitution, persistence, and route regression slices pass.
- Frontend helper tests, lint, and production build pass.
- Production-mode browser smoke covered inactive/active/edit/clear flows, movement and catalog-ID filtering after regeneration, conflict warnings, blocked and successful starts, in-progress logging preservation, no-compatible-substitution state, desktop and mobile-width layout, accessible native controls, and console inspection.
- Browser automation confirmed keyboard focus on the native Edit button; synthetic Enter/Space activation was not observable through the browser harness and remains a tooling-evidence limitation, not a known product failure.
- The isolated full backend suite has 13 pre-existing failures outside this milestone: three stale workflow-memory assertions and ten diagnostic tracer signature failures. New and affected tests pass.
- Project-memory validation and final repository hygiene checks are required before handoff.

## Non-goals preserved

- No diagnosis, treatment recommendation, inferred injury classification, provider/RAG workflow, historical rewrite, autonomous health decision, or new recommendation engine.
- Affected-region descriptions do not implicitly restrict movement.
- No staging, commit, push, merge, or architecture acceptance is performed by this milestone implementation.
