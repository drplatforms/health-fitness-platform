Daily Driver Core Contract v0

Status:
DAILY_DRIVER_CORE_CONTRACT_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW

Purpose:
Create the first backend-owned Today contract for the daily-driver product loop.

Implemented scope:
- Added typed Today contract models for readiness, workout, nutrition, next action, and coach note.
- Added deterministic service assembly for `build_daily_driver_today_response(user_id, target_date)`.
- Added a minimal `GET /api/today` route.
- Added focused model, service, and route tests.

Boundaries preserved:
- No PostgreSQL.
- No auth.
- No hosting.
- No sync.
- No Next.js.
- No Streamlit redesign.
- No provider expansion.
- No OpenAI/Ollama/CrewAI call required.
- No raw provider internals exposed.
- No Markdown in product-facing coach note text.
- No schema migration.

Contract goals:
- backend owns readiness truth
- backend owns workout truth
- backend owns nutrition truth
- backend owns next action truth
- coach_note remains optional only
- missing data degrades through `data_gaps` and `limitations`

Next recommended milestone:
Streamlit on Daily Contract v0
