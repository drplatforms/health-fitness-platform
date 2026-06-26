================================================================================
ARCHITECTURE / PLANNING HANDOFF — NUTRITION CATALOG + SERVING FOUNDATION PLANNING V1
================================================================================

Recipient:
Architecture

CC:
Backend Development
QA
Streamlit UI
TPM / Project Control
DevOps & Tooling
Project Memory / All Future Agents

Project:
AI Health Coach / fitness_ai

Milestone:
Nutrition Catalog + Serving Foundation Planning v1

Recommended branch:
feature/nutrition-catalog-serving-foundation-planning-v1

Source branch:
main

Required source main commit:
f469c89

Milestone type:
PLANNING / ARCHITECTURE / PROJECT MEMORY ONLY

Status:
AUTHORIZED / PLANNING REQUEST

================================================================================
WHY THIS MILESTONE EXISTS
================================================================================

The current workout foundation pass is complete enough for now.

Accepted workout foundation milestones:

1. Workout Preview Full-Slot Rotation v1
   - main merge commit: f39b403

2. Exercise Catalog Utilization / Specialized Movement Coverage v1
   - main merge commit: b343a47

3. Test-First Quality Gate Development Plan v1
   - main merge commit: 37d210f

4. Exercise Eligibility Matrix v1
   - main merge commit: f469c89

The project should now pivot toward nutrition.

The nutrition roadmap needs a short architecture/planning milestone before implementation because several upcoming nutrition features are deeply connected:

- food catalog expansion
- canonical food curation
- serving-size conversion to grams
- household measures
- nutrition actuals confidence
- deterministic food suggestions
- later AI meal/snack candidate generation

We should not jump straight into implementation until the backend model and milestone sequence are agreed.

================================================================================
PRIMARY PLANNING GOAL
================================================================================

Define the nutrition backend foundation sequence for the next major project phase.

The desired product direction:

Build a practical, premium nutrition backend where the user can log food by:

1. weighed grams when precision matters

and

2. practical serving units when convenience matters

Examples:

- 180g cooked white rice
- 1/2 cup cooked white rice
- 1 medium banana
- 1 large egg
- 1 tbsp peanut butter
- 1 scoop protein powder
- 1 slice bread
- 1 cup Greek yogurt
- 1 medium potato

The backend must convert approved serving units into grams using validated metadata.

The backend must track confidence so the app does not pretend estimated household measures are as precise as weighed food.

================================================================================
PRODUCT NORTH STAR
================================================================================

Nutrition should become more than a calorie/macro logger.

It should become a grounded nutrition coaching engine.

Backend owns:
- food truth
- canonical foods
- nutrient data
- serving unit conversions
- grams
- confidence
- logged actuals
- targets
- gaps
- validation
- fallback

AI/provider may eventually help:
- explain approved facts
- assemble meal ideas
- generate snack candidates
- generate meal-plan candidates
- personalize phrasing
- quote approved actuals/targets/gaps

AI/provider must not:
- invent foods
- invent macros
- invent serving sizes
- invent gram conversions
- invent targets
- treat missing logs as zero intake
- make unsupported health claims

================================================================================
KEY STRATEGIC DECISION TO MAKE
================================================================================

Architecture should decide the preferred nutrition foundation order.

Recommended sequence:

1. Nutrition Catalog Diagnostic v1

Purpose:
Measure the current food catalog and nutrition data state before expansion.

2. Curated Food Catalog Expansion v1

Purpose:
Expand approved app-facing canonical foods with high-value daily staples.

3. Serving Unit Normalization / Household Measure Conversion v1

Purpose:
Add serving units that convert to grams with confidence.

4. Nutrition Logging Backend Contract v1

Purpose:
Allow food logs to be represented by grams or approved serving units.

5. Nutrition Actuals Confidence v1

Purpose:
Track whether nutrition actuals are weighed, serving-estimated, saved-meal-estimated, or low-confidence.

6. Nutrition Deterministic Food Suggestions v1

Purpose:
Use backend-approved actuals, targets, gaps, canonical foods, and serving units to suggest practical foods/snacks.

7. Nutrition AI Meal/Snack Candidate Contract v1

Purpose:
Allow qwen/direct_ollama to propose meal/snack candidates using only backend-approved foods, serving units, actuals, targets, and gaps.

================================================================================
IMPORTANT DESIGN DECISION — TWO-LAYER FOOD CATALOG
================================================================================

Architecture should strongly consider a two-layer food model.

Layer 1:
Raw / Source Food Data

Purpose:
- large imported food datasets
- USDA or source records
- not directly user-facing
- useful for search, enrichment, mapping, future expansion

Layer 2:
Canonical App Food Catalog

Purpose:
- curated food names
- aliases
- nutrients per 100g
- approved serving units
- confidence/source metadata
- safe for logging
- safe for deterministic suggestions
- safe for AI/provider contracts

Recommended doctrine:

Do not expose a huge raw import directly to food logging, suggestions, or AI.

Use raw/staging data as an input source.

Only approved canonical foods should power normal logging, suggestions, and provider contracts.

================================================================================
WHY NOT IMPORT EVERYTHING DIRECTLY?
================================================================================

A huge direct food import can make the app worse if it creates:

- duplicate foods
- confusing names
- poor search results
- inconsistent nutrient rows
- weird branded entries
- incomplete serving sizes
- fake precision
- bad macro suggestions
- AI/provider grounding problems
- user distrust

Correct approach:

Raw import can be large.

Canonical app catalog should be curated.

================================================================================
PROPOSED CATALOG EXPANSION SIZE
================================================================================

Recommended first curated expansion:

Food Catalog Expansion v1:
150–300 canonical foods

Serving Unit Normalization v1:
50–100 high-value foods/servings first

Recommended later expansion:

Food Catalog Expansion v2:
500–1,000 curated canonical foods

Raw Import / Source Staging v1:
Potentially 10,000+ source foods, but not all app-approved

================================================================================
HIGH-VALUE FOOD CATEGORIES FOR V1
================================================================================

Architecture should plan the first curated expansion around practical daily staples.

Proteins:
- chicken breast
- chicken thigh
- turkey
- lean ground beef
- eggs
- egg whites
- tuna
- salmon
- shrimp
- Greek yogurt
- cottage cheese
- protein powder

Carbs:
- cooked white rice
- cooked brown rice
- potatoes
- sweet potatoes
- oats
- pasta
- bread
- tortillas
- cereal
- bananas
- apples
- berries

Fats:
- olive oil
- butter
- peanut butter
- avocado
- almonds
- mixed nuts
- cheese

Vegetables:
- broccoli
- spinach
- green beans
- peppers
- onions
- carrots
- salad greens
- mixed vegetables

Convenience / snacks:
- protein bars
- granola bars
- yogurt cups
- popcorn
- crackers
- common sweets/treats

Meal basics:
- rice bowl components
- sandwich components
- wrap components
- salad components
- saved meal templates later

================================================================================
SERVING UNIT / HOUSEHOLD MEASURE DESIGN
================================================================================

Architecture should define a serving-unit model.

Possible model:

CanonicalFood:
- food_id
- canonical_name
- aliases
- nutrients_per_100g
- source
- confidence
- active

ServingUnit:
- serving_unit_id
- food_id
- unit_name
- unit_quantity
- grams_default
- grams_min
- grams_max
- confidence
- source
- source_note
- user_override_allowed
- active

Examples:

Cooked white rice:
- 1/2 cup
- default grams: approximately 90g
- possible range: approximately 80–100g
- confidence: medium

Large egg:
- 1 large egg
- default grams: approximately 50g
- confidence: high

Peanut butter:
- 1 tablespoon
- default grams: approximately 16g
- confidence: medium/high

Banana:
- 1 medium banana
- default grams: approximately 118g
- confidence: medium

================================================================================
IMPORTANT SERVING UNIT RULE
================================================================================

Use ranges and confidence.

Do not pretend estimated serving sizes are exact.

Bad:
1/2 cup cooked rice = exactly 92.000g

Better:
1/2 cup cooked white rice
- grams_default: 90g
- grams_min: 80g
- grams_max: 100g
- confidence: medium

This enables coaching like:

- “This is an estimate.”
- “Weighed grams would be more precise.”
- “Good enough for today.”
- “Protein entries are usually worth weighing.”
- “This carb estimate has medium confidence.”

================================================================================
NUTRITION ACTUALS CONFIDENCE MODEL
================================================================================

Architecture should define how logged foods affect confidence.

Possible confidence sources:

- weighed_grams
- package_label
- serving_unit_estimate
- user_saved_serving
- copied_previous_meal
- AI_candidate_user_confirmed
- unknown_or_low_confidence

This will matter later for coaching and AI explanations.

Example:

If user logs:
1/2 cup cooked rice

Backend should know:
- food: cooked white rice
- serving unit: 1/2 cup
- default grams used: 90g
- confidence: medium
- macros calculated from canonical nutrients per 100g
- actuals are estimated, not weighed

================================================================================
DETERMINISTIC FOOD SUGGESTIONS FUTURE CONTRACT
================================================================================

Planning should define how deterministic food suggestions will work later.

Inputs:
- approved nutrition targets
- logged actuals
- macro gaps
- canonical food catalog
- serving units
- user preferences if available
- confidence level
- training/recovery context later

Outputs:
- approved food candidates
- serving quantity
- estimated grams
- macro contribution
- reason
- confidence
- limitation note if needed

Example:

Protein gap:
35g protein remaining

Approved suggestions:
- Greek yogurt, 1 cup
- protein powder, 1 scoop
- chicken breast, 120g
- cottage cheese, 1 cup

AI should not create these facts.

Backend creates approved candidates.

AI may later assemble or explain them.

================================================================================
AI MEAL/SNACK CANDIDATE FUTURE CONTRACT
================================================================================

Planning should define the eventual provider role.

Provider input must include only approved facts:

- canonical foods
- approved serving units
- approved actuals
- approved targets
- approved gaps
- confidence notes
- user constraints/preferences
- forbidden claims

Provider output should be strict JSON, such as:

- snack_option_1
- snack_option_2
- meal_option_1
- meal_option_2
- rationale
- limitations
- confidence

Backend validation must reject:

- invented food
- invented serving unit
- invented grams
- invented macros
- unsupported health claim
- missing required fields
- non-schema output
- unsafe recommendation

================================================================================
QUESTIONS ARCHITECTURE MUST ANSWER
================================================================================

1. Should the next implementation milestone be Nutrition Catalog Diagnostic v1?

Recommended answer:
Yes.

2. Should curated canonical food expansion come before serving units?

Recommended answer:
Yes, but serving-unit modeling should be designed before expansion so the catalog schema does not need rework.

3. Should raw USDA/source import be implemented before curated expansion?

Recommended answer:
No, not as the first implementation. Use curated expansion first, then raw/staging import later.

4. Should serving sizes be exact numbers or ranges?

Recommended answer:
Ranges plus default grams and confidence.

5. Should serving-unit logging be allowed immediately in the UI?

Recommended answer:
Not necessarily. Backend contract first, UI later.

6. Should AI/provider participate in serving conversion?

Recommended answer:
No. Backend owns conversions.

7. Should AI/provider participate in meal/snack generation later?

Recommended answer:
Yes, but only from backend-approved foods, servings, actuals, targets, and gaps.

8. Should nutrition suggestions come before AI meal generation?

Recommended answer:
Yes. Deterministic food suggestions should come before AI-generated meal/snack candidates.

9. Should recovery be tackled before nutrition?

Recommended answer:
No. Recovery is weaker, but nutrition is the better next learning/personal-use priority.

10. Should workouts continue before nutrition?

Recommended answer:
No, unless a blocking workout regression appears. Workout foundation is good enough for now.

================================================================================
RECOMMENDED NEXT IMPLEMENTATION MILESTONE
================================================================================

Recommended:

Nutrition Catalog Diagnostic v1

Purpose:
Measure and report the current nutrition catalog state before expansion.

Diagnostic should answer:

- how many canonical foods exist
- how many active foods exist
- nutrient completeness
- alias coverage
- serving-unit coverage
- foods with no serving units
- foods with incomplete nutrient data
- duplicate or near-duplicate foods
- high-value staples missing
- current logging assumptions
- current target/actuals calculation dependencies
- whether food suggestions can safely use current data

Expected output:
A diagnostic tool/report and project memory update.

No large catalog expansion yet.

================================================================================
RECOMMENDED FULL NUTRITION FOUNDATION ROADMAP
================================================================================

Phase 1:
Nutrition Catalog Diagnostic v1

Goal:
Understand current catalog/data state.

Phase 2:
Nutrition Canonical Food Model Review v1

Goal:
Confirm whether current food models can support aliases, serving units, grams, confidence, and source metadata.

Phase 3:
Curated Food Catalog Expansion v1

Goal:
Add 150–300 high-value canonical foods.

Phase 4:
Serving Unit Normalization / Household Measure Conversion v1

Goal:
Add serving units for 50–100 high-value foods.

Phase 5:
Nutrition Logging Backend Contract v1

Goal:
Support logs by grams or serving unit.

Phase 6:
Nutrition Actuals Confidence v1

Goal:
Track precision/confidence of nutrition actuals.

Phase 7:
Nutrition Deterministic Food Suggestions v1

Goal:
Suggest safe food/snack options from macro gaps.

Phase 8:
Nutrition AI Meal/Snack Candidate Contract v1

Goal:
Let qwen/direct_ollama assemble approved meal/snack candidates inside strict validation.

================================================================================
STRICT NON-GOALS FOR THIS PLANNING MILESTONE
================================================================================

Do not implement catalog expansion.

Do not implement serving units.

Do not import USDA/source data.

Do not modify food logging.

Do not modify nutrition calculations.

Do not modify provider/Ollama behavior.

Do not add AI meal generation.

Do not modify Streamlit UI.

Do not modify workout generation.

Do not modify recovery engine.

Do not add migrations.

Do not add dependencies.

Do not commit snapshots, qa_artifacts, patch scripts, or local artifacts.

Do not use git add .

================================================================================
EXPECTED FILES TO UPDATE
================================================================================

Expected docs/project-memory only.

Likely files:

- docs/project_memory/current_state.md
- docs/project_memory/next_milestone.md
- docs/project_memory/open_questions.md
- docs/project_memory/project_state.json
- docs/project_memory/handoffs/architecture_handoff_current.md
- docs/project_memory/handoffs/backend_handoff_current.md
- docs/project_memory/handoffs/qa_handoff_current.md
- docs/project_memory/milestones/nutrition_catalog_serving_foundation_planning_v1.md

Optional if present/relevant:

- docs/project_memory/architecture_principles.md
- docs/project_memory/development_workflow.md

================================================================================
VALIDATION REQUIREMENTS
================================================================================

Docs-only validation:

git diff --check

python tools/project_memory_check.py
python tools/dev_assistant.py memory-check
python tools/dev_assistant.py stale-doc-check
python tools/dev_assistant.py continuity-brief
pytest tests/test_project_memory_check.py -q

scripts/dev_commit_check.ps1 -Mode docs-only

. .\scripts\fitness_commands.ps1
fsweep

git status --short

No browser smoke required.

No Linux runtime smoke required unless project policy chooses to pull docs milestones on Linux.

================================================================================
EXPECTED HANDOFF BACK TO ARCHITECTURE
================================================================================

Return:

Recipient:
Architecture

Branch:
feature/nutrition-catalog-serving-foundation-planning-v1

Milestone:
Nutrition Catalog + Serving Foundation Planning v1

Status:
IMPLEMENTED / DOCS VALIDATED / READY FOR ARCHITECTURE REVIEW

Proposed final status:
NUTRITION_CATALOG_SERVING_FOUNDATION_PLANNING_V1_ACCEPTED

Include:

- source main commit: f469c89
- latest feature commit
- feature snapshot filename if created
- files updated
- recommended nutrition sequence
- canonical food model planning decisions
- serving unit model planning decisions
- raw/staging import guidance
- AI/provider boundary guidance
- recommended next milestone
- validation summary
- clean working tree confirmation
- no app/runtime behavior changes confirmation

================================================================================
ACCEPTANCE CRITERIA
================================================================================

Architecture should accept only if:

1. Nutrition foundation sequence is documented.

2. Two-layer food catalog strategy is documented.

3. Serving unit / household measure conversion strategy is documented.

4. Confidence/range strategy is documented.

5. AI/provider nutrition boundary is documented.

6. Recommended next implementation milestone is clear.

7. Workouts are explicitly marked as good enough for now.

8. Recovery remains acknowledged but deferred behind nutrition foundation.

9. Docs validation is green.

10. No runtime/app behavior changed.

================================================================================
END ARCHITECTURE / PLANNING HANDOFF
================================================================================
