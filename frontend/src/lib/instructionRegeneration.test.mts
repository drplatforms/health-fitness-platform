import assert from "node:assert/strict";
import test from "node:test";

import {
  instructionReplacementConfirmationMessage,
  needsInstructionReplacementConfirmation,
} from "./instructionRegeneration.ts";

test("only existing cooking instructions require replacement confirmation", () => {
  assert.equal(needsInstructionReplacementConfirmation(undefined), false);
  assert.equal(needsInstructionReplacementConfirmation(null), false);
  assert.equal(needsInstructionReplacementConfirmation([]), false);
  assert.equal(
    needsInstructionReplacementConfirmation(["Season the chicken."]),
    true,
  );
});

test("replacement confirmation identifies the provider and model", () => {
  assert.equal(
    instructionReplacementConfirmationMessage("OpenAI", "gpt-5.4-mini"),
    "This will make another AI request using OpenAI / gpt-5.4-mini and overwrite the current instructions.",
  );
});
