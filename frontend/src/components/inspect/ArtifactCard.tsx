import { useState } from 'react';
import type { ArtifactLineageView, ArtifactState } from '../../types/inspect';
import ProvenanceBadge from '../common/ProvenanceBadge';

interface ArtifactCardProps {
  artifact: ArtifactLineageView;
}

const STATE_STYLES: Record<ArtifactState, string> = {
  CANONICAL: 'bg-green-100 text-green-700',
  SUPERSEDED: 'bg-yellow-100 text-yellow-700',
  REJECTED: 'bg-red-100 text-red-700',
  DRAFT: 'bg-gray-100 text-gray-700',
};

const KIND_LABELS: Record<string, string> = {
  PROJECT_BRIEF: 'Project Brief',
  CHAPTER_PLAN: 'Chapter Plan',
  SEQUENCE: 'Sequence',
  SCENE_STORYBOARD: 'Scene Storyboard',
  STORY_BIBLE: 'Story Bible',
  MANUSCRIPT_DOCUMENT: 'Manuscript Document',
};

export default function ArtifactCard({ artifact }: ArtifactCardProps) {
  const [expanded, setExpanded] = useState(false);

  const {
    artifact_kind,
    state,
    step_name,
    created_at,
    provenance,
  } = artifact;

  const formattedDate = new Date(created_at).toLocaleString();

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border shadow-sm">
      <div className="flex items-start justify-between gap-3 mb-2">
        <h4 className="font-medium text-gray-900 dark:text-slate-100 flex-1">
          {KIND_LABELS[artifact_kind] || artifact_kind}
        </h4>
        
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATE_STYLES[state]}`}>
          {state}
        </span>
      </div>

      <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-slate-400 mb-2">
        <span>Step: {step_name}</span>
        <span>•</span>
        <span>{formattedDate}</span>
      </div>

      {provenance && (
        <ProvenanceBadge compact provenance={provenance} />
      )}

      <button 
        onClick={() => setExpanded(!expanded)}
        className="mt-3 text-sm text-blue-600 hover:text-blue-700"
      >
        {expanded ? 'Hide preview' : 'Show preview'}
      </button>

      {expanded && (
        <div className="mt-2 p-3 bg-gray-50 dark:bg-slate-700 rounded text-xs text-gray-700 dark:text-slate-300 max-h-48 overflow-y-auto">
          <p className="font-medium mb-1">Artifact ID: {artifact.artifact_id}</p>
          <p>Run ID: {artifact.run_id}</p>
        </div>
      )}
    </div>
  );
}
