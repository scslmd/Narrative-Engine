import { useEffect, useState } from 'react';
import type { CharacterProfile } from '../../types/characters';
import type {
  CanonAnnotation,
  CanonCustomizationProfile,
  CanonCustomizationProfileCreateRequest,
} from '../../types/canonCustomization';
import type { MythosEntry } from '../../types/mythos';
import type { PatternEntry } from '../../types/patterns';
import type { WorldBibleEntry } from '../../types/bible';
import type {
  CanonGenerationPacket,
  CanonGenerationRequest,
  GenerationRunResponse,
  WorldBibleRef,
} from '../../types/storyGeneration';
import type { CanonSelectionState } from '../../domains/canon/useCanonController';
import type { useCanonController } from '../../domains/canon/useCanonController';
import { CanonGenerationRulesEditor } from './CanonGenerationRulesEditor';
import { CanonOverviewPanel } from './CanonOverviewPanel';
import { CanonPacketPreview } from './CanonPacketPreview';
import { CanonProfileEditor } from './CanonProfileEditor';
import { CanonProfileList } from './CanonProfileList';
import { CanonScopeSummary } from './CanonScopeSummary';
import { CanonSelectionDrawer } from './CanonSelectionDrawer';
import { MythosLibraryWorkspace } from '../mythos/MythosLibraryWorkspace';
import { PatternLibraryWorkspace } from '../patterns/PatternLibraryWorkspace';

interface CanonWorkshopControllerProps {
  projectId: string;
  controller: ReturnType<typeof useCanonController>;
  initialTab?: 'overview' | 'mythos' | 'patterns' | 'packet';
}

interface CanonWorkshopLegacyProps {
  projectId: string;
  characters: CharacterProfile[];
  worldEntries: WorldBibleEntry[];
  mythosEntries: MythosEntry[];
  patternEntries: PatternEntry[];
  annotations: CanonAnnotation[];
  profiles: CanonCustomizationProfile[];
  onSaveProfile: (request: CanonCustomizationProfileCreateRequest) => Promise<void>;
  onPreviewPacket: (profileId: string) => Promise<void>;
  onSubmitGeneration: (request: CanonGenerationRequest) => Promise<GenerationRunResponse>;
  packetPreview: CanonGenerationPacket | null;
  initialTab?: 'overview' | 'mythos' | 'patterns' | 'packet';
}

type CanonWorkshopProps = CanonWorkshopControllerProps | CanonWorkshopLegacyProps;

function toLegacyProfileRequest(projectId: string, selection: CanonSelectionState): CanonCustomizationProfileCreateRequest {
  return {
    project_id: projectId,
    name: selection.profileName,
    description: '',
    default_generation_mode: 'same_project_side_story',
    canon_scope: {
      source_project_id: projectId,
      scope_mode: 'selected',
      character_ids: selection.selectedCharacterIds,
      world_bible_refs: selection.selectedWorldRefs,
      continuity_thread_ids: [],
      arc_ids: [],
      mythos_ids: selection.selectedMythosIds,
      pattern_ids: selection.selectedPatternIds,
      include_relationships: true,
      include_unresolved_questions: true,
      include_contradictions_as_forbidden: true,
    },
    canon_policy: {
      locked_character_fields: ['character.display_name', 'character.voice_notes'],
      locked_world_fields: ['world_bible.title', 'world_bible.canonical_facts'],
      allowed_character_changes: [],
      allowed_world_changes: [],
      forbidden_contradictions: [],
      continuity_strictness: 'repair_once',
    },
    generation_brief_template: selection.generationBrief,
    selected_annotation_ids: [],
    status: 'draft',
  };
}

function toLegacyGenerationRequest(projectId: string, selection: CanonSelectionState): CanonGenerationRequest {
  return {
    source_project_id: projectId,
    mode: 'same_project_side_story',
    destination: {
      destination_kind: 'same_project',
      target_project_id: projectId,
    },
    canon_scope: {
      source_project_id: projectId,
      scope_mode: 'selected',
      character_ids: selection.selectedCharacterIds,
      world_bible_refs: selection.selectedWorldRefs,
      continuity_thread_ids: [],
      arc_ids: [],
      mythos_ids: selection.selectedMythosIds,
      pattern_ids: selection.selectedPatternIds,
      include_relationships: true,
      include_unresolved_questions: true,
      include_contradictions_as_forbidden: true,
    },
    generation_brief: selection.generationBrief,
    target_chapter_count: 8,
  };
}

export function CanonWorkshop(props: CanonWorkshopProps) {
  const { projectId, initialTab = 'overview' } = props;
  const controller = 'controller' in props ? props.controller : null;
  const legacy = controller ? null : (props as CanonWorkshopLegacyProps);
  const [activeTab, setActiveTab] = useState<'overview' | 'mythos' | 'patterns' | 'packet'>(initialTab);
  const [profileName, setProfileName] = useState('Default Canon Profile');
  const [generationBrief, setGenerationBrief] = useState('Generate a canon-congruent continuation.');
  const [selectedCharacterIds, setSelectedCharacterIds] = useState<string[]>([]);
  const [selectedWorldRefs, setSelectedWorldRefs] = useState<WorldBibleRef[]>([]);
  const [selectedMythosIds, setSelectedMythosIds] = useState<string[]>([]);
  const [selectedPatternIds, setSelectedPatternIds] = useState<string[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');
  const [materializeMythosId, setMaterializeMythosId] = useState('');
  const [materializePatternId, setMaterializePatternId] = useState('');

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  const toggleString = (items: string[], value: string): string[] =>
    items.includes(value) ? items.filter((item) => item !== value) : [...items, value];

  const toggleWorldRef = (entry: WorldBibleEntry): WorldBibleRef[] => {
    const found = selectedWorldRefs.some(
      (item) => item.entry_type === entry.entry_type && item.title === entry.title,
    );
    if (found) {
      return selectedWorldRefs.filter(
        (item) => !(item.entry_type === entry.entry_type && item.title === entry.title),
      );
    }
    return [...selectedWorldRefs, { entry_type: entry.entry_type, title: entry.title }];
  };

  const selectionState: CanonSelectionState = {
    profileName,
    generationBrief,
    selectedCharacterIds,
    selectedWorldRefs,
    selectedMythosIds,
    selectedPatternIds,
  };

  const model = {
    characters: controller ? controller.characters : legacy!.characters,
    worldEntries: controller ? controller.worldEntries : legacy!.worldEntries,
    mythosEntries: controller ? controller.mythosEntries : legacy!.mythosEntries,
    patternEntries: controller ? controller.patternEntries : legacy!.patternEntries,
    annotations: controller ? controller.annotations : legacy!.annotations,
    profiles: controller ? controller.profiles : legacy!.profiles,
    packetPreview: controller ? controller.packetPreview : legacy!.packetPreview,
    saveProfileFromSelection: async (selection: CanonSelectionState) => {
      if (controller) {
        await controller.saveProfileFromSelection(selection);
        return;
      }
      await legacy!.onSaveProfile(toLegacyProfileRequest(projectId, selection));
    },
    submitGenerationFromSelection: async (selection: CanonSelectionState) => {
      if (controller) {
        return controller.submitGenerationFromSelection(selection);
      }
      return legacy!.onSubmitGeneration(toLegacyGenerationRequest(projectId, selection));
    },
    previewPacket: async (profileId: string) => {
      if (controller) {
        await controller.previewPacket(profileId);
        return;
      }
      await legacy!.onPreviewPacket(profileId);
    },
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button type="button" className="rounded border px-2 py-1 text-xs text-slate-900 dark:text-slate-100" onClick={() => setActiveTab('overview')}>Overview</button>
        <button type="button" className="rounded border px-2 py-1 text-xs text-slate-900 dark:text-slate-100" onClick={() => setActiveTab('mythos')}>Mythos</button>
        <button type="button" className="rounded border px-2 py-1 text-xs text-slate-900 dark:text-slate-100" onClick={() => setActiveTab('patterns')}>Patterns</button>
        <button type="button" className="rounded border px-2 py-1 text-xs text-slate-900 dark:text-slate-100" onClick={() => setActiveTab('packet')}>Packet Preview</button>
      </div>

      <CanonOverviewPanel
        characterCount={model.characters.length}
        worldCount={model.worldEntries.length}
        mythosCount={model.mythosEntries.length}
        patternCount={model.patternEntries.length}
        annotationCount={model.annotations.length}
      />

      {activeTab === 'mythos' && (
        <div className="space-y-3">
          <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
            <div className="flex gap-2">
              <input
                className="flex-1 rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm"
                value={materializeMythosId}
                onChange={(event) => setMaterializeMythosId(event.target.value)}
                placeholder="Extraction ID to materialize"
              />
              <button
                type="button"
                className="rounded bg-slate-900 text-white px-3 py-1.5 text-sm disabled:opacity-50"
                disabled={!materializeMythosId.trim() || !controller}
                onClick={() => void controller?.materializeMythos(materializeMythosId.trim())}
              >
                Materialize
              </button>
            </div>
          </div>
          <MythosLibraryWorkspace
            entries={model.mythosEntries}
            selectedMythosIds={selectedMythosIds}
            onToggleUse={(mythosId) => setSelectedMythosIds(toggleString(selectedMythosIds, mythosId))}
            onDeleteEntry={controller ? (mythosId) => void controller.deleteMythosEntry(mythosId) : undefined}
          />
        </div>
      )}

      {activeTab === 'patterns' && (
        <div className="space-y-3">
          <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
            <div className="flex gap-2">
              <input
                className="flex-1 rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm"
                value={materializePatternId}
                onChange={(event) => setMaterializePatternId(event.target.value)}
                placeholder="Extraction ID to materialize"
              />
              <button
                type="button"
                className="rounded bg-slate-900 text-white px-3 py-1.5 text-sm disabled:opacity-50"
                disabled={!materializePatternId.trim() || !controller}
                onClick={() => void controller?.materializePatterns(materializePatternId.trim())}
              >
                Materialize
              </button>
            </div>
          </div>
          <PatternLibraryWorkspace
            entries={model.patternEntries}
            selectedPatternIds={selectedPatternIds}
            onToggleUse={(patternId) => setSelectedPatternIds(toggleString(selectedPatternIds, patternId))}
            onDeleteEntry={controller ? (patternId) => void controller.deletePatternEntry(patternId) : undefined}
          />
        </div>
      )}

      {activeTab === 'packet' && <CanonPacketPreview packet={model.packetPreview} />}
      {activeTab === 'overview' && (
        <>
          <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 space-y-3">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Canon Workshop</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <label className="text-sm text-slate-700 dark:text-slate-300">
                Profile Name
                <input
                  className="mt-1 block w-full rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm"
                  value={profileName}
                  onChange={(event) => setProfileName(event.target.value)}
                />
              </label>
              <label className="text-sm text-slate-700 dark:text-slate-300">
                Active Profile
                <select
                  className="mt-1 block w-full rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm"
                  value={selectedProfileId}
                  onChange={(event) => setSelectedProfileId(event.target.value)}
                >
                  <option value="">None</option>
                  {model.profiles.map((profile) => (
                    <option key={profile.profile_id} value={profile.profile_id}>
                      {profile.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="text-sm text-slate-700 dark:text-slate-300 block">
              Generation Brief
              <textarea
                className="mt-1 block w-full rounded border border-slate-300 dark:border-slate-600 px-2 py-1.5 text-sm min-h-20"
                value={generationBrief}
                onChange={(event) => setGenerationBrief(event.target.value)}
              />
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
              <h3 className="text-sm font-semibold mb-2 text-slate-900 dark:text-slate-100">Characters</h3>
              <div className="space-y-1 max-h-48 overflow-auto">
                {model.characters.map((item) => (
                  <label key={item.character_id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedCharacterIds.includes(item.character_id)}
                      onChange={() => setSelectedCharacterIds(toggleString(selectedCharacterIds, item.character_id))}
                    />
                    <span className="text-slate-700 dark:text-slate-300">{item.display_name}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
              <h3 className="text-sm font-semibold mb-2 text-slate-900 dark:text-slate-100">World Entries</h3>
              <div className="space-y-1 max-h-48 overflow-auto">
                {model.worldEntries.map((item) => (
                  <label key={`${item.entry_type}:${item.title}`} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedWorldRefs.some((ref) => ref.entry_type === item.entry_type && ref.title === item.title)}
                      onChange={() => setSelectedWorldRefs(toggleWorldRef(item))}
                    />
                    <span className="text-slate-700 dark:text-slate-300">{item.entry_type}: {item.title}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
              <h3 className="text-sm font-semibold mb-2 text-slate-900 dark:text-slate-100">Mythos</h3>
              <div className="space-y-1 max-h-48 overflow-auto">
                {model.mythosEntries.map((item) => (
                  <label key={item.mythos_id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedMythosIds.includes(item.mythos_id)}
                      onChange={() => setSelectedMythosIds(toggleString(selectedMythosIds, item.mythos_id))}
                    />
                    <span className="text-slate-700 dark:text-slate-300">{item.entry_type}: {item.name}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
              <h3 className="text-sm font-semibold mb-2 text-slate-900 dark:text-slate-100">Patterns</h3>
              <div className="space-y-1 max-h-48 overflow-auto">
                {model.patternEntries.map((item) => (
                  <label key={item.pattern_id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedPatternIds.includes(item.pattern_id)}
                      onChange={() => setSelectedPatternIds(toggleString(selectedPatternIds, item.pattern_id))}
                    />
                    <span className="text-slate-700 dark:text-slate-300">{item.pattern_type}: {item.name}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded bg-slate-900 text-white px-3 py-1.5 text-sm"
              onClick={() => void model.saveProfileFromSelection(selectionState)}
            >
              Save Profile
            </button>
            <button
              type="button"
              className="rounded bg-slate-700 text-white px-3 py-1.5 text-sm disabled:opacity-50"
              disabled={!selectedProfileId}
              onClick={() => void model.previewPacket(selectedProfileId)}
            >
              Preview Packet
            </button>
            <button
              type="button"
              className="rounded bg-indigo-700 text-white px-3 py-1.5 text-sm"
              onClick={() => void model.submitGenerationFromSelection(selectionState)}
            >
              Generate with Selected
            </button>
          </div>
          <CanonScopeSummary
            character_ids={selectedCharacterIds}
            world_count={selectedWorldRefs.length}
            mythos_ids={selectedMythosIds}
            pattern_ids={selectedPatternIds}
          />
          <CanonGenerationRulesEditor
            policy={{
              locked_character_fields: ['character.display_name', 'character.voice_notes'],
              locked_world_fields: ['world_bible.title', 'world_bible.canonical_facts'],
              allowed_character_changes: [],
              allowed_world_changes: [],
              forbidden_contradictions: [],
              continuity_strictness: 'repair_once',
            }}
            onChange={() => undefined}
          />
          <CanonProfileList
            profiles={model.profiles}
            selectedProfileId={selectedProfileId}
            onSelect={setSelectedProfileId}
          />
          <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 space-y-2">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded bg-slate-900 text-white px-3 py-1.5 text-sm disabled:opacity-50"
                disabled={!selectedProfileId || !controller}
                onClick={() => void controller?.renameProfile(selectedProfileId, `${profileName} (Updated)`)}
              >
                Rename Selected Profile
              </button>
              <button
                type="button"
                className="rounded bg-red-700 text-white px-3 py-1.5 text-sm disabled:opacity-50"
                disabled={!selectedProfileId || !controller}
                onClick={() => void controller?.deleteProfile(selectedProfileId)}
              >
                Delete Selected Profile
              </button>
              <button
                type="button"
                className="rounded bg-slate-700 text-white px-3 py-1.5 text-sm disabled:opacity-50"
                disabled={!controller || model.annotations.length === 0}
                onClick={() => {
                  const firstAnnotationId = model.annotations[0]?.annotation_id;
                  if (controller && firstAnnotationId) {
                    void controller.deleteAnnotation(firstAnnotationId);
                  }
                }}
              >
                Delete First Annotation
              </button>
            </div>
          </div>
          <CanonProfileEditor
            projectId={projectId}
            selectedProfile={model.profiles.find((item) => item.profile_id === selectedProfileId) || null}
            onCreateProfile={async (request) => {
              await model.saveProfileFromSelection({
                ...selectionState,
                profileName: request.name,
                generationBrief: request.generation_brief_template ?? generationBrief,
                selectedCharacterIds: request.canon_scope.character_ids,
                selectedWorldRefs: request.canon_scope.world_bible_refs,
                selectedMythosIds: request.canon_scope.mythos_ids,
                selectedPatternIds: request.canon_scope.pattern_ids,
              });
            }}
            onSubmitGeneration={async (request) =>
              model.submitGenerationFromSelection({
                ...selectionState,
                generationBrief: request.generation_brief ?? generationBrief,
                selectedCharacterIds: request.canon_scope.character_ids,
                selectedWorldRefs: request.canon_scope.world_bible_refs,
                selectedMythosIds: request.canon_scope.mythos_ids,
                selectedPatternIds: request.canon_scope.pattern_ids,
              })
            }
          />
          <CanonSelectionDrawer
            onGenerate={async () => {
              await model.submitGenerationFromSelection(selectionState);
            }}
            onFork={async () => {
              await model.submitGenerationFromSelection(selectionState);
            }}
          />
        </>
      )}

      {model.packetPreview && (
        <div className="rounded-md border border-indigo-200 bg-indigo-50 p-4">
          <h3 className="text-sm font-semibold text-indigo-900">Packet Preview</h3>
          <div className="mt-2 text-xs text-indigo-900 grid grid-cols-2 md:grid-cols-4 gap-2">
            <span>Characters: {model.packetPreview.characters.length}</span>
            <span>World: {model.packetPreview.world_bible.length}</span>
            <span>Mythos: {model.packetPreview.mythos_entries.length}</span>
            <span>Patterns: {model.packetPreview.pattern_entries.length}</span>
          </div>
        </div>
      )}
    </div>
  );
}
