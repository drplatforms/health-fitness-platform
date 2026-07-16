# Barcode Scanning v1

Last updated: 2026-07-16

Status: implementation complete pending Architecture review and user-owned feature-branch production smoke.

## Purpose

Add barcode acquisition to the existing canonical food workflow:

```text
scan, photo, or manual barcode
→ local canonical/raw resolution
→ USDA Branded exact-GTIN lookup
→ Open Food Facts exact-barcode fallback
→ user confirmation
→ barcode-safe canonical materialization
→ existing serving-unit and canonical logging flow
```

## Backend implementation

- Consumer barcode normalization supports UPC-A, UPC-E, EAN-8, EAN-13, and GTIN-14 with check-digit validation and canonical GTIN-14 identity.
- Local lookup checks equivalent raw-source barcode identities before any provider request.
- One linked active canonical owner resolves immediately; one complete unlinked raw record returns a confirmation candidate; multiple canonical owners return conflict.
- USDA FoodData Central searches Branded data, accepts only an exact normalized `gtinUpc`, and fetches full detail before deterministic macro extraction.
- Open Food Facts uses direct product-by-barcode lookup only after the USDA path has no usable result.
- `FDC_API_KEY` and `OPEN_FOOD_FACTS_USER_AGENT` remain server-side and are documented in `.env.example` without real credentials.
- Exact external results are cached in `raw_food_source_records`; cache persistence does not create canonical foods.
- Confirmation re-reads the raw source record and revalidates expected GTIN, completeness, and current barcode ownership.
- Barcode materialization does not use generic name-based raw-source promotion. Same-name products receive distinct collision-safe canonical identities.
- The four required macros use direct-source canonical nutrient rows.
- A source-backed serving unit is created only for a positive gram serving; volume-only and missing servings retain grams fallback.
- Resolve and materialize routes return bounded public-safe responses without raw provider payloads or provider credentials.

## Frontend implementation

- The existing Food Logging search row now includes a compact `Scan` action.
- The scanner dialog supports user-started rear-facing live camera capture, local barcode-photo decoding, and manual numeric entry.
- Scanner decoding is restricted to UPC-A, UPC-E, EAN-8, EAN-13, and 14-digit ITF/GTIN.
- Camera streams stop on a valid decode, dialog close, cancellation, and component unmount.
- Camera failure or denial leaves photo and manual fallbacks available.
- External/local-raw candidates show product, brand, source, per-100g macros, and trustworthy gram serving details before confirmation.
- Confirmed or already-local canonical foods are selected directly in the existing amount/unit/meal logging transaction.
- Not-found, incomplete, conflict, invalid, provider-unavailable, and generic error states provide bounded fallback actions to scan again, enter manually, search foods, or create a personal food.

## Persistence and scope

- No schema migration or barcode-specific persistence table was added.
- Existing `raw_food_source_records`, `food_source_links`, canonical nutrient tables, and canonical serving-unit infrastructure remain authoritative.
- No AI, OCR, label-image interpretation, product-image recognition, external writes, bulk import, HTTPS infrastructure, or separate food-log subsystem was added.
- Automated work uses isolated pytest databases and does not mutate canonical `fitness_ai.db`.

## Validation evidence

- Barcode service/provider/API slice: 24 passed.
- Barcode plus canonical logging/serving/promotion slice: 82 passed.
- Canonical search, recents, edit/delete serving units, Today target-vs-actual, and personal-food regression slice: 164 passed.
- Lightweight frontend barcode helper tests: 3 passed.
- Touched Python Ruff check: passed.
- Touched Python Ruff format-check: passed.
- Frontend lint: passed.
- Frontend production build: passed, including both barcode proxy routes.

Production browser smoke, project-memory validation, final database hash comparison, temporary-artifact audit, and final diff/status audit are recorded in the implementation handoff rather than as Architecture acceptance.

## User-smoke modal correction

- `BarcodeScannerDialog` renders through a React portal into `document.body` so its backdrop and panel share one application-level stacking context above page cards, sticky surfaces, and the fixed mobile navigation.
- The modal root owns a fixed dynamic-viewport layer at `z-[100]`; unrelated page and navigation z-index values remain unchanged.
- The panel is constrained to the dynamic viewport, scrolls internally when required, and preserves bottom safe-area padding.
- While open, the modal locks body scrolling and restores the previous body overflow value on close or unmount.
- Targeted production smoke passed at `390x844`, `360x800`, and `1440x900` in explicit Light and Dark themes. Camera, photo, manual, candidate-confirmation, and error/fallback actions remained reachable; closing restored normal mobile navigation and desktop My Foods interaction.
- Database safety is not green for this correction: the smoke launcher supplied `NEXT_PUBLIC_API_BASE_URL`, while the server proxy reads `FITNESS_API_BASE_URL`, so the confirmation request reached the already-running canonical backend on port `8000`. The read-only audit identified raw source record `473`, canonical food `1141`, nutrient rows `4450`-`4453`, serving-unit row `727`, and source-link row `116` as the resulting writes. No cleanup was attempted without explicit user authorization.
- No Architecture acceptance state was written by this correction.
