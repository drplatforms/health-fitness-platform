# Product North Star

> Protected strategic direction. This document defines the durable product destination and doctrine. It does not authorize implementation; operational truth and implementation authority live in `docs/project_memory/current_truth.json`.

## Destination

Build a personal health intelligence system that combines nutrition, training, recovery, longitudinal analysis, and moment-of-need coaching in one coherent product.

The system should become more valuable through use because it develops an increasingly accurate, evidence-backed model of the individual:

- what the person actually does;
- what they consistently avoid or modify;
- which foods, exercises, routines, and schedules fit their life;
- how training, recovery, sleep, nutrition, and real-world constraints interact;
- which recommendations they follow, reject, or repeatedly change;
- which patterns are supported by enough history to be useful.

Personalization must emerge from grounded history, explicit user input, validated calculations, and inspectable evidence. It must never be replaced by an invented AI narrative.

The long-term experience should feel less like a collection of trackers and more like a personal operating system for everyday health, nutrition, recovery, and training.

## Eight Product Pillars

### CAPTURE

Make useful data effortless to record through fast, safe, low-friction workflows and strong confirmation boundaries.

### PLAN

Turn goals, constraints, schedules, equipment, preferences, and current state into realistic actions.

### EXECUTE

Help the user carry out workouts and nutrition decisions correctly with minimal interruption and preserved context.

### UNDERSTAND

Explain current state, trends, uncertainty, and meaningful changes in language the user can inspect and trust.

### ADAPT

Adjust approved plans when evidence, constraints, recovery, availability, or outcomes change.

### LEARN

Discover what works for the individual over time without confusing correlation, incomplete data, or model output with fact.

### PREDICT

Anticipate likely friction, meaningful deviations, and useful intervention windows without pretending to predict physiology perfectly.

### ASSIST

Help the user make a better decision at the moment they actually need one.

The pillars are connected. Capture should strengthen planning and understanding; execution should create better evidence; evidence should improve adaptation, learning, prediction, and assistance.

## Stable Product Doctrine

### Backend owns truth

The backend owns persisted facts, calculations, constraints, validation, provenance, confidence, safety boundaries, deterministic decisions, and fallback behavior.

### Deterministic-first

Core product behavior should be testable, inspectable, and reproducible. Generative fluency must not substitute for domain logic or evidence.

### Useful without generative AI

Nutrition, workout, recovery, planning, history, and decision-support workflows must remain useful when every generative provider is unavailable or disabled.

### Optional systems remain non-authoritative

AI and provider systems may propose, retrieve, summarize, or explain backend-approved options. They may not silently own health decisions, calculations, targets, persistence, or personal memory.

### Explainability is a product requirement

Meaningful recommendations and adaptations should expose why they were made, which evidence mattered, and which constraints applied.

### Be honest about uncertainty

Estimated meals, portions, body composition, wearable signals, metabolic calibration, predictions, and longitudinal associations must expose assumptions, confidence, and data limitations rather than fake precision.

### Privacy and user ownership are foundational

Users should understand what is stored, what leaves their device, what optional systems can access, and how to inspect, correct, export, or delete their information.

### Mobile-first daily usefulness

The primary daily experience should optimize for one-handed use, low tap count, minimal scrolling, fast capture, clear next actions, and preservation of in-progress work. Larger screens should support deeper planning, review, and analysis.

### Accumulated use should compound value

Recents, preferences, successful substitutions, workout response, recovery patterns, food habits, adherence history, personal baselines, and outcomes should progressively reduce friction and improve relevance.

### Provenance must survive interpretation

Source facts, derived evidence, approved decisions, retrieved context, optional explanation, and user confirmation should remain distinguishable. Helpful prose must never erase how a conclusion was reached.

### Human authority remains explicit

The user approves consequential actions and can reject, correct, or override proposals within validated product boundaries. Hidden automation must not make health decisions on the user's behalf.

## Product Test

A proposed capability belongs in the product direction when it makes everyday use meaningfully easier, strengthens trustworthy cross-system intelligence, improves the evidence-backed personal model, or helps the user understand and act on approved information.

A capability should be questioned when it adds disconnected feature count, creates unexplained authority, weakens deterministic fallback, hides uncertainty, or depends on generated output to make the core product useful.

## Long-Term Differentiator

The enduring differentiator is not generic personalization or a chatbot interface.

It is a trustworthy system in which real-life constraints, recovery, training history, nutrition, and accumulated user history produce increasingly personalized and explainable decisions.

The longer the user consistently uses the platform, the more valuable it should become because the platform develops a more accurate, evidence-backed model of that individual while preserving their control.
