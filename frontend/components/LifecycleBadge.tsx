/**
 * LifecycleBadge — displays a KDP book lifecycle status as a colored pill.
 */

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  concept_pending:         { label: 'Concept Pending',        color: 'bg-slate-700 text-slate-300' },
  keyword_research:        { label: 'Keyword Research',       color: 'bg-blue-900/60 text-blue-300' },
  keyword_approved:        { label: 'Keywords ✓',             color: 'bg-blue-700/60 text-blue-200' },
  description_generation:  { label: 'Writing Description',    color: 'bg-violet-900/60 text-violet-300' },
  description_approved:    { label: 'Description ✓',          color: 'bg-violet-700/60 text-violet-200' },
  bible_generation:        { label: 'Story Bible',            color: 'bg-indigo-900/60 text-indigo-300' },
  bible_approved:          { label: 'Bible ✓',                color: 'bg-indigo-700/60 text-indigo-200' },
  writing_in_progress:     { label: 'Writing',                color: 'bg-amber-900/60 text-amber-300' },
  qa_review:               { label: 'QA Review',              color: 'bg-orange-900/60 text-orange-300' },
  export_ready:            { label: 'Export Ready',           color: 'bg-teal-900/60 text-teal-300' },
  published_kdp:           { label: 'Published KDP',          color: 'bg-emerald-900/60 text-emerald-300' },
  published_all:           { label: 'Published All',          color: 'bg-green-900/60 text-green-300' },
  archived:                { label: 'Archived',               color: 'bg-slate-800 text-slate-500' },
};

export function lifecycleLabel(status: string): string {
  return STATUS_CONFIG[status]?.label ?? status;
}

export default function LifecycleBadge({
  status,
  size = 'sm',
}: {
  status: string;
  size?: 'xs' | 'sm' | 'md';
}) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: 'bg-slate-700 text-slate-400' };
  const px = size === 'xs' ? 'px-2 py-0.5 text-[10px]' : size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm';
  return (
    <span className={`inline-block rounded-full font-medium ${px} ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}
