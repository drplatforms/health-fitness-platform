# Workout Substitution UX v1

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

## Goal

Make the Workout page substitution flow easier to understand without changing workout generation, exercise selection, scoring, persistence, logging lifecycle, provider behavior, or catalog data.

## Scope

Implemented as a Streamlit UI flow polish milestone:

- Clearer `Need a swap?` section.
- One explicit exercise-to-replace selector.
- Clear `Replacing:` state.
- User-safe suggested replacement table.
- Clear `Apply swap` and `Keep original` controls.
- User-safe success, empty, and failure copy.
- Developer details remain behind Developer Mode.

## Non-goals preserved

- No workout generation changes.
- No substitution algorithm changes.
- No scoring or ranking changes.
- No exercise count/default length changes.
- No workout persistence changes.
- No workout logging lifecycle changes.
- No catalog changes.
- No provider/model changes.
- No narrative persistence changes.
- No report/database/schema changes.

## Follow-up

Workout Exercise Count Preference v1 remains the likely next workout-product milestone. Workout Substitution Logic v1 should be a separate milestone if backend substitution quality itself needs changes.
