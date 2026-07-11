# USDA Generic Full-Dataset Validation v0

Latest accepted application source of truth remains `main` at `e229600 Close USDA generic source expansion memory`.

Validation implementation branch: `feature/usda-generic-full-dataset-validation-v0`.

Status:

```text
USDA_GENERIC_FULL_DATASET_VALIDATION_V0_BLOCKED_BY_IMPORT_COMPATIBILITY
```

## Purpose

Validate the accepted generic raw USDA importer against the current official Foundation Foods, SR Legacy, and Survey Foods (FNDDS) CSV releases. This is a validation milestone only: no canonical promotion or product behavior change is authorized.

## Completed External Validation

- Repository preflight passed on clean `main` at `e229600`; the validation branch was created from that commit.
- C: free space was `799408336896` bytes, above the required 5 GB threshold.
- Downloaded, SHA256-verified, ZIP-validated, and extracted the three official non-branded CSV archives into `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10`.
- Required `food.csv`, `food_nutrient.csv`, and `nutrient.csv` headers are compatible in all three releases.
- Foundation Foods and SR Legacy `food_category.csv` headers are compatible with the accepted importer.

## Compatibility Blocker

The FNDDS archive `FoodData_Central_survey_food_csv_2024-10-31.zip` contains `wweia_food_category.csv` with:

```text
wweia_food_category,wweia_food_category_description
```

The accepted importer and inventory path require:

```text
wweia_food_category_code,wweia_food_category_description
```

The current importer validates `wweia_food_category_code` before FNDDS persistence and preserves it in the payload. The official release therefore cannot complete the accepted FNDDS import contract without a separate narrow compatibility-fix milestone.

Per the milestone stop rule, no source inventory, 25-row import preflight, full import, integrity check, idempotency rerun, or browser smoke was attempted after this finding. No application code was patched.

## Official Archives

| Release | Archive | Bytes | SHA256 |
| --- | --- | ---: | --- |
| Foundation Foods, 2026-04-30 | `FoodData_Central_foundation_food_csv_2026-04-30.zip` | 3825517 | `D6D4F41DCD19A46ABCDD67775379CB6F0292FF08DAA7E0680FDD0982830BF57B` |
| SR Legacy, 2018-04 | `FoodData_Central_sr_legacy_food_csv_2018-04.zip` | 6074592 | `B80817294B8850530AAEDF2E515C02593B1824F763A0FF356E5C2081643E6FD0` |
| Survey Foods (FNDDS), 2024-10-31 | `FoodData_Central_survey_food_csv_2024-10-31.zip` | 3325692 | `5CCC25EC2777A8982FBB61378A42F415316173EB11E48C9A8BA4CB19F5A4F29C` |

## Retained External Assets

- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\archives`
- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\extracted`
- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\reports\usda_generic_full_dataset_validation_v0.md`
- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\reports\usda_generic_full_dataset_validation_v0.json`

No scratch import database, browser-smoke database, launcher, process log, or repository artifact was created. The real `fitness_ai.db` was not read or mutated. Nothing was staged, committed, pushed, merged, or snapshotted.

Project-memory validation after recording this blocker completed with `590 PASS`, `58 WARN`, and `0 FAIL`; checker tests passed with `29 passed`.
