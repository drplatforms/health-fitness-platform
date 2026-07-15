# Health & Fitness Platform

A local-first health and fitness application for nutrition tracking, workout planning and execution, recovery data, and longitudinal user state.

The platform is built around a simple rule: **the backend owns truth**. Core calculations, history, ownership, validation, and decision logic are deterministic and inspectable. Optional provider or generative systems may assist with explanation or experimentation, but they are not required for the product to function and do not own health decisions.

> **Disclaimer:** This project is a software engineering and personal fitness tracking project. It is not medical advice, nutrition counseling, or a replacement for a qualified healthcare professional, registered dietitian, or certified coach.

## What the platform supports

### Nutrition

- Canonical food search and logging
- Grams and serving-unit logging
- Food logging recents
- Edit and delete workflows
- Formula-derived nutrition targets
- Target-vs-actual daily nutrition tracking
- Nutrition trend and calibration foundations
- User-owned personal foods
- Immutable personal-food nutrition revisions
- Archive and restore for personal foods
- Historically stable personal-food logs tied to the exact revision originally logged

### Training

- Equipment-aware workout planning
- Quick, Standard, and Full workout sizes
- Exercise rotation and catalog-driven variation
- Exercise substitution workflows
- Workout selection and start state
- Set logging, editing, and deletion
- Workout completion review
- Planned-versus-actual execution evidence
- Workout history and progression context

### Recovery

- Daily recovery check-ins
- Sleep, energy, soreness, stress, and body-weight inputs
- Readiness and recovery state
- Recovery-aware training context
- Longitudinal recovery data

### Daily product workflow

The Next.js application brings nutrition, training, recovery, and daily state into one practical workflow. The product favors compact, backend-grounded interactions over chatbot-style behavior.

## Architecture principles

The project has evolved through several generations, but its current architecture is guided by a consistent set of rules:

- **Backend owns truth.** Calculations, validation, persistence, ownership, and historical state live behind explicit service boundaries.
- **Deterministic first.** Core workflows must remain useful without a model or external provider.
- **Unknown is not zero.** Missing nutrition and health data is preserved as unknown when the source does not justify a value.
- **History stays historically correct.** Logged records retain the identity, revision, and provenance needed to avoid silent reinterpretation later.
- **User-owned data stays user-scoped.** Personal foods and related operations enforce ownership boundaries.
- **Validation before presentation.** External or generated output cannot bypass backend contracts and validators.
- **Advanced intelligence is optional.** Experimental provider infrastructure exists in the repository, but it is not the product identity and is not authoritative.

## Current stack

### Backend

- Python 3.11
- FastAPI
- Pydantic
- SQLite
- SQLAlchemy
- Pytest
- Ruff

### Frontend

- Next.js 16
- React 19
- TypeScript 5
- Tailwind CSS 4
- ESLint

### Development and quality

- Git / GitHub
- Project-memory validation
- Targeted regression suites
- Production-mode browser smoke for user-visible milestones
- Snapshot-based milestone closeout

## Local development

### Backend

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run build
npm run start -- --hostname 0.0.0.0 --port 3100
```

Open:

```text
http://127.0.0.1:3100
```

For this project, port `3100` is the standard production-mode frontend acceptance port.

## Validation

Backend:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Project memory:

```powershell
.\.venv\Scripts\python.exe tools/project_memory_check.py --project-root .
.\.venv\Scripts\python.exe -m pytest tests/test_project_memory_check.py -q
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

User-visible changes are also validated through production-mode browser smoke.

## Repository structure

```text
api/                  FastAPI routes and API contracts
services/             Deterministic application and domain services
frontend/             Next.js product frontend
ui/                   Legacy/developer Streamlit surfaces
tests/                Backend and workflow regression coverage
tools/                Diagnostics, validation, and developer utilities
scripts/              Local workflow helpers
docs/project_memory/  Architecture history, milestones, and accepted project state
```

## Project status

Health & Fitness Platform is an actively developed local-first engineering project and portfolio system. It is not a production healthcare service.

The current product direction centers on:

- stronger nutrition workflows and food data
- deeper training and workout execution intelligence
- recovery and longitudinal state
- deterministic recommendation and decision systems
- reliable provenance and historical correctness
- practical mobile-first product UX

Optional provider, retrieval, and orchestration technologies may be explored later where they create measurable product value. They are not prerequisites for the core platform.

## Historical note

Earlier versions of the project were branded **AI Health Coach** and included extensive local-model and provider experimentation. That work remains part of the repository's engineering history, but the project has since evolved into a broader health and fitness platform whose core value comes from its backend systems, data model, deterministic logic, and user workflows.
