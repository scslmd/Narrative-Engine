import { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, Users, Globe, GitBranch, Settings, ListTree, FileText } from 'lucide-react';
import { useGuidedSetupStore } from '../../stores/guidedSetupStore';
import type { CategoryProgress, GuidedCharacter, GuidedWorldEntry, GuidedArc, GuidedSequence, GuidedChapter } from '../../services/guidedSetup';

interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
  isOpen?: boolean | undefined;
  onToggle?: (isOpen: boolean) => void;
  completeness?: number;
}

function CollapsibleSection({ title, icon, defaultOpen = false, children, isOpen: isOpenProp, onToggle, completeness }: CollapsibleSectionProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const isControlled = isOpenProp !== undefined;
  const isOpen = isOpenProp ?? internalOpen;

  const handleClick = () => {
    if (isControlled) {
      onToggle?.(!isOpen);
    } else {
      setInternalOpen(!internalOpen);
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg mb-2">
      <button
        onClick={handleClick}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg"
      >
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        <div className="flex items-center gap-2">
          {completeness !== undefined && (
            <div className="w-10 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                role="progressbar"
                aria-valuenow={Math.round(completeness * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${title} ${Math.round(completeness * 100)}% complete`}
                data-testid="completeness-bar"
                className={`h-full rounded-full transition-all duration-300 ${
                  completeness >= 0.7
                    ? 'bg-emerald-500'
                    : completeness >= 0.3
                      ? 'bg-amber-500'
                      : 'bg-gray-400 dark:bg-gray-500'
                }`}
                style={{ width: `${Math.round(completeness * 100)}%` }}
              />
            </div>
          )}
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>
      {isOpen && <div className="px-3 pb-2">{children}</div>}
    </div>
  );
}

function FieldRow({ label, value, editable = false, onChange }: {
  label: string;
  value: string | string[];
  editable?: boolean;
  onChange?: (value: string) => void;
}) {
  const displayValue = Array.isArray(value) ? value.join(', ') : value;
  if (!displayValue) return null;

  return (
    <div className="flex items-start gap-2 py-1 text-sm">
      <span className="text-gray-500 dark:text-gray-400 min-w-[120px] shrink-0">{label}:</span>
      {editable && onChange ? (
        <input
          type="text"
          value={displayValue}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 bg-transparent border-b border-gray-200 dark:border-gray-700 focus:border-violet-500 outline-none text-gray-800 dark:text-gray-200"
        />
      ) : (
        <span className="text-gray-800 dark:text-gray-200">{displayValue}</span>
      )}
    </div>
  );
}

function CharacterCard({ char }: { char: GuidedCharacter }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 mb-1 text-sm">
      <div className="font-medium text-gray-800 dark:text-gray-200">
        {char.name} <span className="text-gray-400">({char.role})</span>
      </div>
      {char.external_goal && (
        <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">Goal: {char.external_goal}</div>
      )}
      {char.fatal_flaw && (
        <div className="text-gray-600 dark:text-gray-400 text-xs">Flaw: {char.fatal_flaw}</div>
      )}
    </div>
  );
}

function WorldCard({ entry }: { entry: GuidedWorldEntry }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 mb-1 text-sm">
      <div className="font-medium text-gray-800 dark:text-gray-200">
        [{entry.entry_type}] {entry.title}
      </div>
      {entry.summary && (
        <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">{entry.summary}</div>
      )}
    </div>
  );
}

function ArcCard({ arc }: { arc: GuidedArc }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 mb-1 text-sm">
      <div className="font-medium text-gray-800 dark:text-gray-200">
        {arc.character_name} <span className="text-gray-400">({arc.arc_type})</span>
      </div>
      {arc.summary && (
        <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">{arc.summary}</div>
      )}
    </div>
  );
}

function MissingFieldTags({ fields }: { fields: string[] }) {
  if (fields.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1 mb-2 px-1">
      {fields.map(f => (
        <span key={f} data-testid="missing-field-tag" className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
          {f}
        </span>
      ))}
    </div>
  );
}

interface FieldPreviewProps {
  categoryProgress?: CategoryProgress[];
}

export function FieldPreview({ categoryProgress }: FieldPreviewProps): React.ReactElement {
  const { accumulatedFields, updateFields } = useGuidedSetupStore();
  const { config, foundation, characters, world_bible, arcs, sequences, chapters } = accumulatedFields;

  const getCompleteness = (category: string): number | undefined => {
    if (!categoryProgress) return undefined;
    const cp = categoryProgress.find(c => c.category === category);
    return cp?.completeness;
  };

  const getMissingFields = (category: string): string[] => {
    if (!categoryProgress) return [];
    const cp = categoryProgress.find(c => c.category === category);
    return cp?.fields_missing || [];
  };

  // Auto-open when data first appears, respect user collapse
  const [seqOpen, setSeqOpen] = useState(sequences.length > 0);
  const [chOpen, setChOpen] = useState(chapters.length > 0);
  const [seqCollapsed, setSeqCollapsed] = useState(false);
  const [chCollapsed, setChCollapsed] = useState(false);

  const handleSeqToggle = (open: boolean) => {
    setSeqOpen(open);
    if (!open) setSeqCollapsed(true);
  };
  const handleChToggle = (open: boolean) => {
    setChOpen(open);
    if (!open) setChCollapsed(true);
  };

  const finalSeqOpen = seqCollapsed ? seqOpen : sequences.length > 0;
  const finalChOpen = chCollapsed ? chOpen : chapters.length > 0;

  return (
    <div className="h-full overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900">
      <CollapsibleSection title="Project Config" icon={<Settings className="w-4 h-4" />} defaultOpen completeness={getCompleteness('config')}>
        <FieldRow label="Name" value={config.project_name} editable onChange={(v) => updateFields({ config: { project_name: v } })} />
        <FieldRow label="Genre" value={config.genre} editable onChange={(v) => updateFields({ config: { genre: v } })} />
        <FieldRow label="Tone" value={config.tone_profile} />
        <FieldRow label="POV" value={config.pov} />
        <FieldRow label="Structure" value={config.story_structure} />
        <FieldRow label="Language" value={config.primary_language} />
        {config.constraints.length > 0 && <FieldRow label="Constraints" value={config.constraints} />}
      </CollapsibleSection>
      <MissingFieldTags fields={getMissingFields('config')} />

      <CollapsibleSection title="Foundation" icon={<BookOpen className="w-4 h-4" />} defaultOpen completeness={getCompleteness('foundation')}>
        <FieldRow label="Premise" value={foundation.premise_text} />
        <FieldRow label="Logline" value={foundation.logline} />
        <FieldRow label="Theme" value={foundation.thematic_spine} />
        <FieldRow label="Audience" value={foundation.target_audience} />
      </CollapsibleSection>
      <MissingFieldTags fields={getMissingFields('foundation')} />

      <CollapsibleSection title={`Characters (${characters.length})`} icon={<Users className="w-4 h-4" />} completeness={getCompleteness('characters')}>
        {characters.length === 0 && <p className="text-sm text-gray-400">No characters yet</p>}
        {characters.map((c, i) => <CharacterCard key={i} char={c} />)}
      </CollapsibleSection>
      <MissingFieldTags fields={getMissingFields('characters')} />

      <CollapsibleSection title={`World (${world_bible.length})`} icon={<Globe className="w-4 h-4" />} completeness={getCompleteness('world_bible')}>
        {world_bible.length === 0 && <p className="text-sm text-gray-400">No world entries yet</p>}
        {world_bible.map((w, i) => <WorldCard key={i} entry={w} />)}
      </CollapsibleSection>
      <MissingFieldTags fields={getMissingFields('world_bible')} />

      <CollapsibleSection title={`Arcs (${arcs.length})`} icon={<GitBranch className="w-4 h-4" />} completeness={getCompleteness('arcs')}>
        {arcs.length === 0 && <p className="text-sm text-gray-400">No arcs yet</p>}
        {arcs.map((a, i) => <ArcCard key={i} arc={a} />)}
      </CollapsibleSection>
      <MissingFieldTags fields={getMissingFields('arcs')} />

      <CollapsibleSection
        title={`Sequences (${sequences.length})`}
        icon={<ListTree className="w-4 h-4" />}
        isOpen={finalSeqOpen}
        onToggle={handleSeqToggle}
      >
        {sequences.length === 0 && <p className="text-sm text-gray-400">No sequences yet</p>}
        {sequences.map((s, i) => <SequenceCard key={i} seq={s} />)}
      </CollapsibleSection>

      <CollapsibleSection
        title={`Chapters (${chapters.length})`}
        icon={<FileText className="w-4 h-4" />}
        isOpen={finalChOpen}
        onToggle={handleChToggle}
      >
        {chapters.length === 0 && <p className="text-sm text-gray-400">No chapters yet</p>}
        {chapters.map((c, i) => <ChapterCard key={i} ch={c} />)}
      </CollapsibleSection>
    </div>
  );
}

function SequenceCard({ seq }: { seq: GuidedSequence }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 mb-1 text-sm">
      <div className="font-medium text-gray-800 dark:text-gray-200">
        {seq.title} <span className="text-gray-400">({seq.chapter_ids.length} chapters)</span>
      </div>
      {seq.summary && (
        <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">{seq.summary}</div>
      )}
    </div>
  );
}

function ChapterCard({ ch }: { ch: GuidedChapter }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 mb-1 text-sm">
      <div className="font-medium text-gray-800 dark:text-gray-200">
        {ch.title} <span className="text-gray-400">[{ch.position}]</span>
      </div>
      {ch.summary && (
        <div className="text-gray-600 dark:text-gray-400 text-xs mt-1">{ch.summary}</div>
      )}
      {ch.objective && (
        <div className="text-gray-600 dark:text-gray-400 text-xs">Objective: {ch.objective}</div>
      )}
    </div>
  );
}
