"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

import { SWITCHABLE_USERS } from "@/lib/userSwitcher";

interface UserSwitcherProps {
  currentUserId: number;
}

export function UserSwitcher({ currentUserId }: UserSwitcherProps) {
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
    <label className="flex flex-col gap-2 sm:items-end">
      <span className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
        User
      </span>
      <select
        value={String(currentUserId)}
        onChange={(event) => handleChange(event.target.value)}
        disabled={isPending}
        className="min-w-[180px] rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 outline-none transition focus:border-emerald-500 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {SWITCHABLE_USERS.map((user) => (
          <option key={user.id} value={user.id}>
            {user.kind === "qa" ? `${user.label} (Test)` : user.label}
          </option>
        ))}
      </select>
    </label>
  );
}
