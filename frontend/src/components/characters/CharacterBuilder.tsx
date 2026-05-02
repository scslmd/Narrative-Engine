import { useEffect, useState } from 'react';
import type { CharacterProfile } from '../../types/characters';
import type { CanonAnnotation, CanonAnnotationKind } from '../../types/canonCustomization';
import { CanonAnnotationToolbar } from '../canon/CanonAnnotationToolbar';

interface CharacterBuilderProps {
  projectId: string;
  character?: CharacterProfile;
  onSave?: (character: Partial<CharacterProfile>) => void;
  onCancel?: () => void;
  canonAnnotations?: CanonAnnotation[];
  onAnnotateField?: (
    targetId: string,
    fieldPath: string,
    annotationKind: CanonAnnotationKind,
    note: string,
  ) => Promise<void>;
}

export function CharacterBuilder({
  projectId,
  character,
  onSave,
  onCancel,
  canonAnnotations = [],
  onAnnotateField,
}: CharacterBuilderProps) {
  const [characterId, setCharacterId] = useState(character?.character_id || '');
  const [displayName, setDisplayName] = useState(character?.display_name || '');
  const [roleInStory, setRoleInStory] = useState(character?.role_in_story || '');
  const [archetype, setArchetype] = useState(character?.archetype || '');
  const [externalGoal, setExternalGoal] = useState(character?.external_goal || '');
  const [internalNeed, setInternalNeed] = useState(character?.internal_need || '');
  const [misbeliefOrWound, setMisbeliefOrWound] = useState(character?.misbelief_or_wound || '');
  const [coreFear, setCoreFear] = useState(character?.core_fear || '');
  const [primaryStrength, setPrimaryStrength] = useState(character?.primary_strength || '');
  const [fatalFlaw, setFatalFlaw] = useState(character?.fatal_flaw_or_limitation || '');
  const [contradictions, setContradictions] = useState<string[]>(character?.contradictions || []);
  const [backstorySummary, setBackstorySummary] = useState(character?.backstory_summary || '');
  const [voiceNotes, setVoiceNotes] = useState(character?.voice_notes || '');
  const [secrets, setSecrets] = useState<string[]>(character?.secrets || []);
  const [values, setValues] = useState<string[]>(character?.values || []);
  const [taboos, setTaboos] = useState<string[]>(character?.taboos || []);
  const [changeAxis, setChangeAxis] = useState(character?.change_axis || '');
  const [arcStageNotes, setArcStageNotes] = useState<string[]>(character?.arc_stage_notes || []);
  const [continuityFacts, setContinuityFacts] = useState<string[]>(character?.continuity_facts || []);
  const [writerNotes, setWriterNotes] = useState(character?.writer_notes || '');

  useEffect(() => {
    setCharacterId(character?.character_id || '');
    setDisplayName(character?.display_name || '');
    setRoleInStory(character?.role_in_story || '');
    setArchetype(character?.archetype || '');
    setExternalGoal(character?.external_goal || '');
    setInternalNeed(character?.internal_need || '');
    setMisbeliefOrWound(character?.misbelief_or_wound || '');
    setCoreFear(character?.core_fear || '');
    setPrimaryStrength(character?.primary_strength || '');
    setFatalFlaw(character?.fatal_flaw_or_limitation || '');
    setContradictions(character?.contradictions || []);
    setBackstorySummary(character?.backstory_summary || '');
    setVoiceNotes(character?.voice_notes || '');
    setSecrets(character?.secrets || []);
    setValues(character?.values || []);
    setTaboos(character?.taboos || []);
    setChangeAxis(character?.change_axis || '');
    setArcStageNotes(character?.arc_stage_notes || []);
    setContinuityFacts(character?.continuity_facts || []);
    setWriterNotes(character?.writer_notes || '');
  }, [character]);

  const handleSave = () => {
    onSave?.({
      project_id: projectId,
      character_id: characterId.trim(),
      display_name: displayName,
      role_in_story: roleInStory,
      archetype,
      external_goal: externalGoal,
      internal_need: internalNeed,
      misbelief_or_wound: misbeliefOrWound,
      core_fear: coreFear,
      primary_strength: primaryStrength,
      fatal_flaw_or_limitation: fatalFlaw,
      contradictions,
      backstory_summary: backstorySummary,
      voice_notes: voiceNotes,
      secrets,
      values,
      taboos,
      change_axis: changeAxis,
      arc_stage_notes: arcStageNotes,
      continuity_facts: continuityFacts,
      writer_notes: writerNotes || null,
    });
  };

  const canSave = Boolean(
    characterId.trim() &&
      displayName.trim() &&
      roleInStory.trim() &&
      archetype.trim() &&
      externalGoal.trim() &&
      internalNeed.trim() &&
      misbeliefOrWound.trim() &&
      coreFear.trim() &&
      primaryStrength.trim() &&
      fatalFlaw.trim() &&
      backstorySummary.trim() &&
      voiceNotes.trim() &&
      changeAxis.trim(),
  );

  const handleArrayChange = <T,>(
    setter: React.Dispatch<React.SetStateAction<T[]>>,
    index: number,
    value: T,
  ) => {
    setter((prev) => {
      const updated = [...prev];
      updated[index] = value;
      return updated;
    });
  };

  const handleAddArrayItem = (setter: React.Dispatch<React.SetStateAction<string[]>>) => {
    setter((prev) => [...prev, '']);
  };

  const handleRemoveArrayItem = (
    setter: React.Dispatch<React.SetStateAction<string[]>>,
    index: number,
  ) => {
    setter((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {character ? 'Edit Character' : 'New Character'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Build and refine your characters
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={!canSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save
            </button>
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <Section title="Character ID" description="Stable backend identifier for this character">
            <input
              type="text"
              value={characterId}
              onChange={(e) => setCharacterId(e.target.value)}
              placeholder="Enter character id"
              readOnly={Boolean(character)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg disabled:bg-gray-100"
            />
          </Section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Section title="Display Name" description="The character's name">
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter character name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
              />
              {characterId && onAnnotateField && (
                <CanonAnnotationToolbar
                  projectId={projectId}
                  target_kind="character"
                  target_id={characterId}
                  field_path="display_name"
                  annotations={canonAnnotations}
                  onCreate={(_, targetId, fieldPath, annotationKind, note) =>
                    onAnnotateField(targetId, fieldPath, annotationKind, note)
                  }
                />
              )}
            </Section>

            <Section title="Role in Story" description="Character's narrative function">
              <input
                type="text"
                value={roleInStory}
                onChange={(e) => setRoleInStory(e.target.value)}
                placeholder="e.g., Protagonist, Antagonist, Mentor"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </Section>
          </div>

          <Section title="Archetype" description="Character archetype">
            <input
              type="text"
              value={archetype}
              onChange={(e) => setArchetype(e.target.value)}
              placeholder="e.g., The Creator, The Sage, The Hero"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </Section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Section title="External Goal" description="What the character wants">
              <textarea
                value={externalGoal}
                onChange={(e) => setExternalGoal(e.target.value)}
                placeholder="What does this character want to achieve?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Internal Need" description="What the character truly needs">
              <textarea
                value={internalNeed}
                onChange={(e) => setInternalNeed(e.target.value)}
                placeholder="What does this character need for growth?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Section title="Misbelief or Wound" description="The character's limiting belief">
              <textarea
                value={misbeliefOrWound}
                onChange={(e) => setMisbeliefOrWound(e.target.value)}
                placeholder="What false belief holds this character back?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Core Fear" description="What the character fears most">
              <textarea
                value={coreFear}
                onChange={(e) => setCoreFear(e.target.value)}
                placeholder="What is this character's deepest fear?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Section title="Primary Strength" description="The character's greatest asset">
              <textarea
                value={primaryStrength}
                onChange={(e) => setPrimaryStrength(e.target.value)}
                placeholder="What is this character's greatest strength?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Fatal Flaw" description="The character's limiting weakness">
              <textarea
                value={fatalFlaw}
                onChange={(e) => setFatalFlaw(e.target.value)}
                placeholder="What flaw holds this character back?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>
          </div>

          <Section title="Contradictions" description="Paradoxical traits">
            <div className="space-y-2">
              {contradictions.map((item, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={item}
                    onChange={(e) => handleArrayChange(setContradictions, index, e.target.value)}
                    placeholder={`Contradiction ${index + 1}`}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleRemoveArrayItem(setContradictions, index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                onClick={() => handleAddArrayItem(setContradictions)}
                className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
              >
                + Add Contradiction
              </button>
            </div>
          </Section>

          <Section title="Backstory Summary" description="The character's past">
            <textarea
              value={backstorySummary}
              onChange={(e) => setBackstorySummary(e.target.value)}
              placeholder="What happened in this character's past?"
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          <Section title="Voice Notes" description="How the character speaks">
            <textarea
              value={voiceNotes}
              onChange={(e) => setVoiceNotes(e.target.value)}
              placeholder="How does this character speak? What's their voice like?"
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
            {characterId && onAnnotateField && (
              <CanonAnnotationToolbar
                projectId={projectId}
                target_kind="character"
                target_id={characterId}
                field_path="voice_notes"
                annotations={canonAnnotations}
                onCreate={(_, targetId, fieldPath, annotationKind, note) =>
                  onAnnotateField(targetId, fieldPath, annotationKind, note)
                }
              />
            )}
          </Section>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Section title="Secrets" description="Hidden truths">
              <div className="space-y-2">
                {secrets.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) => handleArrayChange(setSecrets, index, e.target.value)}
                      placeholder="Secret"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <button
                      onClick={() => handleRemoveArrayItem(setSecrets, index)}
                      className="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAddArrayItem(setSecrets)}
                  className="px-2 py-1 text-blue-600 hover:bg-blue-50 rounded text-xs"
                >
                  + Add
                </button>
              </div>
            </Section>

            <Section title="Values" description="What the character holds dear">
              <div className="space-y-2">
                {values.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) => handleArrayChange(setValues, index, e.target.value)}
                      placeholder="Value"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <button
                      onClick={() => handleRemoveArrayItem(setValues, index)}
                      className="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAddArrayItem(setValues)}
                  className="px-2 py-1 text-blue-600 hover:bg-blue-50 rounded text-xs"
                >
                  + Add
                </button>
              </div>
            </Section>

            <Section title="Taboos" description="What the character rejects">
              <div className="space-y-2">
                {taboos.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) => handleArrayChange(setTaboos, index, e.target.value)}
                      placeholder="Taboo"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <button
                      onClick={() => handleRemoveArrayItem(setTaboos, index)}
                      className="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAddArrayItem(setTaboos)}
                  className="px-2 py-1 text-blue-600 hover:bg-blue-50 rounded text-xs"
                >
                  + Add
                </button>
              </div>
            </Section>
          </div>

          <Section title="Change Axis" description="Character arc trajectory">
            <textarea
              value={changeAxis}
              onChange={(e) => setChangeAxis(e.target.value)}
              placeholder="How does this character change? From what to what?"
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          <Section title="Arc Stage Notes" description="Key moments in character development">
            <div className="space-y-2">
              {arcStageNotes.map((item, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={item}
                    onChange={(e) => handleArrayChange(setArcStageNotes, index, e.target.value)}
                    placeholder={`Arc stage ${index + 1}`}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleRemoveArrayItem(setArcStageNotes, index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                onClick={() => handleAddArrayItem(setArcStageNotes)}
                className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
              >
                + Add Stage
              </button>
            </div>
          </Section>

          <Section title="Continuity Facts" description="Details to track">
            <div className="space-y-2">
              {continuityFacts.map((item, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={item}
                    onChange={(e) => handleArrayChange(setContinuityFacts, index, e.target.value)}
                    placeholder="Continuity fact"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleRemoveArrayItem(setContinuityFacts, index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                onClick={() => handleAddArrayItem(setContinuityFacts)}
                className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
              >
                + Add Fact
              </button>
            </div>
            {characterId && onAnnotateField && (
              <CanonAnnotationToolbar
                projectId={projectId}
                target_kind="character"
                target_id={characterId}
                field_path="continuity_facts"
                annotations={canonAnnotations}
                onCreate={(_, targetId, fieldPath, annotationKind, note) =>
                  onAnnotateField(targetId, fieldPath, annotationKind, note)
                }
              />
            )}
          </Section>

          <Section title="Writer Notes" description="Private notes for the author">
            <textarea
              value={writerNotes}
              onChange={(e) => setWriterNotes(e.target.value)}
              placeholder="Private notes about this character..."
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>
        </div>
      </div>
    </div>
  );
}

interface SectionProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

function Section({ title, description, children }: SectionProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      {children}
    </div>
  );
}
