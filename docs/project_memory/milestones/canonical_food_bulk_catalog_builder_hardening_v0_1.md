# Canonical Food Bulk Catalog Builder Hardening v0.1

Status: `CANONICAL_FOOD_BULK_CATALOG_BUILDER_HARDENING_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Harden Bulk Catalog Builder v0 before any real promotion is run by reducing false duplicate-name skips caused by over-generic display-name curation.

## Problem Found

The first real dry-run after v0 merged promoted only a small subset of imported Foundation candidates and reported many `skipped_duplicate_name` rows. The main cause was display-name curation collapsing distinct foods into generic names such as:

- `Flour`
- `Cheese`
- `Rice`
- `Tomato`
- `Butter`
- `Cream`
- `Bread`
- `Oil`

This was safe but too conservative for building a useful catalog.

## Implemented

- Preserved meaningful qualifiers before duplicate-name checks.
- Added explicit curation for common variant families:
  - flour variants such as `Almond flour`, `Coconut flour`, `Whole wheat flour`, `Bread flour`, and `Brown rice flour`
  - cheese variants such as `Cheddar cheese`, `Mozzarella cheese`, `Parmesan cheese`, and `Feta cheese`
  - rice variants such as `Brown rice`, `White rice`, and `Black rice`
  - oat variants such as `Rolled oats` and `Steel cut oats`
  - tomato variants such as `Tomato paste`, `Tomato puree`, `Tomato sauce`, and `Roma tomato`
  - butter, cream, bread, and oil variants such as `Salted butter`, `Unsalted butter`, `Heavy cream`, `Sour cream`, `White bread`, `Whole wheat bread`, `Coconut oil`, and `Olive oil`
- Fixed over-broad oil matching so `Anchovies, canned in olive oil` becomes `Canned anchovies`, not `Olive oil`.
- Kept raw meat/fowl/fish protection unchanged.
- Kept ready-to-eat/canned/prepared fish/meat eligibility when the source row is clearly safe.
- Kept real duplicate protection for rows that share the same normalized display name and same macro profile.
- Added a fallback for materially different same-name rows to use a second-phrase display name instead of immediately skipping.

## Duplicate Behavior

The builder still reports `skipped_duplicate_name` when multiple source rows curate to the same display name and have the same macro profile. This handles true duplicate-style Foundation rows without choosing an arbitrary source.

When same-name candidates have materially different macro profiles, the builder attempts a more specific display name from the next USDA phrase before giving up.

## Tests Added

Focused tests now prove:

- flour variants do not collapse to `Flour`
- cheese variants do not collapse to `Cheese`
- rice variants do not collapse to `Rice`
- tomato paste/puree/sauce/roma do not collapse to `Tomato`
- butter, cream, bread, and oil qualifiers are preserved
- identical duplicate berries can still be skipped
- materially different same-name berry rows get more specific names
- anchovies canned in olive oil do not become olive oil
- representative dry-run promoted count improves when qualifier curation is active
- idempotency remains covered by existing bulk catalog tests

## Boundaries Preserved

- No real promotion is run by this milestone.
- No frontend files are intentionally changed.
- No food logging UI, serving picker, diary/history, admin UI, raw USDA review UI, AI parser, barcode scanner, workout, recovery, provider, RAG, embeddings, vector search, or agent orchestration changes are added.
- No DB files, generated reports, USDA datasets, ZIPs, or tmp artifacts are committed.

## Deferred

- Human review UI for duplicate resolution.
- Broader taxonomy/serving curation.
- Any real canonical promotion run.
