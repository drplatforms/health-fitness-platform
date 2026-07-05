Next.js Mobile Today Shell v0

Status:
NEXTJS_MOBILE_TODAY_SHELL_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW

Purpose:
Create the first mobile-first Next.js frontend shell that renders the backend-owned Daily Driver Today contract.

Implemented scope:
- Added a new Next.js App Router app under `frontend/`.
- Added TypeScript Daily Driver contract types that match `GET /api/today`.
- Added a server-side Today fetch helper with local env configuration.
- Added a mobile-first Today page with readiness, workout, nutrition, next action, optional coach note, and quiet data-quality sections.
- Added loading, error, and empty states.
- Added `frontend/.env.local.example`.

Boundaries preserved:
- No auth.
- No hosting.
- No PostgreSQL.
- No workout logging.
- No nutrition logging.
- No provider calls.
- No raw JSON main UI.
- No Markdown renderer.
- No Streamlit redesign.
- No backend contract change.

Frontend goals:
- new frontend is under `frontend/`
- uses Next.js App Router
- uses TypeScript
- uses Tailwind
- renders `GET /api/today`
- keeps backend as the owner of readiness/workout/nutrition/next_action truth

Next recommended milestone:
Architecture Review for Next.js Mobile Today Shell v0
