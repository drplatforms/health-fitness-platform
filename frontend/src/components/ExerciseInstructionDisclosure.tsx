"use client";

import { useEffect, useId, useRef, useState } from "react";
import Image from "next/image";

import styles from "@/components/ExerciseInstructionDisclosure.module.css";
import { fetchExerciseInstruction } from "@/lib/exerciseInstructionApi";
import { selectCurrentExerciseInstructionResponse } from "@/lib/exerciseVisualMedia";
import {
  exerciseInstructionAffordance,
  saveWorkoutExerciseProfile,
} from "@/lib/workoutExerciseProfileApi";
import type {
  ExerciseInstructionResponse,
  ExerciseVisualMediaItem,
} from "@/types/exerciseInstruction";
import type {
  WorkoutExerciseFamiliarity,
  WorkoutExercisePreference,
  WorkoutExerciseProfile,
} from "@/types/workoutExerciseProfile";

interface ExerciseInstructionDisclosureProps {
  catalogExerciseId: number | null;
  exerciseName: string;
  isExpanded: boolean;
  userId: number;
  profile: WorkoutExerciseProfile | null | undefined;
  canEditProfile: boolean;
  onExpandedChange: (isExpanded: boolean) => void;
  onProfileChanged: (profile: WorkoutExerciseProfile | null) => void;
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
      <h3 className="text-sm font-semibold text-text-primary">{heading}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm leading-5 text-text-body marker:text-accent-text">
        {items.map((item, index) => (
          <li key={`${heading}-${index + 1}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function AnimatedVisualMedia({ asset }: { asset: ExerciseVisualMediaItem }) {
  const [hasFailed, setHasFailed] = useState(false);

  if (hasFailed) {
    return (
      <p className="px-2 pb-2 pt-1 text-xs text-text-secondary" role="status">
        Animated guide unavailable. Follow the written instructions below.
      </p>
    );
  }

  return (
    <>
      <div className={styles.animatedVisualMediaFrame}>
        {/* Provider URLs are normalized by the backend; an img preserves GIF animation. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={asset.url}
          alt={asset.alt_text}
          className={styles.animatedVisualMedia}
          onError={() => setHasFailed(true)}
        />
      </div>
      {asset.attribution ? (
        <figcaption className="px-2 pb-2 pt-1 text-xs font-medium text-text-secondary">
          {asset.attribution}
        </figcaption>
      ) : null}
    </>
  );
}

function VisualGuide({ media }: { media: ExerciseVisualMediaItem[] }) {
  if (!media.length) {
    return null;
  }

  return (
    <section className={styles.visualGuide} aria-label="Visual guide">
      <h3 className="text-sm font-semibold text-text-primary">Visual guide</h3>
      <div className={styles.visualGuideGrid}>
        {media.map((asset) => (
          <figure key={asset.media_key} className={styles.visualGuideFigure}>
            {asset.media_type === "animated_image" ? (
              <AnimatedVisualMedia asset={asset} />
            ) : (
              <>
                <div className={styles.visualGuideImageFrame}>
                  <Image
                    src={asset.url}
                    alt={asset.alt_text}
                    fill
                    sizes="(max-width: 640px) 100vw, 50vw"
                    className={styles.visualGuideImage}
                  />
                </div>
                {asset.caption ? (
                  <figcaption className="px-2 pb-2 pt-1 text-xs font-medium text-text-secondary">
                    {asset.caption}
                  </figcaption>
                ) : null}
              </>
            )}
          </figure>
        ))}
      </div>
    </section>
  );
}

export function ExerciseInstructionDisclosure({
  catalogExerciseId,
  exerciseName,
  isExpanded,
  userId,
  profile,
  canEditProfile,
  onExpandedChange,
  onProfileChanged,
}: ExerciseInstructionDisclosureProps) {
  const disclosureId = useId();
  const mobilePanelId = `${disclosureId}-mobile`;
  const desktopPanelId = `${disclosureId}-desktop`;
  const [instructionResponse, setInstructionResponse] =
    useState<ExerciseInstructionResponse | null>(null);
  const requestVersionRef = useRef(0);
  const [loadingCatalogExerciseId, setLoadingCatalogExerciseId] = useState<
    number | null
  >(null);
  const [instructionError, setInstructionError] = useState<{
    catalogExerciseId: number;
    message: string;
  } | null>(null);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileErrorMessage, setProfileErrorMessage] = useState<string | null>(
    null,
  );

  useEffect(() => {
    requestVersionRef.current += 1;
  }, [catalogExerciseId]);

  if (catalogExerciseId === null) {
    return null;
  }

  const loadInstruction = async () => {
    const requestedCatalogExerciseId = catalogExerciseId;
    const requestVersion = requestVersionRef.current + 1;
    requestVersionRef.current = requestVersion;
    setLoadingCatalogExerciseId(requestedCatalogExerciseId);
    setInstructionError(null);

    const result = await fetchExerciseInstruction(requestedCatalogExerciseId);
    if (requestVersion !== requestVersionRef.current) {
      return;
    }
    setLoadingCatalogExerciseId(null);
    setInstructionResponse(result.data);
    setInstructionError(
      result.error
        ? {
            catalogExerciseId: requestedCatalogExerciseId,
            message: result.error.message,
          }
        : null,
    );
  };

  const handleToggle = () => {
    const nextIsExpanded = !isExpanded;
    onExpandedChange(nextIsExpanded);

    if (nextIsExpanded && !instruction && !isLoading) {
      void loadInstruction();
    }
  };

  const currentInstructionResponse = selectCurrentExerciseInstructionResponse(
    instructionResponse,
    catalogExerciseId,
  );
  const instruction = currentInstructionResponse?.instruction ?? null;
  const isLoading = loadingCatalogExerciseId === catalogExerciseId;
  const errorMessage =
    instructionError?.catalogExerciseId === catalogExerciseId
      ? instructionError.message
      : null;
  const visualMedia = currentInstructionResponse?.visual_media ?? [];
  const showMediaBeforeOverview =
    profile?.familiarity_state === "unfamiliar" ||
    profile?.familiarity_state === "learning";
  const instructionAffordance = exerciseInstructionAffordance(
    profile?.familiarity_state,
  );

  const handleProfileChange = async (
    dimension: "familiarity" | "preference",
    rawValue: string,
  ) => {
    const familiarityState =
      dimension === "familiarity"
        ? (rawValue || null) as WorkoutExerciseFamiliarity | null
        : (profile?.familiarity_state ?? null);
    const preferenceState =
      dimension === "preference"
        ? (rawValue || null) as WorkoutExercisePreference | null
        : (profile?.preference_state ?? null);

    setIsSavingProfile(true);
    setProfileErrorMessage(null);
    const result = await saveWorkoutExerciseProfile(
      userId,
      catalogExerciseId,
      familiarityState,
      preferenceState,
    );
    setIsSavingProfile(false);
    if (result.error || result.data === null) {
      setProfileErrorMessage(
        result.error?.message ?? "Unable to save this exercise profile.",
      );
      return;
    }
    onProfileChanged(result.data.profile);
  };

  const renderProfileControls = () => {
    if (!canEditProfile || profile === undefined) {
      return null;
    }
    return (
      <section className="space-y-3 border-t border-border-subtle pt-3">
        <div className="grid gap-2 sm:grid-cols-2">
          <label className="space-y-1 text-xs font-semibold text-text-body">
            <span>Familiarity</span>
            <select
              aria-label={`${exerciseName} familiarity`}
              value={profile?.familiarity_state ?? ""}
              disabled={isSavingProfile}
              onChange={(event) =>
                void handleProfileChange("familiarity", event.target.value)
              }
              className="min-h-11 w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none focus:border-focus-subtle disabled:opacity-60"
            >
              <option value="">Clear</option>
              <option value="unfamiliar">Unfamiliar</option>
              <option value="learning">Learning</option>
              <option value="familiar">Familiar</option>
            </select>
          </label>
          <label className="space-y-1 text-xs font-semibold text-text-body">
            <span>Preference</span>
            <select
              aria-label={`${exerciseName} preference`}
              value={profile?.preference_state ?? ""}
              disabled={isSavingProfile}
              onChange={(event) =>
                void handleProfileChange("preference", event.target.value)
              }
              className="min-h-11 w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none focus:border-focus-subtle disabled:opacity-60"
            >
              <option value="favorite">Favorite</option>
              <option value="">Neutral</option>
              <option value="disliked">Disliked</option>
            </select>
          </label>
        </div>
        {isSavingProfile ? (
          <p className="text-xs text-text-muted" role="status">
            Saving profile…
          </p>
        ) : null}
        {profileErrorMessage ? (
          <p className="text-xs font-medium text-danger-action" role="status">
            {profileErrorMessage}
          </p>
        ) : null}
      </section>
    );
  };

  const renderInstructionContent = (isDesktop: boolean) => {
    if (isLoading) {
      return (
        <p className="text-sm text-text-secondary" role="status">
          Loading instructions…
        </p>
      );
    }

    if (errorMessage) {
      return (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1" role="status">
          <p className="text-sm text-text-secondary">{errorMessage}</p>
          <button
            type="button"
            onClick={() => void loadInstruction()}
            className="text-sm font-semibold text-accent-text transition hover:text-accent-text-hover focus-visible:rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
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
        {renderProfileControls()}
        {showMediaBeforeOverview ? <VisualGuide media={visualMedia} /> : null}
        <p
          className={
            isDesktop
              ? "max-w-4xl text-base leading-7 text-text-body"
              : "text-sm leading-5 text-text-body"
          }
        >
          {instruction.overview}
        </p>
        {!showMediaBeforeOverview ? <VisualGuide media={visualMedia} /> : null}
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
        className="shrink-0 rounded-full px-2 py-1 text-sm font-semibold text-accent-text transition hover:bg-surface-highlighted hover:text-accent-text-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
      >
        <span className="md:hidden">
          {isExpanded ? "Hide" : instructionAffordance}
        </span>
        <span className="hidden md:inline">
          {isExpanded ? "Back to workout" : instructionAffordance}
        </span>
      </button>

      {isExpanded ? (
        <>
          <div
            id={mobilePanelId}
            role="region"
            aria-label={`${exerciseName} instructions`}
            className="basis-full rounded-xl border border-positive-surface bg-surface/80 px-3 py-3 md:hidden"
          >
            {renderInstructionContent(false)}
          </div>
          <div
            id={desktopPanelId}
            role="region"
            aria-label={`${exerciseName} instructions`}
            className={`${styles.expandedSurface} hidden basis-full border-t border-positive-surface pt-5 md:block`}
          >
            {renderInstructionContent(true)}
          </div>
        </>
      ) : null}
    </>
  );
}
