export default function Loading() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.16),_transparent_35%),linear-gradient(180deg,#fffdf7_0%,#f8fafc_100%)] px-4 py-6 text-slate-950">
      <div className="mx-auto flex w-full max-w-md flex-col gap-4">
        <div className="animate-pulse rounded-[32px] bg-white/80 p-6 shadow-[0_18px_40px_-32px_rgba(15,23,42,0.4)]">
          <div className="h-4 w-24 rounded-full bg-slate-200" />
          <div className="mt-4 h-10 w-56 rounded-2xl bg-slate-200" />
          <div className="mt-3 h-4 w-44 rounded-full bg-slate-100" />
        </div>
        <div className="animate-pulse rounded-[32px] bg-emerald-50 p-6 shadow-[0_18px_40px_-32px_rgba(15,23,42,0.4)]">
          <div className="h-4 w-28 rounded-full bg-emerald-200" />
          <div className="mt-4 h-9 w-52 rounded-2xl bg-emerald-200" />
          <div className="mt-3 h-4 w-full rounded-full bg-emerald-100" />
          <div className="mt-2 h-4 w-40 rounded-full bg-emerald-100" />
        </div>
      </div>
    </main>
  );
}
