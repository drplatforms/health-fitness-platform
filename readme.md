# AI Health Coach

AI Health Coach is a validation-first health coaching platform built with Python, FastAPI, Streamlit, SQLite, and local LLM provider integration through Ollama.

The system combines deterministic backend health, nutrition, recovery, and training logic with provider-integrated AI report sections. AI output is not rendered directly. Provider responses are parsed, validated, and either approved for user-facing display or replaced with deterministic fallback content.

Core principle:

> Backend owns the facts. AI writes only within approved context. Validators decide what reaches the user.

> **Disclaimer:** This project is for software engineering, experimentation, and personal productivity purposes. It is not medical advice, nutrition counseling, or a replacement for a qualified healthcare professional, registered dietitian, or certified coach.

---

## Project Overview

AI Health Coach is designed around the idea that useful AI coaching should be grounded in structured data, deterministic calculations, and backend validation rather than unrestricted model output.

The backend owns:

- logged nutrition values
- recovery check-ins
- workout and training data
- health-state construction
- macro target calculations and display permissions
- training constraints
- approved evidence claims
- parser and validator rules
- deterministic fallback behavior
- public-safe persistence and status boundaries

AI providers may generate bounded report language only from backend-approved context. Provider output must pass strict parsing and validation before anything becomes user-facing.

The goal is not to build a generic fitness chatbot. The goal is to build a serious backend-driven coaching platform where AI can improve explanation quality without bypassing deterministic safety and correctness rules.

---

## Current Status

The current main branch includes the merged Training Evidence Claim Service and Nutrition Level 5 provider milestone.

Current confirmed state:

- Training Report Section is Level 5 provider-integrated.
- Nutrition Report Section is Level 5 runtime validated.
- Nutrition Report Section provider status is `opt_in_full_report_integrated`.
- Nutrition Target Display remains a separate Level 2 display contract.
- `direct_ollama/qwen2.5:3b` is approved as a tested opt-in provider path.
- qwen3 remains experimental and is not approved.
- Deterministic fallback remains mandatory.
- Provider gates remain mandatory.
- Provider output is parsed and validated before rendering.
- Invalid provider output falls back deterministically.
- Public/status/persisted sanitizer boundaries remain intact.
- Runtime QA matrices were executed across seeded users 101–105.
- Nutrition Level 5 Promotion Runtime QA v1 passed.

Honest coverage note:

Fallback architecture and deterministic fallback behavior are implemented and required, but the latest Nutrition Level 5 fallback runtime semantics were not fully runtime-tested because the project does not yet have a safe QA-only forced-invalid provider mode.

---

## What It Does

AI Health Coach currently supports:

- recovery check-ins
- nutrition logging
- canonical food search and logging
- formula-derived macro target display
- target-vs-actual nutrition tracking
- nutrition food suggestions
- workout logging
- exercise catalog search and filtering
- workout plan preview
- workout execution tracking
- health-state display
- daily grounded recommendations
- AI health report generation
- latest report and report history views
- provider-integrated Training Report Section
- provider-integrated Nutrition Report Section
- developer/debug metadata for provider runtime inspection

The app is local-first and currently designed for controlled development, QA, and portfolio demonstration rather than production healthcare use.

---

## Architecture

The project follows a validation-first pipeline:

```text
User data
→ backend-derived health state
→ deterministic targets and constraints
→ approved provider context
→ local LLM candidate output
→ strict parser
→ backend validator
→ approved report section or deterministic fallback
→ public-safe rendering
