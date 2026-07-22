"use client";

import {
  CSSProperties,
  KeyboardEvent,
  PointerEvent,
  ReactNode,
  useId,
  useRef,
  useState,
} from "react";

import styles from "./FoodWorkspaceDeck.module.css";

export interface WorkspaceDeckTab {
  key: string;
  label: string;
  hint: string;
  content: ReactNode;
}

interface WorkspaceDeckProps {
  ariaLabel: string;
  tabs: WorkspaceDeckTab[];
  initialActiveKey?: string;
}

interface PointerStart {
  pointerId: number;
  x: number;
  y: number;
  isDragging: boolean;
}

const SWIPE_THRESHOLD_PX = 48;

export function WorkspaceDeck({
  ariaLabel,
  tabs,
  initialActiveKey,
}: WorkspaceDeckProps) {
  const [activePanel, setActivePanel] = useState(() =>
    tabs.some((tab) => tab.key === initialActiveKey)
      ? (initialActiveKey ?? tabs[0]?.key ?? "")
      : (tabs[0]?.key ?? ""),
  );
  const id = useId();
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const pointerStartRef = useRef<PointerStart | null>(null);
  const suppressClickRef = useRef(false);
  const activeIndex = Math.max(
    0,
    tabs.findIndex((tab) => tab.key === activePanel),
  );

  function activatePanel(panel: string, moveFocus = false) {
    setActivePanel(panel);
    if (moveFocus) {
      window.requestAnimationFrame(() => tabRefs.current[panel]?.focus());
    }
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    let nextIndex: number | null = null;

    if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = tabs.length - 1;
    } else if (event.key === "ArrowLeft") {
      nextIndex = Math.max(0, activeIndex - 1);
    } else if (event.key === "ArrowRight") {
      nextIndex = Math.min(tabs.length - 1, activeIndex + 1);
    }

    const nextPanel = nextIndex === null ? null : tabs[nextIndex]?.key;
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
    if (
      Math.abs(deltaX) >= SWIPE_THRESHOLD_PX &&
      Math.abs(deltaX) > Math.abs(deltaY) * 1.25
    ) {
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
    if (
      Math.abs(deltaX) < SWIPE_THRESHOLD_PX ||
      Math.abs(deltaX) <= Math.abs(deltaY) * 1.25
    ) {
      return;
    }

    suppressClickRef.current = true;
    const nextIndex = Math.min(
      tabs.length - 1,
      Math.max(0, activeIndex + (deltaX < 0 ? 1 : -1)),
    );
    const nextPanel = tabs[nextIndex]?.key;
    if (nextPanel) {
      activatePanel(nextPanel);
    }
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

  const tabListStyle = {
    "--workspace-tab-count": tabs.length,
  } as CSSProperties;

  return (
    <section className={styles.deck} aria-label={ariaLabel}>
      <div
        className={styles.tabList}
        style={tabListStyle}
        role="tablist"
        aria-label={`${ariaLabel} views`}
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
        {tabs.map((tab) => {
          const isActive = activePanel === tab.key;
          return (
            <button
              key={tab.key}
              ref={(element) => {
                tabRefs.current[tab.key] = element;
              }}
              id={`${id}-${tab.key}-tab`}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`${id}-${tab.key}-panel`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => activatePanel(tab.key)}
              onKeyDown={handleTabKeyDown}
              className={`${styles.tab} ${
                isActive ? styles.activeTab : styles.inactiveTab
              }`}
            >
              <span className={styles.tabLabel}>{tab.label}</span>
              <span className={styles.tabHint}>{tab.hint}</span>
            </button>
          );
        })}
      </div>

      <div className={styles.surface}>
        {tabs.map((tab) => (
          <div
            key={tab.key}
            id={`${id}-${tab.key}-panel`}
            role="tabpanel"
            aria-labelledby={`${id}-${tab.key}-tab`}
            hidden={activePanel !== tab.key}
            className={styles.panel}
          >
            {tab.content}
          </div>
        ))}
      </div>
    </section>
  );
}
