import assert from "node:assert/strict";
import test from "node:test";

import {
  dedupeWorkoutExerciseMemoryRequests,
  mapWorkoutExerciseMemoryResolutions,
  MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE,
  normalizeWorkoutExerciseMemoryName,
  workoutExerciseMemoryIdentityKey,
} from "./workoutExerciseMemoryApi.ts";

test("uses catalog identity before normalized name fallback", () => {
  assert.equal(
    workoutExerciseMemoryIdentityKey({
      catalog_exercise_id: 55,
      exercise_name: "Dumbbell Row",
    }),
    "catalog:55",
  );
  assert.equal(
    workoutExerciseMemoryIdentityKey({
      catalog_exercise_id: null,
      exercise_name: "  Dumbbell   Row ",
    }),
    "name:dumbbell row",
  );
  assert.equal(
    normalizeWorkoutExerciseMemoryName("  One-Arm\n Dumbbell   Row "),
    "one-arm dumbbell row",
  );
});

test("deduplicates requested effective identities in stable order", () => {
  assert.deepEqual(
    dedupeWorkoutExerciseMemoryRequests([
      { catalog_exercise_id: 55, exercise_name: "Dumbbell Row" },
      { catalog_exercise_id: 55, exercise_name: "Row alias" },
      { catalog_exercise_id: null, exercise_name: " Cable Crunch " },
      { catalog_exercise_id: null, exercise_name: "cable   crunch" },
      { catalog_exercise_id: null, exercise_name: "   " },
    ]),
    [
      { catalog_exercise_id: 55, exercise_name: "Dumbbell Row" },
      { catalog_exercise_id: null, exercise_name: "Cable Crunch" },
    ],
  );
});

test("keeps frontend batches within the backend workout-sized bound", () => {
  const requests = Array.from(
    { length: MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE + 5 },
    (_, index) => ({
      catalog_exercise_id: index + 1,
      exercise_name: `Exercise ${index + 1}`,
    }),
  );

  assert.equal(
    dedupeWorkoutExerciseMemoryRequests(requests).length,
    MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE,
  );
});

test("maps fallback results to the requested effective identity", () => {
  const memory = {
    memory_id: 7,
    catalog_exercise_id: null,
    exercise_name: "Dumbbell Row",
    memory_text: "Rack 12.",
    created_at: "2026-07-17 10:00:00",
    updated_at: "2026-07-17 10:00:00",
  };

  assert.deepEqual(
    mapWorkoutExerciseMemoryResolutions([
      {
        requested_catalog_exercise_id: 55,
        requested_exercise_name: "Dumbbell Row",
        memory,
      },
      {
        requested_catalog_exercise_id: null,
        requested_exercise_name: "Cable Crunch",
        memory: null,
      },
    ]),
    {
      "catalog:55": memory,
      "name:cable crunch": null,
    },
  );
});
