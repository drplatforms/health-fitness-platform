const weeklySessionSequences: Record<number, string[]> = {
  1: ["Full Body A"],
  2: ["Full Body A", "Full Body B"],
  3: ["Full Body A", "Full Body B", "Full Body C"],
  4: ["Upper A", "Lower A", "Upper B", "Lower B"],
  5: ["Upper A", "Lower A", "Full Body C", "Upper B", "Lower B"],
  6: ["Upper A", "Lower A", "Upper B", "Lower B", "Upper C", "Lower C"],
};

function parseDateOnly(value: string): Date {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    throw new Error("Expected a YYYY-MM-DD date.");
  }
  const result = new Date(
    Number(match[1]),
    Number(match[2]) - 1,
    Number(match[3]),
  );
  if (
    result.getFullYear() !== Number(match[1]) ||
    result.getMonth() !== Number(match[2]) - 1 ||
    result.getDate() !== Number(match[3])
  ) {
    throw new Error("Expected a valid calendar date.");
  }
  return result;
}

function formatDateOnly(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function getMondayWeekStart(value: string): string {
  const date = parseDateOnly(value);
  const mondayOffset = (date.getDay() + 6) % 7;
  date.setDate(date.getDate() - mondayOffset);
  return formatDateOnly(date);
}

export function shiftWeekStart(weekStartDate: string, weeks: number): string {
  const date = parseDateOnly(getMondayWeekStart(weekStartDate));
  date.setDate(date.getDate() + weeks * 7);
  return formatDateOnly(date);
}

export function weekDateStrings(weekStartDate: string): string[] {
  const monday = parseDateOnly(getMondayWeekStart(weekStartDate));
  return Array.from({ length: 7 }, (_, index) => {
    const value = new Date(monday);
    value.setDate(monday.getDate() + index);
    return formatDateOnly(value);
  });
}

export function previewWeeklySessionTitles(
  trainingWeekdays: number[],
): Array<{ weekday: number; title: string }> {
  const weekdays = [...new Set(trainingWeekdays)].sort((a, b) => a - b);
  const sequence = weeklySessionSequences[weekdays.length] ?? [];
  return weekdays.map((weekday, index) => ({
    weekday,
    title: sequence[index] ?? "Training",
  }));
}

export function buildWeeklyWorkoutHref(
  userId: number,
  explicitWeekStart?: string,
): string {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (explicitWeekStart) {
    params.set("week_start_date", getMondayWeekStart(explicitWeekStart));
  }
  return `/workout/week?${params.toString()}`;
}
