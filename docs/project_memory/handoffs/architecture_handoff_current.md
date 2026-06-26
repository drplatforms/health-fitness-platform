# Architecture Handoff Current

Milestone: Nutrition Catalog + Serving Foundation Planning v1

Status: authorized / planning request.

Source baseline: `main` at `f469c89`.

Branch: `feature/nutrition-catalog-serving-foundation-planning-v1`.

Milestone type: planning / architecture / project memory only.

## Review focus

Architecture should make and document the nutrition foundation decisions before backend implementation begins.

Primary decisions:

- confirm Nutrition Catalog Diagnostic v1 as the next implementation milestone;
- confirm two-layer raw/source plus canonical app food catalog strategy;
- confirm serving-unit / household-measure model direction;
- confirm default grams + min/max range + confidence strategy;
- confirm backend ownership of conversions and nutrition truth;
- confirm deterministic suggestions before AI meal/snack generation;
- confirm provider can only assemble/explain backend-approved foods, servings, actuals, targets, and gaps;
- confirm workouts are good enough for now and recovery remains deferred behind nutrition foundation.

## Planning recommendation

Recommended sequence:

1. Nutrition Catalog Diagnostic v1.
2. Nutrition Canonical Food Model Review v1.
3. Curated Food Catalog Expansion v1.
4. Serving Unit Normalization / Household Measure Conversion v1.
5. Nutrition Logging Backend Contract v1.
6. Nutrition Actuals Confidence v1.
7. Nutrition Deterministic Food Suggestions v1.
8. Nutrition AI Meal/Snack Candidate Contract v1.

## Non-goals

No catalog expansion, serving unit implementation, USDA/source import, food logging changes, nutrition calculation changes, provider/Ollama behavior, AI meal generation, Streamlit UI, workout generation, recovery engine, migrations, or dependencies are authorized by this planning milestone.

## Acceptance intent

Accept this milestone if the nutrition sequence, two-layer catalog doctrine, serving unit strategy, confidence model, provider boundary, and next implementation milestone are documented and docs validation is green.

Proposed final status after successful closeout: `NUTRITION_CATALOG_SERVING_FOUNDATION_PLANNING_V1_ACCEPTED`.
