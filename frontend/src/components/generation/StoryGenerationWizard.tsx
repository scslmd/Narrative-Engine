import { useState } from 'react';
import type { CharacterProfile } from '../../types/characters';
import type { WorldBibleEntry } from '../../types/bible';
import type {
  CanonForkPreviewResponse,
  CanonGenerationRequest,
  CanonPolicy,
  CanonScope,
  GenerationDestination,
  GenerationMode,
  GenerationRunResponse,
} from '../../types/storyGeneration';
import { CanonPolicyEditor } from './CanonPolicyEditor';
import { CanonScopeSelector } from './CanonScopeSelector';
import { ForkPreviewPanel } from './ForkPreviewPanel';
import { GenerationDestinationSelector } from './GenerationDestinationSelector';
import { GenerationModeSelector } from './GenerationModeSelector';

interface StoryGenerationWizardProps {
  projectId: string;
  characters: CharacterProfile[];
  worldEntries: WorldBibleEntry[];
  onPreview: (request: CanonGenerationRequest) => Promise<CanonForkPreviewResponse>;
  onSubmit: (request: CanonGenerationRequest) => Promise<GenerationRunResponse>;
  onSubmitted: (run: GenerationRunResponse) => void;
}

const DEFAULT_POLICY: CanonPolicy = {
  locked_character_fields: ['display_name', 'role_in_story', 'backstory', 'voice_notes', 'continuity_facts', 'relationships_json'],
  locked_world_fields: ['entry_type', 'title', 'summary', 'canonical_facts'],
  allowed_character_changes: [],
  allowed_world_changes: [],
  forbidden_contradictions: [],
  continuity_strictness: 'repair_once',
};

export function StoryGenerationWizard({
  projectId,
  characters,
  worldEntries,
  onPreview,
  onSubmit,
  onSubmitted,
}: StoryGenerationWizardProps) {
  const [mode, setMode] = useState<GenerationMode>('same_project_side_story');
  const [destination, setDestination] = useState<GenerationDestination>({
    destination_kind: 'same_project',
    target_project_id: projectId,
  });
  const [scope, setScope] = useState<CanonScope>({
    source_project_id: projectId,
    scope_mode: 'full_project',
    character_ids: [],
    world_bible_refs: [],
    continuity_thread_ids: [],
    arc_ids: [],
    mythos_ids: [],
    pattern_ids: [],
    include_relationships: true,
    include_unresolved_questions: true,
    include_contradictions_as_forbidden: true,
  });
  const [policy, setPolicy] = useState<CanonPolicy>(DEFAULT_POLICY);
  const [generationBrief, setGenerationBrief] = useState('');
  const [chapterCount, setChapterCount] = useState(3);
  const [preview, setPreview] = useState<CanonForkPreviewResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const request: CanonGenerationRequest = {
    source_project_id: projectId,
    mode,
    destination,
    canon_scope: scope,
    generation_brief: generationBrief,
    target_chapter_count: chapterCount,
    canon_policy: policy,
  };

  const canSubmit = generationBrief.trim().length > 0 && (
    scope.scope_mode === 'full_project' || scope.character_ids.length > 0 || scope.world_bible_refs.length > 0
  );

  return (
    <div data-generation-wizard className="space-y-4 rounded-xl border border-slate-300 p-4">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Story Generation Wizard</h2>
      <GenerationModeSelector value={mode} onChange={setMode} />
      <GenerationDestinationSelector destination={destination} onChange={setDestination} />
      <CanonScopeSelector scope={scope} characters={characters} worldEntries={worldEntries} onChange={setScope} />
      <CanonPolicyEditor policy={policy} onChange={setPolicy} />
      <textarea
        value={generationBrief}
        onChange={(event) => setGenerationBrief(event.target.value)}
        placeholder="Generation brief"
        className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-subtle px-3 py-2 text-sm min-h-[120px]"
      />
      <input
        type="number"
        min={1}
        max={100}
        value={chapterCount}
        onChange={(event) => setChapterCount(Number(event.target.value))}
        className="w-32 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-gray-400 dark:placeholder:text-subtle px-3 py-2 text-sm"
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={async () => setPreview(await onPreview(request))}
          className="px-3 py-2 rounded border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 text-sm transition-colors hover:border-slate-400 dark:hover:border-slate-600"
          disabled={!canSubmit || isSubmitting}
        >
          Preview Fork
        </button>
        <button
          type="button"
          onClick={async () => {
            setIsSubmitting(true);
            try {
              const run = await onSubmit(request);
              onSubmitted(run);
            } finally {
              setIsSubmitting(false);
            }
          }}
          className="px-3 py-2 rounded bg-indigo-600 text-white text-sm disabled:opacity-50"
          disabled={!canSubmit || isSubmitting}
        >
          Start Generation
        </button>
      </div>
      <ForkPreviewPanel preview={preview} />
    </div>
  );
}
