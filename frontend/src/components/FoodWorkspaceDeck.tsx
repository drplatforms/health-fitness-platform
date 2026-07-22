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
    label: "Log",
    hint: "Search and log",
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
    label: "Pantry",
    hint: "Foods on hand",
    content: <AvailableIngredientsPanel userId={userId} />,
  };
  const libraryTab: WorkspaceDeckTab = {
    key: "library",
    label: "Library",
    hint: "Manage your foods",
    content: <FoodLibraryPanel userId={userId} targetDate={requestedDate} />,
  };

  const tabs: WorkspaceDeckTab[] = [
    logTab,
    {
      key: "logged",
      label: "Logged Today",
      hint: "Review and edit",
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
