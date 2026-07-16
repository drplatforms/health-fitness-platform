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

function parseIsoCalendarDate(value: string): [number, number, number] | null {
  const match = value.trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    return null;
  }

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const normalized = new Date(Date.UTC(year, month - 1, day));

  if (
    normalized.getUTCFullYear() !== year ||
    normalized.getUTCMonth() !== month - 1 ||
    normalized.getUTCDate() !== day
  ) {
    return null;
  }

  return [year, month, day];
}

export function getBrowserLocalDateString(now: Date = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function compareIsoCalendarDates(
  left: string,
  right: string,
): -1 | 0 | 1 | null {
  const leftParts = parseIsoCalendarDate(left);
  const rightParts = parseIsoCalendarDate(right);

  if (!leftParts || !rightParts) {
    return null;
  }

  const leftValue = leftParts[0] * 10_000 + leftParts[1] * 100 + leftParts[2];
  const rightValue =
    rightParts[0] * 10_000 + rightParts[1] * 100 + rightParts[2];

  return leftValue === rightValue ? 0 : leftValue < rightValue ? -1 : 1;
}

export function isHistoricalRequestedDate(
  requestedDate: string | null | undefined,
  browserLocalDate: string = getBrowserLocalDateString(),
): boolean {
  if (!requestedDate) {
    return false;
  }

  return compareIsoCalendarDates(requestedDate, browserLocalDate) === -1;
}

export function millisecondsUntilNextLocalMidnight(
  now: Date = new Date(),
): number {
  const nextLocalMidnight = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() + 1,
  );
  return Math.max(0, nextLocalMidnight.getTime() - now.getTime());
}

export interface LiveDayRolloverEnvironment {
  requestedDate?: string;
  now: () => Date;
  schedule: (callback: () => void, delayMilliseconds: number) => number;
  cancel: (timeoutId: number) => void;
  reload: () => void;
  isVisible: () => boolean;
  onVisibilityChange: (callback: () => void) => () => void;
  onFocus: (callback: () => void) => () => void;
}

export function startLiveDayRolloverWatcher(
  environment: LiveDayRolloverEnvironment,
): () => void {
  if (environment.requestedDate) {
    return () => undefined;
  }

  const capturedDate = getBrowserLocalDateString(environment.now());
  let timeoutId: number | null = null;
  let isReloading = false;

  function scheduleNextCheck() {
    if (timeoutId !== null) {
      environment.cancel(timeoutId);
    }

    timeoutId = environment.schedule(
      checkForNewDay,
      millisecondsUntilNextLocalMidnight(environment.now()) + 50,
    );
  }

  function checkForNewDay() {
    if (isReloading) {
      return;
    }

    if (getBrowserLocalDateString(environment.now()) !== capturedDate) {
      isReloading = true;
      environment.reload();
      return;
    }

    scheduleNextCheck();
  }

  function handleVisibilityChange() {
    if (environment.isVisible()) {
      checkForNewDay();
    }
  }

  scheduleNextCheck();
  const removeVisibilityListener =
    environment.onVisibilityChange(handleVisibilityChange);
  const removeFocusListener = environment.onFocus(checkForNewDay);

  return () => {
    if (timeoutId !== null) {
      environment.cancel(timeoutId);
    }
    removeVisibilityListener();
    removeFocusListener();
  };
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
