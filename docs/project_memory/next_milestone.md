# Next Milestone — Daily Coach Wide Context Copy Cleanup + QA Readability v1

Owner: Backend Development with Architecture, QA, and Agent Engineering review.

Baseline: `main` at `42d0bd4 Merge daily coach wide context ceiling trial v1`.

Baseline snapshot: `fitness_ai_snapshot_2026-06-28_42d0bd4_main_merge-daily-coach-wide-context-ceiling-trial-v1.zip`.

Recommended branch: `feature/daily-coach-wide-context-copy-cleanup-qa-readability-v1`.

Goal: keep the wide-context ceiling-trial architecture, but improve user-facing first-pass copy language, prompt/context packaging, and terminal-friendly QA artifact readability.

Required outputs:

- prompt/context cleanup for backend-shaped user-facing wording;
- food choices represented as plain food language, not internal approval language;
- product-language diagnostic scan for QA readability;
- compact first-pass draft artifact;
- variant score summary artifact;
- best variant summary artifact;
- product language findings artifact;
- pasteback report artifact printable with `cat "$out/pasteback_report.md"`;
- optional CLI print flags for first pass, compact comparison, best variant, product issues, and pasteback report path;
- targeted tests for copy cleanup, scan behavior, artifact generation, and CLI flags;
- project memory updates.

Boundaries:

- no normal Today behavior changes;
- no Streamlit changes;
- no API route changes;
- no full report behavior changes;
- deterministic remains default;
- OpenAI remains opt-in/evaluation-only;
- no provider promotion;
- no raw provider envelope persistence;
- no secrets, raw DB rows, or public UI exposure;
- no parser relaxation;
- no Product Voice Audit rewrite;
- no meal planning, workout generation, nutrition target mutation, or recovery score mutation.

Known baseline drift to document, not patch here:

- `tests/test_daily_narrative_rich_day_service.py` copy-expectation mismatches on the supplied baseline lineage.
- Example: expected `Read the day before adding more`; actual `Consider the full day`.
- Full-suite green must not be claimed if this remains.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_COPY_CLEANUP_QA_READABILITY_V1_IMPLEMENTATION_COMPLETE`.
