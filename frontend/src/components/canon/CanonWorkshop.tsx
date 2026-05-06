import { useEffect, useState } from 'react';
import type { CharacterProfile } from '../../types/characters';
import type {
  CanonAnnotation,
  CanonCustomizationProfile,
  CanonCustomizationProfileCreateRequest,
} from '../../types/canonCustomization';
import type { MythosEntry } from '../../types/mythos';
import type { PatternEntry } from '../../types/patterns';
import type { CanonGenerationPacket, CanonGenerationRequest, GenerationRunResponse, WorldBibleRef } from '../../types/storyGeneration';
import type { WorldBibleEntry } from '../../types/bible';
import { CanonGenerationRulesEditor } from './CanonGenerationRulesEditor';
import { CanonOverviewPanel } from './CanonOverviewPanel';
import { CanonPacketPreview } from './CanonPacketPreview';
import { CanonProfileEditor } from './CanonProfileEditor';
import { CanonProfileList } from './CanonProfileList';
import { CanonScopeSummary } from './CanonScopeSummary';
import { CanonSelectionDrawer } from './CanonSelectionDrawer';
import { MythosLibraryWorkspace } from '../mythos/MythosLibraryWorkspace';
import { PatternLibraryWorkspace } from '../patterns/PatternLibraryWorkspace';

interface CanonWorkshopProps {
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
  onDeleteMythosEntry?: (mythosId: string) => void;
  onDeletePatternEntry?: (patternId: string) => void;
  packetPreview: CanonGenerationPacket | null;
  initialTab?: 'overview' | 'mythos' | 'patterns' | 'packet';
}

export function CanonWorkshop({
  projectId,
  characters,
  worldEntries,
  mythosEntries,
  patternEntries,
  annotations,
  profiles,
  onSaveProfile,
  onPreviewPacket,
  onSubmitGeneration,
  onDeleteMythosEntry,
  onDeletePatternEntry,
  packetPreview,
  initialTab = 'overview',
}: CanonWorkshopProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'mythos' | 'patterns' | 'packet'>(initialTab);
  const [profileName, setProfileName] = useState('Default Canon Profile');
  const [generationBrief, setGenerationBrief] = useState('Generate a canon-congruent continuation.');
  const [selectedCharacterIds, setSelectedCharacterIds] = useState<string[]>([]);
  const [selectedWorldRefs, setSelectedWorldRefs] = useState<WorldBibleRef[]>([]);
  const [selectedMythosIds, setSelectedMythosIds] = useState<string[]>([]);
  const [selectedPatternIds, setSelectedPatternIds] = useState<string[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');

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

  const handleSaveProfile = async () => {
    await onSaveProfile({
      project_id: projectId,
      name: profileName,
      description: '',
      default_generation_mode: 'same_project_side_story',
      canon_scope: {
        source_project_id: projectId,
        scope_mode: 'selected',
        character_ids: selectedCharacterIds,
        world_bible_refs: selectedWorldRefs,
        continuity_thread_ids: [],
        arc_ids: [],
        mythos_ids: selectedMythosIds,
        pattern_ids: selectedPatternIds,
        include_relationships: true,
        include_unresolved_questions: true,
        include_contradictions_as_forbidden: true,
      },
      canon_policy: {
        locked_character_fields: ['character.display_name', 'character.voice_notes'],
        locked_world_fields: ['world_bible.title', 'world_bible.canonical_facts'],
        allowed_character_changes: [],
        allowed_world_changes: [],
        forbidden_contradictions: annotations
          .filter((item) => item.annotation_kind === 'forbidden_contradiction')
          .map((item) => item.note || `${item.target_kind}.${item.field_path}`),
        continuity_strictness: 'repair_once',
      },
      generation_brief_template: generationBrief,
      selected_annotation_ids: annotations.map((item) => item.annotation_id),
      status: 'draft',
    });
  };

  const handleSubmitGeneration = async () => {
    await onSubmitGeneration({
      source_project_id: projectId,
      mode: 'same_project_side_story',
      destination: {
        destination_kind: 'same_project',
        target_project_id: projectId,
      },
      canon_scope: {
        source_project_id: projectId,
        scope_mode: 'selected',
        character_ids: selectedCharacterIds,
        world_bible_refs: selectedWorldRefs,
        continuity_thread_ids: [],
        arc_ids: [],
        mythos_ids: selectedMythosIds,
        pattern_ids: selectedPatternIds,
        include_relationships: true,
        include_unresolved_questions: true,
        include_contradictions_as_forbidden: true,
      },
      generation_brief: generationBrief,
      target_chapter_count: 8,
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => setActiveTab('overview')}>Overview</button>
        <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => setActiveTab('mythos')}>Mythos</button>
        <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => setActiveTab('patterns')}>Patterns</button>
        <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => setActiveTab('packet')}>Packet Preview</button>
      </div>

      <CanonOverviewPanel
        characterCount={characters.length}
        worldCount={worldEntries.length}
        mythosCount={mythosEntries.length}
        patternCount={patternEntries.length}
        annotationCount={annotations.length}
      />

      {activeTab === 'mythos' && (
        <MythosLibraryWorkspace
          entries={mythosEntries}
          selectedMythosIds={selectedMythosIds}
          onToggleUse={(mythosId) => setSelectedMythosIds(toggleString(selectedMythosIds, mythosId))}
          onDeleteEntry={onDeleteMythosEntry}
        />
      )}

      {activeTab === 'patterns' && (
        <PatternLibraryWorkspace
          entries={patternEntries}
          selectedPatternIds={selectedPatternIds}
          onToggleUse={(patternId) => setSelectedPatternIds(toggleString(selectedPatternIds, patternId))}
          onDeleteEntry={onDeletePatternEntry}
        />
      )}

      {activeTab === 'packet' && <CanonPacketPreview packet={packetPreview} />}
      {activeTab === 'overview' && (
        <>
      <div className="rounded-md border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="text-base font-semibold text-slate-900">Canon Workshop</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="text-sm text-slate-700">
            Profile Name
            <input
              className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
              value={profileName}
              onChange={(event) => setProfileName(event.target.value)}
            />
          </label>
          <label className="text-sm text-slate-700">
            Active Profile
            <select
              className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
              value={selectedProfileId}
              onChange={(event) => setSelectedProfileId(event.target.value)}
            >
              <option value="">None</option>
              {profiles.map((profile) => (
                <option key={profile.profile_id} value={profile.profile_id}>
                  {profile.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="text-sm text-slate-700 block">
          Generation Brief
          <textarea
            className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm min-h-20"
            value={generationBrief}
            onChange={(event) => setGenerationBrief(event.target.value)}
          />
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-md border border-slate-200 bg-white p-3">
          <h3 className="text-sm font-semibold mb-2">Characters</h3>
          <div className="space-y-1 max-h-48 overflow-auto">
            {characters.map((item) => (
              <label key={item.character_id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedCharacterIds.includes(item.character_id)}
                  onChange={() => setSelectedCharacterIds(toggleString(selectedCharacterIds, item.character_id))}
                />
                <span>{item.display_name}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-3">
          <h3 className="text-sm font-semibold mb-2">World Entries</h3>
          <div className="space-y-1 max-h-48 overflow-auto">
            {worldEntries.map((item) => (
              <label key={`${item.entry_type}:${item.title}`} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedWorldRefs.some((ref) => ref.entry_type === item.entry_type && ref.title === item.title)}
                  onChange={() => setSelectedWorldRefs(toggleWorldRef(item))}
                />
                <span>{item.entry_type}: {item.title}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-3">
          <h3 className="text-sm font-semibold mb-2">Mythos</h3>
          <div className="space-y-1 max-h-48 overflow-auto">
            {mythosEntries.map((item) => (
              <label key={item.mythos_id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedMythosIds.includes(item.mythos_id)}
                  onChange={() => setSelectedMythosIds(toggleString(selectedMythosIds, item.mythos_id))}
                />
                <span>{item.entry_type}: {item.name}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="rounded-md border border-slate-200 bg-white p-3">
          <h3 className="text-sm font-semibold mb-2">Patterns</h3>
          <div className="space-y-1 max-h-48 overflow-auto">
            {patternEntries.map((item) => (
              <label key={item.pattern_id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedPatternIds.includes(item.pattern_id)}
                  onChange={() => setSelectedPatternIds(toggleString(selectedPatternIds, item.pattern_id))}
                />
                <span>{item.pattern_type}: {item.name}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 bg-white p-4 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded bg-slate-900 text-white px-3 py-1.5 text-sm"
          onClick={handleSaveProfile}
        >
          Save Profile
        </button>
        <button
          type="button"
          className="rounded bg-slate-700 text-white px-3 py-1.5 text-sm disabled:opacity-50"
          disabled={!selectedProfileId}
          onClick={() => void onPreviewPacket(selectedProfileId)}
        >
          Preview Packet
        </button>
        <button
          type="button"
          className="rounded bg-indigo-700 text-white px-3 py-1.5 text-sm"
          onClick={handleSubmitGeneration}
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
        profiles={profiles}
        selectedProfileId={selectedProfileId}
        onSelect={setSelectedProfileId}
      />
      <CanonProfileEditor
        projectId={projectId}
        selectedProfile={profiles.find((item) => item.profile_id === selectedProfileId) || null}
        onCreateProfile={async (request) => {
          await onSaveProfile(request);
        }}
        onSubmitGeneration={onSubmitGeneration}
      />
      <CanonSelectionDrawer onGenerate={handleSubmitGeneration} onFork={handleSubmitGeneration} />
      </>
      )}

      {packetPreview && (
        <div className="rounded-md border border-indigo-200 bg-indigo-50 p-4">
          <h3 className="text-sm font-semibold text-indigo-900">Packet Preview</h3>
          <div className="mt-2 text-xs text-indigo-900 grid grid-cols-2 md:grid-cols-4 gap-2">
            <span>Characters: {packetPreview.characters.length}</span>
            <span>World: {packetPreview.world_bible.length}</span>
            <span>Mythos: {packetPreview.mythos_entries.length}</span>
            <span>Patterns: {packetPreview.pattern_entries.length}</span>
          </div>
        </div>
      )}
    </div>
  );
}
