# Meal Builder v1

Current implementation branch: `feature/meal-builder-v1`.

Base branch: `main` at `5fa99e4 Merge mobile daily-driver navigation and compaction v1`.

Status:

```text
MEAL_BUILDER_V1_IMPLEMENTATION_CANDIDATE_READY_FOR_ARCHITECTURE_REVIEW
```

## Implemented Scope

- Added user-owned `saved_meals` and ordered `saved_meal_items` tables through the existing additive, idempotent database initialization path.
- Saved meal names are whitespace-normalized and case-insensitively unique per user. Different users may reuse the same name.
- Saved meal items reference the existing canonical or personal food systems and persist an authoritative positive `resolved_grams` amount.
- Canonical serving-unit and personal-serving inputs are resolved by the backend when a meal is saved. Familiar serving metadata is retained as optional provenance while saved grams remain stable.
- Create, list, detail, full-definition update, archive, restore, and log operations enforce strict user ownership.
- Meal detail and list responses calculate current calories, protein, carbohydrates, and fat from active canonical nutrition or the current personal-food revision. Aggregate macros are not persisted.
- Missing macro values remain limited data instead of being coerced to zero. Item-level availability and validation reasons remain visible when a referenced food becomes inactive or archived.
- Editing supports rename, default meal type changes, amount changes, add/remove, and accessible Move Up / Move Down ordering.
- Whole-meal logging prevalidates every item and inserts all existing-style canonical and personal `food_entries` in one SQLite transaction. Any validation or insertion failure rolls back every item.
- Canonical entries reuse the existing legacy write-through nutrition path through new cursor-aware internal helpers. Personal entries snapshot the current active revision and name exactly as ordinary personal logging does.
- Valid unchanged canonical serving provenance is copied to the existing serving metadata table. If the serving unit is inactive, missing, or now resolves to different grams, logging falls back to the meal's authoritative saved grams.
- The dedicated Food workspace now has Log Food, Meals, and My Foods tabs without adding a primary navigation destination.
- The Meals panel supports compact active/archived lists, one-tap logging when a default meal type exists, an inline meal-type chooser otherwise, edit, archive, restore, and item-level invalid-state messaging.
- The meal editor reuses canonical and personal food search plus canonical/personal serving information, supports stable gram editing and item reordering, and shows a compact draft macro estimate derived from backend-returned current food data.
- Successful meal logging remains in the Food workspace, refreshes server-owned nutrition totals, and dispatches the existing canonical and personal logged-food events so Logged Foods refreshes without a manual reload.
- Meal logging always sends the Food workspace's visible `targetDate`; no server-local date is introduced by the frontend flow.

## Boundaries Preserved

- Meal logging creates normal individual food entries; no meal-log grouping, group edit/delete, parallel nutrition totals, recipe/yield, meal planning, barcode-in-builder, AI suggestion, provider, or sharing system was added.
- Existing canonical, serving-unit, personal-food revision, recents, Logged Foods edit/delete, Today nutrition, barcode scanning, daily navigation, and live/explicit-date contracts remain authoritative.
- Architecture acceptance state in `docs/project_memory/current_state.md` and `docs/project_memory/project_state.json` remains unchanged.
- No dependency or destructive migration was added.

## Validation Completed

- New saved-meal service, transaction, and API tests: `18 passed`.
- Combined saved-meal plus directly relevant canonical logging, serving-unit logging/editing, personal-food service/logging/API, recents, target-vs-actual, and daily-driver regression slice: `215 passed`.
- Ruff check passed for all touched Python files.
- Ruff format-check passed for all touched Python files.
- Frontend helper regression tests: `14 passed`.
- Frontend `npm run lint` passed.
- Frontend production `npm run build` passed and generated the saved-meal proxy routes.
- Project-memory tests: `29 passed`.
- Project-memory checker: `PASS=608`, `WARN=39`, `FAIL=0`.
- Isolated production browser smoke passed against a temporary copy of the database at 360px, 390px, and desktop widths. It covered canonical-only and mixed canonical/personal meals; canonical gram and personal-serving inputs; create, edit, amount change, add/remove, reorder, default and explicit meal-type logging, repeat logging, archive, restore, immediate Logged Foods and nutrition-total refresh, Light/Dark/System themes, and Log Food, My Foods, and barcode-scanner regression surfaces.
- Browser smoke produced no console warnings or errors and no horizontal overflow at the checked widths.
- The canonical `fitness_ai.db` SHA-256 remained `210c6fe35abe5280a706209ef0d6b40dc37b457f78a3402f49484c6a51aacf3b` through final validation and after smoke cleanup. The isolated smoke used only `tmp/meal_builder_smoke.db`; its database, launcher, logs, and local processes were removed after validation.
