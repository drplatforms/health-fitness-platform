# USDA Raw Source Canonical Promotion v0

Last updated: 2026-07-06

## Purpose

Add a narrow backend pathway for reviewing USDA raw source rows and promoting selected rows into the existing curated canonical food tables.

## What was added

- A focused backend review helper for listing promotable USDA raw source rows.
- Default promotion-review filtering for `foundation_food`, with override support for review-mode inclusion of non-default USDA hierarchy rows.
- A deterministic promotion path from `raw_food_source_records` into:
  - `canonical_foods`
  - `canonical_food_aliases`
  - `canonical_food_nutrients`
  - `food_source_links`
- An opt-in scratch-database CLI for manual promotion smoke.

## Promotion behavior

- Promotion reads one `raw_food_source_records` row by internal id.
- If the raw row is already linked to a canonical food, reruns reuse that canonical food instead of creating a duplicate.
- If no source link exists, promotion reuses an existing canonical food with the same normalized name and food type when safe; otherwise it creates a new canonical food.
- USDA source identity is preserved through the linked raw source row:
  - `source_name`
  - `source_record_id` / USDA FDC ID
  - internal raw source record id
- Macro nutrients are synced from per-100g raw values into canonical nutrient rows.
- Missing macro values remain absent.
- Explicit `0` macro values remain `0`.

## What remains non-user-facing

- Raw USDA rows are still not the direct user-facing search path.
- No food search UI or food logging UI was added.
- No barcode, AI food parsing, or meal-builder flow was added.
- Promotion remains an explicit backend/review action.

## Next recommended milestone

Use the new promotion pathway to promote a small reviewed USDA starter set into canonical foods, then add a tightly scoped canonical-food logging flow that stays on curated canonical records only.
