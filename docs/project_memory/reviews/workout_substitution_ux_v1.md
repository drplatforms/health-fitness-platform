# Workout Substitution UX v1 Review

Status: IMPLEMENTED / READY FOR ARCHITECTURE REVIEW

## Summary

Workout Substitution UX v1 improves the Workout page substitution flow after the workout preview. The implementation keeps the existing backend substitution endpoints and behavior intact while making the normal user flow clearer and safer.

## UX changes

- The substitution section is labeled `Need a swap?`.
- Users choose one exercise to replace from a clear selector.
- The selected target is shown as `Replacing: <exercise>`.
- Replacement candidates are shown as `Suggested replacements`.
- Primary action copy is `Apply swap`.
- Cancel/decline copy is `Keep original`.
- Success copy clearly says what changed.
- Empty and failure states avoid technical error language.

## Safety and boundary review

- Normal UI does not expose raw IDs, JSON payloads, ranking internals, scoring internals, provider/model terms, or stack traces.
- Developer details remain separated behind Developer Mode.
- The implementation does not change workout generation, substitution candidate generation, apply-substitution endpoint behavior, workout persistence, logging lifecycle, exercise count, or catalog rows.

## Deferred

- Workout Exercise Count Preference v1.
- Workout Substitution Logic v1 if substitution candidate quality needs backend changes.
- Broader Workout page redesign.
