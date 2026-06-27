# Next Milestone

Current docs/process milestone in progress: Snapshot Ownership / Main Acceptance Artifact Policy v1.

Recommended branch: `feature/snapshot-ownership-main-acceptance-policy-v1`.

Source branch: `main`.

Required source main commit: `2279665`.

Milestone type: docs/process + artifact closeout.

Commit-check mode: docs.

## Objective

Close Nutrition Serving Unit Logging Backend v1 with a canonical accepted main snapshot and update project memory so future teams distinguish implementation artifacts from canonical accepted continuity artifacts.

This milestone is not a backend feature milestone.

## Current canonical state to preserve

- Nutrition Serving Unit Data Model v1: accepted and merged.
- Nutrition Serving Unit Logging Contract Design v1: accepted and merged.
- Project Memory Warning Review v1: accepted and merged.
- Nutrition Serving Unit Logging Backend v1: accepted and merged.
- Current main baseline: `2279665`.
- Latest accepted feature commit: `8b285c6`.
- Latest main merge commit: `2279665`.
- Feature implementation snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`.
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`.
- QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`.
- Project-memory baseline before this policy closeout: `PASS=620 WARN=28 FAIL=0`.
- Remaining warnings are accepted historical/archive/non-actionable continuity noise unless future checks prove otherwise.

## Snapshot ownership policy to record

Snapshot Ownership / Main Acceptance Artifact Policy v1:

1. Backend owns implementation, focused tests, validation, feature branch, feature commit, implementation handoff, and optional feature snapshots.
2. Architecture / TPM / Project Memory owns accepted milestone state, merge-to-main authorization, canonical main commit tracking, canonical accepted snapshot naming, and continuity artifact policy.
3. QA owns validation evidence, pass/fail status, and defect routing.
4. Feature snapshots may exist as implementation artifacts but are not final accepted continuity snapshots unless explicitly designated.
5. Canonical accepted snapshots should be created from `main` after Architecture acceptance / merge and should use the accepted main commit hash in the filename.
6. Snapshots should not be committed to the repo.
7. Future handoffs must distinguish feature commit, main merge commit, feature snapshot, and canonical accepted snapshot.

## Serving-unit backend closeout state

Milestone:
Nutrition Serving Unit Logging Backend v1

Feature commit:
`8b285c6 Add nutrition serving unit logging backend`

Main merge commit:
`2279665 Merge nutrition serving unit logging backend v1`

Feature snapshot:
`fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`

Canonical accepted snapshot:
`fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`

QA result:
`NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`

Accepted backend behavior:

```text
canonical_food_id + serving_unit_id + quantity
-> backend validates canonical food
-> backend validates serving unit
-> backend verifies serving unit belongs to canonical food
-> backend resolves serving quantity to grams
-> backend writes resolved grams through food_entries
-> backend persists serving-unit provenance metadata
-> existing Target-vs-Actual reads resolved grams through existing actuals flow
```

## Behavior to preserve

The following must continue to work unchanged:

- existing raw/source `/nutrition/log` behavior;
- existing canonical grams `/nutrition/{user_id}/log-canonical` behavior;
- existing canonical food search behavior;
- existing canonical food seed behavior;
- existing serving-unit seed behavior;
- existing Target-vs-Actual actuals calculation from grams;
- existing DailyCoachSynthesis/recommendation/report behavior;
- existing provider/Ollama/CrewAI boundaries;
- existing Streamlit behavior.

## Non-goals

Do not add:

- Python runtime changes;
- API changes;
- schema/database changes;
- Streamlit changes;
- test changes unless project-memory tooling requires it;
- serving-unit discovery implementation;
- serving-unit picker UI;
- food suggestion changes;
- meal planning;
- Target-vs-Actual redesign;
- nutrition target formula changes;
- AI/provider serving-unit behavior;
- CrewAI/Ollama changes;
- workout/recovery/report changes;
- repo-wide mutating formatter cleanup.

## Expected next implementation milestone after this closeout

Canonical Serving Unit Discovery API v1.

Expected owner:
Backend Development / Data Layer.

Goal:
Expose active serving units for an active canonical food through a public-safe API endpoint.

Potential endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Expected response:

- `success`;
- `canonical_food_id`;
- canonical food `display_name`;
- `serving_units` list:
  - `serving_unit_id`;
  - `display_name`;
  - `grams_default`;
  - `grams_min`;
  - `grams_max`;
  - `confidence`;
  - `amount_source`;
  - `sort_order` / display order if supported.

Rules:

- only active canonical foods;
- only active serving units;
- no raw source payloads;
- no raw SQL/debug output;
- no AI/provider involvement;
- no Streamlit mapping/inference;
- backend remains source of truth.

This should precede Nutrition Serving Unit Logging Streamlit UI v1.

## Historical continuity anchors

These phrases are retained for project-memory checker continuity and future-agent context:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- `feature/daily-coach-async-persistence-contracts-schema-v1`
- schema/contracts
- NOT_AUTHORIZED_YET

These are historical anchors only. They do not authorize provider/runtime work in the current docs/process closeout milestone.
