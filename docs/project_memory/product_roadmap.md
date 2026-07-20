# Health & Fitness Platform — Product Vision and Strategic Roadmap

> Protected strategic roadmap. This file preserves product direction and is not active implementation authority. Current operational truth is owned by `docs/project_memory/current_truth.json`.

## Purpose

This document preserves the durable product direction for `fitness_ai`.

It is the canonical strategic roadmap, not a commit log, milestone-closeout ledger, or implementation authorization document. `current_state.md` records where the repository is now; this file records where the product is headed and why.

The roadmap is directional. Architecture may reorder bounded milestones when real daily use reveals higher-value friction, but changes should preserve the product north star, trust model, and sequencing principles below.

## Product North Star

Build a personal health intelligence system that combines excellent nutrition tracking, workout execution and programming, recovery awareness, longitudinal analysis, and moment-of-need coaching in one coherent product.

The defining differentiator is not generic personalization. The system should become more valuable with continued use because it develops an increasingly accurate, evidence-backed model of the individual user:

- what they actually do;
- what they consistently avoid;
- which exercises and routines work well for them;
- how they respond to training volume, recovery, sleep, and nutrition;
- which schedules and situations create friction;
- what habits correlate with better or worse outcomes;
- which recommendations they follow, reject, or repeatedly modify.

The long-term product should be able to produce observations such as:

> Your strongest comparable lower-body sessions usually follow a substantial meal two to four hours before training, while several recent underperforming sessions followed unusually low daytime intake.

That level of personalization should emerge from accumulated grounded history, not from invented AI narrative.

The ultimate product should feel less like a collection of trackers and more like a personal operating system for everyday health, nutrition, recovery, and training.

## True Product Pillars

The platform should evolve around eight connected capabilities.

### CAPTURE

Make useful data effortless to record.

### PLAN

Turn goals, constraints, schedules, equipment, and current state into realistic actions.

### EXECUTE

Help the user perform workouts and nutrition decisions correctly with minimal friction.

### UNDERSTAND

Explain current state, trends, and meaningful changes clearly.

### ADAPT

Change plans based on evidence, constraints, recovery, and actual outcomes.

### LEARN

Discover what works for the individual over time.

### PREDICT

Anticipate likely friction, meaningful deviations, and useful intervention windows without pretending to predict physiology perfectly.

### ASSIST

Help the user make a better decision at the moment they actually need one.

These pillars should converge over time. A feature that captures data but never improves planning, execution, understanding, or personalization should be questioned.

## Core Product Principles

### Daily usefulness comes before feature count

Prioritize work that saves time, reduces repetitive effort, improves a real daily decision, makes training or nutrition easier to execute, or increases the value of accumulated history.

### The product should get better the longer it is used

Recents, saved meals, exercise history, preferences, successful substitutions, training response, personal baselines, adherence patterns, food habits, and historical outcomes should progressively reduce friction and improve relevance.

### Deterministic truth before generative interpretation

Backend-owned data, calculations, constraints, validation, persistence, confidence, and provenance remain authoritative.

AI may identify, summarize, explain, retrieve, or creatively assemble backend-approved options, but it must not silently replace grounded product truth.

### Useful without AI

The core platform must continue to function with cloud AI, local AI, and all generative providers disabled.

AI provider independence is a product and architecture strength, not merely an implementation detail.

### Frictionless capture is strategic infrastructure

The best intelligence layer is useless if logging becomes annoying. Nutrition, workout, recovery, weight, and other high-frequency inputs should continually move toward fewer taps, stronger defaults, reusable history, voice or natural-language assistance where appropriate, and confirmation rather than repetitive manual reconstruction.

### Explainability everywhere

Every meaningful recommendation should eventually have a clear answer to “Why?”

Examples include workout changes, exercise selection, substitutions, progression decisions, nutrition suggestions, readiness interpretations, and target adjustments.

### Be honest about uncertainty

Restaurant meals, photo-estimated portions, wearable values, metabolic calibration, body-composition estimates, and longitudinal correlations should expose assumptions and confidence instead of presenting false precision.

### Mobile is the primary daily-use surface

Mobile should optimize for one-handed use, low tap count, minimal scrolling, thumb reach, progressive disclosure, fast capture, and preservation of in-progress workflows.

Desktop should support deeper review, analytics, planning, administration, and larger information surfaces.

### Privacy and user ownership are product features

Users should understand what is stored, what leaves the device, what AI can see, and how to export or delete their data. The project’s local-first roots should remain an architectural advantage as the product matures.

## Current Product Foundation

The repository has already moved well beyond a basic tracker. The following are foundations, not future roadmap promises.

### Nutrition foundation

The current product includes canonical and personal food workflows, serving-aware logging, barcode scanning, saved meals, nutrition targets and daily totals, historical logging behavior, deterministic catalog-driven food suggestions, and direct nutrition gap actions.

### Training foundation

The current product includes persistent workout execution and set history, equipment-aware workout generation, Quick / Standard / Extended sizing, adaptive progression, weekly training planning, smart exercise substitutions, temporary injury / limitation handling, exercise history and progress analytics, structured exercise instruction, and exercise visual-media resolution.

### Recovery foundation

The current product includes recovery check-ins, readiness-oriented state, sleep, energy, soreness, stress/fatigue, body weight, and longitudinal recovery intelligence foundations.

### Daily-use and UX foundation

The current product includes dedicated mobile daily-driver workspaces, compact workout execution surfaces, mobile navigation, a semantic theme system with dark-mode preference, and a growing emphasis on low-friction daily workflows.

### Current exercise-system baseline

At the accepted Visualization v2 closeout:

- the internal catalog contains 240 canonical exercises;
- there are 231 accepted visual identities;
- 138 / 240 canonical exercises have configured visual guidance through direct local, accepted shared-local, or explicitly reviewed provider media;
- the provider-neutral media architecture preserves local media authority and text-only fallback;
- AscendAPI Free is a candidate and media source, not internal catalog truth.

## Current Strategic Priority — Exercise Catalog and Visualization Expansion

This is the active program now.

The objective is to expand the internal canonical exercise catalog from 240 exercises to at least 450–500 high-quality canonical exercises before returning to unrelated major product milestones.

AscendAPI Free is the primary candidate inventory for this expansion, but admission into the product must remain deliberate.

Every accepted exercise should have appropriate internal ownership of:

- canonical identity and deduplication;
- exercise family and physical variant relationships where useful;
- movement pattern;
- primary and secondary muscles;
- equipment requirements;
- unilateral / bilateral semantics where relevant;
- loading and stability characteristics where relevant;
- prescription and measurement semantics;
- difficulty and other useful structured attributes where justified;
- structured setup and execution instructions;
- cues, common mistakes, and safety guidance where appropriate;
- visual identity and approved visual-media relationships;
- workout-generation eligibility and reachability.

The expansion program is not complete merely because more rows exist in the catalog. Catalog utilization and workout rotation must be audited as necessary so newly admitted exercises can produce meaningful training variety.

Provider media and knowledge remain supplemental. The internal curated catalog and media layer remain the product source of truth, and provider rights must be revisited before monetized or SaaS use.

Until this program is substantially complete and Architecture explicitly closes it, unrelated major roadmap milestones are not the primary implementation focus.

## Completed Foundations That Must Not Reappear as Future Milestones

The following capabilities already exist in accepted form and should be treated as foundations for deeper future iterations rather than as unfinished first versions:

- Theme System and Dark Mode;
- Mobile Daily-Driver Navigation and Compaction;
- Active Workout Mobile UX;
- Barcode Scanning v1;
- Meal Builder v1;
- Adaptive Progression Engine v1;
- Weekly Training Planner v1;
- Smart Exercise Substitutions v1;
- Injury / Temporary Limitation Mode v1;
- Exercise History & Progress Analytics v1;
- deterministic nutrition gap suggestions and actions;
- Visualization v2 provider-media integration.

Future roadmap work may deepen these systems without pretending their foundational milestones are still pending.

# Strategic Roadmap After the Current Exercise Expansion Program

The horizons below are ordered by product leverage and dependency, not by rigid release dates. Architecture should continue authorizing bounded milestones rather than attempting entire horizons at once.

## Horizon 1 — Daily Command Center and Frictionless Capture

The Today experience should become the primary reason the user opens the app each day.

It should answer:

> What matters today?

without forcing the user to inspect multiple dashboards.

The mature Daily Command Center should progressively unify:

- readiness and recovery status;
- sleep, soreness, energy, stress, and recent training load;
- today’s planned workout and realistic duration;
- nutrition progress and the most important current gap;
- simple remaining targets;
- relevant food suggestions;
- quick access to logging;
- one meaningful, evidence-backed insight rather than a wall of generated prose.

Examples of useful daily output:

> Training looks appropriate today, but your legs are still carrying fatigue from Tuesday.

> Protein is currently your largest nutrition gap.

> You have about 35 minutes available tonight, so the highest-value version of today’s session is the condensed plan.

### Capture priorities

Continue attacking logging friction across all high-frequency workflows.

Nutrition opportunities include:

- favorites and staples;
- frequently eaten combinations;
- copy previous meal;
- copy yesterday or selected prior day;
- nutrition-label scanning;
- photo-assisted food identification with confirmation;
- natural-language logging;
- voice logging;
- restaurant and takeout estimation with explicit uncertainty;
- richer custom serving workflows.

Workout opportunities include:

- faster set entry and stronger previous-performance defaults;
- rest timers;
- warm-up set support;
- supersets, circuits, drop sets, and AMRAP structures where they fit the existing execution model;
- faster substitutions and skipped-exercise handling;
- voice-assisted set logging such as “185 for 8, RIR 2.”

Recovery should move toward an approximately five-second confirmation workflow, with future integrations prefilling signals when available.

## Horizon 2 — Adaptive Training That Works Around Real Life

The existing weekly planner, progression engine, substitutions, recovery intelligence, and limitation mode provide the foundation. The next generation should make the system more realistic and personally adaptive.

### Adaptive programming

The platform should increasingly combine:

- training goal;
- recent exercise exposure;
- progression history;
- current recovery;
- available equipment;
- available time;
- weekly frequency;
- user preferences;
- temporary limitations;
- actual prior response.

Future capabilities include:

- dynamic set, rep, RIR, and load recommendations;
- more nuanced progression than automatic fixed load increases;
- training-volume response analysis;
- fatigue-aware deload and workload decisions where sufficiently supported;
- preserving the highest-value work when time is limited.

### Minimum Viable Workout Mode

When the planned session no longer fits the available time, the system should offer a condensed version that preserves the highest-value work rather than treating the day as a failure.

### Calendar-aware fitness planning

Future calendar integration should understand realistic training windows around work, appointments, travel, and other commitments.

The product should eventually say:

> Tuesday became unusually busy. Your next two realistic training windows are Thursday evening and Saturday morning.

rather than merely reporting a missed workout.

### Workout duration intelligence

The platform should learn how long the individual actually takes to complete different session types and use those personal estimates when planning.

### Environment-aware training

Support persistent equipment environments such as:

- Home Gym;
- Commercial Gym;
- Hotel;
- Bodyweight / Minimal Equipment.

Travel Mode should temporarily adapt planning and available exercises, then restore normal programming afterward.

### Low-Energy / Bad-Day Mode

A user who feels terrible should be able to choose among a normal session, reduced session, mobility/recovery option, or rest without guilt-driven product behavior.

## Horizon 3 — Nutrition Decision Intelligence

The product should progress from “what are my numbers?” toward “what should I actually eat?” while keeping nutritional calculations deterministic.

### Constraint-aware food suggestions

Support useful request constraints such as:

- cheap;
- quick;
- filling;
- sweet or savory;
- no cooking;
- meal or snack;
- foods already available;
- calorie and macro bounds;
- preparation-time limits.

### Intelligent Meal Builder

Build on the accepted saved-meal foundation so the system can assemble realistic meals under grounded nutritional constraints.

The backend should calculate and validate nutrition. AI may help creatively assemble options, explain substitutions, or interpret a natural-language request, but it should never invent nutritional truth.

### Personal Food Graph

Learn from repeated food behavior:

- liked and disliked foods;
- frequently eaten foods;
- common meal combinations;
- repeatedly purchased staples;
- convenience preferences;
- foods or suggestions the user consistently rejects.

Over time, “Suggest something to eat” should become personal rather than generic.

### Pantry intelligence

Potential future inventory support includes refrigerator, pantry, and freezer items, approximate remaining quantities, and expiration awareness.

This can later support meal suggestions and grocery planning.

### Intelligent grocery lists

Use historical consumption, pantry state, planned meals, nutritional goals, and eventually budget constraints to suggest realistic grocery lists.

### Budget-aware nutrition

Allow users to optimize food decisions around both nutritional goals and grocery budget, with transparent assumptions rather than fake precision.

### Restaurant / Takeout Mode

Handle uncertain meals honestly with ranges, confidence, assumptions, and user confirmation rather than pretending an unmeasured restaurant meal has an exact calorie count.

### Photo-assisted food logging

Computer vision may propose likely foods and estimated portions, but the user confirms the structured result and the backend maps confirmed items to grounded food records and calculations.

## Horizon 4 — Personal Measurement, Metabolic Calibration, and Baselines

The platform should help users understand change without overreacting to noisy individual measurements.

### Weight trend intelligence

Show:

- raw weight;
- rolling average;
- trend;
- estimated rate of change;
- expected short-term noise.

A useful system should be able to explain that scale weight may rise while the underlying trend remains flat.

### Personal metabolic calibration

After enough reasonably complete data exists, cautiously estimate observed maintenance from weight trend, intake, activity, and logging quality.

This should remain conservative, confidence-aware, and transparent about uncertainty.

### Body composition tracking

Potential measurements include weight, waist, chest, arms, thighs, hips, and explicitly uncertain body-fat estimates.

### Standardized progress photos

Guide consistent pose, camera angle, distance, and lighting, with chronological comparison and optional future alignment assistance.

### Personal Baseline Engine

Learn what “normal” means for the individual across signals such as:

- sleep;
- intake;
- workout frequency;
- soreness;
- energy;
- body-weight variability;
- training volume;
- daily activity.

Personal deviation should eventually matter more than generic thresholds alone.

## Horizon 5 — Longitudinal Personal Intelligence

This is where the platform begins to become a genuine personal analyst rather than a tracker.

### Change-point detection

Detect meaningful shifts such as sustained changes in steps, training frequency, protein consistency, sleep, or logging behavior.

### “What Changed?” analysis

Allow the user to ask why an outcome changed and compare the surrounding evidence across nutrition, activity, training, recovery, and data completeness.

Example:

> Three things changed around the same period: daily steps decreased, weekend intake increased, and nutrition logging became less complete.

### Structured personal insights

Longitudinal findings should be stored as structured, inspectable evidence rather than disappearing AI prose.

Useful fields may include:

- hypothesis;
- supporting evidence;
- confidence;
- time range;
- relevant data sources;
- known limitations.

### Personal N-of-1 experiments

The system may suggest bounded personal experiments when a plausible pattern exists, track baseline and intervention periods, and report outcomes with appropriate sample-size caution.

### Predictive friction detection

Learn when plans repeatedly fail and intervene before the likely failure window.

Example:

> Tomorrow looks unusually busy. Would you rather move the workout earlier or use the 30-minute version?

### Adherence intelligence

Move beyond a single adherence percentage and understand why behavior breaks down:

- scheduling conflicts;
- excessive preparation effort;
- disliked exercises;
- repeatedly ignored meal suggestions;
- unsuitable workout timing;
- recurring substitution patterns.

The product should adapt to those findings.

### Weekly Intelligence Review

Provide one high-quality weekly review covering:

- what improved;
- what declined;
- what changed;
- what seemed to work;
- what matters most next week.

Avoid constant low-value AI chatter.

### Meaningful personal records

Recognize more than maximal weight lifted:

- rep PRs;
- volume PRs;
- estimated 1RM milestones;
- first-time movement achievements;
- consistency records;
- adherence milestones;
- body-measurement progress;
- meaningful recovery or fitness trends.

## Horizon 6 — Recovery Intelligence and Wearable Integration

Recovery should become a real decision-support system, not another dashboard score.

Potential inputs include:

- sleep;
- energy;
- soreness;
- stress;
- recent training load;
- nutrition support;
- steps and activity;
- heart-rate signals;
- wearable data where available.

Longitudinal recovery intelligence should focus on the individual’s observed patterns while avoiding medical diagnosis claims.

Potential integrations include:

- Samsung Health / Health Connect;
- Apple Health;
- Garmin;
- Fitbit;
- Oura;
- Whoop.

Wearable values should be treated as signals with source-specific uncertainty, not unquestioned truth.

Manual entry must remain first-class.

## Horizon 7 — Explainable Conversational Assistance

The conversational layer should sit on top of grounded product intelligence rather than replace it.

### “Why?” everywhere

Meaningful system decisions should expose their reasons and supporting evidence.

### Voice assistant

Potential interactions include:

- What am I doing today?
- How much protein do I have left?
- What weight did I use last time?
- Substitute this exercise.
- Log 185 for eight.

### True personal health coach

The mature coach should understand the user’s current state, history, plans, recent decisions, preferences, and limitations.

It should answer grounded questions such as:

- Should I train today?
- Why has my bench stopped progressing?
- What should I eat tonight?
- What changed when my weight-loss trend slowed?
- Why did this workout change?

### Selective RAG and contextual retrieval

Use retrieval only where a real grounding problem exists:

- trusted exercise knowledge;
- user-specific history;
- approved recommendations;
- longitudinal evidence;
- trusted nutrition or recovery reference material.

The preferred architecture remains:

```text
grounded product data
→ deterministic analysis
→ targeted context retrieval
→ selective AI interpretation
```

Do not restart broad AI-generated daily filler prose.

## Horizon 8 — Platform Maturity, Portability, and SaaS Extensions

These capabilities matter as the product grows but should not distract from daily personal usefulness prematurely.

### Offline-first / PWA

Core daily workflows should eventually remain usable with poor connectivity and synchronize safely later.

### Cross-device experience

Support phone, desktop, and tablet coherently, with potential smartwatch execution surfaces later.

### Smart notifications

Notifications should be contextual and learn what the user actually responds to rather than becoming generic nagging.

Potential triggers include planned workouts, meaningful logging gaps, recovery check-ins, weekly reviews, and genuine milestones.

### Privacy controls

Potential mature controls include:

- clear data-source visibility;
- AI/provider visibility;
- local-only or AI-disabled operation where feasible;
- export;
- deletion;
- transparent external-data boundaries.

### Professional export

Provide useful, non-diagnostic reports or CSV/PDF exports users can share with a trainer or healthcare professional.

### Coach / Trainer Mode

A future SaaS extension could allow professionals to manage consenting clients across workouts, adherence, progression, recovery, and high-level nutrition summaries.

### Accountability and social features

Potential late-stage features include partner accountability, private sharing, and small challenges. Do not turn the product into a social network.

## Cross-System Intelligence — The Real Destination

The product becomes powerful when the systems stop behaving like separate trackers.

```text
calendar and real-life constraints
→ realistic training plan

recovery + recent training
→ appropriate session demand

exercise history + preferences + limitations
→ personalized exercise selection

actual performance
→ progression and volume decisions

training demand + nutrition state
→ useful food guidance

food behavior + pantry + preferences
→ realistic meal suggestions

all accumulated history
→ personal baselines and longitudinal insights

all approved decisions + evidence
→ explainable coaching
```

The long-term system should increasingly learn:

- which workouts the user enjoys;
- which exercises they respond to;
- how much training they tolerate;
- how long they usually need to recover;
- what foods and meals help them stay consistent;
- what schedules predict missed workouts;
- how sleep, activity, and nutrition relate to their own performance;
- which habits actually matter for their goals.

After enough high-quality history, the product should be capable of observations such as:

> The most reliable combination for your recent goals has been four weekly training sessions, at least about seven hours of sleep, and consistent protein intake earlier in the day. When two of those break down together, your training consistency tends to fall during the following week.

That is the transition from tracker to personal health intelligence system.

## Strategic Priority Sequence

The current ordering is:

```text
Exercise Catalog + Visualization Expansion to at least 450–500 canonical exercises
        ↓
Daily Command Center + Frictionless Capture
        ↓
Adaptive Real-Life Training and Calendar/Duration Intelligence
        ↓
Nutrition Decision Intelligence
        ↓
Personal Baselines, Weight Trends, and Metabolic Calibration
        ↓
Longitudinal Insight, Change Detection, and Personal Experiments
        ↓
Recovery Intelligence + Wearable Integration
        ↓
Explainable Conversational Coach + Voice + Selective RAG
        ↓
Offline/Cross-Device Maturity + Privacy/Export + Carefully Chosen SaaS Extensions
```

This sequence is directional, not sacred. Daily use may reveal a smaller friction fix that deserves to move ahead of a larger planned initiative.

The governing question remains:

> What improvement would make the product meaningfully better to use every day while strengthening the compounding personal model rather than adding disconnected feature count?

## Milestone Selection Rules

Architecture should continue to break the roadmap into bounded, reviewable milestones.

A major initiative should not be authorized merely because it appears in this roadmap.

Before implementation, Architecture should determine:

- the specific user problem;
- why it is the highest-value next step;
- the existing repository ownership boundaries;
- deterministic source-of-truth rules;
- explicit non-goals;
- the narrowest credible implementation slice;
- validation and smoke requirements;
- whether the milestone improves the long-term personal model or merely adds surface area.

## AI Product Rule

The project should not become an AI demo.

Use AI when it meaningfully reduces friction, interprets complex grounded context, helps with uncertain perception tasks such as images or labels, or enables natural interaction that deterministic software cannot provide efficiently.

Do not use AI to replace simple calculations, core CRUD, persisted truth, deterministic validation, or facts already available in structured data.

## Roadmap Stewardship

Architecture owns strategic roadmap changes.

Codex may implement Architecture-approved roadmap edits, but this file should remain a clean strategic source of truth rather than accumulating milestone-closeout history.

Historical implementation state belongs in current-state and milestone records. The roadmap should be rewritten when necessary to remain useful.

## Definition of Success

The platform succeeds when the user prefers it over separate nutrition, workout, recovery, and coaching tools because it is:

- faster for real daily routines;
- easier to use on mobile;
- trustworthy with personal data;
- useful without AI;
- honest about uncertainty;
- deeply connected across nutrition, recovery, activity, and training;
- explainable when it makes recommendations;
- increasingly personalized as history accumulates;
- better at anticipating and reducing the user’s real friction over time.

The single differentiator to protect throughout the project is this:

> The longer the user consistently uses the platform, the more valuable it becomes because it develops an increasingly accurate, evidence-backed model of that individual.
