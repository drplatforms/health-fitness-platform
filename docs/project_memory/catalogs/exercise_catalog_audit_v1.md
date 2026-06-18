# Exercise Catalog Audit v1

Last updated: 2026-06-18

## Status

`CATALOG_EXPANSION_CURATION_V1_PLANNING_AUDIT`

This is a planning audit only. It does not change workout generation behavior, add new workout logic, or change Training provider semantics.

## Current inventory

The app currently has a curated local exercise catalog seeded through `services/exercise_catalog_service.py` and `scripts/seed_exercise_catalog.py`.

Current curated catalog count observed in the code snapshot:

- exercise catalog entries: 178

Current exercise types:

- strength: 138
- core: 20
- conditioning: 18
- mobility: 2

Current movement-pattern coverage:

- horizontal_pull: 25
- horizontal_push: 20
- hinge: 16
- vertical_push: 16
- conditioning: 15
- lunge: 13
- arms_biceps: 13
- vertical_pull: 13
- squat: 12
- core_anti_extension: 12
- arms_triceps: 11
- core_anti_rotation: 7
- carry: 5

Current equipment coverage:

- dumbbell: 43
- plates: 33
- bodyweight: 29
- adjustable_bench: 27
- cable: 25
- barbell: 23
- resistance_band: 21
- rack: 12
- pull_up_bar: 11
- ez_bar: 7
- treadmill: 6
- rope_cable_attachment: 6
- exercise_ball: 6
- bike: 5
- machine: 3

Current difficulty coverage:

- beginner: 93
- intermediate: 76
- advanced: 9

Current app-facing model fields include:

- `name`
- `exercise_type`
- `movement_pattern`
- `primary_muscle_groups`
- `equipment_required`
- `difficulty`

## Current strengths

- The catalog is curated and deterministic.
- It already covers the user's home-gym equipment well: dumbbells, bench, barbell/rack/plates, cables, bands, pull-up bar, treadmill, and bike.
- Movement patterns are explicit enough for deterministic workout planning and substitutions.
- Existing substitution service can reason from movement pattern, muscles, and equipment.
- The catalog already includes a meaningful number of dumbbell, bodyweight, cable, barbell, and band movements.

## Current gaps

Likely gaps to review before Exercise Catalog Expansion v1:

- Mobility/recovery entries are very limited.
- Recovery suitability is not first-class yet.
- Joint stress is not first-class yet.
- Substitution groups are inferred rather than explicitly curated.
- Setup and safety notes are not first-class fields.
- Progression type is not first-class.
- Some near-duplicates likely need naming/alias policy review.
- Advanced movements exist but should be bounded by safety/recovery tags before being surfaced aggressively.
- Machine entries exist but may not match the user's home-gym environment and should be treated carefully.

## Proposed target exercise catalog groups

Exercise Catalog Expansion v1 should focus on practical variety and safer substitutions across:

1. Dumbbell movements
   - pressing variants
   - rowing variants
   - squat/lunge/hinge variants
   - shoulder/arm accessories

2. Barbell and rack movements
   - squat/bench/press/row/hinge variants
   - conservative variants where recovery-limited

3. EZ bar movements
   - curls/extensions
   - selected accessory work only

4. Cable system movements
   - rows/pulldowns/pressdowns/curls
   - safe accessory options

5. Bodyweight movements
   - scalable push/pull/lower/core options

6. Band movements
   - warm-up, accessory, recovery-friendly, and substitution options

7. Conditioning
   - treadmill
   - bike
   - low-impact options

8. Mobility/recovery
   - warm-up drills
   - low-stress recovery options
   - movement-prep entries

## Recommended fields for Exercise Catalog Expansion v1

Current schema can support a basic expansion, but the target catalog should define these fields explicitly:

- `exercise_id`
- `display_name`
- `movement_pattern`
- `primary_muscles`
- `secondary_muscles`
- `equipment_required`
- `difficulty`
- `joint_stress`
- `recovery_suitability`
- `progression_type`
- `substitution_group`
- `setup_notes`
- `safety_notes`

Implementation can begin with deterministic constants and existing tables. Schema expansion should be planned separately if first-class fields are needed for workout generation or UI filtering.

## Curation rules

An exercise qualifies as catalog-ready only when:

- display name is clear and non-duplicative
- movement pattern is explicit
- required equipment is accurate
- primary muscles are listed conservatively
- difficulty is reasonable
- high joint-stress or advanced options are not surfaced as default recovery-limited choices
- substitution group is clear enough for deterministic alternatives
- setup/safety notes are included when execution risk is non-obvious

Duplicates should be avoided by:

- normalized name review
- equipment-specific naming rules
- movement-pattern review
- substitution-group review

Recovery-sensitive tagging should distinguish:

- recovery-friendly
- neutral
- use-with-caution
- avoid-when-recovery-limited

## Non-goals

Do not add:

- generated exercise dumps
- RAG/embeddings
- AI-authored production catalog entries
- new workout generation behavior in the planning milestone
- new progression algorithms
- clinical rehab claims
- unsupported pain/injury guidance

## Recommended second implementation slice

`Exercise Catalog Expansion v1`

Reason:
After food logging improves, workout variety and equipment-aware substitutions become the next daily-use bottleneck. The existing catalog is strong enough to build on, but recovery suitability, joint stress, substitution grouping, and mobility/recovery depth need deliberate curation.
