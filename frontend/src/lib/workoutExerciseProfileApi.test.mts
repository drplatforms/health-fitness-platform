import assert from "node:assert/strict";
import test from "node:test";

import {
  dedupeWorkoutExerciseProfileIds,
  exerciseInstructionAffordance,
  mapWorkoutExerciseProfileResolutions,
  MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE,
} from "./workoutExerciseProfileApi.ts";

test("deduplicates stable catalog identities and rejects non-catalog values", () => {
  assert.deepEqual(
    dedupeWorkoutExerciseProfileIds([55, 55, null, 0, -1, 72]),
    [55, 72],
  );
});

test("keeps profile batches within the workout-sized backend bound", () => {
  const catalogIds = Array.from(
    { length: MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE + 5 },
    (_, index) => index + 1,
  );
  assert.equal(
    dedupeWorkoutExerciseProfileIds(catalogIds).length,
    MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE,
  );
});

test("maps resolved profiles by requested catalog identity", () => {
  const profile = {
    profile_id: 7,
    catalog_exercise_id: 55,
    familiarity_state: "learning" as const,
    preference_state: "favorite" as const,
    created_at: "2026-07-17 10:00:00",
    updated_at: "2026-07-17 10:00:00",
  };
  assert.deepEqual(
    mapWorkoutExerciseProfileResolutions([
      { requested_catalog_exercise_id: 55, profile },
      { requested_catalog_exercise_id: 72, profile: null },
    ]),
    { 55: profile, 72: null },
  );
});

test("adapts the compact instruction affordance from familiarity only", () => {
  assert.equal(exerciseInstructionAffordance("unfamiliar"), "Learn");
  assert.equal(exerciseInstructionAffordance("learning"), "Review");
  assert.equal(exerciseInstructionAffordance("familiar"), "How To");
  assert.equal(exerciseInstructionAffordance(null), "How To");
  assert.equal(exerciseInstructionAffordance(undefined), "How To");
});
