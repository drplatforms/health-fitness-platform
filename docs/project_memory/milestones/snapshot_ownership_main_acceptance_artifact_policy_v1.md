# Snapshot Ownership / Main Acceptance Artifact Policy v1

Status: authorized / docs-process patch drafted.

Milestone type: docs/process + artifact closeout.

Commit-check mode: docs.

Branch: `feature/snapshot-ownership-main-acceptance-policy-v1`.

Source branch: `main`.

Required source main commit: `2279665`.

## Purpose

Nutrition Serving Unit Logging Backend v1 exposed a process ambiguity:

- Backend produced a feature-branch implementation snapshot from commit `8b285c6`.
- Architecture later merged and accepted the work on `main` at `2279665`.
- QA passed the accepted backend milestone.
- No new main snapshot was created immediately after merge.

That is technically explainable but operationally confusing.

This milestone establishes the project rule that canonical accepted snapshots should be created from accepted `main` commits after Architecture acceptance / merge, while feature snapshots remain optional implementation artifacts.

## Architecture decision

Canonical accepted snapshots should be created from accepted `main` commits after Architecture acceptance / merge.

Backend may still produce temporary feature-branch implementation artifacts if useful, but those should not be treated as the final canonical accepted snapshot unless explicitly designated.

For Nutrition Serving Unit Logging Backend v1:

- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`

## Ownership policy

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

## Artifact policy

Feature snapshots:

- may exist as implementation artifacts;
- are optional unless requested;
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

## Serving-unit backend closeout state

Milestone:
Nutrition Serving Unit Logging Backend v1

Feature commit:
`8b285c6 Add nutrition serving unit logging backend`

Main merge commit:
`2279665 Merge nutrition serving unit logging backend v1`

QA result:
`NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`

Feature snapshot:
`fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`

Canonical accepted snapshot:
`fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`

Current source of truth:
`main` at `2279665`

## Accepted serving-unit backend behavior

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

QA PASS confirmed:

- valid serving-unit logging succeeds;
- wrong-food serving units reject safely;
- zero/negative quantity rejects safely;
- missing serving units reject safely;
- missing canonical foods reject safely;
- resolved grams persist to `food_entries`;
- provenance persists to `nutrition_serving_unit_log_metadata`;
- Target-vs-Actual sees serving-unit logs;
- raw/source `/nutrition/log` remains stable;
- canonical grams `/nutrition/{user_id}/log-canonical` remains stable;
- no raw source payloads exposed;
- no Streamlit behavior changed;
- no AI/provider behavior changed;
- missing nutrients remain missing/unknown, not zero.

## Next milestone routing

QA found one non-blocking product/API follow-up:

Serving-unit IDs are not currently discoverable through a public-safe API response.

Manual QA had to look up `serving_unit_id` directly in:

`canonical_food_serving_units`

This is acceptable for backend QA, but it blocks clean Streamlit serving-unit picker work.

Recommended next implementation milestone:

Canonical Serving Unit Discovery API v1

Expected owner:
Backend Development / Data Layer

Goal:
Expose active serving units for a canonical food through a public-safe endpoint.

Potential endpoint:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Expected response:

- `success`;
- `canonical_food_id`;
- `display_name`;
- `serving_units`:
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

This should precede:

Nutrition Serving Unit Logging Streamlit UI v1

## Scope

Allowed:

- project-memory updates;
- continuity/bootstrap updates;
- current handoff updates;
- milestone closeout doc;
- canonical main snapshot creation from `2279665`.

Not allowed:

- Python runtime code changes;
- API changes;
- schema changes;
- Streamlit changes;
- test changes unless project-memory tooling requires it;
- serving-unit discovery implementation;
- nutrition logging behavior changes;
- AI/provider changes;
- broad process rewrite;
- historical rewrite across every old milestone;
- repo-wide mutating formatter commands.

## Validation expectations

Recommended validation:

```powershell
git diff --check

python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief

pytest tests/test_project_memory_check.py -q

.\scripts\dev_commit_check.ps1 -Mode docs-only
```

Use docs-only commit-check mode if the tooling does not have a literal `docs` mode.

## Final status target

Expected final proposed status:

`SNAPSHOT_OWNERSHIP_MAIN_ACCEPTANCE_ARTIFACT_POLICY_V1_ACCEPTED`
