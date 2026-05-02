import type { CanonAnnotationKind } from '../../types/canonCustomization';

interface CanonLockBadgeProps {
  kind: CanonAnnotationKind;
}

const styleMap: Record<CanonAnnotationKind, string> = {
  locked: 'bg-red-100 text-red-700 border-red-200',
  soft_guidance: 'bg-amber-100 text-amber-700 border-amber-200',
  mutable: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  forbidden_contradiction: 'bg-violet-100 text-violet-700 border-violet-200',
  generation_note: 'bg-slate-100 text-slate-700 border-slate-200',
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
