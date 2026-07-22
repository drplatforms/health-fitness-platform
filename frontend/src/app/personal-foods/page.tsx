import { redirect } from "next/navigation";

import { getDefaultUserId } from "@/lib/dailyDriverApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function PersonalFoodsRedirect({
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
  const destination = new URLSearchParams({
    user_id: String(userId),
    view: "library",
  });
  const targetDate = first(params.date);
  if (targetDate) destination.set("date", targetDate);
  redirect(`/food?${destination.toString()}`);
}
