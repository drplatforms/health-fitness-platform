import Link from "next/link";
import type { CSSProperties } from "react";

import styles from "./FoodWorkspaceDeck.module.css";

interface LinkCardDeckItem {
  key: string;
  label: string;
  href: string;
}

interface LinkCardDeckProps {
  activeKey: string;
  ariaLabel: string;
  className?: string;
  items: ReadonlyArray<LinkCardDeckItem>;
}

export function LinkCardDeck({
  activeKey,
  ariaLabel,
  className = "",
  items,
}: LinkCardDeckProps) {
  const listStyle = {
    "--workspace-tab-count": items.length,
  } as CSSProperties;

  return (
    <nav aria-label={ariaLabel} className={className}>
      <div
        className={`${styles.tabList} ${styles.navigationList}`}
        style={listStyle}
      >
        {items.map((item) => {
          const isActive = item.key === activeKey;
          return (
            <Link
              key={item.key}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={`${styles.tab} ${styles.navigationTab} ${
                isActive ? styles.activeTab : styles.inactiveTab
              }`}
            >
              <span className={styles.tabLabel}>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
