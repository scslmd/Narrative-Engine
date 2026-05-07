import { useState } from 'react';
import type {
  CanonCustomizationProfile,
  CanonCustomizationProfileCreateRequest,
} from '../../types/canonCustomization';
import type { CanonGenerationRequest, GenerationRunResponse } from '../../types/storyGeneration';

interface CanonProfileEditorProps {
  projectId: string;
  selectedProfile: CanonCustomizationProfile | null;
  onCreateProfile: (request: CanonCustomizationProfileCreateRequest) => Promise<void>;
  onSubmitGeneration: (request: CanonGenerationRequest) => Promise<GenerationRunResponse>;
}

export function CanonProfileEditor({
  projectId,
  selectedProfile,
  onCreateProfile,
  onSubmitGeneration,
}: CanonProfileEditorProps) {
  const [profileName, setProfileName] = useState('Default Canon Profile');
  const [brief, setBrief] = useState('Generate a canon-congruent story.');

  return (
    <div className="rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 space-y-2">
      <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Profile Editor</div>
      <input
        className="w-full rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm"
        value={profileName}
        onChange={(event) => setProfileName(event.target.value)}
      />
      <textarea
        className="w-full rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm min-h-20"
        value={brief}
        onChange={(event) => setBrief(event.target.value)}
      />
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded bg-slate-900 text-white px-3 py-1.5 text-sm"
          onClick={() =>
            void onCreateProfile({
              project_id: projectId,
              name: profileName,
              generation_brief_template: brief,
              canon_scope: {
                source_project_id: projectId,
                scope_mode: 'selected',
                character_ids: [],
                world_bible_refs: [],
                continuity_thread_ids: [],
                arc_ids: [],
                mythos_ids: [],
                pattern_ids: [],
                include_relationships: true,
                include_unresolved_questions: true,
                include_contradictions_as_forbidden: true,
              },
            })
          }
        >
          Save Profile
        </button>
        {selectedProfile && (
          <button
            type="button"
            className="rounded bg-indigo-700 text-white px-3 py-1.5 text-sm"
            onClick={() =>
              void onSubmitGeneration({
                source_project_id: projectId,
                mode: selectedProfile.default_generation_mode,
                destination: { destination_kind: 'same_project', target_project_id: projectId },
                canon_scope: selectedProfile.canon_scope,
                canon_policy: selectedProfile.canon_policy,
                generation_brief: selectedProfile.generation_brief_template || brief,
                target_chapter_count: 8,
              })
            }
          >
            Submit Generation
          </button>
        )}
      </div>
    </div>
  );
}
