# Next.js Canonical Food Logging UI v0

Status:

```text
NEXTJS_CANONICAL_FOOD_LOGGING_UI_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add the first small Next.js food logging surface so users can search canonical foods, enter grams, log food, and see Today nutrition actuals refresh through the existing backend contract.
```

UI added:

- Added `frontend/src/components/FoodLoggingCard.tsx`.
- Placed the card under the existing Nutrition card on the Today page.
- Kept the layout compact, data-dense, and focused on search, grams, meal selection, and save.

Backend endpoints used:

- `GET /foods/canonical/search?q=<query>&limit=<n>`
- `POST /nutrition/{user_id}/log-canonical`

Canonical logging rule:

- The UI only logs `canonical_food_id`.
- No raw USDA source identifier, FDC identifier, or raw source row becomes a UI logging target.

Grams-first behavior:

- The UI requires grams for save.
- Macro preview is calculated client-side from per-100g canonical nutrient values.
- Logged save payload preserves grams as the source-of-truth amount.

Today refresh behavior:

- Successful save triggers `router.refresh()`.
- The existing Today backend contract continues to own nutrition actuals.
- No second Today-specific nutrition aggregation path was added.

Local runtime hotfix:

- Existing SQLite app DBs are upgraded through the normal database init path on FastAPI startup.
- Older `food_entries` tables now receive the canonical logging columns additively, without dropping or recreating the table.

What remains deferred:

- Serving-size/unit conversion
- Favorites or recent foods
- Food diary/history
- Edit/delete food logs
- Meal builder
- Barcode scanning
- AI parsing or image recognition
- Raw USDA review/promotion UI
