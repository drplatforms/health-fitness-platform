import Link from "next/link";
import { notFound } from "next/navigation";

import { AppPageShell } from "@/components/AppPageShell";
import { PersonalFoodForm } from "@/components/PersonalFoodForm";
import { getDefaultUserId } from "@/lib/dailyDriverApi";
import { formatLongReadableDate } from "@/lib/dateFormatting";

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
  contextParams.set("view", "library");

  return (
    <AppPageShell
      title="Edit food"
      dateLabel={formatLongReadableDate(targetDate)}
      userId={userId}
      navigationDate={targetDate}
    >
      <div className="mx-auto w-full max-w-2xl space-y-3 sm:space-y-4">
        <Link
          href={`/food?${contextParams.toString()}`}
          className="type-button inline-flex text-accent-text hover:text-accent-text-hover"
        >
          Back to Food Library
        </Link>
        <section className="rounded-2xl bg-surface p-4 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:p-5">
          <PersonalFoodForm
            key={`${userId}:${personalFoodId}`}
            mode="edit"
            userId={userId}
            personalFoodId={personalFoodId}
            targetDate={targetDate}
          />
        </section>
      </div>
    </AppPageShell>
  );
}
