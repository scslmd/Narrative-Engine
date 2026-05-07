import type { CanonForkPreviewResponse } from '../../types/storyGeneration';

interface ForkPreviewPanelProps {
  preview: CanonForkPreviewResponse | null;
}

export function ForkPreviewPanel({ preview }: ForkPreviewPanelProps) {
  if (!preview) {
    return null;
  }
  return (
    <div className="rounded border border-slate-300 dark:border-slate-600 p-3 text-sm">
      <p className="font-semibold mb-1">Fork Preview</p>
      <p>Characters: {preview.selected_character_ids.length}</p>
      <p>World Entries: {preview.selected_world_bible_refs.length}</p>
      <p>Arcs: {preview.selected_arc_ids.length}</p>
      <p>Threads: {preview.selected_continuity_thread_ids.length}</p>
    </div>
  );
}
