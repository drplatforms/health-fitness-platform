# Canonical Food Search Result Curation v0

Status: `CANONICAL_FOOD_SEARCH_RESULT_CURATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Make canonical food search feel practical for daily logging by returning cleaner, human-friendly labels while preserving canonical IDs, source provenance, and nutrient truth.

## Implemented

- Added deterministic display-name curation for public canonical search responses.
- Reused the same curation helper during raw-source promotion so new promoted rows can store practical names such as `Hummus`.
- Preserved original/raw USDA descriptions through existing source links and aliases instead of exposing raw rows as log targets.
- Added curated starter aliases during canonical seed.
- Adjusted oatmeal seed aliases so `oatmeal` resolves to cooked oatmeal and `oats` still resolves to dry oats.
- Added default raw meat/fowl/fish ranking penalties for ordinary searches.
- Kept raw meat/fowl/fish discoverable when the query explicitly includes `raw` or `uncooked`.
- Kept non-meat raw foods eligible in normal search, including raw tomato-style records.

## Curation Rules

- Clean safe everyday labels, including `Hummus`, `2% milk`, `Egg`, `Oatmeal`, `Chicken breast`, `Tuna`, and `Grape tomatoes`.
- Do not relabel explicit raw meat/fowl/fish as cooked or everyday cooked food.
- Keep explicit raw meat/fowl/fish visibly raw, such as `Chicken breast, raw`.
- Do not change nutrient amounts when names or aliases are curated.
- Keep source identity available through existing canonical source summaries and links.

## Boundaries

- No frontend changes.
- No canonical logging behavior changes.
- No nutrition rollup, serving-unit, workout, recovery, provider, or user-routing changes.
- No raw USDA rows became direct user-facing log targets.
- No full taxonomy, admin curation UI, raw source review UI, serving picker, food history, edit/delete logging, meal builder, barcode flow, AI parser, or image recognition was added.

## Validation

- Focused canonical search/normalization/promotion tests.
- Canonical logging regression.
- Ruff check and format-check on touched Python files.

## Deferred

- Larger food taxonomy.
- Manual curation workflow.
- Serving-size and household-unit curation.
- Food diary/history and edit/delete UX.
- AI food parsing, barcode scanning, and image recognition.
