export type DailyWorkspaceDestination =
  | "today"
  | "food"
  | "meals"
  | "workout"
  | "recovery";

const dailyWorkspacePaths: Record<DailyWorkspaceDestination, string> = {
  today: "/",
  food: "/food",
  meals: "/meals",
  workout: "/today/workout",
  recovery: "/recovery",
};

export function activeDailyWorkspace(
  pathname: string,
): DailyWorkspaceDestination {
  if (pathname === "/food" || pathname.startsWith("/personal-foods")) {
    return "food";
  }
  if (pathname === "/meals" || pathname.startsWith("/meals/")) {
    return "meals";
  }
  if (pathname === "/today/workout" || pathname.startsWith("/workout/")) {
    return "workout";
  }
  if (pathname === "/recovery") {
    return "recovery";
  }
  return "today";
}

export function buildDailyWorkspaceHref(
  destination: DailyWorkspaceDestination,
  userId: number,
  explicitDate?: string,
): string {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (explicitDate) {
    params.set("date", explicitDate);
  }

  return `${dailyWorkspacePaths[destination]}?${params.toString()}`;
}
