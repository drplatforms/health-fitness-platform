# Daily Coach Narrative Limited Today UI Readiness v1

Status: `DAILY_COACH_NARRATIVE_LIMITED_TODAY_UI_READINESS_V1_IMPLEMENTED_PENDING_REVIEW`

Branch: `feature/daily-coach-narrative-limited-today-ui-readiness-v1`

## Purpose

Prepare the Today tab for a limited, safe, product-facing Daily Coach narrative card without promoting provider generation to normal users.

The product goal is for Today to feel more like a coach:

```text
Here is what matters today.
Here is why.
Here is the one thing to do next.
```

## Implementation summary

Implemented a deterministic Today Coach Note card powered by Daily Next Action.

New backend contract:

- `DailyCoachTodayCard` display model
- `services/daily_coach_today_card_service.py`
- `GET /daily-coach/{user_id}/today-card`

New Today UI behavior:

- Adds `Today’s Coach Note` immediately after the Daily Next Action panel.
- Displays short deterministic coach copy tied to the selected Daily Next Action.
- Uses a user-safe CTA label that mirrors the deterministic next action.
- Displays a single grounded supporting reason from existing deterministic action text.
- Degrades gracefully if the card cannot load.
- Keeps the existing developer preview panel separate.

## Boundary

This milestone is not provider promotion.

Preserved boundaries:

- normal Today UI does not call provider generation
- provider preview remains manual/developer-gated only
- provider remains disabled by default
- no model is promoted
- no provider defaults are changed
- no approved provider persistence is added
- no rejected provider output is displayed
- no raw provider output is displayed
- no prompt/model context is displayed in normal UI
- no report persistence is changed
- no database schema changes are added
- Daily Next Action selection logic is unchanged
- nutrition calculations are unchanged
- workout generation is unchanged
- catalog files are unchanged

## User-facing card contract

Normal UI may display:

- card title
- coach note
- next action title
- CTA label
- CTA target
- supporting reason

Normal UI must not display:

- provider name
- model name
- raw provider response
- rejected provider response
- prompt text
- parse/validation internals
- fallback reasons
- stack traces
- raw JSON

The normal route returns only the public card payload. Source/debug metadata remains service-side or Developer Mode only.

## Copy rules

The card copy is deterministic and action-specific.

It is intentionally:

- short
- practical
- linked to the Daily Next Action
- non-medical
- not guilt-based
- free of provider/debug terminology
- free of invented calorie/protein targets
- free of unsupported adherence/fatigue/progress claims

## Tests added

- `tests/test_daily_coach_today_card_service.py`
- `tests/test_daily_coach_today_card_route.py`
- `tests/test_streamlit_today_coach_card.py`

The tests prove:

- card builds for deterministic Daily Next Action input
- public card payload does not expose provider/model/debug terms
- rejected/raw provider-like nearby metadata is not included in the public card
- normal route returns public-safe fields only
- normal route does not call narrative preview/provider code
- Streamlit Today places the card after Daily Next Action and before the developer preview panel
- Today Coach Note UI calls the deterministic Today card route, not the narrative preview route

## Non-goals

Not included:

- provider generation on normal Today load
- qwen3 promotion
- qwen3:32b normal Today use
- background provider jobs
- user-facing provider persistence
- rejected/raw provider display
- prompt/context display in normal UI
- report persistence changes
- database schema changes
- provider default changes
- model routing changes
- Daily Next Action selection changes
- catalog changes
