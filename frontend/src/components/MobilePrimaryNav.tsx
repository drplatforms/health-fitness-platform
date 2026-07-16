"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

interface MobilePrimaryNavProps {
  userId: number;
  date?: string;
}

function buildHref(
  pathname: string,
  userId: number,
  date?: string,
  hash?: string,
): string {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (date) {
    params.set("date", date);
  }

  return `${pathname}?${params.toString()}${hash ?? ""}`;
}

export function MobilePrimaryNav({ userId, date }: MobilePrimaryNavProps) {
  const pathname = usePathname();
  const [hash, setHash] = useState("");

  useEffect(() => {
    const updateHash = () => setHash(window.location.hash);
    updateHash();
    window.addEventListener("hashchange", updateHash);
    window.addEventListener("popstate", updateHash);
    return () => {
      window.removeEventListener("hashchange", updateHash);
      window.removeEventListener("popstate", updateHash);
    };
  }, [pathname]);

  const activeDestination = pathname.startsWith("/personal-foods")
    ? "food"
    : pathname === "/today/workout"
      ? "workout"
      : hash === "#food-workspace"
        ? "food"
        : hash === "#recovery"
          ? "recovery"
          : "today";
  const items = [
    {
      key: "today",
      label: "Today",
      href: buildHref("/", userId, date),
    },
    {
      key: "food",
      label: "Food",
      href: buildHref("/", userId, date, "#food-workspace"),
    },
    {
      key: "workout",
      label: "Workout",
      href: buildHref("/today/workout", userId, date),
    },
    {
      key: "recovery",
      label: "Recovery",
      href: buildHref("/", userId, date, "#recovery"),
    },
  ] as const;

  return (
    <nav
      aria-label="Primary mobile navigation"
      className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-surface/95 px-2 pt-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] shadow-[0_-16px_35px_-28px_rgba(15,23,42,0.55)] backdrop-blur md:hidden"
    >
      <div className="mx-auto grid max-w-lg grid-cols-4 gap-1">
        {items.map((item) => {
          const isActive = item.key === activeDestination;

          return (
            <Link
              key={item.key}
              href={item.href}
              onClick={(event) => {
                if (pathname !== "/" || item.key === "workout") {
                  return;
                }

                event.preventDefault();
                const nextUrl = new URL(item.href, window.location.href);
                window.history.pushState(null, "", nextUrl);
                setHash(nextUrl.hash);

                if (nextUrl.hash) {
                  document
                    .getElementById(nextUrl.hash.slice(1))
                    ?.scrollIntoView({ block: "start" });
                } else {
                  window.scrollTo({ top: 0 });
                }
              }}
              aria-current={isActive ? "page" : undefined}
              className={`relative flex min-h-11 items-center justify-center rounded-xl px-1 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus ${
                isActive
                  ? "bg-surface-highlighted text-accent-text"
                  : "text-text-secondary hover:bg-surface-muted hover:text-text-primary"
              }`}
            >
              {item.label}
              {isActive ? (
                <span
                  aria-hidden="true"
                  className="absolute inset-x-4 bottom-1 h-0.5 rounded-full bg-action-primary"
                />
              ) : null}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
