"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.16),_transparent_35%),linear-gradient(180deg,#fffdf7_0%,#f8fafc_100%)] px-4 py-6 text-slate-950">
      <div className="mx-auto flex w-full max-w-md flex-col gap-4">
        <section className="rounded-[32px] border border-rose-200 bg-white p-6 shadow-[0_18px_40px_-32px_rgba(15,23,42,0.4)]">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-rose-700">
            Today
          </p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">
            Something went wrong
          </h1>
          <p className="mt-3 text-sm leading-6 text-slate-700">
            Refresh the page or try again after the backend is running.
          </p>
          <button
            type="button"
            onClick={reset}
            className="mt-5 inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Try again
          </button>
        </section>
      </div>
    </main>
  );
}
