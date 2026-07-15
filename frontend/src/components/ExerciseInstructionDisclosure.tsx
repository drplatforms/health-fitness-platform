"use client";

import { useId, useState } from "react";

import { fetchExerciseInstruction } from "@/lib/exerciseInstructionApi";
import { ExerciseInstructionResponse } from "@/types/exerciseInstruction";

interface ExerciseInstructionDisclosureProps {
  catalogExerciseId: number | null;
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
}: ExerciseInstructionDisclosureProps) {
  const panelId = useId();
  const [isExpanded, setIsExpanded] = useState(false);
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
    if (isExpanded) {
      setIsExpanded(false);
      return;
    }

    setIsExpanded(true);
    if (!instructionResponse && !isLoading) {
      void loadInstruction();
    }
  };

  const instruction =
    instructionResponse?.instruction.catalog_exercise_id === catalogExerciseId
      ? instructionResponse.instruction
      : null;

  return (
    <>
      <button
        type="button"
        aria-expanded={isExpanded}
        aria-controls={panelId}
        onClick={handleToggle}
        className="shrink-0 text-sm font-semibold text-emerald-800 transition hover:text-emerald-950 focus-visible:rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700"
      >
        {isExpanded ? "Hide" : "How to"}
      </button>

      {isExpanded ? (
        <div
          id={panelId}
          className="basis-full rounded-xl border border-emerald-100 bg-white/80 px-3 py-3"
        >
          {isLoading ? (
            <p className="text-sm text-slate-600" role="status">
              Loading instructions…
            </p>
          ) : errorMessage ? (
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1" role="status">
              <p className="text-sm text-slate-600">{errorMessage}</p>
              <button
                type="button"
                onClick={() => void loadInstruction()}
                className="text-sm font-semibold text-emerald-800 transition hover:text-emerald-950"
              >
                Retry
              </button>
            </div>
          ) : instruction ? (
            <div className="space-y-3">
              <p className="text-sm leading-5 text-slate-700">
                {instruction.overview}
              </p>
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
          ) : null}
        </div>
      ) : null}
    </>
  );
}
