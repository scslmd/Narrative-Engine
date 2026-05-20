import { ChevronDown, ChevronRight } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { ArcCandidate } from '../../types/arcs';

interface ArcBuilderProps {
  projectId: string;
  arc?: ArcCandidate;
  onSave?: (arc: Partial<ArcCandidate>) => void;
  onCancel?: () => void;
}

export function ArcBuilder({
  projectId,
  arc,
  onSave,
  onCancel,
}: ArcBuilderProps) {
  const [arcId, setArcId] = useState(arc?.arc_id || '');
  const [name, setName] = useState(arc?.name || '');
  const [summary, setSummary] = useState(arc?.summary || '');
  const [stageMapNotes, setStageMapNotes] = useState<string[]>(arc?.stage_map_notes || []);
  const [fitNotes, setFitNotes] = useState<string[]>(arc?.fit_notes || []);
  const [tags, setTags] = useState<string[]>(arc?.tags || []);

  useEffect(() => {
    setArcId(arc?.arc_id || '');
    setName(arc?.name || '');
    setSummary(arc?.summary || '');
    setStageMapNotes(arc?.stage_map_notes || []);
    setFitNotes(arc?.fit_notes || []);
    setTags(arc?.tags || []);
  }, [arc]);

  const handleSave = () => {
    onSave?.({
      project_id: projectId,
      arc_id: arcId.trim(),
      name,
      summary,
      stage_map_notes: stageMapNotes,
      fit_notes: fitNotes,
      tags,
    });
  };

  const canSave = Boolean(arcId.trim() && name.trim() && summary.trim());

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
    <div className="flex flex-col h-full bg-gray-50 dark:bg-slate-900">
      <div className="p-4 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100">
              {arc ? 'Edit Arc' : 'New Arc'}
            </h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
              Define character arcs and story threads
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
        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <span className="text-red-500">*</span> Required
          </span>
          <span className="flex items-center gap-1">
            <span className="text-amber-500">⚡</span> Used by story generation
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Core fields */}
          <ArcSectionGroup title="Core" description="Arc identity">
            <ArcSection title="Arc ID" badge="required">
              <input
                type="text"
                value={arcId}
                onChange={(e) => setArcId(e.target.value)}
                placeholder="Enter arc id"
                readOnly={Boolean(arc)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg disabled:bg-gray-100 dark:disabled:bg-slate-700"
              />
            </ArcSection>

            <ArcSection title="Name" badge="required">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., The Hero's Journey, Redemption Arc"
                className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
              />
            </ArcSection>

            <ArcSection title="Summary" badge="required">
              <textarea
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="What is this arc about? What transforms?"
                className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </ArcSection>
          </ArcSectionGroup>

          {/* Structure fields */}
          <ArcCollapsibleSection
            title="Structure"
            description="Key turning points and narrative progression"
            defaultExpanded
          >
            <ArcSection title="Stage Map Notes" badge="recommended" description="Key moments in arc progression">
              <div className="space-y-2">
                {stageMapNotes.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) => handleArrayChange(setStageMapNotes, index, e.target.value)}
                      placeholder={`Stage ${index + 1}`}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={() => handleRemoveArrayItem(setStageMapNotes, index)}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAddArrayItem(setStageMapNotes)}
                  className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
                >
                  + Add Stage
                </button>
              </div>
            </ArcSection>
          </ArcCollapsibleSection>

          {/* Metadata fields */}
          <ArcCollapsibleSection
            title="Metadata"
            description="Fit assessment and organization tags"
          >
            <ArcSection title="Fit Notes" description="How well this arc fits the story">
              <div className="space-y-2">
                {fitNotes.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) => handleArrayChange(setFitNotes, index, e.target.value)}
                      placeholder={`Fit note ${index + 1}`}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={() => handleRemoveArrayItem(setFitNotes, index)}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAddArrayItem(setFitNotes)}
                  className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
                >
                  + Add Note
                </button>
              </div>
            </ArcSection>

            <ArcSection title="Tags" description="Organization labels">
              <div className="space-y-2">
                {tags.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) => handleArrayChange(setTags, index, e.target.value)}
                      placeholder="Tag"
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <button
                      onClick={() => handleRemoveArrayItem(setTags, index)}
                      className="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAddArrayItem(setTags)}
                  className="px-2 py-1 text-blue-600 hover:bg-blue-50 rounded text-xs"
                >
                  + Add
                </button>
              </div>
            </ArcSection>
          </ArcCollapsibleSection>
        </div>
      </div>
    </div>
  );
}

/* ── Section Group (always visible) ── */

interface ArcSectionGroupProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

function ArcSectionGroup({ title, description, children }: ArcSectionGroupProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-baseline gap-2">
        <h2 className="text-base font-semibold text-gray-900 dark:text-slate-100">{title}</h2>
        <p className="text-xs text-gray-500 dark:text-slate-400">{description}</p>
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

/* ── Collapsible Section Group ── */

interface ArcCollapsibleSectionProps {
  title: string;
  description: string;
  defaultExpanded?: boolean;
  children: React.ReactNode;
}

function ArcCollapsibleSection({ title, description, defaultExpanded = false, children }: ArcCollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full text-left"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-gray-500 dark:text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-500 dark:text-slate-400" />
        )}
        <h2 className="text-base font-semibold text-gray-900 dark:text-slate-100">{title}</h2>
        <p className="text-xs text-gray-500 dark:text-slate-400">{description}</p>
      </button>
      {isExpanded && <div className="space-y-3">{children}</div>}
    </div>
  );
}

/* ── Individual Field Section ── */

interface ArcSectionProps {
  title: string;
  description?: string;
  badge?: 'required' | 'recommended';
  children: React.ReactNode;
}

function ArcSection({ title, description, badge, children }: ArcSectionProps) {
  const badgeElement =
    badge === 'required' ? (
      <span className="text-red-500 text-xs ml-1">*</span>
    ) : badge === 'recommended' ? (
      <span className="text-amber-500 text-xs ml-1" title="Used by story generation">⚡</span>
    ) : null;

  return (
    <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg p-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-slate-100 flex items-center">
          {title}
          {badgeElement}
        </h3>
        {description && <p className="text-xs text-gray-500 dark:text-slate-400">{description}</p>}
      </div>
      {children}
    </div>
  );
}
