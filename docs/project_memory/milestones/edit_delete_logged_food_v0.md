# Edit/Delete Logged Food v0

Current accepted baseline:

```text
53c559a Merge food log grouping and workout prose cleanup v0
```

Active full-stack implementation milestone:

```text
Edit/Delete Logged Food v0
```

Requested status:

```text
EDIT_DELETE_LOGGED_FOOD_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

## Purpose

Allow users to correct today's logged canonical food entries without turning Today into a full food diary.

## Implemented scope

- Added `PATCH /nutrition/{user_id}/canonical-logs/{entry_id}` for editing grams and meal type.
- Added `DELETE /nutrition/{user_id}/canonical-logs/{entry_id}` for deleting one canonical logged-food entry.
- Added backend service helpers that require both `entry_id` and `user_id`, with optional selected-date guards.
- Recalculate stored macro snapshots when grams change.
- Preserve missing macro values as `null` and explicit zero macro values as `0`.
- Preserve canonical food identity; edit does not change canonical food, food name, or entry date.
- Delete removes only the owned `food_entries` row and does not delete canonical foods, nutrients, aliases, or source links.
- Added frontend proxy/helper support for PATCH and DELETE.
- Added compact inline `Edit`, `Save`, `Cancel`, and two-step `Delete` controls to the grouped `Logged today` list.
- Refreshes the logged-food list and server-rendered Today nutrition after edit/delete through the existing local event plus `router.refresh()`.

## Ownership and validation behavior

- Wrong-user edits/deletes return a clean not-found response.
- Missing entry IDs return a clean not-found response.
- Selected-date mismatch returns a clean not-found response when the frontend sends the date guard.
- Invalid grams are rejected.
- Meal type is normalized/validated to `breakfast`, `lunch`, `dinner`, `snack`, or `other`.

## Boundaries preserved

- No full food diary/history, multi-date editor, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image recognition, raw USDA source review UI, canonical promotion UI, workout changes, recovery changes, or broad Today redesign was added.
- Raw USDA/source rows are not logged or mutated directly.
- Backend nutrition actuals remain backend-owned through existing `food_entries` and nutrient rollup paths.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

## Validation target

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q
.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py
.\.venv\Scripts\python.exe -m ruff format --check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py
cd C:\projects\fitness_ai\frontend
npm run lint
npm run build
cd C:\projects\fitness_ai
git diff --check
```
