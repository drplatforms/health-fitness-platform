# Open Questions

Last updated: 2026-06-18

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- Should Architecture approve `Nutrition Full Report Opt-In Integration v1` after the design review?
- Should full-report Nutrition integration use a separate full-report integration gate in addition to the existing section provider gate?
- What exact safe Nutrition metadata keys should be added to persisted full-report history during implementation?
- Should the initial full-report Nutrition integration render a distinct Nutrition Report Section below Nutrition Target Display?
- What exact runtime QA matrix is required before Nutrition can move from Level 4 to Level 5?
- What additional negative validator cases are required after observing real qwen2.5 output in section-only runtime QA?
- When should Nutrition provider metadata be allowed into persisted full-report history, and at what level of detail?

## Recovery

- What backend-owned recovery evidence is needed before recovery becomes a provider-ready section?

## Grounded Recommendation

- How should cross-domain recommendations consume approved section claims without becoming a monolithic AI-owned summary?

## Developer workflow

- Should the new Windows validation helper eventually be mirrored with a Linux runtime-QA helper?
