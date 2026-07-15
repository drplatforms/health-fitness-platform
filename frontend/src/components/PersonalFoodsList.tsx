"use client";

import Link from "next/link";
import { useDeferredValue, useEffect, useState } from "react";

import {
  archivePersonalFood,
  fetchPersonalFoods,
  restorePersonalFood,
} from "@/lib/personalFoodApi";
import { PersonalFood } from "@/types/personalFood";

interface PersonalFoodsListProps {
  userId: number;
  targetDate?: string;
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function macroLine(food: PersonalFood): string {
  const revision = food.current_revision;
  const parts = [
    revision.calories_per_100g === null
      ? null
      : `${formatNumber(revision.calories_per_100g)} cal`,
    revision.protein_g_per_100g === null
      ? null
      : `${formatNumber(revision.protein_g_per_100g)}g protein`,
    revision.carbs_g_per_100g === null
      ? null
      : `${formatNumber(revision.carbs_g_per_100g)}g carbs`,
    revision.fat_g_per_100g === null
      ? null
      : `${formatNumber(revision.fat_g_per_100g)}g fat`,
  ].filter((value): value is string => value !== null);
  return parts.length ? `${parts.join(" · ")} per 100g` : "Nutrition details limited";
}

function withContext(path: string, userId: number, targetDate?: string) {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (targetDate) {
    params.set("date", targetDate);
  }
  return `${path}?${params.toString()}`;
}

export function PersonalFoodsList({
  userId,
  targetDate,
}: PersonalFoodsListProps) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query.trim());
  const [showArchived, setShowArchived] = useState(false);
  const [foods, setFoods] = useState<PersonalFood[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingFoodId, setPendingFoodId] = useState<number | null>(null);
  const [confirmingArchiveId, setConfirmingArchiveId] = useState<number | null>(
    null,
  );

  useEffect(() => {
    let isActive = true;
    const timeoutId = window.setTimeout(() => {
      setIsLoading(true);
      setError(null);
      void fetchPersonalFoods({
        userId,
        query: deferredQuery,
        includeArchived: showArchived,
      })
        .then((response) => {
          if (!isActive) {
            return;
          }
          setFoods(
            response.results.filter((food) =>
              showArchived ? !food.active : food.active,
            ),
          );
        })
        .catch((loadError) => {
          if (isActive) {
            setFoods([]);
            setError(
              loadError instanceof Error
                ? loadError.message
                : "Unable to load personal foods.",
            );
          }
        })
        .finally(() => {
          if (isActive) {
            setIsLoading(false);
          }
        });
    }, deferredQuery ? 200 : 0);

    return () => {
      isActive = false;
      window.clearTimeout(timeoutId);
    };
  }, [deferredQuery, showArchived, userId]);

  async function archive(food: PersonalFood) {
    if (confirmingArchiveId !== food.id) {
      setConfirmingArchiveId(food.id);
      setError(null);
      return;
    }
    setPendingFoodId(food.id);
    setError(null);
    try {
      await archivePersonalFood(userId, food.id);
      setFoods((current) => current.filter((item) => item.id !== food.id));
      setConfirmingArchiveId(null);
    } catch (archiveError) {
      setError(
        archiveError instanceof Error
          ? archiveError.message
          : "Unable to archive this food.",
      );
    } finally {
      setPendingFoodId(null);
    }
  }

  async function restore(food: PersonalFood) {
    setPendingFoodId(food.id);
    setError(null);
    try {
      await restorePersonalFood(userId, food.id);
      setFoods((current) => current.filter((item) => item.id !== food.id));
    } catch (restoreError) {
      setError(
        restoreError instanceof Error
          ? restoreError.message
          : "Unable to restore this food.",
      );
    } finally {
      setPendingFoodId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
            My foods
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Foods you can find in the normal food search.
          </p>
        </div>
        <Link
          href={withContext("/personal-foods/new", userId, targetDate)}
          className="inline-flex items-center justify-center rounded-2xl bg-emerald-900 px-4 py-2.5 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800"
        >
          Add food
        </Link>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={showArchived ? "Search archived foods..." : "Search my foods..."}
          aria-label="Search personal foods"
          className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-950 outline-none transition focus:border-emerald-500"
        />
        <button
          type="button"
          onClick={() => {
            setShowArchived((current) => !current);
            setConfirmingArchiveId(null);
          }}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-emerald-300"
        >
          {showArchived ? "Show active" : "Archived"}
        </button>
      </div>

      {error ? (
        <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {error}
        </p>
      ) : null}
      {isLoading ? (
        <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Loading foods...
        </p>
      ) : null}
      {!isLoading && !error && foods.length === 0 ? (
        <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          {showArchived
            ? "No archived foods found."
            : query.trim()
              ? "No personal foods match this search."
              : "No personal foods yet."}
        </p>
      ) : null}

      {!isLoading && foods.length > 0 ? (
        <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-white">
          {foods.map((food) => (
            <div
              key={food.id}
              className="grid gap-2 px-4 py-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
            >
              <div className="min-w-0">
                <p className="font-semibold text-slate-950">{food.display_name}</p>
                {food.brand_name ? (
                  <p className="text-sm text-slate-600">{food.brand_name}</p>
                ) : null}
                {!showArchived ? (
                  <p className="mt-1 text-xs leading-5 text-slate-600">
                    {food.current_revision.serving_grams !== null
                      ? `${food.current_revision.serving_name || "serving"} · ${formatNumber(food.current_revision.serving_grams)}g · `
                      : ""}
                    {macroLine(food)}
                  </p>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-3 text-sm font-semibold">
                {showArchived ? (
                  <button
                    type="button"
                    disabled={pendingFoodId === food.id}
                    onClick={() => void restore(food)}
                    className="text-emerald-800 transition hover:text-emerald-950 disabled:opacity-60"
                  >
                    {pendingFoodId === food.id ? "Restoring..." : "Restore"}
                  </button>
                ) : (
                  <>
                    <Link
                      href={withContext(`/personal-foods/${food.id}`, userId, targetDate)}
                      className="text-emerald-800 transition hover:text-emerald-950"
                    >
                      Edit
                    </Link>
                    <button
                      type="button"
                      disabled={pendingFoodId === food.id}
                      onClick={() => void archive(food)}
                      className={
                        confirmingArchiveId === food.id
                          ? "text-rose-700 transition hover:text-rose-900 disabled:opacity-60"
                          : "text-slate-500 transition hover:text-rose-700 disabled:opacity-60"
                      }
                    >
                      {pendingFoodId === food.id
                        ? "Archiving..."
                        : confirmingArchiveId === food.id
                          ? "Confirm archive"
                          : "Archive"}
                    </button>
                    {confirmingArchiveId === food.id ? (
                      <button
                        type="button"
                        onClick={() => setConfirmingArchiveId(null)}
                        className="text-slate-500 transition hover:text-slate-800"
                      >
                        Cancel
                      </button>
                    ) : null}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
