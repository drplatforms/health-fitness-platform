import Link from "next/link";
import { notFound } from "next/navigation";

import { PersonalFoodForm } from "@/components/PersonalFoodForm";
import { getDefaultUserId } from "@/lib/dailyDriverApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function EditPersonalFoodPage({
  params,
  searchParams,
}: {
  params: Promise<{ personalFoodId: string }>;
  searchParams: SearchParams;
}) {
  const [{ personalFoodId: rawFoodId }, query] = await Promise.all([
    params,
    searchParams,
  ]);
  const personalFoodId = Number(rawFoodId);
  if (!Number.isInteger(personalFoodId) || personalFoodId <= 0) {
    notFound();
  }
  const parsedUserId = Number(first(query.user_id));
  const userId =
    Number.isInteger(parsedUserId) && parsedUserId > 0
      ? parsedUserId
      : getDefaultUserId();
  const targetDate = first(query.date);
  const contextParams = new URLSearchParams({ user_id: String(userId) });
  if (targetDate) {
    contextParams.set("date", targetDate);
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6 text-slate-950">
      <div className="mx-auto w-full max-w-2xl space-y-4">
        <div className="flex flex-wrap gap-4 text-sm font-semibold">
          <Link href={`/?${contextParams.toString()}`} className="text-emerald-800">
            Back to Today
          </Link>
          <Link
            href={`/personal-foods?${contextParams.toString()}`}
            className="text-slate-600"
          >
            My foods
          </Link>
        </div>
        <section className="rounded-[28px] bg-white px-5 py-5 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:px-6">
          <h1 className="mb-5 text-2xl font-semibold tracking-tight">Edit food</h1>
          <PersonalFoodForm
            mode="edit"
            userId={userId}
            personalFoodId={personalFoodId}
            targetDate={targetDate}
          />
        </section>
      </div>
    </main>
  );
}
