import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  DailyDriverNutritionStatus,
  DailyDriverNutritionSummary,
} from "@/types/dailyDriver";

const nutritionToneMap: Record<
  DailyDriverNutritionStatus,
  "positive" | "caution" | "warning" | "neutral"
> = {
  on_track: "positive",
  behind: "warning",
  complete: "positive",
  not_logged: "caution",
  unknown: "neutral",
};

function formatNumber(value: number | null, suffix = ""): string {
  if (value === null) {
    return "Not available";
  }

  return `${value.toLocaleString()}${suffix}`;
}

function resolveStatusLine(nutrition: DailyDriverNutritionSummary): string {
  if (
    nutrition.status === "not_logged" &&
    nutrition.calories_logged === null &&
    nutrition.protein_logged_g === null &&
    nutrition.carbs_logged_g === null &&
    nutrition.fat_logged_g === null
  ) {
    return "No nutrition logged yet today.";
  }

  return nutrition.today_mission;
}

export function NutritionMacroCard({
  nutrition,
  className,
}: {
  nutrition: DailyDriverNutritionSummary;
  className?: string;
}) {
  return (
    <TodayCard title="Nutrition" className={className}>
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm leading-6 text-slate-700">
            {resolveStatusLine(nutrition)}
          </p>
          <StatusPill
            label={nutrition.status.replace("_", " ")}
            tone={nutritionToneMap[nutrition.status]}
          />
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Calories
            </p>
            <p className="mt-2 font-semibold text-slate-900">
              {formatNumber(nutrition.calories_logged)} /{" "}
              {formatNumber(nutrition.calorie_target)}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Protein
            </p>
            <p className="mt-2 font-semibold text-slate-900">
              {formatNumber(nutrition.protein_logged_g, "g")} /{" "}
              {formatNumber(nutrition.protein_target_g, "g")}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Carbs
            </p>
            <p className="mt-2 font-semibold text-slate-900">
              {formatNumber(nutrition.carbs_logged_g, "g")} /{" "}
              {formatNumber(nutrition.carbohydrate_target_g, "g")}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Fat
            </p>
            <p className="mt-2 font-semibold text-slate-900">
              {formatNumber(nutrition.fat_logged_g, "g")} /{" "}
              {formatNumber(nutrition.fat_target_g, "g")}
            </p>
          </div>
        </div>
      </div>
    </TodayCard>
  );
}
