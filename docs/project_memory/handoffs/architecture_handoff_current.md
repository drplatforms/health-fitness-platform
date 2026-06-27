# Architecture Handoff Current

Milestone: Nutrition Serving Unit Logging Streamlit UI v1

Status: implementation branch prepared for Streamlit UI validation and Architecture review.

Source baseline: `main` at `fd87538`.

Branch: `feature/nutrition-serving-unit-logging-streamlit-ui-v1`.

Milestone type: Streamlit UI / user-facing nutrition logging workflow / project memory.

Commit-check mode: code.

## Review focus

Architecture should verify that Streamlit adds only the approved serving-unit logging UI path and preserves backend-owned truth.

Primary review decisions:

1. Confirm Streamlit reuses canonical food search.
2. Confirm Streamlit calls `GET /foods/canonical/{canonical_food_id}/serving-units` for serving-unit options.
3. Confirm submitted `serving_unit_id` comes from that backend discovery response.
4. Confirm Streamlit submits `canonical_food_id + serving_unit_id + quantity` to `POST /nutrition/{user_id}/log-serving`.
5. Confirm Streamlit does not submit grams overrides for serving-unit logging.
6. Confirm Streamlit does not calculate grams or nutrient values.
7. Confirm no raw DB table access was added.
8. Confirm normal UI exposes no raw DB/source/debug/provider internals.
9. Confirm existing canonical grams logging remains available as fallback.
10. Confirm existing raw/source fallback remains available.
11. Confirm Target-vs-Actual remains stable.
12. Confirm no backend/API/provider/persistence behavior changed.

## Accepted backend baseline

Canonical Serving Unit Discovery API v1 is accepted at main commit `fd87538` with QA result `CANONICAL_SERVING_UNIT_DISCOVERY_API_QA_V1_PASS`.

The accepted backend chain is:

```text
GET /foods/canonical/search
-> returns canonical_food_id
GET /foods/canonical/{canonical_food_id}/serving-units
-> returns backend-approved serving_unit_id values
POST /nutrition/{user_id}/log-serving
-> backend validates food/unit/ownership/quantity
-> backend resolves grams
-> backend writes food_entries and serving-unit provenance metadata
```

## Recommended final Architecture decision after review

Accept Nutrition Serving Unit Logging Streamlit UI v1 if validation and manual smoke pass.

Recommended final status:

`NUTRITION_SERVING_UNIT_LOGGING_STREAMLIT_UI_V1_ACCEPTED`
