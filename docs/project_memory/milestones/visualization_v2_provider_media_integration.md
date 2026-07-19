# Visualization v2: Animated Provider Media Integration

Baseline: `main @ d6f968b` (`Merge structured AscendAPI coverage reassessment v1`).

Feature branch: `feature/visualization-v2-provider-media`.

Status: `VISUALIZATION_V2_PROVIDER_MEDIA_INTEGRATION_ARCHITECTURE_ACCEPTED`.

## Accepted architecture

- The internal canonical catalog owns exercise identity.
- Structured taxonomy owns physical `visual_identity_slug`.
- ExerciseDB / AscendAPI Free V1 supplies only explicitly reviewed remote animated media.
- Resolution order is direct local media, accepted shared-local visual identity, approved configured provider mapping, then no visual media.
- Local form media remains authoritative.
- Provider mappings remain repository-owned metadata rather than persisted fake local-media rows.
- The instruction contract adds normalized `visual_media` and `visual_media_resolution` while preserving existing direct-local `form_media`.

## Exact accepted coverage

- 240 canonical exercises.
- 231 accepted visual identities.
- 83 direct local owners with 166 checksum-verified static assets.
- Exactly three accepted shared-local canonical resolutions.
- Exactly 46 reviewed `ascendapi_free_v1` provider visual identities.
- Those provider identities fan out to exactly 52 canonical exercises.
- Configured total: 83 direct + 3 shared + 52 provider = 138 / 240 canonical exercises with visual guidance.
- Remaining text-only exercises: 102 / 240.

The three accepted shared-local cases are:

1. `Tempo Push-Up` -> `visual_push_up`
2. `Dumbbell Tempo Goblet Squat` -> `visual_goblet_squat`
3. `Treadmill Recovery Walk` -> `visual_treadmill_walk`

## Provider and rights boundary

Runtime provider media is enabled only through explicit server-side selection:

`EXERCISE_VISUAL_MEDIA_PROVIDER=ascendapi_free_v1`

The implementation emits only reviewed provider GIF URLs and performs no live provider search, permanent download, caching, mirroring, vendoring, redistribution, or provider-media database persistence.

Provider failure or missing configuration degrades safely to complete text-only exercise guidance.

This provider integration is accepted only for the current non-commercial/prototype phase. Provider rights must be revisited before monetized or SaaS use.

## Read-only shared-local runtime invariant

Shared-local runtime resolution does not call `get_exercise_catalog()` and does not invoke catalog seeding.

The resolver performs a genuinely read-only persisted lookup over catalog, taxonomy, and direct form-media state.

The persisted source owner must match both the accepted source exercise name and expected `visual_identity_slug`.

If multiple direct local-media owners unexpectedly exist for one accepted shared visual identity, resolution fails explicitly rather than choosing arbitrarily.

## API and frontend behavior

`GET /exercise-catalog/{id}/instruction` returns normalized visual media and resolution provenance while preserving the existing instruction contract.

Local Start/Finish media remains unchanged.

Animated provider media is displayed as a compact centered movement demonstration using its natural aspect ratio, bounded by the available viewport and without forced cropping or aggressive enlargement.

Visible provider attribution is preserved.

Media-load failure preserves written instructions and falls back safely.

## Acceptance evidence

- Focused post-correction backend validation: 39 passed.
- Architecture clean-baseline reconstruction and relevant backend regression slice: 121 passed.
- Frontend visual-media tests: 4 passed.
- Targeted Ruff checks: passed.
- Ruff formatting checks: passed.
- Frontend lint: passed.
- Frontend production build: passed.
- Complete final working-tree source review: passed.
- Desktop production browser smoke: passed.
- Mobile production browser smoke at approximately 390 x 844: passed.
- Provider animation, attribution, written guidance, responsive containment, and compact sizing were user-validated.

## Roadmap continuation

Visualization v2 completes the provider-neutral visual-media foundation, but it does not complete the current exercise-catalog program.

The active strategic objective is to expand the internal canonical exercise catalog from 240 to at least 450-500 exercises, using the free AscendAPI inventory as the primary candidate source.

AscendAPI remains a source/provider rather than catalog truth. Candidate exercises must be deliberately reviewed, canonicalized, deduplicated, assigned internal taxonomy, equipment and measurement semantics, instructions, and approved visual-media relationships before admission.

Catalog utilization and rotation should be audited and improved as necessary during the expansion program so newly admitted exercises are genuinely reachable.

The broader unrelated product roadmap resumes only after the 450-500 canonical-exercise objective is substantially achieved and Architecture explicitly closes the expansion program.

Injury / Temporary Limitation Mode is already complete and is not a future roadmap milestone.
