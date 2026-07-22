"use client";

import { ManualRecipePanel } from "@/components/ManualRecipePanel";
import { MealIdeasPanel } from "@/components/MealIdeasPanel";
import { SavedMealsPanel } from "@/components/SavedMealsPanel";
import { WorkspaceDeck } from "@/components/WorkspaceDeck";

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
          label: "Ideas",
          hint: "Generate grounded meals",
          content: <MealIdeasPanel userId={userId} targetDate={targetDate} />,
        },
        {
          key: "saved",
          label: "Saved Recipes",
          hint: "Reuse and manage",
          content: (
            <SavedMealsPanel
              userId={userId}
              targetDate={targetDate}
            />
          ),
        },
        {
          key: "create",
          label: "Create Manually",
          hint: "Build from your foods",
          content: <ManualRecipePanel userId={userId} />,
        },
      ]}
    />
  );
}
