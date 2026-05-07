import type { CanonAnnotationKind } from '../../types/canonCustomization';

interface CanonLockBadgeProps {
  kind: CanonAnnotationKind;
}

const styleMap: Record<CanonAnnotationKind, string> = {
  locked: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800',
  soft_guidance: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800',
  mutable: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
  forbidden_contradiction: 'bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 border-violet-200 dark:border-violet-800',
  generation_note: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-600',
};

const labelMap: Record<CanonAnnotationKind, string> = {
  locked: 'Locked',
  soft_guidance: 'Soft',
  mutable: 'Mutable',
  forbidden_contradiction: 'Forbidden',
  generation_note: 'Note',
};

export function CanonLockBadge({ kind }: CanonLockBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-xs ${styleMap[kind]}`}>
      {labelMap[kind]}
    </span>
  );
}
