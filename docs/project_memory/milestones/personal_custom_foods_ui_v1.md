# Personal Custom Foods UI v1

## Status

```text
PERSONAL_CUSTOM_FOODS_UI_V1_IMPLEMENTED_AWAITING_ARCHITECTURE_REVIEW
```

This milestone is implemented locally but is not accepted, merged, closed, or declared product-ready. Architecture diff review and controlled browser smoke remain pending.

## Git State

- Starting branch: `main`.
- Starting commit: `8a7c5d60767d5573d85c2e84325bbe304c8eeef1`.
- Implementation branch: `feature/personal-custom-foods-ui-v1`.
- Changes remain unstaged and uncommitted for Architecture review.

## Delivered UI

- Added compact personal-food list, create, and edit pages under `/personal-foods`.
- Preserved `user_id` and the selected Today date through management navigation.
- Added active/archived search, inline archive confirmation, and restore without modals, browser-native confirmation, new icon libraries, or design-system dependencies.
- Added nutrition-label and per-100g modes. Blank nutrient inputs are omitted rather than converted to zero, and edits prefill from the current revision's entered values.
- Added a `My foods` action to the existing Log Food card.
- Merged canonical and personal searches concurrently after the existing two-character threshold. Personal results are visibly labeled and do not suppress same-name canonical results.
- Added grams and saved-serving personal-food logging with resolved-grams preview and a 5,000 g client guard.
- Added refresh events so successful personal logging updates Today and Logged today while preserving the active user/date.
- Extended Logged today with a discriminated canonical/personal union and personal amount, saved-serving, meal, and delete controls.

## Architecture Corrections

- Canonical and personal searches now settle independently. A successful source remains visible if the other source fails, while a double failure retains the concise full-search error. The two-character threshold, exact personal-match ordering, `My food` label, canonical duplicates, and discriminated result types remain unchanged.
- Canonical and personal Logged today refreshes now settle independently. Successful source data is replaced, failed-source entries already on screen are preserved, partial availability is reported concisely, and superseded concurrent refresh results cannot overwrite the latest refresh.
- Switching between Nutrition label and Per 100g clears all four nutrient fields plus prior success/error state while preserving food name, brand, and serving context. The user must deliberately enter nutrients for the new basis, and blank nutrient fields still submit as unknown rather than zero.
- The Nutrition summary now listens to the same successful canonical/personal log event contract used by Logged today. Personal create, amount/meal edit, and delete events refresh backend-owned Today totals only after the mutation succeeds; failed mutations dispatch no false refresh.

## Bounded Backend Additions

- Added `GET /nutrition/{user_id}/personal-logs?date=YYYY-MM-DD`.
- Added `PATCH /nutrition/{user_id}/personal-logs/{entry_id}` for grams, stored-revision saved-serving quantity, or meal-only updates.
- Added `DELETE /nutrition/{user_id}/personal-logs/{entry_id}?date=YYYY-MM-DD`.
- Personal-log reads and mutations require user ownership and personal-food provenance. Canonical and raw entries cannot be changed through these endpoints.
- Update calculations join the entry's stored `personal_food_revision_id`; an old log never switches to the personal food's current revision.
- Historical `food_name_snapshot`, exact revision identity, known nutrient snapshots, and unknown nutrient nulls remain public-safe. Internal legacy IDs and names are not returned.
- No schema or database-initialization change was required.

## Validation

- Personal-food model/service/logging/API tests: `84 passed`.
- Canonical logging, canonical edit/delete, recents, Target-vs-Actual, and API smoke regression tests: `93 passed`.
- Ruff check: passed for `api`, `services`, `models`, and `tests`.
- Python compile: passed for the touched nutrition route and personal-food logging service.
- Frontend ESLint: passed.
- Next.js production build: passed, including `/personal-foods`, `/personal-foods/new`, `/personal-foods/[personalFoodId]`, and the personal-food/log proxy routes.
- Post-Architecture-correction frontend ESLint: passed.
- Post-Architecture-correction Next.js production build: passed; static page generation completed `23/23`, and the expected route table was produced.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; checker tests: `29 passed`.
- `git diff --check`: passed.
- Browser smoke: intentionally deferred to Architecture by the implementation handoff.

## Database Safety

- Automated backend validation used pytest temporary databases.
- No backend or frontend runtime was started against the real ignored database.
- The real `fitness_ai.db` began at SHA-256 `5829A88632674377CC4A7AB5BD3D2022F01128A474EF859FB270F7B77768BA38`.
- Final verification matched the starting database: length `5,443,584`, modification time `2026-07-15T00:37:43.3678125Z`, and SHA-256 `5829A88632674377CC4A7AB5BD3D2022F01128A474EF859FB270F7B77768BA38`.

## Deferred Scope

Recipes, recipe ingredients, saved meals, meal templates, barcode scanning, OCR, external food imports, AI food matching, AI nutrition generation, meal planning, nutrition-gap recommendations, new dashboard analytics, authentication changes, schema changes, workout changes, and report changes remain outside this milestone.
