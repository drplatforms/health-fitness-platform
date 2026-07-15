interface DataQualityNoteProps {
  title: string;
  items: string[];
  className?: string;
}

export function DataQualityNote({
  title,
  items,
  className = "",
}: DataQualityNoteProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section
      className={`rounded-[24px] border border-border-subtle/90 bg-surface-subtle/90 p-5 ${className}`}
    >
      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-text-secondary">
          {title}
        </h2>
        <ul className="space-y-2 text-sm leading-6 text-text-body">
          {items.map((item) => (
            <li key={item} className="rounded-2xl bg-surface px-4 py-3">
              {item}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
