"use client";

import { ManualRecipePanel } from "@/components/ManualRecipePanel";
import { MealIdeasPanel } from "@/components/MealIdeasPanel";
import { SavedMealsPanel } from "@/components/SavedMealsPanel";
import { WorkspaceDeck } from "@/components/WorkspaceDeck";
import { MEALS_WORKSPACE_LABELS } from "@/lib/appUiStandards";

interface MealsWorkspaceDeckProps {
  userId: number;
  targetDate: string;
}

export function MealsWorkspaceDeck({
  userId,
  targetDate,
}: MealsWorkspaceDeckProps) {
  return (
    <WorkspaceDeck
      ariaLabel="Meals workspace"
      tabs={[
        {
          key: "ideas",
          label: MEALS_WORKSPACE_LABELS.ideas,
          content: <MealIdeasPanel userId={userId} targetDate={targetDate} />,
        },
        {
          key: "saved",
          label: MEALS_WORKSPACE_LABELS.saved,
          content: (
            <SavedMealsPanel
              userId={userId}
              targetDate={targetDate}
            />
          ),
        },
        {
          key: "create",
          label: MEALS_WORKSPACE_LABELS.create,
          content: <ManualRecipePanel userId={userId} />,
        },
      ]}
    />
  );
}
