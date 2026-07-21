import assert from "node:assert/strict";
import test from "node:test";

import { exerciseGuidancePresentation } from "./exerciseGuidanceDuringWorkout.ts";

test("uses a compact dialog presentation while workout logging is active", () => {
  assert.deepEqual(exerciseGuidancePresentation(true), {
    mobilePresentation: "dialog",
    showProfileControls: false,
    triggerLabel: "Form guide",
  });
});

test("keeps the established inline guidance presentation outside execution", () => {
  assert.deepEqual(exerciseGuidancePresentation(false), {
    mobilePresentation: "inline",
    showProfileControls: true,
    triggerLabel: null,
  });
});
