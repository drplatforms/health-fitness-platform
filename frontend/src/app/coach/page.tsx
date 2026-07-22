import { DailyWorkspacePage } from "@/components/DailyWorkspacePage";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function CoachPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  return <DailyWorkspacePage workspace="coach" searchParams={searchParams} />;
}
