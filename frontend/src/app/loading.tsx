export default function Loading() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,var(--theme-canvas-glow),transparent_35%),linear-gradient(180deg,var(--theme-canvas-start)_0%,var(--theme-canvas)_100%)] px-4 py-6 text-text-strong">
      <div className="mx-auto flex w-full max-w-md flex-col gap-4">
        <div className="animate-pulse rounded-[32px] bg-surface/80 p-6 shadow-[0_18px_40px_-32px_rgba(15,23,42,0.4)]">
          <div className="h-4 w-24 rounded-full bg-surface-interactive-hover" />
          <div className="mt-4 h-10 w-56 rounded-2xl bg-surface-interactive-hover" />
          <div className="mt-3 h-4 w-44 rounded-full bg-surface-muted" />
        </div>
        <div className="animate-pulse rounded-[32px] bg-surface-highlighted p-6 shadow-[0_18px_40px_-32px_rgba(15,23,42,0.4)]">
          <div className="h-4 w-28 rounded-full bg-border-accent" />
          <div className="mt-4 h-9 w-52 rounded-2xl bg-border-accent" />
          <div className="mt-3 h-4 w-full rounded-full bg-positive-surface" />
          <div className="mt-2 h-4 w-40 rounded-full bg-positive-surface" />
        </div>
      </div>
    </main>
  );
}
