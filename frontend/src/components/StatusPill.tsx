interface StatusPillProps {
  label: string;
  tone?: "neutral" | "positive" | "caution" | "warning";
}

const TONE_CLASS_MAP = {
  neutral: "bg-slate-100 text-slate-700",
  positive: "bg-emerald-100 text-emerald-800",
  caution: "bg-amber-100 text-amber-900",
  warning: "bg-rose-100 text-rose-800",
} as const;

export function StatusPill({
  label,
  tone = "neutral",
}: StatusPillProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold tracking-[0.12em] uppercase ${TONE_CLASS_MAP[tone]}`}
    >
      {label}
    </span>
  );
}
