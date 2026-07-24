import assert from "node:assert/strict";
import test from "node:test";

import {
  getSwitchableUserLabel,
  isQaSwitcherUser,
  SWITCHABLE_USERS,
} from "./userSwitcher.ts";

test("exposes the realistic longitudinal QA personas without changing existing users", () => {
  assert.deepEqual(
    SWITCHABLE_USERS.map(({ id, label, kind }) => ({ id, label, kind })),
    [
      { id: 1, label: "Dustin", kind: "real" },
      { id: 2, label: "Danielle", kind: "real" },
      { id: 101, label: "QA 101", kind: "qa" },
      { id: 102, label: "QA 102", kind: "qa" },
      { id: 103, label: "QA 103", kind: "qa" },
      { id: 104, label: "QA 104", kind: "qa" },
      { id: 105, label: "QA 105", kind: "qa" },
      { id: 106, label: "QA106 — Consistent Strength", kind: "qa" },
      { id: 107, label: "QA107 — Interrupted Progress", kind: "qa" },
      { id: 108, label: "QA108 — Mixed Modality", kind: "qa" },
    ],
  );
});

test("classifies the new personas as QA users and preserves fallback labels", () => {
  for (const userId of [106, 107, 108]) {
    assert.equal(isQaSwitcherUser(userId), true);
  }

  assert.equal(isQaSwitcherUser(1), false);
  assert.equal(isQaSwitcherUser(999), false);
  assert.equal(getSwitchableUserLabel(108), "QA108 — Mixed Modality");
  assert.equal(getSwitchableUserLabel(999), "User 999");
});
