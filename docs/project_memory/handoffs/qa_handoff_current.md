# QA Handoff Current

Milestone: Nutrition Serving Unit Logging Streamlit UI v1

QA class: CLASS 4 — STREAMLIT / USER-FACING WORKFLOW.

Branch: `feature/nutrition-serving-unit-logging-streamlit-ui-v1`.

Source baseline: `main` at `fd87538`.

Commit-check mode: code.

## QA focus

Validate the actual Streamlit serving-unit logging path, not just backend API contracts.

Expected UI path:

```text
Nutrition page
-> search canonical food
-> select canonical food
-> serving units load from backend
-> select serving unit
-> enter positive quantity
-> log serving
-> success shows backend-returned resolved grams
```

## Manual Streamlit smoke

Confirm:

1. Streamlit starts.
2. Nutrition page loads.
3. Existing nutrition UI still appears.
4. Serving-unit logging section appears.
5. User can search canonical foods.
6. User can select canonical food.
7. Serving units load from backend.
8. Serving-unit selector shows backend-approved options.
9. `serving_unit_id` is not manually typed by user.
10. Quantity input accepts positive values.
11. Submit logs serving successfully.
12. Success message displays backend-returned resolved grams.
13. UI does not calculate grams.
14. Existing canonical grams fallback still works.
15. Existing raw/source fallback still works.
16. Target-vs-Actual updates according to existing UI pattern.
17. No traceback appears.
18. No AI/provider path is involved.
19. No raw DB/source/debug internals appear in normal UI.
20. Changing selected canonical food does not submit a stale `serving_unit_id`.

## Focused validation

```powershell
git diff --check
ruff check ui/streamlit_app.py
black --check ui/streamlit_app.py
python -m py_compile ui/streamlit_app.py
pytest tests/test_canonical_serving_unit_discovery_api.py -q
pytest tests/test_nutrition_serving_unit_logging_api.py -q
pytest tests/test_canonical_food_logging_api.py -q
pytest tests/test_food_canonical_search_api.py -q
pytest tests/test_nutrition_target_vs_actual_service.py -q
pytest tests/test_api_smoke.py -q
python tools/project_memory_check.py
```

Expected QA decision options:

- `PASS_STREAMLIT_SERVING_UNIT_LOGGING_READY_FOR_ARCHITECTURE`
- `PASS_WITH_MINOR_UI_NOTES`
- `FAIL_UI_LEAKAGE_OR_SCOPE_DRIFT`
