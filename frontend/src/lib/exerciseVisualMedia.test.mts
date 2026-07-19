import assert from "node:assert/strict";
import test from "node:test";

import { selectCurrentExerciseInstructionResponse } from "./exerciseVisualMedia.ts";
import type {
  ExerciseInstructionResponse,
  ExerciseVisualMediaItem,
  ExerciseVisualMediaResolutionMode,
  ExerciseVisualMediaSourceType,
} from "../types/exerciseInstruction.ts";

function instructionResponse(
  requestedCatalogExerciseId: number,
  resolutionMode: ExerciseVisualMediaResolutionMode,
  sourceType: ExerciseVisualMediaSourceType,
  sourceCatalogExerciseId: number | null,
  visualMedia: ExerciseVisualMediaItem[],
): ExerciseInstructionResponse {
  return {
    success: true,
    exercise: {
      id: requestedCatalogExerciseId,
      name: "Test exercise",
      exercise_type: "strength",
      movement_pattern: "hinge",
      primary_muscle_groups: ["glutes"],
      equipment_required: ["dumbbell"],
      difficulty: "intermediate",
    },
    instruction: {
      catalog_exercise_id: requestedCatalogExerciseId,
      overview: "Follow the persisted written instructions.",
      setup_steps: [],
      execution_steps: [],
      form_cues: [],
      common_mistakes: [],
      safety_notes: [],
    },
    form_media: [],
    visual_media: visualMedia,
    visual_media_resolution: {
      requested_catalog_exercise_id: requestedCatalogExerciseId,
      visual_identity_slug: "visual_test",
      resolution_mode: resolutionMode,
      source_type: sourceType,
      source_catalog_exercise_id: sourceCatalogExerciseId,
      provider:
        resolutionMode === "provider" ? "ascendapi_free_v1" : null,
      provider_exercise_id:
        resolutionMode === "provider" ? "freeV1Id" : null,
    },
  };
}

test("selects normalized provider animated media for the requested exercise", () => {
  const providerMedia: ExerciseVisualMediaItem = {
    media_key: "ascendapi_free_v1:freeV1Id",
    media_type: "animated_image",
    role: "movement_demo",
    url: "https://static.exercisedb.dev/media/freeV1Id.gif",
    alt_text: "Animated movement demonstration",
    caption: null,
    source_type: "remote_provider",
    source_catalog_exercise_id: null,
    provider: "ascendapi_free_v1",
    provider_exercise_id: "freeV1Id",
    attribution: "ExerciseDB / AscendAPI Free V1",
    provenance: "reviewed free V1 mapping",
  };
  const response = instructionResponse(
    41,
    "provider",
    "remote_provider",
    null,
    [providerMedia],
  );

  const selected = selectCurrentExerciseInstructionResponse(response, 41);

  assert.ok(selected);
  assert.deepEqual(selected.visual_media, [providerMedia]);
});

test("accepts shared-local media whose source owner differs from the request", () => {
  const sharedMedia: ExerciseVisualMediaItem = {
    media_key: "local:7:start",
    media_type: "static_image",
    role: "start_position",
    url: "/exercise-media/free-exercise-db/start.jpg",
    alt_text: "Start position",
    caption: "Start",
    source_type: "local",
    source_catalog_exercise_id: 7,
    provider: null,
    provider_exercise_id: null,
    attribution: null,
    provenance: "reviewed local asset",
  };
  const response = instructionResponse(
    12,
    "shared_local_visual_identity",
    "local",
    7,
    [sharedMedia],
  );

  const selected = selectCurrentExerciseInstructionResponse(response, 12);

  assert.ok(selected);
  assert.equal(
    selected.visual_media_resolution.requested_catalog_exercise_id,
    12,
  );
  assert.equal(selected.visual_media[0].source_catalog_exercise_id, 7);
});

test("rejects stale exercise and stale resolution responses", () => {
  const staleExerciseResponse = instructionResponse(
    41,
    "provider",
    "remote_provider",
    null,
    [],
  );
  assert.equal(
    selectCurrentExerciseInstructionResponse(staleExerciseResponse, 42),
    null,
  );

  const staleResolutionResponse = instructionResponse(
    42,
    "provider",
    "remote_provider",
    null,
    [],
  );
  staleResolutionResponse.visual_media_resolution.requested_catalog_exercise_id =
    41;
  assert.equal(
    selectCurrentExerciseInstructionResponse(staleResolutionResponse, 42),
    null,
  );
});

test("keeps written guidance and selects no media for provider fallback", () => {
  const noMediaResponse = instructionResponse(41, "none", "none", null, []);

  const selected = selectCurrentExerciseInstructionResponse(noMediaResponse, 41);

  assert.ok(selected);
  assert.equal(selected.instruction.overview, "Follow the persisted written instructions.");
  assert.deepEqual(selected.visual_media, []);
  assert.equal(selectCurrentExerciseInstructionResponse(null, 41), null);
});
