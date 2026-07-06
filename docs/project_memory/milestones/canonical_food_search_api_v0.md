# Canonical Food Search API v0

Last updated: 2026-07-06

## Purpose

Add a tightly scoped backend search API for canonical foods only so future food logging/search stays on curated canonical records instead of raw USDA source rows.

## What was added

- Hardened the canonical food search endpoint at `GET /foods/canonical/search`.
- Preserved canonical-only search behavior through `canonical_foods` and `canonical_food_aliases`.
- Added compact default source summary output when a canonical food has a linked source record.
- Preserved compact per-100g macro output from canonical nutrient rows only.

## Search behavior

- Empty query returns a safe empty result.
- Non-empty queries shorter than the minimum search length still fail with a small deterministic validation error.
- Name and alias matches remain supported.
- Stable ordering remains based on exact/prefix/substring ranking plus deterministic fallback ordering.
- Alias aggregation is now deterministic.

## Data boundaries

- Search results are canonical-only.
- The endpoint does not directly return `raw_food_source_records` as user-facing results.
- Raw `source_payload_json` remains hidden from API output.
- Missing macros remain absent.
- Explicit zero macros remain zero.

## What comes next

Use this canonical-only search path as the read side for a narrow canonical food logging backend milestone without exposing raw USDA rows directly to the future UI.
