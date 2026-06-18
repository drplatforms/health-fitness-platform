# Section Registry Summary

Last updated: 2026-06-18

## Current full-report sections

| Section id | Display purpose | Current maturity | Provider status |
|---|---|---:|---|
| overall_score | High-level score/status | 1 | None |
| profile_context | User profile and context | 1 | None |
| grounded_recommendation | Approved action-plan recommendation | 3 | Not provider-owned |
| nutrition_target_display | Backend-approved target display | 2 | None |
| nutrition_report_section | Backend-owned nutrition evidence/claims/fallback boundary plus isolated opt-in provider implementation, full-report opt-in integration, accepted diagnostic visibility, and provider-approved seeded matrix after approved-suggestion context tuning | 4 | Ready for Level 5 promotion patch review; not promoted yet |
| training | Training report section | 5 | direct_ollama opt-in integrated |
| biggest_issue | Current issue summary | 1 | None |
| likely_cause | Possible contributing factor | 1 | None |
| priority_action | Highest-priority action | 1 | None |
| best_recommendation | Best recommendation summary | 1 | None |

## Provider-integrated report sections

`training` only.

## Important distinction

`nutrition_target_display` is not the final nutrition voice section. It can feed the future `nutrition_report_section`, but it should not become provider-owned by itself.

`nutrition_report_section` has a proven isolated opt-in provider path, an implemented full-report opt-in integration gate, accepted diagnostic visibility, practical_food_focus no-suggestion and approved-suggestion runtime fixes, and a provider-approved seeded runtime matrix. It is not Level 5 until a separate Nutrition Provider Level 5 Promotion v1 patch is implemented, validated, and accepted.

## Next likely section path

Nutrition Provider Approved Suggestion Runtime QA v1 passed with `PASS_PROVIDER_APPROVED_MATRIX`: users 101-105 all provider-approved, safe_fallback_count 0, fail_count 0, and practical_food_focus_failure_count 0.

The next step is Nutrition Provider Level 5 Promotion Readiness Review v1, followed by a separate Nutrition Provider Level 5 Promotion v1 patch if Architecture accepts readiness. Level 5 promotion should preserve deterministic fallback, provider gates, public/persisted sanitizer boundaries, and the distinction between Nutrition Target Display and Nutrition Report Section.
