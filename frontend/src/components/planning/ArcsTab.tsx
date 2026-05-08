import { ArcStageMapFlow } from '../arcs/ArcStageMapFlow';
import { ArcComparisonGraph } from '../arcs/ArcComparisonGraph';
import { Section, EmptyState, WorkspaceStatus } from './ui';
import { useIsDark } from './hooks';
import type { ArcCandidate, ArcSelection, ArcStageMap, ArcComparisonRecord, ArcSelectionUpdateRequest } from '../../types/arcs';

const STAGE_OPTIONS = [
  'exposition',
  'inciting_incident',
  'rising_action',
  'complication',
  'crisis',
  'climax',
  'falling_action',
  'resolution',
];

export interface ArcsTabProps {
  data: {
    arcCandidates: ArcCandidate[];
    arcSelections: ArcSelection[];
    arcStageMaps: ArcStageMap[];
    arcComparisons: ArcComparisonRecord[];
    selectedArcId: string | null;
    candidatesLoading: boolean;
    selectionsLoading: boolean;
    stageMapsLoading: boolean;
    comparisonsLoading: boolean;
  };
  actions: {
    onUpdateSelection: (selectionId: string, data: ArcSelectionUpdateRequest) => void;
    onDeleteSelection: (selectionId: string) => void;
  };
  tab: {
    arcCandidateCreateOpen: boolean;
    arcCandidateCreateId: string;
    arcCandidateCreateName: string;
    arcCandidateCreateSummary: string;
    stageMapCreateOpen: boolean;
    stageMapCreateArcId: string;
    stageMapCreateNotes: string;
    stageMapCreateKinds: string[];
    onCreateArcCandidate: () => void;
    onSetArcCandidateCreateOpen: (open: boolean) => void;
    onSetArcCandidateCreateId: (value: string) => void;
    onSetArcCandidateCreateName: (value: string) => void;
    onSetArcCandidateCreateSummary: (value: string) => void;
    onStageMapCreate: () => void;
    onSetStageMapCreateOpen: (open: boolean) => void;
    onSetStageMapCreateArcId: (value: string) => void;
    onSetStageMapCreateNotes: (value: string) => void;
    onSetStageMapCreateKinds: (kinds: string[]) => void;
    onToggleStageKind: (stage: string) => void;
    onSelectArc: (arcId: string) => void;
    onDeselectArc: () => void;
  };
}

export function ArcsTab({ data, actions, tab }: ArcsTabProps) {
  const isDark = useIsDark();
  const selectClass = `text-xs px-2 py-1.5 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`;
  const inputClass = `text-xs px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`;
  const cardClass = (isSelected: boolean) =>
    `p-3 rounded-lg border ${isSelected
      ? isDark ? 'bg-emerald-950/30 border-emerald-900/50' : 'bg-emerald-50 border-emerald-300'
      : isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
    }`;
  const stageButtonClass = (selected: boolean) =>
    `px-2 py-1 rounded text-xs font-medium transition-colors ${
      selected
        ? isDark ? 'bg-violet-900 text-violet-200 border border-violet-700' : 'bg-violet-100 text-violet-800 border border-violet-300'
        : isDark ? 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700' : 'bg-slate-50 text-slate-500 border border-slate-200 hover:bg-slate-100'
    }`;

  return (
    <>
      <Section title="Selected Arc">
        {data.selectionsLoading ? (
          <WorkspaceStatus title="Loading arc selections" detail="Fetching selected arcs..." />
        ) : data.selectedArcId || data.arcSelections.length > 0 ? (
          <div className="space-y-2">
            {data.arcSelections.map((selection) => {
              const arc = selection.selected_arc;
              return (
                <div key={selection.selection_id} className={`p-4 rounded-lg border ${isDark ? 'bg-emerald-950/30 border-emerald-900/50' : 'bg-emerald-50 border-emerald-200'}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{arc.name || arc.arc_id}</div>
                      {arc.summary && <p className={`text-sm mt-1 ${isDark ? 'text-emerald-300/70' : 'text-emerald-700'}`}>{arc.summary}</p>}
                    </div>
                    <div className="flex gap-1.5 flex-shrink-0">
                      <button
                        onClick={() => actions.onUpdateSelection(selection.selection_id, { comparison_notes: [...(selection.comparison_notes ?? []), 'Updated inline'] })}
                        className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-violet-950 text-violet-300 hover:bg-violet-900' : 'bg-violet-50 text-violet-700 hover:bg-violet-100'}`}
                      >
                        Update
                      </button>
                      <button
                        onClick={() => actions.onDeleteSelection(selection.selection_id)}
                        className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-rose-950 text-rose-300 hover:bg-rose-900' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'}`}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState text="No arc selected. Arc selections define the narrative trajectory for this project." />
        )}
      </Section>

      {data.stageMapsLoading ? (
        <Section title="Stage Map">
          <WorkspaceStatus title="Loading stage maps" detail="Fetching arc stage progression..." />
        </Section>
      ) : tab.stageMapCreateOpen ? (
        <Section title="Stage Map">
          <div className="space-y-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-body">Arc</label>
              <select
                value={tab.stageMapCreateArcId}
                onChange={(e) => tab.onSetStageMapCreateArcId(e.target.value)}
                className={selectClass}
              >
                <option value="">Select an arc candidate...</option>
                {data.arcCandidates.map((c) => (
                  <option key={c.arc_id} value={c.arc_id}>{c.name} ({c.arc_id})</option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-body">Stages</label>
              <div className="flex flex-wrap gap-1.5">
                {STAGE_OPTIONS.map((stage) => (
                  <button
                    key={stage}
                    type="button"
                    onClick={() => tab.onToggleStageKind(stage)}
                    className={stageButtonClass(tab.stageMapCreateKinds.includes(stage))}
                  >
                    {stage.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
              {tab.stageMapCreateKinds.length > 0 && (
                <p className="text-xs text-subtle">
                  Order: {tab.stageMapCreateKinds.map((k) => k.replace(/_/g, ' ')).join(' → ')}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-body">Notes (optional)</label>
              <textarea
                value={tab.stageMapCreateNotes}
                onChange={(e) => tab.onSetStageMapCreateNotes(e.target.value)}
                rows={2}
                placeholder="Stage map notes..."
                className={`text-xs px-2 py-1.5 rounded border resize-none ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={tab.onStageMapCreate}
                disabled={!tab.stageMapCreateArcId || tab.stageMapCreateKinds.length === 0}
                className="text-xs px-2.5 py-1 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40"
              >
                Save Stage Map
              </button>
              <button
                onClick={() => {
                  tab.onSetStageMapCreateOpen(false);
                  tab.onSetStageMapCreateArcId('');
                  tab.onSetStageMapCreateKinds([]);
                  tab.onSetStageMapCreateNotes('');
                }}
                className={`text-xs px-2 py-1 rounded-md ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'}`}
              >
                Cancel
              </button>
            </div>
          </div>
        </Section>
      ) : data.arcStageMaps.length > 0 ? (
        <Section title="Stage Map">
          <ArcStageMapFlow
            stageMaps={data.arcStageMaps}
            candidates={data.arcCandidates}
            selectedArcId={data.selectedArcId}
            className="h-[260px]"
          />
        </Section>
      ) : (
        <Section title="Stage Map">
          <EmptyState text="No stage maps yet. Create one to define the narrative progression for an arc candidate." />
        </Section>
      )}

      {!data.comparisonsLoading && data.arcComparisons.length > 0 && (
        <Section title="Arc Comparisons">
          <ArcComparisonGraph
            comparisons={data.arcComparisons}
            className="h-[420px]"
          />
        </Section>
      )}

      <Section title="Arc Candidates" count={data.arcCandidates.length}>
        <div className="flex justify-end mb-2">
          {!tab.arcCandidateCreateOpen ? (
            <button
              onClick={tab.onCreateArcCandidate}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-violet-950 text-violet-300 hover:bg-violet-900' : 'bg-violet-50 text-violet-700 hover:bg-violet-100'}`}
            >
              + New Arc
            </button>
          ) : (
            <div className="flex flex-col gap-1.5">
              <input type="text" placeholder="Arc ID (e.g. arc-hero)" value={tab.arcCandidateCreateId} onChange={(e) => tab.onSetArcCandidateCreateId(e.target.value)} className={`${inputClass} w-48`} />
              <input type="text" placeholder="Arc name" value={tab.arcCandidateCreateName} onChange={(e) => tab.onSetArcCandidateCreateName(e.target.value)} className={`${inputClass} w-56`} />
              <input type="text" placeholder="Summary (optional)" value={tab.arcCandidateCreateSummary} onChange={(e) => tab.onSetArcCandidateCreateSummary(e.target.value)} className={`${inputClass} w-64`} />
              <div className="flex gap-2">
                <button
                  onClick={tab.onCreateArcCandidate}
                  disabled={!tab.arcCandidateCreateId.trim() || !tab.arcCandidateCreateName.trim()}
                  className="text-xs px-2.5 py-1 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40"
                >
                  Create
                </button>
                <button onClick={() => tab.onSetArcCandidateCreateOpen(false)} className={`text-xs px-2 py-1 rounded-md ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'}`}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
        {data.candidatesLoading ? (
          <WorkspaceStatus title="Loading arc candidates" detail="Fetching all arc candidates..." />
        ) : data.arcCandidates.length === 0 ? (
          <EmptyState text="No arc candidates available. Create one manually or import from foundation/character work." />
        ) : (
          <div className="space-y-2">
            {data.arcCandidates.map((candidate) => {
              const isSelected = data.selectedArcId === candidate.arc_id;
              return (
                <div key={candidate.arc_id} className={cardClass(isSelected)}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{candidate.name}</div>
                      {candidate.summary && <p className="text-sm mt-1 text-body">{candidate.summary}</p>}
                      {isSelected && (
                        <span className={`inline-block mt-2 px-2 py-0.5 text-xs font-medium rounded-full ${isDark ? 'bg-emerald-900/50 text-emerald-300' : 'bg-emerald-100 text-emerald-700'}`}>
                          Selected
                        </span>
                      )}
                    </div>
                    <div className="flex gap-1.5 flex-shrink-0">
                      {isSelected ? (
                        <button
                          onClick={tab.onDeselectArc}
                          className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-rose-950 text-rose-300 hover:bg-rose-900 disabled:opacity-40' : 'bg-rose-50 text-rose-700 hover:bg-rose-100 disabled:opacity-40'}`}
                        >
                          Deselect
                        </button>
                      ) : (
                        <button
                          onClick={() => tab.onSelectArc(candidate.arc_id)}
                          className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-emerald-950 text-emerald-300 hover:bg-emerald-900 disabled:opacity-40' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 disabled:opacity-40'}`}
                        >
                          Select
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Section>
    </>
  );
}
