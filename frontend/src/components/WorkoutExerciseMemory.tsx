"use client";

import { useState } from "react";

import {
  deleteWorkoutExerciseMemory,
  MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS,
  saveWorkoutExerciseMemory,
} from "@/lib/workoutExerciseMemoryApi";
import {
  WorkoutExerciseMemory as WorkoutExerciseMemoryValue,
  WorkoutExerciseMemoryIdentity,
} from "@/types/workoutExerciseMemory";

interface WorkoutExerciseMemoryProps {
  userId: number;
  identity: WorkoutExerciseMemoryIdentity;
  memory: WorkoutExerciseMemoryValue | null | undefined;
  canEdit: boolean;
  onSaved: (memory: WorkoutExerciseMemoryValue) => void;
  onDeleted: () => void;
}

export function WorkoutExerciseMemory({
  userId,
  identity,
  memory,
  canEdit,
  onSaved,
  onDeleted,
}: WorkoutExerciseMemoryProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(memory?.memory_text ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (memory === undefined) {
    return null;
  }

  function beginEditing() {
    setDraft(memory?.memory_text ?? "");
    setErrorMessage(null);
    setIsEditing(true);
  }

  function cancelEditing() {
    setDraft(memory?.memory_text ?? "");
    setErrorMessage(null);
    setIsEditing(false);
  }

  async function handleSave() {
    const memoryText = draft.trim();
    if (!memoryText) {
      setErrorMessage("Enter something useful to remember.");
      return;
    }
    if (memoryText.length > MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS) {
      setErrorMessage(
        `Keep exercise memory to ${MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS} characters or fewer.`,
      );
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    const result = await saveWorkoutExerciseMemory(
      userId,
      identity,
      memoryText,
      memory?.memory_id,
    );
    setIsSubmitting(false);
    if (result.error || !result.data?.memory) {
      setErrorMessage(result.error?.message ?? "Unable to save this memory.");
      return;
    }
    setDraft(result.data.memory.memory_text);
    setIsEditing(false);
    onSaved(result.data.memory);
  }

  async function handleDelete() {
    if (!memory) {
      return;
    }
    setIsSubmitting(true);
    setErrorMessage(null);
    const result = await deleteWorkoutExerciseMemory(userId, memory.memory_id);
    setIsSubmitting(false);
    if (result.error) {
      setErrorMessage(result.error.message);
      return;
    }
    setDraft("");
    setIsEditing(false);
    onDeleted();
  }

  if (!isEditing) {
    if (!memory) {
      return canEdit ? (
        <button
          type="button"
          onClick={beginEditing}
          className="min-h-11 rounded-lg px-2 py-2 text-left text-xs font-semibold text-text-muted transition hover:bg-surface hover:text-accent-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
        >
          Add memory
        </button>
      ) : null;
    }

    return (
      <div className="px-1 py-1">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="type-compact-metadata font-semibold uppercase tracking-[0.14em] text-text-muted">
              Memory
            </p>
            <p className="mt-1 whitespace-pre-wrap text-sm leading-5 text-text-body">
              {memory.memory_text}
            </p>
          </div>
          {canEdit ? (
            <button
              type="button"
              onClick={beginEditing}
              className="min-h-10 shrink-0 rounded-lg px-2 py-2 text-xs font-semibold text-accent-text transition hover:bg-surface-highlighted hover:text-accent-text-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
            >
              Edit
            </button>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2 px-1 py-1">
      <label className="block space-y-1 text-xs font-medium text-text-body">
        <span className="sr-only">Exercise memory</span>
        <textarea
          rows={2}
          maxLength={MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-base text-text-strong outline-none focus:border-focus-subtle md:text-sm"
        />
      </label>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => void handleSave()}
          disabled={isSubmitting}
          className="min-h-11 rounded-xl bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          onClick={cancelEditing}
          disabled={isSubmitting}
          className="min-h-11 rounded-xl px-3 py-2 text-sm font-semibold text-text-muted transition hover:bg-surface-subtle hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
        >
          Cancel
        </button>
        {memory ? (
          <button
            type="button"
            onClick={() => void handleDelete()}
            disabled={isSubmitting}
            className="min-h-11 rounded-xl px-3 py-2 text-sm font-semibold text-danger-action transition hover:bg-danger-surface disabled:cursor-not-allowed disabled:opacity-60"
          >
            Delete memory
          </button>
        ) : null}
      </div>
      {errorMessage ? (
        <p className="text-xs font-medium text-danger-action" role="status">
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
