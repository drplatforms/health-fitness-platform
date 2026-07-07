# Canonical Food Starter Set Promotion Pack v0

Status: `CANONICAL_FOOD_STARTER_SET_PROMOTION_PACK_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW`

## Purpose

Create a deterministic backend workflow for expanding practical loggable canonical foods from already-imported raw USDA/source rows without importing a larger dataset or fabricating nutrition values.

## Implemented

- Added a reviewable starter-set definition covering everyday proteins, carbs/starches, fruits, vegetables, dairy/fats, and common extras.
- Added conservative candidate matching against existing `raw_food_source_records`.
- Added report buckets for `matched`, `skipped_missing`, `skipped_ambiguous`, `skipped_raw_only`, and `already_promoted`.
- Added a CLI at `scripts/promote_canonical_food_starter_set.py`.
- Reused the existing raw-source promotion service for canonical food creation, aliases, macro nutrient sync, and source provenance.

## Candidate Matching

- Matching only considers existing raw source rows.
- Default source filtering remains `USDA FoodData Central` plus `foundation_food`.
- Candidates must include at least one macro value.
- Candidate text must match all tokens for a starter definition search term.
- Prefer terms improve score; avoid terms reduce score.
- Exact top-score ties are reported as ambiguous instead of promoted.
- Missing source rows are reported instead of forced.

## Raw Handling

- Raw/uncooked meat, fowl, and fish candidates are not promoted as everyday starter items.
- If only raw/uncooked unsafe candidates exist for those items, the report uses `skipped_raw_only`.
- Raw produce remains eligible where raw is normal, such as tomatoes, lettuce, carrots, bananas, apples, and grape tomatoes.
- No raw source row becomes a direct user-facing log target.

## Promotion and Idempotency

- Non-dry-run promotion calls `promote_raw_source_record_to_canonical(...)`.
- Canonical foods, aliases, macro nutrients, and `food_source_links` are created through the existing promotion path.
- Source provenance preserves source name, source record id, raw source record id, and raw description through existing links and aliases.
- Existing primary source links are reported as `already_promoted` and are not duplicated.
- Dry-run builds the same candidate report without creating canonical foods, aliases, nutrients, or source links.

## CLI Usage

```powershell
.\.venv\Scripts\python.exe scripts/promote_canonical_food_starter_set.py --db-path fitness_ai.db --dry-run

.\.venv\Scripts\python.exe scripts/promote_canonical_food_starter_set.py --db-path fitness_ai.db --report-path tmp/starter_set_report.json
```

Optional arguments:

- `--limit`
- `--include-categories`
- `--report-path`

## Report Shape

The JSON report includes:

- `dry_run`
- `definition_count`
- `processed_count`
- `matched`
- `skipped_missing`
- `skipped_ambiguous`
- `skipped_raw_only`
- `already_promoted`
- `summary`

Each item includes the starter display name, category, status, source identity when available, raw description when available, canonical food id when promoted/already linked, aliases, nutrients synced, and a reason.

## Boundaries Preserved

- No full USDA dataset expansion.
- No FNDDS, SR Legacy, branded import expansion, or external data fetch.
- No admin/manual curation UI.
- No food logging UI, edit/delete, serving picker, diary/history, meal builder, barcode scanning, image recognition, or AI food parsing changes.
- No workout, recovery, provider, RAG, embeddings, vector search, or agent orchestration changes.
- No DB files, USDA datasets, CSVs, ZIPs, generated reports, or runtime artifacts are part of the milestone.

## Deferred

- Manual curation UI.
- Serving-size and household-unit curation.
- Larger reviewed canonical food expansion beyond source rows already present locally.
- AI/parser-assisted food logging.
- Barcode or image workflows.
