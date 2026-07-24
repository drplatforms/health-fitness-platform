import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(
  new URL("./WorkoutHistoryAnalytics.tsx", import.meta.url),
  "utf8",
);

test("keeps zoom controls out of the plotted area", () => {
  assert.doesNotMatch(source, /aria-label="Graph zoom"/);
  assert.doesNotMatch(source, /aria-label="Zoom out"/);
  assert.doesNotMatch(source, /aria-label="Fit full range"/);
  assert.doesNotMatch(source, /aria-label="Zoom in"/);
});

test("uses one metric scale for the main graph and overview navigator", () => {
  assert.match(
    source,
    /performanceMetricPosition\(value, metricScale\)[\s\S]*function navigatorPoint/,
  );
  assert.match(
    source,
    /function navigatorPoint[\s\S]*performanceMetricPosition\(value, metricScale\)/,
  );
});

test("keeps touch scrubbing separate from viewport panning", () => {
  assert.match(source, /gesture\.mode = "scrub"/);
  assert.match(
    source,
    /if \(gesture\.mode === "scrub"\) \{[\s\S]*scrubAtClientX/,
  );
  assert.match(
    source,
    /if \(gesture\.mode === "pan"\) \{[\s\S]*dragNavigatorViewport/,
  );
  assert.match(source, /gesture\.mode === "scroll"[\s\S]*\? "scroll"/);
  assert.match(source, /touchGestureOpensSession\(touchGesture\)/);
});
