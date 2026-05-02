import type { GenerationRunResponse } from '../../types/storyGeneration';

interface GeneratedStoryReviewProps {
  run: GenerationRunResponse | null;
}

export function GeneratedStoryReview({ run }: GeneratedStoryReviewProps) {
  if (!run) {
    return null;
  }
  const manuscript = run.created_artifacts.find((item) => item.artifact_kind === 'manuscript_document');
  return (
    <div className="rounded border border-slate-300 p-3 text-sm">
      <p className="font-semibold">Generated Story Review</p>
      <p>Run: {run.generation_id || 'pending'}</p>
      <p>Manuscript: {manuscript?.artifact_id || 'Not yet available'}</p>
    </div>
  );
}
