export type DailyWorkspaceDestination =
  | "today"
  | "food"
  | "workout"
  | "recovery";

const dailyWorkspacePaths: Record<DailyWorkspaceDestination, string> = {
  today: "/",
  food: "/food",
  workout: "/today/workout",
  recovery: "/recovery",
};

export function activeDailyWorkspace(
  pathname: string,
): DailyWorkspaceDestination {
  if (pathname === "/food" || pathname.startsWith("/personal-foods")) {
    return "food";
  }
  if (pathname === "/today/workout") {
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
