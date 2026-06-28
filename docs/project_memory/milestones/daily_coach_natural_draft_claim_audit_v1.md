# Daily Coach Natural Draft + Claim Audit v1

Status: Backend implementation in progress.

Branch: feature/daily-coach-natural-draft-claim-audit-v1

Baseline: main at b9b46c9, after Prompt Lab / Voice Lab v1 was merged as developer-only tooling.

## Objective

Build a developer-only natural draft + claim audit flow for Daily Coach provider copy.

This milestone is the product-voice pivot after v5 and Prompt Lab showed that constrained prompt variants alone were not solving Daily Coach voice.

## Scope

- ApprovedCoachBrief model and builder
- Natural draft writer path
- deterministic claim extraction
- backend claim audit
- one repair attempt
- deterministic fallback after repair failure
- developer CLI
- sanitized artifacts
- tests
- project memory updates

## Non-goals

No production Today replacement, provider promotion, parser relaxation, final approval bypass, public UI, Streamlit provider controls, RAG, embeddings, meal planning, workout generation changes, recovery score changes, or background worker.

## Acceptance target

QA should verify the developer-only workflow runs, artifacts are sanitized, high-risk claims are detected, unsupported claims fail, one repair attempt is enforced, and normal Today behavior remains unchanged.
