# Exercise Guidance During Workout v1

Status: `IMPLEMENTATION_COMPLETE_PENDING_ARCHITECTURE_REVIEW`

Architecture authorization: direct Architecture handoff dated 2026-07-20.

Implementation baseline: `main` at `f3a1c16` (`Merge workout rest timer v1`).

Feature branch: `codex/exercise-guidance-during-workout-v1`.

## Implemented behavior

- Active workout exercise cards expose a compact, stable `Form guide` action.
- On mobile, the action opens the current exercise guidance in a full-viewport,
  scrollable dialog above the persistent workout navigation.
- The dialog supports a visible close action, Escape dismissal, contained Tab
  focus, focus restoration, and background-scroll locking.
- The workout exercise card and its set-entry/editor state remain mounted while
  guidance is open, so unsaved entries survive dismissal.
- Active-workout guidance omits familiarity and preference editing so the
  reference surface remains execution-first. Those controls and their existing
  behavior remain unchanged outside active workout logging.
- Desktop active-workout guidance continues to use the established expanded
  instruction surface.

## Reused systems

- `ExerciseInstructionDisclosure` remains the single guidance renderer.
- The existing exercise-instruction API supplies overview, setup, execution,
  form cues, common mistakes, and safety notes by catalog exercise ID.
- The existing visual-media selector and renderer supply approved direct-local,
  shared-local, or configured provider media and preserve text-only fallback.
- Substituted exercises continue to resolve guidance through the existing
  replacement catalog-exercise identity.

No instructional copy, media infrastructure, backend route, schema,
persistence, dependency, provider integration, or workout-state transition was
added or changed.

## Validation

- Focused frontend guidance/media tests: 6 passed.
- Established backend exercise instruction/media slice: 39 passed.
- Frontend ESLint: passed with zero warnings.
- Frontend production build: passed.
- Production browser smoke used a disposable copy of `fitness_ai.db` with a
  production Next.js server and isolated FastAPI server.
- Mobile smoke at 390 x 844 verified current-exercise focus, written-only
  fallback, approved Start/Finish visuals, all instruction sections, close,
  Escape, Tab containment, focus restoration, preserved unsaved reps/weight,
  no profile controls, and no horizontal overflow.
- Desktop smoke verified the established inline expansion, approved visuals,
  all instruction sections, no profile controls during execution, no horizontal
  overflow, and no console errors.

## Database safety confirmation

- The canonical `fitness_ai.db` SHA-256 was
  `7B96ED6774223DD322DFFF1D698E383ED141C351FCA9880587FA61B30F83943A`
  before targeted validation and
  `00867ECBB4F37D62748195CF948D41DF448FD8FDA5C1F5E08A634216F7A50E80`
  at final closeout.
- Browser mutations were verified to remain in the disposable database: workout
  plan 436 was started in the smoke copy but remained selected in the canonical
  database.
- The three targeted pytest files use autouse temporary-database fixtures.
- A pre-existing `uvicorn api.main:app` process was concurrently listening on
  port 8000, and the user confirmed the canonical hash change was caused by
  their own live activity.
- Milestone validation did not mutate the canonical database. The canonical
  database was not restored, overwritten, or otherwise changed during the
  investigation. Projectmem issue 0444 records the resolved attribution.

## Representation findings

No existing instruction response shape failed to render. Exercises without
approved visual media continue to render the complete written guidance without
an empty visual section. No new product decision is required from Architecture.
