"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,var(--theme-canvas-glow),transparent_35%),linear-gradient(180deg,var(--theme-canvas-start)_0%,var(--theme-canvas)_100%)] px-4 py-6 text-text-strong">
      <div className="mx-auto flex w-full max-w-md flex-col gap-4">
        <section className="rounded-[32px] border border-danger-action bg-surface p-6 shadow-[0_18px_40px_-32px_rgba(15,23,42,0.4)]">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-danger-action">
            Today
          </p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-text-strong">
            Something went wrong
          </h1>
          <p className="mt-3 text-sm leading-6 text-text-body">
            Refresh the page or try again after the backend is running.
          </p>
          <button
            type="button"
            onClick={reset}
            className="mt-5 inline-flex rounded-full bg-control-selected-surface px-5 py-3 text-sm font-semibold text-text-inverse transition hover:bg-control-selected-surface-hover"
          >
            Try again
          </button>
        </section>
      </div>
    </main>
  );
}
