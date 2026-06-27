# QA Handoff Current

Milestone: Snapshot Ownership / Main Acceptance Artifact Policy v1

QA status: docs/process closeout validation required.

Branch: `feature/snapshot-ownership-main-acceptance-policy-v1`.

Source baseline: `main` at `2279665`.

Commit-check mode: docs.

## QA focus

Validate that project memory closes Nutrition Serving Unit Logging Backend v1 with the accepted main commit and canonical accepted snapshot.

This milestone has no runtime behavior changes.

## Expected current accepted state

Nutrition Serving Unit Logging Backend v1:

- Feature commit: `8b285c6 Add nutrition serving unit logging backend`
- Main merge commit: `2279665 Merge nutrition serving unit logging backend v1`
- Feature snapshot: `fitness_ai_snapshot_2026-06-26_8b285c6_nutrition-serving-unit-logging-backend-v1.zip`
- Canonical accepted snapshot: `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip`
- QA result: `NUTRITION_SERVING_UNIT_LOGGING_QA_V1_PASS`

## Snapshot policy to verify

Project memory should now say:

- feature snapshots may exist as temporary implementation artifacts;
- feature snapshots are not final accepted continuity snapshots unless explicitly designated;
- canonical accepted snapshots should be created from `main` after Architecture acceptance / merge;
- canonical accepted snapshot filenames should use the accepted main commit hash;
- snapshots should not be committed to the repo;
- future handoffs must distinguish feature commit, main merge commit, feature snapshot, and canonical accepted snapshot.

## Serving-unit backend behavior already accepted

The accepted backend flow is:

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

QA PASS already confirmed:

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

## Non-goals to verify

No changes should appear in:

- Python runtime code;
- API routes;
- database/schema code;
- Streamlit UI;
- tests unless project-memory tooling requires it;
- AI/provider/Ollama/CrewAI paths;
- nutrition actuals behavior;
- Target-vs-Actual behavior;
- food suggestions;
- meal planning;
- workout/recovery/report behavior.

## Suggested docs validation

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

Do not run repo-wide mutating formatter commands for this milestone.

## Next QA routing

After Architecture accepts this docs/process closeout, the next implementation milestone should be:

Canonical Serving Unit Discovery API v1.

QA should later verify that active serving units are discoverable through a public-safe backend endpoint before Streamlit serving-unit picker work begins.

## Runtime command continuity anchor

Local Command Menu App Runtime Correction v1 remains in effect.

`app` means Linux canonical app runtime.

`wapp` remains Windows-local only.

`fports` remains available for local port inspection.
