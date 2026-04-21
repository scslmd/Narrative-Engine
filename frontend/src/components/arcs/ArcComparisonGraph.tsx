import { useMemo, useState } from 'react';
import type { ArcComparisonRecord, ArcCandidate } from '../../types/arcs';
import {
  GitCompareArrowsIcon,
  Award,
  Sparkles,
} from 'lucide-react';

interface ArcComparisonGraphProps {
  comparisons: ArcComparisonRecord[];
  className?: string;
}

interface CandidateNode {
  candidate: ArcCandidate;
  rank: number;
  score: [number, number, number, number];
  notes: string[];
  x: number;
  y: number;
  isSelected: boolean;
}

const SCORE_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];
const SCORE_LABELS = ['Relevance', 'Originality', 'Feasibility', 'Impact'];

const scoreColor = (index: number) => SCORE_COLORS[index % SCORE_COLORS.length];
const scoreLabel = (index: number) => SCORE_LABELS[index % SCORE_LABELS.length];

function computeLayout(
  candidates: CandidateNode[],
  width: number,
  height: number,
): CandidateNode[] {
  if (candidates.length <= 1) {
    return candidates.map((c) => ({ ...c, x: width / 2, y: height / 2 }));
  }

  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.32;
  const sorted = [...candidates].sort((a, b) => a.rank - b.rank);

  return sorted.map((node, i) => {
    const angle = (2 * Math.PI * i) / sorted.length - Math.PI / 2;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });
}

function ScoreBar({ value, max, color, label }: {
  value: number;
  max: number;
  color: string;
  label: string;
}) {
  const percentage = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-gray-500 dark:text-gray-400 w-20 shrink-0 truncate">{label}</span>
      <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] font-medium text-gray-700 dark:text-gray-300 w-6 text-right">
        {value}
      </span>
    </div>
  );
}

function CandidateCard({
  candidate,
  rank,
  isSelected,
  x,
  y,
}: {
  candidate: ArcCandidate;
  rank: number;
  score?: [number, number, number, number];
  isSelected: boolean;
  x: number;
  y: number;
}) {
  const displayName = candidate.name.length > 12 ? candidate.name.slice(0, 11) + '\u2026' : candidate.name;

  return (
    <g
      transform={`translate(${x}, ${y})`}
      className="cursor-pointer"
    >
      <circle
        r={40}
        fill={isSelected ? '#f0fdf4' : '#ffffff'}
        stroke={isSelected ? '#16a34a' : '#e2e8f0'}
        strokeWidth={isSelected ? 3 : 1.5}
        className="transition-all"
      />
      {rank <= 3 && (
        <g transform="translate(0, -45)">
          <rect
            x="-10"
            y="-10"
            width="20"
            height="20"
            rx="4"
            className="bg-gradient-to-br from-amber-400 to-amber-500"
          />
          <text
            x="0"
            y="4"
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-sm font-bold fill-white pointer-events-none select-none"
            style={{ fontSize: '11px' }}
          >
            #{rank}
          </text>
        </g>
      )}

      <foreignObject width="80" height="60" x="-40" y="-15">
        <div className="flex flex-col items-center gap-0.5 px-1">
          <span className="text-xs font-semibold text-gray-800 dark:text-gray-200 text-center leading-tight line-clamp-2">
            {displayName}
          </span>
          <div className="flex items-center gap-0.5">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: scoreColor(i) }}
              />
            ))}
          </div>
        </div>
      </foreignObject>
    </g>
  );
}

function ComparisonEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
}: {
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  rank?: number;
}) {
  return (
    <line
      x1={sourceX}
      y1={sourceY}
      x2={targetX}
      y2={targetY}
      stroke="#cbd5e1"
      strokeWidth={1}
      strokeDasharray="4 2"
      opacity={0.5}
    />
  );
}

export function ArcComparisonGraph({
  comparisons,
  className = '',
}: ArcComparisonGraphProps) {
  const [selectedComparisonId, setSelectedComparisonId] = useState<string>(
    comparisons.length > 0 ? comparisons[comparisons.length - 1].comparison_id : '',
  );
  const [containerSize, setContainerSize] = useState({ width: 600, height: 400 });
  const containerRef = useMemo(() => ({ current: null as HTMLDivElement | null }), []);

  const selectedComparison = useMemo(() => {
    if (comparisons.length === 0) return null;
    return comparisons.find((c) => c.comparison_id === selectedComparisonId)
      ?? comparisons[comparisons.length - 1];
  }, [comparisons, selectedComparisonId]);

  const nodes = useMemo(() => {
    if (!selectedComparison) return [] as CandidateNode[];
    const nodes: CandidateNode[] = selectedComparison.ranked_candidates.map((rc: { candidate: ArcCandidate; rank: number; score: [number, number, number, number]; notes: string[] }) => ({
      candidate: rc.candidate,
      rank: rc.rank,
      score: rc.score,
      notes: rc.notes,
      x: 0,
      y: 0,
      isSelected: rc.rank === 1,
    }));
    return computeLayout(nodes, containerSize.width, containerSize.height);
  }, [selectedComparison, containerSize]);

  const maxScore = useMemo(() => {
    if (nodes.length === 0) return 1;
    let max = 0;
    for (const node of nodes) {
      for (const s of node.score) {
        if (s > max) max = s;
      }
    }
    return max || 1;
  }, [nodes]);

  if (comparisons.length === 0) {
    return (
      <div
        ref={(el) => { containerRef.current = el; }}
        className={`relative flex items-center justify-center bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 ${className}`}
      >
        <div className="text-center py-12">
          <div className="mx-auto w-12 h-12 mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <GitCompareArrowsIcon className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">No arc comparisons yet</p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1 max-w-sm mx-auto">
            Arc comparisons will appear here once candidates are scored and ranked.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitCompareArrowsIcon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Arc Comparison
          </h3>
        </div>

        {comparisons.length > 1 && (
          <select
            value={selectedComparisonId}
            onChange={(e) => setSelectedComparisonId(e.target.value)}
            className="text-xs px-2 py-1 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {comparisons.map((c) => (
              <option key={c.comparison_id} value={c.comparison_id}>
                Comparison #{c.comparison_id.split('-').pop()?.slice(0, 6) ?? c.comparison_id}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="relative">
        <svg
          ref={(el) => { if (el) setContainerSize({ width: el.clientWidth, height: el.clientHeight }); }}
          width="100%"
          style={{ height: 300, minHeight: 250 }}
        >
          {nodes.map((node, i) => {
            const nextNode = nodes[(i + 1) % nodes.length];
            return (
              <ComparisonEdge
                key={`edge-${node.candidate.arc_id}`}
                sourceX={node.x}
                sourceY={node.y}
                targetX={nextNode.x}
                targetY={nextNode.y}
                rank={node.rank}
              />
            );
          })}

          {nodes.map((node) => (
            <CandidateCard
              key={node.candidate.arc_id}
              candidate={node.candidate}
              rank={node.rank}
              score={node.score}
              isSelected={node.isSelected}
              x={node.x}
              y={node.y}
            />
          ))}

          <g transform={`translate(${containerSize.width / 2}, ${containerSize.height - 15})`}>
            <text
              textAnchor="middle"
              className="text-[9px] fill-gray-400 dark:fill-gray-500 pointer-events-none select-none"
            >
              Ranked by weighted score
            </text>
          </g>
        </svg>
      </div>

      <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 space-y-2 max-h-40 overflow-y-auto">
        {nodes.map((node) => (
          <div key={node.candidate.arc_id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50">
            <div className={`flex items-center justify-center w-6 h-6 rounded-full shrink-0 text-xs font-bold ${
              node.rank === 1 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
              node.rank === 2 ? 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400' :
              node.rank === 3 ? 'bg-amber-50 text-amber-800 dark:bg-amber-900/20 dark:text-amber-500' :
              'bg-gray-50 text-gray-500 dark:bg-gray-800 dark:text-gray-500'
            }`}>
              {node.rank}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                  {node.candidate.name}
                </span>
                {node.isSelected && (
                  <span className="flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    <Award className="w-2.5 h-2.5" />
                    Selected
                  </span>
                )}
              </div>
              <div className="mt-1 space-y-0.5">
                {node.score.map((s, i) => (
                  <ScoreBar
                    key={i}
                    value={s}
                    max={maxScore}
                    color={scoreColor(i)}
                    label={scoreLabel(i)}
                  />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedComparison!.review_notes.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-start gap-2">
            <Sparkles className="w-3 h-3 text-gray-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-gray-500 dark:text-gray-400 italic">
              {selectedComparison!.review_notes.join(' ')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
