import { DailyWorkspacePage } from "@/components/DailyWorkspacePage";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function RecoveryPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  return <DailyWorkspacePage workspace="recovery" searchParams={searchParams} />;
}
