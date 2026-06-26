# Next Milestone

Current milestone in progress: Nutrition Catalog + Serving Foundation Planning v1.

Recommended branch: `feature/nutrition-catalog-serving-foundation-planning-v1`.

Source branch: `main`.

Required source main commit: `f469c89`.

Milestone type: planning / architecture / project memory only.

## Planning objective

Define the nutrition backend foundation sequence before implementation begins.

The planning milestone should document:

- the preferred nutrition foundation roadmap;
- two-layer food catalog strategy;
- serving-unit / household-measure strategy;
- confidence/range model for estimated servings;
- nutrition actuals confidence strategy;
- deterministic food suggestion future contract;
- AI meal/snack candidate future contract;
- strict backend/provider boundary;
- the next implementation milestone.

No app/runtime behavior should change.

## Recommended planning decisions

### 1. Next implementation milestone

Recommended next implementation milestone: Nutrition Catalog Diagnostic v1.

Purpose: measure and report the current nutrition catalog state before expansion.

Diagnostic should answer:

- how many canonical foods exist;
- how many active foods exist;
- nutrient completeness;
- alias coverage;
- serving-unit coverage;
- foods with no serving units;
- foods with incomplete nutrient data;
- duplicate or near-duplicate foods;
- high-value staples missing;
- current logging assumptions;
- current target/actuals calculation dependencies;
- whether food suggestions can safely use current data.

Expected output: diagnostic tool/report and project memory update. No large catalog expansion yet.

### 2. Two-layer food catalog

Preferred model:

Layer 1: raw / source food data.

- large imported food datasets;
- USDA or other source records;
- not directly user-facing;
- useful for search, enrichment, mapping, future expansion.

Layer 2: canonical app food catalog.

- curated food names;
- aliases;
- nutrients per 100g;
- approved serving units;
- confidence/source metadata;
- safe for logging;
- safe for deterministic suggestions;
- safe for provider contracts.

Do not expose a huge raw import directly to normal logging, suggestions, or AI/provider contracts.

### 3. Serving unit model

The backend should eventually support weighed grams and practical serving units.

Possible model:

CanonicalFood:

- food_id
- canonical_name
- aliases
- nutrients_per_100g
- source
- confidence
- active

ServingUnit:

- serving_unit_id
- food_id
- unit_name
- unit_quantity
- grams_default
- grams_min
- grams_max
- confidence
- source
- source_note
- user_override_allowed
- active

### 4. Confidence/range rule

Use default grams, ranges, and confidence.

Do not present household measures as exact.

Example:

`1/2 cup cooked white rice`

- grams_default: 90g
- grams_min: 80g
- grams_max: 100g
- confidence: medium

### 5. Nutrition actuals confidence

Potential confidence sources:

- weighed_grams
- package_label
- serving_unit_estimate
- user_saved_serving
- copied_previous_meal
- AI_candidate_user_confirmed
- unknown_or_low_confidence

This should allow coaching copy like “This is an estimate,” “Weighed grams would be more precise,” or “Good enough for today.”

### 6. Deterministic food suggestions

Future deterministic suggestions should use backend-approved actuals, targets, gaps, canonical foods, serving units, and confidence.

Backend creates approved candidates. AI may later explain or assemble only those approved candidates.

### 7. AI/provider boundary

Provider input must include only approved facts:

- canonical foods;
- approved serving units;
- approved actuals;
- approved targets;
- approved gaps;
- confidence notes;
- user constraints/preferences;
- forbidden claims.

Backend validation must reject invented food, serving unit, grams, macros, targets, unsupported claims, missing required fields, non-schema output, and unsafe recommendations.

## Recommended full nutrition foundation roadmap

1. Nutrition Catalog Diagnostic v1.
2. Nutrition Canonical Food Model Review v1.
3. Curated Food Catalog Expansion v1.
4. Serving Unit Normalization / Household Measure Conversion v1.
5. Nutrition Logging Backend Contract v1.
6. Nutrition Actuals Confidence v1.
7. Nutrition Deterministic Food Suggestions v1.
8. Nutrition AI Meal/Snack Candidate Contract v1.

## Strict non-goals for the current planning milestone

Do not implement catalog expansion.

Do not implement serving units.

Do not import USDA/source data.

Do not modify food logging.

Do not modify nutrition calculations.

Do not modify provider/Ollama behavior.

Do not add AI meal generation.

Do not modify Streamlit UI.

Do not modify workout generation.

Do not modify recovery engine.

Do not add migrations.

Do not add dependencies.

Do not commit snapshots, qa_artifacts, patch scripts, or local artifacts.

Do not use `git add .`.

## Required validation for this docs-only milestone

```powershell
git diff --check
python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q
scripts/dev_commit_check.ps1 -Mode docs-only
```

No browser smoke required.

No Linux runtime smoke required unless project policy chooses to pull docs milestones on Linux.

## Historical project-memory requirements still present

Some older project-memory tooling still checks for retained phrases related to prior Daily Coach async work:

- Daily Coach Async Provider Runtime Design v1
- DAILY_COACH_ASYNC_PROVIDER_RUNTIME_DESIGN_V1_ACCEPTED
- Project Continuity System v2
- Daily Coach Async Persistence Design v1
- DAILY_COACH_ASYNC_PERSISTENCE_DESIGN_V1_ACCEPTED
- Daily Coach Async Persistence Contracts + Schema v1
- feature/daily-coach-async-persistence-contracts-schema-v1
- schema/contracts
- NOT_AUTHORIZED_YET

These are historical continuity markers only. They do not authorize old async/provider implementation work.
