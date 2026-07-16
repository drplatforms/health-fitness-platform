"use client";

import { KeyboardEvent, PointerEvent, useId, useRef, useState } from "react";

import { FoodLoggingCard } from "@/components/FoodLoggingCard";
import { PersonalFoodsList } from "@/components/PersonalFoodsList";

import styles from "./FoodWorkspaceDeck.module.css";

interface FoodWorkspaceDeckProps {
  userId: number;
  targetDate: string;
  requestedDate?: string;
}

type FoodWorkspacePanel = "log" | "personal";

interface PointerStart {
  pointerId: number;
  x: number;
  y: number;
  isDragging: boolean;
}

const SWIPE_THRESHOLD_PX = 48;

export function FoodWorkspaceDeck({
  userId,
  targetDate,
  requestedDate,
}: FoodWorkspaceDeckProps) {
  const [activePanel, setActivePanel] = useState<FoodWorkspacePanel>("log");
  const id = useId();
  const logTabRef = useRef<HTMLButtonElement>(null);
  const personalTabRef = useRef<HTMLButtonElement>(null);
  const pointerStartRef = useRef<PointerStart | null>(null);
  const suppressClickRef = useRef(false);

  function activatePanel(panel: FoodWorkspacePanel, moveFocus = false) {
    setActivePanel(panel);
    if (moveFocus) {
      window.requestAnimationFrame(() => {
        (panel === "log" ? logTabRef : personalTabRef).current?.focus();
      });
    }
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    let nextPanel: FoodWorkspacePanel | null = null;

    if (event.key === "ArrowLeft" || event.key === "Home") {
      nextPanel = "log";
    } else if (event.key === "ArrowRight" || event.key === "End") {
      nextPanel = "personal";
    }

    if (nextPanel) {
      event.preventDefault();
      activatePanel(nextPanel, true);
    }
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!event.isPrimary) {
      return;
    }

    pointerStartRef.current = {
      pointerId: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      isDragging: false,
    };
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    const start = pointerStartRef.current;

    if (!start || start.pointerId !== event.pointerId || start.isDragging) {
      return;
    }

    const deltaX = event.clientX - start.x;
    const deltaY = event.clientY - start.y;
    const isHorizontalDrag =
      Math.abs(deltaX) >= SWIPE_THRESHOLD_PX &&
      Math.abs(deltaX) > Math.abs(deltaY) * 1.25;

    if (isHorizontalDrag) {
      start.isDragging = true;
      event.currentTarget.setPointerCapture(event.pointerId);
    }
  }

  function handlePointerUp(event: PointerEvent<HTMLDivElement>) {
    const start = pointerStartRef.current;
    pointerStartRef.current = null;

    if (!start || start.pointerId !== event.pointerId) {
      return;
    }

    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }

    const deltaX = event.clientX - start.x;
    const deltaY = event.clientY - start.y;
    const isHorizontalSwipe =
      Math.abs(deltaX) >= SWIPE_THRESHOLD_PX &&
      Math.abs(deltaX) > Math.abs(deltaY) * 1.25;

    if (!isHorizontalSwipe) {
      return;
    }

    suppressClickRef.current = true;
    activatePanel(deltaX < 0 ? "personal" : "log");
    window.setTimeout(() => {
      suppressClickRef.current = false;
    }, 0);
  }

  function handlePointerCancel(event: PointerEvent<HTMLDivElement>) {
    pointerStartRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  return (
    <section className={styles.deck} aria-label="Food workspace">
      <div
        className={styles.tabList}
        role="tablist"
        aria-label="Food workspace views"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
        onClickCapture={(event) => {
          if (suppressClickRef.current) {
            event.preventDefault();
            event.stopPropagation();
            suppressClickRef.current = false;
          }
        }}
      >
        <button
          ref={logTabRef}
          id={`${id}-log-tab`}
          type="button"
          role="tab"
          aria-selected={activePanel === "log"}
          aria-controls={`${id}-log-panel`}
          tabIndex={activePanel === "log" ? 0 : -1}
          onClick={() => activatePanel("log")}
          onKeyDown={handleTabKeyDown}
          className={`${styles.tab} ${
            activePanel === "log" ? styles.activeTab : styles.inactiveTab
          }`}
        >
          <span className={styles.tabLabel}>Log Food</span>
          <span className={styles.tabHint}>Search and log</span>
        </button>
        <button
          ref={personalTabRef}
          id={`${id}-personal-tab`}
          type="button"
          role="tab"
          aria-selected={activePanel === "personal"}
          aria-controls={`${id}-personal-panel`}
          tabIndex={activePanel === "personal" ? 0 : -1}
          onClick={() => activatePanel("personal")}
          onKeyDown={handleTabKeyDown}
          className={`${styles.tab} ${
            activePanel === "personal" ? styles.activeTab : styles.inactiveTab
          }`}
        >
          <span className={styles.tabLabel}>My Foods</span>
          <span className={styles.tabHint}>Manage saved foods</span>
        </button>
      </div>

      <div className={styles.surface}>
        <div
          id={`${id}-log-panel`}
          role="tabpanel"
          aria-labelledby={`${id}-log-tab`}
          hidden={activePanel !== "log"}
          className={styles.panel}
        >
          <FoodLoggingCard
            userId={userId}
            targetDate={targetDate}
            navigationDate={requestedDate}
            variant="embedded"
          />
        </div>
        <div
          id={`${id}-personal-panel`}
          role="tabpanel"
          aria-labelledby={`${id}-personal-tab`}
          hidden={activePanel !== "personal"}
          className={styles.panel}
        >
          <PersonalFoodsList
            userId={userId}
            targetDate={requestedDate}
            variant="embedded"
          />
        </div>
      </div>
    </section>
  );
}
