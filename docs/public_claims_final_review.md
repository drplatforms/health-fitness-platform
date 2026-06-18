# Public Claims Final Review v1

## Decision

PASS

AI Health Coach public-facing materials are approved for portfolio, GitHub, LinkedIn, resume, and interview use.

The current public package accurately positions the project as a validation-first health coaching platform with deterministic backend logic, provider-integrated report sections, strict parser/validator gates, deterministic fallback behavior, and public-safe rendering boundaries.

No feature, provider, API, persistence, Streamlit UI, or validation behavior changes are required as part of this review.

---

## Reviewed Materials

Reviewed public-facing materials:

- GitHub repo description
- README.md
- README screenshot captions
- README screenshot order
- Portfolio project summary
- LinkedIn project entry language
- Resume bullet variants
- Interview/project explanation language
- Public screenshot set under `docs/assets/portfolio`

---

## Final Public Positioning

Approved public positioning:

AI Health Coach is a validation-first health coaching platform built with Python, FastAPI, Streamlit, SQLite, and local LLM provider integration through Ollama.

The system combines deterministic backend health, nutrition, recovery, and training logic with provider-integrated AI report sections. AI output is not rendered directly. Provider responses are parsed, validated, and either approved for user-facing display or replaced with deterministic fallback content.

Core phrasing remains approved:

> Backend owns the facts. AI writes only within approved context. Validators decide what reaches the user.

The strongest public narrative is:

> I built a validation-first health coaching platform where backend services own truth, AI providers generate bounded report language, validators decide what reaches the user, and deterministic fallback keeps the product safe.

This should not be diluted into:

> I built an AI fitness app.

---

## Approved Claims

The following claims are approved for public use:

- AI Health Coach is a validation-first health coaching platform.
- The project is built with Python, FastAPI, Streamlit, SQLite, and local LLM integration through Ollama.
- Backend services own logged data, macro targets, training evidence, validation rules, fallback behavior, and public-safe rendering boundaries.
- AI providers generate bounded report language only from backend-approved context.
- Provider output is parsed and validated before reaching the user.
- Invalid provider output falls back to deterministic content.
- Training Report Section is Level 5 provider-integrated.
- Nutrition Report Section is Level 5 runtime validated.
- Nutrition Report Section provider status is `opt_in_full_report_integrated`.
- Nutrition Target Display remains a separate Level 2 display contract.
- `direct_ollama/qwen2.5:3b` is approved as a tested opt-in provider path.
- qwen3 remains experimental and is not approved.
- Deterministic fallback remains mandatory.
- Provider gates remain mandatory.
- Public/status/persisted sanitizer boundaries remain intact.
- Runtime QA matrices were executed across seeded users 101–105.
- Users 101–105 passed provider-approved Level 5 runtime QA.
- Disabled-gate semantics passed.
- The UI includes canonical food logging, nutrition target comparison, workout preview, daily coaching overview, and report rendering.
- Screenshot assets are portfolio-ready and public-safe.

---

## Required Corrections

No required corrections were identified.

README.md is approved as currently structured, including:

- opening validation-first summary
- disclaimer
- screenshot section near the top
- Project Overview
- Current Status
- What It Does
- Architecture
- Core Engineering Concepts
- provider/runtime configuration
- QA/testing section
- What This Project Is Not
- roadmap language

No README copy changes are required for this milestone.

---

## Public-Safe Limitations

The following limitation must remain preserved in technical/public materials:

Fallback architecture and deterministic fallback behavior are implemented and required, but the latest Nutrition Level 5 fallback runtime semantics were not fully runtime-tested because the project does not yet have a safe QA-only forced-invalid provider mode.

This limitation does not need to be overemphasized in marketing copy, but public materials must not contradict it.

Do not claim fallback runtime coverage is complete for the latest Nutrition Level 5 provider path.

---

## Screenshot Review

Approved README screenshot order:

1. Nutrition Target Bands / Target-vs-Actual
2. Canonical Food Logging
3. Workout Preview Card Layout
4. Today / Daily Coach Overview
5. Terminal Validation Passing

Approved screenshot files:

- `docs/assets/portfolio/nutrition-target-vs-actual.png`
- `docs/assets/portfolio/canonical-food-logging.png`
- `docs/assets/portfolio/workout-preview-card.png`
- `docs/assets/portfolio/today-daily-coach.png`
- `docs/assets/portfolio/terminal-validation.png`

Screenshot captions are approved.

The screenshot section correctly leads with product value while supporting the validation-first architecture story.

The screenshots do not expose:

- raw provider output
- rejected candidate text
- prompt/schema text
- raw debug metadata in normal UI
- traceback or exception internals
- raw validation errors
- unsupported nutrition claims
- unsupported training claims

---

## Repo Description Review

Current GitHub repo description:

> Backend-driven AI health coaching platform with deterministic health logic, strict provider validation, local Ollama integration, and safe fallback behavior.

Decision:

APPROVED

Rationale:

The description is concise, technical, and public-safe. It highlights backend ownership, validation, local provider integration, and fallback behavior without overclaiming AI autonomy or production healthcare behavior.

---

## Portfolio Summary Review

Approved portfolio summary:

> AI Health Coach is a validation-first health coaching platform built with Python, FastAPI, Streamlit, SQLite, and local LLM integration through Ollama. The project combines deterministic backend health logic with provider-integrated AI report sections that must pass strict parser and validator gates before reaching the user.
>
> The system models nutrition, recovery, training, macro targets, canonical food logging, workout execution, and evidence-based report generation. AI is used as a bounded explanation layer over backend-approved context, while deterministic fallback and public-safe metadata boundaries keep the platform reliable when provider output is invalid.

Decision:

APPROVED

Rationale:

The summary accurately communicates product scope, technical stack, AI boundaries, validation-first architecture, and fallback behavior. It does not claim medical authority, autonomous AI decision-making, meal planning, production RAG/embeddings, or unsupported provider behavior.

---

## LinkedIn Project Entry Review

Approved LinkedIn project language:

> Built a validation-first health coaching platform using Python, FastAPI, Streamlit, SQLite, and local LLM integration through Ollama.
>
> The project combines deterministic backend health, nutrition, recovery, and training logic with provider-integrated AI report sections. Backend services own logged data, macro targets, training evidence, validation rules, fallback behavior, and public-safe rendering boundaries, while AI providers generate bounded report language only from approved context.
>
> Key engineering work included strict JSON parsing, backend validation gates, deterministic fallback paths, seeded runtime QA matrices, provider debug metadata, canonical food logging, workout execution tracking, and evidence-based training/nutrition report sections.

Decision:

APPROVED

Rationale:

The LinkedIn copy is strong, concise, and engineering-focused. It accurately frames the project as a backend/platform engineering effort and does not overstate provider autonomy or healthcare authority.

---

## Resume Bullet Review

Approved resume themes:

- validation-first AI health coaching platform
- Python / FastAPI / Streamlit / SQLite
- local Ollama provider integration
- deterministic backend health logic
- strict parser/validator boundaries
- provider-integrated Training and Nutrition report sections
- seeded runtime QA matrices
- public-safe debug/status/persistence boundaries
- canonical food logging
- workout execution tracking
- deterministic fallback behavior

Decision:

APPROVED

Recommended strongest general-purpose bullet:

> Built a full-stack, validation-first AI Health Coach platform with deterministic backend logic, local LLM provider integration, strict parser/validator gates, safe fallback behavior, and polished Streamlit portfolio UI.

Recommended backend/platform bullet:

> Built a validation-first AI Health Coach platform using Python, FastAPI, Streamlit, SQLite, and local Ollama integration, with backend-owned health logic and provider-integrated training/nutrition report sections.

Recommended AI tooling bullet:

> Designed strict AI provider workflows where local LLM output is parsed, validated, and either approved for rendering or replaced with deterministic fallback content.

Recommended QA/reliability bullet:

> Implemented seeded runtime QA matrices, persistence-boundary checks, debug metadata separation, and sanitizer tests to prevent raw provider output, prompts, schemas, and validation internals from leaking into public surfaces.

Recommended full-stack bullet:

> Developed full-stack coaching workflows for canonical food logging, target-vs-actual nutrition review, workout preview, recovery check-ins, and evidence-backed report generation.

---

## Interview Explanation Review

Approved interview framing:

AI Health Coach started as a personal fitness and nutrition app, but the engineering focus became building a safe AI-backed coaching pipeline.

The backend owns the facts: nutrition logs, workout data, recovery state, macro targets, training evidence, and display permissions. AI providers do not get to invent those values. They receive approved context and return structured candidate output.

That output is parsed and validated before anything reaches the user. If the provider output is malformed, unsupported, or unsafe, the system falls back to deterministic backend-rendered content.

The main engineering challenge was creating the boundaries: strict provider contracts, validation rules, fallback behavior, debug-only runtime metadata, seeded QA scenarios, and public-safe rendering. The project is less about making an AI chatbot and more about building a backend platform where AI can improve coaching language without bypassing deterministic rules.

Decision:

APPROVED

---

## Forbidden Claims Confirmed Absent

Public materials must not claim or imply:

- `direct_ollama` is default
- qwen3 is approved
- meal planning exists
- RAG/embeddings/agents are production behavior
- AI calculates targets
- AI owns workout generation
- AI can invent food suggestions
- raw model output is persisted or exposed
- provider output bypasses backend validation
- fallback runtime coverage is complete for the latest Nutrition Level 5 path
- Nutrition Target Display and Nutrition Report Section are the same feature
- the app provides medical advice
- the app provides clinical nutrition counseling
- the app is production healthcare software
- the app replaces a doctor, dietitian, or certified coach

Decision:

PASS

No reviewed public material requires correction for these issues.

---

## Non-Goals Confirmed

This milestone did not and should not change:

- backend services
- API routes
- provider behavior
- validation services
- persistence behavior
- Streamlit UI behavior
- report generation behavior
- Nutrition Target Display behavior
- Nutrition Report Section behavior
- Training Report Section behavior
- test behavior
- screenshot image content

This was a documentation and claims-safety review only.

---

## Validation

Recommended validation for this docs-only milestone:

```powershell
git status --short
git diff -- README.md
git diff -- docs/public_claims_final_review.md
```

If README.md is unchanged, no code validation is required.

Optional light validation:

```powershell
python -m py_compile ui\streamlit_app.py
```

No pytest run is required for this milestone unless README links or code-adjacent files are changed.

---

## Final Decision

PASS

The public-facing AI Health Coach package is approved for use in:

- GitHub
- portfolio page
- LinkedIn project entry
- resume project bullets
- interview discussion
- recruiter/application review

The project should now be presented as:

> A validation-first health coaching platform where backend services own facts and rules, AI providers generate bounded report language, validators decide what reaches the user, and deterministic fallback keeps the system safe when provider output is invalid.
