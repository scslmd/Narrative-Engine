import { useState } from 'react';
import type { FoundationRecord } from '../../types/foundation';

interface FoundationEditorProps {
  projectId: string;
  foundation?: FoundationRecord;
  onSave?: (foundation: Partial<FoundationRecord>) => void;
  onCancel?: () => void;
}

export function FoundationEditor({ foundation, onSave, onCancel }: FoundationEditorProps) {
  const [coreConcept, setCoreConcept] = useState(foundation?.core_concept || '');
  const [protagonist, setProtagonist] = useState(foundation?.protagonist || '');
  const [antagonist, setAntagonist] = useState(foundation?.antagonist || '');
  const [centralConflict, setCentralConflict] = useState(foundation?.central_conflict || '');
  const [setting, setSetting] = useState(foundation?.setting || '');
  const [theme, setTheme] = useState(foundation?.theme || '');
  const [tone, setTone] = useState(foundation?.tone || '');
  const [premise, setPremise] = useState(foundation?.premise || '');
  const [logline, setLogline] = useState(foundation?.logline || '');

  const handleSave = () => {
    onSave?.({
      core_concept: coreConcept,
      protagonist,
      antagonist,
      central_conflict: centralConflict,
      setting,
      theme,
      tone,
      premise,
      logline,
    });
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Foundation</h2>
            <p className="text-sm text-gray-500 mt-1">
              Define the core elements of your story
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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

      {/* Editor content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Core Concept */}
          <Section title="Core Concept" description="The central idea or concept of your story">
            <textarea
              value={coreConcept}
              onChange={(e) => setCoreConcept(e.target.value)}
              placeholder="What is your story fundamentally about? What's the central idea?"
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          {/* Premise */}
          <Section title="Premise" description="The foundational situation or scenario">
            <textarea
              value={premise}
              onChange={(e) => setPremise(e.target.value)}
              placeholder="What is the basic situation or scenario that drives your story?"
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          {/* Logline */}
          <Section title="Logline" description="A one-sentence summary of your story">
            <textarea
              value={logline}
              onChange={(e) => setLogline(e.target.value)}
              placeholder="In one sentence: Who is the protagonist, what do they want, and what stands in their way?"
              className="w-full h-20 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Protagonist */}
            <Section title="Protagonist" description="The main character">
              <textarea
                value={protagonist}
                onChange={(e) => setProtagonist(e.target.value)}
                placeholder="Who is your main character? What do they want?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            {/* Antagonist */}
            <Section title="Antagonist" description="The opposing force">
              <textarea
                value={antagonist}
                onChange={(e) => setAntagonist(e.target.value)}
                placeholder="Who or what opposes your protagonist?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>
          </div>

          {/* Central Conflict */}
          <Section title="Central Conflict" description="The main struggle or tension">
            <textarea
              value={centralConflict}
              onChange={(e) => setCentralConflict(e.target.value)}
              placeholder="What is the main conflict or struggle in your story?"
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          {/* Setting */}
          <Section title="Setting" description="Where and when the story takes place">
            <textarea
              value={setting}
              onChange={(e) => setSetting(e.target.value)}
              placeholder="Where and when does your story take place?"
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Theme */}
            <Section title="Theme" description="The underlying message or meaning">
              <textarea
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                placeholder="What is your story really about? What's the deeper meaning?"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            {/* Tone */}
            <Section title="Tone" description="The mood and atmosphere">
              <textarea
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                placeholder="What is the mood and atmosphere of your story? (e.g., dark, hopeful, comedic)"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>
          </div>
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
