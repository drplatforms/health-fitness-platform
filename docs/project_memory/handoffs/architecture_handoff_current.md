# Architecture Handoff Current

Milestone: Snapshot Ownership / Main Acceptance Artifact Policy v1

Status: docs/process + artifact closeout authorized.

Source baseline: `main` at `2279665`.

Branch: `feature/snapshot-ownership-main-acceptance-policy-v1`.

Milestone type: docs/process + artifact closeout.

## Review focus

Architecture should verify that project memory now distinguishes:

1. Feature implementation artifacts.
2. Canonical accepted main artifacts.

Primary review decisions:

1. Confirm Nutrition Serving Unit Logging Backend v1 is recorded as accepted and merged.
2. Confirm feature commit is recorded as `8b285c6`.
3. Confirm main merge commit is recorded as `2279665`.
4. Confirm feature snapshot is preserved as implementation artifact only.
5. Confirm canonical accepted snapshot is recorded as:
   `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`
6. Confirm future handoffs must distinguish feature commit, main merge commit, feature snapshot, and canonical accepted snapshot.
7. Confirm next implementation milestone routes to Canonical Serving Unit Discovery API v1.
8. Confirm no runtime/API/Streamlit/provider changes were made.

## Snapshot ownership policy

Architecture decision to preserve:

Feature snapshots:

- may exist as implementation artifacts;
- are optional;
- are not final accepted continuity snapshots unless explicitly designated;
- may have hashes that differ from main merge commits.

Canonical accepted snapshots:

- are created from `main` after Architecture acceptance / merge;
- use the accepted main commit hash in the filename;
- are not committed to the repo;
- are referenced in project memory.

## Serving-unit backend closeout state

Nutrition Serving Unit Logging Backend v1:

- Feature commit: `8b285c6 Add nutrition serving unit logging backend`
- Main merge commit: `2279665 Merge nutrition serving unit logging backend v1`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`
- QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`

Accepted behavior:

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

## Recommended final Architecture decision after review

Accept Snapshot Ownership / Main Acceptance Artifact Policy v1.

Recommended final status:

`SNAPSHOT_OWNERSHIP_MAIN_ACCEPTANCE_ARTIFACT_POLICY_V1_ACCEPTED`

## Recommended next implementation milestone

Canonical Serving Unit Discovery API v1.

Purpose:

Expose active serving units for an active canonical food through a public-safe backend endpoint so Streamlit can later build a serving-unit picker without direct DB lookup or invented mappings.

Potential endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Rules:

- only active canonical foods;
- only active serving units;
- no raw source payloads;
- no raw SQL/debug output;
- no AI/provider involvement;
- no Streamlit mapping/inference;
- backend remains source of truth.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` is now the canonical Linux runtime launcher.

`wapp` remains Windows-local only.

Linux is the canonical FastAPI + Streamlit app runtime.
