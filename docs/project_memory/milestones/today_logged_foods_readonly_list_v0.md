# Today Logged Foods Read-Only List v0

Status: `TODAY_LOGGED_FOODS_READONLY_LIST_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Close the daily food logging visibility loop by showing what the selected user has logged today without adding diary management, edit/delete, or history scope.

## Implemented

- Added `GET /nutrition/{user_id}/canonical-logs?date=YYYY-MM-DD`.
- Added `get_daily_canonical_food_logs(...)` to read canonical food entries for one user/date.
- Returned compact entry fields: entry id, canonical food id, food name, grams, meal type, and stored macro snapshots.
- Preserved missing macro snapshots as `null`.
- Preserved explicit zero macro snapshots as `0`.
- Added a server-side frontend fetch helper for Today.
- Added the `Logged today` card under Log Food in the Today left column.
- Kept `router.refresh()` as the refresh mechanism after logging so Nutrition actuals and logged-food rows update together.
- Added the empty state: `No foods logged yet today.`

## Boundaries

- No edit/delete food log actions.
- No multi-day food diary or food history.
- No serving picker, meal builder, recent foods, favorites, barcode scanner, AI parser, image recognition, raw USDA review UI, or canonical promotion UI.
- No nutrition calculation, workout, recovery, provider, or user-routing changes.
- No raw USDA payload JSON or raw source identifiers are exposed.

## Validation

- Backend canonical logging/read endpoint tests.
- Frontend lint and production build.
- Ruff check and format-check on touched backend Python files.
- Root whitespace check.

## Deferred

- Food log edit/delete.
- Read-only food history across dates.
- Serving picker and household-unit display.
- Recent foods/favorites.
- Meal builder.
- Barcode, AI parser, and image recognition flows.
