import assert from "node:assert/strict";
import test from "node:test";

import {
  computeLimitationExpiresAt,
  limitationSummary,
  limitationTokenLabel,
} from "./temporaryWorkoutLimitation.ts";

test("temporary limitation labels remain compact and user-facing", () => {
  assert.equal(limitationTokenLabel("wrist_hand"), "Wrist Hand");
  assert.equal(limitationTokenLabel("vertical_push"), "Vertical Push");
  assert.equal(
    limitationSummary({
      user_id: 1,
      affected_regions: [],
      restricted_movement_patterns: ["vertical_push", "horizontal_push"],
      excluded_catalog_exercise_ids: [2],
      expires_at: null,
      created_at: null,
      updated_at: null,
    }),
    "2 movement restrictions · 1 exercise · until cleared",
  );
});

test("duration choices produce bounded UTC expirations", () => {
  const now = new Date("2026-07-17T12:00:00.000Z");
  assert.equal(computeLimitationExpiresAt("until_cleared", null, now), null);
  assert.equal(
    computeLimitationExpiresAt("7_days", null, now),
    "2026-07-24T12:00:00.000Z",
  );
  assert.equal(
    computeLimitationExpiresAt("existing", "2026-07-20T12:00:00Z", now),
    "2026-07-20T12:00:00Z",
  );
});
