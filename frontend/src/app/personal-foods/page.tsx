import Link from "next/link";

import { PersonalFoodsList } from "@/components/PersonalFoodsList";
import { getDefaultUserId } from "@/lib/dailyDriverApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function userIdFrom(value: string | undefined): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : getDefaultUserId();
}

export default async function PersonalFoodsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const userId = userIdFrom(first(params.user_id));
  const targetDate = first(params.date);
  const todayParams = new URLSearchParams({ user_id: String(userId) });
  if (targetDate) {
    todayParams.set("date", targetDate);
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6 text-slate-950">
      <div className="mx-auto w-full max-w-3xl space-y-4">
        <Link
          href={`/?${todayParams.toString()}`}
          className="text-sm font-semibold text-emerald-800 hover:text-emerald-950"
        >
          Back to Today
        </Link>
        <section className="rounded-[28px] bg-white px-5 py-5 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:px-6">
          <PersonalFoodsList userId={userId} targetDate={targetDate} />
        </section>
      </div>
    </main>
  );
}
