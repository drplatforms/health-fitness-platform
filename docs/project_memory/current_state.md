# Current State - Weekly Training Planner v1

Canonical implementation baseline before merge: main at 7685843.

Feature branch: feature/weekly-training-planner-v1.

Status: WEEKLY_TRAINING_PLANNER_V1_ARCHITECTURE_ACCEPTED

Accepted behavior:

- Users can create persistent Monday-through-Sunday weekly training plans with 1-6 scheduled training days.
- Weekly plans persist session structure and explicit rest days without freezing future detailed workout prescriptions.
- Exact daily workouts remain generated day-of using current recovery, constraints, equipment, exercise rotation, and existing deterministic workout generation.
- Supported deterministic split sequencing includes Full Body, Upper/Lower, and six-day Upper/Lower variants based on selected training frequency.
- Future untouched weekly schedule dates may be edited while past, selected, in-progress, and completed dates remain protected.
- Missed scheduled sessions are not automatically rescheduled.
- Rest days suppress the normal workout preview unless the user explicitly chooses Train Anyway.
- Preview variation preserves the scheduled session identity while allowing valid exercise rotation.
- Quick, Standard, and Extended workout sizing remain available.
- Existing persisted workouts retain precedence over weekly-plan context.
- Adaptive Progression, Previous Performance, Recovery Intelligence, and Smart Exercise Substitutions remain integrated with weekly-directed workouts.
- Mobile and desktop weekly planning UX, Today/Week navigation, responsive layouts, and Light/Dark themes passed production smoke.
- Required feature-branch automated validation and user acceptance smoke passed.

Known workflow safety incident:

- A full pytest run unexpectedly initialized the two intended weekly-training-plan tables in canonical fitness_ai.db.
- Both new tables were confirmed empty and existing user/workout data remained present.
- No destructive rollback was attempted without a known-good pre-run database copy.
- Future automated validation must continue using isolated database copies.

Known follow-up backlog:

- Hide Recent History when no meaningful historical evidence exists.
- Hide Next Target when progression status is insufficient_data rather than rendering generic placeholder guidance.
- Apply conditional workout intelligence display consistently on mobile and desktop.
- Replacement exercise equipment badges may retain original equipment metadata.
- Starting a workout may clear the visible substitution overlay.
- Richer longitudinal QA seed data remains recommended for workout, recovery, and nutrition scenarios.

Roadmap status:

Weekly Training Planner v1 is accepted.
A fresh Architecture chat should be onboarded from the post-merge canonical snapshot.
The broader roadmap should be deliberately reassessed in that new Architecture chat before authorizing the next major milestone.
No next product milestone is implementation-authorized yet.

---
# Current State - GitHub README and Project Presentation Refresh

Canonical baseline before refresh: main at df5abc8.

Documentation branch: docs/readme-refresh-v1.

Status: GITHUB_README_PROJECT_PRESENTATION_REFRESH_V1_ACCEPTED

Accepted outcome:

- The root README now reflects the current Health & Fitness Platform rather than the earlier AI Health Coach-era project state.
- Current nutrition, barcode scanning, saved meals, workout execution, exercise guidance, substitutions, adaptive progression, recovery intelligence, and mobile workspace capabilities are represented.
- The README explains the deterministic backend architecture, historical-correctness principles, external food-data integration, current technology stack, local setup, validation workflow, and active-development status.
- Public-facing language remains grounded and does not present the application as a finished commercial healthcare product or finished portfolio piece.

Roadmap status:

The GitHub README and project presentation refresh is complete.
Weekly Training Planner v1 is the next recommended major product milestone.
No next product milestone is implementation-authorized yet.

---
# Current State - Meal Builder v1

Canonical implementation baseline before merge: main at 5fa99e4.

Feature branch: feature/meal-builder-v1.

Status: MEAL_BUILDER_V1_ARCHITECTURE_ACCEPTED

Accepted behavior:

- Users can create, edit, reorder, archive, restore, and reuse saved meal templates.
- Saved meals are strictly user-owned.
- Meals may contain both canonical foods and user-owned personal foods.
- Saved meal items preserve stable resolved gram quantities while retaining serving provenance where useful.
- Future meal summaries and logs use current canonical nutrition truth and the current active personal-food revision.
- Historical food entries remain immutable snapshots and are not rewritten when a saved meal or personal food changes.
- Whole-meal logging is transactional and creates normal individual food entries for every component.
- Logged meal components immediately participate in existing Logged Foods, nutrition totals, recents, and individual edit/delete behavior.
- Saved meals support optional default meal types and explicit meal-type overrides.
- The dedicated Food workspace now includes Log Food, Meals, and My Foods workflows.
- Meal logging and editing were validated on mobile and desktop in production mode.
- Existing text food search, barcode scanning, personal foods, serving-unit logging, and logged-food workflows remain functional.
- Required feature-branch automated validation, isolated production smoke, and user acceptance smoke passed.

Architecture boundaries preserved:

- No parallel meal nutrition-total subsystem was introduced.
- No recipe yield, preparation, grocery-list, meal-planning, or AI meal-generation scope was added.
- No logged-meal grouping/history entity was added.

Near-term follow-up:

- Refresh the GitHub README and repository presentation so public-facing documentation reflects the current working system.
- Continue treating the application as an actively developed project rather than a finished portfolio product.
- Richer deterministic QA seed data remains recommended before future milestones that require broad scenario coverage.

Roadmap status:

Meal Builder v1 is accepted.
The immediate recommended follow-up is GitHub README and project presentation refresh.
Weekly Training Planner v1 remains the next recommended major product milestone after that documentation pass.
No next product milestone is implementation-authorized yet.

---
# Current State - Mobile Daily-Driver Navigation & Compaction v1

Canonical implementation baseline before merge: main at e56bd61.

Feature branch: feature/mobile-daily-driver-navigation-compaction-v1.

Status: MOBILE_DAILY_DRIVER_NAVIGATION_AND_COMPACTION_V1_ARCHITECTURE_ACCEPTED

Accepted behavior:

- Mobile Today, Food, Workout, and Recovery now behave as distinct primary workspaces.
- Mobile bottom navigation uses real pathname-based routing instead of hash-anchor scrolling.
- Live unpinned navigation remains unpinned while supported explicit-date navigation preserves the selected date.
- Mobile Today is an overview rather than a container for every full daily workflow.
- Mobile Today removes redundant Today and USER labels and avoids duplicating the selected username outside the user selector.
- Food now has a dedicated workspace with nutrition, search, barcode scanning, recent foods, logged foods, and My Foods access without Workout content bleeding below it.
- Recovery now has a dedicated workspace and preserves Recovery Check-In persistence and existing recovery intelligence behavior.
- Mobile Workout status and preview controls are substantially more compact, reducing time and scrolling before the first exercise.
- Exercise-level substitutions remain available while redundant header-level substitution summary content is removed.
- Exercise Actuals status semantics now reserve green for completed work, amber for remaining work, and a distinct subdued state for not-started work.
- Mobile workout visual hierarchy is flatter and Previous Performance plus Next Target are presented more compactly.
- Barcode scanning remains functional from the dedicated Food route, including trusted-HTTPS live camera access.
- Desktop behavior remains functional and retains the richer combined Today experience where appropriate.
- Required feature-branch automated validation, isolated production smoke, and real-device acceptance smoke passed.
- No backend, API, schema, or database behavior changes were introduced.

Product direction:

- The mobile bottom navigation now represents true primary workspaces and should remain the foundation for future daily-driver UX.
- Future mobile features should be added to the appropriate dedicated workspace rather than extending one long cross-workflow Today page.
- Continued UI refinement is expected, but this milestone is accepted as a major improvement to the daily mobile experience.

Near-term follow-up:

- Refresh the GitHub repository README and public project presentation so they accurately reflect the current working system.
- Continue updating the LinkedIn project description as active-project visibility rather than presenting the application as a finished portfolio product.
- Richer deterministic QA seed data remains a recommended enablement improvement before future milestones requiring broad workout, recovery, or nutrition scenario coverage.

Roadmap status:

Mobile Daily-Driver Navigation & Compaction v1 is accepted.
Meal Builder v1 remains the next recommended major product milestone.
No next product milestone is implementation-authorized yet.

---
# Current State - Barcode Scanning v1

Canonical implementation baseline before merge: main at d5bbbe4.

Feature branch: feature/barcode-scanning-v1.

Status: BARCODE_SCANNING_V1_ARCHITECTURE_ACCEPTED

Accepted behavior:

- Packaged foods can be resolved by UPC, EAN, or GTIN through a local-first barcode pipeline.
- Local linked canonical foods resolve immediately without remote provider lookup.
- Complete local raw-source records can be surfaced as confirmation candidates.
- Remote lookup uses USDA FoodData Central Branded Foods first with exact normalized GTIN matching.
- Open Food Facts is used as the external fallback when USDA has no usable exact match.
- External products require one explicit user confirmation before barcode-safe canonical materialization.
- Imported branded foods reuse the existing canonical serving and nutrition logging infrastructure.
- Same-name products with different barcode identities are protected from unsafe name-based merging or nutrient overwrite.
- Repeated scans of an already materialized barcode resolve locally.
- Live mobile barcode scanning was validated over trusted HTTPS using Nord Meshnet plus Caddy.
- Photo and manual barcode entry remain fallback paths.
- No schema migration or barcode-specific persistence table was introduced.
- Required feature-branch validation and real-device user smoke passed.

Runtime enablement:

- Private remote mobile access is available through Nord Meshnet.
- Caddy provides trusted private HTTPS for the Meshnet hostname and enables secure-context browser APIs such as live camera access.
- Caddy runtime configuration and private CA material remain outside the repository.
- FDC_API_KEY remains a private runtime secret and must never be committed.

Mobile daily-driver backlog:

- Mobile primary navigation should represent distinct Today, Food, Workout, and Recovery workspaces rather than one long cross-section page.
- Food should be isolated from workout content so food logging, logged entries, barcode scanning, and My Foods have dedicated working space.
- Today should remain its own overview surface and should remove redundant Today and USER labels and duplicate username display.
- Workout mobile UI should reduce nested-card depth and substantially compress or remove oversized Session Status/header surfaces.
- Workout header substitution summary should be removed; substitution belongs at the exercise level.
- Workout execution status colors should reserve green for completed work, use amber/yellow for remaining work, and use a distinct subdued not-started state.
- Recent History and Next Target need a more compact presentation as exercise intelligence grows.
- Recent Foods horizontal overflow and empty Logged Today states should receive a later mobile compaction pass.
- These findings are future product work and were not blockers for Barcode Scanning v1 acceptance.

Roadmap status:

Barcode Scanning v1 is accepted.
Meal Builder v1 remains the previously planned next major product milestone.
Mobile Daily-Driver Navigation & Compaction v1 is now a high-priority candidate milestone and should be considered before the next implementation authorization.
No next milestone is implementation-authorized yet.

---
# Current State - Adaptive Progression Engine v1

Canonical implementation baseline: main at edd32f8.

Feature branch: feature/adaptive-progression-engine-v1.

Status: ADAPTIVE_PROGRESSION_ENGINE_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Deterministic advisory progression decisions resolve each actionable current exercise to progress_reps, increase_load, hold, ease_back, or insufficient_data.
- Load progression requires two consecutive qualifying top-range sessions and never invents an exact next weight.
- Conservative ease-back requires two consecutive meaningful-underperformance sessions; one difficult session produces hold.
- Recovery Intelligence v2 acts only as a strong brake on upward progression when readiness is recovery_limited or fatigue support is limiting.
- Progression evidence uses historical planned rep/RIR truth, rejects incomplete latest evidence, and is substitution-aware for the exercise actually performed.
- The active Next.js workout shows compact Next Target guidance without mutating approved plans, logged-set defaults, or historical read-only workouts.
- Required feature-branch validation and acceptance smoke passed.
- No unauthorized scope expansion was introduced.

QA enablement note:

- Future workout, recovery, and nutrition milestones that depend on richer scenario coverage should consider expanding deterministic QA seed data and user fixtures before acceptance testing.

Roadmap status:

Adaptive Progression Engine v1 is accepted.
The next recommended milestone is Barcode Scanning v1.
Barcode Scanning v1 remains pending Architecture grounding and scoping and is not yet implementation-authorized.

---
# Daily Date Rollover Correctness v1 — Architecture Accepted

- Baseline: `d44a5e3`
- Branch: `feature/daily-date-rollover-correctness-v1`
- Status: `DAILY_DATE_ROLLOVER_CORRECTNESS_V1_ARCHITECTURE_ACCEPTED`

Accepted behavior:

- Date-less Today and Workout routes remain live and do not acquire an explicit `date=` through normal navigation.
- Explicitly dated routes remain pinned to the requested date.
- Live Today and Workout surfaces follow the browser-local calendar day.
- Live surfaces detect a local-day change and reload while preserving the unpinned live URL.
- Rollover is rechecked after browser focus and visibility return.
- Explicit historical workouts remain visible but are read-only.
- Historical unfinished workouts cannot be resumed or mutated after their calendar day has passed.
- Historical workout mutation, preview-generation, size, variation, set logging/edit/delete, substitution, and completion controls are suppressed.
- Historical dates with no persisted workout show a read-only empty state and do not generate a workout preview.
- An explicit date equal to the browser-local current day remains interactive.
- Historical food viewing remains unchanged.
- Existing backend workout daily-state behavior was preserved.
- No backend, API, schema, persistence, provider, workout-generation, progression, substitution, recovery, or nutrition-policy changes were required.
- Feature-branch production smoke passed on canonical ports `8000/3100`.
- Live and explicitly dated navigation behavior passed.
- Historical unfinished, completed, and empty workout states passed.
- Browser-local rollover simulation passed.
- Mobile approximately `390x844`, mobile approximately `360px`, desktop, Light, and Dark acceptance surfaces passed.
- No relevant console, hydration, warning, horizontal-overflow, or runtime regressions were observed.
- Automated validation used an isolated temporary database and the canonical `fitness_ai.db` remained unchanged.

Next recommended product milestone:

- `Exercise Explanations v1`
- Status: `NOT_IMPLEMENTATION_AUTHORIZED`
- Owner: Architecture
# Current State - Smart Exercise Substitutions v1

Canonical implementation baseline: main at f810424.

Feature branch: feature/smart-exercise-substitutions-v1.

Status: SMART_EXERCISE_SUBSTITUTIONS_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Upgraded the existing substitution candidate flow from a flat compatible list to deterministic ranked substitutions.
- Existing substitution eligibility remains conservative and unchanged; ranking operates only within candidates already valid by movement-pattern compatibility and current equipment compatibility.
- No new compatible movement-family mappings were introduced.
- Ranking considers movement-match quality, planned-muscle overlap, exercise-type preservation, recent exercise exposure, and a stable deterministic tie-break.
- Candidate responses identify one Best Match followed by Also Compatible options with deterministic user-facing explanations.
- Added the smallest practical Next.js request, review, and apply workflow inside the daily-driver workout experience.
- Substitution review remains inline and does not navigate away from or remount the active workout.
- Unsaved set-entry state, exercise focus, planned prescriptions, logged sets, and existing workout execution state are preserved through substitution review and application.
- Applied substitutions continue using the existing backend-owned substitution overlay rather than mutating the immutable ApprovedWorkoutPlan snapshot or original planned workout exercise rows.
- Replacement catalog identity drives the displayed replacement exercise and exercise instructions while preserving original planned-exercise attribution.
- The v1 UI suppresses selecting a new substitution after completed sets exist for that planned exercise, avoiding mixed original/replacement execution editing in this milestone.
- Existing set logging, editing, deletion, exercise navigation, completion review, substitution persistence, refresh behavior, and workout history behavior remain intact.
- Production browser smoke passed on the canonical application surfaces across mobile, narrow mobile, desktop, Light, and Dark themes.
- Required substitution keyboard interaction passed during production smoke.
- No relevant console, hydration, or horizontal-overflow regression was identified.
- Canonical fitness_ai.db remained unchanged during automated validation and production smoke.
- No schema, dependency, provider, recommendation, progression, or workout-generation behavior change was added.

Known follow-up:

- Daily date rollover is not correctly clearing date-scoped Today data when the calendar day changes.
- Previous-day Logged Today food entries can remain visible on the following day.
- A previous-day workout can remain presented as Today's Workout.
- A previous-day in-progress workout can remain surfaced as the current day's active workout.
- This is a separate daily date-scoping correctness issue and is not part of Smart Exercise Substitutions v1.

Roadmap status:

Smart Exercise Substitutions v1 is accepted.
The next recommended milestone is Daily Date Rollover Correctness v1.
That milestone should restore clean date-scoped daily state for food and workouts while preserving historical records.
The next milestone remains pending Architecture scoping and is not yet implementation-authorized.

---
# Current State - Projectmem Workflow Integration v1

Status: PROJECTMEM_WORKFLOW_INTEGRATION_V1_ARCHITECTURE_ACCEPTED

- Projectmem 0.2.0 is integrated as a supplemental local context accelerator.
- Canonical Architecture handoffs, AGENTS.md, docs/project_memory, and repository truth remain authoritative.
- .projectmem remains local and Git-ignored.
- Projectmem Git hooks and background watcher remain disabled.
- Codex MCP integration is configured and validated.
- Fresh-session onboarding probe passed in approximately 2m10s without a broad repository scan.
- The probe correctly recovered workflow authority, ownership, environment, database safety, UI acceptance rules, mobile product direction, and the next product milestone.
- Next product milestone: Smart Exercise Substitutions.

---
# Current State - Active Workout Mobile UX v1

Canonical implementation baseline: main at beeb2da.

Feature branch: feature/active-workout-mobile-ux-v1.

Status: ACTIVE_WORKOUT_MOBILE_UX_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Added mobile-only focused exercise execution keyed by planned exercise ID.
- Active mobile workouts initialize focus on the first incomplete exercise, or the final exercise when all exercises are complete.
- Exercise focus remains stable after set logging and advances only through explicit user action.
- Added a compact mobile exercise navigator with previous, next, direct exercise selection, completion state, and overall set progress.
- Mobile active execution shows one focused exercise at a time while non-focused exercise cards remain mounted and preserve unsaved form and instruction state.
- Added compact three-column Reps, Weight, and RIR mobile entry and edit layouts.
- Added prominent mobile Save Set placement after the entry fields.
- Preserved previous-performance context, inline exercise instructions, logged-set edit/delete behavior, and existing set defaults.
- Added explicit completed-exercise state and user-driven Next Exercise navigation.
- Compacted active mobile workout progress while preserving the full Execution Summary on desktop.
- Existing completion-review behavior remains accessible during active mobile execution.
- Desktop retains the full exercise grid and accepted instruction-focused behavior.
- Workout lifecycle, APIs, persistence, substitutions, history, and backend behavior were not changed.
- Production browser smoke passed at approximately 390x844, 360px narrow mobile, and desktop widths in Light and Dark themes.
- Unsaved set-entry values were verified to survive exercise switching and instruction expansion.
- Canonical database SHA-256 remained unchanged during validation.
- No dependency, backend, API, database, or schema change was added.

Known follow-up UX:

- After successfully logging food, the completed food remains selected in Food Logging even though macros and Logged Today update correctly; successful logging should reset the completed food-selection transaction while likely preserving Meal selection.
- Food and Recovery bottom-navigation highlighting does not track anchored Today sections.
- Recent Foods needs a denser presentation so it does not push Logged Today below an entire mobile viewport.
- My Foods needs a denser scalable catalog presentation for both mobile and desktop.

Mobile roadmap status:

Active Workout Mobile UX v1 is accepted.
The next recommended milestone is Mobile Food Logging and Recovery UX.
That milestone should include the known food-selection reset bug and the mobile food-density improvements where appropriate.
The next milestone remains pending Architecture scoping and is not yet implementation-authorized.

---
# Current State - Mobile UX Foundation v1

Canonical implementation baseline: main at ac5b731.

Feature branch: feature/mobile-ux-foundation-v1.

Status: MOBILE_UX_FOUNDATION_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Added a reusable fixed, safe-area-aware mobile primary navigation for Today, Food, Workout, and Recovery.
- Mobile navigation preserves user_id and date context across routes and anchored Today sections.
- Added stable Food workspace and Recovery section anchors on Today.
- Compacted the Today mobile header, shared Today cards, Nutrition summary, user control, and theme control.
- Added a compact narrow-screen Food workspace selector while preserving tap, swipe, and keyboard behavior.
- Compacted mobile route shells for Workout and Personal Foods.
- Desktop layouts and accepted Light, Dark, and System theme behavior are intentionally preserved.
- Active workout execution, Food Logging workflow internals, Recovery workflow internals, and Personal Food form internals were not redesigned.
- Production browser smoke passed at approximately 390x844, 360px narrow mobile, and desktop widths.
- No relevant console errors, warnings, hydration issues, horizontal overflow, or bottom-navigation content obstruction were observed.
- Canonical database SHA-256 remained unchanged during validation.
- No dependency, backend, API, database, or schema change was added.

Mobile roadmap status:

Mobile UX Foundation v1 is accepted.
The next recommended milestone is Active Workout Mobile UX.
Mobile Food Logging and Recovery UX remains the following dedicated workflow milestone.
The next milestone remains pending Architecture scoping and is not yet implementation-authorized.

---
# Current State - Dark Mode + Theme Preference v1

Canonical implementation baseline: main at 306b6ea.

Feature branch: feature/dark-mode-theme-preference-v1.

Status: DARK_MODE_THEME_PREFERENCE_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Added user-visible System, Light, and Dark theme preferences.
- Theme preference is persisted browser-locally using fitness_ai_theme_preference_v1.
- Explicit Light and Dark use a root data-theme override; System delegates to browser/OS color preference.
- Added synchronous pre-paint theme bootstrap to avoid an obvious light-theme flash for persisted explicit preferences.
- Theme switching updates immediately without navigation or remounting product state.
- Added a reusable compact ThemePreferenceControl across all persistent user-facing routes.
- Added complete dark semantic values for the centralized theme contract.
- Completed the remaining residual semantic color migration across frontend surfaces.
- Repository-wide direct palette audit is clean outside centralized palette definitions and intentional shadows.
- Theme switching preserves in-progress Today food logging state, unsaved Recovery state, and unsaved workout-set input state.
- Added an in-memory preference fallback so live theme selection remains correct when browser storage is unavailable.
- Production browser smoke passed across desktop and approximately 390px mobile Today, Workout, and Personal Foods flows.
- No relevant browser console warnings, hydration warnings, or horizontal overflow were observed.
- No dependency, backend, API, database schema, or provider architecture change was added.

Theme initiative status:

The semantic theme foundation, daily-surface migration, workout-surface migration, and user-visible Dark Mode + Theme Preference feature are accepted.
The theme initiative is complete for the current roadmap phase.
The next recommended product milestone is Mobile UX Foundation v1.
That milestone remains pending Architecture scoping and is not yet implementation-authorized.

---
# Current State - Theme Workout Surface Migration v1

Canonical implementation baseline: main at 2439fb6.

Feature branch: feature/theme-workout-surface-migration-v1.

Status: THEME_WORKOUT_SURFACE_MIGRATION_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Migrated the core workout and training experience from direct palette-specific color utilities to the accepted semantic theme system.
- Migrated the workout route shell, WorkoutPreviewExperience, and ExerciseInstructionDisclosure.
- Covered workout preview, selection controls, exercise cards, active execution, set logging/edit/delete, completion review, history context, and exercise instructions.
- Added only narrowly required semantic workout roles for canvas/header/focused-card gradients, focused borders, caution actions, selected-control hover, and completion indicators.
- The accepted light appearance and existing workout behavior are intentionally preserved.
- Scoped direct-color audit is clean across all three workout surface files.
- Production browser smoke passed across desktop and approximately 390px mobile workout flows and the Today regression route.
- No dark mode, theme preference, persistence, provider, hydration behavior, dependency, backend, schema, or database change was added.

Theme initiative status:

Theme System Foundation v1, Theme Daily Surface Migration v1, and Theme Workout Surface Migration v1 are accepted.
No additional standalone preparatory theme-migration milestone is planned.
The next bounded theme milestone is the user-visible Dark Mode + Theme Preference v1 milestone, which may include the remaining small residual semantic cleanup required for complete dark-theme coverage.
That next milestone remains pending Architecture scoping and is not yet implementation-authorized.

---
# Current State - Theme Daily Surface Migration v1

Canonical implementation baseline: main at 9589586.

Feature branch: feature/theme-daily-surface-migration-v1.

Status: THEME_DAILY_SURFACE_MIGRATION_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Migrated the highest-frequency Today and daily-use surfaces from direct palette-specific color utilities to the accepted semantic theme system.
- Migrated the Today shell/header, Food Logging, Logged Today, Recovery Check-In, and My Foods surfaces.
- Added only narrowly required semantic roles for daily interactive, selected, focus, positive, caution, danger, and Today-header treatments.
- The accepted light appearance and existing interaction behavior are intentionally preserved.
- The Personal Food Serving Display Fix remains intact for both per-serving and per-100g personal foods.
- Production browser smoke passed on desktop and narrow/mobile Today, standalone /personal-foods, and /today/workout.
- No dark mode, theme toggle, theme preference, persistence, hydration logic, dependency, backend, schema, or database behavior was added.

Theme initiative status:

The shared theme foundation and core daily-surface semantic migration are accepted.
The next bounded Theme System + Dark Mode milestone remains pending Architecture review and is not implementation-authorized.

---
# Current State - Theme System Foundation v1

Canonical implementation baseline: main at c526289.

Feature branch: feature/theme-system-foundation-v1.

Status: THEME_SYSTEM_FOUNDATION_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Added the first semantic frontend color-token foundation using CSS custom properties exposed through the existing Tailwind v4 theme layer.
- Added semantic roles for application canvas and surfaces, text hierarchy, borders, primary interaction and focus, neutral/positive/caution/warning states, and warm/highlighted surfaces.
- Migrated TodayCard, StatusPill, DataQualityNote, UserSwitcher, and NutritionMacroCard from direct palette-oriented color utilities to semantic theme roles.
- The accepted light-theme color and opacity values are intentionally preserved.
- Production browser smoke passed on desktop and narrow/mobile Today, standalone /personal-foods, and /today/workout.
- No dark mode, theme preference, persistence, theme provider, first-paint script, dependency, backend, schema, or database behavior was added.

Theme initiative status:

The semantic foundation is accepted. The next bounded Theme System + Dark Mode milestone remains pending Architecture review and is not implementation-authorized.

---
# Current State - Personal Food Serving Display Fix v1

Canonical implementation baseline: main at 15964d7.

Feature branch: feature/personal-food-serving-display-fix-v1.

Status: PERSONAL_FOOD_SERVING_DISPLAY_FIX_V1_ARCHITECTURE_ACCEPTED

Implementation scope:

- Personal foods created from a nutrition label now display persisted entered_* nutrition values as per-serving nutrition in the shared My Foods renderer.
- Nutrition-label foods display per serving.
- Foods entered on a per-100g basis retain normalized *_per_100g values and the per 100g label.
- Existing serving-name and serving-weight context remains unchanged.
- Missing nutrients continue to be omitted individually.
- Foods without displayable nutrition retain the Nutrition details limited fallback.
- The corrected shared renderer was validated on standalone /personal-foods and Today -> My Foods at desktop and narrow/mobile widths.
- Backend APIs, database/schema, personal-food persistence, normalization, logging calculations, canonical foods, and target-vs-actual behavior are unchanged.

Next product milestone:

Pending product-roadmap review after this milestone is merged and closed.

No subsequent milestone is implementation-authorized.

## Canonical Strategic Roadmap

`docs/project_memory/product_roadmap.md` is the canonical strategic product roadmap and should be read by future Architecture onboarding alongside this current-state record. `current_state.md` describes where the project is now; `product_roadmap.md` describes where the product is headed.

---
# Current State - Today Food Workspace Deck v1

Canonical baseline: `main` at `5c9ae9e Merge desktop workout layout and explanation polish v1`.

Canonical baseline snapshot: `fitness_ai_snapshot_2026-07-15_5c9ae9e_main_merge-desktop-workout-layout-explanation-polish-v1.zip`.

Feature branch: `feature/today-food-workspace-deck-v1`.

Status:

```text
TODAY_FOOD_WORKSPACE_DECK_V1_ARCHITECTURE_ACCEPTED
```

Implementation scope:

- The Today page now presents Log Food and My Foods as one overlapping two-card workspace. The compact card headers are semantic tabs, preserve the Today URL, and switch between the existing logging and personal-food management surfaces without a route change.
- Both child surfaces remain mounted while one is hidden, so in-progress Log Food search, selection, amount, unit, and meal state and My Foods search/archive-view state survive card switching.
- The semantic selector buttons own ordinary click/tap activation. The header alone recognizes bounded horizontal pointer swipes: left opens My Foods and right opens Log Food, with pointer capture and click suppression beginning only after horizontal movement crosses the swipe threshold. Vertical movement remains available for page scrolling, and inputs, food results, action controls, and the card body do not initiate deck swipes.
- Keyboard Arrow Left/Right and Home/End switch the tab state with roving focus. Active/inactive stacking, overlap, and motion remain clear at desktop and mobile widths, with reduced-motion support.
- The existing Log Food and Personal Foods business logic is reused through narrow embedded variants. Standalone `/personal-foods`, create, edit, archive, restore, canonical/personal search, logging, and Today refresh behavior remain unchanged.
- User-facing capitalization in the touched Personal Foods surfaces is consistently `My Foods`.
- No backend API, database, schema, nutrition calculation, food identity, logging contract, workout behavior, provider, or AI behavior changed.

Next recommended milestone after Architecture acceptance:

```text
Theme System + Dark Mode v1
```

That next milestone is not implementation-authorized.

---

# Current State - Desktop Workout Layout + Explanation Interaction Polish v1

Accepted merge: `5c9ae9e Merge desktop workout layout and explanation polish v1`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-15_5c9ae9e_main_merge-desktop-workout-layout-explanation-polish-v1.zip`.

Feature branch: `feature/desktop-workout-layout-explanation-polish-v1`.

Status:

```text
DESKTOP_WORKOUT_LAYOUT_EXPLANATION_POLISH_V1_ACCEPTED_MERGED_AND_CLOSED
```

Implementation scope:

- The Exercises workspace now spans the existing centered workout shell instead of remaining in the left column. Exercise cards use an auto-fitting CSS grid with a readable `20rem` minimum, producing a single column at narrow widths and naturally adapting to roughly two or three columns across the available desktop width.
- Explanation expansion is coordinated by one parent-owned active key. On desktop, opening `How To` enters a focused detail state: the selected card spans the full exercise grid, the other exercise cards and workout controls are hidden, and compact workout details are replaced by the structured explanation surface without navigation or workout-state changes.
- The desktop detail surface retains the exercise name and a clear `Back to workout` control, keeps the overview prominent, and arranges Setup, How to do it, Form cues, Common mistakes, and Safety in a readable two-column layout where width allows.
- The reveal uses a short perspective rotation and crossfade when motion is allowed. `prefers-reduced-motion` receives only a brief fade, and the semantic disclosure buttons retain `aria-expanded`, panel associations, keyboard operation, and visible focus treatment.
- Closing the focused detail state restores the complete exercise grid and its controls in their prior responsive layout. Narrow layouts retain the accepted inline disclosure behavior, compact exercise content, and single-column flow; the focused-card hiding begins only at the existing medium breakpoint, with no nested instruction scroll region.
- Stable catalog-ID lookup, lazy instruction fetching, mounted component-local success caching, retry behavior, active-substitution identity, and null-ID omission remain unchanged. No backend, database, instruction corpus, workout generation, selection, execution, substitution, progression, set logging, or completion behavior changed.

Next implemented milestone:

```text
Today Food Workspace Deck v1
```

The accepted desktop workout layout is the stable baseline for the separately authorized Today Food Workspace Deck v1 milestone.

---

# Current State - Next.js Exercise Explanation UX v1

Accepted merge: `0159393 Merge Next.js exercise explanation UX v1`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-15_0159393_main_merge-nextjs-exercise-explanation-ux-v1.zip`.

Feature branch: `feature/nextjs-exercise-explanation-ux-v1`.

Status:

```text
NEXTJS_EXERCISE_EXPLANATION_UX_V1_ACCEPTED_MERGED_AND_CLOSED
```

Implementation scope:

- Added a compact, accessible `How to` disclosure to both exercise-card paths in the existing Next.js workout experience without changing workout selection, execution, substitution, progression, set logging, or completion behavior.
- Instructions load lazily through a narrow same-origin Next.js proxy backed by `GET /exercise-catalog/{catalog_exercise_id}/instruction`; successful content is cached within the disclosure while it remains mounted, and no instruction corpus is preloaded.
- Preview cards use `approvedPlan.exercises[].catalog_exercise_id`. Persisted cards use `plannedExercises[].catalog_exercise_id`. Active substitutions use `replacement_catalog_exercise_id`, so the explanation always follows the visible replacement exercise.
- Legacy persisted exercises with a null catalog identity render no explanation control. No name lookup, fuzzy match, or fabricated fallback is used.
- Expanded disclosures render the accepted overview plus Setup, How to do it, Form cues, Common mistakes, and Safety sections as plain text and structured lists.
- Loading and retryable failure states remain local to the affected exercise card. The proxy validates positive integer IDs, preserves meaningful backend statuses and bounded detail text, and returns `502` when the backend cannot be reached.
- No backend, database, instruction corpus, exercise library, media, provider/AI, or workout behavior change is included.

Next implemented milestone:

```text
Desktop Workout Layout + Explanation Interaction Polish v1
```

The accepted explanation UX is the stable functional baseline for that separately authorized desktop-only layout and interaction milestone.

---

# Current State - Exercise Instruction API / Read Surface v1

Accepted merge: `41dbb3a Merge exercise instruction API read surface v1`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-15_41dbb3a_main_merge-exercise-instruction-api-read-surface-v1.zip`.

Status:

```text
EXERCISE_INSTRUCTION_API_READ_SURFACE_V1_ACCEPTED_MERGED_AND_CLOSED
```

Exercise Instruction API / Read Surface v1 was Architecture accepted and merged. Its stable-ID detail route, complete persisted instruction response, not-found behavior, runtime seed initialization, focused API coverage, and backend-only scope are the accepted baseline for the active Next.js explanation UX milestone.

---

# Current State - Exercise Instruction Seed Coverage v1

Implementation baseline: `main` at `08a962c Merge exercise instruction contract and persistence v1`.

Feature branch: `feature/exercise-instruction-seed-coverage-v1`.

Feature implementation: `fed767c Add exercise instruction seed coverage`.

Accepted merge: `da660d8 Merge exercise instruction seed coverage v1`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-15_da660d8_main_merge-exercise-instruction-seed-coverage-v1.zip`.

Status:

```text
EXERCISE_INSTRUCTION_SEED_COVERAGE_V1_ACCEPTED_MERGED_AND_CLOSED
```

Implementation scope:

- Added deterministic repository-owned structured instruction seed coverage for all `240` current curated catalog exercises.
- The dedicated seed-data module organizes shared movement/equipment-specific instruction profiles plus exact-name definitions and exercise-specific overrides where mechanics diverge. Every final payload contains an overview, setup steps, one coherent execution sequence, form cues, common mistakes, and conservative safety notes written for the named exercise.
- Architecture's corpus-quality repair removed the generic-profile-plus-specific-step composition from all `240` final records. Supported and unsupported rows, unilateral and bilateral work, holds and moving repetitions, rotational and anti-rotational work, technique drills, and conditioning modalities no longer share incompatible execution copy.
- Exact catalog names are used only to validate and resolve the static seed corpus. Persisted instruction ownership remains keyed solely by `exercise_catalog_exercises.id`; no second identity, fuzzy matching, or runtime name fallback was added.
- `seed_exercise_instructions()` seeds the curated catalog, validates complete exact coverage before instruction writes, resolves stable persisted IDs, validates every instruction object, and upserts all `240` rows in one rollback-capable transaction.
- Repeated seeding is deterministic and idempotent. Repository copy changes may update the corresponding instruction rows without creating duplicates.
- Coverage validation fails on missing, unknown, or duplicate names before instruction writes. A simulated mid-write failure test verifies that partial instruction coverage is rolled back.
- Content integrity checks reject blank fields, empty production lists, placeholder words such as `specified`, `required`, and `chosen`, the known leaked template phrases, generic profile execution steps in final records, tautological name-overview openings, ambiguous mixed-variant fragments, and explicit equipment terms not present in the exercise's catalog requirements.
- No API route or response, frontend, Streamlit, workout generation/selection/substitution, progression, provider/AI, or canonical database data change is included.
- Validation passed after the corpus-quality repair: focused seed-coverage plus accepted persistence tests `25 passed`; required catalog/workout regression slice `263 passed`; project-memory tests `29 passed`; project-memory checker `608 PASS`, `39 WARN`, `0 FAIL`; touched-file Ruff check, Ruff format check, and Python compilation passed.
- No browser smoke was required because there is no frontend or public API behavior. The canonical `fitness_ai.db` remained unchanged at SHA-256 `FEDC430E47E32B338E1E2EF471B355528B99AA5007A1EF577A32678EECF3ABA7` throughout validation.

Next recommended milestone after Architecture acceptance:

```text
Exercise Instruction API / Read Surface v1
```

Exercise Instruction Seed Coverage v1 is Architecture accepted, merged, and closed. Its instruction corpus is exposed only through the separately authorized Exercise Instruction API / Read Surface v1 milestone.

---

# Current State - Exercise Instruction Contract + Persistence v1

Feature implementation: `cc06a25 Add exercise instruction contract and persistence`.

Accepted merge: `08a962c Merge exercise instruction contract and persistence v1`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-15_08a962c_main_merge-exercise-instruction-contract-persistence-v1.zip`.

Status:

```text
EXERCISE_INSTRUCTION_CONTRACT_PERSISTENCE_V1_ACCEPTED_MERGED_AND_CLOSED
```

Implementation scope:

- Added a structured `ExerciseInstruction` backend contract keyed only by the existing stable `exercise_catalog_exercises.id`.
- Added the additive one-to-one `exercise_catalog_instructions` table. `exercise_id` is both its primary key and its foreign key to the parent catalog exercise; there is no second instruction identity.
- Added internal deterministic `upsert_exercise_instruction(...)` and `get_exercise_instruction(...)` service seams. Upsert replaces the record for the same catalog exercise, rejects a missing parent exercise, and preserves ordered instruction-list content through JSON persistence.
- Catalog exercises without instruction records return explicit absence. No instruction fallback or exercise-name matching is used.
- Existing catalog initialization gains the empty instruction table additively without rebuilding, backfilling, or changing catalog records or IDs.
- Focused coverage uses pytest-owned temporary databases and verifies the contract, schema identity, round-trip behavior, update behavior, independent records, absence, invalid parent rejection, empty lists, deterministic catalog seeding, unchanged catalog rows, and additive initialization.
- No production instruction corpus, API route or response, frontend, Streamlit, workout generation/selection/substitution, progression, media, provider/AI, or canonical database data change is included.
- Validation passed: focused instruction persistence `12 passed`; required catalog/workout regression slice `263 passed`; project-memory tests `29 passed`; project-memory checker `608 PASS`, `39 WARN`, `0 FAIL`; touched-file Ruff check, Ruff format check, and Python compilation passed.
- No browser smoke was required because there is no frontend or public API behavior. The canonical `fitness_ai.db` remained unchanged at SHA-256 `FEDC430E47E32B338E1E2EF471B355528B99AA5007A1EF577A32678EECF3ABA7` throughout validation.

Next implemented milestone:

```text
Exercise Instruction Seed Coverage v1
```

Exercise Instruction Contract + Persistence v1 is accepted, merged, and closed. It did not add production instruction coverage, API exposure, or frontend behavior.

---

# Current State - Exercise Catalog Identity Propagation v1

Accepted main merge: `6227f50 Merge exercise catalog identity propagation v1`.

Feature implementation: `65fccbd Add exercise catalog identity propagation`.

Status:

```text
EXERCISE_CATALOG_IDENTITY_PROPAGATION_V1_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Stable `exercise_catalog_exercises.id` identity now propagates through candidate workout exercise, approved workout exercise, approved workout-plan serialization, planned-workout persistence, and downstream read state.
- Legacy approved-plan JSON without `catalog_exercise_id` remains compatible.
- Legacy persisted planned-workout rows with `catalog_exercise_id = NULL` remain compatible.
- Exercise substitution lookup prefers persisted stable catalog identity when available and retains name lookup only as the legacy null-ID fallback.
- The schema addition is additive and nullable. No legacy planned-workout rows were backfilled.
- No workout generation behavior, selection policy, substitution compatibility or scoring policy, or frontend behavior changed.
- Affected automated tests use pytest-owned databases, and guarded validation confirmed they cannot access the canonical `fitness_ai.db`.
- Merged-main targeted validation, project-memory checks, Ruff checks, formatting checks, Python compilation, and `git diff --check` passed.
- No browser smoke was required because no frontend behavior changed.
- Canonical user data was not part of this milestone.
- Exercise Catalog Identity Propagation v1 is accepted, merged, and closed.

Next recommended milestone:

```text
Exercise Instruction Contract + Persistence v1
```

This next milestone is recommended for Architecture definition but is not authorized for implementation.

See the closed baseline milestone memory:
`docs/project_memory/milestones/project_memory_developer_workflow_canonicalization_v1.md`.

---

# Current State - Personal Custom Foods UI v1

Accepted merge: `0715c63 Merge personal custom foods UI v1`.

Feature implementation: `f1df5fb Add personal custom foods UI`.

Status:

```text
PERSONAL_CUSTOM_FOODS_UI_V1_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- The accepted Personal Custom Foods backend contract/persistence milestone is now exposed through the Next.js product workflow without changing the accepted schema, personal-food identity model, immutable revision model, or historical logging contract.
- Added `/personal-foods`, `/personal-foods/new`, and `/personal-foods/{personalFoodId}` management pages with user/date-preserving navigation, active/archived views, search, create, future-facing revision edits, archive, and restore.
- Normal Log Food search now combines canonical and active user-owned personal foods while preserving discriminated result types, canonical duplicates, and the existing two-character threshold. Personal results are labeled `My food`.
- Personal foods can be logged in grams or by a stored serving when available. Logged today now displays canonical and personal entries together and supports personal amount, saved-serving, meal, and delete operations.
- Bounded personal-log list/update/delete routes remain user-, type-, and date-scoped. Edits recalculate against the exact stored `personal_food_revision_id`; historical logs never silently switch to a newer revision.
- Blank personal-food nutrient inputs remain unknown rather than becoming zero. Switching between Nutrition label and Per 100g clears nutrient inputs so values cannot be silently reinterpreted under a different basis.
- Canonical and personal search/refresh sources settle independently. One failing source no longer hides successful results from the other, and stale concurrent refreshes cannot overwrite newer data.
- Today nutrition totals refresh after successful canonical or personal log mutations without moving nutrition calculations into the frontend.
- Browser acceptance passed on the production Next.js build served on the project's standard port `3100`. The smoke covered personal-food creation, search, normal Log Food discovery, grams and saved-serving logging, Logged today updates, macro refresh, personal-log editing/deletion, immutable historical revision behavior, archive/restore, canonical logging regression behavior, and responsive layout.
- The `My foods` entry point is functionally accepted but visually too subtle in the current Log Food card. This is recorded as a future navigation/UI-polish follow-up rather than a blocker for this milestone.
- Pre-merge implementation validation passed: personal-food focused tests `84 passed`; canonical/edit/recents/Target-vs-Actual/API regression slice `93 passed`; project-memory tests `29 passed`; project-memory checker `590 PASS`, `58 WARN`, `0 FAIL`; Ruff, Ruff format, Python compile, frontend lint, Next.js production build, and `git diff --check` passed.
- Merged-main validation completed successfully through the targeted backend regression slices, Ruff/format/compile checks, frontend lint and production build, project-memory checker/tests, and `git diff --check`.
- The browser smoke intentionally created personal-food test data in the real local database. The resulting hash change was investigated and matched that intentional smoke activity; it was not database corruption. Post-smoke database SHA-256: `7269CF76E3C4AAE714E6D168CE9E5B30BEDD28F50FFCC8FAC8565E5CC0CBE5B3`.
- No recipes, saved meals, meal templates, barcode/OCR/import flows, authentication changes, new AI/provider behavior, workout behavior, report behavior, or new schema design was added in this milestone.

Next architecture milestone:

```text
PUBLIC_PROJECT_REBRAND_AND_README_REFRESH_V1
```

The public rebrand should remove the obsolete AI-first identity from the project name and primary public surfaces, rename the GitHub repository, rewrite the README around the actual health/fitness platform capabilities, update repository description/topics, and refresh the LinkedIn project presentation. Historical architecture documents may retain accurate references to prior AI/provider experiments where relevant.

See milestone memory:
`docs/project_memory/milestones/personal_custom_foods_ui_v1.md`.

---

# Current State - Personal Custom Foods Contract and Persistence v1

Accepted merge: `4da8672 Merge personal custom foods contract and persistence v1`.

Feature implementation: `89c1d58 Add personal custom food persistence`.

Status:

```text
PERSONAL_CUSTOM_FOODS_CONTRACT_PERSISTENCE_V1_ACCEPTED_MERGED_AND_CLOSED
```

Active scope:

- Add deterministic, user-owned personal-food identities with immutable nutrition revisions, archive behavior, user-scoped search, and historically stable logging.
- Keep personal foods separate from global canonical foods and future recipes/saved meals.
- Preserve unknown nutrient values as `NULL`; preserve explicitly entered zeroes as zero.
- Use immutable internal legacy food/nutrient rows per revision so existing nutrition actuals remain historically correct while internal rows stay hidden from global legacy search.
- Add explicit `food_entries` provenance for personal identity, exact revision, and user-facing name snapshot.
- This is backend contract, persistence, service, and API work only. Personal Custom Foods UI v1 is a later milestone.

Implementation and validation:

- Added explicit personal-food identities, immutable revisions, internal legacy nutrition rows, and nullable `food_entries` provenance columns through database initialization only.
- Added atomic create, revise, archive, restore, and log services with user ownership checks, deterministic label normalization, unknown-value preservation, and historical macro/name snapshots.
- Added user-scoped API contracts and excluded opaque internal personal-food rows from legacy global food search without changing canonical search responses.
- Architecture corrections ensure existing databases add both personal-food provenance foreign keys after the referenced tables exist, reject non-finite derived label normalization before persistence, and apply the established 5,000 g ceiling to direct and serving-resolved personal-food logs.
- Final boundary corrections reject JSON booleans before Pydantic numeric coercion for every personal-food nutrition/log field, validate positive integer personal-food IDs in direct service calls, and reject non-finite nutrient snapshots before log insertion.
- Resolved serving grams are validated after multiplication, so finite positive inputs that underflow to `0.0` are rejected without a log entry. Latest personal-food tests passed: `73`; existing nutrition regression tests passed: `143`. The prior final-correction full repository suite passed: `2496`; this narrow underflow handoff did not require a full rerun.
- Touched-file Ruff check and format check passed for all ten milestone Python files. Formatting was limited to milestone-touched files.
- Python compile checks passed. The project-memory checker passed with `590 PASS`, `58 WARN`, and `0 FAIL`; its tests passed: `29`.
- A final audit after the initial full-suite run found that the real ignored `fitness_ai.db` had unintentionally received the new empty personal-food schema. Both personal tables contained zero rows and all personal provenance values on existing food entries were `NULL`.
- Architecture authorized a bounded recovery. The current database was backed up externally through both a filesystem copy and SQLite's backup API, then only the empty personal tables, indexes, and provenance columns were removed in one `BEGIN IMMEDIATE` transaction.
- Cleanup evidence is retained at `C:\projects\fitness_ai_external\db_recovery\personal_custom_foods_schema_cleanup_20260714_203741`. Pre-existing table counts and data fingerprints matched before and after; `integrity_check` remained `ok`; and the exact pre-existing 34-row foreign-key violation set remained unchanged with SHA-256 `E8B9DF295C8DAA60E5B5E41AB0BAA15605B216A1D4B207412EB6EB0993F1F133`.
- Underflow-correction validation ran from an isolated temporary source mirror with no live database. Personal-food tests passed: `73`; nutrition regression tests passed: `143`. The prior final-correction full repository suite passed: `2496`. The cleaned live database hash remained `5829A88632674377CC4A7AB5BD3D2022F01128A474EF859FB270F7B77768BA38` throughout validation.
- Browser smoke remains intentionally deferred to Personal Custom Foods UI v1.
- Merged-main validation passed: personal-food focused tests `73 passed`; nutrition regression tests passed; the full repository suite passed; touched-file Ruff, format, compile, project-memory, and diff checks passed.
- Architecture accepted the complete implementation and final correction diffs. The separate automated review produced no usable result and was not repeated.
- The real ignored database remained unchanged during merged-main validation at SHA-256 `5829A88632674377CC4A7AB5BD3D2022F01128A474EF859FB270F7B77768BA38`.
- The backend milestone is accepted, merged locally, and closed. Personal Custom Foods UI v1 is next.

Prior experiment closeout:

- Cross-Domain Narrative Decision Freedom v1 was not merged.
- Qwen3:8B safety enforcement worked, but its narrative product quality failed human acceptance.
- AI-written daily coaching prose is paused indefinitely. The product-voice audit is not an accepted readiness gate.
- The nominal read path can invoke workout schema initialization and was sufficient to explain the observed database hash change.

See milestone memory:
`docs/project_memory/milestones/personal_custom_foods_contract_persistence_v1.md`.

See experiment closeout:
`docs/project_memory/milestones/cross_domain_narrative_experiment_closeout_v1.md`.

---

# Current State - Cross-Domain Coaching Synthesis Preview v1

Accepted merge: `b63ec69 Merge semantic cross-domain coaching preview`.

Feature implementation: `596f14b Add semantic cross-domain coaching preview`.

Status:

```text
CROSS_DOMAIN_COACHING_SYNTHESIS_PREVIEW_V1_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- The developer-only two-call cross-domain preview is merged on `main`. It adds no Today/public UI, public API route, normal provider runtime, persistence, schema, migration, dependency, frontend behavior, or provider promotion.
- Backend-owned evidence is projected into bounded semantic assessment and narrative contexts. Provider-facing actions contain semantic IDs, typed parameters, approved support, confidence, and conditions rather than backend-authored coaching sentences.
- The raw `ApprovedCoachBrief`, today-intent copy, instruction/interpretation copy, allowed-phrasing banks, coach-safe summaries, deterministic fallback prose, and specialist prose do not enter the narrative call.
- The complete audit/provenance packet remains available for developer inspection. The assessment context is capped at recovery/nutrition/training/shared `8/8/10/5`; narrative facts are bounded at `6/8/6`.
- Successful previews make at most two provider calls. Invalid assessment output blocks the narrative call. Direct Ollama, OpenAI, and mock provider seams remain developer-only; Qwen3 strict calls set `think: false`.
- Claim audit, confidence-coherence audit, and product-voice audit remain in the approval path. Unsupported foods, values, servings, timing, causal claims, certainty escalation, source-gap denial, and workout changes remain rejected without requiring sentence similarity.
- Merged-main validation passed: targeted provider/audit regression `136 passed`; project-memory checker `590 PASS`, `58 WARN`, `0 FAIL`; project-memory tests `29 passed`; Ruff check and format check passed; `git diff --check` passed.
- Frozen live benchmark: QA user `102`, date `2026-05-31`, scenario `aligned_managed`.
- Qwen3:8B and Qwen3:32B confirmed that the semantic contract removed direct legacy-copy leakage and allowed novel wording. Narrative quality is still not accepted for product use: outputs remained generic and structurally constrained by the backend-selected primary/supporting action outline.
- The product-voice audit is not accepted as a reliable product-readiness signal for this workflow; it scored mediocre provider prose too generously. It remains implemented but requires a later evaluation/redesign milestone.
- The OpenAI upper-bound benchmark is intentionally deferred to avoid spending credits before the provider receives meaningful editorial decision freedom.
- The semantic contract is accepted as infrastructure. It is not authorization for Today/public/provider promotion.

Next architecture direction:

```text
Cross-Domain Narrative Decision Freedom v1
```

That milestone should let the narrative provider choose the most useful focus and zero, one, or two approved supporting ideas from a safe candidate envelope, while the backend continues to validate selected semantic keys, facts, foods, values, and safety constraints.

A later, separate milestone should expand coaching food candidates through deterministic retrieval/ranking from the broader canonical catalog rather than repeatedly exposing only the current narrow food pool.

See milestone memory:
`docs/project_memory/milestones/cross_domain_coaching_synthesis_preview_v1.md`.

---

# Current State - USDA Generic Source-Specific Promotion Rules v0

Current source of truth: `main` at `929886d Merge USDA generic source-specific promotion rules v0`.

Feature implementation commit: `50d7e2b Add USDA source-specific promotion rules`.

Status:

```text
USDA_GENERIC_SOURCE_SPECIFIC_PROMOTION_RULES_V0_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Fixed source precedence is Foundation, SR Legacy, then FNDDS; lower-priority
  collision rows are explicit duplicate-name skips.
- SR Legacy is limited to seven conservative basic-food categories and rejects
  bounded commercial/product-line evidence including Bolthouse Farms, Daily
  Greens, Silk, Vitasoy, and Nasoya, plus USDA distribution-program metadata.
- FNDDS remains fully deferred from canonical promotion.
- Same-name/same-macro families select one deterministic representative; unresolved
  different-macro families no longer use generic comma-phrase renaming.
- Nine initial and 33 review-corrected Foundation display-name mappings, plus a
  peeled-kiwifruit correction, cover the approved diagnostic examples without
  restoring generic comma-phrase fallback.
- SR meatless rows retain their `Meatless` qualifier; soy vermicelli retains its
  soy identity. Focused tests passed: `110`; import/promotion safety tests passed:
  `131`. Ruff check and format check passed.
- Official external dry-runs processed Foundation `469`, SR Legacy `7,793`, FNDDS
  `5,432`, and combined `13,694` rows. Combined promoted `348` rows; all 151
  Foundation-only candidates remained present and reversed data-type order produced
  identical promoted identities and names.
- The final audit found zero promoted Bolthouse/Daily Greens rows, zero promoted
  Silk/Vitasoy/Nasoya rows, zero promoted meatless rows without `Meatless`, zero
  promoted USDA distribution metadata rows, zero `Kiwifruit Kiwi` names, and zero
  adjacent duplicate-word names. General `Kiwifruit` and `Peeled kiwifruit` both
  remain promoted. External evidence verdict:
  `READY_FOR_LIMITED_FOUNDATION_SR_PROMOTION_PLAN`.
- No canonical records were promoted. Raw count remained `13,694`; canonical
  tables remained empty; the real `fitness_ai.db` was not accessed or mutated.
- The rules remain dry-run evidence only and do not authorize live canonical promotion.
- Accepted merge: `929886d Merge USDA generic source-specific promotion rules v0`.
- Feature implementation: `50d7e2b Add USDA source-specific promotion rules`.
- Project-memory checker passed with `590 PASS`, `58 WARN`, and `0 FAIL`; project-memory tests passed: `29`.
- Final verdict: `READY_FOR_LIMITED_FOUNDATION_SR_PROMOTION_PLAN`.
- Milestone is accepted, merged, and closed. Git is authoritative for the final documentation commit and snapshot hash.

See milestone memory:
`docs/project_memory/milestones/usda_generic_source_specific_promotion_rules_v0.md`.

---

# Current State - USDA Generic Canonical Promotion Diagnostic v0

Accepted diagnostic base: `main` at `53703aa Close USDA generic full dataset validation memory`.

Status:

```text
USDA_GENERIC_CANONICAL_PROMOTION_DIAGNOSTIC_V0_ACCEPTED_AND_CLOSED
```

Closeout:

- Existing deterministic promotion rules were evaluated against all `13,694` validated generic USDA rows.
- Foundation classified `138` rows as promotable, with `231` duplicate-name skips, `58` unsafe-raw skips, and `42` missing-macro skips.
- SR Legacy classified `670` rows as promotable, with `4,681` duplicate-name skips, `1,274` category skips, `1,166` unsafe-raw skips, and `2` invalid skips.
- FNDDS classified `0` rows as promotable; `5,431` were blocked by current category policy and one lacked supported macros.
- The combined run classified `691` rows as promotable, including `57` Foundation and `634` SR Legacy rows.
- The diagnostic identified `2,534` candidate-name families, `356` multi-source overlaps, `933` same-name families with different macro profiles, and `652` suspicious-name review flags.
- Current combined handling does not preserve Foundation precedence and can allow lower-priority SR Legacy rows to displace Foundation candidates.
- Current generic duplicate renaming can produce malformed commercial or over-generic display names.
- No canonical foods, aliases, nutrients, source links, or raw application rows were changed.
- Final verdict: `READY_FOR_SOURCE_SPECIFIC_PROMOTION_RULE_DESIGN`.
- Existing rules are not approved for live canonical promotion.
- Milestone is accepted and closed. Git is authoritative for the final documentation commit and snapshot hash.

Architecture direction:

- Source precedence will be Foundation, then SR Legacy, then FNDDS.
- Foundation remains the preferred generic source.
- SR Legacy will initially be restricted to conservative basic-food categories, with commercial or manufacturer-style rows rejected.
- FNDDS canonical promotion remains deferred for a separate prepared-food strategy.
- Cross-source collisions will prefer the highest-priority valid source.
- Generic second-phrase renaming will not be used when it creates low-quality names.
- The next source-specific promotion-rules milestone will remain dry-run only.

Retained evidence:

- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\working\usda_generic_promotion_diagnostic_v0.db`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_canonical_promotion_diagnostic_v0.json`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_canonical_promotion_diagnostic_v0.md`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_candidate_name_families.csv`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_category_matrix.csv`
- `C:\projects\fitness_ai_external\usda_generic_promotion_diagnostic_2026-07-11\reports\usda_generic_review_samples.csv`

See milestone memory: `docs/project_memory/milestones/usda_generic_canonical_promotion_diagnostic_v0.md`.

---

# Current State - USDA Generic Full-Dataset Validation v0

Accepted validation base: `main` at `fde27bf Close FNDDS macro payload compatibility memory`.

Status:

```text
USDA_GENERIC_FULL_DATASET_VALIDATION_V0_ACCEPTED_AND_CLOSED
```

Closeout:

- The complete official Foundation, SR Legacy, and FNDDS generic datasets imported successfully into one fresh external scratch database.
- Foundation first pass: `469` processed, `469` inserted, `0` updated.
- SR Legacy first pass: `7,793` processed, `7,793` inserted, `0` updated.
- FNDDS first pass: `5,432` processed, `5,432` inserted, `0` updated.
- Total first-pass raw records: `13,694`.
- The full idempotency rerun inserted `0` rows and updated the exact source count for all three datasets.
- Final raw record total remained `13,694`.
- No unexpected source types, duplicate or missing source identities, empty descriptions, negative macro values, or missing resolved categories were found.
- FNDDS provenance was populated for all `5,432` FNDDS records.
- Canonical food and canonical source-link counts remained `0`.
- The real `fitness_ai.db` was not accessed or mutated.
- The repository remained clean and unchanged throughout validation.
- Final verdict: `READY_FOR_GENERIC_CANONICAL_PROMOTION_DIAGNOSTIC`.
- External scratch database and reports were retained for promotion-diagnostic work.
- Milestone is accepted and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Prove that the complete official generic USDA datasets import together, preserve identity and provenance, remain canonical-safe, and rerun idempotently before promotion design begins.
```

Retained evidence:

- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\scratch\usda_generic_full_dataset_validation_v0_final.db`
- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\reports\usda_generic_full_dataset_validation_v0_final.json`
- `C:\projects\fitness_ai_external\usda_generic_full_validation_2026-07-10\reports\usda_generic_full_dataset_validation_v0_final.md`

See milestone memory: `docs/project_memory/milestones/usda_generic_full_dataset_validation_v0.md`.

---

# Current State - FNDDS Macro and Payload Compatibility v0.1

Current source of truth: `main` at `21f5655 Merge FNDDS macro and payload compatibility v0.1`.

Feature implementation commit: `9b93a4a Support FNDDS macro identifiers and payload provenance`.

Status:

```text
FNDDS_MACRO_PAYLOAD_COMPATIBILITY_V0_1_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Accepted merge: `21f5655 Merge FNDDS macro and payload compatibility v0.1`.
- Feature implementation: `9b93a4a Support FNDDS macro identifiers and payload provenance`.
- Focused importer tests: `48 passed`.
- Importer and bulk-catalog regression: `76 passed`.
- Import and promotion safety regression: `49 passed`.
- Ruff checks and merged-main production browser smoke passed.
- Official full FNDDS import processed `5,432` rows and reran as `0` inserts plus `5,432` updates.
- `5,431` rows preserved all four supported macros; one source row had no supported macros and remained unmodified.
- No schema, migration, canonical promotion, frontend behavior, dependency, or real-database mutation occurred.
- Milestone is accepted, merged, and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Support the nutrient identifier convention used by the current official FNDDS release and preserve resolved WWEIA category descriptions in raw source provenance.
```

Implemented scope:

- Recognized macro definitions are registered through both `nutrient.id` and optional `nutrient.nutrient_nbr` identifiers.
- Existing Foundation and SR Legacy identifier behavior remains supported.
- Conflicting numeric identifier mappings fail clearly; blank optional nutrient numbers remain safe.
- Missing macro source rows remain missing and zero macro values remain zero.
- FNDDS raw payloads now preserve `wweia_food_category_description`.
- The payload description equals the persisted resolved food category.
- The input-only alias key `wweia_food_category` remains excluded from raw payloads.

Validation completed:

- Focused USDA importer tests: `48 passed`.
- USDA importer and bulk-catalog slice: `76 passed`.
- Food import and promotion safety slice: `49 passed`.
- Ruff check and format checks passed for the touched Python files.
- Official full FNDDS first pass: `5,432` processed, `5,432` inserted, `0` updated.
- Official full FNDDS rerun: `5,432` processed, `0` inserted, `5,432` updated.
- `5,431` rows had calories, protein, carbohydrates, and fat; one row had no supported macro values.
- All `5,432` rows preserved food code, WWEIA number, stable WWEIA code, and WWEIA category description.
- There were no duplicates, negative macros, canonical foods, or canonical source links.
- Merged-main production browser smoke passed for Today, Nutrition, canonical search, Workout, console safety, and mobile overflow.
- The real `fitness_ai.db` was not read or mutated.

See milestone memory: `docs/project_memory/milestones/fndds_macro_payload_compatibility_v0_1.md`.

---

# Current State - FNDDS WWEIA Header Compatibility v0.1

Current source of truth: `main` at `34d4a59 Merge FNDDS WWEIA header compatibility v0.1`.

Feature implementation commit: `75486d8 Support current FNDDS WWEIA header`.

Status:

```text
FNDDS_WWEIA_HEADER_COMPATIBILITY_V0_1_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Accepted merge: `34d4a59 Merge FNDDS WWEIA header compatibility v0.1`.
- Feature implementation: `75486d8 Support current FNDDS WWEIA header`.
- Importer and inventory regression: `70 passed`.
- Import and promotion safety regression: `49 passed`.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; checker tests: `29 passed`.
- Ruff checks and production browser smoke passed.
- Official FNDDS 25-row import inserted `25` rows and reran as `0` inserts plus `25` updates.
- No schema, migration, canonical promotion, frontend behavior, or real-database mutation occurred.
- Milestone is accepted, merged, and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Accept the current official FNDDS WWEIA category header without changing generic source selection, promotion, schema, or user-facing behavior.
```

Implemented scope:

- Importer and read-only inventory accept either `wweia_food_category` (current official FNDDS header) or `wweia_food_category_code` (documented/legacy header).
- Both inputs resolve to the stable internal and raw-payload key `wweia_food_category_code`; no `wweia_food_category` payload key is emitted.
- Dual headers accept matching values or one empty value; conflicting non-empty values, missing accepted headers, blank resolved codes, and duplicate resolved codes fail clearly.
- The generic fixture now uses the current official FNDDS header, while focused runtime-copy tests preserve documented and dual-header coverage.
- No schema, migration, source profile, streaming, category semantics, source identity, canonical promotion, CLI, frontend, dependency, or real-database change was added.

Validation completed:

- Importer/inventory regression: `70 passed`.
- Import/promotion safety regression: `49 passed`.
- Project-memory checker: `590 PASS`, `58 WARN`, `0 FAIL`; checker tests: `29 passed`.
- Official FNDDS header confirmed as `wweia_food_category,wweia_food_category_description`.
- Official 25-row FNDDS scratch import inserted `25` rows and reran as `0` inserts plus `25` updates; all rows had FNDDS provenance and category descriptions, without duplicates, negative macros, canonical foods, or source links.
- Production browser smoke passed on a temporary database for Today, Nutrition, canonical search, Workout, zero console errors, and no horizontal overflow around 390px.
- Temporary scratch and browser-smoke artifacts and dedicated processes were removed; the real `fitness_ai.db` was not read or mutated.

See milestone memory: `docs/project_memory/milestones/fndds_wweia_header_compatibility_v0_1.md`.

---

# Current State - USDA Generic Source Expansion v0

Current source of truth: `main`. Accepted application merge: `f4b44da Merge USDA generic source expansion v0`.

Latest accepted food-catalog milestone:

```text
USDA Generic Source Expansion v0
```

Status:

```text
USDA_GENERIC_SOURCE_EXPANSION_V0_ACCEPTED_MERGED_AND_CLOSED
```

Closeout:

- Accepted merge: `f4b44da Merge USDA generic source expansion v0`.
- Feature implementation: `e8a96ce Expand USDA generic source import`.
- Validation accepted: 58 importer/inventory tests, 44 import/promotion tests, 70 canonical logging/search tests, and 29 project-memory tests.
- Project-memory checker: 590 PASS, 58 WARN, 0 FAIL.
- Production browser smoke passed using a temporary database; the real `fitness_ai.db` was not used or mutated.
- Milestone is merged and closed. Git is authoritative for the final documentation commit and snapshot hash.

Purpose:

```text
Expand the raw FoodData Central catalog to Foundation Foods, SR Legacy, and Survey Foods (FNDDS) without promoting rows into the canonical catalog.
```

Implemented scope:

- The FDC directory importer defaults to stable keys `foundation_food`, `sr_legacy_food`, and `survey_fndds_food`; branded, experimental, and support rows remain excluded unless explicitly requested.
- `food.csv` and `food_nutrient.csv` are streamed and filtered so only selected foods and their four supported macros are retained in memory.
- FNDDS rows use the documented survey-to-WWEIA category relationship and preserve food code and category provenance in the raw payload.
- Raw records preserve both the original USDA data-type label and its normalized stable key.
- Inventory now reports grouped macro coverage and source-appropriate category counts for all three generic types while remaining read-only.
- Source identity and idempotent upserts remain `source_name + FDC ID`; no canonical promotion, schema, or migration change was added.

Validation completed:

- USDA importer and inventory slice: `58 passed`.
- Food import and promotion regression slice: `44 passed`.
- Canonical logging and search confidence slice: `70 passed`.
- Scratch import processed `5` generic rows (`1` Foundation, `2` SR Legacy, `2` FNDDS), excluded branded/experimental rows, and reran as `5` updates with no duplicates or canonical-table changes.
- Ruff lint/format checks passed for the touched Python files.
- Project-memory validation completed with `590 PASS`, `58 WARN`, and `0 FAIL`; checker tests passed with `29 passed`.
- Read-only production browser smoke passed for Today, Nutrition, canonical food search/logging UI, Workout, zero console errors, and no horizontal overflow around 390px.
- No extracted full local FDC dataset was available for the optional large-dataset validation; no download was attempted.
- The real `fitness_ai.db` was untouched; scratch and browser-smoke artifacts and dedicated processes were removed.

See milestone memory: `docs/project_memory/milestones/usda_generic_source_expansion_v0.md`.

---

# Current State - Workout Execution Integrity Fixes v0.1 (Closed)

Current source of truth: `main` at `d424a83 Merge workout execution integrity fixes v0.1`.

Feature implementation commit: `d2538d7 Fix workout execution integrity`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-10_d424a83_main_merge-workout-execution-integrity-fixes-v0-1.zip`.

Milestone status:

```text
WORKOUT_EXECUTION_INTEGRITY_FIXES_V0_1_ACCEPTED_MERGED_PUSHED_SNAPSHOTTED_CLOSED
```

The milestone was accepted, merged, pushed, snapshotted, and closed after its targeted tests, Ruff checks, frontend lint/build, project-memory validation, and production browser smoke passed.

See milestone memory: `docs/project_memory/milestones/workout_execution_integrity_fixes_v0_1.md`.

---

# Current State â€” Agent Workflow Hardening v0 (Closed)

Current source of truth: `main` at `4e89f27 Merge agent workflow hardening v0`.

Accepted merge commit: `4e89f27`.

Feature implementation commit: `1fa45a2`.

Accepted snapshot: `fitness_ai_snapshot_2026-07-10_4e89f27_main_merge-agent-workflow-hardening-v0.zip`.

Milestone:

```text
Agent Workflow Hardening v0
```

Milestone status:

```text
AGENT_WORKFLOW_HARDENING_V0_ACCEPTED_MERGED_PUSHED_SNAPSHOTTED_CLOSED
```

Purpose:

```text
Add concise repository-native Codex instructions, a reusable milestone loop, a targeted validation matrix, and a read-only status helper without changing application behavior.
```

Delivered scope:

- Replace the historical root instruction bundle with concise repository-wide implementation and safety rules.
- Add frontend-specific instructions for compact UI work and production browser confidence.
- Add the repository-owned `fitness-ai-milestone` skill for implementation and interruption recovery.
- Add a maintainable targeted validation matrix using existing tests only.
- Add a read-only PowerShell milestone status helper with Git, artifact, database, and diff checks.
- Preserve application, API, persistence, dependency, and provider behavior.

Accepted validation:

- Repository skill validation passed.
- The status helper passed normal feature-work inspection and detected a temporary forbidden-artifact fixture without failing; the fixture was removed.
- Independent review hardening confirmed ignored `frontend/.next`, `frontend/node_modules`, nested `tmp/**/__pycache__/*.pyc`, and temporary smoke databases are reported without mutation or a blocking exit; tracked or staged forbidden artifacts remain blocking.
- Final review hardening replaced the recursive `tmp/` scan with a depth-6 walker that skips reparse points and excluded/generated directories; fixtures proved in-depth detection, no `__pycache__` or `node_modules` traversal, no traversal beyond the limit, unchanged files, and exit code `0`.
- Project-memory validation completed with `590 PASS`, `58 WARN`, and `0 FAIL`; checker tests passed with `29 passed`.
- Today/workout persistence, route, and view confidence tests passed with `88 passed`.
- Frontend lint and production build passed.
- Production browser smoke passed against a temporary database copy with zero console errors and no mobile horizontal overflow.
- The real `fitness_ai.db` was not mutated, and milestone-created smoke, bounded-walker fixture, and generated-cache artifacts were removed.
- The milestone was accepted, merged to `main`, pushed, snapshotted, and closed.

See milestone memory: `docs/project_memory/milestones/agent_workflow_hardening_v0.md`.

---

# Current State â€” Workout Actuals Summary v0

Current source of truth: `feature/workout-actuals-summary-v0`.

Active workout milestone:

```text
Workout Actuals Summary v0
```

Requested status:

```text
WORKOUT_ACTUALS_SUMMARY_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add a compact per-exercise view of logged versus planned workout execution using existing backend-owned planned exercises and actual sets.
```

Implemented scope:

- Added a compact exercise-actuals breakdown below the existing Execution Summary metrics.
- Each planned exercise shows logged/planned set count, accessible set-completion dots, and a neutral completion label.
- Completed non-skipped actual sets determine logged counts; substitution-linked sets remain attributed to their planned exercise.
- Per-exercise average actual RIR maps to hard, moderate, easy, or limited-data effort labels.
- Logged reps map to on-target, mixed, below-range, above-range, or no-logged-reps labels using the planned rep range.
- Extra logged sets remain visible as planned dots plus a neutral extra-set indicator.
- Edits and deletes update the summary through the existing actual-set state and summary refresh paths.

Boundaries preserved:

- No backend route, service, schema, persistence, planned workout snapshot, progression history, completion review, workout generation, recommendation, deload, periodization, nutrition, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Actual set create/edit/delete remains user-entered and backend-validated.
- Progression history remains read-only and derives from completed actual-set rows only.
- Completion remains explicitly user-triggered through the existing completion review and backend completion endpoint.

Validation completed:

- Workout persistence and progression-history slice: `91 passed`.
- Workout planning, route, view, rotation, and sizing slice: `128 passed`.
- Frontend lint and production build passed.
- `git diff --check` passed.
- Browser smoke passed against a temporary database copy, including complete, partial, not-started, edit, cancel, delete, completion-review, accessibility-label, and narrow-layout states.
- The real `fitness_ai.db` was not mutated.

See milestone memory: `docs/project_memory/milestones/workout_actuals_summary_v0.md`.

---

# Current State â€” Workout Completion Review UX v0.1

Current source of truth: `feature/workout-completion-review-ux-v0-1`.

Active workout milestone:

```text
Workout Completion Review UX v0.1
```

Requested status:

```text
WORKOUT_COMPLETION_REVIEW_UX_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make workout completion intentional by showing a compact pre-completion review based on existing backend planned-vs-actual summary data.
```

Implemented scope:

- Changed the workout completion button so the first click opens an inline review instead of completing immediately.
- Added a compact completion review with logged/planned set count, exercise completion count, average RIR, and all-logged or missing-set status.
- Kept missing-set language neutral and allowed explicit completion anyway through the existing backend completion path.
- Added cancel behavior that returns to the normal active workout logging view.
- Kept the existing completed state, execution summary, saved sets, and previous-performance context visible after completion.
- Used the existing planned-vs-actual summary contract; no backend summary contract or completion semantics changed.

Boundaries preserved:

- No automatic progression, load increase, deload, periodization, workout generation, recommendation behavior, nutrition, food logging, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Planned workout snapshots remain immutable.
- Actual set create/edit/delete behavior remains user-entered and backend-validated.
- Progression history remains read-only and derives from completed actual-set rows only.
- Completion remains explicitly user-triggered through the existing backend completion endpoint.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_persistence_service.py tests/test_workout_progression_history_service.py tests/test_workout_progression_history_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py tests/test_workout_preview_full_slot_rotation_v1.py tests/test_workout_preview_full_slot_rotation_quality_gate_v1.py tests/test_workout_generation_sizing_persistence_stabilization_v1.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/workout_plans.py services/workout_plan_persistence_service.py tests/test_workout_plan_persistence_service.py`
- `npm run lint`
- `npm run build`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/workout_completion_review_ux_v0_1.md`.

---

# Current State â€” Workout Set Logging UX v0.1

Current source of truth: `feature/workout-set-logging-ux-v0-1`.

Active workout milestone:

```text
Workout Set Logging UX v0.1
```

Requested status:

```text
WORKOUT_SET_LOGGING_UX_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make actual workout set logging faster and clearer while preserving the existing workout execution model and backend-owned logged-set truth.
```

Implemented scope:

- Added a backend actual-set delete path alongside the existing create/edit path.
- Added `DELETE /workout-plans/{plan_instance_id}/actual-sets/{actual_set_id}`.
- Kept actual-set delete scoped to the owning workout plan execution session and returned refreshed actual sets plus planned-vs-actual summary.
- Added frontend proxy support and typed client helpers for actual-set edit/delete.
- Updated workout exercise cards to show saved set rows, compact logged-set counts, and no-sets-yet states.
- Added inline saved-set edit controls for reps, weight, RIR, and notes.
- Added delete controls for mistaken actual sets.
- Preserved previous-performance context as read-only display.

Boundaries preserved:

- No automatic progression, load increase, deload, periodization, workout generation, recommendation behavior, nutrition, food logging, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Planned workout snapshots remain immutable.
- Actual set values remain user-entered and backend-validated.
- Progression history remains read-only and derives from completed actual-set rows only.
- Existing workout preview/select/start/log/edit/complete/history and planned-vs-actual behavior remains stable.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_persistence_service.py tests/test_workout_progression_history_service.py tests/test_workout_progression_history_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_workout_plan_persistence_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py tests/test_training_execution_summary_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/workout_plan_persistence_service.py api/routes/workout_plans.py tests/test_workout_plan_persistence_service.py`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint`
- `npm run build`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/workout_set_logging_ux_v0_1.md`.

---

# Current State â€” Workout Progression History v0

Current accepted source of truth: `main` after `ce5d316 Merge workout progression history v0`.

Accepted workout milestone:

```text
Workout Progression History v0
```

Accepted status:

```text
WORKOUT_PROGRESSION_HISTORY_V0_ACCEPTED_AND_MERGED
```

Purpose:

```text
Add compact previous-performance context to the workout flow so the user can see what they did last time for the same exercise.
```

Implemented scope:

- Added a read-only, user-scoped workout progression history service for completed planned workout executions.
- Added `POST /workout-plans/{user_id}/progression-history`.
- Summarized last completed session, recent best set, completed session count, logging quality, and no-history/limited-history states by exercise name.
- Kept public output bounded and excluded raw actual-set rows and notes.
- Added compact previous-performance display near workout preview/persisted exercise cards.
- Added a frontend proxy route, typed API helper, and TypeScript response models.

Boundaries preserved:

- No automatic progression, load increase, deload, periodization, workout generation, workout mutation, recommendation behavior, nutrition, report, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Existing workout preview/select/start/log/edit/complete/history and planned-vs-actual behavior remains stable.
- Only completed planned workout executions are used for the public history surface.
- Incomplete set logging returns limited-state messaging rather than coaching claims.

See milestone memory: `docs/project_memory/milestones/workout_progression_history_v0.md`.

---

# Current State â€” Food Logging Edit UX v0.1

Current accepted source of truth: `main` after `a2bc7b3 Merge food logging edit UX v0.1`.

Accepted nutrition logging milestone:

```text
Food Logging Edit UX v0.1
```

Accepted status:

```text
FOOD_LOGGING_EDIT_UX_V0_1_ACCEPTED_AND_MERGED
```

Purpose:

```text
Make logged canonical food correction as usable as logging by supporting grams or backend-approved serving-unit edits while preserving canonical_food_id + resolved grams as persisted truth.
```

Implemented scope:

- Extended canonical log editing to accept either grams or `serving_unit_id` + `quantity`, never both.
- Serving-unit edits resolve to grams through backend serving-unit validation and recalculate macro snapshots.
- Serving-unit edits create or update serving metadata for the existing food entry.
- Grams edits clear stale serving metadata from previously serving-unit-backed entries.
- Meal-only edits preserve existing serving metadata.
- Delete removes associated serving metadata before deleting the food entry.
- Daily canonical logs now include optional public-safe serving context when present.
- Logged Today inline edit UI now supports grams fallback, approved serving-unit selection, previous serving-unit prefill, resolved grams preview, and macro preview.

Boundaries preserved:

- No favorites, meal templates, full diary/history, barcode scanning, AI food parsing, AI suggestions, meal planning, raw-source logging, target formula, Daily Coach, report, workout, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Backend remains responsible for serving-unit resolution, canonical nutrient snapshots, ownership checks, and persistence.
- Frontend remains a compact controller/renderer and does not invent nutrition values.
- Raw source payloads remain non-public.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_log_edit_serving_units_api.py tests/test_canonical_food_log_edit_serving_units_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_nutrition_serving_unit_logging_api.py tests/test_nutrition_serving_unit_logging_service.py tests/test_food_logging_recents_api.py tests/test_food_logging_recents_service.py tests/test_nutrition_target_vs_actual_service.py tests/test_api_smoke.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py services/nutrition_serving_unit_logging_service.py services/nutrition_serving_unit_service.py services/food_logging_recents_service.py tests`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint` and `npm run build` from `frontend`
- touched-file `git diff --check`

See milestone memory: `docs/project_memory/milestones/food_logging_edit_ux_v0_1.md`.

---

# Current State â€” Food Logging Recents v0

Current accepted source of truth: `main` after `merge-food-logging-recents-v0`.

Accepted nutrition logging milestone:

```text
Food Logging Recents v0
```

Accepted status:

```text
FOOD_LOGGING_RECENTS_V0_ACCEPTED_AND_MERGED
```

Purpose:

```text
Reduce daily food logging friction by deriving recent canonical foods from existing logs and letting the user quickly reselect the last-used grams or serving-unit context.
```

Implemented scope:

- Added a user-scoped recent canonical foods service derived from `food_entries`.
- Added `GET /nutrition/{user_id}/recent-canonical-foods?limit=10`.
- Returned distinct active canonical foods ordered by most recent log entry.
- Preserved grams-only context when serving metadata is absent.
- Preserved last serving-unit ID, serving label, quantity, and resolved grams when serving metadata is present.
- Kept recent result limits bounded and public-safe.
- Added a frontend recent-foods proxy and client helper.
- Updated the food logging card with compact Recent Foods chips that prefill grams or serving-unit context while preserving the canonical logging endpoint as the write path.

Boundaries preserved:

- No favorites, meal templates, full diary/history, barcode scanning, AI food parsing, meal planning, raw source logging, nutrition target, workout, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Backend remains responsible for serving-unit resolution and nutrition snapshots.
- Recent foods are derived from existing canonical logs; no new recents persistence was added.
- Raw source payloads remain non-public.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_logging_recents_service.py tests/test_food_logging_recents_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_nutrition_serving_unit_logging_api.py tests/test_canonical_serving_unit_discovery_api.py tests/test_nutrition_target_vs_actual_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services api tests scripts`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `npm run lint` and `npm run build` from `frontend`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/food_logging_recents_v0.md`.

---

# Current State â€” Serving Unit UX v0

Current source of truth: `feature/serving-unit-ux-v0`.

Active nutrition logging milestone:

```text
Serving Unit UX v0
```

Requested status:

```text
SERVING_UNIT_UX_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Allow canonical foods to be logged by grams or by backend-approved serving units while preserving canonical_food_id + resolved grams as the persisted source of truth.
```

Implemented scope:

- Extended canonical food logging so callers may submit either grams or `serving_unit_id` + `quantity`, but not both.
- Preserved existing grams logging behavior, canonical nutrient snapshots, daily actuals, and target-vs-actual rollups.
- Kept serving-unit logging backed by reviewed serving-unit rows and provenance metadata.
- Added public serving-unit discovery aliases for frontend use while keeping the earlier serving-unit response fields stable.
- Added starter serving-unit aliases for reviewed raw chicken breast and ground beef entries.
- Updated the food logging card to offer grams plus approved serving units, show resolved grams, and log the selected unit through the canonical endpoint.

Boundaries preserved:

- No real food promotion, barcode scanning, meal planning, AI/provider path, RAG, embeddings, vector search, agent orchestration, or nutrition semantic changes were added.
- Canonical foods still persist as canonical food ID plus resolved grams in `food_entries`; serving-unit metadata remains supporting provenance.
- No DB snapshots, ZIPs, raw source payloads, or runtime reports are part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_nutrition_serving_unit_data_model_v1.py tests/test_canonical_serving_unit_discovery_api.py tests/test_nutrition_serving_unit_logging_service.py tests/test_nutrition_serving_unit_logging_api.py tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_nutrition_target_vs_actual_service.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_api_smoke.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services api tests scripts`
- `.\.venv\Scripts\python.exe -m ruff format --check` on touched Python files
- `npm run lint` and `npm run build` from `frontend`
- `git diff --check`

See milestone memory: `docs/project_memory/milestones/serving_unit_ux_v0.md`.

---

# Current State â€” Exercise Rotation Coverage v0

Current source of truth: `feature/exercise-rotation-coverage-v0`.

Active backend workout milestone:

```text
Exercise Rotation Coverage v0
```

Requested status:

```text
EXERCISE_ROTATION_COVERAGE_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Increase deterministic workout exercise coverage so preview rotation can use most equipment-compatible, generator-eligible curated catalog exercises over time while preserving safety constraints, movement balance, workout sizing, and selected-workout immutability.
```

Implemented scope:

- Added a catalog-driven workout rotation pool service that appends safe catalog candidates after existing deterministic anchor options.
- Expanded lower, push, pull, accessory, core, carry, arms, upper-back, and conditioning-compatible deterministic slots without rewriting workout templates.
- Preserved existing anchors, preview variation behavior, recent-exercise penalties, equipment filtering, unavailable-equipment filtering, duplicate-name protection, and same-workout rotation-group protection.
- Enforced avoid movements and movement restrictions against hard-coded anchors as well as catalog-expanded options.
- Kept mobility entries out of generator pools and kept internal/external rotation drills out of primary pull slots.
- Extended the exercise catalog utilization diagnostic with generator-eligible counts, full candidate names, selected exercise types, not-selected reasons, and slot-family candidate pool sizes.
- Added Exercise Rotation Coverage v0 tests and updated older utilization/eligibility expectations for the broader catalog reachability.

Diagnostic result:

```text
Pre-change local 25-variation sweep: 69 unique selected exercises.
Final local 25-variation sweep: 126 unique selected exercises.
Total active catalog exercises: 240.
Equipment-eligible home-gym exercises: 237.
Generator-eligible home-gym exercises: 224.
Equipment-eligible not in candidate options: 18.
Generator-eligible not selected in sweep: 98.
Selected movement patterns: 13.
```

The v0 target of roughly 120+ unique selected exercises was achieved without selecting mobility as an exercise type.

Boundaries preserved:

- No provider, OpenAI, Ollama, CrewAI, RAG, embeddings, vector search, agent orchestration, frontend, database schema, food catalog, nutrition/serving, clinical/rehab, periodization, progression, or 1RM changes were added.
- No exercise catalog entries were added.
- No DB, generated JSON report, snapshot, ZIP, or temporary runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_exercise_rotation_coverage_v0.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_exercise_catalog_service.py tests/test_exercise_eligibility_matrix_v1.py tests/test_exercise_catalog_utilization_specialized_movement_coverage_v1.py tests/test_workout_preview_full_slot_rotation_v1.py tests/test_workout_preview_full_slot_rotation_quality_gate_v1.py tests/test_workout_generation_sizing_persistence_stabilization_v1.py tests/test_workout_plan_service.py tests/test_workout_plan_selection_service.py tests/test_workout_plan_persistence_service.py tests/test_today_workout_route.py tests/test_today_workout_view_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services tools tests`
- `.\.venv\Scripts\python.exe -m ruff format --check services tools tests`
- `git diff --check`

---

# Current State â€” Canonical Food Bulk Catalog Builder Hardening v0.1

Current source of truth: `feature/canonical-food-bulk-catalog-builder-hardening-v0-1`.

Active backend hardening milestone:

```text
Canonical Food Bulk Catalog Builder Hardening v0.1
```

Requested status:

```text
CANONICAL_FOOD_BULK_CATALOG_BUILDER_HARDENING_V0_1_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Harden bulk canonical food catalog curation before any real promotion by preserving meaningful food qualifiers and reducing false skipped_duplicate_name results.
```

Implemented scope:

- Preserved meaningful qualifiers for common bulk catalog families before duplicate-name checks.
- Added specific display names for flour, cheese, rice, oats, tomato, butter, cream, bread, and oil variants.
- Fixed over-broad oil curation so `Anchovies, canned in olive oil` becomes `Canned anchovies`, not `Olive oil`.
- Kept raw meat/fowl/fish protection intact while preserving clearly prepared/canned/ready-to-eat eligibility.
- Kept true duplicate protection for same normalized display name plus same macro profile.
- Added fallback naming for materially different same-name rows so the builder can use a more specific second-phrase display name instead of immediately skipping.
- Extended bulk catalog tests for qualifier preservation, true duplicate skips, anchovy/oil curation, representative dry-run improvement, and idempotency regression coverage.

Boundaries preserved:

- No real promotion run is authorized or performed.
- No frontend files, food logging UI, serving picker, diary/history, admin UI, raw USDA review UI, AI parser, barcode scanner, workout, recovery, provider, RAG, embeddings, vector search, or agent orchestration changes were added.
- Raw source rows remain non-user-facing and are never logged directly.
- Nutrients are copied only from existing raw source records; no nutrition values are fabricated.
- No DB, USDA dataset, CSV, ZIP, generated report, or runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_bulk_catalog_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_starter_set_service.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services scripts tests`
- touched-file `.\.venv\Scripts\python.exe -m ruff format --check ...`
- `git diff --check`

---

# Current State â€” Canonical Food Bulk Catalog Builder v0

Current source of truth: `feature/canonical-food-bulk-catalog-builder-v0`.

Active backend implementation milestone:

```text
Canonical Food Bulk Catalog Builder v0
```

Requested status:

```text
CANONICAL_FOOD_BULK_CATALOG_BUILDER_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Promote many safe, practical USDA Foundation raw source rows into searchable/loggable canonical foods through deterministic inventory, category safety, dry-run, report, and idempotent promotion tooling.
```

Implemented scope:

- Added `scripts/inspect_usda_food_catalog_sources.py` for read-only source inventory reports across raw source rows, macro coverage, canonical counts, and optional FDC CSV data type/category counts.
- Enriched FDC directory import with optional `food_category.csv` lookup so imported `foundation_food` rows can store readable category names.
- Added `services/food_bulk_catalog_service.py` for category-gated bulk candidate selection and promotion through the existing raw-source promotion service.
- Added `scripts/promote_canonical_food_bulk_catalog.py` with `--db-path`, `--dry-run`, `--source-name`, `--include-data-types`, `--include-categories`, `--exclude-categories`, `--limit`, `--max-promotions`, and `--report-path`.
- Added report buckets for `promoted`, `already_promoted`, `skipped_missing_macros`, `skipped_unsafe_raw`, `skipped_category`, `skipped_duplicate_name`, `skipped_ambiguous`, and `skipped_invalid`.
- Added duplicate-name protection so broad catalog runs do not overwrite existing/manual canonical nutrients when multiple source rows curate to the same display name.
- Preserved raw produce eligibility and skipped raw/not-clearly-prepared meat, fowl, and fish rows.

Boundaries preserved:

- No frontend changes, food logging UI changes, serving picker, food diary/history, admin curation UI, raw USDA review UI, AI food parser, barcode scanner, workout, recovery, provider, RAG, embeddings, vector search, or agent orchestration was added.
- USDA imports still default to `foundation_food`; no FNDDS, SR Legacy, branded, sample, sub-sample, market acquisition, or agricultural acquisition expansion was added.
- Raw source rows remain non-user-facing and are never logged directly.
- Nutrients are copied only from existing raw source records; no nutrition values are fabricated.
- No DB, USDA dataset, CSV, ZIP, generated report, or runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_bulk_catalog_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_starter_set_service.py tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services scripts tests`
- `.\.venv\Scripts\python.exe -m ruff format --check services scripts tests`
- `git diff --check`

---

# Current State â€” Canonical Food Starter Set Promotion Pack v0

Current source of truth: `feature/canonical-food-starter-set-promotion-pack-v0`.

Active backend implementation milestone:

```text
Canonical Food Starter Set Promotion Pack v0
```

Requested status:

```text
CANONICAL_FOOD_STARTER_SET_PROMOTION_PACK_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Expand practical everyday canonical food availability by promoting high-confidence starter foods from existing raw source records without importing datasets or fabricating nutrition values.
```

Implemented scope:

- Added a reviewable 67-item starter-set definition across proteins, carbs/starches, fruits, vegetables, dairy/fats, and common extras.
- Added deterministic matching against existing `raw_food_source_records`, defaulting to USDA `foundation_food` rows with macro data.
- Added conservative report buckets: `matched`, `skipped_missing`, `skipped_ambiguous`, `skipped_raw_only`, and `already_promoted`.
- Added `scripts/promote_canonical_food_starter_set.py` with required `--db-path`, `--dry-run`, optional `--limit`, `--include-categories`, and `--report-path`.
- Reused the existing raw-source promotion service for canonical food creation/reuse, aliases, macro nutrient sync, and source provenance.
- Preserved idempotency by reporting existing primary source links as `already_promoted`.
- Preserved raw produce eligibility while skipping raw/uncooked meat, fowl, and fish as everyday starter entries.

Boundaries preserved:

- No full USDA import expansion, new dataset type, admin UI, manual review UI, serving picker, food diary/history, edit/delete change, food logging UI change, workout change, recovery change, AI food parsing, barcode scanning, image recognition, RAG, embeddings, vector search, or agent orchestration was added.
- Raw source rows remain non-user-facing and are never logged directly.
- Nutrients are copied only from existing raw source records; no nutrition values are fabricated.
- No DB, USDA dataset, CSV, ZIP, generated report, or runtime artifact is part of this milestone.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_starter_set_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services scripts tests`
- `.\.venv\Scripts\python.exe -m ruff format --check services scripts tests`
- `git diff --check`

---

# Current State â€” Edit/Delete Logged Food v0

Current accepted baseline:

```text
53c559a Merge food log grouping and workout prose cleanup v0
```

Active full-stack implementation milestone:

```text
Edit/Delete Logged Food v0
```

Requested status:

```text
EDIT_DELETE_LOGGED_FOOD_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add safe edit/delete support for today's logged canonical foods while preserving backend-owned nutrition truth and compact Today UI scope.
```

Implemented scope:

- Added `PATCH /nutrition/{user_id}/canonical-logs/{entry_id}` for editing grams and meal type.
- Added `DELETE /nutrition/{user_id}/canonical-logs/{entry_id}` for deleting one canonical logged-food entry.
- Added backend service helpers that require `entry_id` and `user_id`, with optional selected-date guards.
- Recalculated stored macro snapshots when grams change so canonical logs and canonical totals reflect edits.
- Preserved missing macro values as `null` and explicit zero macro values as `0`.
- Preserved canonical food identity; edit does not change canonical food, food name, or entry date.
- Delete removes only the owned `food_entries` row and does not delete canonical foods, nutrients, aliases, or source links.
- Added frontend proxy/helper support for PATCH and DELETE.
- Added compact inline `Edit`, `Save`, `Cancel`, and two-step `Delete` controls to the grouped `Logged today` list.
- Refreshed the logged-food list and server-rendered Today nutrition after edit/delete through the existing local event plus `router.refresh()`.

Ownership and validation behavior:

- Wrong-user edits/deletes return a clean not-found response.
- Missing entry IDs return a clean not-found response.
- Selected-date mismatch returns a clean not-found response when the frontend sends the date guard.
- Invalid grams are rejected.
- Meal type is normalized/validated to `breakfast`, `lunch`, `dinner`, `snack`, or `other`.

Boundaries preserved:

- No full food diary/history, multi-date editor, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image recognition, raw USDA source review UI, canonical promotion UI, workout changes, recovery changes, or broad Today redesign was added.
- Raw USDA/source rows are not logged or mutated directly.
- Backend nutrition actuals remain backend-owned through existing `food_entries` and nutrient rollup paths.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State â€” Today Food Log Grouping + Workout Prose Cleanup v0

Current accepted baseline:

```text
ced70d0 Merge Today logged foods read-only list v0
```

Active frontend implementation milestone:

```text
Today Food Log Grouping + Workout Prose Cleanup v0
```

Requested status:

```text
TODAY_FOOD_LOG_GROUPING_WORKOUT_PROSE_CLEANUP_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make the Today logged-food and Workout detail surfaces more compact, grouped, and data-first without changing backend contracts.
```

Implemented scope:

- Grouped the read-only `Logged today` food list by normalized meal type.
- Rendered known meal types as Breakfast, Lunch, Dinner, and Snack; missing or unknown values render as Other.
- Hid empty meal groups while preserving the compact empty-day state.
- Kept explicit zero macro values visible and omitted missing macro values from compact rows.
- Added compact per-meal item counts and a bounded logged-food scroll area for longer days.
- Put `Logged today` and `Today's Workout` side-by-side in the Today primary column on wide desktop viewports.
- Preserved mobile order as Nutrition, Log Food, Logged today, Today's Workout, Recovery.
- Removed low-value deterministic prose from the Workout page hero and Session Status area.
- Removed the Workout page Session Notes card rather than relocating generic deterministic prose.
- Changed Workout detail exercise cards to a two-column desktop grid and single-column mobile layout.
- Preserved existing active workout logging controls.

Boundaries preserved:

- Backend behavior and contracts were not changed.
- Food search, food logging, logged-food refresh, Nutrition actual refresh, Today workout detail navigation, active workout logging, and Recovery Check-In behavior were not intentionally changed.
- No edit/delete food logs, full food diary/history, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, provider behavior, recovery logic changes, nutrition calculation changes, food search changes, or AI workout prose generation were added.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State â€” Today Logged Foods Read-Only List v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active full-stack implementation milestone:

```text
Today Logged Foods Read-Only List v0
```

Requested status:

```text
TODAY_LOGGED_FOODS_READONLY_LIST_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Make today's food logging loop visible by showing a compact read-only list of canonical foods logged for the selected user/date near Nutrition and Log Food.
```

Implemented scope:

- Added a read-only backend endpoint at `GET /nutrition/{user_id}/canonical-logs?date=YYYY-MM-DD`.
- Added a nutrition service helper that reads only canonical food entries for the selected user/date.
- Returned stored macro snapshots from `food_entries` so missing macros remain `null` and explicit zero values remain `0`.
- Preserved canonical food IDs and friendly food names without exposing raw USDA payloads or raw source identifiers.
- Added a compact `Logged today` component under Log Food on the Today page.
- Kept the left-column order as Nutrition, Log Food, Logged today, Today's Workout.
- Preserved `router.refresh()` after food logging so Nutrition actuals and the logged-food list reload together.
- Added a clean empty state: `No foods logged yet today.`

Boundaries preserved:

- No edit/delete food log flow was added.
- No food history across dates, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image food recognition, raw USDA review UI, or canonical promotion UI was added.
- Nutrition calculations, canonical logging behavior, workout, recovery, provider behavior, and user routing were not changed.
- Full USDA datasets, generated DB files, ZIPs, CSVs, and runtime artifacts remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check api/routes/nutrition.py services/nutrition_service.py tests/test_canonical_food_logging_api.py`
- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State â€” Canonical Food Search Result Curation v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Canonical Food Search Result Curation v0
```

Requested status:

```text
CANONICAL_FOOD_SEARCH_RESULT_CURATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Improve canonical food search result quality so daily food logging returns practical, human-friendly canonical food results instead of raw USDA-style names.
```

Implemented scope:

- Added a deterministic canonical display-name curation helper for public search labels and raw-source promotion.
- Kept canonical search on `canonical_food_id`; raw USDA source rows still do not become direct log targets.
- Preserved source identity through existing source links and compact `source` summaries.
- Added conservative practical labels such as `Chicken breast`, `Hummus`, `2% milk`, `Egg`, `Oatmeal`, and `Grape tomatoes`.
- Preserved raw meat/fowl/fish truth by keeping explicit raw names visibly raw, such as `Chicken breast, raw`.
- Added a default search-ranking penalty for raw meat/fowl/fish canonical foods unless the user explicitly searches `raw` or `uncooked`.
- Kept non-meat raw foods, such as raw tomatoes, eligible for normal search results.
- Added starter curation aliases during seed so practical names can be found without changing nutrient values.
- Adjusted oatmeal seeding so `oatmeal` prefers cooked oatmeal while `oats` still finds dry oats.

Boundaries preserved:

- No frontend files were changed.
- No canonical logging behavior, nutrition rollup behavior, serving-unit behavior, workout, recovery, provider, or user-routing behavior changed.
- No full USDA taxonomy, admin curation UI, raw source review UI, food diary/history, edit/delete logs, serving picker, meal builder, barcode scanner, AI food parser, or image recognition was added.
- Nutrient values, missing macro behavior, explicit zero macro behavior, and source payload privacy remain unchanged.
- Full USDA datasets, generated SQLite DBs, ZIPs, CSVs, and runtime artifacts remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py tests/test_food_normalization_service.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py`

---

# Current State â€” Today Workout Detail UX Refinement v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Today Workout Detail UX Refinement v0
```

Requested status:

```text
TODAY_WORKOUT_DETAIL_UX_REFINEMENT_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Refine the Today and Workout detail screens after the main-loop density polish so the daily workout loop is more compact, data-rich, and less repetitive.
```

Implemented scope:

- Reworked the Today page into independent desktop column stacks so Today's Workout sits directly below Log Food instead of being pushed down by the taller Recovery Check-In card.
- Preserved mobile Today order as Nutrition, Log Food, Today's Workout, Recovery Check-In.
- Reused existing current-workout payload data to show compact Today exercise rows with set completion, reps, weight, and RIR when actual set data is available.
- Kept planned-only Today workout rows compact with planned set and rep detail.
- Tightened the Workout detail hero/status card into a compact Session Status card.
- Removed redundant completed-workout status copy from the Workout detail hero/status area.
- Moved Execution Summary above Session Notes and gave it a more prominent visual treatment.
- Kept Session Notes available below Execution Summary.

Boundaries preserved:

- Backend behavior and contracts were not changed.
- Nutrition logging, canonical food search/logging, recovery scoring, workout lifecycle, workout logging/completion, provider behavior, and user routing were not changed.
- No food diary/history, edit/delete flow, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, USDA curation UI, dashboard layout framework, or collapsible-card system was added.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`
- `cd C:\projects\fitness_ai`
- `git diff --check`

---

# Current State â€” Today Main Loop Density Polish v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Today Main Loop Density Polish v0
```

Requested status:

```text
TODAY_MAIN_LOOP_DENSITY_POLISH_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Polish the Next.js Today page into a compact operator dashboard for the real daily loops: Nutrition / Log Food, Workout summary, and Recovery Check-In.
```

Implemented scope:

- Removed the giant green Next Action card from prime Today page real estate.
- Moved Nutrition and Log Food to the top of the Today layout.
- Kept Nutrition and Log Food as adjacent existing components instead of adding a new combined nutrition system.
- Compacted the Food Logging selected state so selected food appears once, search results hide after selection until the query changes, macro preview is inline, and success/error messages are small.
- Converted completed workout state into a compact summary using existing Today workout payload data.
- Removed redundant completed-workout instructional copy from the Today summary surface.
- Preserved Recovery Check-In behavior while removing the internal-ish Recovery eyebrow.
- Preserved mobile order as Nutrition / Log Food, Workout, then Recovery.

Boundaries preserved:

- No backend behavior, nutrition aggregation, canonical logging, recovery scoring, workout lifecycle, provider, or user-routing behavior changed.
- No food diary/history, edit/delete flow, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image recognition, dashboard state manager, or collapsible-card framework was added.
- Full USDA datasets, generated DB files, CSVs, ZIPs, and runtime artifacts remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`

---

# Current State â€” Next.js Canonical Food Logging UI v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Next.js Canonical Food Logging UI v0
```

Requested status:

```text
NEXTJS_CANONICAL_FOOD_LOGGING_UI_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add the first small Next.js food logging surface so users can search canonical foods, enter grams, log food, and see Today nutrition actuals refresh through the existing backend contract.
```

Implemented scope:

- Added a compact `FoodLoggingCard` near the existing Today Nutrition card.
- Added Next.js proxy routes for canonical food search and canonical food logging.
- Reused the existing backend canonical search route and canonical logging route without exposing raw USDA rows.
- Added client-side macro preview from per-100g canonical nutrient data.
- Refreshed Today after save with `router.refresh()` so Nutrition actuals update through the existing Today contract.
- Preserved current `user_id` and date selection when searching and logging food.
- Added a backend runtime SQLite schema-init hotfix so older local `food_entries` tables receive canonical logging columns on FastAPI startup without deleting existing DB data.

Boundaries preserved:

- No serving picker, meal builder, barcode flow, AI food parser, favorites, recent foods, food diary history, or raw USDA review UI was added.
- No backend nutrition aggregation path was changed.
- No workout, recovery, provider, or user-switcher behavior was changed.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`

---

# Current State â€” Today Nutrition Logged Totals Integration v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Today Nutrition Logged Totals Integration v0
```

Requested status:

```text
TODAY_NUTRITION_LOGGED_TOTALS_INTEGRATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Connect canonical food logging to the existing Today nutrition card by proving the Today backend contract reflects canonical food log actuals through the shared target-vs-actual path.
```

Implemented scope:

- Confirmed the existing Today backend already sources nutrition actuals from `build_target_vs_actual_nutrition_summary(...)`.
- Confirmed canonical food logs already flow into that path through `food_entries`, so no second Today-specific canonical rollup was added.
- Added Today service and Today route integration tests that log canonical foods and verify the Today nutrition payload updates by the expected macro delta exactly once.
- Added focused Today tests for user/date separation and clean no-log-day behavior.
- Preserved the existing compact frontend Nutrition Macro Card without redesign or code changes.

Boundaries preserved:

- No food search UI, food logging UI, serving picker, meal builder, barcode flow, or AI food parser was added.
- No raw USDA source identifier became a Today input.
- No workout, recovery, provider, USDA import, or canonical-promotion behavior was changed.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py tests/test_daily_driver_contract_models.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/daily_driver_today_service.py tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/daily_driver_today_service.py tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py`

---

# Current State â€” Next.js Today Workout UI Polish v0

---

# Current State â€” Canonical Food Logging Backend v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Canonical Food Logging Backend v0
```

Requested status:

```text
CANONICAL_FOOD_LOGGING_BACKEND_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add the backend write path that logs canonical foods by canonical_food_id and grams so daily nutrition tracking can consume the curated canonical food pipeline without exposing raw USDA rows directly.
```

Implemented scope:

- Hardened the existing canonical logging route at `POST /nutrition/{user_id}/log-canonical`.
- Preserved the canonical-only logging rule with `canonical_food_id` as the user-facing identifier.
- Persisted canonical linkage and canonical macro snapshots on `food_entries`.
- Preserved grams as the logging calculation source of truth.
- Added a canonical-only daily macro rollup helper plus a small read route for daily rollup totals.
- Kept the existing legacy nutrition actuals path working through the current write-through mirror behavior.
- Added focused tests for persisted canonical linkage, invalid input, missing-vs-zero macro behavior, user/date separation, and rollup output.

Boundaries preserved:

- No Next.js UI, food search UI, meal builder, serving-size UX, barcode flow, or AI food parser was added.
- No raw USDA identifier became the normal logging path.
- No workout, recovery, provider, or user-switcher behavior was touched.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_canonical_food_logging_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py tests/test_food_canonical_promotion_service.py tests/test_food_normalization_service.py tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m ruff check database.py services/nutrition_service.py api/routes/nutrition.py tests/test_canonical_food_logging_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check database.py services/nutrition_service.py api/routes/nutrition.py tests/test_canonical_food_logging_api.py`

---

# Current State â€” Canonical Food Search API v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
Canonical Food Search API v0
```

Requested status:

```text
CANONICAL_FOOD_SEARCH_API_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Add a tightly scoped backend search API for canonical foods only so future food logging/search stays on curated canonical foods and not raw USDA source rows.
```

Implemented scope:

- Hardened the canonical food search route at `GET /foods/canonical/search`.
- Preserved canonical-only search behavior through `canonical_foods` and alias search.
- Added compact default source summary output when a canonical food has a linked source row.
- Preserved macro summaries from canonical nutrient rows only.
- Made empty search queries return a safe empty result.
- Kept deterministic matching order and tightened alias ordering.
- Added focused tests for promoted canonical foods, compact source identity, and missing-vs-zero macro behavior.

Boundaries preserved:

- No food logging backend or UI was added.
- No raw USDA direct-search endpoint was added.
- No meal builder, barcode, AI food parsing, workout, recovery, or provider behavior was touched.
- Full USDA datasets and generated DB files remain local-only artifacts.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_search_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_promotion_service.py tests/test_food_normalization_service.py tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/food_normalization_service.py services/food_canonical_promotion_service.py api/routes/food_canonical_search.py tests/test_food_canonical_search_api.py`

---

# Current State â€” USDA Raw Source Canonical Promotion v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Raw Source Canonical Promotion v0
```

Requested status:

```text
USDA_RAW_SOURCE_CANONICAL_PROMOTION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Create a narrow backend bridge from USDA raw source rows into the existing curated canonical food tables so future food search/logging stays canonical and not raw-source-backed.
```

Implemented scope:

- Added a focused backend review helper for listing promotable USDA raw source rows.
- Defaulted promotion-review queries to `foundation_food`, with override support for review-mode inclusion of non-default USDA hierarchy rows.
- Added a deterministic promotion path from `raw_food_source_records` into `canonical_foods`, `canonical_food_aliases`, `canonical_food_nutrients`, and `food_source_links`.
- Preserved USDA source identity through `source_name`, `source_record_id`, and the linked internal raw source record id.
- Reused existing canonical-food tables and upsert behavior instead of adding a parallel canonical subsystem.
- Preserved missing macro values as absent and explicit `0` values as `0` during canonical nutrient sync.
- Added an opt-in scratch-database CLI for promotion smoke and focused service tests for idempotency, source-link preservation, review filtering, and macro handling.

Boundaries preserved:

- No food search UI, food logging UI, barcode flow, meal builder, or AI food parsing was added.
- Raw USDA rows still do not become the direct user-facing search path.
- Full USDA datasets and generated DB files remain local-only artifacts.
- Frontend, workout, recovery, and provider behavior were not touched.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_food_canonical_promotion_service.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_normalization_service.py tests/test_food_canonical_search_api.py tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m ruff check models/food_normalization_models.py services/food_canonical_promotion_service.py scripts/promote_usda_raw_food.py tests/test_food_canonical_promotion_service.py`
- `.\.venv\Scripts\python.exe -m ruff format --check models/food_normalization_models.py services/food_canonical_promotion_service.py scripts/promote_usda_raw_food.py tests/test_food_canonical_promotion_service.py`

---

# Current State â€” USDA Import Loggable Foundation Filter v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Import Loggable Foundation Filter v0
```

Requested status:

```text
USDA_IMPORT_LOGGABLE_FOUNDATION_FILTER_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Hotfix the USDA real-dataset directory importer so extracted FoodData Central CSV imports default to loggable top-level foundation_food rows instead of mostly sample/subsample/acquisition hierarchy rows.
```

Implemented scope:

- Preserved the existing simple `--input` USDA-style CSV import path.
- Preserved extracted FoodData Central `--fdc-dir` import support.
- Defaulted real FDC directory imports to `foundation_food`.
- Added `--include-data-types` override support for review-mode imports.
- Moved `--limit` application to after FDC `data_type` filtering.
- Preserved `source_record_id` as the USDA FDC ID and kept `fdc_id` in `source_payload_json`.
- Preserved missing joined macro nutrients as `NULL` / `None` while keeping explicit USDA zero values as `0`.
- Skipped negative joined macro values so malformed USDA macro rows do not abort the import or store negative macros.
- Added focused real-shape fixture coverage for default filtering, override behavior, post-filter limits, and null-vs-zero macro handling.

Boundaries preserved:

- No food search UI, food logging UI, or canonical-food promotion flow was added.
- Full USDA datasets and generated DB files remain local-only artifacts.
- Backend remains the owner of imported source metadata and macro truth.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_normalization_service.py tests/test_food_canonical_search_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`
- `.\.venv\Scripts\python.exe -m ruff format --check services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Next.js Today Workout UI Polish v0
```

Requested status:

```text
NEXTJS_TODAY_WORKOUT_UI_POLISH_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Polish the existing Next.js Today and Workout screens so they feel tighter and more useful for daily use without changing backend workout, recovery, nutrition, or user-routing behavior.
```

Implemented scope:

- Tightened the Today header into a shorter card with long readable date formatting and inline user selection.
- Removed normal UI clutter that labeled users as `Real user`, `QA / Test User`, or `(Test)`.
- Reworked the Today workout summary card to use plain app language, remove generated workout titles from the summary surface, and promote the workout-detail action.
- Tightened the Workout page header and removed backend-ish preview wording.
- Simplified the Workout experience layout by removing `Preview Details`, shrinking the summary area, and moving preview actions to the top of the exercises card.
- Kept session notes smaller and conditional so low-value note content no longer creates a large side panel.

Boundaries preserved:

- No backend behavior or workout contracts were changed.
- URL `user_id` remains the source of truth.
- Workout preview/select/start/logging/completion flows remain on their existing API and component path.
- Recovery Check-In and Nutrition Macro Card behavior remain unchanged.

Validation target:

- `cd C:\projects\fitness_ai\frontend`
- `npm run lint`
- `npm run build`

---

# Current State â€” USDA Real Dataset Adapter Smoke v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Real Dataset Adapter Smoke v0
```

Requested status:

```text
USDA_REAL_DATASET_ADAPTER_SMOKE_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Extend the local USDA import foundation so the repo can ingest the real extracted FoodData Central CSV directory shape while keeping nutrition scope small and preserving the current raw-source boundaries.
```

Implemented scope:

- Reused the existing USDA raw-source importer foundation and shared upsert path into `raw_food_source_records`.
- Added a real FoodData Central directory importer that joins `food.csv`, `food_nutrient.csv`, and `nutrient.csv`, with optional `branded_food.csv` metadata.
- Preserved the original simple fixture CSV import path so current tiny-fixture workflows still work.
- Added defensive macro mapping from USDA nutrient definitions for calories, protein, carbs, and fat.
- Added CLI support for `--fdc-dir` and optional `--limit` for smoke-sized local imports.
- Added a tiny checked-in extracted-directory fixture plus focused tests covering joins, optional metadata omission, rerun idempotence, row limiting, and CLI directory import.

Boundaries preserved:

- No fake food database, meal database, AI food parser, or long-term nutrition logging system was added.
- Canonical foods and user-facing food search/logging remain unchanged.
- Full USDA data extracts remain local-only and ignored by Git.
- Backend remains the owner of imported source metadata and normalized macro truth.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_food_normalization_service.py tests/test_food_canonical_search_api.py -q`
- `.\.venv\Scripts\python.exe -m ruff check models/usda_food_data_models.py services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`
- `.\.venv\Scripts\python.exe -m ruff format --check models/usda_food_data_models.py services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`

---

# Current State â€” USDA Food Data Import Foundation v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active backend implementation milestone:

```text
USDA Food Data Import Foundation v0
```

Requested status:

```text
USDA_FOOD_DATA_IMPORT_FOUNDATION_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Create a repeatable local USDA FoodData Central import foundation that stores USDA-backed raw food source rows locally without committing full datasets or changing user-facing food logging behavior yet.
```

Implemented scope:

- Reused the existing two-layer nutrition catalog architecture built around `raw_food_source_records` and canonical foods.
- Extended `raw_food_source_records` to preserve USDA-ready metadata including `data_type`, `gtin_upc`, serving metadata, normalized per-100g macros, and `import_batch`.
- Added a deterministic USDA CSV importer service that validates required columns, preserves `fdc_id`, upserts by `source_name + source_record_id`, and stores source payload metadata locally.
- Added a CLI importer at `scripts/import_usda_food_data.py` with optional scratch DB override support.
- Added a tiny checked-in USDA-style fixture for tests only.
- Added focused tests covering schema expansion, fixture import, optional-field handling, idempotent re-import behavior, invalid input handling, and CLI help.
- Added ignored local USDA data paths so full source downloads stay out of Git.

Discovered existing nutrition persistence:

- Legacy nutrition actuals still read through `foods`, `food_nutrients`, and `food_entries`.
- App-facing search/logging uses curated canonical food tables plus source-link metadata.
- A staged catalog importer already existed under `tools/`, but it writes review artifacts only and does not populate the local database.
- This milestone adds the first repeatable local database import path for USDA-backed source rows.

Boundaries preserved:

- Canonical app-facing foods remain curated and unchanged by this importer.
- No food logging UI, food search UI, meal builder, barcode flow, AI food parsing, or provider behavior was added.
- No full USDA dataset, archive, or generated SQLite database was committed.
- Backend remains the owner of source metadata, macro normalization, and future catalog promotion boundaries.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_usda_food_data_import.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_daily_driver_contract_models.py tests/test_daily_driver_routes.py tests/test_daily_driver_today_service.py -q`
- `.\.venv\Scripts\python.exe -m ruff check models/food_normalization_models.py models/usda_food_data_models.py services/food_normalization_service.py services/usda_food_data_import_service.py scripts/import_usda_food_data.py tests/test_usda_food_data_import.py`

---

# Current State â€” Next.js Nutrition Macro Card v0

Current accepted baseline:

```text
187e433 main_merge-platform-north-star-future-stack-canonicalization-v1
```

Active frontend implementation milestone:

```text
Next.js Nutrition Macro Card v0
```

Requested status:

```text
NEXTJS_NUTRITION_MACRO_CARD_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Expose a small nutrition status surface on the Next.js Today page by reusing existing backend-owned nutrition targets and logged macro actuals without introducing a new food logging system.
```

Implemented scope:

- Reused the existing backend-owned Today contract and nutrition target-vs-actual service as the source of nutrition truth.
- Extended the Today nutrition summary to expose carbohydrate and fat targets plus logged carbohydrate and fat actuals alongside calories and protein.
- Added a compact Next.js Nutrition Macro Card for Today that shows calories, protein, carbs, and fat with a simple status line.
- Added a clean empty-state message when no nutrition has been logged yet for the selected user/date.
- Preserved `user_id` routing through the existing Today query flow.
- Added focused contract, route, and service test coverage for the expanded nutrition summary.

Explicit deferral:

- Manual macro total entry/update was deferred in this milestone.
- The repo has nutrition logging routes for canonical foods/servings, but it does not have a small existing backend path for direct daily macro-total persistence.
- No fake food database, meal database, AI food parser, or parallel nutrition write model was added.

Boundaries preserved:

- Backend remains the owner of nutrition targets, logging actuals, comparisons, and safe wording boundaries.
- No nutrition target logic was moved into the frontend.
- No Streamlit nutrition changes were added.
- No USDA import, searchable foods table, meal builder, barcode flow, or long-term nutrition logging architecture was added.
- No provider, RAG, vector, or agent behavior was added.

Validation target:

- `.\.venv\Scripts\python.exe -m pytest tests/test_daily_driver_contract_models.py tests/test_daily_driver_routes.py tests/test_daily_driver_today_service.py -q`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

---

# Current State â€” Workout Generation + Today Workout View v0

Current accepted baseline:

```text
9192863 Merge nextjs mobile today shell v0
```

Active frontend implementation milestone:

```text
Workout Generation + Today Workout View v0
```

Requested status:

```text
WORKOUT_GENERATION_TODAY_VIEW_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Expose the existing backend-owned workout generation and planned-workout flow through the Next.js daily-driver frontend so normal daily workout viewing no longer depends on Streamlit.
```

Implemented scope:

- Inspected and reused the existing workout planning path built around `services/workout_daily_state_service.py`, `services/workout_plan_persistence_service.py`, `services/workout_plan_service.py`, `api/routes/workout_plans.py`, and the existing Streamlit Workout/Today wiring.
- Added a typed backend workout detail contract at `GET /api/today/workout`.
- Added `models/today_workout_view_models.py` and `services/today_workout_view_service.py`.
- Reused current-day persisted workout execution state when it exists.
- Reused existing deterministic workout generation as a read-only preview when no current-day persisted plan exists.
- Added focused backend tests for the new workout contract, service, and route.
- Added frontend types and API client support for the workout detail contract.
- Added a new Next.js route at `frontend/src/app/today/workout/page.tsx`.
- Wired the Today Workout card to the workout detail page.
- Wired the Next Action card to the workout detail page when the next action is workout-related.
- Preserved mobile stacked rendering while adding a practical desktop workout detail layout.

Files changed:

- `api/routes/daily_driver.py`
- `models/today_workout_view_models.py`
- `services/today_workout_view_service.py`
- `tests/test_today_workout_view_models.py`
- `tests/test_today_workout_view_service.py`
- `tests/test_today_workout_route.py`
- `frontend/src/app/page.tsx`
- `frontend/src/app/today/workout/page.tsx`
- `frontend/src/components/NextActionCard.tsx`
- `frontend/src/lib/dailyDriverApi.ts`
- `frontend/src/lib/todayWorkoutApi.ts`
- `frontend/src/types/todayWorkout.ts`

Boundaries preserved:

- Backend remains the owner of readiness, workout, nutrition, and next-action truth.
- No backend truth was invented in the frontend.
- No auth, hosting, sync, or multi-user work was added.
- No PostgreSQL work was added.
- No workout logging or nutrition logging was added.
- No provider execution, OpenAI, Ollama, or CrewAI work was added.
- No raw provider internals are exposed in the UI.
- No Markdown rendering or rich-text rendering was added for coach note.
- No Streamlit redesign or Streamlit removal was added.
- No backend Python write-path behavior was added for workout logging or selection.
- No parallel frontend workout engine was created.

Validation recorded:

- `git diff --check`
- targeted `ruff check` on touched Python files
- targeted `black --check` on touched Python files
- `py_compile` on touched Python files
- `python -m pytest tests/test_daily_driver_contract_models.py tests/test_daily_driver_today_service.py tests/test_daily_driver_routes.py tests/test_today_workout_view_models.py tests/test_today_workout_view_service.py tests/test_today_workout_route.py tests/test_workout_daily_state_lifecycle_v1.py -q`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

Open limitations:

- This milestone exposes workout viewing only. It does not add full workout logging controls to Next.js.
- The preview path is read-only and uses existing deterministic workout generation without mutating workout lifecycle state.
- Linux runtime-box manual smoke is still required for final runtime confirmation outside this Windows implementation pass.

Reference-only continuity anchors remain preserved:

```text
Project Memory Alignment + North Star Architecture v1
feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
reference-only
No provider may run on normal Today page load
Provider Narrative QA Matrix v2
Daily Coach Same-Session Approved Preview Bridge v1 Retry
Same-Session Bridge Runtime QA v1
Daily Coach Narrative Product Voice Polish v1
Daily Coach Narrative Product Voice Runtime QA v1
PASS_WITH_NOTE
sound right and be right
Local Developer Command Menu Audit + Repo-Owned Commands v1
scripts/fitness_commands.ps1
Local Command Menu App Runtime Correction v1
Linux is the canonical
wapp
Daily Coach Async Service Shell / No Worker v1
service shell only
no provider execution added
```

---

# Current State â€” Daily Driver Core Contract v0

Current accepted baseline:

```text
df2a56f Merge daily coach gpt family human voice trial v1
```

Active backend implementation milestone:

```text
Daily Driver Core Contract v0
```

Requested status:

```text
DAILY_DRIVER_CORE_CONTRACT_V0_IMPLEMENTATION_COMPLETE_READY_FOR_ARCHITECTURE_REVIEW
```

Purpose:

```text
Create the first backend-owned daily-driver Today contract so the app can answer what to do today without requiring provider calls or a frontend rebuild.
```

Implemented scope:

- Added typed Daily Driver contract models for readiness, workout, nutrition, next action, coach note, and the Today response.
- Added a deterministic `build_daily_driver_today_response()` service that composes existing backend-owned recovery, workout, nutrition, and next-action facts.
- Added a minimal `GET /api/today` route with `user_id` and `date` inputs.
- Added focused model, service, and route tests for the new contract.
- Kept `coach_note` optional and disabled by default for v0.
- Preserved graceful fallback behavior through `data_gaps` and `limitations` when some daily data is sparse.

Boundaries preserved:

- SQLite remains the current data store.
- No PostgreSQL work was added.
- No auth, hosting, sync, or multi-user work was added.
- No Next.js or frontend-shell work was added.
- No Streamlit redesign was added.
- No provider expansion or provider promotion was added.
- No OpenAI, Ollama, or CrewAI call is required for the Today contract.
- No raw provider internals are exposed in user-facing Today fields.
- No Markdown is allowed in product-facing coach note text.
- Backend remains the owner of readiness, workout, nutrition, and next-action truth.

---

# Current State â€” Daily Coach GPT Family Human Voice Trial v1

Current accepted baseline:

```text
05313fd Merge daily coach human voice prompt contract v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_05313fd_main_merge-daily-coach-human-voice-prompt-contract-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Human Voice Prompt Contract v1
```

Active backend implementation milestone:

```text
Daily Coach GPT Family Human Voice Trial v1
```

Requested status:

```text
DAILY_COACH_GPT_FAMILY_HUMAN_VOICE_TRIAL_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Use the accepted human-editable Daily Coach prompt preview lane to compare GPT-family model output against the same raw backend provider-preview payload.
```

Implemented scope:

- Added a developer-only OpenAI/GPT-family provider path for the human voice prompt preview lane.
- Added a multi-model comparison tool at `tools/dev_daily_coach_gpt_family_human_voice_trial.py`.
- Extended `tools/dev_daily_coach_human_voice_prompt_preview.py` with explicit `--provider openai` support.
- Preserved `--provider ollama` and `--mock-output` developer smoke behavior.
- Model IDs are CLI-configurable and not hardcoded as final truth.
- `OPENAI_API_KEY` is read from the environment and must not be printed.
- OpenAI Responses API calls send only `model` and `input`.
- The provider input remains the human-editable prompt file plus `RAW_BACKEND_PAYLOAD_JSON` from the raw provider-preview payload.
- Multi-model trials continue after one model fails.
- Optional trial artifacts are written only when `--output-dir` is explicitly provided.

Project/product boundaries:

- Daily Coach Human Voice Prompt Contract v1 is the accepted baseline.
- The human-editable prompt remains user-owned.
- The raw provider-preview payload remains the data source.
- OpenAI/GPT-family output is raw trial evidence only.
- No model is promoted.
- No output is persisted by default.
- No output reaches Today UI.
- No output becomes Daily Coach Note public copy.
- No Daily Next Action behavior changes.
- No API/schema/migration/persistence/report/recommendation behavior changes.
- No OpenAI behavior is enabled outside explicit developer CLI.

Strong non-goals preserved:

```text
normal Today provider calls
Today UI
Streamlit UI layout
API routes
database schema
migrations
persistence behavior
report behavior
recommendation behavior
Daily Next Action selection logic
Daily Coach Note public copy
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
provider promotion
model approval
RAG/vector/agent behavior
CrewAI behavior
OpenAI behavior outside explicit developer CLI
```

---
# Current State â€” Daily Coach Human Voice Prompt Contract v1

Current accepted baseline:

```text
d5bfd29 Merge daily coach provider preview raw data payload v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_d5bfd29_main_merge-daily-coach-provider-preview-raw-data-payload-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Provider Preview Raw Data Payload v1
```

Rejected milestone context:

```text
Daily Coach Provider Preview Runtime Spike v1 was rejected for voice failure.
```

Active backend implementation milestone:

```text
Daily Coach Human Voice Prompt Contract v1
```

Requested status:

```text
DAILY_COACH_HUMAN_VOICE_PROMPT_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Make Daily Coach provider-preview voice iteration human-editable and rerunnable without Python patching.
```

Implemented scope:

- Added a human-editable Daily Coach voice prompt file at `docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md`.
- Added a developer-only terminal preview runner at `tools/dev_daily_coach_human_voice_prompt_preview.py`.
- Added a read-only service that loads the prompt file, passes the prompt text through exactly, appends `RAW_BACKEND_PAYLOAD_JSON`, and calls a provider only when the explicit developer CLI path is used.
- Added a result model that records prompt metadata, payload metadata, raw model output, and safe error metadata.
- Added focused tests for prompt loading, provider input shape, anti-cage prompt contamination rules, raw-output preservation, fake-provider injection, failure metadata, no database mutation from already-built payloads, and terminal output.

Project/product boundaries:

- The user owns final prompt wording.
- Prompt wording can be edited and rerun without Python patching.
- The prompt file is developer-only.
- The preview runner is developer-only and terminal-only.
- The raw provider-preview payload remains the data source.
- The code must not inject backend-authored Daily Coach Note sentence templates.
- The code must not use the old caged Daily Coach Narrative prompt/schema path.
- The code does not parse, validate, score, reject, or approve provider output.
- The code does not persist provider output.
- The code does not change Today UI.
- The code does not change Daily Coach Note public copy.
- The code does not change Daily Next Action.
- The code does not change API/schema/persistence/report/recommendation behavior.
- The code does not promote any model.

Developer-only prompt iteration workflow:

```text
edit docs/provider_trials/daily_coach_human_voice_prompt_contract_v1.md
run tools/dev_daily_coach_human_voice_prompt_preview.py
inspect terminal output
edit the prompt file again
rerun without patching Python
```

Strong non-goals preserved:

```text
normal Today provider calls
Today UI
Streamlit UI layout
API routes
database schema
migrations
persistence behavior
report behavior
recommendation behavior
Daily Next Action selection logic
Daily Coach Note public copy
workout plan behavior
nutrition target behavior
automatic deload logic
automatic progression logic
wearable/HRV integration
medical interpretation
provider promotion
model approval
RAG/vector/agent behavior
CrewAI behavior
OpenAI behavior
```

---
# Current State â€” Daily Coach Provider Preview Raw Data Payload v1

Current accepted baseline:

```text
e26c4e0 Merge daily coach note copy QA matrix v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_e26c4e0_main_merge-daily-coach-note-copy-qa-matrix-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Note Copy QA Matrix v1
```

Active backend implementation milestone:

```text
Daily Coach Provider Preview Raw Data Payload v1
```

Requested status:

```text
DAILY_COACH_PROVIDER_PREVIEW_RAW_DATA_PAYLOAD_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Create a developer-only raw data payload for future Daily Coach Note provider preview from backend-owned deterministic source data.
```

Implemented scope:

- Added `DailyCoachProviderPreviewRawDataPayload` as a developer-only read-only payload model.
- Added a service that builds the provider-preview raw data payload from a `DailyCoachIntelligenceSnapshot` object.
- Added a service path that builds the same payload from a serialized snapshot dictionary.
- Added a convenience service path that builds the payload for `user_id` and `target_date` by first building the existing Daily Coach Intelligence Snapshot.
- Added a developer terminal tool that prints the payload as JSON.
- Preserved raw deterministic source sections under `source_data` instead of collapsing them into a polished paragraph.
- Preserved recovery intelligence, recovery intelligence v2, workout set intelligence, training execution summary, nutrition trend window, foundation layer status, data completeness, source data gaps, reason codes, and limitations where present.
- Added explicit backend truth contract metadata.
- Added explicit provider voice-space metadata that preserves the Uncaged Provider Voice Principle.
- Added provider input guidance that rejects sentence banks, final copy authorization, and normal Today surface authorization.
- Added forbidden provider authority categories for future provider-preview work.

This milestone creates the model's future data pasture.

This milestone preserves the Uncaged Provider Voice Principle.

This milestone gives future provider work raw deterministic backend data, not backend-written sentence banks.

This milestone does not call providers.

This milestone does not generate Daily Coach Note copy.

This milestone does not change Today UI.

This milestone does not change API/schema/persistence/report/recommendation behavior.

This milestone does not change Daily Next Action selection.

This milestone does not add OpenAI/Ollama/CrewAI/RAG/agent behavior.

This milestone does not add model routing or Prompt Lab runtime behavior.

This milestone does not add workout plan, nutrition target, automatic deload, automatic progression, wearable/HRV, or medical interpretation behavior.

Developer-only payload boundaries:

```text
developer_preview_only = true
provider_call_allowed = false
persistence_allowed = false
product_surface_allowed = false
```

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend reports branch, commit, and validation evidence when requested.
Architecture owns final acceptance, merge, snapshot, and next milestone selection.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Provider Preview Raw Data Payload work.

---
# Current State â€” Daily Coach Note Copy QA Matrix v1

Current accepted baseline:

```text
33ebf18 Merge daily coach note recovery-aware language v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_33ebf18_main_merge-daily-coach-note-recovery-aware-language-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Note Recovery-Aware Language v1
```

Active backend implementation milestone:

```text
Daily Coach Note Copy QA Matrix v1
```

Requested status:

```text
DAILY_COACH_NOTE_COPY_QA_MATRIX_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add a focused QA/test/documentation matrix for Daily Coach Note public copy after the first recovery-aware language integration.
```

Expected implementation files:

```text
tests/test_daily_coach_today_card_copy_matrix.py
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/daily_coach_note_copy_qa_matrix_v1.md
```

Implemented scope:

- Added a focused Daily Coach Note copy QA matrix.
- Covered all approved Daily Next Action classes.
- Covered no-contract, unavailable, limited, low-pressure, moderate-pressure, and high-pressure recovery contract states.
- Verified no-contract Daily Coach Note behavior remains backward compatible.
- Verified recovery contract object input remains valid.
- Verified serialized recovery contract dictionary input remains valid.
- Verified limited/unavailable recovery context uses cautious wording.
- Verified low/moderate/high recovery pressure copy remains bounded.
- Verified public payload does not expose provider/debug/internal contract terminology.
- Verified public payload does not expose unsafe medical, injury, overtraining, automatic deload, automatic progression, or unsafe-to-train claims.
- Verified `coach_note` remains capped at 520 characters.
- Verified Daily Next Action fields are unchanged by recovery copy.
- Verified deterministic public copy remains stable for the same inputs.
- Verified provider calls do not occur in the deterministic Today card matrix path.

This milestone adds QA/test/documentation coverage only.

This milestone does not implement provider behavior.

This milestone does not add OpenAI/Ollama/CrewAI/RAG/agent behavior.

This milestone does not add UI/API/schema/persistence/report/recommendation behavior.

This milestone records the Uncaged Provider Voice Principle for future provider work.

This milestone cages evaluation, not model voice.

Future provider voice should receive raw deterministic backend data, not only backend-written prose summaries.

Repeated-template risk is explicitly recorded as a future provider evaluation concern.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend reports branch, commit, and validation evidence when requested.
Architecture owns final acceptance, merge, snapshot, and next milestone selection.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Note Copy QA Matrix work.

---

# Current State â€” Daily Coach Note Recovery-Aware Language v1

Current accepted baseline:

```text
c940ff4 Merge recovery-aware coach copy contract v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_c940ff4_main_merge-recovery-aware-coach-copy-contract-v1.zip
```

Latest accepted milestone:

```text
Recovery-Aware Coach Copy Contract v1
```

Active backend implementation milestone:

```text
Daily Coach Note Recovery-Aware Language v1
```

Requested status:

```text
DAILY_COACH_NOTE_RECOVERY_AWARE_LANGUAGE_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Use the accepted Recovery-Aware Coach Copy Contract to add the first bounded, deterministic, user-facing recovery-aware sentence to the Daily Coach Note / Today card path when an approved contract is supplied.
```

Expected implementation files:

```text
services/daily_coach_today_card_service.py
tests/test_daily_coach_today_card_service.py
docs/project_memory/current_state.md
docs/project_memory/next_milestone.md
docs/project_memory/project_state.json
docs/project_memory/milestones/daily_coach_note_recovery_aware_language_v1.md
```

Implemented scope:

- `build_daily_coach_today_card()` remains backward compatible when no recovery contract is provided.
- The Today card can accept a `RecoveryAwareCoachCopyContract` object or serialized contract dictionary.
- Recovery-aware Today card language is deterministic and contract-bound.
- The Today card may add one short recovery-aware sentence only when the supplied contract supports bounded copy.
- Limited, unavailable, missing, partial, Low-confidence, or Limited-confidence recovery context uses limited-context wording.
- The Today card does not expose provider/debug/internal contract terminology in public text.
- The Today card does not display forbidden recovery-copy language.
- The Today card keeps `coach_note` within the 520-character limit.
- Daily Next Action selection behavior remains unchanged.

This milestone adds the first bounded user-facing Daily Coach Note recovery-aware language.

The language is deterministic and contract-bound.

The language is not provider-generated.

The language does not change Daily Next Action selection.

The language does not add automatic deload/progression behavior.

The language does not add medical interpretation.

The language does not change UI/API/schema/persistence/report/recommendation behavior.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend reports branch, commit, and validation evidence when requested.
Architecture owns final acceptance, merge, snapshot, and next milestone selection.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Note Recovery-Aware Language work.

---

# Current State â€” Recovery-Aware Coach Copy Contract v1

Current accepted baseline:

```text
66a70d3 Merge daily coach note recovery v2 integration v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_66a70d3_main_merge-daily-coach-note-recovery-v2-integration-v1.zip
```

Latest accepted milestone:

```text
Daily Coach Note Recovery v2 Integration v1
```

Active backend implementation milestone:

```text
Recovery-Aware Coach Copy Contract v1
```

Requested status:

```text
RECOVERY_AWARE_COACH_COPY_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Create a deterministic, backend-owned copy contract that translates Recovery Intelligence v2 facts into bounded, coach-safe Daily Coach Note copy inputs for future use.
```

Expected implementation files:

```text
models/daily_coach_recovery_copy_models.py
services/daily_coach_recovery_copy_contract_service.py
tests/test_daily_coach_recovery_copy_contract_service.py
docs/project_memory/milestones/recovery_aware_coach_copy_contract_v1.md
```

Scope is limited to a read-only contract/guardrail layer:

- reads existing `recovery_intelligence_v2` from the backend Daily Coach Note context
- returns a structured `RecoveryAwareCoachCopyContract`
- preserves Recovery v2 classification, pressure, confidence, and data-quality status
- lists allowed recovery-aware claim guidance only when supported by Recovery v2 facts
- carries caveats when confidence or data quality is limited, partial, missing, or unavailable
- keeps body weight context bounded and non-causal
- lists forbidden claim categories without authorizing forbidden wording
- serializes through `to_dict()`
- returns a valid limited/unavailable contract when `recovery_intelligence_v2` is missing

This milestone does not expose new user-facing copy.

This milestone does not change Today behavior.

This milestone does not change UI/API/provider/schema/persistence/recommendation/report behavior.

This milestone creates a deterministic copy contract for future use.

No Daily Coach final copy, Today card copy, Streamlit UI, API route, provider, OpenAI/Ollama/CrewAI, RAG/vector/agent, schema/migration, persistence, report, recommendation, workout plan, nutrition target, automatic deload/progression, wearable/HRV, or medical interpretation behavior is authorized by this implementation slice.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend does not prepare handoff artifacts.
Backend does not prepare QA findings.
Backend does not prepare QA instructions.
Backend reports branch, commit, and validation evidence when requested.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Recovery-Aware Coach Copy Contract work.

---

# Current State â€” Daily Coach Note Recovery v2 Integration v1

Current accepted baseline:

```text
d2e0178 main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_d2e0178_main_merge-recovery-intelligence-v2-qa-seed-matrix-validation-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 QA Seed Matrix Validation v1
```

Active backend implementation milestone:

```text
Daily Coach Note Recovery v2 Integration v1
```

Requested status:

```text
DAILY_COACH_NOTE_RECOVERY_V2_INTEGRATION_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add Recovery Intelligence v2 additively to the backend-owned Daily Coach Note context layer without changing user-facing Daily Coach copy, Today behavior, UI, API, providers, recommendations, reports, schema, migrations, persistence, or product runtime behavior.
```

Expected implementation files:

```text
models/daily_coach_intelligence_models.py
services/daily_coach_intelligence_snapshot_service.py
tests/test_daily_coach_intelligence_snapshot_service.py
docs/project_memory/milestones/daily_coach_note_recovery_v2_integration_v1.md
```

Scope is limited to exposing structured Recovery Intelligence v2 facts in the existing backend Daily Coach context object:

- preserve existing `recovery_intelligence` v1 field for compatibility
- add optional `recovery_intelligence_v2` field
- source services include `recovery_intelligence_v2_service` when v2 succeeds
- foundation layer status and data completeness record Recovery v2 separately
- source data gaps, reason codes, and limitations record bounded v2 limited/unavailable status
- serialization includes `recovery_intelligence_v2`
- fallback keeps a valid context object if Recovery v2 is unavailable

New roadmap/docs language should prefer `Daily Coach Note` when referring to the future user-facing coach context layer. Existing internal code names such as `DailyCoachIntelligenceSnapshot`, `daily_coach_intelligence_snapshot_service.py`, and `snapshot_version` are not broadly renamed in this milestone.

This slice does not add final Daily Coach copy, Today card copy, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, persistence behavior, RAG/vector/agent work, wearable integration, automatic deload/progression behavior, workout plan behavior, nutrition target behavior, or medical interpretation.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend does not prepare handoff artifacts.
Backend does not prepare QA findings.
Backend does not prepare QA instructions.
Backend reports branch, commit, and validation evidence when requested.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated Daily Coach Note Recovery v2 integration work.

---

# Current State â€” Recovery Intelligence v2 QA Seed Matrix Validation v1

Current accepted baseline:

```text
f50a1cb main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_f50a1cb_main_merge-recovery-intelligence-v2-product-language-docs-cleanup-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Product Language Docs Cleanup v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 QA Seed Matrix Validation v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_QA_SEED_MATRIX_VALIDATION_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add a terminal-friendly developer/QA seed matrix runner that validates Recovery Intelligence v2 service output across named recovery scenarios before any Daily Coach Note integration is authorized.
```

Expected implementation files:

```text
tools/dev_recovery_intelligence_v2_seed_matrix.py
tests/test_recovery_intelligence_v2_seed_matrix.py
docs/project_memory/milestones/recovery_intelligence_v2_qa_seed_matrix_validation_v1.md
```

Scope is limited to a developer/QA validation artifact that calls the accepted Recovery Intelligence v2 service path:

- named scenario labels
- per-scenario classification, recovery pressure, confidence, data quality, reason codes, limitations, and source facts
- valid JSON-only output for automation and QA parsing
- compact and full terminal-readable output
- optional local `qa-runs/.../qa_report.md` generation for manual QA runs
- focused tests proving the tool uses `build_recovery_intelligence_v2()` instead of duplicating service calculations

The seed matrix is evidence-gathering only. It does not create or mutate seed data, does not add product copy, and does not decide final user-facing recovery voice.

New roadmap/docs language should prefer `Daily Coach Note` when referring to the future user-facing coach context layer. Existing code names such as `DailyCoachIntelligenceSnapshot` are not renamed in this milestone.

No Daily Coach Note integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, persistence behavior, RAG/vector/agent work, wearable integration, automatic deload/progression behavior, runtime product behavior, or medical interpretation is authorized by this implementation slice.

Backend chat operating rule remains active:

```text
Architecture prepares Backend implementation handoffs/tasks.
Architecture separately prepares QA testing instructions.
Backend implements the Architecture-provided task.
Backend does not prepare handoff artifacts.
Backend does not prepare QA findings.
Backend does not prepare QA instructions.
Backend reports branch, commit, and validation evidence when requested.
```

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated recovery intelligence or developer-artifact milestones.

---

# Current State â€” Recovery Intelligence v2 Developer Artifact / Inspection Tool v1

Current accepted baseline:

```text
09c6581 main_merge-recovery-intelligence-v2-service-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-07-01_09c6581_main_merge-recovery-intelligence-v2-service-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Service v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 Developer Artifact / Inspection Tool v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_DEV_INSPECTION_TOOL_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add a terminal-friendly developer inspection tool that lets Architecture, QA, Backend, and future agents inspect build_recovery_intelligence_v2() output for a user/date before any Daily Coach Note, UI, API, report, recommendation, provider, or schema integration is authorized.
```

Expected implementation files:

```text
tools/dev_recovery_intelligence_v2.py
tests/test_dev_recovery_intelligence_v2_tool.py
docs/project_memory/milestones/recovery_intelligence_v2_dev_inspection_tool_v1.md
```

Scope is limited to a developer artifact that calls the accepted Recovery Intelligence v2 service:

- text inspection output
- valid JSON output from `RecoveryIntelligenceV2Summary.to_dict()`
- compact terminal output
- optional source-fact visibility controls
- focused tests proving the tool uses `build_recovery_intelligence_v2()` instead of duplicating service calculations

New roadmap/docs language should prefer `Daily Coach Note` when referring to the future user-facing coach context layer. Existing code names such as `DailyCoachIntelligenceSnapshot` are not renamed in this milestone.

No Daily Coach Note integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, persistence behavior, RAG/vector/agent work, wearable integration, automatic deload/progression behavior, or medical interpretation is authorized by this implementation slice.

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated recovery intelligence or developer-artifact milestones.

---

# Current State â€” Recovery Intelligence v2 Service v1

Current accepted baseline:

```text
dd6db0f main_merge-recovery-intelligence-v2-model-contract-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_dd6db0f_main_merge-recovery-intelligence-v2-model-contract-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Model Contract v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 Service v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_SERVICE_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Implement a read-only Recovery Intelligence v2 service that builds the accepted v2 model contract from daily_checkins without changing Daily Coach output, reports, providers, UI, API contracts, schema, migrations, recommendation behavior, or persistence behavior.
```

Expected implementation files:

```text
services/recovery_intelligence_v2_service.py
tests/test_recovery_intelligence_v2_service.py
docs/project_memory/milestones/recovery_intelligence_v2_service_v1.md
```

Scope is limited to constructing the existing `RecoveryIntelligenceV2Summary` model from check-in data:

- preserve `checkin_date` as the primary date
- dedupe duplicate same-day check-ins by latest `created_at` / `id`
- construct current-day context
- construct a 28-day recovery baseline
- construct recent 7-day vs baseline delta
- construct recent 7-day vs prior 7-day delta
- construct indicator-level interpretations for sleep, energy, soreness, body weight, and check-in consistency
- construct data quality, provenance/source facts, confidence, reason codes, limitations, and a coach-safe summary

No Daily Coach Note integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, report behavior, or runtime behavior beyond the new read-only service is authorized by this implementation slice.

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated model-contract or intelligence milestones.

---

# Current State â€” Recovery Intelligence v2 Model Contract v1

Current accepted baseline:

```text
871d090 main_merge-recovery-intelligence-v2-architecture-planning-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_871d090_main_merge-recovery-intelligence-v2-architecture-planning-v1.zip
```

Latest accepted milestone:

```text
Recovery Intelligence v2 Architecture Planning v1
```

Active backend implementation milestone:

```text
Recovery Intelligence v2 Model Contract v1
```

Requested status:

```text
RECOVERY_INTELLIGENCE_V2_MODEL_CONTRACT_V1_IMPLEMENTATION_COMPLETE
```

Purpose:

```text
Add Recovery Intelligence v2 model contracts and tests before any v2 service, Daily Coach Intelligence Snapshot integration, recommendation behavior, provider, API, UI, schema, or persistence changes are authorized.
```

Expected implementation files:

```text
models/recovery_intelligence_v2_models.py
tests/test_recovery_intelligence_v2_models.py
docs/project_memory/milestones/recovery_intelligence_v2_model_contract_v1.md
```

Scope is limited to bounded, serializable model contracts for future Recovery Intelligence v2 concepts:

- current recovery indicator/day context
- recovery baseline
- recent-vs-baseline delta
- recent-vs-prior delta
- indicator-level interpretation
- recovery pressure classification
- readiness classification v2
- data quality
- provenance/source-fact references
- confidence, reason codes, limitations, and coach-safe summary guardrails

No service integration, Daily Coach snapshot integration, provider behavior, UI behavior, API behavior, schema/migration behavior, recommendation behavior, or runtime behavior is authorized by this implementation slice.

Hard workflow rule remains active:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated model-contract or intelligence milestones.

---

# Current State â€” Recovery Intelligence v2 Architecture Planning v1

Current accepted baseline before this docs-only planning slice:

```text
fc7ed70 main_merge-post-north-star-state-reconciliation-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_fc7ed70_main_merge-post-north-star-state-reconciliation-v1.zip
```

Latest accepted milestone:

```text
Post-North-Star State Reconciliation + Architecture/Backend Workflow Memory v1
```

Current Architecture docs-only milestone:

```text
Recovery Intelligence v2 Architecture Planning v1
```

Primary deliverable:

```text
docs/project_memory/architecture/recovery_intelligence_v2_plan.md
```

The Recovery Intelligence v2 plan defines the staged source-data contract direction after v1. It does not authorize runtime behavior changes by itself.

Latest Backend Intelligence Foundation evidence:

- Recovery Intelligence v1 is accepted and merged at `43927d4`.
- Workout Set Intelligence v1 + Daily Coach Intelligence Snapshot v2 is accepted and merged at `123d115`.
- Platform North Star + Future Stack Canonicalization v1 is accepted and merged at `187e433`.
- Post-North-Star State Reconciliation + Architecture/Backend Workflow Memory v1 is accepted and merged at `fc7ed70`.
- Provider voice iteration remains paused.

Next recommended implementation slice after Architecture accepts the plan:

```text
Recovery Intelligence v2 Model Contract v1
```

Purpose of the next implementation slice:

```text
Add Recovery Intelligence v2 model contracts and tests before any v2 service, snapshot integration, recommendation behavior, provider, API, UI, or persistence changes are authorized.
```

No runtime/product behavior changes are authorized by this current state update.

Hard workflow rule now recorded in project memory:

```text
Windows is the only commit/merge/push/snapshot machine.
Linux is pull/validate/runtime QA only and must never commit, merge, or push.
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside unrelated docs or intelligence milestones.

---

# Current State â€” Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2

Current accepted main:

```text
43927d4 main_merge-daily-coach-intelligence-snapshot-recovery-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-30_43927d4_main_merge-daily-coach-intelligence-snapshot-recovery-v1.zip
```

Active backend milestone:

```text
Daily Coach Workout Set Intelligence v1 + Intelligence Snapshot v2
```

Requested status:

```text
DAILY_COACH_WORKOUT_SET_INTELLIGENCE_V1_IMPLEMENTATION_COMPLETE
```

This is the second concrete Backend Intelligence Foundation implementation slice after Recovery Intelligence v1.

Implemented/active scope:

- Workout Set Intelligence v1 as a read-only deterministic set/exercise training indicator layer.
- Daily Coach Intelligence Snapshot v2 with `workout_set_intelligence` included as the richer training source-data layer.
- Existing Training Execution Summary remains in the snapshot for compatibility.
- Existing Recovery Intelligence v1 remains present.
- Existing Nutrition Trend Window remains read-only or recorded as a controlled limitation if unavailable locally.
- Developer-only artifact tool updated to include workout set indicators in JSON, Markdown, pasteback, and `workout_set_intelligence_summary.md`.

Foundation layer status:

```text
recovery_intelligence: implemented_v1
workout_set_intelligence: implemented_v1
trend_engine: nutrition_trend_existing_only
six_month_seed_data: existing_qa_seed_data_only
food_knowledge_expansion: starter_catalog_existing_expansion_pending
```

Provider voice iteration remains paused. This milestone improves backend facts and source-data contracts, not provider prompts.

No user-facing behavior changes are authorized or implemented. Normal Today remains unchanged.

Future next architecture target after acceptance:

```text
Recovery Intelligence v2
```

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside this milestone.

---

# Current State â€” Daily Coach Intelligence Snapshot + Recovery Intelligence v1

Current accepted main:

```text
271ac7e main_merge-project-memory-docs-development-architecture-refresh-v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-29_271ac7e_main_merge-project-memory-docs-development-architecture-refresh-v1.zip
```

Active backend milestone:

```text
Daily Coach Intelligence Snapshot + Recovery Intelligence v1
```

Requested status:

```text
DAILY_COACH_INTELLIGENCE_SNAPSHOT_RECOVERY_V1_IMPLEMENTATION_COMPLETE
```

This is the first concrete Backend Intelligence Foundation implementation slice after the docs/process/development architecture refresh.

Implemented/active scope:

- Recovery Intelligence v1 as a read-only deterministic layer over `daily_checkins`.
- Daily Coach Intelligence Snapshot v1 as a read-only backend-owned source-data contract.
- Existing Training Execution Summary is included read-only.
- Existing Nutrition Trend Window is included read-only or recorded as a controlled limitation if unavailable locally.
- Developer-only artifact tool: `tools/dev_daily_coach_intelligence_snapshot.py`.

Foundation layer status:

```text
recovery_intelligence: implemented_v1
workout_set_intelligence: existing_training_execution_summary_only
trend_engine: nutrition_trend_existing_only
six_month_seed_data: existing_qa_seed_data_only
food_knowledge_expansion: starter_catalog_existing_expansion_pending
```

Provider voice iteration remains paused. This milestone improves backend facts and source-data contracts, not provider prompts.

No user-facing behavior changes are authorized or implemented. Normal Today remains unchanged.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Do not patch that drift inside this milestone.

---

# Current State â€” Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1

Current accepted main:

```text
23b5378 Merge daily coach fully free source-data lab evidence v1
```

Current accepted snapshot:

```text
fitness_ai_snapshot_2026-06-29_23b5378_main_merge-daily-coach-fully-free-source-data-lab-evidence-v1.zip
```

Latest Daily Coach provider evidence:

- v4 free-range prompt/payload decaging is accepted as a developer-only diagnostic baseline at `56d63c4`.
- Fully Free Source-Data Lab v1 is merged as developer-only evidence at `23b5378`.
- Fully Free v1 was technically valid and useful as evidence, but it was not meaningfully better than v4.
- Outputs were competent but generic and structurally repetitive.
- Provider voice iteration is paused.

Active milestone:

```text
Project Memory + Handoff Workflow Compression + Stale Docs Hygiene + Development Architecture v1
```

Requested status:

```text
PROJECT_MEMORY_HANDOFF_COMPRESSION_STALE_DOCS_DEVELOPMENT_ARCHITECTURE_V1_IMPLEMENTATION_COMPLETE
```

Owner:

```text
Backend Development, as routed by Architecture for a docs-only repo patch.
```

Next product architecture center after this docs milestone:

```text
Daily Coach Backend Intelligence Foundation
```

Foundation layers:

- Recovery Intelligence
- Workout Set Intelligence
- Trend Engine
- Six-Month Seed Data
- Food Knowledge Expansion

Sequencing principle:

```text
Build the product brain first. Then build the fancy nervous system.
```

No serious RAG, vector search, embeddings, multi-agent orchestration, LangGraph, CrewAI, LlamaIndex, or production-grade agent architecture should proceed until these backend intelligence layers are designed and robust enough to feed them.

Canonical seven visible team/chat lanes:

1. Architecture
2. Backend Development
3. QA
4. Agent Engineering
5. Streamlit UI / UX
6. Portfolio Packaging
7. DevOps & Tooling

Project Memory / All Future Agents is not one of the seven visible team/chat lanes. It is a repo continuity concern that every team must respect.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated milestones.

## Active docs-only non-goals

This milestone does not authorize runtime behavior changes, provider behavior changes, OpenAI default changes, Today provider display, Streamlit UI changes, API/schema/migration changes, RAG, embeddings, pgvector, vector DB setup, LangGraph, CrewAI, LlamaIndex, multi-agent runtime, custom GPT build, recovery intelligence implementation, workout set intelligence implementation, trend engine implementation, six-month seed data generation, food catalog expansion, provider prompt experiments, or reviewer/renderer implementation.

## Historical current-state notes

The sections below are retained for history only. The active state is the `23b5378` docs refresh state above.

# Current State â€” Daily Coach Fully Free Source-Data Lab v1

Current source of truth: `main` at `56d63c4 Merge daily coach free-range decaging diagnostic baseline v4`.

Active backend milestone: `Daily Coach Fully Free Source-Data Lab v1`.

Status: Architecture merged and snapshotted the free-range decaging v4 diagnostic baseline, then routed Backend to build a separate developer-only source-data lab from `main`, not from the unmerged feature chain.

Purpose: test whether GPT-5.5 can produce a meaningfully better Daily Coach note when it receives clean, organized source data and almost no coaching cage. This is a single-model lab, not multi-agent orchestration, RAG, embeddings, vector search, production provider enablement, or normal Today replacement.

Implementation direction: add a separate developer-only lab tool, build `fully_free_source_data_packet` artifacts, use a minimal prompt, support fully free prompt variants, capture exact first-pass drafts, and add post-hoc audits for source-data completeness, model freedom, backend-prose contamination, completion diagnostics, claim risk, artifact safety, and token/cost telemetry.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FULLY_FREE_SOURCE_DATA_LAB_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3

Current source of truth: `feature/daily-coach-free-range-voice-precision-payload-enrichment-v2` at `d731a6c Enrich free range voice precision payload`.

Active backend milestone: `Daily Coach Free-Range Output Completion + Coach Surface Polish + Data Seeding v3`.

Status: Architecture classified v2 as a promising partial with product signal, but found truncation, raw-number formatting leaks, thin food context, and one targeted regression. Backend is continuing the developer-only free-range experiment from the unmerged v2 feature branch, not `main`.

Purpose: improve output completion, display-ready numeric surfaces, macro/food card artifacts, AI snack candidates, bounded food seeding, weight-anomaly handling, workout/session naming visibility, and voice-style diagnostics while preserving the full first-pass coach note.

Implementation direction: keep first-pass drafts exact and unmodified; keep diagnostics post-hoc only; fix deterministic provider live-opt-in regression; add completion diagnostics; expand practical food candidates; add food option/macro display cards, AI snack candidates, number-formatting and voice-style summaries; preserve provider-input debug and model-input manifest artifacts.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FREE_RANGE_OUTPUT_COMPLETION_COACH_SURFACE_POLISH_DATA_SEEDING_V3_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Free-Range Voice + Precision + Payload Enrichment v2

Current source of truth: `feature/daily-coach-full-user-day-free-range-payload-baseline-v1` at `eb26c59 Add daily coach full user-day free-range trial`.

Active backend milestone: `Daily Coach Free-Range Voice + Precision + Payload Enrichment v2`.

Status: Architecture accepted the v1 free-range thesis as materially better but requested one more developer-only iteration before merge/product-renderer work. Backend is enriching the free-range path with voice variants, precision metadata, broader inspectable food context, set-level data availability reporting, and stronger model-input manifest artifacts.

Purpose: determine whether GPT-5.5 continues improving when it receives a broad neutral full user-day packet with clearer precision/quote metadata, more useful food candidate structure, multiple coach voices, and exact provider-input inspection.

Implementation direction: keep the full coach note intact, preserve exact first-pass draft capture, add strict/empathetic/hypeman coach variants, expose food/macro precision and quote style, make model input inspectable through `model_input_manifest.md`, summarize food candidates and precision, and keep all audits post-hoc only.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FREE_RANGE_VOICE_PRECISION_PAYLOAD_ENRICHMENT_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Full User-Day Free-Range Payload Baseline v1

Current source of truth: `main` at `490d2ae Merge daily coach wide context copy cleanup qa readability v1`.

Active backend milestone: `Daily Coach Full User-Day Free-Range Payload Baseline v1`.

Status: Architecture stopped the phrase-cleanup loop after provider payload forensics showed GPT-5.5 still received app/deterministic prose through the rendered prompt. Backend is implementing a developer-only free-range payload baseline from the last accepted main snapshot, not from the failed v2 branch.

Purpose: answer whether GPT-5.5 can write a genuinely useful Daily Coach note when given a broad neutral structured user-day packet instead of app-generated coach prose, deterministic fallback copy, phrase bans, repair context, or Product Voice Audit scaffolding.

Implementation direction: build a `DailyCoachFullUserDayPacket`, render it as provider-visible data, support minimal/practical/direct free-range prompt variants, support repeated runs, capture exact first-pass drafts before any post-hoc diagnostics, and add opt-in provider payload debug artifacts (`provider_input_prompt.md` and `provider_payload_debug.json`).

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated Daily Coach provider milestones.

Requested final status: `DAILY_COACH_FULL_USER_DAY_FREE_RANGE_PAYLOAD_BASELINE_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Wide Context Copy Cleanup + QA Readability v1

Current source of truth: `main` at `42d0bd4 Merge daily coach wide context ceiling trial v1`.

Active backend milestone: `Daily Coach Wide Context Copy Cleanup + QA Readability v1`.

Status: Backend implementation patch is ready for local validation after Architecture routed the merged wide-context ceiling-trial baseline back for a narrow copy/readability patch. Live QA classified the prior result as `CONTEXT_HELPED_BUT_NOT_ENOUGH`.

Purpose: keep the wide-context ceiling-trial architecture, but clean backend-shaped wording from prompt/context packaging and make QA artifacts easier to inspect from the terminal. This remains developer-only. It is not production integration, not provider promotion, not normal Today replacement, and not another Product Voice Audit/fallback-gate milestone.

Implementation direction: preserve backend truth and safety boundaries while making writer-facing context more human-facing; avoid wording such as `Nutrition is lagging`, `approved option`, `gap is still open`, and `planned workout as written`; add terminal-friendly compact artifacts, product-language findings, best-variant summary, and pasteback report support.

Known baseline drift remains documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied 718c614/42d0bd4 lineage, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside unrelated milestones unless directly scoped.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_COPY_CLEANUP_QA_READABILITY_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1

Current source of truth: `main` at `718c614 Merge daily coach product voice audit gate fix v1`.

Active backend milestone: `Daily Coach Wide Context Uncaged GPT-5.5 Ceiling Trial v1`.

Status: Architecture accepted Backend Continuation Onboarding and directed Backend to proceed with the ceiling trial. Backend implementation is complete and ready for Architecture / QA review.

Purpose: answer whether GPT-5.5 can write genuinely better Daily Coach copy when given richer backend-approved context and fewer pre-draft writing shackles. This is a developer-only ceiling trial, not production integration, not provider promotion, not normal Today replacement, and not another Product Voice Audit phrase patch.

Implementation direction: wide context packet builder, minimal writer prompt variants, exact first-pass draft capture, side-by-side comparison against deterministic and current narrow path, token/cost telemetry fields, sanitized artifacts, QA scoring template, and baseline drift documentation.

Known baseline drift documented: `tests/test_daily_narrative_rich_day_service.py` has copy-expectation mismatches on the supplied 718c614 snapshot, including expected `Read the day before adding more` vs actual `Consider the full day`. Architecture directed Backend to document this and not patch it inside the ceiling trial unless it directly blocks targeted validation. Full-suite green must not be claimed if this drift remains.

Requested final status: `DAILY_COACH_WIDE_CONTEXT_UNCAGED_GPT55_CEILING_TRIAL_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1

Current source of truth: `feature/daily-coach-natural-draft-product-voice-audit-v2` at `9ba9579 Add daily coach natural draft product voice audit v2`.

Active backend patch: `Daily Coach Product Voice Audit Calibration + Final Approval Gate Fix v1`.

Status: Architecture routed v2 back to Backend for a focused approval-gate and audit-calibration patch.

QA found v2 architecture is useful as a diagnostic system, but final approval was wrong: failed fallback could still become final approved copy, Product Voice Audit was too lenient, food-action language was incomplete, and repair gave up too early when first-pass copy only needed light wording cleanup.

Patch direction: keep the writer loose, sharpen the reviewer, prefer light product-voice repair over fallback when factual claims are safe, and block final approval when fallback itself fails Product Voice Audit.

Required status: `DAILY_COACH_PRODUCT_VOICE_AUDIT_CALIBRATION_FINAL_APPROVAL_GATE_FIX_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Natural Draft + Product Voice Audit v2

Current source of truth: `main` at `4104796 Merge daily coach natural draft claim audit v1`.

Active backend milestone: `Daily Coach Natural Draft + Product Voice Audit v2`.

Status: Architecture approved for Backend implementation.

Natural Draft + Claim Audit v1 is merged as developer infrastructure but QA found it was only a technical partial: the factual reviewer existed, but product-quality review did not. V2 extends that path with first-pass model draft visibility, Product Voice Audit, food-action language checks, side-by-side comparison, repair delta reporting, humanized fallback, final approval gates, and reviewer conclusions.

Core principle: loosen the writer, tighten the reviewer, expose the first draft, and compare honestly. Deterministic fallback is the floor, not the goal.

V2 remains developer-only. Normal Today behavior is unchanged. OpenAI/direct_ollama remain explicit opt-in/evaluation-only. Backend remains final authority for facts, claim audit, product voice audit, repair limits, fallback, and final approval.

Requested final status: `DAILY_COACH_NATURAL_DRAFT_PRODUCT_VOICE_AUDIT_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Natural Draft + Claim Audit v1

Current source of truth: `main` at `b9b46c9 Merge daily coach prompt lab voice lab v1`.

Active backend milestone: `Daily Coach Natural Draft + Claim Audit v1`.

Status: Architecture approved for Backend implementation.

Prompt Lab / Voice Lab v1 is merged as technical developer tooling, but product strategy has pivoted to Natural Draft + Claim Audit. The active architecture is: backend-approved coach brief â†’ natural coach draft â†’ deterministic claim extraction â†’ backend claim audit â†’ one targeted repair attempt â†’ final approved copy or deterministic fallback.

Core principle: loosen the writer, tighten the reviewer. GPT-5.5 may draft naturally from a clean `ApprovedCoachBrief`, but Backend remains final authority for facts, interpretations, claim audit, repair limits, fallback, and final approval.

Boundaries remain unchanged: developer-only path; normal Today behavior unchanged; deterministic remains default; OpenAI/direct_ollama remain explicit opt-in/evaluation-only; no provider promotion; no public UI; no provider output persistence; no parser/validation/fallback relaxation; no raw DB access for provider; no RAG, embeddings, meal planning, workout generation, recovery-score, worker, scheduler, or queue changes.

Requested final status: `DAILY_COACH_NATURAL_DRAFT_CLAIM_AUDIT_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Provider Prompt Lab / Voice Lab v1

Current source of truth: `main` at `2835d09 Merge daily coach plainspoken voice action clarity v5`.

Active backend milestone: `Daily Coach Provider Prompt Lab / Voice Lab v1`.

Status: Architecture approved for Backend implementation.

V5 technically passed infrastructure but failed product voice. The current milestone is developer-only Prompt Lab / Voice Lab tooling, not another one-off phrase-hardening patch.

The lab compares fixed scenario cases and prompt/context variants through the existing Daily Coach provider path, parser, validator, fallback boundary, sanitized artifacts, and manual scoring template.

Deterministic remains default. OpenAI/direct_ollama remain explicit opt-in/evaluation-only. Normal Today behavior, product persistence, Streamlit provider controls, parser rules, quote/value validation, and fallback behavior remain unchanged.

Requested final status: `DAILY_COACH_PROVIDER_PROMPT_LAB_VOICE_LAB_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Provider Plainspoken Voice & Action Clarity v5

Current source of truth: `feature/daily-coach-provider-human-voice-food-action-specificity-v4` at `0ace3da`.

Active backend milestone: `Daily Coach Provider Plainspoken Voice & Action Clarity v5`.

Architecture status: approved for Backend implementation after the green v4 baseline snapshot.

Status: backend implementation patch ready for local validation.

V5 replaces phrase-ban-only tuning with a plainspoken coaching contract. The Daily Coach should say the actual action, use friendly food labels, explain the food reason, connect recovery to training behavior, and keep the priority action concrete without motivational packaging or backend/framework language.

Implemented direction:

- plainspoken voice contract and rejected phrase registry;
- `food_action_context` with friendly food options, macro reason, and backed food-action sentence patterns;
- prompt rewrite around plain examples and anti-examples;
- stronger visible-output validation for user-rejected phrases, canonical food leakage, unbacked food action, invented timing, invented pairings, and invented serving labels;
- trial-matrix v5 diagnostics for plainspoken phrase flags, food-gap reason use, food condition use, slogan-like phrases, and manual product voice scoring.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama remain opt-in/evaluation-only; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_PLAINSPOKEN_VOICE_ACTION_CLARITY_V5_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3

Current source of truth: `feature/daily-coach-context-selection-coaching-synthesis-v2` at `2cd7708`.

Active backend milestone: `Daily Coach Provider Voice, Context Freedom & Rich Synthesis v3`.

Architecture status: approved for Backend implementation.

Status: backend implementation patch ready for local validation.

V3 addresses product-copy quality after v2 technical pass by giving providers a more natural, human-readable, claim-backed context starter while preserving strict backend truth boundaries. The implementation adds `approved_context_brief`, `claim_backing_map`, cleaned today_story phrasing, natural voice examples/anti-examples, explicit `verbosity_budget`, hard/diagnostic phrase checks, and v3 trial-matrix diagnostics.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama remain opt-in/evaluation-only; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_VOICE_CONTEXT_FREEDOM_RICH_SYNTHESIS_V3_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Provider Context Selection & Coaching Synthesis v2

Current source of truth: accepted copy-grounding branch baseline at `2bbffdb`.

Active backend milestone: `Daily Coach Provider Context Selection & Coaching Synthesis v2`.

Architecture status: approved for Backend implementation.

Status: backend implementation complete pending validation/handoff.

This milestone improves provider context selection and coaching synthesis by adding deterministic `today_story`, expanded high-value claim selection, field-specific claim budgets, adaptive verbosity guidance, prompt synthesis framing, and v2 trial-matrix diagnostics.

Adaptive verbosity rule: the target is useful, grounded, scannable coaching, not maximum brevity. More words are allowed only when approved context is rich and the extra words improve actionability, connect multiple domains, or explain food/training/recovery context clearly. Shorter copy is required when context is sparse, generic, report-like, repetitive, or unsupported.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama are opt-in; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, embeddings, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_CONTEXT_SELECTION_COACHING_SYNTHESIS_V2_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Provider Copy Grounding & Approved Context Enrichment v1

Current source of truth: `main` / accepted runtime-fix baseline at `60fe77b`.

Active backend milestone: `Daily Coach Provider Copy Grounding & Approved Context Enrichment v1`.

Architecture status: approved for Backend implementation.

Status: backend implementation complete pending validation/handoff.

This milestone enriches provider-approved context packaging and prompt guidance so OpenAI can write more specific Daily Coach copy without weakening the existing parser, quote/value validator, fallback path, or deterministic default.

Implemented direction:

- approved value claim metadata: `priority`, `section_hint`, `coaching_use`, `display_hint`, `value_style`;
- provider context packaging: `provider_task_context`, `high_value_claims`, `preferred_claims_by_field`, `claim_usage_rules`, `field_role_guidance`;
- prompt/field-role guidance for practical coach copy using 2-4 high-value claims;
- trial-matrix copy-quality diagnostics and manual review placeholders.

Boundaries remain unchanged: deterministic is default; OpenAI/direct_ollama are opt-in; provider output is parsed, quote/value validated, approved, or deterministically fallen back; no raw provider output is public; no provider output persistence, Streamlit provider controls, nutrition/workout/recovery/report changes, RAG, Prompt Lab, or multi-agent orchestration are included.

Requested final status: `DAILY_COACH_PROVIDER_COPY_GROUNDING_APPROVED_CONTEXT_ENRICHMENT_V1_IMPLEMENTATION_COMPLETE`.

---

# Current State â€” Daily Coach Provider Trial Diagnostics v1

Current source of truth: `main` at `a6cd8d0` plus accepted Daily Coach Narrative Provider Trial Matrix tooling at `4641c91`.

Active backend milestone: `Daily Coach Provider Trial Diagnostics v1`.

Status: Architecture approved for Backend implementation.

Diagnostics v1 improves the provider trial matrix only. It adds explicit local raw-provider-output diagnostics, safer OpenAI configuration/error classification, safe provider config metadata, optional Ollama unload cleanup, and artifact-safety guardrails.

Deterministic remains default. `direct_ollama` and `openai` remain opt-in. No product runtime, Streamlit, persistence, parser, validator, quote/value, nutrition, workout, recovery, or report behavior changes are authorized.

Requested final status: `DAILY_COACH_PROVIDER_TRIAL_DIAGNOSTICS_V1_ACCEPTED`.

---

# Current State Update â€” Daily Coach Narrative Provider Trial Matrix v1

Current source of truth: `main`.

Required source main commit: `a6cd8d0`.

Canonical accepted baseline snapshot: `fitness_ai_snapshot_2026-06-27_a6cd8d0_daily-coach-narrative-approved-value-quote-validation-v1.zip`.

Previous accepted statuses:

- `DAILY_COACH_NARRATIVE_VALUE_AWARE_PROVIDER_COMPARISON_V1_ACCEPTED_AND_QA_PASSED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_VALIDATION_V1_ACCEPTED_AND_MERGED`
- `DAILY_COACH_NARRATIVE_APPROVED_VALUE_QUOTE_QA_V1_PASS`

Current backend milestone: Daily Coach Narrative Provider Trial Matrix v1.

Branch: `feature/daily-coach-narrative-provider-trial-matrix-v1`.

Commit-check mode: code.

QA class: CLASS 2 / CLASS 5 HYBRID.

Status: backend implementation in progress.

Requested final status: `DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.

## Goal

Add repeatable provider trial matrix tooling for Daily Coach value-aware narratives.

The tool compares the same approved Daily Coach contexts across:

- deterministic;
- direct_ollama;
- openai.

The matrix records schema adherence, parse/validation/fallback behavior, quote/value discipline, latency, approved narrative output, rendered narrative output, and manual-review placeholders without changing runtime defaults.

## Implemented direction

Provider evaluation must run through the accepted Daily Coach value-aware narrative path and approved value quote validation path.

Live providers are skipped unless explicitly enabled with `--allow-live-providers`.

Generated artifacts must not include raw provider output or secrets.

The normal app/runtime behavior remains unchanged.

## Scope boundaries

Deterministic remains default.

`direct_ollama` remains opt-in offline/developer mode.

`openai` remains opt-in hosted comparison provider.

No provider default change is authorized.

No live provider calls are allowed in automated tests.

No Streamlit provider controls are added.

No provider narratives are persisted.

No parser, validator, quote/value, nutrition, workout, recovery, report, schema, or persistence behavior is changed.

No snapshots are committed.

## Architecture review step

Return to Architecture after implementation and validation.

Requested final status:

`DAILY_COACH_NARRATIVE_PROVIDER_TRIAL_MATRIX_V1_ACCEPTED`.


## Historical continuity anchors â€” reference-only

These phrases are preserved for project-memory continuity checks and are reference-only, not current scope:

- Project Memory Alignment + North Star Architecture v1
- Provider Narrative QA Matrix v2
- Daily Coach Async Service Shell / No Worker v1
- Daily Coach Async Provider Runtime Design v1
- qwen3:32b research / future premium async candidate only
- deterministic fallback remains mandatory
- Backend owns facts, validation, persistence, provenance/confidence, and safety boundaries
- AI explains backend-approved truth
- no provider on normal Today page load unless explicitly configured

## Historical continuity anchors â€” additional reference-only preservation

These phrases are preserved to avoid losing accepted historical continuity context:

- feature/daily-coach-narrative-same-session-approved-preview-bridge-v1
- No provider may run on normal Today page load
- Daily Coach Same-Session Approved Preview Bridge v1 Retry
- Same-Session Bridge Runtime QA v1
- Daily Coach Narrative Product Voice Polish v1
- Daily Coach Narrative Product Voice Runtime QA v1
- PASS_WITH_NOTE
- sound right and be right
- Local Developer Command Menu Audit + Repo-Owned Commands v1
- scripts/fitness_commands.ps1
- Local Command Menu App Runtime Correction v1
- Linux is the canonical
- wapp
- service shell only
- no provider execution added


---

# Current Implementation Update â€” Daily Coach Provider Human Voice & Food Action Specificity v4

Status: Backend v4 patch candidate built from v3 baseline `e23a435`.

This milestone addresses the v3 product-copy failure after technical validation passed. It improves provider-facing human voice and food action specificity while preserving strict backend truth boundaries.

Implemented direction:

- friendly food labels are generated for provider/user-facing copy;
- canonical food labels remain traceability/debug context;
- serving display remains conservative and backend-approved only;
- nutrition_action_context explains the approved food action without letting the model invent meal plans;
- claim_backing_map separates internal meaning from user-facing phrase examples;
- approved_context_brief and today_story avoid known awkward framework phrases;
- prompt examples now directly ban the phrases rejected in QA/user critique;
- validation catches canonical food label leakage, unquoted friendly foods, invented serving wording, and repeatedly rejected phrases;
- trial matrix diagnostics include v4 food/voice fields.

Boundaries preserved:

- deterministic default unchanged;
- OpenAI/direct_ollama opt-in only;
- parser and quote/value validation remain strict;
- no provider persistence;
- no Streamlit changes;
- no nutrition target, workout, recovery, or report architecture changes.


---

# Current Implementation Update â€” Daily Coach Free-Range Prompt + Payload Decaging v4

Status: Backend v4 patch candidate built from v3 baseline `c36c50a`.

This milestone continues the unmerged free-range Daily Coach experiment and addresses the v3 finding that the coach output was still too backend-bound. The implementation splits internal/debug payloads from the model-facing coach-facts surface, decages the provider prompt when explicitly requested, and adds direct/hypeman-clean variants while preserving exact first-pass output and post-hoc-only diagnostics.

Implemented direction:

- deterministic provider remains runnable without `--allow-live-provider` while OpenAI/direct_ollama remain explicit opt-in;
- debug payloads may retain backend/internal fields, but `model_facing_coach_facts.md/json` exposes cleaner coaching source material;
- `--prefer-decaged-prompt` uses `MODEL_FACING_COACH_FACTS_JSON` instead of the full backend-shaped packet;
- the decaged prompt tells GPT-5.5 not to echo field labels/internal categories and to use editorial judgment;
- the prompt specifically discourages main-note numeric overload, panic-level macro deficit framing, Markdown bold, emoji headers, decorative Markdown, and repeated `roughly` wording;
- direct/hypeman-oriented clean variants were added for the v4 voice matrix;
- completion diagnostics now report expected/captured/complete/truncated/skipped counts;
- food/snack formatting aggregates mini-meal macros before display;
- new artifacts include model-facing coach facts, decaging summary, and backend label exposure summary;
- provider payload debug includes both debug packet and model-facing facts so Architecture/QA can inspect the split.

Boundaries preserved:

- developer-only experiment;
- normal Today unchanged;
- no production Today replacement;
- no restrictive renderer/reviewer gate;
- no OpenAI default or provider promotion;
- no public UI or Streamlit controls;
- no raw provider envelope persistence, secrets, or raw DB dumps;
- no medical advice generation;
- no meal planning, workout generation, nutrition target, recovery score, RAG, embeddings, multi-agent runtime, Headroom/context compression, local/cheaper model comparison, or full 450â€“500 food expansion.
