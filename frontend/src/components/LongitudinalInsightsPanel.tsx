import type { DailyDriverApiError } from "@/lib/dailyDriverApi";
import type {
  LongitudinalInsight,
  LongitudinalInsightDomain,
  LongitudinalInsightResponse,
} from "@/types/longitudinalInsight";

interface LongitudinalInsightsPanelProps {
  data: LongitudinalInsightResponse | null;
  error: DailyDriverApiError | null;
}

const domainLabels: Record<LongitudinalInsightDomain, string> = {
  recovery: "Recovery",
  training: "Training",
  nutrition: "Nutrition",
  body_weight: "Body weight",
  cross_domain: "Recovery + training",
};

const domainToneClasses: Record<LongitudinalInsightDomain, string> = {
  recovery: "bg-caution-surface text-caution-foreground",
  training: "bg-positive-surface text-positive-foreground-strong",
  nutrition: "bg-surface-warm text-text-warm",
  body_weight: "bg-neutral-surface text-neutral-foreground",
  cross_domain: "bg-surface-highlighted text-positive-foreground-strong",
};

export function LongitudinalInsightsPanel({
  data,
  error,
}: LongitudinalInsightsPanelProps) {
  const insights = data?.insights ?? [];

  return (
    <section
      aria-labelledby="longitudinal-insights-heading"
      className="overflow-hidden rounded-2xl border border-border-accent bg-surface shadow-[0_18px_40px_-34px_rgba(15,23,42,0.7)]"
    >
      <div className="flex items-end justify-between gap-4 border-b border-border-subtle bg-[linear-gradient(145deg,var(--theme-surface-highlighted),var(--theme-surface))] px-4 py-4 sm:px-5">
        <div>
          <p className="type-compact-metadata font-semibold uppercase tracking-[0.18em] text-accent-text">
            Patterns from your history
          </p>
          <h2
            id="longitudinal-insights-heading"
            className="mt-1 text-xl font-semibold tracking-tight text-text-strong"
          >
            Insights
          </h2>
        </div>
        {insights.length > 0 ? (
          <span className="rounded-full bg-surface px-3 py-1 text-xs font-semibold text-text-secondary ring-1 ring-border">
            {insights.length} current
          </span>
        ) : null}
      </div>

      <div className="p-4 sm:p-5">
        {error ? (
          <div className="rounded-2xl bg-surface-subtle px-4 py-3">
            <p className="text-sm font-semibold text-text-primary">{error.heading}</p>
            <p className="mt-1 text-sm leading-6 text-text-body">{error.message}</p>
          </div>
        ) : insights.length === 0 ? (
          <div className="rounded-2xl bg-surface-subtle px-4 py-4">
            <p className="text-sm font-semibold text-text-primary">
              No strong historical pattern is ready yet.
            </p>
            <p className="mt-1 text-sm leading-6 text-text-body">
              Insights appear only when enough comparable check-ins, workouts, or
              complete-enough nutrition logs support them.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {insights.map((insight) => (
              <InsightCard key={insight.stable_id} insight={insight} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function InsightCard({ insight }: { insight: LongitudinalInsight }) {
  const comparisonWindow = insight.comparison_window;

  return (
    <article className="flex min-w-0 flex-col rounded-2xl border border-border bg-surface px-4 py-4">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`type-compact-metadata rounded-full px-2.5 py-1 font-semibold uppercase tracking-[0.12em] ${domainToneClasses[insight.domain]}`}
        >
          {domainLabels[insight.domain]}
        </span>
        <span className="text-xs font-medium capitalize text-text-muted">
          {insight.evidence_strength} evidence
        </span>
      </div>

      <h3 className="mt-3 text-base font-semibold leading-6 text-text-strong">
        {insight.title}
      </h3>
      <p className="mt-1.5 text-sm leading-6 text-text-body">
        {insight.explanation}
      </p>

      <p className="mt-3 text-xs leading-5 text-text-muted">
        {insight.observation_window.label} · {insight.observation_window.observation_count}{" "}
        observations
        {comparisonWindow
          ? ` · compared with ${comparisonWindow.observation_count} prior observations`
          : ""}
      </p>

      <details className="mt-3 border-t border-border-subtle pt-3">
        <summary className="cursor-pointer text-sm font-semibold text-accent-text hover:text-accent-text-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
          View supporting evidence
        </summary>
        <div className="mt-3 space-y-2">
          {insight.evidence.map((evidence) => (
            <div
              key={`${insight.stable_id}:${evidence.metric}`}
              className="flex items-start justify-between gap-4 rounded-xl bg-surface-subtle px-3 py-2"
            >
              <span className="text-xs leading-5 text-text-secondary">
                {evidence.label}
              </span>
              <span className="text-right text-xs font-semibold leading-5 text-text-primary">
                {evidence.value}
              </span>
            </div>
          ))}
          {insight.data_coverage.limitations.map((limitation) => (
            <p key={limitation} className="text-xs leading-5 text-text-muted">
              {limitation}
            </p>
          ))}
        </div>
      </details>
    </article>
  );
}
