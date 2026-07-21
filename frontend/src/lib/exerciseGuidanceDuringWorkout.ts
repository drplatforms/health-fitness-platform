export type ExerciseGuidanceMobilePresentation = "inline" | "dialog";

export interface ExerciseGuidancePresentation {
  mobilePresentation: ExerciseGuidanceMobilePresentation;
  showProfileControls: boolean;
  triggerLabel: string | null;
}

export function exerciseGuidancePresentation(
  canLogWorkout: boolean,
): ExerciseGuidancePresentation {
  return canLogWorkout
    ? {
        mobilePresentation: "dialog",
        showProfileControls: false,
        triggerLabel: "Form guide",
      }
    : {
        mobilePresentation: "inline",
        showProfileControls: true,
        triggerLabel: null,
      };
}
