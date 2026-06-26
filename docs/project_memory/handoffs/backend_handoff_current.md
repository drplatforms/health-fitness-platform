# Backend Handoff Current

Milestone: Nutrition Catalog + Serving Foundation Planning v1

Status: planning request / no runtime implementation.

Source baseline: `main` at `f469c89`.

Branch: `feature/nutrition-catalog-serving-foundation-planning-v1`.

## Backend planning direction

Backend should prepare for nutrition work in this order:

1. Diagnose the current nutrition catalog state.
2. Review whether current models can support canonical foods, aliases, per-100g nutrients, source/confidence metadata, and active flags.
3. Curate 150-300 high-value app-facing foods.
4. Add serving units for 50-100 high-value foods.
5. Support food logs by grams or approved serving unit.
6. Track actuals confidence.
7. Build deterministic food suggestions from macro gaps.
8. Only then allow provider meal/snack candidates using backend-approved facts.

## Backend ownership

Backend owns food truth, canonical foods, nutrients, serving conversions, grams, confidence, logged actuals, targets, gaps, validation, and fallback.

Provider/AI must not invent foods, serving units, grams, macros, targets, actuals, or unsupported claims.

## Two-layer catalog doctrine

Use raw/source data as staging/enrichment. Use canonical app foods for normal logging, suggestions, and provider contracts.

Do not expose a huge raw import directly to user-facing food logging, deterministic suggestions, or provider contracts.

## Current non-goals

Do not implement nutrition code in this planning milestone.

Do not modify food logging, nutrition calculations, provider/Ollama behavior, Streamlit UI, workouts, recovery, migrations, dependencies, snapshots, qa_artifacts, or local patch scripts.

Do not use `git add .`.

## Expected next backend milestone

Nutrition Catalog Diagnostic v1.

Expected diagnostic output:

- canonical food counts;
- active food counts;
- nutrient completeness;
- alias coverage;
- serving-unit coverage;
- foods with no serving units;
- foods with incomplete nutrient data;
- duplicate/near-duplicate foods;
- high-value staples missing;
- current logging assumptions;
- target/actuals calculation dependencies;
- whether deterministic suggestions can safely use current data.
