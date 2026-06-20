# Daily Coach Narrative Limited Today UI Readiness v1 Review Notes

Status: `IMPLEMENTED / READY FOR ARCHITECTURE REVIEW`

Proposed final status: `DAILY_COACH_NARRATIVE_LIMITED_TODAY_UI_READINESS_V1_ACCEPTED`

## Summary

Implemented a limited deterministic Today Coach Note card in normal Today UI.

The card is downstream of deterministic Daily Next Action and gives the user a compact coach-like note tied to the next action. It is product-facing but does not use provider generation, provider persistence, model routing, or raw/rejected provider output.

## Files changed

- `models/daily_coach_narrative_models.py`
- `services/daily_coach_today_card_service.py`
- `api/routes/daily_coach.py`
- `ui/streamlit_app.py`
- `tests/test_daily_coach_today_card_service.py`
- `tests/test_daily_coach_today_card_route.py`
- `tests/test_streamlit_today_coach_card.py`
- `docs/project_memory/milestones/daily_coach_narrative_limited_today_ui_readiness_v1.md`
- `docs/project_memory/reviews/daily_coach_narrative_limited_today_ui_readiness_v1.md`
- `docs/project_memory/current_state.md`
- `docs/project_memory/open_questions.md`

## User-facing behavior

Normal Today UI now includes:

- Daily Next Action panel
- Today’s Coach Note card
- existing recovery/check-in, synthesis, grounded recommendation, nutrition, reflection, and workout sections
- existing Developer Mode narrative preview panel, still separate and manual

The new card appears immediately after Daily Next Action.

## Service/model behavior

`DailyCoachTodayCard` captures the safe display contract.

`build_daily_coach_today_card(...)`:

- receives or builds deterministic Daily Next Action
- creates action-specific deterministic coach copy
- returns a public-safe card object
- validates public display text
- never calls provider generation
- never reads provider output
- never persists narrative text
- never mutates reports or database state
- never changes Daily Next Action selection

## API behavior

`GET /daily-coach/{user_id}/today-card` returns:

- `success`
- `user_id`
- `today_card`

The `today_card` payload contains only public-safe display fields.

It does not return:

- display source
- developer metadata
- provider/model status
- parse status
- validation status
- fallback reason
- raw/rejected output
- prompt/context text

## Streamlit behavior

`render_daily_coach_today_card(user_id)` calls only:

```text
/daily-coach/{user_id}/today-card
```

It does not call the narrative preview debug route.

Failure behavior is safe:

```text
Today’s plan is still available. Start with the next action above.
```

Developer Mode may show the sanitized route response, but normal UI does not display provider/model/debug internals.

## Validation focus

The implementation adds explicit tests for:

- deterministic card creation
- all accepted Daily Next Action classes
- public no-leak boundaries
- no provider call boundary
- route public-safe payload
- route no-preview boundary
- UI placement and route boundary

## Boundary confirmation

Confirmed by implementation and tests:

- normal Today UI does not call provider
- provider remains disabled by default
- qwen3:8b not promoted
- qwen3:32b not promoted
- no model promoted
- no provider defaults changed
- no raw provider output displayed
- no rejected provider output displayed
- no prompt/model context displayed
- no user-facing persistence added
- no database schema changes
- no report persistence changes
- no Daily Next Action selection changes
- no nutrition calculation changes
- no workout generation changes
- no catalog changes
- no Streamlit debug leak in normal UI
- no unsafe FastAPI route exposure
- no paid tools required
- no Aider required
- no Codex required
- no Headroom reintroduced
- no Claude workflow
- no `CLAUDE.md`
- `qa_artifacts` not committed

## Recommended next step

Accept as:

```text
DAILY_COACH_NARRATIVE_LIMITED_TODAY_UI_READINESS_V1_ACCEPTED
```

Recommended next milestone after acceptance:

```text
Today UX Polish v1
```

Alternative next milestones:

- Daily Coach Narrative Same-Session Approved Preview Bridge v1
- Daily Coach Narrative Async Persistence Design v1
- Provider Narrative QA Matrix v2
