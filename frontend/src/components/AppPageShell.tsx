import { Fragment, type ReactNode } from "react";

import { PrimaryNavigation } from "@/components/PrimaryNavigation";
import { UserSwitcher } from "@/components/UserSwitcher";

interface AppPageShellProps {
  children: ReactNode;
  dateLabel: string;
  headerAction?: ReactNode;
  navigationDate?: string;
  title: string;
  userId: number;
}

export function AppPageShell({
  children,
  dateLabel,
  headerAction,
  navigationDate,
  title,
  userId,
}: AppPageShellProps) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,var(--theme-canvas-glow),transparent_35%),linear-gradient(180deg,var(--theme-canvas-start)_0%,var(--theme-canvas)_100%)] px-3 py-3 text-text-strong sm:px-4 sm:py-6">
      <div className="mx-auto flex w-full max-w-7xl min-w-0 flex-col gap-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:gap-4 md:pb-8 lg:gap-6 lg:px-2">
        <header className="min-h-32 rounded-2xl bg-[linear-gradient(160deg,var(--theme-header-surface-start),var(--theme-header-surface-end))] p-4 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:p-5">
          <div className="flex min-h-24 items-start justify-between gap-3">
            <div className="min-w-0 pt-1">
              <h1 className="type-page-title truncate text-text-strong">
                {title}
              </h1>
              <p className="type-body mt-1 truncate text-text-body">
                {dateLabel}
              </p>
            </div>
            <div className="flex min-w-0 shrink-0 items-end gap-2">
              <UserSwitcher
                currentUserId={userId}
                selectClassName="bg-surface/90 py-2.5"
              />
              {headerAction}
            </div>
          </div>
        </header>

        <PrimaryNavigation userId={userId} date={navigationDate} />

        <Fragment key={`user:${userId}`}>{children}</Fragment>
      </div>
    </main>
  );
}
