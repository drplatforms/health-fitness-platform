interface DataQualityNoteProps {
  title: string;
  items: string[];
}

export function DataQualityNote({ title, items }: DataQualityNoteProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="rounded-[24px] border border-slate-200/90 bg-slate-50/90 p-5">
      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-600">
          {title}
        </h2>
        <ul className="space-y-2 text-sm leading-6 text-slate-700">
          {items.map((item) => (
            <li key={item} className="rounded-2xl bg-white px-4 py-3">
              {item}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
