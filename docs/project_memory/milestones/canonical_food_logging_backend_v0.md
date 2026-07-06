# Canonical Food Logging Backend v0

Last updated: 2026-07-06

## Purpose

Add the backend write path that logs canonical foods by `canonical_food_id` and grams, then makes those logged actuals available for daily nutrition rollups.

## What was added

- Hardened the existing canonical logging route at `POST /nutrition/{user_id}/log-canonical`.
- Preserved the canonical-only logging rule: logging consumes `canonical_food_id`, not raw USDA identifiers.
- Persisted canonical linkage and macro snapshots on `food_entries`:
  - `canonical_food_id`
  - `meal_type`
  - `notes`
  - `calories`
  - `protein_g`
  - `carbs_g`
  - `fat_g`
- Added a canonical-only daily macro rollup helper and a small read route for the rollup.

## Logging behavior

- Grams remain the calculation source of truth.
- Canonical nutrients are read from `canonical_food_nutrients`.
- Legacy `foods` / `food_nutrients` / `food_entries` compatibility is preserved through the existing write-through path so current nutrition actuals keep working.
- Missing macro values remain absent.
- Explicit zero macro values remain zero.

## Deferred on purpose

- No Next.js food logging UI.
- No serving picker requirement for gram logging v0.
- No barcode, AI food parsing, or meal builder flow.
- No raw USDA direct logging path.

## Next recommended milestone

Use the canonical logging backend and search backend together to add a small UI flow for search → choose canonical food → enter grams → log food, without exposing raw USDA rows directly.
