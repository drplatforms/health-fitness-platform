# Section Registry Summary

Last updated: 2026-06-18

## Current full-report sections

| Section id | Display purpose | Current maturity | Provider status |
|---|---|---:|---|
| overall_score | High-level score/status | 1 | None |
| profile_context | User profile and context | 1 | None |
| grounded_recommendation | Approved action-plan recommendation | 3 | Not provider-owned |
| nutrition_target_display | Backend-approved target display | 2 | None |
| nutrition_report_section | Provider-integrated full-report Nutrition voice section with opt-in direct_ollama/qwen2.5 path, strict parser/validator, backend-approved practical_food_focus options, report-specific provider-integrated metadata, and deterministic fallback | 5 | direct_ollama opt-in integrated |
| training | Training report section | 5 | direct_ollama opt-in integrated |
| biggest_issue | Current issue summary | 1 | None |
| likely_cause | Possible contributing factor | 1 | None |
| priority_action | Highest-priority action | 1 | None |
| best_recommendation | Best recommendation summary | 1 | None |

## Provider-integrated report sections

Section maturity: `training`, `nutrition_report_section`.

Per-report persisted metadata lists `nutrition_report_section` only when approved Nutrition provider output actually rendered. Fallback or disabled-gate Nutrition reports remain explicit and do not imply provider approval.

## Important distinction

`nutrition_target_display` is not the final nutrition voice section. It can feed the future `nutrition_report_section`, but it should not become provider-owned by itself.

`nutrition_report_section` is now a Level 5 opt-in provider-integrated full-report section after accepted provider-approved seeded runtime QA and the explicit Nutrition Provider Level 5 Promotion v1 patch. This promotion does not make direct_ollama default, remove fallback, remove gates, or merge Nutrition Target Display into Nutrition Report Section.

## Next likely section path

Nutrition Provider Approved Suggestion Runtime QA v1 passed with `PASS_PROVIDER_APPROVED_MATRIX`: users 101-105 all provider-approved, safe_fallback_count 0, fail_count 0, and practical_food_focus_failure_count 0.

Nutrition Provider Level 5 Promotion v1 is implemented pending review. The next step is Nutrition Level 5 Promotion Runtime QA v1 to confirm provider-approved path semantics, fallback/disabled-gate metadata semantics, and public/persisted sanitizer boundaries.
