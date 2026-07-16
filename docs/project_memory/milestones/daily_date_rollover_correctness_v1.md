# Daily Date Rollover Correctness v1

Current implementation branch: `feature/daily-date-rollover-correctness-v1`.

Base branch: `main` at `d44a5e3 Merge smart exercise substitutions v1`.

Status:

```text
DAILY_DATE_ROLLOVER_CORRECTNESS_V1_IMPLEMENTATION_CANDIDATE_READY_FOR_ARCHITECTURE_REVIEW
```

## Implemented Scope

- Daily-driver routes without an explicit `date` remain live and do not acquire the backend-resolved `target_date` through Today, Food, Workout, Recovery, or Back to Today navigation.
- Explicitly dated routes remain pinned and continue preserving their requested date through the same navigation.
- Live Today and Workout surfaces schedule one browser-local midnight check, recheck on focus and visible-tab return, and reload the unchanged live URL when the local calendar date changes.
- Browser-local calendar helpers use local year/month/day fields, validate ISO calendar dates conservatively, and classify only explicit dates before the browser-local current day as historical.
- Historical workouts use one explicit read-only mode. Persisted plan, execution summary, logged sets, substitutions, instructions, and progression context remain viewable while select, start, resume/log, edit, delete, substitution, completion, preview sizing, and variation controls are omitted.
- Explicit past dates without a persisted workout show `No workout was recorded for this date.` and do not request or render a generated preview.
- An explicit date equal to the browser-local current date remains actionable.

## Boundaries Preserved

- The implementation is frontend-only. No backend route, service, schema, persistence, migration, or database behavior changed.
- Existing backend daily-state resolution and historical persistence remain authoritative.
- No workout is automatically completed, deleted, migrated, regenerated, or resumed because the calendar day changed.
- Historical food behavior, recovery policy, substitution ranking, progression behavior, nutrition persistence, provider behavior, and timezone architecture are unchanged.
- Architecture acceptance state remains unchanged; this file records an implementation candidate only.

## Validation Completed

- Pure browser-date and rollover watcher tests: `8 passed`.
- Workout daily-state lifecycle regression slice: `8 passed`.
- Frontend `npm run lint` passed.
- Frontend production `npm run build` passed, including TypeScript and production route generation.
- Isolated production browser smoke used a temporary copy of `fitness_ai.db` on dedicated ports and covered live/unpinned navigation, dated/pinned navigation, historical empty state, unfinished historical read-only state, historical completed logged-set detail, explicit-current interactivity, 390px and 360px mobile widths, desktop Back to Today, Light and Dark themes, console state, hydration, and horizontal overflow.
- The user-owned canonical feature-branch production smoke remains required before Architecture acceptance.
