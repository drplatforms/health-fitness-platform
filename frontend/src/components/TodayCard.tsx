import { ReactNode } from "react";

interface TodayCardProps {
  eyebrow?: string;
  title: string;
  children: ReactNode;
  accent?: "default" | "warm" | "highlight" | "subtle";
}

const ACCENT_CLASS_MAP = {
  default: "border-slate-200 bg-white",
  warm: "border-amber-200 bg-amber-50/70",
  highlight: "border-emerald-300 bg-emerald-50/90 shadow-[0_18px_45px_-28px_rgba(5,150,105,0.55)]",
  subtle: "border-slate-200/80 bg-slate-50/90",
} as const;

export function TodayCard({
  eyebrow,
  title,
  children,
  accent = "default",
}: TodayCardProps) {
  return (
    <section
      className={`rounded-[28px] border p-5 shadow-[0_20px_40px_-32px_rgba(15,23,42,0.45)] ${ACCENT_CLASS_MAP[accent]}`}
    >
      <div className="flex flex-col gap-4">
        <div className="space-y-1">
          {eyebrow ? (
            <p className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-slate-500">
              {eyebrow}
            </p>
          ) : null}
          <h2 className="text-xl font-semibold text-slate-950">{title}</h2>
        </div>
        {children}
      </div>
    </section>
  );
}
