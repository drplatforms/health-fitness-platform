import { DailyWorkspacePage } from "@/components/DailyWorkspacePage";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function MealsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  return <DailyWorkspacePage workspace="meals" searchParams={searchParams} />;
}
