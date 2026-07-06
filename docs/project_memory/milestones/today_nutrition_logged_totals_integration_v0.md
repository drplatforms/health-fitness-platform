# Today Nutrition Logged Totals Integration v0

Status:

```text
TODAY_NUTRITION_LOGGED_TOTALS_INTEGRATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Connect canonical food logging to the existing Today nutrition card by confirming the Today backend contract reflects canonical food log actuals through the shared target-vs-actual path.
```

What was integrated:

- The Today backend nutrition summary continues to read logged actuals from `build_target_vs_actual_nutrition_summary(...)`.
- Canonical food logs already enter that path through `food_entries` because canonical logging mirrors nutrients into the legacy food-entry read path.
- This milestone locked that integration in with focused Today service and Today route tests instead of adding a second canonical totals aggregation path.

Frontend touched:

- No frontend files were changed.
- The existing Next.js Nutrition Macro Card already renders the Today nutrition payload correctly, including the clean no-log state.

Today actuals source:

- Today actual calories, protein, carbs, and fat come from the existing target-vs-actual service.
- Canonical logged foods affect Today by updating the shared `food_entries` source that target-vs-actual already reads.
- A second Today-specific canonical rollup was intentionally not added to avoid double-counting risk.

Empty state behavior:

- No-log days remain `not_logged` with `null` logged macro values in the Today payload.
- The frontend continues to render that state as `No nutrition logged yet today.`

User/date separation:

- Today nutrition actuals remain scoped to the requested `user_id` and selected date.
- Added integration tests prove canonical logs for one user/date do not leak into another user or another date.

What remains deferred:

- Food logging UI
- Food search UI
- Serving/unit selector UX
- Meal builder
- Barcode scanning
- AI food parsing or image recognition
- Any broader Today redesign

Next recommended milestone:

- A narrow food logging UI milestone that uses canonical search plus the existing canonical logging route without changing the Today contract.
