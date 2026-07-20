# Health & Fitness Platform — Strategic Product Roadmap

> Protected strategic roadmap. This file preserves product direction and is not active implementation authority. Current operational truth is owned by `docs/project_memory/current_truth.json`.

## Purpose and Authority

This is the comprehensive protected strategic capability inventory for `fitness_ai`. It records what the product may grow toward and why.

It is not a commit log, an accepted-state snapshot, a milestone queue, or implementation authorization. Operational truth, including any active milestone or immediate priority, is owned exclusively by `docs/project_memory/current_truth.json`.

The stable destination and doctrine live in `docs/project_memory/product_north_star.md`. This roadmap applies that direction to capability clusters and long-term sequencing.

## Strategic Disposition Vocabulary

- `COMPLETED` — the intended strategic capability is accepted in full for its defined scope; later refinement is a new scope.
- `FOUNDATION EXISTS` — meaningful accepted capability exists, but the broader strategic destination remains open.
- `ACTIVE` — Architecture has explicitly designated the initiative as active in operational truth; this label alone never authorizes work.
- `PLANNED` — retained as a future capability for Architecture to scope when justified.
- `DEFERRED` — intentionally postponed until prerequisites, evidence, or product value justify reconsideration.
- `SUPERSEDED` — replaced by another direction with explicit decision evidence.
- `REJECTED` — intentionally excluded with explicit decision evidence.

Roadmap disposition is strategic, not operational. `SUPERSEDED` and `REJECTED` require cited decision evidence. A partial implementation is `FOUNDATION EXISTS`, not `COMPLETED`.

Statuses apply at the initiative or capability-cluster level where they clarify disposition; they are not required on every bullet.

## Cross-System Destination

The central product direction is to combine real-life constraints, recovery, training history, nutrition, and accumulated user history into increasingly personalized and explainable decisions.

The capability horizons below preserve the route toward that destination. Their ordering expresses dependency and product leverage, not a live implementation sequence.

## World-Class Exercise Catalog and Visual Form Guidance — `FOUNDATION EXISTS`; continued depth `PLANNED`

The product should maintain a broad, high-quality internal exercise catalog with useful visual form guidance and written fallback. Continued expansion remains a roadmap capability, not a standing implementation mandate.

The durable capability includes:

- canonical identity, deduplication, and physical variant relationships;
- movement pattern, muscle, equipment, and unilateral/bilateral semantics;
- loading, stability, difficulty, prescription, and measurement attributes where justified;
- structured setup, execution, cues, common mistakes, and safety guidance;
- visual identity and reviewed media relationships with rights and provenance;
- workout-generation eligibility, reachability, utilization, and meaningful rotation;
- provider media or knowledge only as supplemental input, never internal catalog truth;
- text-only and local-media fallback when external media is absent or unsuitable.

Expansion quality is measured by correct ownership and useful product reachability, not row count. Commercial or SaaS use of external media requires renewed rights review.

## Established Product Foundations

These accepted foundational scopes are protected from being reintroduced as unfinished first-version roadmap work:

- Theme System and Dark Mode v1 — `COMPLETED`
- Mobile Daily-Driver Navigation and Compaction v1 — `COMPLETED`
- Active Workout Mobile UX v1 — `COMPLETED`
- Barcode Scanning v1 — `COMPLETED`
- Meal Builder v1 — `COMPLETED`
- Adaptive Progression Engine v1 — `COMPLETED`
- Weekly Training Planner v1 — `COMPLETED`
- Smart Exercise Substitutions v1 — `COMPLETED`
- Injury / Temporary Limitation Mode v1 — `COMPLETED`
- Exercise History & Progress Analytics v1 — `COMPLETED`
- Deterministic Nutrition Gap Suggestions and Actions v1 — `COMPLETED`
- Visualization v2 Provider-Media Integration — `COMPLETED`

Each `COMPLETED` label applies only to the accepted foundational scope. Deeper versions may remain `PLANNED`; this section records strategic disposition, not live operational truth or implementation authorization.

## Horizon 1 — Daily Command Center and Frictionless Capture — `FOUNDATION EXISTS`; deeper unification `PLANNED`

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

## Horizon 2 — Adaptive Training That Works Around Real Life — `FOUNDATION EXISTS`; broader adaptation `PLANNED`

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
- progression forecasting grounded in comparable performance evidence;
- training-volume response analysis;
- fatigue-aware deload and workload decisions where sufficiently supported;
- preserving the highest-value work when time is limited.

### Training depth

Longer-term training intelligence may include:

- warm-up generation and support, plus cooldown support where useful;
- workout review with performance evidence and post-session coaching feedback;
- training-load modeling and longer-term periodization;
- movement-pattern balancing and exercise variety controls;
- explicit exercise preference and avoidance controls;
- progression explanations tied to comparable history, workload, and recovery evidence.

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

### What-If simulator and scenario planning — `PLANNED`

A deterministic-first, evidence-bounded scenario planner may compare approved options before anything changes. It could show what happens to the week if a workout moves, which training option fits a reduced time window, or how a proposed nutrition or schedule change affects an approved plan.

## Horizon 3 — Nutrition Decision Intelligence — `FOUNDATION EXISTS`; broader decision support `PLANNED`

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

### Nutrition planning depth — `PLANNED`

Future nutrition support may include:

- recipe parsing and reusable recipe workflows;
- meal planning and meal-prep support beyond the existing meal builder;
- micronutrient awareness with appropriate completeness and confidence boundaries;
- meal-timing context where it materially improves a decision;
- grounded food swaps under the same nutritional and preference constraints;
- trend-aware nutrition-target review;
- cautious macro-target adaptation only when sufficient intake, weight-trend, activity, and data-quality evidence supports it.

## Horizon 4 — Personal Measurement, Metabolic Calibration, and Baselines — `FOUNDATION EXISTS`; calibration depth `PLANNED`

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

## Horizon 5 — Longitudinal Personal Intelligence — `FOUNDATION EXISTS`; advanced analysis `PLANNED`

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

### Reporting and evidence experience — `PLANNED`

The longitudinal product experience should also support:

- monthly review in addition to weekly review;
- report diffing and change comparison;
- user-facing evidence links;
- structured claim and evidence tracking;
- a report audit trail;
- recommendation outcome tracking;
- training evidence summaries;
- nutrition target-vs-actual summaries;
- data-quality summaries that expose gaps and confidence limits.

### Inspectable personal memory and feedback — `PLANNED`

The user should be able to inspect and correct the durable context that improves future relevance, including:

- editable user facts and editable preferences;
- goals and constraints;
- typed distinctions among facts, preferences, goals, constraints, observations, and model suggestions;
- trend memory and structured observations;
- explicit memory expiration or staleness behavior;
- user correction and recommendation feedback that can influence future relevance.

There is no hidden model memory. Generated prose is not persistent truth, and personal memory remains inspectable, correctable, exportable, and bounded by provenance.

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

## Horizon 6 — Recovery Intelligence and Wearable Integration — recovery foundation `FOUNDATION EXISTS`; wearables `DEFERRED`

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

## Horizon 7 — Explainable Conversational Assistance — explainability `FOUNDATION EXISTS`; generative assistance `DEFERRED`

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

### Education, help, and explanation — `PLANNED`

Future assistance may provide a user education mode, app help and onboarding assistance, “teach me this” explanations, and evidence tracing for “why did the system say or change this?” The experience may later use selective retrieval, but its product promise is grounded explanation rather than a specific retrieval technology.

### Recommendation and coaching feedback — `PLANNED`

The product may collect user feedback on recommendations, track recommendation outcomes, offer context-aware nudges, and support same-day plan adjustments when grounded evidence and approved constraints justify them. Optional tone preferences may shape presentation but remain subordinate to factual content, safety, and deterministic decisions.

## Horizon 8 — Platform Maturity, Portability, and SaaS Extensions — `PLANNED`; SaaS extensions carefully `DEFERRED`

These capabilities matter as the product grows but should not distract from daily personal usefulness prematurely.

### Offline-first / PWA

Core daily workflows should eventually remain usable with poor connectivity and synchronize safely later.

### Cross-device experience

Support phone, desktop, and tablet coherently, with potential smartwatch execution surfaces later.

### Contextual notifications

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

## Strategic Sequencing Principles

Architecture may reorder bounded milestones when evidence from real daily use reveals a higher-value problem. Strategic sequencing should generally:

- protect low-friction daily capture and execution;
- strengthen deterministic cross-system evidence before adding interpretation layers;
- deepen adaptive training and nutrition decision support before relying on conversational presentation;
- establish personal baselines before making longitudinal or predictive claims;
- introduce wearables, retrieval, voice, providers, or SaaS infrastructure only for a concrete, separately authorized need;
- preserve portability, privacy, explainability, and deterministic fallback as the platform matures.

The roadmap does not select the next implementation milestone. That decision belongs to operational truth.

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
