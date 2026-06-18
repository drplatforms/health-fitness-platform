# Open Questions

Last updated: 2026-06-18

## Daily Coaching Product Loop

Resolved for v1:

- Daily Next Action Panel v1 uses a deterministic backend service and stable API route before Streamlit renders it.
- Priority order is recovery/safety, missing recovery input, nutrition logging completeness, workout readiness, report guidance, then data-quality/nutrition-target progress.
- Workflow targets are limited to existing surfaces: Today recovery check-in, Today workout, Nutrition quick log, Nutrition target-vs-actual, Workout preview, and Reports guidance.
- Seeded QA classes are defined for users 101, 102, and 105.

Open after v1 implementation:

- Should future versions support a secondary action, or should Today remain strictly one primary action?
- Should workflow targets become real Streamlit navigation anchors after UI navigation is formalized?
- Should action availability be persisted for analytics, or remain read-only/computed at request time?
- How should the panel behave once catalog expansion and food logging usability improve?


## Catalog Expansion & Curation

Planning status: `CATALOG_EXPANSION_CURATION_V1_PLANNED_PENDING_ARCHITECTURE_ACCEPTANCE`.

Resolved in planning draft:

- Current starter inventory is documented at planning level: 132 canonical starter foods and 178 curated exercise entries observed in the code snapshot.
- Food Catalog Expansion v1 is recommended as the first implementation slice because Daily Next Action Panel v1 often routes users to food logging.
- Exercise Catalog Expansion v1 is recommended second because workout variety, equipment matching, substitutions, and recovery suitability are the next training-loop usability bottlenecks.
- Catalogs should remain deterministic, curated, inspectable, testable, and backend-owned.
- RAG, embeddings, scraping, AI-generated production entries, meal planning, and unreviewed catalog dumps remain out of scope.

Open for Architecture review:

- Should Food Catalog Expansion v1 add only new seed entries, or also add explicit first-class category fields?
- Should default serving sizes remain optional metadata or become required for quick logging?
- Should fiber and sodium be required for new foods or remain optional v1 nutrients?
- Should Exercise Catalog Expansion v1 require schema changes for joint stress, recovery suitability, substitution group, setup notes, and safety notes, or start with deterministic constants/docs first?
- What is the target size for curated Food Catalog Expansion v1 and Exercise Catalog Expansion v1 before QA?
- Should catalog additions be split by user-relevant home-gym and food-logging priorities rather than broad generic completeness?

## Product voice

- When should qwen3 be re-tested for Training product voice?
- What validator/evidence improvements are needed before qwen3 can safely sound more natural?

## Nutrition

- After accepted forced-fallback runtime QA, should public claims be updated to say Nutrition fallback semantics are runtime-validated through a QA-only forced-invalid provider mode?
- Should a future production-like fallback QA scenario be designed, or is the QA-only forced-invalid mode sufficient for portfolio claims and regression protection?
- Should Nutrition remain opt-in indefinitely after Level 5 runtime validation, or should a separate future default-provider readiness review be planned?
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
