# Open Questions

Last updated: 2026-06-18

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- Which safe validation diagnostic categories repeat across users 101-105 during Nutrition Provider Diagnostic Matrix QA Retry v1?
- Which diagnostic category should be addressed first if qwen2.5 still fails validation for matrix users after diagnostic propagation is confirmed?
- What additional runtime cases are needed before Architecture considers Level 5 promotion?
- What additional negative validator cases are required after observing real qwen2.5 output in matrix runtime QA?
- When should Nutrition provider metadata be allowed into persisted full-report history, and at what level of detail?
- Should debug/QA-only Nutrition validation diagnostic categories remain limited to `/reports/status/{job_id}/debug`, or should Architecture define a broader debug-only QA surface later?

## Recovery

- What backend-owned recovery evidence is needed before recovery becomes a provider-ready section?

## Grounded Recommendation

- How should cross-domain recommendations consume approved section claims without becoming a monolithic AI-owned summary?

## Developer workflow

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?
