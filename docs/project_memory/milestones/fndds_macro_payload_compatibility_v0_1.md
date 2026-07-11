# FNDDS Macro and Payload Compatibility v0.1

Current source of truth: `main` at `21f5655 Merge FNDDS macro and payload compatibility v0.1`.

Feature implementation commit: `9b93a4a Support FNDDS macro identifiers and payload provenance`.

Status:

```text
FNDDS_MACRO_PAYLOAD_COMPATIBILITY_V0_1_ACCEPTED_MERGED_AND_CLOSED
```

## Closeout

- Accepted merge: `21f5655 Merge FNDDS macro and payload compatibility v0.1`.
- Feature implementation: `9b93a4a Support FNDDS macro identifiers and payload provenance`.
- Focused importer tests: `48 passed`.
- Importer and bulk-catalog regression: `76 passed`.
- Import and promotion safety regression: `49 passed`.
- Ruff checks passed.
- Merged-main production browser smoke passed.
- Official full FNDDS import inserted `5,432` rows and reran as `0` inserts plus `5,432` updates.
- Canonical foods and canonical source links remained unchanged.
- The real `fitness_ai.db` was not read or mutated.
- Milestone is accepted, merged, and closed.

## Purpose

Restore compatibility with the nutrient identifier convention used by the current official FNDDS release and retain resolved WWEIA category descriptions in raw source provenance.

## Implemented Scope

- Supported macro definitions register both their stable `nutrient.id` value and optional legacy `nutrient.nutrient_nbr` value.
- `food_nutrient.nutrient_id` can therefore resolve either supported identifier convention.
- Identifier collisions that would map one number to different macro keys fail clearly.
- Missing or blank optional nutrient numbers remain allowed.
- Missing source macros remain null and zero values remain zero.
- FNDDS raw payloads preserve `wweia_food_category_description`.
- The payload description matches the persisted resolved category.
- The input alias `wweia_food_category` is not emitted in raw payloads.

## Official Full FNDDS Validation

- Reused the retained October 2024 official FNDDS release outside the repository.
- First pass processed `5,432` rows, inserted `5,432`, and updated `0`.
- Rerun processed `5,432` rows, inserted `0`, and updated `5,432`.
- `5,431` rows had all four supported macros.
- One row had no supported macro values and remained unmodified without fabricated nutrition.
- All `5,432` rows preserved food code, WWEIA number, stable WWEIA code, and WWEIA category description.
- All payload descriptions matched the persisted resolved food category.
- No payload exposed the input-only `wweia_food_category` alias.
- No duplicate raw identities, negative macros, canonical foods, or canonical source links were produced.

## Validation

- Focused importer tests: `48 passed`.
- Importer and bulk-catalog regression: `76 passed`.
- Import and promotion safety regression: `49 passed`.
- Ruff check and touched-file format checks passed.
- Merged-main production browser smoke passed for Today, Nutrition, canonical food search, Workout, zero console errors, and no horizontal overflow around 390px.

## Boundaries

- No schema, migration, inventory, canonical-promotion, canonical-search, food-logging, frontend, dependency, workout, provider, or AI change was made.
- Only `services/usda_food_data_import_service.py` and `tests/test_usda_food_data_import.py` changed in the implementation commit.
- The implementation was committed as `9b93a4a` and merged to `main` as `21f5655`.
