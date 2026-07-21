# Close the Gap Suggestions v2

## Status

- Architecture authorization: explicit user authorization in the Codex task dated 2026-07-20.
- Implementation status: accepted after final user smoke testing on 2026-07-21; authorized for exact milestone staging, feature-branch commit, and feature-branch push.
- Base: `main` at `46cf092` (`Merge exercise guidance during workout v1`).
- The user explicitly authorized staging the exact milestone files, committing them on the current feature branch, and pushing that feature branch. Merge to `main`, schema migration, dependency changes, and provider changes remain unauthorized.

## Product outcome

Close the Gap remains a deterministic, backend-approved food-suggestion and exact-quantity quick-log flow. Suggestions now choose among finite practical portions, account for every approved calorie and macro comparison that is actually available, evolve as normalized remaining-gap pressure changes, and avoid allowing concentrated powder-form foods to dominate ordinary foods merely through nutrient density. The existing Food UI card is also rendered on the desktop Today food workspace as well as the mobile Food route.

Daily nutrition presentation now keeps incomplete-data status outside the numeric subtotal, displays the backend-approved target ranges instead of midpoint stand-ins, and keeps Close the Gap visible with a concise integrity explanation when incomplete nutrient data prevents trustworthy suggestions. Logged today, Nutrition, and Close the Gap now independently refetch current backend truth from the same food-log event with latest-request-wins protection.

## Previous behavior

- Candidate grams were calculated by scaling each food to mathematically close the addressed nutrient gap, then clamping that result to broad role-specific bounds.
- Protein ranking primarily rewarded protein density and closeness to a 150 g quantity. It did not consistently evaluate the candidate against the other approved remaining calorie and macro comparisons.
- A branded item such as `COLLAGEN PEPTIDES + PROBIOTICS` could therefore receive an approximately 140 g portion: the exact protein-gap calculation happened to fall inside the generic protein bounds.
- Macro-role round-robin and canonical-food deduplication existed, but close variants within a role could still crowd the result.
- Static curated preference bonuses and a fixed protein/carbohydrate/calorie/fat role order outweighed the relatively small remaining-context adjustment. Changing nutrition state therefore changed gram quantities much more often than food identities.
- Recent usage could add a familiarity bonus, but same-day consumption was not measured. Frequently logged foods could remain permanently favored even after being consumed heavily that day.
- The shared Close the Gap card and quick-log flow were present on the mobile Food route but were not rendered in the desktop Today Food experience.
- Daily nutrition summed each nutrient independently, but the UI presented a known calorie subtotal as complete when some logged foods had macros and no calorie value. The same incomplete state correctly blocked calorie and macro comparisons, causing Close the Gap to disappear without explaining why.
- The Today UI rendered each approved target range as a single midpoint, making in-range values appear over or under a singular target that the backend did not use.
- The first state-sensitive correction still applied rotation and diversity only inside 8-point and 12-point leader-relative windows. In reproduced states those windows often contained one or only a few curated candidates, so broad eligible pools still behaved like static per-role leaderboards.
- Logged today already performed a direct client refetch after each food-log event. Nutrition instead issued an unsequenced `router.refresh()`, so rapid consecutive logs could leave the first refresh result visible, and Close the Gap did not listen for external food logs at all. Its same-user/date local state also retained the original response even after Logged today advanced.

## Authorized implementation

### Portion evidence and bounds

Portions are no longer generated from exact gap closure. Each candidate evaluates a finite option set in this order:

1. Existing active serving-unit metadata with `Moderate` or `High` confidence, using only 0.5x, 1x, 1.5x, and 2x multiples that remain inside the role's practical upper bound.
2. If no reliable serving unit exists, the user's most recent logged gram quantity for that canonical food through the suggestion date, using the same bounded multiples when they remain practical.
3. If neither reference is usable, a small deterministic set sampled from the existing curated or catalog-fallback role bounds.

Low-confidence or missing serving metadata is not treated as a portion fact. A food may meaningfully improve a gap without closing it. Distance from a 1x metadata/history reference is penalized, and no option is scaled indefinitely.

### Remaining-context ranking

- Portion scoring still rewards meaningful improvement to the addressed gap, but exact closure is only a bounded score input rather than the portion generator.
- Every other approved/displayable calorie or macro comparison is evaluated at the proposed quantity.
- A portion receives a small benefit when it also fits another remaining gap, is penalized for a substantial conflict, and is rejected for a severe conflict.
- Unavailable or unapproved targets are skipped. The guardrails are single-suggestion conflict limits and do not manufacture daily targets.

### State-sensitive candidate selection

- Approved remaining gaps are converted to normalized pressure (`remaining / target`). Macro roles are ordered by that pressure, and roles below a 12% actionable threshold stop generating suggestions. This makes resolved or token gaps fall out instead of occupying permanent roster slots.
- The addressed-gap contribution and compatible improvement to other approved gaps now outweigh the static catalog/curated score. Static preference remains only as a bounded quality prior and deterministic tie-break input.
- Candidate selection uses nutrition profiles derived only from the candidate's existing protein, carbohydrate, fat, calorie, and gram data. Candidates must now clear fixed state-relative contribution and absolute quality floors rather than remain within a fixed distance of the current leader.
- State-fit tiers are derived from the candidate portion's contribution to the current approved remaining gap, including bounded overshoot treatment and the existing cross-macro context result. Fixed absolute quality tiers preserve nutritional usefulness; catalog-fallback candidates must clear stronger role-specific floors because they lack curated serving-quality evidence.
- A state/date/user-derived stable hash rotates candidates inside fixed state-fit and quality tiers. The result is deterministic for the same state, while materially changed state changes tier membership and ordering without promoting candidates that fail the hard floors.
- Existing canonical log history still supplies a small familiarity signal and an evidence-backed quantity reference. Same-day logged grams now add a repetition penalty, and foods already consumed at least two minimum practical portions today are excluded for that role.

### Concentrated forms and variety

- Existing food display-name data is used to detect a small generic set of concentrated-form terms (`isolate`, `peptide`, `peptides`, and `powder`). No health, supplement, or nutrition classification is inferred.
- Such non-curated foods reuse the existing whey-powder portion range and receive a strong ranking penalty. A reliable stored serving unit may still provide the candidate portion, but concentrated forms do not outrank ordinary food solely through nutrient density.
- Existing macro-role diversity and canonical deduplication remain. Within a role, selection now combines normalized food-name distinction with the nutrition-profile diversity described above.
- Recent log quantity and a small bounded usage bonus are used only when the data exists; suggestions do not require personalization.
- A food's tightest existing curated maximum is respected across every role in which it is evaluated, preventing a food with a known small practical range from inheriting a much larger calorie-fallback range. Foods at or above 350 kcal per 100 g also receive a general 300 kcal single-suggestion ceiling, and unanchored catalog portions are penalized as they scale above their minimum practical bound.

### Desktop parity and quick log

- The desktop Today page now requests the same approved suggestion payload and renders the same `NutritionGapActionsCard` used by the mobile Food page, following the existing responsive card pattern.
- The existing exact-gram quick-log component and API contract are unchanged.
- After a successful quick-log, the card now refreshes its approved suggestion payload through a same-origin frontend proxy. The newly relevant roster appears immediately while a refresh failure cannot undo or block the successful food log.
- Canonical and personal food-log events now trigger latest-request-wins client refetches for Nutrition and Close the Gap, matching the existing Logged today sequencing. Nutrition uses a narrow same-origin Today proxy so displayed totals continue to come from the backend rather than being recalculated in the browser.

### Incomplete totals and target ranges

- Foods with incomplete nutrient data remain loggable, and missing calories or macros remain missing. No calorie value is derived from macros or otherwise fabricated.
- The daily-driver nutrition contract now exposes the approved minimum and maximum for each target plus a per-nutrient completeness flag for the known logged subtotal.
- The shared nutrition card renders the known numeric subtotal normally and lists any affected nutrients in a separate compact `Incomplete totals: ...` message. It presents each approved target as a compact range on both Today and Food surfaces.
- If the backend returns no suggestions because incomplete logging removes all trustworthy actionable gaps, the shared Close the Gap card remains visible and explains that suggestions are paused until remaining nutrition can be calculated reliably.

## Data limitations

- Serving-unit coverage is partial, and reliability is represented only by the existing Low/Moderate/High confidence field. Many catalog and barcode foods therefore fall back to recent-history or bounded role options.
- Existing food data has no general meal-role, food-group, supplement, or preparation-suitability taxonomy. Concentrated-form deprioritization is deliberately limited to terms already present in display names; it does not make unsupported nutrition claims.
- Canonical and source food records can contain macros without calories or can be incomplete for another individual nutrient. The UI can now represent the resulting known subtotal honestly, but recommendation context remains limited until the source nutrient is corrected or a complete food record is used.
- Log-history reuse is limited to canonical food IDs and logged gram quantities. Non-canonical entries and household-unit preferences cannot provide a deterministic portion anchor or same-day repetition signal here.
- Nutrition-profile variety is inferred only from the existing numeric nutrient data. Richer meal-role, culinary, ingredient, or food-group diversity would require stronger food metadata and is outside this milestone.

## Validation

- Focused suggestion, API/model, target-vs-actual, daily-driver service/contract/route, serving-unit, and food-recents slice: `177 passed`.
- Exact disposable replay of the reported 2026-07-21 states at 4, 6, 7, 9, 11, 12, 13, 14, and 15 entries produced `27` distinct foods across the seven actionable states, compared with `17` before this correction. The roster changed at every checkpoint; no food appeared in all seven actionable states.
- The replay preserved the integrity boundary: once incomplete oats removed all trustworthy actionable gaps at checkpoints 14 and 15, suggestions remained empty with `logging_incomplete_limits_suggestions` rather than being forced through.
- Ruff check and format check for touched Python files: passed.
- Frontend lint and production build (41 routes): passed.
- Focused live-data investigation confirmed Dustin's 2026-07-21 Egg and Cottage Cheese snapshots were both complete. Current backend truth was `388 kcal / 40g protein / 8g carbs / 22g fat` with a populated suggestion set while the reported client had retained the egg-only Nutrition response and paused Close the Gap response.
- Production browser smoke reproduced rapid `Egg, Large — 150g` then `Cottage Cheese — 163g` logging against a disposable database. Logged today advanced to two items, Nutrition advanced from `214 / 19 / 1 / 14` to `388 / 40 / 8 / 22`, and Close the Gap refreshed from the prior set to a `Cod, Cooked` lead without reloading the page.
- Separate incomplete-data smoke rendered `388 kcal` rather than `At least 388 kcal`, with `Incomplete totals: Calories.` outside the number. Desktop Today and 390 x 844 mobile Food had no horizontal overflow or console warnings/errors.
- At the complete 11-entry checkpoint, mobile quick-log persisted exactly `200g` Shrimp to the disposable database and immediately refreshed the lead suggestion to `Black Beans, Cooked`.
- Canonical `fitness_ai.db` was read only for the replay/smoke source copy. Automated validation and browser mutation used disposable databases only, and all temporary artifacts were removed.

## Acceptance and closeout boundary

Architecture acceptance was granted after final user smoke testing. The exact milestone files may be committed and pushed on the current feature branch. Merge to `main` and canonical current-truth advancement remain separate, unauthorized actions and are not part of this closeout. No unresolved product choice is known from the implementation; future taxonomy or richer serving metadata would be a separate product/data milestone.
