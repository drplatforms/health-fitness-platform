import { DailyWorkspacePage } from "@/components/DailyWorkspacePage";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function FoodPage({ searchParams }: { searchParams: SearchParams }) {
  return <DailyWorkspacePage workspace="food" searchParams={searchParams} />;
}
