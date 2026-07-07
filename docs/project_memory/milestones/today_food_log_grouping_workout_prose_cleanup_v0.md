# Today Food Log Grouping + Workout Prose Cleanup v0

Current accepted baseline:

```text
ced70d0 Merge Today logged foods read-only list v0
```

Active frontend implementation milestone:

```text
Today Food Log Grouping + Workout Prose Cleanup v0
```

Requested status:

```text
TODAY_FOOD_LOG_GROUPING_WORKOUT_PROSE_CLEANUP_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

## Purpose

Make the Today and Workout surfaces more compact and data-first now that the core food logging loop is visible.

## Implemented scope

- Grouped the read-only `Logged today` food list by normalized meal type.
- Display labels normalize `breakfast`, `lunch`, `dinner`, and `snack`; missing or unknown meal types render as `Other`.
- Empty meal groups are hidden while the empty-day state remains `No foods logged yet today.`
- Kept explicit zero macro values visible while omitted macro values stay omitted from the compact row.
- Added compact per-meal item counts and a bounded internal scroll area for longer logged-food days.
- Placed `Logged today` and `Today's Workout` side-by-side inside the Today primary column on wide desktop viewports.
- Preserved mobile order as Nutrition, Log Food, Logged today, Today's Workout, Recovery.
- Removed low-value deterministic prose from the Workout page hero and Session Status area.
- Removed the Workout page `Session Notes` card instead of moving generic deterministic plan prose elsewhere.
- Changed Workout detail exercise cards to a two-column desktop grid and a single-column mobile grid.
- Preserved existing active workout logging controls.

## Boundaries preserved

- Backend behavior and contracts were not changed.
- Food search, food logging, logged-food refresh, Nutrition actual refresh, workout detail navigation, active workout logging, and Recovery Check-In behavior were not intentionally changed.
- No edit/delete food log flow, diary/history, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, provider behavior, recovery logic, nutrition calculation, food search change, or AI workout prose generation was added.
- No DB files, USDA datasets, ZIPs, CSVs, generated artifacts, or runtime outputs belong in this milestone.

## Deferred

- Food log editing/deleting.
- Full food diary/history.
- Meal builder or serving-size UX.
- AI food parsing or AI workout prose.
- Workout exercise-card redesign beyond the compact two-column layout.

## Validation target

```powershell
cd C:\projects\fitness_ai\frontend
npm run lint
npm run build
cd C:\projects\fitness_ai
git diff --check
```
