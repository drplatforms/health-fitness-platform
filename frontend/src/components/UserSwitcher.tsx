"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

import { SWITCHABLE_USERS } from "@/lib/userSwitcher";

interface UserSwitcherProps {
  currentUserId: number;
  showLabel?: boolean;
  className?: string;
  selectClassName?: string;
}

export function UserSwitcher({
  currentUserId,
  showLabel = true,
  className = "",
  selectClassName = "",
}: UserSwitcherProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  function handleChange(nextUserId: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("user_id", nextUserId);

    startTransition(() => {
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    });
  }

  return (
    <label
      className={`flex ${showLabel ? "flex-col gap-2 sm:items-end" : "items-center gap-2"} ${className}`}
    >
      {showLabel ? (
        <span className="type-field-label uppercase tracking-[0.16em] text-text-muted">
          User
        </span>
      ) : null}
      <select
        value={String(currentUserId)}
        onChange={(event) => handleChange(event.target.value)}
        disabled={isPending}
        className={`min-w-[140px] rounded-2xl border border-border bg-surface px-3 py-3 text-sm font-medium text-text-primary outline-none transition focus:border-focus disabled:cursor-not-allowed disabled:opacity-70 sm:min-w-[180px] sm:px-4 ${selectClassName}`}
      >
        {SWITCHABLE_USERS.map((user) => (
          <option key={user.id} value={user.id}>
            {user.label}
          </option>
        ))}
      </select>
    </label>
  );
}
