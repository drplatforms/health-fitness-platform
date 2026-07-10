# Frontend Instructions

These rules extend the repository root `AGENTS.md` for work under `frontend/`.

## UI Direction

- Keep layouts compact, data-dense, practical, and easy to scan.
- Avoid excessive instructional prose and giant per-item cards unless the milestone explicitly approves them.
- Render persisted backend state; do not invent client-side health truth or silently diverge from backend state.
- Preserve accessible names, labels, focus behavior, and keyboard-operable controls.
- Do not add automatic progression, load changes, deloads, or health recommendations without explicit Architecture approval.

## Workout Safety

When touching workout UI, preserve actual-set logging, edit, delete, cancel, completion review, progression-history context, and existing persisted-state transitions unless the milestone explicitly changes them.

## Required Validation

- Run `npm run lint` and `npm run build` from `frontend/`.
- Run production-mode browser smoke; lint/build do not replace interaction-level verification.
- Inspect the affected workflow at a mobile viewport around 390px.
- Check browser console errors and horizontal overflow.
- Verify relevant controls have stable accessibility names and keyboard behavior.
- Use a temporary database copy or safe test user, and clean all smoke artifacts afterward.
