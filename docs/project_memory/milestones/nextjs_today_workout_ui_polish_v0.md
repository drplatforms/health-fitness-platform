# Next.js Today Workout UI Polish v0

Status:

```text
NEXTJS_TODAY_WORKOUT_UI_POLISH_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Polish the existing Next.js Today and Workout screens so the daily-driver experience feels tighter and more intentional without changing backend workout, recovery, nutrition, or user-routing behavior.
```

What was updated:

- Tightened the Today header into a shorter layout with:
  - `Today`
  - a long readable date
  - current user name plus inline selector
- Removed normal-surface user clutter such as:
  - `Real user`
  - `QA / Test User`
  - `(Test)` suffixes inside the selector
- Reworked the Today workout summary card to:
  - use `Today's Workout`
  - remove the generated workout title from the summary card
  - show compact real metadata such as exercise count, duration when available, and status
  - promote the workout detail link into a button-style action with status-aware wording
- Tightened the Workout page header and replaced backend-ish preview wording with plain user-facing copy.
- Reworked the Workout experience layout to:
  - keep a smaller top summary card
  - remove the `Preview Details` section entirely
  - move preview actions near the top of the exercises card
  - keep selected/start/complete actions close to the exercise flow
  - demote/remove generated workout titles from primary display
- Shrunk session notes into a compact side card and hid the section when there are no meaningful notes to show.

Boundaries preserved:

- No backend workout behavior, contracts, or routing rules were changed.
- URL `user_id` remains the source of truth.
- Workout preview, try-different-version, select, start, log-set, and complete flows remain in the existing component and API path.
- Completed workout handling remains protected from preview/logging controls.
- Recovery Check-In and Nutrition cards remain on Today and were not given new behavior.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`

Remaining risks:

- This milestone improves presentation only; it does not change the underlying Today workout summary contract, so richer compact metrics on the Today card still depend on future backend exposure.
- Manual cross-state smoke in production mode is still valuable for confirming preview, active, and completed behavior against live local backend data.
