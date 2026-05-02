import { useState } from 'react';
import type { CanonAnnotation, CanonAnnotationKind, CanonTargetKind } from '../../types/canonCustomization';
import { CanonLockBadge } from './CanonLockBadge';

interface CanonAnnotationToolbarProps {
  projectId: string;
  target_kind: CanonTargetKind;
  target_id: string;
  field_path: string;
  annotations: CanonAnnotation[];
  onCreate: (
    targetKind: CanonTargetKind,
    targetId: string,
    fieldPath: string,
    annotationKind: CanonAnnotationKind,
    note: string,
  ) => Promise<void>;
}

export function CanonAnnotationToolbar({
  projectId,
  target_kind,
  target_id,
  field_path,
  annotations,
  onCreate,
}: CanonAnnotationToolbarProps) {
  const [note, setNote] = useState('');
  const matching = annotations.filter(
    (item) =>
      item.project_id === projectId &&
      item.target_kind === target_kind &&
      item.target_id === target_id &&
      item.field_path === field_path,
  );

  return (
    <div className="mt-2 rounded border border-slate-200 bg-slate-50 p-2 space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {matching.map((item) => (
          <CanonLockBadge key={item.annotation_id} kind={item.annotation_kind} />
        ))}
        <button
          type="button"
          className="text-xs px-2 py-1 rounded border border-red-300 text-red-700"
          onClick={() => void onCreate(target_kind, target_id, field_path, 'locked', note)}
        >
          Lock
        </button>
        <button
          type="button"
          className="text-xs px-2 py-1 rounded border border-amber-300 text-amber-700"
          onClick={() => void onCreate(target_kind, target_id, field_path, 'soft_guidance', note)}
        >
          Soft
        </button>
        <button
          type="button"
          className="text-xs px-2 py-1 rounded border border-emerald-300 text-emerald-700"
          onClick={() => void onCreate(target_kind, target_id, field_path, 'mutable', note)}
        >
          Mutable
        </button>
        <button
          type="button"
          className="text-xs px-2 py-1 rounded border border-violet-300 text-violet-700"
          onClick={() => void onCreate(target_kind, target_id, field_path, 'forbidden_contradiction', note)}
        >
          Forbidden
        </button>
      </div>
      <input
        value={note}
        onChange={(event) => setNote(event.target.value)}
        placeholder="Optional canon note"
        className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
      />
    </div>
  );
}
