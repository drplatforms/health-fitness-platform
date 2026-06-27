# Backend Handoff Current

Milestone: Nutrition Serving Unit Logging Streamlit UI v1

Backend status: CC / support only.

Source baseline: `main` at `fd87538`.

Branch: `feature/nutrition-serving-unit-logging-streamlit-ui-v1`.

## Backend role

Backend should not receive this as an implementation milestone unless Streamlit finds a true backend contract defect.

Escalate to Backend only if:

- `GET /foods/canonical/{canonical_food_id}/serving-units` is missing at runtime;
- response shape lacks usable `serving_unit_id`;
- returned `serving_unit_id` fails with `POST /nutrition/{user_id}/log-serving`;
- endpoint exposes unsafe fields;
- endpoint cannot support the accepted UI flow.

Do not escalate to Backend for UI placement, copy, Streamlit state, or normal user messaging.

## Backend boundaries preserved

This Streamlit milestone must not change backend behavior, provider behavior, API response shape, persistence, nutrition formulas, workout generation, validators, or Target-vs-Actual semantics.
