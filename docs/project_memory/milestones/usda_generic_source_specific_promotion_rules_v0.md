# USDA Generic Source-Specific Promotion Rules v0

Current source of truth: `main` at `929886d Merge USDA generic source-specific promotion rules v0`.

Feature implementation commit: `50d7e2b Add USDA source-specific promotion rules`.

Status:

```text
USDA_GENERIC_SOURCE_SPECIFIC_PROMOTION_RULES_V0_ACCEPTED_MERGED_AND_CLOSED
```

## Closeout

- Accepted merge: `929886d Merge USDA generic source-specific promotion rules v0`.
- Feature implementation: `50d7e2b Add USDA source-specific promotion rules`.
- Direct bulk-catalog tests: `110 passed`.
- Import and promotion safety slice: `131 passed`.
- Ruff check and format check passed.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; project-memory tests: `29 passed`.
- Foundation dry-run: `469` processed and `151` promoted.
- SR Legacy dry-run: `7,793` processed and `218` promoted.
- FNDDS dry-run: `5,432` processed, `0` promoted, `5,431` category skips, and `1` missing-macro skip.
- Combined dry-run: `13,694` processed and `348` promoted.
- All `151` Foundation-only identities remained promoted in the combined run.
- Reversed data-type order produced identical promoted identities and names.
- Final commercial, identity, metadata, malformed-name, and duplicate-word audits reported zero promoted defects.
- Raw records remained `13,694`; canonical foods, aliases, nutrients, and source links remained `0`.
- The real `fitness_ai.db` was not accessed or mutated, and no live promotion occurred.
- Final verdict: `READY_FOR_LIMITED_FOUNDATION_SR_PROMOTION_PLAN`.
- This milestone is accepted, merged, and closed. It does not authorize live canonical promotion.

## Delivered Policy

- Candidate-name families use fixed source precedence: `foundation_food`, then
  `sr_legacy_food`, then `survey_fndds_food`.
- Lower-priority candidates in an overlapping family are skipped with an explicit
  precedence reason. Promotion caps apply only after precedence and duplicate
  resolution.
- Foundation retains the existing category, macro, invalid-source, and raw
  meat/fowl/fish safety behavior.
- SR Legacy is limited to Fruits and Fruit Juices; Vegetables and Vegetable
  Products; Legumes and Legume Products; Cereal Grains and Pasta; Dairy and Egg
  Products; Nut and Seed Products; and Spices and Herbs. Caller category filters
  may narrow this policy but cannot broaden it.
- FNDDS remains deferred: macro-complete rows are category skips and the one
  source row without supported macros remains a missing-macro skip.
- SR Legacy commercial rejection is bounded to trademark symbols, explicit
  commercial/product-line signals including Bolthouse Farms, Daily Greens, Silk,
  Vitasoy, and Nasoya, repeated leading uppercase commercial tokens, and the USDA
  Food Distribution Program metadata phrase. Generic Foundation "commercially
  prepared" descriptions remain eligible.
- Same-name/same-macro families select one stable representative using source
  identity and description keys; remaining rows are duplicate-name skips.
- Same-name/different-macro families without targeted clean names are all
  duplicate-name skips. The generic second-comma-phrase fallback is removed.
- Foundation-specific display corrections cover red rice, braised chicken
  drumstick, cooked bacon, oatmeal raisin cookies, canned/dry chickpeas, and
  pumpkin/sunflower seed preparation variants, plus 33 recovered basic-food
  variants for dairy, juices, mangoes, plantains, legumes, produce, and canned
  tomatoes, plus a final bounded correction for peeled kiwifruit.
- SR Legacy meatless rows retain a clear `Meatless` qualifier for the approved
  meatless base names, and soy vermicelli retains its soy identity.

## Validation

- Direct bulk-catalog service and CLI test: `110 passed`.
- Import and promotion safety slice: `131 passed`.
- Ruff check and format check passed for
  `services/food_bulk_catalog_service.py`,
  `tests/test_food_bulk_catalog_service.py`, and
  `scripts/promote_canonical_food_bulk_catalog.py`.
- Official dry-runs used only a fresh external working copy of the validated
  13,694-row USDA catalog. No live canonical promotion occurred.

| Run | Processed | Promoted | Duplicate | Category | Invalid | Unsafe | Missing macros |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Foundation | 469 | 151 | 215 | 0 | 3 | 58 | 42 |
| SR Legacy | 7,793 | 218 | 1,794 | 5,521 | 260 | 0 | 0 |
| FNDDS | 5,432 | 0 | 0 | 5,431 | 0 | 0 | 1 |
| Combined | 13,694 | 348 | 2,030 | 10,952 | 263 | 58 | 43 |

- All 151 Foundation-only promoted source IDs remain promoted in the combined
  run; no promoted SR Legacy name overlaps a promoted Foundation name.
- Reversing the combined data-type argument order produces identical promoted
  identities and names.
- All 33 Foundation rows previously lost when generic second-phrase fallback was
  removed are promoted with bounded approved names. Foundation reaches 151
  candidates while retaining the no-generic-fallback policy. The general
  `Kiwifruit` and `Peeled kiwifruit` rows coexist; no promoted name is
  `Kiwifruit Kiwi`.
- The final quality audit found zero promoted Bolthouse/Daily Greens rows, zero
  promoted Silk/Vitasoy/Nasoya rows, zero promoted meatless rows without
  `Meatless`, zero promoted USDA distribution metadata rows, zero promoted
  `Kiwifruit Kiwi` names, and zero adjacent duplicate-word names. The Bolthouse
  Daily Greens SR row is a `skipped_invalid` row.
- Application-table counts remain raw `13,694`; canonical foods, aliases,
  canonical nutrients, and source links `0`. Working-copy SQLite hashes changed
  across CLI invocations, but application table counts and schema remained
  unchanged. The retained source database and real `fitness_ai.db` were not
  touched.

## Retained Evidence

- Working database:
  `C:\projects\fitness_ai_external\usda_generic_source_specific_rules_2026-07-13\working\usda_generic_source_specific_rules_v0.db`
- Reports:
  `C:\projects\fitness_ai_external\usda_generic_source_specific_rules_2026-07-13\reports\`
- Final-corrections summary verdict:
  `READY_FOR_LIMITED_FOUNDATION_SR_PROMOTION_PLAN`.

## Remaining Limitation

These rules are dry-run evidence only. They are not approved for live canonical
promotion, do not select final source precedence beyond this policy, and defer
FNDDS prepared-food promotion to a separate milestone.
