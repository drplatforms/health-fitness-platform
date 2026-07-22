"use client";

import { useState } from "react";

import { SavedMealEditor } from "@/components/SavedMealEditor";
import { SAVED_MEAL_CHANGED_EVENT } from "@/types/savedMeal";

interface ManualRecipePanelProps {
  userId: number;
}

export function ManualRecipePanel({ userId }: ManualRecipePanelProps) {
  const [editorKey, setEditorKey] = useState(0);
  const [message, setMessage] = useState<string | null>(null);

  function resetEditor() {
    setEditorKey((current) => current + 1);
  }

  return (
    <div className="space-y-3">
      {message ? (
        <p
          role="status"
          className="rounded-lg bg-positive-surface px-3 py-2 text-sm text-positive-foreground-strong"
        >
          {message}
        </p>
      ) : null}
      <SavedMealEditor
        key={editorKey}
        userId={userId}
        onCancel={() => {
          setMessage(null);
          resetEditor();
        }}
        onSaved={(meal) => {
          setMessage(`${meal.display_name} saved. Find it in Saved Recipes.`);
          window.dispatchEvent(new Event(SAVED_MEAL_CHANGED_EVENT));
          resetEditor();
        }}
      />
    </div>
  );
}
