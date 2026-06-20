# Today UX Polish v1

Status: `TODAY_UX_POLISH_V1_IMPLEMENTED_PENDING_REVIEW`

Branch: `feature/today-ux-polish-v1`

## Purpose

Improve Today tab readability, hierarchy, and product feel after the deterministic Today Coach Note became available in normal UI.

This is a Streamlit UI polish milestone, not a provider or coaching-logic milestone.

## Implementation summary

Implemented a calmer Today presentation:

- Replaced the late garnet/gold Streamlit palette override with a neutral slate/teal product palette.
- Added semantic card classes for action and coach cards.
- Changed the Daily Next Action presentation from alert-style `st.info` / `st.warning` / `st.success` banners into a calmer product card labeled `Your next move`.
- Kept the deterministic Today Coach Note card near the Daily Next Action and retitled the visible card framing around `Today’s Focus`.
- Preserved Developer Mode diagnostics while keeping normal UI free of provider/model/debug labels.

Implemented a limited Workout substitution copy cleanup:

- Renamed the normal substitution area to `Need a swap?`.
- Made the selected replacement target explicit with `Replace: <exercise>` and `Original exercise` labels.
- Renamed quick actions from ambiguous usage to `Swap in`.
- Renamed full-list controls to `More swap options` and `Choose a replacement exercise`.
- Preserved the existing substitution API, backend behavior, and workout generation flow.

## Boundary

Preserved boundaries:

- no provider calls on normal Today load
- provider remains disabled by default
- no model is promoted
- no provider defaults are changed
- no raw/rejected provider output is displayed
- no narrative persistence is added
- no database schema changes are added
- no report persistence changes are added
- no Daily Next Action selection changes are made
- no nutrition calculation changes are made
- no workout generation changes are made
- no exercise substitution algorithm changes are made
- no catalog files are changed
- no Developer Mode functionality is removed

## Tests added

- `tests/test_today_ux_polish_v1.py`

The tests verify:

- the FSU-like garnet/gold palette identifiers are removed
- the Next Action panel uses a calm card instead of a heavy alert banner
- the Today Coach Note uses integrated focus-card copy
- substitution UI copy uses clearer swap/replacement language
- normal UI polish functions do not introduce provider/model/debug terms

## Non-goals

Not included:

- provider generation on normal Today load
- qwen3 promotion
- provider persistence
- narrative persistence
- async provider orchestration
- Daily Next Action logic changes
- workout generation algorithm changes
- exercise substitution algorithm changes
- workout exercise count changes
- full Workout tab redesign
- catalog changes

## Follow-up recommendation

If Workout still feels poor after this polish, split the next work into a focused `Workout Substitution UX v1` milestone rather than hiding a larger redesign in Today polish.
