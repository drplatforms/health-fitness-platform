# Open Questions

## Current milestone questions

### Snapshot Ownership / Main Acceptance Artifact Policy v1

Status: authorized docs/process closeout.

Architecture has answered the core process question:

- Canonical accepted snapshots should be created from accepted `main` commits after Architecture acceptance / merge.
- Feature snapshots may exist as temporary implementation artifacts.
- Feature snapshots are not final accepted continuity snapshots unless explicitly designated.
- Future handoffs must distinguish feature commit, main merge commit, feature snapshot, and canonical accepted snapshot.

Remaining closeout checks:

1. Was the canonical accepted snapshot created from `main` at `2279665`?
2. Do current project-memory files identify `2279665` as the accepted main state?
3. Do current project-memory files identify `fitness_ai_snapshot_2026-06-26_2279665_nutrition-serving-unit-logging-backend-v1.zip` as the canonical accepted snapshot?
4. Do current handoffs distinguish the feature snapshot from the canonical accepted snapshot?
5. Does the next milestone route to Canonical Serving Unit Discovery API v1?

## Product/API follow-up discovered by QA

### Canonical Serving Unit Discovery API v1

Status: recommended next implementation milestone.

QA found one non-blocking follow-up after Nutrition Serving Unit Logging Backend v1:

Serving-unit IDs are not yet discoverable through a public-safe API response.

Manual QA had to look up `serving_unit_id` directly in:

`canonical_food_serving_units`

This is acceptable for backend QA but blocks clean Streamlit serving-unit picker work.

Open implementation questions for the next milestone:

1. Should the endpoint live under `/foods/canonical/{canonical_food_id}/serving-units`?
2. Should inactive canonical foods return 404 or a safe empty result?
3. Should inactive serving units be omitted silently?
4. Should response include source/source_note, or only public-safe amount confidence fields?
5. Should response include `unit_name` and `unit_quantity`, or only display-ready text plus gram estimates?
6. Should `amount_source` be explicit in the response for Streamlit display readiness?
7. Should the route live in `api/routes/foods.py`, a canonical foods route module, or existing nutrition route structure?

## Deferred questions

### Nutrition Actuals Confidence Model v1

Still open for a future milestone:

- How should actuals confidence combine weighed grams, grams-entered, package labels, serving-unit estimates, copied entries, and unknown amounts?
- Which confidence vocabulary should be displayed to users for logged actuals?
- Should Target-vs-Actual show estimated-vs-weighed context in the macro table or a separate note?
- How should estimated actuals affect DailyCoachSynthesis, nutrition explanations, and reports?

### Streamlit Serving Unit Logging UI v1

Deferred until Backend discovery API is accepted:

- How should the UI display active serving units for the selected canonical food?
- Should users see gram ranges immediately, or only confidence/source language?
- Should custom serving overrides remain hidden until a later user-saved-serving milestone?

### AI/provider context

Deferred:

- When should provider context include serving-unit-derived actuals confidence summaries?
- What approved summary fields should be allowed?
- How do we prevent provider explanations from overstating serving-size certainty?

## Closed by accepted contract/backend milestones

The following are no longer open for v1:

- Whether `food_entries` remains the actuals bridge: yes.
- Whether a companion provenance table is preferred: yes.
- Whether a dedicated endpoint is preferred: yes.
- Whether grams override is allowed in serving-unit v1: no.
- Whether Streamlit may invent mappings/conversions: no.
- Whether AI/provider may invent serving conversions: no.
- Whether backend serving-unit logging should persist provenance: yes.
- Whether Target-vs-Actual sees serving-unit logs through resolved grams: yes.
- Whether the 8b285c6 feature snapshot is the canonical accepted snapshot: no.
- Whether the 2279665 main snapshot is the canonical accepted snapshot: yes.
