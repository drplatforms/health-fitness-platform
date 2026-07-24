"use client";

import { AvailableIngredientsPanel } from "@/components/AvailableIngredientsPanel";
import { FoodLibraryPanel } from "@/components/FoodLibraryPanel";
import { FoodLoggingCard } from "@/components/FoodLoggingCard";
import {
  LoggedFoodEntry,
  LoggedFoodsList,
} from "@/components/LoggedFoodsList";
import {
  WorkspaceDeck,
  WorkspaceDeckTab,
} from "@/components/WorkspaceDeck";
import { FOOD_WORKSPACE_LABELS } from "@/lib/appUiStandards";

interface FoodWorkspaceDeckProps {
  userId: number;
  targetDate: string;
  requestedDate?: string;
  initialLoggedEntries?: LoggedFoodEntry[];
  initialLoggedError?: string | null;
  initialView?: "log" | "logged" | "pantry" | "library";
}

export function FoodWorkspaceDeck({
  userId,
  targetDate,
  requestedDate,
  initialLoggedEntries = [],
  initialLoggedError = null,
  initialView,
}: FoodWorkspaceDeckProps) {
  const logTab: WorkspaceDeckTab = {
    key: "log",
    label: FOOD_WORKSPACE_LABELS.log,
    content: (
      <FoodLoggingCard
        userId={userId}
        targetDate={targetDate}
        navigationDate={requestedDate}
        variant="embedded"
      />
    ),
  };
  const pantryTab: WorkspaceDeckTab = {
    key: "pantry",
    label: FOOD_WORKSPACE_LABELS.pantry,
    content: <AvailableIngredientsPanel userId={userId} />,
  };
  const libraryTab: WorkspaceDeckTab = {
    key: "library",
    label: FOOD_WORKSPACE_LABELS.library,
    content: <FoodLibraryPanel userId={userId} targetDate={requestedDate} />,
  };

  const tabs: WorkspaceDeckTab[] = [
    logTab,
    {
      key: "logged",
      label: FOOD_WORKSPACE_LABELS.logged,
      content: (
        <LoggedFoodsList
          initialEntries={initialLoggedEntries}
          initialError={initialLoggedError}
          userId={userId}
          targetDate={targetDate}
        />
      ),
    },
    pantryTab,
    libraryTab,
  ];

  return (
    <WorkspaceDeck
      ariaLabel="Food workspace"
      tabs={tabs}
      initialActiveKey={initialView}
    />
  );
}
