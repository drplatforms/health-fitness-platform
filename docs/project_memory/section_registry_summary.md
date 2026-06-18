# Section Registry Summary

Last updated: 2026-06-18

## Current full-report sections

| Section id | Display purpose | Current maturity | Provider status |
|---|---|---:|---|
| overall_score | High-level score/status | 1 | None |
| profile_context | User profile and context | 1 | None |
| grounded_recommendation | Approved action-plan recommendation | 3 | Not provider-owned |
| nutrition_target_display | Backend-approved target display | 2 | None |
| nutrition_report_section | Backend-owned nutrition evidence/claims/fallback boundary plus isolated opt-in provider implementation and accepted section-only runtime QA | 4 | Not full-report integrated |
| training | Training report section | 5 | direct_ollama opt-in integrated |
| biggest_issue | Current issue summary | 1 | None |
| likely_cause | Possible contributing factor | 1 | None |
| priority_action | Highest-priority action | 1 | None |
| best_recommendation | Best recommendation summary | 1 | None |

## Provider-integrated report sections

`training` only.

## Important distinction

`nutrition_target_display` is not the final nutrition voice section. It can feed the future `nutrition_report_section`, but it should not become provider-owned by itself.

`nutrition_report_section` has a proven isolated opt-in provider path, but it is not full-report provider-integrated yet and must not be treated as Level 5.

## Next likely section path

Nutrition Full Report Opt-In Integration Design Review v1 should define how the proven section-only Nutrition provider path can later enter async full-report composition behind explicit gates.

A future implementation may move Nutrition toward full-report runtime QA, but Level 5 requires later Architecture approval after runtime QA, persisted-history inspection, composition fallback checks, and raw/debug leakage checks.
