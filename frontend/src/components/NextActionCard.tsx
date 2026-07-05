import { DailyDriverNextAction } from "@/types/dailyDriver";

interface NextActionCardProps {
  action: DailyDriverNextAction;
}

export function NextActionCard({ action }: NextActionCardProps) {
  return (
    <section className="rounded-[32px] border border-emerald-300 bg-[linear-gradient(160deg,rgba(236,253,245,0.96),rgba(209,250,229,0.92))] p-6 shadow-[0_24px_50px_-30px_rgba(5,150,105,0.65)]">
      <div className="space-y-4">
        <div className="space-y-2">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-emerald-700">
            Next Action
          </p>
          <h2 className="text-2xl font-semibold tracking-tight text-emerald-950">
            {action.label}
          </h2>
          <p className="text-sm leading-6 text-emerald-900/85">{action.context}</p>
        </div>
        <div className="rounded-2xl bg-emerald-950 px-4 py-3 text-center text-sm font-semibold text-emerald-50">
          What should I do now? Start here.
        </div>
      </div>
    </section>
  );
}
