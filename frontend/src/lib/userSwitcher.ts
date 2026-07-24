export interface SwitchableUser {
  id: number;
  label: string;
  kind: "real" | "qa";
}

export const SWITCHABLE_USERS: SwitchableUser[] = [
  { id: 1, label: "Dustin", kind: "real" },
  { id: 2, label: "Danielle", kind: "real" },
  { id: 101, label: "QA 101", kind: "qa" },
  { id: 102, label: "QA 102", kind: "qa" },
  { id: 103, label: "QA 103", kind: "qa" },
  { id: 104, label: "QA 104", kind: "qa" },
  { id: 105, label: "QA 105", kind: "qa" },
  { id: 106, label: "QA106 — Consistent Strength", kind: "qa" },
  { id: 107, label: "QA107 — Interrupted Progress", kind: "qa" },
  { id: 108, label: "QA108 — Mixed Modality", kind: "qa" },
];

export function getSwitchableUserLabel(userId: number): string {
  return SWITCHABLE_USERS.find((user) => user.id === userId)?.label ?? `User ${userId}`;
}

export function isQaSwitcherUser(userId: number): boolean {
  return (
    SWITCHABLE_USERS.find((user) => user.id === userId)?.kind === "qa"
  );
}
