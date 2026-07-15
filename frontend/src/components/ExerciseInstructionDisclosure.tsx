"use client";

import { useId, useState } from "react";

import styles from "@/components/ExerciseInstructionDisclosure.module.css";
import { fetchExerciseInstruction } from "@/lib/exerciseInstructionApi";
import { ExerciseInstructionResponse } from "@/types/exerciseInstruction";

interface ExerciseInstructionDisclosureProps {
  catalogExerciseId: number | null;
  exerciseName: string;
  isExpanded: boolean;
  onExpandedChange: (isExpanded: boolean) => void;
}

interface InstructionSectionProps {
  heading: string;
  items: string[];
}

function InstructionSection({ heading, items }: InstructionSectionProps) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="space-y-1.5">
      <h3 className="text-sm font-semibold text-slate-900">{heading}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm leading-5 text-slate-700 marker:text-emerald-700">
        {items.map((item, index) => (
          <li key={`${heading}-${index + 1}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function ExerciseInstructionDisclosure({
  catalogExerciseId,
  exerciseName,
  isExpanded,
  onExpandedChange,
}: ExerciseInstructionDisclosureProps) {
  const disclosureId = useId();
  const mobilePanelId = `${disclosureId}-mobile`;
  const desktopPanelId = `${disclosureId}-desktop`;
  const [isLoading, setIsLoading] = useState(false);
  const [instructionResponse, setInstructionResponse] =
    useState<ExerciseInstructionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (catalogExerciseId === null) {
    return null;
  }

  const loadInstruction = async () => {
    const requestedCatalogExerciseId = catalogExerciseId;
    setIsLoading(true);
    setErrorMessage(null);

    const result = await fetchExerciseInstruction(requestedCatalogExerciseId);
    setIsLoading(false);
    setInstructionResponse(result.data);
    setErrorMessage(result.error?.message ?? null);
  };

  const handleToggle = () => {
    const nextIsExpanded = !isExpanded;
    onExpandedChange(nextIsExpanded);

    if (nextIsExpanded && !instructionResponse && !isLoading) {
      void loadInstruction();
    }
  };

  const instruction =
    instructionResponse?.instruction.catalog_exercise_id === catalogExerciseId
      ? instructionResponse.instruction
      : null;

  const renderInstructionContent = (isDesktop: boolean) => {
    if (isLoading) {
      return (
        <p className="text-sm text-slate-600" role="status">
          Loading instructions…
        </p>
      );
    }

    if (errorMessage) {
      return (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1" role="status">
          <p className="text-sm text-slate-600">{errorMessage}</p>
          <button
            type="button"
            onClick={() => void loadInstruction()}
            className="text-sm font-semibold text-emerald-800 transition hover:text-emerald-950 focus-visible:rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700"
          >
            Retry
          </button>
        </div>
      );
    }

    if (!instruction) {
      return null;
    }

    return (
      <div className={isDesktop ? "space-y-6" : "space-y-3"}>
        <p
          className={
            isDesktop
              ? "max-w-4xl text-base leading-7 text-slate-700"
              : "text-sm leading-5 text-slate-700"
          }
        >
          {instruction.overview}
        </p>
        <div
          className={
            isDesktop
              ? "grid gap-x-10 gap-y-6 lg:grid-cols-2"
              : "space-y-3"
          }
        >
          <InstructionSection heading="Setup" items={instruction.setup_steps} />
          <InstructionSection
            heading="How to do it"
            items={instruction.execution_steps}
          />
          <InstructionSection heading="Form cues" items={instruction.form_cues} />
          <InstructionSection
            heading="Common mistakes"
            items={instruction.common_mistakes}
          />
          <InstructionSection heading="Safety" items={instruction.safety_notes} />
        </div>
      </div>
    );
  };

  return (
    <>
      <button
        type="button"
        aria-expanded={isExpanded}
        aria-controls={`${mobilePanelId} ${desktopPanelId}`}
        onClick={handleToggle}
        className="shrink-0 rounded-full px-2 py-1 text-sm font-semibold text-emerald-800 transition hover:bg-emerald-50 hover:text-emerald-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700"
      >
        <span className="md:hidden">{isExpanded ? "Hide" : "How To"}</span>
        <span className="hidden md:inline">
          {isExpanded ? "Back to workout" : "How To"}
        </span>
      </button>

      {isExpanded ? (
        <>
          <div
            id={mobilePanelId}
            role="region"
            aria-label={`${exerciseName} instructions`}
            className="basis-full rounded-xl border border-emerald-100 bg-white/80 px-3 py-3 md:hidden"
          >
            {renderInstructionContent(false)}
          </div>
          <div
            id={desktopPanelId}
            role="region"
            aria-label={`${exerciseName} instructions`}
            className={`${styles.expandedSurface} hidden basis-full border-t border-emerald-100 pt-5 md:block`}
          >
            {renderInstructionContent(true)}
          </div>
        </>
      ) : null}
    </>
  );
}
