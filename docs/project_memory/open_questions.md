# Open Questions

Last updated: 2026-06-18

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- Will Nutrition Level 5 Promotion Runtime QA v1 confirm users 101-105 remain provider-approved after registry/metadata promotion?
- Will runtime QA confirm `provider_integrated_report_sections` includes `nutrition_report_section` only when approved provider Nutrition content actually rendered?
- What fallback-forced runtime case should QA use to confirm fallback Nutrition output is not falsely represented as provider-approved?
- Should Nutrition remain opt-in after Level 5 promotion until a separate default-provider decision is made?
- What additional non-seeded runtime cases are required after Level 5 promotion, if any?
- What additional negative validator cases are required after observing real qwen2.5 approved output in matrix runtime QA?
- When should Nutrition provider metadata be allowed into persisted full-report history, and at what level of detail?
- Should debug/QA-only Nutrition validation diagnostic categories remain limited to `/reports/status/{job_id}/debug`, or should Architecture define a broader debug-only QA surface later?

## Recovery

- What backend-owned recovery evidence is needed before recovery becomes a provider-ready section?

## Grounded Recommendation

- How should cross-domain recommendations consume approved section claims without becoming a monolithic AI-owned summary?

## Developer workflow

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?
