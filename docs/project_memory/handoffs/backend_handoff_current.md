# Backend Handoff Current

Milestone: Snapshot Ownership / Main Acceptance Artifact Policy v1

Status: authorized docs/process + artifact closeout.

Source baseline: `main` at `2279665`.

Branch: `feature/snapshot-ownership-main-acceptance-policy-v1`.

Milestone type: docs/process + artifact closeout.

Commit-check mode: docs.

## Why this exists

Nutrition Serving Unit Logging Backend v1 is accepted and merged.

Current accepted serving-unit backend state:

- Feature commit: `8b285c6 Add nutrition serving unit logging backend`
- Main merge commit: `2279665 Merge nutrition serving unit logging backend v1`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`
- QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`

QA noted that no new main snapshot was created after merge.

That is technically explainable but operationally confusing, because feature-branch implementation artifacts and canonical accepted main artifacts can have different hashes.

## Current task

Create/record the canonical accepted main snapshot and update project memory with the artifact ownership policy.

Canonical accepted snapshot for this milestone:

`fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`

## Snapshot ownership policy to document

Backend owns:

- implementation;
- focused tests;
- validation;
- feature branch;
- feature commit;
- implementation handoff;
- optional feature implementation snapshot.

Architecture / TPM / Project Memory owns:

- accepted milestone state;
- merge-to-main authorization;
- canonical main commit tracking;
- canonical accepted snapshot naming;
- continuity artifact policy.

QA owns:

- validation against accepted main;
- pass/fail evidence;
- defect routing.

Feature snapshots:

- may exist as implementation artifacts;
- are not final accepted continuity snapshots unless explicitly designated;
- may have hashes that differ from main merge commits.

Canonical accepted snapshots:

- should be created from `main` after Architecture acceptance / merge;
- should use the accepted main commit hash in the filename;
- should not be committed to the repo;
- should be referenced in project memory.

Future handoffs must distinguish:

- feature commit;
- main merge commit;
- feature snapshot, if any;
- canonical accepted snapshot.

## Serving-unit backend accepted behavior

Accepted behavior from Nutrition Serving Unit Logging Backend v1:

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

## Scope preserved

Do not change:

- Python runtime code;
- API routes;
- schema/database behavior;
- Streamlit;
- AI/provider/Ollama/CrewAI behavior;
- Target-vs-Actual behavior/design;
- nutrition target formulas;
- food suggestions;
- meal planning;
- workout/recovery/report behavior;
- tests unless docs/tooling checks require it.

Do not use repo-wide mutating formatter commands for this docs/process milestone.

## Required project-memory updates

Update current project-memory files so they show:

- Nutrition Serving Unit Logging Backend v1 accepted and merged.
- Feature commit: `8b285c6`.
- Main merge commit: `2279665`.
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`.
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`.
- Next implementation milestone: Canonical Serving Unit Discovery API v1.

## Expected next implementation milestone

Canonical Serving Unit Discovery API v1.

Goal:

Expose active serving units for an active canonical food through a public-safe endpoint.

Potential endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

This should precede Nutrition Serving Unit Logging Streamlit UI v1.

## Process notes

Use explicit staging only.

Do not use `git add .`.

Push must be its own separate phase.

## Runtime command continuity anchor

Linux pull/validation should use explicit commands only:

```bash
cd ~/projects/fitness-ai-platform
git fetch origin --prune
git switch feature/snapshot-ownership-main-acceptance-policy-v1
git pull --ff-only origin feature/snapshot-ownership-main-acceptance-policy-v1
source .venv/bin/activate
```

Do not use `lpush`.
