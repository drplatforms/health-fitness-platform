# Health & Fitness Platform — Product Vision and Strategic Roadmap

## Purpose

This document preserves the durable product direction for `fitness_ai`.

It is not a commit log, milestone-closeout ledger, or exhaustive feature backlog. Its job is to help future Architecture chats answer:

- What are we ultimately building?
- What already exists?
- What matters most next?
- Why is the roadmap ordered this way?
- What product principles should survive even as individual milestones change?

The roadmap may evolve as daily use exposes new friction, but changes should preserve the core product vision below.

## Product North Star

Build a local-first health, nutrition, recovery, and workout platform that can genuinely replace MyFitnessPal and other daily food/workout trackers for real everyday use.

The product should remain useful even with every AI/provider turned off.

AI may enhance the experience later, but the core value must come from fast daily use, excellent food and workout tracking, useful workout guidance, low-friction nutrition capture, adaptive progression and planning, strong mobile usability, meaningful longitudinal insight, and trustworthy user-owned data.

The goal is not to keep adding tabs or features. The goal is to make the product increasingly useful, connected, efficient, low-friction, personalized, and adaptive.

Daily use should drive prioritization.

## Core Product Principles

### Daily usefulness comes before feature count

Do not add features merely because they are possible. Every major feature should save time, reduce repetitive work, improve a real daily decision, make training or nutrition easier to execute, or help the product learn from accumulated history.

### Mobile is the primary daily-use surface

Desktop is suited to deep review, planning, history, analytics, administration, and large data sets.

Mobile should optimize for rapid capture, one-handed use, low tap count, minimal scrolling, strong thumb reach, progressive disclosure, fast search, and preserving active workflows.

Do not treat mobile as desktop compressed into a narrow viewport.

### The product should get easier with use

Repeated behavior should reduce future friction through recents, personal foods, favorites/staples, saved meals, remembered serving choices, recent exercises, previous set performance, and useful defaults.

### Data truth stays grounded

User health, nutrition, workout, and recovery state should remain grounded in persisted data and deterministic rules. AI should interpret grounded data, not replace it.

### Preserve user context during interaction

Temporary navigation or detail views should not destroy in-progress work. This includes switching between Log Food and My Foods, opening exercise instructions, checking substitutions, reviewing workout history, and returning to an active workout.

### Progressive disclosure over information overload

Show the information required for the current decision first while keeping deeper information available. Avoid giant warnings, filler prose, long desktop-style mobile pages, wasted space, and giant selectors when search, recents, or favorites would work better.

The preferred UI is compact, polished, practical, and data-dense without becoming overwhelming.

## Current Product Foundation

### Nutrition

Existing capabilities include canonical food search/logging, grams and serving-unit logging, nutrition targets, daily totals, recents, logged-food edit/delete, canonical food catalog curation, personal foods, archive/restore, personal-food revisions, serving-aware logging, and nutrition trend/report foundations.

The product is moving from basic nutrition correctness toward faster capture and lower daily friction.

### Training

Existing capabilities include equipment-aware planning, Quick / Standard / Extended workout sizing, catalog-backed exercise selection, stable exercise catalog identity, exercise rotation coverage, substitutions, workout preview/selection, workout start lifecycle, set logging/edit/delete, planned-versus-actual tracking, completion review, execution history, progression context, structured exercise explanations, deterministic instruction coverage, instruction API/read surface, and polished desktop explanation interaction.

The product is moving from workout generation toward a smarter, more adaptive training system.

### Recovery

Existing capabilities include recovery check-ins, sleep, energy, soreness, stress/fatigue, body weight, readiness state, and longitudinal recovery data.

Recovery should eventually shape training recommendations and planning without forcing the user through heavy forms or unnecessary coaching prose.

### Daily UX

Recent work established a compact Today loop, high-priority Nutrition and Log Food surfaces, compact logged-food views, Today workout access, Recovery access, the overlapping Log Food / My Foods workspace with preserved state, desktop workout layout improvements, and exercise explanations integrated into the workout experience.

The next major UX challenge is mobile.

## Current Strategic Position

The product has moved beyond basic backend foundations.

The strategic shift is now:

```text
Build the core tracking system
        ↓
Make it genuinely pleasant to use every day
        ↓
Reduce repeated manual work
        ↓
Add smarter adaptation and planning
        ↓
Layer selective intelligence on top of trustworthy history
```

The highest-value work is increasingly driven by daily friction rather than missing backend capability.

## Current Strategic Priority — Exercise Catalog and Visualization Expansion

The immediate strategic priority is the exercise-catalog and visualization expansion program.

Visualization v2 establishes the provider-neutral visual-media foundation.

The active objective is to expand the internal canonical catalog from 240 exercises to at least 450-500 canonical exercises, using the free AscendAPI inventory as the primary candidate source.

AscendAPI is not the platform source of truth. New exercises must be deliberately reviewed, canonicalized, deduplicated, assigned internal taxonomy, equipment and measurement semantics, structured instructions, visual-media relationships, and appropriate workout-generation eligibility.

Catalog utilization and rotation must be reviewed and improved as necessary so expanded catalog coverage produces real workout variety rather than unreachable inventory.

Until this objective is substantially achieved and Architecture closes the expansion program, unrelated major roadmap milestones are not the primary implementation focus.

Injury / Temporary Limitation Mode is already completed.

Smart Exercise Substitutions is already completed.

Older roadmap sections below are retained as durable historical product direction, but their ordering is not current implementation authority and individual items may already be complete.

## Immediate Roadmap

### 1. Personal Food Serving Display Fix v1

Fix the confirmed display bug where nutrition-label personal foods show normalized per-100g nutrients in My Foods instead of the persisted per-serving values entered by the user.

Expected scope:

- display-layer correction;
- no backend/schema/migration change;
- preserve normalized values for logging calculations;
- verify custom servings such as `1 bar`, `1 scoop`, `1 packet`, `1 bottle`, and `2 cookies`.

### 2. Theme System + Dark Mode

Introduce a semantic theme foundation rather than scattering dark-mode overrides across existing components.

Direction:

- semantic color tokens;
- preserve the accepted light theme first;
- add dark theme values;
- system preference when no explicit choice exists;
- persisted user preference;
- avoid first-paint light flash;
- do not remount application state when switching themes.

Dark mode should become a foundation for future UI work, especially the mobile redesign.

### 3. Mobile UX Foundation

This is a major product initiative, not a responsive-CSS cleanup.

Primary goals:

- radically reduce scrolling;
- improve one-handed usability;
- reduce tap count;
- create thumb-reachable navigation/actions;
- use progressive disclosure;
- make Today a focused mobile command center;
- establish reusable temporary-action patterns such as bottom sheets;
- remove desktop interaction assumptions from mobile workflows.

### 4. Active Workout Mobile UX

Turn the active workout experience into a focused execution tool with the current exercise front and center, previous performance visible, fast set entry, useful defaults, easy save/edit/delete, instructions without losing state, substitutions without navigation churn, and clear progression context.

### 5. Mobile Food Logging and Recovery UX

Continue the mobile pass around the highest-frequency workflows.

Nutrition direction: fast search, recents, personal foods, future favorites/staples, saved meals later, and low-friction serving selection.

Recovery direction: a fast check-in with large touch targets, minimal typing, and reliable controls.

## Next Major Capability Roadmap

### Smart Exercise Substitutions

Move beyond simple replacements toward context-aware substitutions.

A future substitution flow should rank options rather than simply swap blindly:

```text
Best Match
One-Arm Dumbbell Row

Also Compatible
Cable Row
Band Row
Inverted Row
```

The ranking should consider:

- movement pattern;
- target muscles;
- available equipment;
- user constraints;
- exercise history;
- recent variation;
- workout intent;
- fatigue and recovery context.

The system should explain why a replacement is appropriate:

> Same horizontal-pull movement pattern and compatible with your current equipment.

Later:

> You performed chest-supported rows in your previous two sessions. One-arm dumbbell rows provide a similar training stimulus while adding variation.

The substitution engine should remain deterministic and explainable before AI is used to improve wording.

### Barcode Nutrition Scanning

A high-value daily-friction feature.

Goal:

```text
scan barcode
→ identify packaged food
→ confirm serving
→ log
```

Core barcode lookup generally does not require AI.

### Nutrition Label Scanning

Use camera/image capture to extract nutrition-label information and create a loggable food.

Likely flow:

```text
capture label
→ extract nutrition fields
→ user confirms/corrects
→ save/log
```

This is a strong candidate for OCR/vision or multimodal AI assistance, with user confirmation before persisted nutrition is trusted.

### Adaptive Progression Engine

This is one of the highest-value long-term capabilities.

Use execution history to approve progression decisions from:

```text
planned workout
+ actual performance
+ weight
+ reps
+ RIR/RPE where available
+ completion history
+ recent recovery
→ ProgressionDecision
→ approved recommendation
```

Examples:

> Last session: 3 × 10 at 25 lb, average RIR 3.
> Recent recovery: stable.
> Try 3 × 11–12 today at the same weight.

Or:

> Keep the load unchanged and aim for cleaner execution.

Or:

> Recent effort has been harder than planned. Hold progression today.

Progression should begin as transparent deterministic logic.

AI may later explain the approved decision, but it should not invent performance history or control progression authority.

### Weekly Training Planner

Move from isolated workout generation toward a real adaptive training system that thinks across the next seven days.

Example:

```text
Monday      Lower
Tuesday     Recovery
Wednesday   Upper
Thursday    Rest
Friday      Full Body
Saturday    Optional Conditioning
```

When life disrupts the plan, the system should adapt rather than treat the week as failed.

Example:

> Wednesday was missed. Move Upper to Thursday and preserve at least one recovery day before the next full-body session.

Planning should consider:

- training frequency;
- recovery between sessions;
- movement and muscle coverage;
- planned volume;
- completed and missed work;
- equipment availability;
- progression needs;
- optional versus required sessions.

This is the step that turns the product from a workout generator into a training system.

### Meal Builder, Saved Meals, and Gap-Aware Food Suggestions

Reduce repetitive nutrition logging by combining foods into reusable meals, saving common meals, logging them quickly, and preserving serving context.

The meal builder should also evolve into an actionable nutrition-gap tool.

Example:

> You have roughly 45 g of protein and 60 g of carbs remaining based on today's approved targets.

Then offer grounded options:

```text
Quick option
Chicken breast + rice

Lighter option
Greek yogurt + banana + oats

Snack option
Cottage cheese + fruit
```

Food selection and nutrient math should come from approved food data.

AI may improve the explanation:

> Since you're still short on both protein and carbs, chicken and rice would close both gaps more efficiently than another high-fat snack.

Possible extensions:

- repeat yesterday's meal;
- copy meals between days;
- favorite/staple meals;
- frequently used meal suggestions;
- quick portion adjustments.

### Exercise History Inside the Workout

Exercise history should be available directly where the user makes training decisions.

Example:

```text
Dumbbell Bench Press

Last 5 sessions

Date       Weight     Reps     RIR
Jul 10     25 lb      12       2
Jul 5      25 lb      11       2
Jun 29     25 lb      10       3

Recent trend:
Reps are gradually increasing at similar effort.
```

This should support:

- recent performance;
- progression over time;
- previous working weights;
- RIR/RPE trends where available;
- best sets;
- volume trends;
- workout consistency;
- exercise-specific notes.

The history should support the current workout decision, not merely exist as a separate analytics screen.

## Explainable Recommendations — “Why Am I Doing This?”

The platform should make its intelligence visible.

Workout recommendations should eventually support a compact explanation such as:

> Chest-supported rows are included today because your plan needs horizontal pulling volume without adding much lower-back fatigue. Your available bench and dumbbells make this a good fit for your current equipment.

The explanation can be grounded in:

```text
current workout
+ movement-pattern needs
+ equipment
+ recovery
+ recent training history
+ exercise knowledge
→ grounded explanation
```

This pattern should expand beyond exercise selection to:

- progression decisions;
- substitutions;
- workout intensity changes;
- nutrition recommendations;
- weekly schedule adjustments.

The user should be able to understand why the system made a recommendation without exposing backend implementation details.

## Meaningful Personal Records and Milestones

Avoid shallow gamification and badge overload.

Useful milestones may include:

- new rep bests;
- new load bests;
- workout completion streaks;
- consistency records;
- volume milestones;
- improved RIR consistency;
- first pain-free return to an exercise;
- improved sleep consistency;
- increased workout completion;
- protein-target consistency.

Examples:

> New rep best: 12 reps at 135 lb.

> You've completed 20 planned workouts.

> Your average working-set RIR has become more consistent over the past month.

Milestones should reinforce useful behavior and progress, not turn the product into a “gym-bro casino.”

## “What I Have at Home” Food Mode

Allow users to maintain a lightweight pantry/staples list such as:

- eggs;
- chicken;
- rice;
- oatmeal;
- tuna;
- yogurt.

Nutrition recommendations should prioritize foods the user actually has.

Example:

> You're still lacking protein. Since you have canned tuna and chicken breast available, either would help close the gap.

This can later connect directly to the meal builder and nutrition-gap system.

## Voice Logging

Voice input could dramatically reduce logging friction.

Nutrition example:

> I ate three eggs, two pieces of toast, and a banana.

Workout example:

> I did 3 sets of bench. 135 for 10, 9, and 8.

Architecture principle:

```text
voice
→ AI parses candidate structured records
→ canonical matching / validation
→ user confirms
→ backend stores approved records
```

AI proposes structure. It does not silently create trusted records.

Voice logging can eventually cover:

- food;
- sets;
- body weight;
- recovery notes;
- workout notes.

## Recovery Pattern Discovery

Once enough longitudinal data exists, the platform should surface careful observational patterns.

Examples:

> Over the past six weeks, workouts following less than six hours of sleep were associated with higher reported effort and more skipped exercises.

> Your soreness tends to increase after consecutive lower-body sessions with fewer than two recovery days between them.

These should be framed as observations, not medical conclusions.

A future `Personal Insights` surface could summarize patterns across:

- sleep;
- soreness;
- stress;
- readiness;
- workout completion;
- effort;
- nutrition consistency;
- progression.

## Tomorrow Readiness Preview

Provide a cautious forward-looking training preview without pretending to predict physiology perfectly.

Example:

> Based on today's training load, recent sleep, soreness trend, and tomorrow's planned session, tomorrow currently looks suitable for moderate training if recovery remains stable overnight.

The next-day check-in then confirms or adjusts the plan.

This creates a useful loop:

```text
expected recovery
→ overnight data
→ actual recovery
→ training decision
→ actual performance
→ future calibration
```

## Wearable Integrations

Potential future integrations:

- Apple Health;
- Garmin;
- Fitbit;
- Oura;
- Health Connect.

Useful signals may include:

- sleep duration;
- resting heart rate;
- steps;
- recorded workouts;
- HRV where appropriate and available.

Wearables should enrich the product, not become a dependency.

Manual entry must remain a first-class experience.

## Longer-Term Product Intelligence

### Grounded Personal Coach

The long-term conversational coach should answer questions about the user's own approved data rather than behave like generic ChatGPT.

Examples:

- Why did you lower my workout intensity today?
- Have my workouts actually been improving?
- What exercises have I been skipping most?
- Why are you recommending more carbs today?
- What did I do last time I trained chest?
- Why was this exercise selected?
- Why is today's progression recommendation different from last week?

The system should retrieve:

```text
approved user data
+ exercise knowledge
+ training history
+ nutrition history
+ recovery trends
+ approved recommendations
→ grounded answer
```

Do not restart broad AI-generated daily filler prose.

The useful architecture is:

```text
grounded product data
→ deterministic analysis
→ targeted context retrieval
→ selective AI interpretation
```

The coach should explain approved system decisions, identify patterns, and answer questions without becoming the source of truth.

### Selective RAG / Context Retrieval

Introduce RAG only where a real retrieval problem exists, such as trusted exercise knowledge, trusted reference material, user-specific historical context, or contextual coaching explanations.

Do not introduce RAG merely because the product uses AI.

## AI Product Rule

The project should not become an AI demo.

Build an excellent health and fitness product first. Use AI where it removes friction, synthesizes complex grounded context, or enables a capability deterministic software cannot provide efficiently.

Good AI candidates include nutrition-label extraction, contextual longitudinal analysis, natural-language explanation, selective coaching synthesis, and richer image/document understanding.

Poor AI candidates include replacing simple calculations, generating filler coaching prose, making basic CRUD unpredictable, or inventing facts already available in structured data.

## Developer Context Infrastructure

Projectmem and OKF Generator were evaluated as potential agent-context tooling.

### Projectmem

Promising for workflow decisions, known failures, architecture constraints, and project-history retrieval. It may become useful when Architecture-chat onboarding or agent context begins to strain again.

It should supplement, not immediately replace, canonical project memory.

### OKF Generator

Useful for broad code orientation, symbol discovery, and cross-layer file identification.

Observed limitations include unreliable relationship/caller-callee results in tested cases, weaker JSX relationship understanding, and no meaningful CSS/theme coverage.

Keep it optional for targeted investigations rather than mandatory infrastructure.

### Current operating choice

Use:

```text
compact curated Architecture onboarding
+ canonical repository snapshot
+ durable project memory
+ this product roadmap
```

Revisit Projectmem first if onboarding becomes too large or repeated historical mistakes return.

## Cross-System Intelligence — The Larger Product Direction

The next generation of the platform should not be about adding more tabs.

The systems should become increasingly aware of one another.

```text
skipped exercise
→ execution history

execution history
→ progression

progression
→ weekly planning

recovery
→ training decisions

training demand
→ nutrition needs

nutrition gaps
→ meal suggestions

all approved decisions
→ explainable coaching
```

The long-term product becomes powerful when these systems form one coherent loop.

This is the difference between a collection of trackers and a connected coaching platform.

## Roadmap Ordering Principle

The roadmap is directional, not sacred.

The order should change when daily use exposes higher-value friction.

Examples:

- a recurring food-logging bug may outrank a planned feature;
- mobile usability may outrank a sophisticated training feature;
- barcode scanning may move earlier if manual food entry remains the dominant daily pain point.

The question should always be:

> What improvement would make the product meaningfully better to use every day?

Do not lose the long-term roadmap, but do not follow it blindly when real usage gives better information.

## High-Level Strategic Sequence

```text
Personal Food Serving Display Fix
        ↓
Theme System + Dark Mode
        ↓
Mobile UX Foundation
        ↓
Active Workout Mobile UX
        ↓
Mobile Food / Recovery UX
        ↓
Smart Exercise Substitutions
        ↓
Barcode Nutrition Scanning
        ↓
Nutrition Label Scanning
        ↓
Adaptive Progression Engine
        ↓
Weekly Training Planner
        ↓
Exercise History Inside Workout
        ↓
Meal Builder / Saved Meals / Pantry Awareness
        ↓
Meaningful Records and Personal Insights
        ↓
Voice Logging
        ↓
Recovery Pattern Discovery / Tomorrow Readiness
        ↓
Wearable Integrations
        ↓
Grounded Personal Coach / Selective RAG
```

Individual milestones inside these initiatives should remain small enough to review, validate, and safely close.

## Highest-Value Long-Term Opportunities

Beyond the immediate mobile and friction-reduction work, the highest-value strategic opportunities are:

1. **Adaptive Progression Engine** — workouts truly evolve with the user.
2. **Weekly Training Planner** — isolated workouts become actual adaptive programming.
3. **Grounded Personal Coach / RAG** — the intelligence becomes accessible conversationally.
4. **Gap-Aware Meal Builder** — nutrition targets become concrete eating decisions.
5. **Voice Logging** — friction drops substantially across nutrition and training.

These priorities are directional and may move as real daily use reveals stronger opportunities.

## Roadmap Stewardship

Architecture owns strategic roadmap changes. Codex may implement Architecture-approved edits, which should update the relevant roadmap section instead of appending historical milestone noise. Projectmem may later help retrieve decisions behind roadmap changes, but this markdown document remains the human-readable strategic source of truth.

## Definition of Success

The platform succeeds when the user prefers using it over established food and workout trackers because it is faster for real routines, more personal, more transparent, better connected across nutrition/recovery/training, easier to use on mobile, increasingly helpful as history accumulates, trustworthy with personal data, useful without requiring AI, and intelligently enhanced when AI genuinely adds value.

The ultimate product should feel less like a collection of tracking forms and more like a personal operating system for everyday health, nutrition, and training.
