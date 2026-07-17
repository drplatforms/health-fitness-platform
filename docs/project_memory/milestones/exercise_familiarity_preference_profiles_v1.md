# Exercise Familiarity & Preference Profiles v1

## Status

Implementation candidate on `feature/exercise-familiarity-preference-profiles-v1` from canonical `main @ 58dee0e`.

Architecture acceptance remains pending. This document records implemented behavior and validation evidence; it does not self-accept the milestone.

## Authorized outcome

Users may explicitly maintain one catalog-backed exercise profile with two independent optional dimensions:

- familiarity: `unfamiliar`, `learning`, `familiar`, or unset;
- preference: `favorite`, `disliked`, or neutral/unset.

Familiarity adapts only the compact instruction affordance. Preference provides bounded deterministic ranking influence among otherwise valid workout-generation options and within the already-approved substitution candidate universe.

## Implemented behavior

### Persistence and API

- `workout_exercise_profiles` is an additive service-owned table with `UNIQUE(user_id, catalog_exercise_id)`.
- Profile identity is catalog-only. There is no name fallback, normalized-name profile, or automatic promotion.
- Catalog IDs are validated against the canonical exercise catalog before save or resolve.
- Familiarity and preference remain independent nullable fields.
- Clearing both fields deletes the persisted row; explicit delete is idempotent.
- The user-scoped API supports bounded batch resolve, save/update/reset, and delete without one request per exercise.
- Public responses expose only profile identity, catalog identity, explicit states, and timestamps.

### Workout generation

- The preview composition loads one bounded preference map for the user and passes it into the otherwise-pure deterministic workout context.
- Favorite adds `+120` and disliked adds `-120` to valid option ranking.
- Existing recent-exercise (`-700+`), most-recent-plan (`-950`), equipment, movement, modality, and rotation safeguards remain stronger and authoritative.
- Preference does not alter hard eligibility or deterministic tie behavior.
- A missing profile map preserves existing selection behavior exactly.
- Familiarity is not read by generation.

### Substitutions

- Candidate eligibility is unchanged.
- Ranking priority remains movement match, target-muscle overlap, and exercise type before explicit preference; recent exposure and stable deterministic tie-break remain after preference.
- Favorite, neutral, and disliked form a deterministic preference tier only among semantically equivalent candidates.
- Favorite cannot outrank a materially better movement match.
- Preference reason codes are factual; favorite explanations may say that the option matches an exercise the user favors.

### Instruction UX and state isolation

- Collapsed exercise cards gain no permanent profile chip or new card.
- The existing instruction affordance reads `Learn` for unfamiliar, `Review` for learning, and `How To` for familiar/unset.
- Instructions never auto-expand.
- Two accessible native selects inside the opened instruction surface edit Familiarity and Preference.
- Historical read-only workout dates do not resolve or expose current editable profile controls.
- Active substitutions switch profile display/editing to the replacement catalog ID.
- Profile state is isolated by user, date mode, workout view, preview variation, and effective catalog-ID signature.
- Profile refreshes do not touch Reps, Weight, RIR, Notes, actual sets, Session Memory, progression, or history state.

## Boundaries preserved

- No inferred familiarity or preference.
- No automatic profile changes from workout history, Session Memory, substitutions, progression, instructions, AI, or providers.
- No `never suggest`, injury/limitation state, profile history, confidence, management page, custom exercise identity, or recommendation AI.
- No hard exclusion for disliked exercises and no substitution eligibility expansion.
- No dependencies, provider changes, Session Memory changes, Exercise History changes, or broad workout UI cleanup.
- Automated tests use temporary databases. Production smoke must use a disposable physical database copy rather than `DB_PATH` alone.

## Validation evidence

- New profile service/API: `8 passed`.
- Focused generation/substitution preference regressions: `5 passed`.
- Workout generation and selection matrix: `128 passed`.
- Substitution service/persistence/UX matrix: `52 passed`.
- Workout persistence, Today views/routes, progression history, and Session Memory regressions: `139 passed`.
- Frontend profile helper tests: `4 passed`.
- Touched Python Ruff check and format: passed.
- Frontend lint: passed.
- Frontend production build: passed.
- Project-memory pytest: `29 passed`.
- Standalone project-memory check: `PASS=609 WARN=38 FAIL=0` (existing warnings only).
- Production-mode browser smoke used a disposable physical copy of `fitness_ai.db` with seeded QA users and verified desktop and mobile-width Light/Dark behavior, profile persistence, user/exercise isolation, effective replacement identity after substitution, unsaved set-field preservation, historical read-only isolation, no horizontal overflow, and no console warnings or errors.
- The canonical `fitness_ai.db` SHA-256 remained `89dee348fdfee1b71c9eb3bf5e8a12eb593e962b66f1f0ddbe115ba3a63adb3e` across validation.
- Smoke services were stopped and the disposable database, launcher, and logs were removed.

Final repository audit completed with no staged files and no temporary smoke artifacts. Architecture acceptance remains pending.

## Architecture acceptance

EXERCISE_FAMILIARITY_PREFERENCE_PROFILES_V1_ARCHITECTURE_ACCEPTED

Accepted after source review and feature-branch production user smoke.
