import { useMemo, useState } from 'react';
import type { ArcStageMap, ArcCandidate } from '../../types/arcs';
import { LayersIcon, ArrowRight } from 'lucide-react';

interface ArcStageMapFlowProps {
  stageMaps: ArcStageMap[];
  candidates: ArcCandidate[];
  selectedArcId: string | null;
  className?: string;
}

const NARRATIVE_STAGE_COLORS: Record<string, { color: string; bg: string; darkBg: string }> = {
  'exposition':     { color: '#3b82f6', bg: '#eff6ff', darkBg: '#1e3a5f' },
  'rising_action':  { color: '#f59e0b', bg: '#fffbeb', darkBg: '#5c3d10' },
  'rising action':  { color: '#f59e0b', bg: '#fffbeb', darkBg: '#5c3d10' },
  'complication':   { color: '#ef4444', bg: '#fef2f2', darkBg: '#5c1a1a' },
  'crisis':         { color: '#ef4444', bg: '#fef2f2', darkBg: '#5c1a1a' },
  'climax':         { color: '#dc2626', bg: '#fef2f2', darkBg: '#6b1a1a' },
  'falling_action': { color: '#8b5cf6', bg: '#f5f3ff', darkBg: '#3b1f6e' },
  'falling action': { color: '#8b5cf6', bg: '#f5f3ff', darkBg: '#3b1f6e' },
  'resolution':     { color: '#10b981', bg: '#ecfdf5', darkBg: '#14532d' },
  'denouement':     { color: '#10b981', bg: '#ecfdf5', darkBg: '#14532d' },
  'introduction':   { color: '#6366f1', bg: '#eef2ff', darkBg: '#1e1b4b' },
  'setup':          { color: '#6366f1', bg: '#eef2ff', darkBg: '#1e1b4b' },
  'inciting':       { color: '#f97316', bg: '#fff7ed', darkBg: '#431407' },
  'inciting incident': { color: '#f97316', bg: '#fff7ed', darkBg: '#431407' },
  'inciting_incident': { color: '#f97316', bg: '#fff7ed', darkBg: '#431407' },
  'confrontation':  { color: '#ef4444', bg: '#fef2f2', darkBg: '#5c1a1a' },
  'turning_point':  { color: '#ec4899', bg: '#fdf2f8', darkBg: '#500724' },
  'turning point':  { color: '#ec4899', bg: '#fdf2f8', darkBg: '#500724' },
  'reversal':       { color: '#e11d48', bg: '#fff1f2', darkBg: '#500724' },
  'twist':          { color: '#e11d48', bg: '#fff1f2', darkBg: '#500724' },
  'cliffhanger':    { color: '#dc2626', bg: '#fef2f2', darkBg: '#500724' },
  'interlude':      { color: '#64748b', bg: '#f8fafc', darkBg: '#1e293b' },
  'transition':     { color: '#64748b', bg: '#f8fafc', darkBg: '#1e293b' },
  'prologue':       { color: '#78716c', bg: '#fafaf9', darkBg: '#292524' },
  'epilogue':       { color: '#78716c', bg: '#fafaf9', darkBg: '#292524' },
  'aftermath':      { color: '#10b981', bg: '#ecfdf5', darkBg: '#14532d' },
  'character':      { color: '#22c55e', bg: '#f0fdf4', darkBg: '#14532d' },
  'character_development': { color: '#22c55e', bg: '#f0fdf4', darkBg: '#14532d' },
  'relationship':   { color: '#ec4899', bg: '#fdf2f8', darkBg: '#500724' },
  'world_building': { color: '#8b5cf6', bg: '#f5f3ff', darkBg: '#3b1f6e' },
  'action':         { color: '#ef4444', bg: '#fef2f2', darkBg: '#5c1a1a' },
  'conflict':       { color: '#dc2626', bg: '#fef2f2', darkBg: '#5c1a1a' },
  'theme':          { color: '#14b8a6', bg: '#f0fdfa', darkBg: '#042f2e' },
  'subplot':        { color: '#a855f7', bg: '#faf5ff', darkBg: '#3b0764' },
  'foreshadowing':  { color: '#fbbf24', bg: '#fefce8', darkBg: '#422006' },
  'pov':            { color: '#6366f1', bg: '#eef2ff', darkBg: '#1e1b4b' },
  'setting':        { color: '#0d9488', bg: '#f0fdfa', darkBg: '#042f2e' },
  'time_jump':      { color: '#f59e0b', bg: '#fffbeb', darkBg: '#5c3d10' },
  'time jump':      { color: '#f59e0b', bg: '#fffbeb', darkBg: '#5c3d10' },
  'parallel':       { color: '#a855f7', bg: '#faf5ff', darkBg: '#3b0764' },
  'parallel_story': { color: '#a855f7', bg: '#faf5ff', darkBg: '#3b0764' },
};

const getStageStyle = (kind: string): { color: string; bg: string; darkBg: string } => {
  const normalized = kind.toLowerCase().replace(/[\s-]+/g, '_').trim();
  return NARRATIVE_STAGE_COLORS[normalized] ?? {
    color: '#64748b',
    bg: '#f8fafc',
    darkBg: '#1e293b',
  };
};

const formatKind = (kind: string): string => {
  return kind
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

export function ArcStageMapFlow({
  stageMaps,
  candidates,
  selectedArcId,
  className = '',
}: ArcStageMapFlowProps) {
  const [activeMapIndex, setActiveMapIndex] = useState(0);

  const candidateNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const c of candidates) {
      map[c.arc_id] = c.name;
    }
    return map;
  }, [candidates]);

  const availableMaps = useMemo(() => {
    const maps = stageMaps.map((m) => ({
      ...m,
      name: candidateNameMap[m.arc_id] || m.arc_id,
      isSelected: m.arc_id === selectedArcId,
    }));
    const sorted = [...maps].sort((a, b) => {
      if (a.isSelected && !b.isSelected) return -1;
      if (!a.isSelected && b.isSelected) return 1;
      return a.arc_id.localeCompare(b.arc_id);
    });
    return sorted;
  }, [stageMaps, candidateNameMap, selectedArcId]);

  const [containerSize, setContainerSize] = useState({ width: 600, height: 220 });

  const activeMap = availableMaps[activeMapIndex];
  const isMultiple = availableMaps.length > 1;
  const isActiveSelected = activeMap?.isSelected ?? false;

  const stages = useMemo(() => {
    if (!activeMap) return [];
    return activeMap.stage_kinds.map((kind, order) => ({
      id: `${activeMap.arc_stage_map_id}-stage-${order}`,
      kind,
      ...getStageStyle(kind),
      order,
    }));
  }, [activeMap]);

  if (availableMaps.length === 0 || !activeMap) {
    return (
      <div
        className={`relative flex items-center justify-center bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 ${className}`}
      >
        <div className="text-center py-12">
          <div className="mx-auto w-12 h-12 mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <LayersIcon className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">No stage maps yet</p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1 max-w-sm mx-auto">
            Stage maps will appear once arc candidates are compared and scored.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LayersIcon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Stage Map
          </h3>
          {isActiveSelected && (
            <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              Active
            </span>
          )}
        </div>

        {isMultiple && (
          <select
            value={activeMapIndex}
            onChange={(e) => setActiveMapIndex(Number(e.target.value))}
            className="text-xs px-2 py-1 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {availableMaps.map((m, i) => (
              <option key={m.arc_stage_map_id} value={i}>
                {m.name}
                {m.isSelected ? ' (active)' : ''}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="relative">
        <svg
          ref={(el) => { if (el) setContainerSize({ width: el.clientWidth, height: el.clientHeight }); }}
          width="100%"
          style={{ height: 200, minHeight: 180 }}
          className="overflow-visible"
        >
          {stages.length > 0 && (
            <>
              {stages.map((stage, i) => {
                const totalWidth = stages.length * 110 + (stages.length - 1) * 20;
                const startX = Math.max(30, (containerSize.width - totalWidth) / 2);
                const nodeX = startX + i * (110 + 20);
                const nodeY = containerSize.height / 2 - 30;
                const nextNodeX = i < stages.length - 1
                  ? nodeX + 110 + 20
                  : nodeX + 110 + 10;

                return (
                  <g key={stage.id}>
                    {i < stages.length - 1 && (
                      <g transform={`translate(${nextNodeX - 10}, ${nodeY + 30})`}>
                        <line
                          x1={10}
                          y1={0}
                          x2={80}
                          y2={0}
                          stroke="#cbd5e1"
                          strokeWidth={1.5}
                          className="dark:stroke-gray-600"
                        />
                        <polygon
                          points="80,-5 90,0 80,5"
                          fill="#cbd5e1"
                          className="dark:fill-gray-600"
                        />
                      </g>
                    )}

                    <foreignObject
                      width={110}
                      height={60}
                      x={nodeX}
                      y={nodeY}
                    >
                      <div className="flex flex-col items-center justify-center h-full px-2">
                        <span
                          className="text-[10px] font-semibold text-center leading-tight line-clamp-2 w-full dark:text-gray-200 dark:bg-opacity-80"
                          style={{
                            color: stage.color,
                            backgroundColor: stage.bg,
                          }}
                        >
                          {formatKind(stage.kind)}
                        </span>
                        <span className="text-[8px] text-gray-400 dark:text-gray-500 mt-0.5">
                          #{stage.order + 1}
                        </span>
                      </div>
                    </foreignObject>
                  </g>
                );
              })}

              {activeMap.notes && (
                <g transform={`translate(${containerSize.width / 2}, ${containerSize.height - 12})`}>
                  <text
                    textAnchor="middle"
                    className="text-[9px] fill-gray-400 dark:fill-gray-500 pointer-events-none select-none italic"
                  >
                    {activeMap.notes.length > 80
                      ? `${activeMap.notes.slice(0, 80)}...`
                      : activeMap.notes}
                  </text>
                </g>
              )}
            </>
          )}
        </svg>
      </div>

      {stages.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-800 flex items-center gap-1 flex-wrap">
          {stages.map((stage, i) => (
            <div key={stage.id} className="flex items-center gap-1">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: stage.color }}
              />
              <span className="text-[10px] text-gray-500 dark:text-gray-400">
                {formatKind(stage.kind)}
              </span>
              {i < stages.length - 1 && (
                <ArrowRight className="w-3 h-3 text-gray-300 dark:text-gray-600 ml-1" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
