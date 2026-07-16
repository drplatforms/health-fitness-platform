# Mobile Daily-Driver Navigation & Compaction v1

Current implementation branch: `feature/mobile-daily-driver-navigation-compaction-v1`.

Base branch: `main` at `e56bd61 Merge barcode scanning v1`.

Status:

```text
MOBILE_DAILY_DRIVER_NAVIGATION_AND_COMPACTION_V1_IMPLEMENTATION_CANDIDATE_READY_FOR_ARCHITECTURE_REVIEW
```

## Implemented Scope

- Mobile primary navigation now uses dedicated Today (`/`), Food (`/food`), Workout (`/today/workout`), and Recovery (`/recovery`) routes with pathname-derived active state and `aria-current` semantics.
- Live daily routes preserve an absent `date` parameter during workspace transitions; explicitly dated routes preserve the requested date across all supported daily destinations.
- Personal-food routes remain part of the Food navigation workspace, preserve explicit date context only when one was supplied, and return to the dedicated Food route.
- Food and Recovery share one server-rendered daily workspace composition with the existing browser-local live-day rollover boundary, user switcher, theme control, backend-owned daily data, and mobile navigation.
- Mobile Today is an overview: Nutrition, compact workout context, compact recovery context, and direct workspace actions remain visible while full Food, Logged Today, and Recovery Check-In workflows remain available on desktop only.
- The standalone Food workspace preserves nutrition, food search, recent foods, barcode scanning, logged-food editing/deletion, and My Foods. Recent foods use intentional scrollbar-hidden touch scrolling and the empty Logged Today state remains compact.
- The standalone Recovery workspace preserves the existing check-in and readiness behavior without changing recovery logic or persistence contracts.
- Mobile workout status, preview controls, exercise surfaces, and set-entry nesting are more compact. Previous Performance and Next Target share one compact intelligence section with progressive disclosure for history and recommendation rationale.
- Exercise-level substitution and How To controls remain in place; no substitution summary was added to the workout header.
- Exercise Actuals now uses green only for complete work, amber for remaining sets, and a subdued rose treatment for not-started work through the existing semantic Light/Dark theme contract.

## Boundaries Preserved

- The implementation is frontend-only. No backend route, service, API contract, schema, migration, persistence, nutrition, workout-generation, progression, substitution, barcode-provider, or recovery-classification behavior changed.
- Historical workout read-only behavior, explicit-current interactivity, and live browser-local rollover behavior remain intact.
- Barcode scanning remains portal-mounted above mobile navigation and retains camera, photo, and manual entry paths.
- Desktop Today retains the combined dashboard; standalone Food and Recovery routes remain functional without a broad desktop redesign.
- Architecture acceptance state in `docs/project_memory/current_state.md` and `docs/project_memory/project_state.json` remains unchanged.

## Validation Completed

- Lightweight frontend helper tests: `14 passed` across daily navigation, date formatting, live-day rollover, and barcode helper coverage.
- Frontend `npm run lint` passed.
- Frontend production `npm run build` passed, including TypeScript and route generation for `/food` and `/recovery`.
- Isolated production browser smoke used a temporary database copy and dedicated ports `8180/3180`.
- Smoke covered mobile route isolation and active states, live/unpinned navigation, explicit-date preservation, personal-food navigation, Food and Recovery workflows, compact empty Logged Today, recent-food horizontal scrolling, barcode modal layering, workout preview/selected/active compaction, exercise-level substitutions, Previous Performance/Next Target, historical workout read-only behavior, semantic not-started/remaining/complete colors, approximately `390x844`, `360px`, desktop, Light, Dark, console state, and horizontal overflow.
- The barcode modal layer remained above navigation (`z-index 100` versus `50`) and restored normal page state after close.
- All temporary servers, logs, launcher code, and the temporary database were removed; ports `8180/3180` were closed.
- Canonical `fitness_ai.db` SHA-256 remained `e734e9ad6030b4bf389faf8e5e14c1150ffb637034888b3ca8e8cc8e8b5c7828` before and after validation.

The user-owned feature-branch production smoke and Architecture review remain required before acceptance and Git closeout.
