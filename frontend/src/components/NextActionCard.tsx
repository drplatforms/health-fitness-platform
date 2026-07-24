import Link from "next/link";

import { DailyDriverNextAction } from "@/types/dailyDriver";

interface NextActionCardProps {
  action: DailyDriverNextAction;
  href?: string | null;
  className?: string;
}

export function NextActionCard({
  action,
  href = null,
  className = "",
}: NextActionCardProps) {
  return (
    <section
      className={`rounded-2xl border border-border-accent [background:var(--theme-next-action-surface)] p-4 shadow-[0_24px_50px_-30px_rgba(5,150,105,0.65)] sm:p-5 ${className}`}
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <p className="type-compact-metadata font-semibold uppercase tracking-[0.18em] text-accent-text">
            Next Action
          </p>
          <h2 className="type-section-title text-positive-foreground-strong">
            {action.label}
          </h2>
          <p className="max-w-2xl text-sm leading-6 text-positive-foreground md:text-base">
            {action.context}
          </p>
        </div>
        {href ? (
          <Link
            href={href}
            className="inline-flex rounded-2xl bg-action-primary px-4 py-3 text-center text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover md:max-w-sm"
          >
            Open workout details
          </Link>
        ) : (
          <div className="rounded-2xl bg-action-primary px-4 py-3 text-center text-sm font-semibold text-action-primary-foreground md:max-w-sm">
            Start here.
          </div>
        )}
      </div>
    </section>
  );
}
