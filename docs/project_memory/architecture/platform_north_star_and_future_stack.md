# Future Technical Architecture Reference

> Canonical technical future-architecture reference. This file is stable, non-authorizing, and not a default strategic source. Load it only when a task specifically concerns future architecture or stack decisions. Product direction lives in `docs/project_memory/product_north_star.md`; operational truth and implementation authority live in `docs/project_memory/current_truth.json`.

## Purpose

This reference preserves plausible long-term technical directions, dependencies, and safety boundaries without turning technology options into product commitments.

Every item here requires a separately authorized, bounded milestone before implementation. Candidate technologies are examples to evaluate, not defaults or approved dependencies.

## Architectural Doctrine

- Backend services own facts, calculations, constraints, validation, provenance, confidence, decisions, persistence, and deterministic fallback.
- Core workflows remain useful with all providers and generative systems disabled.
- Provider output may propose or explain only within backend-approved context and never becomes truth by fluency.
- Retrieved content and vector matches are evidence candidates, not facts or decisions.
- Model routing and tool permissions are backend-owned and inspectable.
- Consequential writes require explicit backend policy and user approval.
- Personal data and inferred memory must be inspectable, correctable, exportable, and deletable.
- Safety, privacy, observability, cost, rollback, and provenance are architecture concerns from the beginning.

## Foundation Before Advanced Systems

Advanced retrieval, model routing, or orchestration is useful only after the product has stable, inspectable source-data contracts.

Potential foundation layers include:

- a deterministic unified health-state projection;
- stable nutrition, workout, recovery, and history contracts;
- user profile, preference, goal, and constraint models;
- provenance, confidence, and data-quality indicators;
- deterministic recommendation and policy services;
- scenario-based quality evaluation;
- structured decision and observation outputs.

No advanced system should compensate for weak product behavior or unclear backend ownership.

## Local-First Evolution

The local-first foundation should remain a product and privacy advantage as deployment matures.

Possible evolution includes:

- local server and LAN deployment;
- offline-capable clients with conflict-safe synchronization;
- service-managed application processes;
- containerized development or deployment when it improves reliability;
- deliberate migration from SQLite only when multi-user or operational needs justify it;
- backup, restore, import, export, and retention tooling;
- clear environment and configuration profiles.

Local-first evolution does not require discarding deterministic services or forcing cloud dependence into core workflows.

## Provider Abstraction

A future provider layer may support multiple local or remote systems behind one validated backend contract.

Potential capabilities include:

- explicit provider adapters;
- a model capability registry;
- latency, cost, parse, validation, and fallback telemetry;
- manual preview and evaluation lanes;
- async or precomputed explanation where product value justifies it;
- per-capability provider policies;
- sanitized audit trails;
- deterministic renderers and fallback.

Provider systems must not own normal product truth, silently change decisions, persist hidden memory, expose rejected output, or become mandatory for daily use.

## Curated Knowledge and Selective RAG

Retrieval may support a specific grounding or explanation need using trusted, source-tagged material.

Potential sources include:

- curated exercise knowledge;
- curated nutrition and recovery references;
- approved product help and education;
- backend-approved recommendations;
- bounded user-specific history and evidence.

Preferred flow:

```text
grounded product data
-> deterministic analysis
-> targeted source-tagged retrieval
-> optional interpretation
-> validation and safe presentation
```

RAG does not decide, prescribe, create truth, or override backend calculations. Broader retrieval is justified only by a concrete product need and source-trust model.

## Vector Retrieval and Embeddings

Vector retrieval may eventually support semantic discovery across curated knowledge or bounded personal history.

Candidate approaches include integrated relational extensions or a dedicated local retrieval store. Technology selection should follow measured use cases, metadata quality, deletion semantics, privacy boundaries, and operational cost.

Required boundaries include:

- stable document and evidence identities;
- source, user, date, and confidence metadata;
- inspectable retrieval results;
- deterministic filtering before semantic ranking;
- safe deletion and rebuild paths;
- no conversion of similarity into factual authority.

## Model Routing

A future model router may assign narrowly defined tasks to deterministic services, small structured-output models, larger explanation models, perception models, or fallback renderers.

Routing must remain:

- backend-owned;
- policy-gated;
- quality- and cost-aware;
- logged and inspectable;
- covered by capability-specific evaluations;
- unable to expand a model's authority.

No model chooses its own tools, data scope, persistence rights, or decision authority.

## Agents and Orchestration

Agents or workflow orchestration may be useful for bounded, auditable tasks after domain services expose reliable evidence and permissions.

Potential patterns include:

- explicit state machines;
- human-in-the-loop review;
- policy-gated tool execution;
- durable job states and retry rules;
- trace artifacts;
- structured specialist handoffs;
- cancellation and recovery.

Agent tools should call approved backend APIs rather than receive raw database freedom. Autonomous consequential writes are outside this reference unless a later milestone explicitly designs and authorizes them.

## Background Jobs

Recoverable async work may support long-running or scheduled workflows such as imports, reports, evaluations, backups, or approved retrieval indexing.

A job system should provide:

- explicit pending, running, succeeded, failed, retrying, and cancelled states;
- idempotency or clear duplicate policy;
- bounded retries and timeouts;
- observable progress and sanitized failure details;
- safe cancellation and replay;
- deterministic fallback for user-facing paths.

Start with the simplest durable mechanism that satisfies the approved use case.

## Data and Storage Maturity

Possible future capabilities include:

- disciplined schema migrations;
- relational storage suited to multi-user operation;
- structured event and audit records;
- data-quality validation;
- job, report, observation, and memory ledgers;
- embedding metadata where retrieval is approved;
- encrypted backup and restore;
- import, export, deletion, and retention controls;
- analytical projections or columnar stores when evidence volume justifies them.

Schema and storage changes require explicit migration, rollback, compatibility, and canonical-database safety plans.

## Inspectable Personal Memory

Long-term personal context may include facts, preferences, goals, constraints, schedule patterns, recurring barriers, and structured observations.

Memory must be:

- typed by meaning and source;
- separated from generated prose;
- confidence- and staleness-aware;
- inspectable and correctable by the user;
- exportable and deletable;
- written only through explicit backend and user-approved rules.

Hidden model memory is not an acceptable product architecture.

## Multimodal Input

Potential input modes include:

- barcode and nutrition-label capture;
- food, menu, or receipt images;
- voice-assisted check-ins and logging;
- document parsing;
- future movement or form media analysis.

Perception systems may propose structured candidates. The user confirms consequential interpretation, and backend services resolve candidates to grounded identities and validated calculations.

## Wearables and External Integrations

Potential integrations include health platforms, wearables, smart scales, calendars, notifications, recipe or grocery services, and trusted public catalogs.

Integration architecture should preserve:

- explicit source provenance;
- source-specific uncertainty;
- permission minimization;
- revocation and deletion behavior;
- manual entry as a first-class path;
- graceful operation when an external system is unavailable.

External signals support decisions; they do not become unquestioned truth.

## Frontend and Cross-Device Maturity

Possible evolution includes:

- a shared design system;
- generated or strongly typed API clients;
- mobile-first responsive workflows;
- offline/PWA capabilities;
- accessible charts and longitudinal analysis;
- stronger end-to-end automation;
- phone, desktop, tablet, and carefully chosen wearable surfaces.

Frontend evolution should preserve backend authority and avoid duplicating decision logic in clients.

## Observability and Quality

Future operational maturity may include:

- structured logs and trace identifiers;
- health endpoints and service-level signals;
- metrics for errors, latency, fallback, validation, and data quality;
- distributed tracing where multiple services justify it;
- provider and retrieval evaluation dashboards;
- reproducible QA artifacts;
- contract, integration, regression, and end-to-end test layers;
- release and rollback evidence.

Diagnostics must be useful without leaking sensitive health-adjacent data or unsafe raw provider output.

## Security and Privacy

Possible platform controls include:

- authentication and role boundaries;
- least-privilege tool and service permissions;
- encryption in transit and at rest where appropriate;
- secret and dependency scanning;
- audit logging;
- prompt-injection and unsafe-tool defenses;
- provider-visible-data controls;
- user export and deletion;
- backup and restore drills;
- explicit medical, nutrition, and exercise safety boundaries.

Privacy, correction rights, and data ownership must remain visible product capabilities rather than hidden infrastructure details.

## Deployment and SaaS Maturity

Deployment may evolve through measured stages such as local services, containers, reverse proxies, TLS, managed databases, cloud hosting, infrastructure as code, and horizontally scalable components only when justified.

Carefully bounded SaaS possibilities include:

- user accounts and tenancy isolation;
- consent-based trainer or coach workflows;
- subscriptions, quotas, and billing controls;
- rate limits and abuse protection;
- reliable backups and regional data policies;
- operational support and auditability.

Kubernetes, distributed services, frontier-model multi-call workflows, and other expensive infrastructure are not default maturity goals. They require a concrete scale, reliability, or product need.

## Technology Selection Rule

Select technology only after the approved milestone defines the user problem, ownership boundary, data and safety model, failure behavior, migration path, validation, and operational cost.

Prefer the smallest architecture that preserves deterministic behavior, local-first value, explainability, privacy, and future replacement paths.

## Non-Authorization Boundary

This reference does not authorize RAG, embeddings, vector databases, provider changes, model routing, agents, tool runtimes, multimodal inference, wearable integrations, schema migration, frontend replacement, cloud deployment, billing, or SaaS infrastructure.

Those possibilities remain available for separate Architecture scoping. Their presence here is preservation of technical direction, not approval to implement them.
