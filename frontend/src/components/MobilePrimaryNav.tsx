"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  activeDailyWorkspace,
  buildDailyWorkspaceHref,
  DailyWorkspaceDestination,
} from "@/lib/dailyNavigation";

interface MobilePrimaryNavProps {
  userId: number;
  date?: string;
}

export function MobilePrimaryNav({ userId, date }: MobilePrimaryNavProps) {
  const pathname = usePathname();
  const activeDestination = activeDailyWorkspace(pathname);
  const items: Array<{
    key: DailyWorkspaceDestination;
    label: string;
  }> = [
    {
      key: "today",
      label: "Today",
    },
    {
      key: "food",
      label: "Food",
    },
    {
      key: "workout",
      label: "Workout",
    },
    {
      key: "recovery",
      label: "Recovery",
    },
  ];

  return (
    <nav
      aria-label="Primary mobile navigation"
      className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-surface/95 px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-16px_35px_-28px_rgba(15,23,42,0.55)] backdrop-blur md:hidden"
    >
      <div className="mx-auto grid max-w-lg grid-cols-4 gap-1">
        {items.map((item) => {
          const isActive = item.key === activeDestination;
          const href = buildDailyWorkspaceHref(item.key, userId, date);

          return (
            <Link
              key={item.key}
              href={href}
              aria-current={isActive ? "page" : undefined}
              className={`relative flex min-h-11 items-center justify-center rounded-xl px-1 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus ${
                isActive
                  ? "bg-surface-highlighted text-accent-text"
                  : "text-text-secondary hover:bg-surface-muted hover:text-text-primary"
              }`}
            >
              {item.label}
              {isActive ? (
                <span
                  aria-hidden="true"
                  className="absolute inset-x-4 bottom-1 h-0.5 rounded-full bg-action-primary"
                />
              ) : null}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
