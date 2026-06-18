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

`nutrition_report_section` has a proven isolated opt-in provider path and an implemented full-report opt-in integration gate, but it is not Level 5 until runtime QA, persisted-history inspection, leakage checks, and Architecture approval pass.

## Next likely section path

Nutrition Full Report Opt-In Integration v1 has implemented the first gated full-report integration step.

The next step is Nutrition Full Report Opt-In Runtime QA v1. Level 5 still requires Architecture approval after runtime QA, persisted-history inspection, composition fallback checks, and raw/debug leakage checks.
