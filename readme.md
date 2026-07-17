# Health & Fitness Platform

A local-first, full-stack health and fitness application for nutrition tracking, workout planning and execution, recovery monitoring, and deterministic coaching.

The platform is built around a simple rule: **the backend owns truth**. Calculations, validation, persistence, historical state, and decision logic remain explicit and inspectable. AI/provider integrations may assist with selected workflows or experimentation, but the core product does not depend on a model to function and does not hand authoritative health decisions to one.

**Current stack:** Python 3.11 · FastAPI · Next.js 16 · React 19 · TypeScript · SQLite

> **Project status:** Actively developed. This is a software engineering and personal fitness tracking project, not a production healthcare service or a replacement for qualified medical, nutrition, or coaching advice.

## Why this project exists

Nutrition logs, workouts, recovery data, and coaching recommendations are often treated as separate products. This project explores what happens when they share one historically correct backend state.

A food entry should keep the nutrition truth that was logged at the time. A completed workout should preserve what was actually prescribed and performed. A progression recommendation should come from inspectable training evidence. Recovery can influence training without silently rewriting it. New convenience features should reuse existing application truth rather than creating parallel systems.

The result is an application designed around **daily usefulness, explainability, and continuity over time**.

## Current capabilities

### Nutrition

- Canonical food search and serving-aware logging
- Grams fallback when no trustworthy serving conversion exists
- User-owned personal foods with immutable nutrition revisions
- Historically stable food logs tied to the identity and revision originally logged
- Food logging recents plus edit and delete workflows
- Formula-derived nutrition targets and target-vs-actual tracking
- Nutrition trend and calibration foundations
- Live UPC, EAN, and GTIN barcode scanning
- Local-first barcode resolution with USDA FoodData Central branded-food lookup and Open Food Facts fallback
- Explicit confirmation before externally discovered products become canonical local foods
- Saved reusable meals containing canonical and personal foods
- Transactional whole-meal logging into normal individual food entries

### Training

- Equipment-aware deterministic workout planning
- Quick, Standard, and Extended workout variants
- Workout preview, selection, start, execution, and completion flows
- Set-level reps, weight, and RIR logging with edit and delete support
- Planned-versus-actual execution history
- Curated exercise catalog with structured exercise explanations
- Smart exercise substitutions ranked within valid movement/equipment constraints
- Substitution-aware workout history and progression evidence
- Adaptive progression guidance based on recent completed performance and recovery state
- Conservative progression decisions such as add reps, increase load, hold, ease back, or gather more data
- Historical workouts preserved as read-only execution records

### Recovery

- Daily recovery check-ins
- Sleep, energy, soreness, stress, and body-weight inputs
- Deterministic readiness and recovery intelligence
- Recovery-aware training context
- Recovery used as a bounded progression brake rather than an opaque workout override
- Longitudinal recovery state available to downstream coaching and decision services

### Daily product experience

The Next.js frontend is organized around four primary mobile workspaces:

```text
Today · Food · Workout · Recovery
```

- Mobile navigation uses real route-based workspaces rather than one long cross-domain page
- Food provides dedicated logging, barcode scanning, saved meals, logged foods, and personal-food workflows
- Workout prioritizes exercise execution and compact progression/history context
- Recovery provides a focused check-in and readiness surface
- Today remains a daily overview and has room to grow independently
- Live date-less daily routes follow the browser-local calendar day
- Explicitly dated historical workout views remain pinned and read-only
- Light, Dark, and System theme modes are supported
- Desktop retains a richer multi-domain overview where additional information density is useful

## Architecture

```text
                         ┌─────────────────────────┐
                         │      Next.js UI         │
                         │ Today / Food / Workout  │
                         │      / Recovery         │
                         └────────────┬────────────┘
                                      │ REST / JSON
                         ┌────────────▼────────────┐
                         │        FastAPI          │
                         │   routes + contracts    │
                         └────────────┬────────────┘
                                      │
                ┌─────────────────────▼─────────────────────┐
                │           Deterministic services          │
                │                                           │
                │ Nutrition · Training · Recovery · Coach   │
                │ Validation · History · Ownership · Rules  │
                └───────────────┬───────────────────────────┘
                                │
                         ┌──────▼──────┐
                         │   SQLite    │
                         │ local state │
                         └─────────────┘

 External read sources:
 USDA FoodData Central · Open Food Facts

 Optional experimental/provider layer:
 CrewAI / local-model / provider integrations behind backend contracts
```

### Selected architectural boundaries

- **Backend owns truth.** Calculations, validation, persistence, and historical state live behind explicit service boundaries.
- **Deterministic first.** Core product workflows remain usable without an LLM or external inference provider.
- **Unknown is not zero.** Missing health or nutrition data is preserved as unknown when the source does not justify a value.
- **History stays historically correct.** Logged records keep the identity, revision, prescription, and provenance required to avoid silent reinterpretation later.
- **User-owned records are scoped by user.** Personal foods, saved meals, and related service operations enforce ownership boundaries.
- **External data is not blindly trusted.** Barcode provider results are validated, normalized, and explicitly confirmed before canonical materialization.
- **One source of application truth.** Convenience features such as saved meals and barcode imports feed existing food logging and nutrition totals rather than creating parallel accounting systems.
- **AI is optional and non-authoritative.** Experimental provider infrastructure exists, but deterministic backend contracts remain the final gate.

## External food data

Barcode scanning uses a local-first resolution path:

```text
local canonical/raw barcode identity
        ↓
USDA FoodData Central branded-food lookup
        ↓
Open Food Facts fallback
        ↓
user confirmation
        ↓
barcode-safe canonical materialization
        ↓
existing serving and food logging workflow
```

The system uses exact normalized barcode identity rather than fuzzy product-name matching when deciding whether two packaged products are the same item.

A successfully imported product becomes part of the local canonical catalog, so future scans can resolve locally without repeating the full external lookup flow.

## Current stack

### Backend

- Python 3.11 target
- FastAPI
- Pydantic
- SQLite
- Pytest
- Ruff

### Frontend

- Next.js 16
- React 19
- TypeScript 5
- Tailwind CSS 4
- ZXing browser barcode decoding
- ESLint

### Engineering workflow

- Git and GitHub feature-branch workflow
- Project-memory contracts for architecture and milestone continuity
- Targeted regression suites
- Isolated-database validation for milestone QA
- Production-mode browser smoke for user-visible changes
- Real-device mobile acceptance testing
- Snapshot-based milestone closeout

## Local development

### Prerequisites

- Python 3.11
- Node.js / npm compatible with the current Next.js toolchain
- Git

Core deterministic workflows do not require an AI provider.

For remote branded-food barcode lookup, configure the relevant values from `.env.example`:

```text
FDC_API_KEY=
OPEN_FOOD_FACTS_USER_AGENT=HealthFitnessPlatform/1.0 (your-email@example.com)
```

`FDC_API_KEY` is a private runtime secret and must not be committed.

### Backend

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

The application initializes its additive local database schema on startup.

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
npm run start -- --hostname 127.0.0.1 --port 3100
```

Open:

```text
http://127.0.0.1:3100
```

Port `3100` is the standard local production-mode frontend acceptance port for this project.

For LAN development, bind deliberately to an appropriate network interface instead of `127.0.0.1`. Do not expose local development ports directly to the public internet.

Private remote access and HTTPS termination are deployment concerns and are intentionally kept outside the repository.

## Validation

Backend:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Project memory:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_project_memory_check.py -q
.\.venv\Scripts\python.exe tools/project_memory_check.py --project-root .
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

User-visible milestones are additionally validated through production-mode browser smoke. Database-sensitive validation is performed against isolated database copies rather than the canonical local application database.

## Repository structure

```text
api/                  FastAPI application and route contracts
models/               Domain and API data models
services/             Deterministic application/domain services
frontend/             Next.js product frontend
tests/                Backend and workflow regression coverage
tools/                Diagnostics, validation, and developer utilities
scripts/              Local workflow helpers
data/                 Food/source datasets and development data assets
ui/                   Legacy/developer Streamlit surfaces
docs/project_memory/  Architecture history, milestone contracts, and accepted state
```

## Project status

Health & Fitness Platform is under active development.

The current system already supports a substantial end-to-end daily workflow across food logging, packaged-food import, reusable meals, workout execution, exercise guidance, substitutions, adaptive progression, recovery tracking, and longitudinal state.

Near-term development is focused on continuing to improve the usefulness of the daily training and nutrition experience, expanding planning capabilities, strengthening deterministic QA scenarios, and refining the product as real-world use exposes friction.

This repository should be read as an evolving engineering system rather than a finished commercial healthcare product.

## Historical note

Earlier versions of the project were branded **AI Health Coach** and included extensive local-model and provider experimentation.

That work remains part of the repository's engineering history, but the platform has since evolved into a broader health and fitness system whose core value comes from its data model, deterministic services, historical correctness, and practical user workflows. AI remains a possible supporting capability rather than the foundation of product truth.
