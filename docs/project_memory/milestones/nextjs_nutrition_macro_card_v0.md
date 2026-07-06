# Next.js Nutrition Macro Card v0

Status:

```text
NEXTJS_NUTRITION_MACRO_CARD_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add a small nutrition status card to the Next.js Today page by reusing existing backend-owned macro targets and logged daily macro actuals.
```

Scope implemented:

- Extended the existing Today nutrition contract to include carbohydrate and fat targets plus logged carbohydrate and fat values.
- Added a compact Nutrition Macro Card to the Next.js Today page.
- Preserved the existing selected `user_id` flow so nutrition state stays user-specific.
- Added a clean empty-state message for dates with no nutrition logs.
- Added focused backend contract and route/service tests for the expanded nutrition payload.

Backend discovered:

- Existing read path already exists through `services/nutrition_target_vs_actual_service.py`.
- The Today contract already reused that service for calories and protein.
- Existing nutrition write paths are food-entry based (`/nutrition/log`, `/nutrition/{user_id}/log-canonical`, `/nutrition/{user_id}/log-serving`), not direct daily macro-total persistence.

Explicit deferral:

- Manual daily macro-total entry/update is deferred.
- This milestone does not add a direct macro-total write route, fake meal table, fake food database, or AI nutrition parser.

Files changed:

- `models/daily_driver_contract_models.py`
- `services/daily_driver_today_service.py`
- `frontend/src/app/page.tsx`
- `frontend/src/components/NutritionMacroCard.tsx`
- `frontend/src/types/dailyDriver.ts`
- `tests/test_daily_driver_contract_models.py`
- `tests/test_daily_driver_routes.py`
- `tests/test_daily_driver_today_service.py`
- `docs/project_memory/current_state.md`
- `docs/project_memory/milestones/nextjs_nutrition_macro_card_v0.md`

Boundaries preserved:

- Backend remains the only source of truth for nutrition targets and logged actuals.
- No long-term nutrition logging architecture was introduced.
- No USDA import, searchable local foods table, meal builder, barcode scan flow, or provider work was added.
