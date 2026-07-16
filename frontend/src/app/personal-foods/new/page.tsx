import Link from "next/link";

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
    <main className="min-h-screen bg-canvas px-4 py-6 text-text-strong">
      <div className="mx-auto w-full max-w-2xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-4 text-sm font-semibold">
            <Link
              href={`/?${contextParams.toString()}`}
              className="text-accent-text hover:text-accent-text-hover"
            >
              Back to Today
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
        <section className="rounded-[28px] bg-surface px-5 py-5 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:px-6">
          <h1 className="mb-5 text-2xl font-semibold tracking-tight">Add food</h1>
          <PersonalFoodForm
            mode="create"
            userId={userId}
            targetDate={targetDate}
          />
        </section>
      </div>
    </main>
  );
}
