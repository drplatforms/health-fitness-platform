"use client";

import { KeyboardEvent, PointerEvent, useId, useRef, useState } from "react";

import { AvailableIngredientsPanel } from "@/components/AvailableIngredientsPanel";
import { FoodLoggingCard } from "@/components/FoodLoggingCard";
import { PersonalFoodsList } from "@/components/PersonalFoodsList";
import { SavedMealsPanel } from "@/components/SavedMealsPanel";

import styles from "./FoodWorkspaceDeck.module.css";

interface FoodWorkspaceDeckProps {
  userId: number;
  targetDate: string;
  requestedDate?: string;
}

type FoodWorkspacePanel = "log" | "meals" | "available" | "personal";

interface PointerStart {
  pointerId: number;
  x: number;
  y: number;
  isDragging: boolean;
}

const SWIPE_THRESHOLD_PX = 48;
const PANEL_ORDER: FoodWorkspacePanel[] = [
  "log",
  "meals",
  "available",
  "personal",
];

export function FoodWorkspaceDeck({
  userId,
  targetDate,
  requestedDate,
}: FoodWorkspaceDeckProps) {
  const [activePanel, setActivePanel] = useState<FoodWorkspacePanel>("log");
  const id = useId();
  const logTabRef = useRef<HTMLButtonElement>(null);
  const mealsTabRef = useRef<HTMLButtonElement>(null);
  const availableTabRef = useRef<HTMLButtonElement>(null);
  const personalTabRef = useRef<HTMLButtonElement>(null);
  const pointerStartRef = useRef<PointerStart | null>(null);
  const suppressClickRef = useRef(false);

  function activatePanel(panel: FoodWorkspacePanel, moveFocus = false) {
    setActivePanel(panel);
    if (moveFocus) {
      window.requestAnimationFrame(() => {
        ({
          log: logTabRef,
          meals: mealsTabRef,
          available: availableTabRef,
          personal: personalTabRef,
        })[panel].current?.focus();
      });
    }
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    let nextPanel: FoodWorkspacePanel | null = null;

    const currentIndex = PANEL_ORDER.indexOf(activePanel);
    if (event.key === "Home") {
      nextPanel = PANEL_ORDER[0];
    } else if (event.key === "End") {
      nextPanel = PANEL_ORDER[PANEL_ORDER.length - 1];
    } else if (event.key === "ArrowLeft") {
      nextPanel = PANEL_ORDER[Math.max(0, currentIndex - 1)];
    } else if (event.key === "ArrowRight") {
      nextPanel = PANEL_ORDER[Math.min(PANEL_ORDER.length - 1, currentIndex + 1)];
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
    const currentIndex = PANEL_ORDER.indexOf(activePanel);
    const nextIndex = Math.min(
      PANEL_ORDER.length - 1,
      Math.max(0, currentIndex + (deltaX < 0 ? 1 : -1)),
    );
    activatePanel(PANEL_ORDER[nextIndex]);
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
          ref={mealsTabRef}
          id={`${id}-meals-tab`}
          type="button"
          role="tab"
          aria-selected={activePanel === "meals"}
          aria-controls={`${id}-meals-panel`}
          tabIndex={activePanel === "meals" ? 0 : -1}
          onClick={() => activatePanel("meals")}
          onKeyDown={handleTabKeyDown}
          className={`${styles.tab} ${
            activePanel === "meals" ? styles.activeTab : styles.inactiveTab
          }`}
        >
          <span className={styles.tabLabel}>Meals</span>
          <span className={styles.tabHint}>Build and reuse</span>
        </button>
        <button
          ref={availableTabRef}
          id={`${id}-available-tab`}
          type="button"
          role="tab"
          aria-selected={activePanel === "available"}
          aria-controls={`${id}-available-panel`}
          tabIndex={activePanel === "available" ? 0 : -1}
          onClick={() => activatePanel("available")}
          onKeyDown={handleTabKeyDown}
          className={`${styles.tab} ${
            activePanel === "available" ? styles.activeTab : styles.inactiveTab
          }`}
        >
          <span className={styles.tabLabel}>Available</span>
          <span className={styles.tabHint}>Foods on hand</span>
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
          id={`${id}-meals-panel`}
          role="tabpanel"
          aria-labelledby={`${id}-meals-tab`}
          hidden={activePanel !== "meals"}
          className={styles.panel}
        >
          <SavedMealsPanel userId={userId} targetDate={targetDate} />
        </div>
        <div
          id={`${id}-available-panel`}
          role="tabpanel"
          aria-labelledby={`${id}-available-tab`}
          hidden={activePanel !== "available"}
          className={styles.panel}
        >
          <AvailableIngredientsPanel userId={userId} />
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
