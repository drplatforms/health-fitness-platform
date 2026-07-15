# Personal Custom Foods UI v1

## Status

```text
PERSONAL_CUSTOM_FOODS_UI_V1_ACCEPTED_MERGED_AND_CLOSED
```

## Accepted Git State

- Starting main: `8a7c5d60767d5573d85c2e84325bbe304c8eeef1`.
- Feature implementation: `f1df5fb Add personal custom foods UI`.
- Accepted merge: `0715c63 Merge personal custom foods UI v1`.
- Final docs-only closeout and snapshot hashes are authoritative in Git after this memory update.

## Delivered Product Workflow

- Added compact personal-food management under `/personal-foods`, including active and archived views, search, create, edit/revise, archive, and restore.
- Added shared create/edit forms for Nutrition label and Per 100g input bases.
- Blank nutrients remain unknown rather than being converted to zero.
- Switching input basis clears nutrient values instead of silently reinterpreting the same numbers under a different basis.
- Added a `My foods` entry point to the existing Log Food card.
- Normal Log Food search now requests canonical and personal foods concurrently after the existing two-character threshold.
- Personal results carry a `My food` label while same-name canonical results remain available.
- Personal foods support grams logging and stored-serving logging when a saved serving exists.
- Logged today now presents canonical and personal entries through a discriminated UI union.
- Personal logged entries support amount edits, stored-serving quantity edits, meal edits, and deletion.
- Successful canonical and personal log mutations refresh backend-owned Today nutrition totals without requiring a browser reload.

## Bounded Backend Support

Added:

- `GET /nutrition/{user_id}/personal-logs?date=YYYY-MM-DD`
- `PATCH /nutrition/{user_id}/personal-logs/{entry_id}`
- `DELETE /nutrition/{user_id}/personal-logs/{entry_id}?date=YYYY-MM-DD`

Accepted behavior:

- Personal-log reads and mutations require user ownership and personal-food provenance.
- Canonical/raw entries cannot be modified through personal-log endpoints.
- Date scoping is preserved.
- Amount edits recalculate nutrition from the exact `personal_food_revision_id` stored on the original log entry.
- A historical log never switches to a newer personal-food revision.
- Historical food-name snapshots and known/unknown nutrient state remain stable.
- Internal legacy IDs and names remain hidden from public responses.
- No schema or database-initialization change was added by UI v1.

## Architecture Corrections

- Canonical and personal search failures settle independently; one successful source remains usable if the other fails.
- Canonical and personal Logged today refreshes settle independently; successful source data updates while failed-source data already on screen is preserved.
- Superseded concurrent refreshes cannot overwrite newer results.
- Switching between Nutrition label and Per 100g clears all nutrient fields and prior result messages while preserving food identity and serving context.
- Nutrition summary refreshes use the same successful logging-event contract as Logged today.
- Failed mutations dispatch no false refresh event.

## Validation

Pre-merge implementation validation:

- Personal-food model/service/logging/API tests: `84 passed`.
- Canonical logging, canonical edit/delete, recents, Target-vs-Actual, and API smoke regression slice: `93 passed`.
- Ruff check: passed.
- Ruff format check: passed.
- Python compile: passed.
- Frontend ESLint: passed.
- Next.js production build: passed.
- Static generation: `23/23`.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`.
- Project-memory tests: `29 passed`.
- `git diff --check`: passed.

Merged-main closeout validation:

- Targeted personal-food backend regression: passed.
- Targeted nutrition/canonical regression: passed.
- Ruff check and format check: passed.
- Python compile: passed.
- Frontend lint: passed.
- Next.js production build: passed.
- Project-memory checker and tests: passed.
- `git diff --check`: passed.

## Browser Acceptance

Browser smoke passed against the production Next.js build on port `3100`.

Accepted smoke coverage included:

- create a personal food;
- manage active and archived personal foods;
- discover personal foods through normal Log Food search;
- confirm `My food` labeling;
- log by grams;
- log by stored serving;
- confirm Logged today updates;
- confirm Today nutrition totals refresh;
- edit personal logged amount;
- edit meal;
- delete a personal log;
- revise a personal food;
- confirm historical logs remain tied to the original revision and name snapshot;
- archive and restore;
- verify canonical food search/logging remains functional;
- inspect desktop and narrow/mobile layout.

UX follow-up:

- The `My foods` action passed functional acceptance but is too visually subtle in the current Log Food card. Improve discoverability during a future navigation/UI-polish pass rather than reopening this milestone.

## Database Accounting

The browser smoke created intentional personal-food test data in the real local database.

The hash therefore changed from the pre-smoke baseline. A follow-up diagnostic confirmed the delta matched the expected smoke-created personal foods/revisions/log entries rather than corruption.

Post-smoke database SHA-256:

```text
7269CF76E3C4AAE714E6D168CE9E5B30BEDD28F50FFCC8FAC8565E5CC0CBE5B3
```

The milestone is accepted with that local smoke data present. No destructive recovery or rollback is required.

## Deferred Scope

Still deferred:

- recipes;
- saved meals;
- meal templates;
- barcode scanning;
- OCR;
- external food imports;
- AI food matching;
- AI nutrition generation;
- meal planning;
- nutrition-gap recommendation expansion;
- authentication changes;
- new schema design;
- workout behavior changes;
- report behavior changes.

## Next Milestone

```text
Public Project Rebrand and README Refresh v1
```

The next milestone should:

- rename the public project from the obsolete AI-first identity to `Health & Fitness Platform`;
- rename the GitHub repository;
- update the GitHub description;
- replace stale GitHub topics, including AI/provider-specific topics that no longer represent the product;
- rewrite the README around the current nutrition, training, recovery, longitudinal-data, deterministic-backend, and product-workflow capabilities;
- update the LinkedIn project title and description;
- preserve accurate historical references to prior provider/AI experiments where they remain useful architecture history rather than public branding.
