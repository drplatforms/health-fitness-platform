# USDA Generic Canonical Promotion Diagnostic v0

Accepted diagnostic base: `main` at `53703aa Close USDA generic full dataset validation memory`.

Status:

```text
USDA_GENERIC_CANONICAL_PROMOTION_DIAGNOSTIC_V0_ACCEPTED_AND_CLOSED
```

## Purpose

Measure the behavior and safety of the existing deterministic canonical bulk-promotion rules against the complete validated generic USDA catalog before changing promotion policy.

## Classification

| Source | Processed | Promotable | Duplicate name | Category | Unsafe raw | Missing macros | Invalid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Foundation | 469 | 138 | 231 | 0 | 58 | 42 | 0 |
| SR Legacy | 7,793 | 670 | 4,681 | 1,274 | 1,166 | 0 | 2 |
| FNDDS | 5,432 | 0 | 0 | 5,431 | 0 | 1 | 0 |
| Combined | 13,694 | 691 | 5,029 | 6,705 | 1,224 | 43 | 2 |

The combined promotable set contained `57` Foundation rows and `634` SR Legacy rows.

## Candidate-Family Evidence

- Candidate-name families: `2,534`.
- Multi-source families: `356`.
- Foundation/SR Legacy overlaps: `144`.
- Foundation/FNDDS overlaps: `124`.
- SR Legacy/FNDDS overlaps: `300`.
- Families represented by all three sources: `106`.
- Same-name families with different macro profiles: `933`.
- Same-name families with identical macro profiles: `49`.
- Families with at least five source rows: `411`.
- Suspicious or over-generic display-name flags: `652`.

The suspicious-name count is a review queue, not an automatic rejection total, because legitimate one-token foods are intentionally included in the audit.

## Architecture Findings

- Combined processing lacks explicit source precedence.
- Lower-priority SR Legacy rows can displace valid Foundation candidates.
- Generic second-phrase renaming can create malformed display names.
- Commercial and restaurant product descriptions appear among current SR Legacy candidates.
- Broad names such as `Beef`, `Fish`, `Chicken`, `Pork`, `Rice`, and `2% milk` collapse materially different foods and macro profiles.
- FNDDS requires a separate mixed-dish and prepared-food strategy rather than reuse of Foundation and SR Legacy category rules.

## Approved Next Direction

1. Apply source precedence: Foundation, then SR Legacy, then FNDDS.
2. Preserve valid Foundation candidates ahead of overlapping SR Legacy rows.
3. Add targeted Foundation display-name corrections for proven low-quality names.
4. Restrict initial SR Legacy eligibility to conservative basic-food categories.
5. Reject commercial or manufacturer-style SR Legacy rows.
6. Keep FNDDS disabled for canonical promotion pending a prepared-food strategy.
7. Select one deterministic representative for identical same-name and same-macro duplicates.
8. Require clean, unique names for same-name and different-macro variants.
9. Keep the source-specific promotion-rules milestone dry-run only.

## Mutation Safety

- Raw-food count remained `13,694`.
- Canonical foods remained `0`.
- Canonical aliases remained `0`.
- Canonical nutrients remained `0`.
- Canonical source links remained `0`.
- The retained source database was not modified.
- The working-copy application schema and table counts remained unchanged.
- The repository remained clean at `main` commit `53703aa`.

## Retained Evidence

- Working database: `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\working\usda_generic_promotion_diagnostic_v0.db`.
- JSON report: `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_canonical_promotion_diagnostic_v0.json`.
- Markdown summary: `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_canonical_promotion_diagnostic_v0.md`.
- Candidate families: `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_candidate_name_families.csv`.
- Category matrix: `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_category_matrix.csv`.
- Review samples: `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_review_samples.csv`.

## Verdict

```text
READY_FOR_SOURCE_SPECIFIC_PROMOTION_RULE_DESIGN
```
