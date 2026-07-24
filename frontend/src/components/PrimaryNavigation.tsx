"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { LinkCardDeck } from "@/components/LinkCardDeck";
import {
  activeDailyWorkspace,
  buildDailyWorkspaceHref,
} from "@/lib/dailyNavigation";
import { PRIMARY_NAV_ITEMS } from "@/lib/appUiStandards";

interface PrimaryNavigationProps {
  userId: number;
  date?: string;
}

function MobileNavigationItems({ userId, date }: PrimaryNavigationProps) {
  const pathname = usePathname();
  const activeDestination = activeDailyWorkspace(pathname);

  return PRIMARY_NAV_ITEMS.map((item) => {
    const isActive = item.key === activeDestination;
    return (
      <Link
        key={item.key}
        href={buildDailyWorkspaceHref(item.key, userId, date)}
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
            className="absolute inset-x-3 bottom-1 h-0.5 rounded-full bg-action-primary"
          />
        ) : null}
      </Link>
    );
  });
}

export function PrimaryNavigation({ userId, date }: PrimaryNavigationProps) {
  const pathname = usePathname();
  const activeDestination = activeDailyWorkspace(pathname);
  const desktopItems = PRIMARY_NAV_ITEMS.map((item) => ({
    ...item,
    href: buildDailyWorkspaceHref(item.key, userId, date),
  }));

  return (
    <>
      <LinkCardDeck
        activeKey={activeDestination}
        ariaLabel="Primary navigation"
        className="hidden md:block"
        items={desktopItems}
      />
      <nav
        aria-label="Primary mobile navigation"
        className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-surface/95 px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-16px_35px_-28px_rgba(15,23,42,0.55)] backdrop-blur md:hidden"
      >
        <div className="mx-auto grid max-w-xl grid-cols-6 gap-1">
          <MobileNavigationItems userId={userId} date={date} />
        </div>
      </nav>
    </>
  );
}
