# Nutrition Serving Unit Logging Streamlit UI v1

Status: implemented on feature branch / pending validation and Architecture review.

Owner: Streamlit UI.

Source baseline: `main` at `fd87538`.

Branch: `feature/nutrition-serving-unit-logging-streamlit-ui-v1`.

Commit-check mode: code.

## Purpose

Add the first Streamlit UI path for logging a canonical food by backend-approved serving unit.

The UI path is:

```text
canonical food search
-> select canonical food
-> load backend-approved serving units
-> select serving unit
-> enter quantity
-> POST /nutrition/{user_id}/log-serving
-> display backend-returned resolved grams and public-safe context
```

## Backend contract consumed

Canonical food search:

`GET /foods/canonical/search?q=<query>`

Serving-unit discovery:

`GET /foods/canonical/{canonical_food_id}/serving-units`

Serving-unit logging:

`POST /nutrition/{user_id}/log-serving`

## Implementation boundaries

Streamlit must not:

- query raw database tables;
- inspect `canonical_food_serving_units` directly;
- invent serving-unit mappings;
- infer `serving_unit_id`;
- convert serving units to grams;
- submit grams overrides to `/nutrition/{user_id}/log-serving`;
- calculate nutrients/macros/actuals;
- expose raw source payloads or SQL/debug internals in normal UI;
- involve AI/provider/Ollama/CrewAI logic;
- redesign Target-vs-Actual or DailyCoachSynthesis.

Backend remains responsible for canonical food validation, serving-unit validation, ownership checks, quantity validation, grams resolution, food entry writes, provenance persistence, and Target-vs-Actual compatibility.

## UI behavior added

- Reuses existing Nutrition page canonical food search.
- Shows `Log Food by Serving Unit` after canonical food selection.
- Calls the serving-unit discovery endpoint for the selected canonical food.
- Renders serving-unit labels from backend-returned `display_name` and `grams_default`.
- Submits only backend-approved identifiers plus user quantity/date.
- Displays backend-returned resolved grams, date, confidence, source, and grams range when returned.
- Preserves canonical grams logging as a fallback.
- Preserves raw/source food database logging as an advanced fallback.
- Keeps Developer Mode details behind the existing Developer Mode gate.

## Acceptance criteria

This milestone is acceptable when:

1. User can search canonical foods in Streamlit.
2. User can select a canonical food.
3. Streamlit calls the backend serving-unit discovery endpoint.
4. User can select a returned backend-approved serving unit.
5. User can enter positive quantity.
6. Streamlit submits `canonical_food_id + serving_unit_id + quantity` to log-serving.
7. Streamlit does not submit grams override.
8. Streamlit does not calculate grams.
9. Streamlit displays backend-returned resolved grams.
10. Successful serving-unit logs update existing nutrition actuals path.
11. Target-vs-Actual remains stable.
12. Existing nutrition logging paths remain stable.
13. No raw DB/source/debug internals appear in normal UI.
14. No AI/provider behavior changes.
15. Streamlit compiles.
16. Focused tests pass.
17. Manual UI smoke passes.
18. Project memory is updated.
19. No snapshots are committed.
20. Feature branch is pushed.

## Expected final status

`NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED`
