# Today Main Loop Density Polish v0

Status: implementation complete, ready for Architecture review.

Branch:

```text
feature/today-main-loop-density-polish-v0
```

## Purpose

Polish the Next.js Today page into a tighter daily operator dashboard by giving prime space to the real daily loops:

- Nutrition / Log Food
- Workout summary
- Recovery Check-In

## Implemented Scope

- Removed the giant green Next Action card from the main Today layout.
- Moved Nutrition and Log Food to the top of the Today page so the food logging loop is visible before scrolling on normal desktop layouts.
- Kept Nutrition and Log Food as separate existing components, grouped directly together with a smaller gap.
- Compacted the Log Food selected state so selected food appears once, search results hide after selection until the query changes, macro preview is inline, and success/error messages are small.
- Converted completed workout state into a compact summary that uses the existing Today workout payload for exercise names, set counts, duration, status, and the existing completed-workout detail link.
- Removed completed-workout instructional copy such as "Today's workout is done." from the Today summary surface.
- Removed the internal-ish Recovery eyebrow while preserving Recovery Check-In behavior and save contract.
- Preserved mobile order as Nutrition / Log Food, Workout, then Recovery.

## Boundaries Preserved

- No backend behavior changed.
- No nutrition aggregation, canonical logging, recovery scoring, workout lifecycle, provider, or user-routing behavior changed.
- No food diary/history, edit/delete flow, serving picker, meal builder, recent foods, favorites, barcode scanner, AI food parser, image recognition, dashboard state manager, or collapsible-card framework was added.
- No DB files, USDA datasets, CSVs, ZIPs, or generated runtime artifacts are part of the milestone.

## Deferred

- Read-only logged foods list.
- Serving-size picker.
- Food log edit/delete/history.
- Saved-state recovery summary redesign.
- New recommendation or next-action system.
- Deeper completed workout metrics beyond data already present in the Today workout payload.

## Validation Target

```powershell
cd C:\projects\fitness_ai\frontend
npm run lint
npm run build
```
