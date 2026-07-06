function ordinalSuffix(day: number): string {
  const remainder = day % 100;
  if (remainder >= 11 && remainder <= 13) {
    return "th";
  }

  switch (day % 10) {
    case 1:
      return "st";
    case 2:
      return "nd";
    case 3:
      return "rd";
    default:
      return "th";
  }
}

function formatDateParts(date: Date): string {
  const weekday = new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    timeZone: "UTC",
  }).format(date);
  const month = new Intl.DateTimeFormat("en-US", {
    month: "long",
    timeZone: "UTC",
  }).format(date);
  const day = Number(
    new Intl.DateTimeFormat("en-US", {
      day: "numeric",
      timeZone: "UTC",
    }).format(date),
  );
  const year = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    timeZone: "UTC",
  }).format(date);

  return `${weekday}, ${month} ${day}${ordinalSuffix(day)}, ${year}`;
}

export function formatLongReadableDate(
  value: string | null | undefined,
): string {
  const normalized = value?.trim() ?? "";
  const match = normalized.match(/^(\d{4})-(\d{2})-(\d{2})$/);

  if (match) {
    const [, year, month, day] = match;
    return formatDateParts(
      new Date(Date.UTC(Number(year), Number(month) - 1, Number(day))),
    );
  }

  if (normalized) {
    const fallbackDate = new Date(normalized);
    if (!Number.isNaN(fallbackDate.getTime())) {
      return formatDateParts(
        new Date(
          Date.UTC(
            fallbackDate.getUTCFullYear(),
            fallbackDate.getUTCMonth(),
            fallbackDate.getUTCDate(),
          ),
        ),
      );
    }

    return normalized;
  }

  const now = new Date();
  return formatDateParts(
    new Date(
      Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()),
    ),
  );
}
