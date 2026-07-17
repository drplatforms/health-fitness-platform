import { getBrowserLocalDateString } from "@/lib/dateFormatting";
import { DailyDriverApiError } from "@/lib/dailyDriverApi";
import {
  buildWeeklyWorkoutHref,
  getMondayWeekStart,
  previewWeeklySessionTitles,
  shiftWeekStart,
  weekDateStrings,
} from "@/lib/weeklyTrainingPlanDates";
import {
  WeeklyTrainingPlan,
  WeeklyTrainingPlanResponse,
  WeeklyWorkoutSizePreference,
} from "@/types/weeklyTrainingPlan";

export interface WeeklyTrainingPlanApiResult {
  data: WeeklyTrainingPlanResponse | null;
  error: DailyDriverApiError | null;
}

export interface WeeklyTrainingPlanMutation {
  weekStartDate: string;
  trainingWeekdays: number[];
  defaultWorkoutSizePreference: WeeklyWorkoutSizePreference;
  currentDate?: string;
}

export function resolveVisibleWeekStart(explicitWeekStart?: string): string {
  return getMondayWeekStart(explicitWeekStart ?? getBrowserLocalDateString());
}

export {
  buildWeeklyWorkoutHref,
  getMondayWeekStart,
  previewWeeklySessionTitles,
  shiftWeekStart,
  weekDateStrings,
};

async function parseResult(response: Response): Promise<WeeklyTrainingPlanApiResult> {
  const payload = (await response.json().catch(() => null)) as
    | WeeklyTrainingPlanResponse
    | { detail?: string }
    | null;
  if (!response.ok) {
    return {
      data: null,
      error: {
        heading: "Unable to save weekly plan",
        message:
          (payload && "detail" in payload ? payload.detail : null) ??
          "The backend could not update the weekly training plan.",
        statusCode: response.status,
      },
    };
  }
  return { data: payload as WeeklyTrainingPlanResponse, error: null };
}

export async function fetchWeeklyTrainingPlan(
  userId: number,
  weekStartDate: string,
  currentDate = getBrowserLocalDateString(),
): Promise<WeeklyTrainingPlanApiResult> {
  const params = new URLSearchParams({
    user_id: String(userId),
    week_start_date: getMondayWeekStart(weekStartDate),
    current_date: currentDate,
  });
  try {
    return await parseResult(
      await fetch(`/api/weekly-training-plans?${params.toString()}`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      }),
    );
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then refresh the weekly planner.",
      },
    };
  }
}

export async function createWeeklyTrainingPlan(
  userId: number,
  mutation: WeeklyTrainingPlanMutation,
): Promise<WeeklyTrainingPlanApiResult> {
  try {
    return await parseResult(
      await fetch("/api/weekly-training-plans", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          week_start_date: getMondayWeekStart(mutation.weekStartDate),
          training_weekdays: mutation.trainingWeekdays,
          default_workout_size_preference:
            mutation.defaultWorkoutSizePreference,
          current_date: mutation.currentDate ?? getBrowserLocalDateString(),
        }),
      }),
    );
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then try saving the week again.",
      },
    };
  }
}

export async function updateWeeklyTrainingPlan(
  userId: number,
  plan: WeeklyTrainingPlan,
  mutation: WeeklyTrainingPlanMutation,
): Promise<WeeklyTrainingPlanApiResult> {
  try {
    return await parseResult(
      await fetch("/api/weekly-training-plans", {
        method: "PATCH",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          weekly_plan_id: plan.id,
          training_weekdays: mutation.trainingWeekdays,
          default_workout_size_preference:
            mutation.defaultWorkoutSizePreference,
          current_date: mutation.currentDate ?? getBrowserLocalDateString(),
        }),
      }),
    );
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then try updating the week again.",
      },
    };
  }
}
