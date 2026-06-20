# Today UX Polish v1 Review

Status: `TODAY_UX_POLISH_V1_IMPLEMENTED_PENDING_REVIEW`

## Summary

Today UX Polish v1 improves readability and product feel in the normal Streamlit UI while preserving accepted backend/provider boundaries.

The prior late-stage garnet/gold palette override was replaced with a calmer slate/teal palette. The Daily Next Action now renders as a softer card instead of a large alert-style banner. The Today Coach Note remains deterministic and visible near the Next Action, with clearer `Today’s Focus` framing.

Workout substitution changes are intentionally modest: only copy, labels, and user-facing structure were clarified. The substitution backend, APIs, and workout generation behavior were not changed.

## Files changed

- `ui/streamlit_app.py`
- `tests/test_today_ux_polish_v1.py`
- `docs/project_memory/milestones/today_ux_polish_v1.md`
- `docs/project_memory/reviews/today_ux_polish_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## Today UI changes

- Added calm neutral/teal semantic styling.
- Reduced the prior FSU-like palette dominance.
- Replaced heavy Next Action alert rendering with `portfolio-card-action`.
- Kept Today Coach Note deterministic and displayed as `portfolio-card-coach`.
- Replaced implementation-flavored framing with product-oriented labels:
  - `Your next move`
  - `Start here`
  - `Today’s Focus`
  - `Why this matters`

## Workout substitution cleanup

- Normal substitution section now uses `Need a swap?`.
- Each replacement target is labeled `Replace: <exercise>`.
- Candidate actions use `Swap in`.
- Full candidate list uses `More swap options` and `Choose a replacement exercise`.
- Developer Mode still exposes raw candidate details only behind developer expanders.

## Boundary confirmation

Confirmed by implementation scope:

- no provider calls added
- provider remains disabled by default
- no model promoted
- no provider defaults changed
- no raw/rejected provider output displayed
- no persistence/schema/report changes
- no Daily Next Action selection changes
- no nutrition calculation changes
- no workout generation changes
- no substitution backend behavior changes
- no catalog changes
- no paid tools/external agents required
- no Claude workflow
- no `CLAUDE.md`

## Validation

Expected validation:

- `git diff --check`
- `scripts/dev_commit_check.ps1 -Mode code`
- `python -m py_compile ui/streamlit_app.py`
- `python -m py_compile services/daily_coach_today_card_service.py`
- `pytest tests/test_today_ux_polish_v1.py -q`
- `pytest tests/test_streamlit_today_coach_card.py -q`
- `pytest tests/test_daily_coach_today_card_service.py -q`
- `pytest tests/test_daily_coach_today_card_route.py -q`
- existing Daily Coach safety tests
- report persistence tests
- project memory tests
- catalog regression tests
- memory-check
- stale-doc-check

## Manual QA recommendation

Manual QA should verify:

- Today tab is more readable.
- The heavy blue / FSU-like feel is removed or substantially toned down.
- Daily Next Action remains obvious.
- Today Coach Note remains visible and readable.
- Normal UI does not show provider/model/debug/internal labels.
- Developer Mode remains available.
- Workout substitution flow is easier to understand.
- Workout generation and logging behavior are unchanged.
