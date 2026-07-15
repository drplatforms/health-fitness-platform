# Premium Platform Blueprint

Last updated: 2026-07-15

## Purpose

This blueprint describes what the Health & Fitness Platform could become as a premium, paid-platform-quality product.

It is aspirational but disciplined. It connects product experience, backend architecture, optional provider/generative systems, data architecture, DevOps, frontend architecture, observability, testing, and agent workflows.

This document is aspirational. It does not authorize implementation of all features.

Every feature must still be implemented through scoped milestones, tests, validation, manual QA where appropriate, project-memory updates, and Architecture acceptance.

## 1. Platform vision

Health & Fitness Platform can become a local-first, data-grounded health and fitness platform with:

- deterministic backend truth
- practical nutrition, training, recovery, and progress workflows
- validated optional provider explanation
- long-term coach memory
- RAG-backed coaching knowledge
- vector search over user history and curated knowledge
- optional model routing
- optional async provider orchestration
- production-grade diagnostics
- a production-grade frontend
- strong data architecture
- traceable project memory
- agent-safe engineering workflows

The platform should feel informed, useful, context-aware, practical, and personal. Optional generative features must never substitute fluent language for grounded product truth.

## 2. Premium product principles

The premium version should follow these principles:

- useful before fancy
- truthful before persuasive
- deterministic before generative
- explainable before automated
- user control before hidden intelligence
- coach-like but bounded
- premium backend, not just premium UI
- every recommendation can explain why
- every provider-generated sentence has an approved evidence path
- every fallback is safe and understandable
- every user-facing claim has a confidence boundary
- every persistent memory item can be inspected and corrected

The product should never fake certainty to feel premium.

## 3. Today experience

A premium Today surface could become the user's command center.

Future Today capabilities:

- Daily Next Action
- Coach's Read for Today
- Today Coach Note
- Daily Grounded Recommendation
- workout status
- nutrition status
- recovery status
- data quality/confidence indicators
- explain-why controls
- action cards
- user feedback buttons
- quick logging
- context-aware nudges
- same-day plan adjustments
- clear distinction between deterministic product truth and optional approved provider copy

The Today screen should answer:

- What matters now?
- Why does it matter?
- What should I do next?
- What information is missing?
- What changed since yesterday?
- What can I ignore?

Normal Today load should remain fast and deterministic unless a later milestone explicitly approves async/precomputed provider display.

## 4. Workout platform

Future workout capabilities may include:

- workout plan generator
- exercise count preference
- exercise substitution engine
- exposure tracking
- progression engine
- deload engine
- readiness-aware adjustments
- equipment-aware programming
- workout session player
- rest timer
- warmup generation
- cooldown generation
- workout review
- performance evidence service
- training load model
- periodization layer
- movement-pattern balancing
- exercise variety controls
- exercise avoid/preference lists
- progression explanations
- coach feedback after sessions

Premium workout programming should not mean more random exercises. It should mean more appropriate, explainable, and adaptive programming.

## 5. Nutrition platform

Future nutrition capabilities may include:

- food logging
- canonical food catalog
- food search
- meal builder
- saved meals/templates
- macro gap engine
- snack suggestion engine
- meal suggestion engine
- preference-aware suggestions
- target confidence gates
- micronutrient awareness
- meal timing context
- barcode or label capture eventually
- recipe parser
- grocery list generator
- nutrition calibration
- trend-aware target review
- "close the gap" suggestions
- food swaps
- pantry-aware planning later

Nutrition should remain confidence-gated. The app should not fabricate targets, serving sizes, or health claims.

## 6. Recovery / readiness

Future recovery capabilities may include:

- daily recovery check-in
- readiness score
- fatigue trend tracking
- sleep trend support
- soreness map
- stress-aware coaching
- low-time mode
- low-energy mode
- injury/avoidance constraints
- recovery recommendation cards
- deload suggestions
- workout intensity adjustment
- rest-day coaching

Recovery should influence recommendations without pretending to diagnose medical conditions.

## 7. Reports / coaching intelligence

Future reporting capabilities may include:

- full daily report
- weekly review
- monthly review
- section registry
- report diffing
- claim ledger
- report audit trail
- user-facing evidence links
- narrative versioning
- coach insights queue
- recommendation outcome tracking
- provider-approved narrative sections
- fallback transparency
- training evidence summaries
- nutrition target-vs-actual summaries
- data quality summaries

Reports should become a trustworthy record of what happened, what changed, and what the coach recommends next.

## 8. Optional provider / generative capabilities

Future provider or generative capabilities may include:

- provider preview lanes
- approved provider narratives
- async coach narratives
- tone controls
- model capability registry
- provider QA matrix
- fallback renderer
- model routing
- coach memory integration
- narrative QA dashboards
- user feedback on coach tone
- "why did coach say this?" tracing

Strict boundary:

Provider output may explain or synthesize within backend-approved context. It is optional, non-authoritative, and subordinate to deterministic product behavior. It may not own truth, change decisions, persist memories, or override validators without explicit backend/user approval.

Provider-written daily coaching narrative is currently paused after failing human product-quality acceptance. No specific model is part of the public product identity or an active roadmap commitment.

## 9. RAG / knowledge experience

Future RAG-backed experience may include:

- curated health/training/nutrition knowledge base
- source-tagged retrieval
- user education mode
- explain-with-context controls
- retrieval evaluation
- local docs ingestion
- safe citation-aware coaching
- app help and onboarding assistant
- "teach me this" explanations
- technique and habit explanations

RAG only supports explanation. It does not decide, prescribe, or create truth.

## 10. Long-term memory experience

Future memory features may include:

- inspectable coach memory
- editable user facts
- editable preferences
- goals and constraints
- trend memory
- memory expiration
- coach observation ledger
- memory retrieval service
- user feedback incorporated into future coaching
- explicit distinction between facts, preferences, goals, constraints, observations, and model suggestions

No hidden model memory is acceptable. The user should be able to see what the system believes and correct it.

## 11. Backend premium systems

A premium backend may include:

- FastAPI
- Pydantic contracts
- service layer
- repository/data access layer
- domain models
- event log
- job system
- API versioning
- feature flags
- config system
- policy engine
- provider abstraction
- validation services
- audit trails
- structured errors
- stable route contracts
- traceable decision outputs

The backend is the product's trust layer.

## 12. Data / storage systems

Future storage systems may include:

- SQLite now
- PostgreSQL later
- Alembic migrations
- Redis
- canonical catalog tables
- staging tables
- job tables
- report tables
- memory ledger
- vector store
- embedding metadata
- backups
- export/import
- data quality checks
- retention policy

Data architecture should evolve deliberately. Schema changes require migration discipline and Architecture acceptance.

## 13. Orchestration systems

Future orchestration may include:

- Celery
- Redis
- Prefect
- APScheduler
- background jobs
- retries
- job dashboards
- ingestion pipelines
- provider job queue
- async reports
- scheduled reviews
- embedding jobs
- backup jobs

Async work should be observable and recoverable.

## 14. Frontend premium systems

Current frontend:

- Next.js
- React
- TypeScript
- Tailwind
- production runtime on project port `3100`
- Streamlit retained only for legacy/developer-only surfaces where still needed

Future frontend possibilities:

- design system
- theme system
- mobile-responsive UI
- PWA
- charts
- active workout UI
- API client generation
- Playwright E2E tests

The future frontend should preserve the product spine:

- Today
- Workout
- Nutrition
- Reports
- History
- Developer Mode
- traceable diagnostics

Replacement of the accepted Next.js frontend is not approved by this blueprint.

## 15. Observability / QA systems

A premium platform needs:

- OpenTelemetry
- Prometheus
- Grafana
- structured logs
- provider quality dashboard
- trace IDs
- fallback metrics
- parse-failure metrics
- validation-failure metrics
- health endpoints
- QA artifacts
- regression suite
- smoke tests
- docs tests
- CI/CD
- pre-commit
- coverage
- type checking
- manual QA scripts
- model comparison matrices

If the coach is going to feel intelligent, failures must be measurable.

## 16. Security / privacy / safety

Future security and safety systems may include:

- authentication
- roles
- Developer Mode lock
- health data controls
- user export/delete
- prompt injection defense
- tool permissions
- audit logs
- raw output quarantine
- medical safety boundaries
- nutrition safety boundaries
- exercise safety boundaries
- encryption later
- backups/restore
- dependency scanning
- secret scanning

The project handles sensitive health-adjacent data. Privacy and correction rights must be part of the architecture.

## 17. DevOps / deployment

Future deployment capabilities may include:

- Docker
- Docker Compose
- Apache reverse proxy candidate
- Nginx or Caddy alternatives
- systemd services
- TLS
- environment profiles
- secrets management
- release notes
- versioned snapshots
- backup automation
- restore drills
- infrastructure-as-code later
- Kubernetes much later if useful

Deployment should improve reliability without hiding failures.

## 18. Developer / learning platform

Health & Fitness Platform is also a serious learning vehicle.

Developer systems may include:

- Supercharger / dev assistant
- session briefs
- project memory checks
- stale-doc checks
- architecture decision records
- branch templates
- handoff templates
- QA checklist generation
- code map
- dependency map
- learning notes
- `AGENTS.md` rules
- agent continuity doctrine
- future scoped Codex workflows
- future MCP/tool workflows

The agent memory is the architecture continuity layer. The repo docs must keep future agents grounded.

## 19. Suggested long-term build order

A disciplined long-term sequence from the accepted `14b09db` baseline:

1. Public Project Rebrand and README Refresh v1
2. Continued refinement of the Next.js daily product loop
3. Saved meals, recipes, and other explicitly prioritized nutrition workflows
4. Richer progress, trend, and history experiences
5. Mobile, accessibility, privacy, export, and deployment hardening
6. Observability and operational reliability
7. Optional long-term memory or curated knowledge capabilities when a concrete product need is approved
8. Optional provider, retrieval, model-routing, or tool-interface experiments only after separate Architecture authorization and human acceptance

The order can change, but every step must remain scoped and accepted.

## 20. Explicit boundary statement

This document is aspirational.

It does not authorize implementation of all features.

It does not change current runtime behavior, provider behavior, persistence, schema, reports, workouts, nutrition, catalogs, model defaults, or UI behavior.

Every feature must still be implemented through scoped milestones, tests, validation, project-memory updates, and Architecture acceptance.

<!-- START ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->
## Historical Daily Coach Narrative Direction

Date: 2026-06-21

Earlier architecture explored async generation rather than page-load generation for provider-written coaching narrative. That history is retained as experimental context, not as an active roadmap commitment.

Provider-written daily coaching narrative is currently paused after failing human product-quality acceptance. No specific model is part of the public product identity or promised as a premium capability.

Historical research evaluated `qwen3:32b` and MoE/model-routing concepts. They remain deferred experimental references only, not product commitments or implementation authorization.

Any future provider-written narrative must remain optional and bounded by backend-approved truth, validation gates, context identity checks, deterministic fallback, and explicit human product-quality acceptance.
<!-- END ASYNC_DAILY_COACH_NARRATIVE_IMPLEMENTATION_PLAN_V1 -->
