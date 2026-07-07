# Today Workout Detail UX Refinement v0

Status: implementation complete, ready for Architecture review.

Branch:

```text
feature/today-workout-detail-ux-refinement-v0
```

## Purpose

Refine the Today and Workout detail screens after Today Main Loop Density Polish v0 so they feel more like a compact owner/operator dashboard.

## Implemented Scope

- Reworked the Today page desktop layout into independent left and right column stacks so Today's Workout sits directly below Log Food instead of waiting for the taller Recovery Check-In card.
- Preserved mobile Today order as Nutrition, Log Food, Today's Workout, Recovery Check-In.
- Reused existing current-workout payload data on Today to show compact exercise rows with set completion, reps, weight, and RIR when actual logged sets are available.
- Kept planned-only workout rows compact with planned sets/reps/RIR where available.
- Tightened the Workout detail status card from a repeated "Workout / Today's Workout / complete" block into a compact Session Status card.
- Removed redundant completed-workout status copy from the Workout detail hero card.
- Moved Execution Summary above Session Notes and made it visually more prominent.
- Kept Session Notes available below Execution Summary.

## Boundaries Preserved

- Backend behavior and contracts were not changed.
- Nutrition logging, canonical food search/logging, recovery scoring, workout lifecycle, workout logging/completion, provider behavior, and user routing were not changed.
- No food diary/history, edit/delete flow, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, USDA curation UI, dashboard framework, or collapsible-card system was added.
- No DB files, USDA datasets, CSVs, ZIPs, or generated runtime artifacts are part of the milestone.

## Deferred

- Food naming/curation changes such as reducing overuse of ", cooked" in canonical food names.
- Full workout detail redesign.
- New backend Today workout payload fields.
- Editing/deleting logged workout sets.
- Read-only food log history and food serving workflows.

## Validation Target

```powershell
cd C:\projects\fitness_ai\frontend
npm run lint
npm run build

cd C:\projects\fitness_ai
git diff --check
```
