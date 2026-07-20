# Platform North Star + Future Stack

**Status:** Strategic architecture compass / non-authorizing future-stack reference
**Baseline:** `14b09db Close personal custom foods UI v1`
**Baseline snapshot:** `fitness_ai_snapshot_2026-07-15_14b09db_main_personal-custom-foods-ui-closed.zip`
**Milestone:** Platform North Star + Future Stack Canonicalization v1
**Accepted in:** `187e433 main_merge-platform-north-star-future-stack-canonicalization-v1`

This file is the durable strategic north star for the Health & Fitness Platform. It preserves the long-term platform vision while keeping implementation sequencing disciplined.

This file records direction. It does not authorize implementation by itself.

## One-Sentence North Star

Health & Fitness Platform is a local-first, data-grounded product for managing nutrition, training, recovery, and progress through trustworthy data, deterministic services, practical workflows, and optional non-authoritative generative capabilities.

## What This Platform Is Not

Health & Fitness Platform is not:

- just a workout tracker
- just a macro tracker
- just a chatbot
- just a report generator
- a prompt demo
- a provider-wrapper
- an agent demo

The goal is a serious health and fitness platform where structured facts, deterministic intelligence, and useful product workflows stand on their own. Optional provider synthesis may enhance those workflows only inside backend-approved boundaries.

## Architecture Doctrine

- Backend owns truth.
- Deterministic logic comes first.
- AI/provider output is optional, gated, audited, and never truth.
- Retrieved/RAG content is context, not truth.
- Agents may assist later, but cannot own authority.
- Docs/project memory are part of Definition of Done.
- Cost, safety, provenance, confidence, and rollback paths are architecture concerns.
- Provider-written language is an optional product capability, not the product's identity or source of authority.

## Sequencing Doctrine

Huge dream. Strong sequencing. No random feature explosion.

Build and validate the core product first. Consider advanced retrieval, provider, or orchestration systems only when a scoped product need justifies them.

Do not use RAG, vector search, agents, frontier-model workflows, or fancy orchestration to compensate for weak backend intelligence.

Every future platform move still needs:

- Architecture-scoped milestone
- team handoff
- explicit non-goals
- tests
- validation
- project-memory update
- QA classification
- Architecture acceptance
- merge, push, and snapshot when authorized

## Backend Intelligence Foundation

Backend Intelligence Foundation is the prerequisite for advanced AI.

Core layers:

- Recovery Intelligence
- Workout Set Intelligence
- Cross-Domain Trend Engine
- Six-Month Seed Data
- Food Knowledge Expansion
- Unified Daily Coach Intelligence Snapshot
- user profile / preferences / constraints
- provenance and confidence models
- data-quality indicators
- scenario QA framework
- deterministic recommendation engine
- rules / policy layer

These layers must provide stable, inspectable source-data contracts before advanced retrieval, orchestration, or multi-model systems become useful.

Current accepted state at this baseline:

- Next.js, React, and TypeScript provide the active product frontend; it runs on the project-standard production port `3100`.
- FastAPI, SQLite, and deterministic backend services remain the product truth layer.
- Canonical food search and logging are implemented.
- Formula-derived nutrition targets and Target-vs-Actual are implemented.
- Personal Custom Foods contract, persistence, logging, and UI milestones are accepted, merged, and closed.
- Recovery workflows are implemented.
- Deterministic workout planning, execution, substitution, history, and progression context are implemented.
- Provider-written daily coaching narrative is paused after failing human product-quality acceptance. Provider infrastructure remains optional experimental capability outside the core product identity.
- The immediate next milestone is Public Project Rebrand and README Refresh v1.

## Product Intelligence Vision

Future product capabilities may include:

- Daily Command Center
- adaptive training
- progression forecasting
- recovery-aware training adjustment
- nutrition adherence trends
- macro target adaptation
- meal planning / meal prep
- grocery list generation
- What-If simulator
- weekly/monthly coach review
- coach memory
- preference learning
- schedule-aware recommendations
- friction/adherence modeling
- confidence/provenance everywhere

These are product architecture goals, not automatic implementation approval.

## Core App / Backend Stack

Candidate technologies:

- Python
- FastAPI
- Pydantic
- SQLAlchemy / SQLModel
- Alembic
- PostgreSQL
- SQLite for local/dev
- Pytest
- Ruff
- Black
- Mypy or Pyright
- Pre-commit
- GitHub Actions
- Docker
- Docker Compose

## Data / Analytics Stack

Candidate technologies:

- PostgreSQL
- pgvector
- Redis
- DuckDB
- Parquet
- Polars
- Pandas
- dbt later if analytics grows
- Great Expectations or Pandera for data validation
- S3-compatible object storage / MinIO
- structured event/audit tables

## Retrieval / RAG / Knowledge Systems

Candidate future technologies and patterns:

- embeddings
- hybrid retrieval: keyword + vector
- BM25 / full-text search
- pgvector for integrated Postgres retrieval
- Qdrant if a dedicated vector DB becomes justified
- rerankers
- RAG over exercise knowledge
- RAG over food knowledge
- RAG over user history
- RAG over project docs
- RAG over coaching rules
- RAG over wearable explanations
- RAG over product education content

Boundary:

```text
RAG does not decide.
Retrieved content is context, not truth.
Backend facts and deterministic policy remain authoritative.
```

## Optional Provider / Generative Stack

Candidate future technologies and practices:

- OpenAI provider adapter
- Anthropic provider adapter
- Gemini provider adapter
- local Ollama provider adapter
- vLLM or llama.cpp later for local serving
- LiteLLM-style model routing
- Prompt Lab
- model capability registry
- cost-aware model routing
- structured output validation
- provider fallback rules
- token/cost telemetry
- model comparison harness
- golden-output evals
- coach voice evals

## Agent / Orchestration Stack

Candidate future technologies and practices:

- LangGraph
- state-machine orchestration
- LlamaIndex workflows
- CrewAI as experimental/limited-use reference only
- custom job table first
- background job scheduler
- human-in-the-loop review
- agent audit logs
- agent trace artifacts
- tool permission boundaries
- policy-gated tool execution

Boundary:

```text
Multi-agent coaching waits until backend intelligence and service contracts are stable enough to give agents real evidence.
```

## Frontend / UX Stack

Current technologies and direction:

- React
- Next.js
- TypeScript
- Tailwind
- production frontend on project port `3100`
- Streamlit retained only for legacy/developer-only surfaces where still needed

Candidate future technologies and direction:

- shadcn/ui
- TanStack Query
- Recharts / ECharts / Plotly
- PWA
- React Native / Expo later
- mobile-first Daily Command Center
- offline-friendly logging
- push notifications
- voice input later
- photo capture flows
- barcode scanning UX

## Multimodal Input

Future possibilities:

- barcode scanning
- nutrition label OCR
- photo-assisted food logging
- restaurant/menu parsing
- receipt/grocery import
- voice check-ins
- workout form video review eventually
- document parsing for plans/reports

## Wearables / Integrations

Future possibilities:

- Apple HealthKit
- Google Health Connect
- Fitbit
- Garmin
- Oura
- Whoop
- Strava
- smart scales
- calendar integration
- notification integrations
- grocery/recipe APIs later
- USDA FoodData Central
- Open Food Facts

## Observability / Operations

Candidate technologies:

- OpenTelemetry
- Prometheus
- Grafana
- Loki
- Sentry
- structured logs
- trace IDs
- provider telemetry
- token/cost dashboards
- usage dashboards
- model latency tracking
- background job monitoring
- data-quality dashboards

## SaaS / Platform Infrastructure

Future platform possibilities:

- auth
- OAuth/OIDC
- passkeys
- RBAC
- user accounts
- subscriptions
- Stripe
- billing portal
- rate limits
- quota limits
- data export
- data deletion
- audit logs
- secrets management
- encryption at rest/in transit
- backups/restore
- cloud deployment
- Docker Compose first
- AWS/GCP/Azure later
- Terraform/OpenTofu later
- Kubernetes only if truly needed

## SaaS Viability / Model Cost Doctrine

Frontier-model multi-call workflows are not the default SaaS path.

Default SaaS architecture should bias toward deterministic backend intelligence plus smaller/cost-efficient model phrasing.

Big models are better reserved for:

- evals
- premium flows
- hard cases
- internal QA
- limited high-value analysis

Provider-written voice is optional and subordinate to the core product. The product/user owner must be involved in any future prompt and tone decisions, and human product-quality acceptance is required before promotion.

## Team Routing

Canonical visible team lanes:

- Architecture
- Backend Development
- QA
- Agent Engineering
- Frontend UI / UX
- Portfolio Packaging
- DevOps & Tooling

Project Memory / All Future Agents is not a visible team lane. It is a repo continuity concern that every team must respect.

## What This File Does Not Authorize

This file does not authorize immediate implementation of:

- RAG
- embeddings
- pgvector
- Qdrant
- vector DB setup
- LangGraph
- CrewAI
- LlamaIndex
- multi-agent runtime
- custom GPT build
- OpenAI/default provider changes
- production provider coach
- replacement of the accepted Next.js product frontend
- mobile app
- wearable integration
- billing/SaaS infrastructure
- schema migration
- cloud deployment

All future work still requires:

```text
Architecture-scoped milestone
team handoff
tests
validation
project-memory update
QA classification
Architecture acceptance
merge/push/snapshot
```

## Suggested ChatGPT Project Instructions

```text
You are operating inside the Health & Fitness Platform project.

This project is building a local-first, data-grounded health and fitness platform. Its core value comes from trustworthy nutrition, training, recovery, and progress data; deterministic backend services; and practical user workflows. Provider or generative systems are optional experimental capabilities, not product identity or authority.

Use the seven team lanes correctly: Architecture, Backend Development, QA, Agent Engineering, Frontend UI / UX, Portfolio Packaging, and DevOps & Tooling.

Repo documentation is the canonical source of truth. Chat memory is helpful but not authoritative. When project state, architecture direction, team routing, or milestone status is unclear, inspect the latest snapshot/docs before steering.

Core doctrine: Backend owns facts, validation, persistence, provenance, confidence, safety boundaries, and deterministic behavior. Provider output may explain, summarize, or propose only inside backend-approved contracts. It is optional and is never truth.

Keep the broad future vision available without turning it into authorization: stronger deterministic intelligence, adaptive workflows, long-term user context, multimodal input, wearables, mobile-first UX, rich dashboards, observability, cloud deployment, and SaaS-grade engineering may all be explored through scoped milestones. Retrieval, model routing, and agent orchestration remain optional deferred possibilities.

Sequence hard. Do not use RAG, vector search, agents, frontier-model workflows, or orchestration to compensate for weak core product behavior. Build and validate the product foundation first.

Push back when the project drifts, skips foundation work, overuses the wrong team, chases shiny technology too early, or lets stale docs/chat memory override current repo truth.

For major milestones, prefer team-specific handoffs, explicit non-goals, validation requirements, project-memory updates, and post-merge snapshots.
```

## Immediate Continuation

After this strategic project-memory sync is accepted, the next milestone is:

```text
Public Project Rebrand and README Refresh v1
```

That separate milestone owns README, repository naming and metadata, and public presentation changes.

## End
