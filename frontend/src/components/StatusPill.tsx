interface StatusPillProps {
  label: string;
  tone?: "neutral" | "positive" | "caution" | "warning";
}

const TONE_CLASS_MAP = {
  neutral: "bg-neutral-surface text-neutral-foreground",
  positive: "bg-positive-surface text-positive-foreground",
  caution: "bg-caution-surface text-caution-foreground",
  warning: "bg-warning-surface text-warning-foreground",
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
