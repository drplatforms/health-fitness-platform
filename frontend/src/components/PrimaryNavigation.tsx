"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  activeDailyWorkspace,
  buildDailyWorkspaceHref,
  DailyWorkspaceDestination,
} from "@/lib/dailyNavigation";

interface PrimaryNavigationProps {
  userId: number;
  date?: string;
}

const ITEMS: Array<{
  key: DailyWorkspaceDestination;
  label: string;
}> = [
  { key: "today", label: "Today" },
  { key: "food", label: "Food" },
  { key: "meals", label: "Meals" },
  { key: "coach", label: "Coach" },
  { key: "workout", label: "Workout" },
  { key: "recovery", label: "Recovery" },
];

function NavigationItems({
  userId,
  date,
  mobile,
}: PrimaryNavigationProps & { mobile: boolean }) {
  const pathname = usePathname();
  const activeDestination = activeDailyWorkspace(pathname);

  return ITEMS.map((item) => {
    const isActive = item.key === activeDestination;
    return (
      <Link
        key={item.key}
        href={buildDailyWorkspaceHref(item.key, userId, date)}
        aria-current={isActive ? "page" : undefined}
        className={`relative flex min-h-11 items-center justify-center rounded-xl px-1 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus md:px-3 md:text-sm ${
          isActive
            ? "bg-surface-highlighted text-accent-text"
            : "text-text-secondary hover:bg-surface-muted hover:text-text-primary"
        }`}
      >
        {item.label}
        {isActive ? (
          <span
            aria-hidden="true"
            className={`absolute h-0.5 rounded-full bg-action-primary ${
              mobile ? "inset-x-3 bottom-1" : "inset-x-4 bottom-0.5"
            }`}
          />
        ) : null}
      </Link>
    );
  });
}

export function PrimaryNavigation({ userId, date }: PrimaryNavigationProps) {
  return (
    <>
      <nav
        aria-label="Primary navigation"
        className="hidden rounded-2xl border border-border-subtle bg-surface/80 p-1 shadow-[0_16px_35px_-32px_rgba(15,23,42,0.55)] backdrop-blur md:block"
      >
        <div className="grid grid-cols-6 gap-1">
          <NavigationItems userId={userId} date={date} mobile={false} />
        </div>
      </nav>
      <nav
        aria-label="Primary mobile navigation"
        className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-surface/95 px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-16px_35px_-28px_rgba(15,23,42,0.55)] backdrop-blur md:hidden"
      >
        <div className="mx-auto grid max-w-xl grid-cols-6 gap-1">
          <NavigationItems userId={userId} date={date} mobile />
        </div>
      </nav>
    </>
  );
}
