"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { TodayCard } from "@/components/TodayCard";
import { CANONICAL_FOOD_LOGGED_EVENT } from "@/types/canonicalFood";
import { DailyDriverNutritionSummary } from "@/types/dailyDriver";
import { PERSONAL_FOOD_LOGGED_EVENT } from "@/types/personalFood";

function formatNumber(value: number | null, suffix = ""): string {
  if (value === null) {
    return "--";
  }

  return `${value.toLocaleString()}${suffix}`;
}

export function NutritionMacroCard({
  nutrition,
  className,
}: {
  nutrition: DailyDriverNutritionSummary;
  className?: string;
}) {
  const router = useRouter();

  useEffect(() => {
    const refreshNutrition = () => router.refresh();

    window.addEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshNutrition);
    window.addEventListener(PERSONAL_FOOD_LOGGED_EVENT, refreshNutrition);

    return () => {
      window.removeEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshNutrition);
      window.removeEventListener(PERSONAL_FOOD_LOGGED_EVENT, refreshNutrition);
    };
  }, [router]);

  return (
    <TodayCard title="Nutrition" className={className}>
      <div className="space-y-3">
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
