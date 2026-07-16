import { ReactNode } from "react";

interface TodayCardProps {
  eyebrow?: string;
  title: string;
  children: ReactNode;
  accent?: "default" | "warm" | "highlight" | "subtle";
  className?: string;
}

const ACCENT_CLASS_MAP = {
  default: "border-border bg-surface",
  warm: "border-border-warm bg-surface-warm",
  highlight: "border-border-accent bg-surface-highlighted shadow-[0_18px_45px_-28px_rgba(5,150,105,0.55)]",
  subtle: "border-border-subtle/80 bg-surface-subtle/90",
} as const;

export function TodayCard({
  eyebrow,
  title,
  children,
  accent = "default",
  className = "",
}: TodayCardProps) {
  return (
    <section
      className={`rounded-2xl border p-4 shadow-[0_20px_40px_-32px_rgba(15,23,42,0.45)] sm:rounded-[28px] sm:p-5 ${ACCENT_CLASS_MAP[accent]} ${className}`}
    >
      <div className="flex flex-col gap-3 sm:gap-4">
        <div className="space-y-1">
          {eyebrow ? (
            <p className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-text-muted">
              {eyebrow}
            </p>
          ) : null}
          <h2 className="text-xl font-semibold text-text-strong">{title}</h2>
        </div>
        {children}
      </div>
    </section>
  );
}
