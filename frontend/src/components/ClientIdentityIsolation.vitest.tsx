import type { AnchorHTMLAttributes, ReactNode } from "react";
import { useState } from "react";

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppPageShell } from "@/components/AppPageShell";
import { PersonalFoodForm } from "@/components/PersonalFoodForm";
import { RecoveryCheckInCard } from "@/components/RecoveryCheckInCard";
import { WorkoutPageShell } from "@/components/WorkoutPageShell";
import { WorkoutPreviewExperience } from "@/components/WorkoutPreviewExperience";
import type { DailyDriverReadinessSummary } from "@/types/dailyDriver";
import type {
  RecoveryCheckInRecord,
  RecoveryCheckInResponse,
  SaveRecoveryCheckInResponse,
} from "@/types/recoveryCheckin";

const routerMocks = vi.hoisted(() => ({
  push: vi.fn(),
  refresh: vi.fn(),
  replace: vi.fn(),
}));

const recoveryApiMocks = vi.hoisted(() => ({
  fetch: vi.fn(),
  save: vi.fn(),
}));

const personalFoodApiMocks = vi.hoisted(() => ({
  create: vi.fn(),
  fetch: vi.fn(),
  update: vi.fn(),
}));

const workoutApiMocks = vi.hoisted(() => ({
  fetchCurrent: vi.fn(),
  fetchPreview: vi.fn(),
  unused: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & {
    children: ReactNode;
    href: string;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => routerMocks,
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/components/ExerciseInstructionDisclosure", () => ({
  ExerciseInstructionDisclosure: () => null,
}));
vi.mock("@/components/LinkCardDeck", () => ({
  LinkCardDeck: () => null,
}));
vi.mock("@/components/PrimaryNavigation", () => ({
  PrimaryNavigation: () => null,
}));
vi.mock("@/components/StatusPill", () => ({
  StatusPill: ({ label }: { label: string }) => <span>{label}</span>,
}));
vi.mock("@/components/TemporaryWorkoutLimitationCard", () => ({
  TemporaryWorkoutLimitationCard: () => null,
}));
vi.mock("@/components/TodayCard", () => ({
  TodayCard: ({
    children,
    title,
  }: {
    children: ReactNode;
    title: string;
  }) => (
    <section aria-label={title}>
      <h2>{title}</h2>
      {children}
    </section>
  ),
}));
vi.mock("@/components/UserSwitcher", () => ({
  UserSwitcher: () => null,
}));
vi.mock("@/components/WorkoutExerciseMemory", () => ({
  WorkoutExerciseMemory: () => null,
}));

vi.mock("@/lib/recoveryCheckinApi", () => ({
  fetchRecoveryCheckIn: recoveryApiMocks.fetch,
  saveRecoveryCheckIn: recoveryApiMocks.save,
}));

vi.mock("@/lib/personalFoodApi", () => ({
  createPersonalFood: personalFoodApiMocks.create,
  fetchPersonalFood: personalFoodApiMocks.fetch,
  updatePersonalFood: personalFoodApiMocks.update,
}));

vi.mock("@/lib/todayWorkoutApi", () => ({
  applyWorkoutSubstitution: workoutApiMocks.unused,
  buildTodayWorkoutHref: () => "/today/workout",
  completeWorkout: workoutApiMocks.unused,
  deleteWorkoutActualSet: workoutApiMocks.unused,
  fetchWorkoutCurrent: workoutApiMocks.fetchCurrent,
  fetchWorkoutPlannedVsActual: workoutApiMocks.unused,
  fetchWorkoutPreview: workoutApiMocks.fetchPreview,
  fetchWorkoutProgressionDecisions: workoutApiMocks.unused,
  fetchWorkoutProgressionHistory: workoutApiMocks.unused,
  fetchWorkoutSubstitutionCandidates: workoutApiMocks.unused,
  logWorkoutActualSet: workoutApiMocks.unused,
  selectWorkoutPreview: workoutApiMocks.unused,
  startWorkoutPlan: workoutApiMocks.unused,
  updateWorkoutActualSet: workoutApiMocks.unused,
}));

interface Deferred<T> {
  promise: Promise<T>;
  reject: (reason?: unknown) => void;
  resolve: (value: T) => void;
}

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, reject, resolve };
}

function recoveryRecord(
  userId: number,
  sleepHours: number,
  checkinDate = "2099-01-01",
): RecoveryCheckInRecord {
  return {
    id: userId,
    user_id: userId,
    checkin_date: checkinDate,
    body_weight: null,
    sleep_hours: sleepHours,
    sleep_quality: null,
    energy_level: 5,
    soreness_level: 3,
    stress_level: null,
    training_motivation: null,
    pain_concern: null,
    pain_area: null,
    mood: null,
    notes: null,
    created_at: null,
  };
}

function recoveryResponse(
  checkin: RecoveryCheckInRecord | null,
): RecoveryCheckInResponse {
  return {
    success: true,
    checkin,
    recent_checkins: checkin ? [checkin] : [],
  };
}

const readiness: DailyDriverReadinessSummary = {
  status: "ready",
  headline: "Ready",
  reason: "Test",
  confidence: "high",
  score: 80,
};

function RecoveryWorkspace({ userId }: { userId: number }) {
  return (
    <AppPageShell
      title="Recovery"
      dateLabel="January 1, 2099"
      userId={userId}
    >
      <RecoveryCheckInCard
        userId={userId}
        targetDate="2099-01-01"
        readiness={readiness}
      />
    </AppPageShell>
  );
}

function PersonalFoodWorkspace({ userId }: { userId: number }) {
  return (
    <AppPageShell
      title="Add food"
      dateLabel="January 1, 2099"
      userId={userId}
    >
      <PersonalFoodForm
        mode="create"
        userId={userId}
        targetDate="2099-01-01"
      />
    </AppPageShell>
  );
}

function WorkoutWorkspace({ userId }: { userId: number }) {
  const requestedDate = "2099-01-01";
  return (
    <WorkoutPageShell
      activePage="today"
      userId={userId}
      date={requestedDate}
      todayDate={requestedDate}
      primaryNavigationDate={requestedDate}
    >
      <WorkoutPreviewExperience
        key={`${userId}:${requestedDate}`}
        userId={userId}
        requestedDate={requestedDate}
      />
    </WorkoutPageShell>
  );
}

async function resolveDeferred<T>(pending: Deferred<T>, value: T) {
  await act(async () => {
    pending.resolve(value);
    await pending.promise;
  });
}

beforeEach(() => {
  routerMocks.push.mockReset();
  routerMocks.refresh.mockReset();
  routerMocks.replace.mockReset();

  recoveryApiMocks.fetch.mockReset();
  recoveryApiMocks.save.mockReset();
  personalFoodApiMocks.create.mockReset();
  personalFoodApiMocks.fetch.mockReset();
  personalFoodApiMocks.update.mockReset();
  workoutApiMocks.fetchCurrent.mockReset();
  workoutApiMocks.fetchPreview.mockReset();
  workoutApiMocks.unused.mockReset();

  recoveryApiMocks.fetch.mockResolvedValue(recoveryResponse(null));
  recoveryApiMocks.save.mockResolvedValue({
    success: true,
    message: "Check-in saved.",
    checkin_id: 1,
  } satisfies SaveRecoveryCheckInResponse);
  personalFoodApiMocks.create.mockResolvedValue({});
  personalFoodApiMocks.fetch.mockResolvedValue({});
  personalFoodApiMocks.update.mockResolvedValue({});
  workoutApiMocks.fetchCurrent.mockResolvedValue({ data: null, error: null });
  workoutApiMocks.fetchPreview.mockResolvedValue({
    data: null,
    error: { message: "Preview unavailable." },
  });
});

describe("shared user-owned client boundary", () => {
  it("remounts transient state for a new user and preserves it for the same user", () => {
    function DraftProbe() {
      const [draft, setDraft] = useState("");
      return (
        <input
          aria-label="Scoped draft"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
      );
    }

    const { rerender } = render(
      <AppPageShell title="Today" dateLabel="Today" userId={1}>
        <DraftProbe />
      </AppPageShell>,
    );
    const draft = screen.getByLabelText<HTMLInputElement>("Scoped draft");
    fireEvent.change(draft, { target: { value: "A draft" } });
    expect(draft.value).toBe("A draft");

    rerender(
      <AppPageShell title="Today" dateLabel="Today" userId={1}>
        <DraftProbe />
      </AppPageShell>,
    );
    expect(screen.getByLabelText<HTMLInputElement>("Scoped draft").value).toBe(
      "A draft",
    );

    rerender(
      <AppPageShell title="Today" dateLabel="Today" userId={2}>
        <DraftProbe />
      </AppPageShell>,
    );
    expect(screen.getByLabelText<HTMLInputElement>("Scoped draft").value).toBe(
      "",
    );
  });
});

describe("RecoveryCheckInCard identity isolation", () => {
  it("ignores A's delayed load after B becomes active", async () => {
    const aLoad = deferred<RecoveryCheckInResponse>();
    recoveryApiMocks.fetch.mockImplementation((userId: number) =>
      userId === 1
        ? aLoad.promise
        : Promise.resolve(recoveryResponse(recoveryRecord(2, 7.5))),
    );

    const { rerender } = render(<RecoveryWorkspace userId={1} />);
    rerender(<RecoveryWorkspace userId={2} />);

    await waitFor(() => {
      expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe(
        "7.5",
      );
    });
    await resolveDeferred(aLoad, recoveryResponse(recoveryRecord(1, 4)));

    expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe("7.5");
    expect(screen.queryByText("Sleep 4h")).toBeNull();
  });

  it("shows B's empty defaults when B has no check-in", async () => {
    recoveryApiMocks.fetch.mockImplementation((userId: number) =>
      Promise.resolve(
        userId === 1
          ? recoveryResponse(recoveryRecord(1, 8))
          : recoveryResponse(null),
      ),
    );

    const { rerender } = render(<RecoveryWorkspace userId={1} />);
    await waitFor(() => {
      expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe("8");
    });

    rerender(<RecoveryWorkspace userId={2} />);
    expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe("");
    await waitFor(() => {
      expect(
        screen.getByRole<HTMLButtonElement>("button", {
          name: "Save check-in",
        }).disabled,
      ).toBe(false);
    });
    expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe("");
  });

  it("clears A's draft before B can save and binds B's payload to B", async () => {
    const bLoad = deferred<RecoveryCheckInResponse>();
    recoveryApiMocks.fetch.mockImplementation((userId: number) =>
      userId === 1 ? Promise.resolve(recoveryResponse(null)) : bLoad.promise,
    );

    const { rerender } = render(<RecoveryWorkspace userId={1} />);
    await waitFor(() => {
      expect(
        screen.getByRole<HTMLButtonElement>("button", {
          name: "Save check-in",
        }).disabled,
      ).toBe(false);
    });
    fireEvent.change(screen.getByLabelText("Sleep"), {
      target: { value: "6" },
    });

    rerender(<RecoveryWorkspace userId={2} />);
    expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe("");
    expect(
      screen.getByRole<HTMLButtonElement>("button", {
        name: "Save check-in",
      }).disabled,
    ).toBe(true);

    await resolveDeferred(bLoad, recoveryResponse(null));
    fireEvent.change(screen.getByLabelText("Sleep"), {
      target: { value: "7" },
    });
    fireEvent.click(
      screen.getByRole("button", {
        name: "Save check-in",
      }),
    );

    await waitFor(() => {
      expect(recoveryApiMocks.save).toHaveBeenCalledTimes(1);
    });
    expect(recoveryApiMocks.save.mock.calls[0]?.[0]).toMatchObject({
      user_id: 2,
      sleep_hours: 7,
    });
  });

  it("does not show an A save result after switching to B", async () => {
    const aSave = deferred<SaveRecoveryCheckInResponse>();
    recoveryApiMocks.save.mockImplementation(() => aSave.promise);

    const { rerender } = render(<RecoveryWorkspace userId={1} />);
    await waitFor(() => {
      expect(
        screen.getByRole<HTMLButtonElement>("button", {
          name: "Save check-in",
        }).disabled,
      ).toBe(false);
    });
    fireEvent.change(screen.getByLabelText("Sleep"), {
      target: { value: "6" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save check-in" }));
    await waitFor(() => {
      expect(recoveryApiMocks.save).toHaveBeenCalledTimes(1);
    });

    rerender(<RecoveryWorkspace userId={2} />);
    await resolveDeferred(aSave, {
      success: true,
      message: "A saved",
      checkin_id: 1,
    });

    expect(screen.queryByText("A saved")).toBeNull();
    expect(
      recoveryApiMocks.fetch.mock.calls.filter(([userId]) => userId === 1),
    ).toHaveLength(1);
  });

  it("accepts only the latest A request after rapid A to B to A switching", async () => {
    const aFirstLoad = deferred<RecoveryCheckInResponse>();
    const bLoad = deferred<RecoveryCheckInResponse>();
    let aRequestCount = 0;
    recoveryApiMocks.fetch.mockImplementation((userId: number) => {
      if (userId === 2) {
        return bLoad.promise;
      }
      aRequestCount += 1;
      return aRequestCount === 1
        ? aFirstLoad.promise
        : Promise.resolve(recoveryResponse(recoveryRecord(1, 9)));
    });

    const { rerender } = render(<RecoveryWorkspace userId={1} />);
    rerender(<RecoveryWorkspace userId={2} />);
    rerender(<RecoveryWorkspace userId={1} />);
    await waitFor(() => {
      expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe("9");
    });

    await resolveDeferred(aFirstLoad, recoveryResponse(recoveryRecord(1, 3)));
    await resolveDeferred(bLoad, recoveryResponse(recoveryRecord(2, 5)));
    expect(screen.getByLabelText<HTMLInputElement>("Sleep").value).toBe("9");
  });
});

describe("PersonalFoodForm identity isolation", () => {
  it("clears A's draft, prevents late A navigation, and submits only B's values", async () => {
    const aSave = deferred<unknown>();
    personalFoodApiMocks.create
      .mockImplementationOnce(() => aSave.promise)
      .mockResolvedValueOnce({});

    const { rerender } = render(<PersonalFoodWorkspace userId={1} />);
    fireEvent.change(screen.getByLabelText("Food name"), {
      target: { value: "A private food" },
    });
    fireEvent.change(screen.getByLabelText("Serving weight in grams"), {
      target: { value: "100" },
    });
    fireEvent.change(screen.getByLabelText("Calories"), {
      target: { value: "250" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add food" }));
    await waitFor(() => {
      expect(personalFoodApiMocks.create).toHaveBeenCalledTimes(1);
    });

    rerender(<PersonalFoodWorkspace userId={2} />);
    expect(screen.getByLabelText<HTMLInputElement>("Food name").value).toBe("");
    expect(screen.getByLabelText<HTMLInputElement>("Calories").value).toBe("");
    await resolveDeferred(aSave, {});
    expect(routerMocks.push).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Food name"), {
      target: { value: "B food" },
    });
    fireEvent.change(screen.getByLabelText("Serving weight in grams"), {
      target: { value: "50" },
    });
    fireEvent.change(screen.getByLabelText("Calories"), {
      target: { value: "125" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add food" }));

    await waitFor(() => {
      expect(personalFoodApiMocks.create).toHaveBeenCalledTimes(2);
      expect(routerMocks.push).toHaveBeenCalledWith(
        "/food?user_id=2&date=2099-01-01&view=library",
      );
    });
    expect(personalFoodApiMocks.create.mock.calls[1]?.[0]).toMatchObject({
      user_id: 2,
      display_name: "B food",
      serving_grams: 50,
      calories: 125,
    });
  });
});

describe("Today workout preview identity isolation", () => {
  it("resets same-date preferences and ignores A's late preview result under B", async () => {
    const aPreview = deferred<{
      data: null;
      error: { message: string };
    }>();
    const bPreview = deferred<{
      data: null;
      error: { message: string };
    }>();
    workoutApiMocks.fetchPreview.mockImplementation(
      ({ userId }: { userId: number }) =>
        userId === 1 ? aPreview.promise : bPreview.promise,
    );

    const { rerender } = render(<WorkoutWorkspace userId={1} />);
    await waitFor(() => {
      expect(workoutApiMocks.fetchPreview).toHaveBeenCalled();
    });
    fireEvent.click(screen.getByRole("button", { name: "Extended" }));
    expect(
      screen
        .getByRole("button", { name: "Extended" })
        .getAttribute("aria-pressed"),
    ).toBe("true");

    rerender(<WorkoutWorkspace userId={2} />);
    expect(
      screen
        .getByRole("button", { name: "Standard" })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      screen
        .getByRole("button", { name: "Extended" })
        .getAttribute("aria-pressed"),
    ).toBe("false");

    await resolveDeferred(aPreview, {
      data: null,
      error: { message: "A preview must stay private" },
    });
    expect(screen.queryByText("A preview must stay private")).toBeNull();

    await resolveDeferred(bPreview, {
      data: null,
      error: { message: "B preview unavailable" },
    });
    await waitFor(() => {
      expect(screen.getByText("B preview unavailable")).not.toBeNull();
    });
    expect(
      workoutApiMocks.fetchPreview.mock.calls.some(
        ([request]) => request.userId === 2,
      ),
    ).toBe(true);
  });
});
