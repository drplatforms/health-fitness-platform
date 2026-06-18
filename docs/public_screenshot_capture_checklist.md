# Public Screenshot Capture Checklist

Status: UI_POLISH_READY_FOR_SCREENSHOT_CAPTURE candidate

Branch: chore/public-ui-polish

Primary demo user: QA 102 — Well-recovered baseline
Secondary demo user: QA 105 — Messy/incomplete logging

## Validation before screenshots

- `ruff check . --fix`
- `black .`
- `python -m py_compile ui/streamlit_app.py`
- `pytest tests/test_full_report_section_registry.py -q`
- `pytest tests/test_report_persistence_boundary.py -q`
- If anything beyond Streamlit/docs changed: `scripts/dev_commit_check.ps1 -Mode code`

## Mandatory screenshot set

1. User 102 Today / Daily Coach Overview
2. User 102 Nutrition Target Transparency
3. User 102 Canonical Food Search / Logging
4. User 102 Workout Plan Preview
5. User 102 Nutrition Report Section or Training Report Section
6. Terminal test suite passing or sanitized Developer Debug Metadata

## Optional screenshots

7. User 105 limited-confidence / safety-boundary nutrition view
8. User 105 sanitized Developer Debug Metadata view
9. User 101 recovery-limited coaching boundary view

## Capture rules

- Use seeded data.
- Keep Developer Mode off unless intentionally capturing engineering evidence.
- Do not capture raw provider output, prompt text, schema text, exception internals, or tracebacks.
- Normal UI screenshots should show user value first.
- Engineering screenshots should show sanitized metadata only.
- Avoid local paths unless capturing terminal validation.
- Avoid huge raw tables and unexpanded debug JSON.
- Keep direct_ollama described as opt-in/experimental where visible; do not present it as default.
- Do not show qwen3 as approved.

## Recommended capture order

1. Today tab, QA 102, Daily Grounded Recommendation expanded.
2. Nutrition tab, QA 102, target-vs-actual plus Formula-Derived Targets.
3. Nutrition tab, QA 102, canonical food search results for `chicken breast`, `rice`, or `egg`.
4. Workout tab, QA 102, Plan step with Workout Plan Preview.
5. Reports tab, QA 102, latest sectionized Nutrition or Training report section.
6. Terminal validation screenshot after checks pass.

## Final acceptance label

UI_POLISH_READY_FOR_SCREENSHOT_CAPTURE
