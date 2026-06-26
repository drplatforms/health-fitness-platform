# Open Questions

## Nutrition Catalog + Serving Foundation Planning v1

Current planning questions for Architecture:

1. Should the next implementation milestone be Nutrition Catalog Diagnostic v1?

Recommended answer: yes.

2. Should curated canonical food expansion come before serving units?

Recommended answer: yes, but serving-unit modeling should be designed before expansion so the catalog schema does not need rework.

3. Should raw USDA/source import be implemented before curated expansion?

Recommended answer: no, not as the first implementation. Use curated expansion first, then raw/staging import later.

4. Should serving sizes be exact numbers or ranges?

Recommended answer: ranges plus default grams and confidence.

5. Should serving-unit logging be allowed immediately in the UI?

Recommended answer: not necessarily. Backend contract first, UI later.

6. Should AI/provider participate in serving conversion?

Recommended answer: no. Backend owns conversions.

7. Should AI/provider participate in meal/snack generation later?

Recommended answer: yes, but only from backend-approved foods, servings, actuals, targets, and gaps.

8. Should nutrition suggestions come before AI meal generation?

Recommended answer: yes. Deterministic food suggestions should come before AI-generated meal/snack candidates.

9. Should recovery be tackled before nutrition?

Recommended answer: no. Recovery is weaker, but nutrition is the better next learning/personal-use priority.

10. Should workouts continue before nutrition?

Recommended answer: no, unless a blocking workout regression appears. Workout foundation is good enough for now.

## Nutrition catalog and serving follow-up questions

- What is the current shape of food catalog tables/services?
- How many current foods are true canonical foods versus seed/demo foods?
- Which fields currently support aliases, source metadata, active flags, and per-100g nutrients?
- Where should serving units live: schema table, JSON metadata, or service-owned mapping first?
- What confidence enum should be used across logging, suggestions, and provider contracts?
- Which 150-300 foods should be included in the first curated expansion?
- Which 50-100 foods need serving units first?
- Should user-specific serving overrides be allowed in v1 or deferred?

## Exercise Eligibility Matrix v1 follow-up

Exercise Eligibility Matrix v1 created an explicit generator-facing eligibility service and developer diagnostic, but it intentionally did not force full catalog reachability.

Current known findings from the diagnostic baseline:

- 240 active catalog exercises.
- 237 equipment-compatible exercises.
- 232 generator-eligible exercises.
- 54 exercises appeared in the 10-variation deterministic sweep.
- 186 generator-eligible exercises did not appear in that sweep.
- top exclusion reason: `not_supported_by_current_generator_candidate_pools` (170).
- weak movement families: arms_biceps, arms_triceps, mobility.

Open follow-up questions:

- Should arms work remain mostly deferred, or should a future accessory slot make limited biceps/triceps work reachable?
- Should mobility exercises stay excluded until warmup/mobility slots exist?
- Should catalog reachability be improved through candidate-pool scoring, slot expansion, or a separate reachability audit first?
- Should the diagnostic eventually consume the eligibility service directly? An optional refactor patch failed to apply during v1 and was deliberately deferred instead of stacked blindly.

## Rolling multi-refresh novelty

Workout Preview Full-Slot Rotation v1 accepted immediate previous-preview anti-repeat only.

Rolling multi-refresh novelty is deferred to Workout Preview Rolling Exposure Rotation v2.

Open question: should long-window exercise exposure tracking be session-only, persisted, or derived from selected workout history?

## Provider strategy roadmap

Provider strategy remains pending.

Possible future planning should compare local-first `qwen` / `direct_ollama` paths with higher-tier OpenAI/provider adapter options, but no provider strategy implementation is authorized by the current nutrition planning milestone.

Provider may propose. Backend validates. User sees only approved output.

## Complex milestone process tuning

The current process doctrine is now: bite by bite, just bigger bites.

Open questions for future process/tooling work:

- Should dev assistant generate complexity scores for proposed milestones?
- Should dev assistant generate expected file-change budgets automatically?
- Should stop-condition handoffs get a repo-owned template?
- Should feature branch validation check whether the original smoke failure has a corresponding regression or diagnostic test?

## Daily Narrative feedback hardening

The first feedback-driven deterministic copy hardening pass is implemented. A future milestone may decide whether to continue provider-facing examples and validation prompt guidance, or pause Daily Narrative while workout/catalog/nutrition systems continue maturing.

## Feedback storage lifecycle

The v1 feedback store is local JSONL and should not be committed by default. A future milestone may decide whether selected approved examples should be manually promoted from runtime feedback into project-memory docs. Raw runtime JSONL should not be committed.

## Model selection

Do not treat bad copy or strict-schema failures as a model-size issue by default. The current priority is better approved context, stricter contracts, deterministic fallback, diagnostics, and well-scoped provider experiments.
