import { useEffect, useState } from 'react';
import type { FoundationProfile, FoundationRevision, FoundationReviewCue } from '../../types/foundation';

interface FoundationEditorProps {
  projectId: string;
  foundation?: FoundationProfile;
  onSave?: (foundation: Partial<FoundationProfile>) => void;
  onCancel?: () => void;
  revisions?: FoundationRevision[];
  reviewCues?: FoundationReviewCue[];
}

export function FoundationEditor({ projectId, foundation, onSave, onCancel, revisions, reviewCues }: FoundationEditorProps) {
  const [activeTab, setActiveTab] = useState<'editor' | 'history' | 'cues'>('editor');
  const [premise, setPremise] = useState(foundation?.premise || '');
  const [logline, setLogline] = useState(foundation?.logline || '');
  const [thematicSpine, setThematicSpine] = useState(foundation?.thematic_spine || '');
  const [emotionalPromise, setEmotionalPromise] = useState(foundation?.emotional_promise || '');
  const [toneAndVoiceDirection, setToneAndVoiceDirection] = useState(foundation?.tone_and_voice_direction || '');
  const [targetAudience, setTargetAudience] = useState(foundation?.target_audience || '');
  const [narrativeConstraints, setNarrativeConstraints] = useState<string[]>(foundation?.narrative_constraints || []);
  const [complexityLevel, setComplexityLevel] = useState(foundation?.complexity_level || '');
  const [successDefinition, setSuccessDefinition] = useState(foundation?.success_definition || '');

  useEffect(() => {
    setPremise(foundation?.premise || '');
    setLogline(foundation?.logline || '');
    setThematicSpine(foundation?.thematic_spine || '');
    setEmotionalPromise(foundation?.emotional_promise || '');
    setToneAndVoiceDirection(foundation?.tone_and_voice_direction || '');
    setTargetAudience(foundation?.target_audience || '');
    setNarrativeConstraints(foundation?.narrative_constraints || []);
    setComplexityLevel(foundation?.complexity_level || '');
    setSuccessDefinition(foundation?.success_definition || '');
  }, [foundation]);

  const handleSave = () => {
    onSave?.({
      project_id: projectId,
      premise,
      logline,
      thematic_spine: thematicSpine,
      emotional_promise: emotionalPromise,
      tone_and_voice_direction: toneAndVoiceDirection,
      target_audience: targetAudience,
      narrative_constraints: narrativeConstraints,
      complexity_level: complexityLevel,
      success_definition: successDefinition,
    });
  };

  const canSave = Boolean(
    premise.trim() &&
      logline.trim() &&
      thematicSpine.trim() &&
      emotionalPromise.trim() &&
      toneAndVoiceDirection.trim() &&
      targetAudience.trim() &&
      complexityLevel.trim() &&
      successDefinition.trim(),
  );

  const handleAddConstraint = () => {
    setNarrativeConstraints([...narrativeConstraints, '']);
  };

  const handleConstraintChange = (index: number, value: string) => {
    const updated = [...narrativeConstraints];
    updated[index] = value;
    setNarrativeConstraints(updated);
  };

  const handleRemoveConstraint = (index: number) => {
    setNarrativeConstraints(narrativeConstraints.filter((_, i) => i !== index));
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-slate-900">
      {/* Header */}
      <div className="p-4 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100">Foundation</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
              Define the core elements of your story
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
                className="px-4 py-2 bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-600"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <button
          onClick={() => setActiveTab('editor')}
          className={`px-4 py-2 text-sm font-medium ${activeTab === 'editor' ? 'border-b-2 border-indigo-500 text-indigo-600' : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100'}`}
        >
          Editor
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 text-sm font-medium ${activeTab === 'history' ? 'border-b-2 border-indigo-500 text-indigo-600' : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100'}`}
        >
          History ({revisions?.length ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('cues')}
          className={`px-4 py-2 text-sm font-medium ${activeTab === 'cues' ? 'border-b-2 border-indigo-500 text-indigo-600' : 'text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100'}`}
        >
          Review Cues ({reviewCues?.length ?? 0})
        </button>
      </div>

      {/* Editor content */}
      {activeTab === 'editor' && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <Section title="Premise" description="The foundational situation or scenario">
              <textarea
                value={premise}
                onChange={(e) => setPremise(e.target.value)}
                placeholder="What is the basic situation or scenario that drives your story?"
                className="w-full h-24 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Logline" description="A one-sentence summary of your story">
              <textarea
                value={logline}
                onChange={(e) => setLogline(e.target.value)}
                placeholder="In one sentence: Who is the protagonist, what do they want, and what stands in their way?"
                className="w-full h-20 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Thematic Spine" description="The central theme or message">
              <textarea
                value={thematicSpine}
                onChange={(e) => setThematicSpine(e.target.value)}
                placeholder="What is your story really about? What's the deeper meaning?"
                className="w-full h-24 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Emotional Promise" description="What readers will feel">
              <textarea
                value={emotionalPromise}
                onChange={(e) => setEmotionalPromise(e.target.value)}
                placeholder="What emotional journey will readers experience?"
                className="w-full h-24 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Tone and Voice Direction" description="The mood and narrative style">
              <textarea
                value={toneAndVoiceDirection}
                onChange={(e) => setToneAndVoiceDirection(e.target.value)}
                placeholder="What is the mood and narrative voice? (e.g., dark and lyrical, light and conversational)"
                className="w-full h-24 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Target Audience" description="Who will read this story">
              <textarea
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="Who is your intended readership?"
                className="w-full h-20 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Complexity Level" description="Narrative complexity">
              <select
                value={complexityLevel}
                onChange={(e) => setComplexityLevel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select complexity level</option>
                <option value="simple">Simple</option>
                <option value="moderate">Moderate</option>
                <option value="complex">Complex</option>
                <option value="very complex">Very Complex</option>
              </select>
            </Section>

            <Section title="Narrative Constraints" description="Guidelines and limitations">
              <div className="space-y-2">
                {narrativeConstraints.map((constraint, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={constraint}
                      onChange={(e) => handleConstraintChange(index, e.target.value)}
                      placeholder={`Constraint ${index + 1}`}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={() => handleRemoveConstraint(index)}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={handleAddConstraint}
                  className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
                >
                  + Add Constraint
                </button>
              </div>
            </Section>

            <Section title="Success Definition" description="What makes this story successful">
              <textarea
                value={successDefinition}
                onChange={(e) => setSuccessDefinition(e.target.value)}
                placeholder="What would make this story a success? What should it achieve?"
                className="w-full h-24 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>
          </div>
        </div>
      )}

      {/* History tab */}
      {activeTab === 'history' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {revisions?.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-slate-400 py-8">No revision history</div>
          ) : (
            revisions?.map((revision) => (
              <div key={revision.revision_id} className="rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-slate-100">{revision.revision_id}</span>
                  <span className="text-xs text-gray-500 dark:text-slate-400">{revision.change_summary ?? 'No summary'}</span>
                </div>
                <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-slate-300">{revision.snapshot?.premise || 'No premise'}</pre>
              </div>
            ))
          )}
        </div>
      )}

      {/* Review Cues tab */}
      {activeTab === 'cues' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {reviewCues?.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-slate-400 py-8">No review cues</div>
          ) : (
            reviewCues?.map((cue, index) => (
            <div key={index} className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/40 p-3">
                 <p className="text-sm font-medium text-amber-900 dark:text-amber-200">{cue.impacted_area}</p>
                 <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">{cue.reason}</p>
              </div>
            ))
          )}
        </div>
      )}
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
    <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg p-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-slate-100">{title}</h3>
        <p className="text-xs text-gray-500 dark:text-slate-400">{description}</p>
      </div>
      {children}
    </div>
  );
}
