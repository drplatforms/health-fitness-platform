import Link from "next/link";

import { MobilePrimaryNav } from "@/components/MobilePrimaryNav";
import { PersonalFoodForm } from "@/components/PersonalFoodForm";
import { ThemePreferenceControl } from "@/components/ThemePreferenceControl";
import { getDefaultUserId } from "@/lib/dailyDriverApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function NewPersonalFoodPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const parsedUserId = Number(first(params.user_id));
  const userId =
    Number.isInteger(parsedUserId) && parsedUserId > 0
      ? parsedUserId
      : getDefaultUserId();
  const targetDate = first(params.date);
  const contextParams = new URLSearchParams({ user_id: String(userId) });
  if (targetDate) {
    contextParams.set("date", targetDate);
  }

  return (
    <main className="min-h-screen bg-canvas px-3 py-3 text-text-strong sm:px-4 sm:py-6">
      <div className="mx-auto w-full max-w-2xl space-y-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:space-y-4 md:pb-0">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-4 text-sm font-semibold">
            <Link
              href={`/food?${contextParams.toString()}`}
              className="hidden text-accent-text hover:text-accent-text-hover md:inline"
            >
              Back to Food
            </Link>
            <Link
              href={`/personal-foods?${contextParams.toString()}`}
              className="text-text-secondary hover:text-text-primary"
            >
              My Foods
            </Link>
          </div>
          <ThemePreferenceControl />
        </div>
        <section className="rounded-2xl bg-surface px-4 py-4 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:rounded-[28px] sm:px-6 sm:py-5">
          <h1 className="mb-4 text-2xl font-semibold tracking-tight sm:mb-5">Add food</h1>
          <PersonalFoodForm
            mode="create"
            userId={userId}
            targetDate={targetDate}
          />
        </section>
      </div>
      <MobilePrimaryNav userId={userId} date={targetDate} />
    </main>
  );
}
