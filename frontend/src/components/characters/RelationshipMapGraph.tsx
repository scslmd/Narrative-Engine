import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import type { RelationshipEdge, CharacterProfile } from '../../types/characters';
import {
  X,
  AlertCircle,
  Users,
  Heart,
  Sword,
  BookOpen,
  Zap,
  Mountain,
  Shield,
  Compass,
} from 'lucide-react';

interface RelationshipMapGraphProps {
  characters: CharacterProfile[];
  relationships: RelationshipEdge[];
  onDeleteRelationship?: (edgeId: string) => void;
  className?: string;
}

interface GraphNode {
  id: string;
  name: string;
  role: string;
  x: number;
  y: number;
  connections: number;
}

interface GraphEdge {
  id: string;
  sourceId: string;
  targetId: string;
  relationKind: string;
  summary: string;
  tension: string | null;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  controlX: number;
  controlY: number;
}

const RELATION_KIND_STYLES: Record<string, { color: string; icon: typeof Users }> = {
  'ALLY': { color: '#10b981', icon: Users },
  'ALLIED': { color: '#10b981', icon: Users },
  'ENEMY': { color: '#ef4444', icon: Sword },
  'FOE': { color: '#ef4444', icon: Sword },
  'ENEMIES': { color: '#ef4444', icon: Sword },
  'LOVER': { color: '#ec4899', icon: Heart },
  'LOVED': { color: '#ec4899', icon: Heart },
  'ROMANCE': { color: '#ec4899', icon: Heart },
  'PARTNER': { color: '#ec4899', icon: Heart },
  'FRIEND': { color: '#8b5cf6', icon: Users },
  'FRIENDS': { color: '#8b5cf6', icon: Users },
  'MENTOR': { color: '#f59e0b', icon: BookOpen },
  'MENTORED': { color: '#f59e0b', icon: BookOpen },
  'TEACHER': { color: '#f59e0b', icon: BookOpen },
  'MASTER': { color: '#f59e0b', icon: BookOpen },
  'FAMILY': { color: '#f97316', icon: Users },
  'SIBLING': { color: '#f97316', icon: Users },
  'PARENT': { color: '#f97316', icon: Users },
  'CHILD': { color: '#f97316', icon: Users },
  'RELATIVE': { color: '#f97316', icon: Users },
  'RIVAL': { color: '#f43f5e', icon: Shield },
  'COMPETITOR': { color: '#f43f5e', icon: Shield },
  'MERCENARY': { color: '#06b6d4', icon: Zap },
  'GUARDIAN': { color: '#14b8a6', icon: Shield },
  'PROTECTOR': { color: '#14b8a6', icon: Shield },
  'SUBORDINATE': { color: '#a855f7', icon: Users },
  'SERVANT': { color: '#a855f7', icon: Users },
  'WORLD': { color: '#64748b', icon: Mountain },
  'OTHER': { color: '#6b7280', icon: Compass },
};

function getStyleForRelationKind(kind: string) {
  const normalized = kind.toUpperCase();
  if (RELATION_KIND_STYLES[normalized]) {
    return RELATION_KIND_STYLES[normalized];
  }
  if (normalized.includes('ALLY') || normalized.includes('ALLIED')) {
    return RELATION_KIND_STYLES['ALLY'];
  }
  if (normalized.includes('ENEMY') || normalized.includes('FOE')) {
    return RELATION_KIND_STYLES['ENEMY'];
  }
  if (normalized.includes('LOVER') || normalized.includes('LOVE')) {
    return RELATION_KIND_STYLES['LOVER'];
  }
  if (normalized.includes('FRIEND')) {
    return RELATION_KIND_STYLES['FRIEND'];
  }
  if (normalized.includes('MENTOR') || normalized.includes('TEACH')) {
    return RELATION_KIND_STYLES['MENTOR'];
  }
  if (normalized.includes('FAMILY') || normalized.includes('PARENT') || normalized.includes('CHILD') || normalized.includes('SIBLING')) {
    return RELATION_KIND_STYLES['FAMILY'];
  }
  if (normalized.includes('RIVAL') || normalized.includes('COMPETE')) {
    return RELATION_KIND_STYLES['RIVAL'];
  }
  if (normalized.includes('GUARDIAN') || normalized.includes('PROTECT')) {
    return RELATION_KIND_STYLES['GUARDIAN'];
  }
  return { color: '#6b7280', icon: Compass };
}

function computeLayout(
  nodes: GraphNode[],
  width: number,
  height: number,
): GraphNode[] {
  if (nodes.length <= 1) {
    return nodes.map((node) => ({
      ...node,
      x: width / 2,
      y: height / 2,
    }));
  }

  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.35;
  const sorted = [...nodes].sort((a, b) => b.connections - a.connections);

  return sorted.map((node, i) => {
    const angle = (2 * Math.PI * i) / sorted.length - Math.PI / 2;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });
}

function computeEdges(
  relationships: RelationshipEdge[],
  nodes: Map<string, GraphNode>,
): GraphEdge[] {
  const edges: GraphEdge[] = [];
  for (const rel of relationships) {
    const source = nodes.get(rel.source_character_id);
    const target = nodes.get(rel.target_character_id);
    if (!source || !target) continue;

    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;

    const curvature = 0.2;
    const midX = (source.x + target.x) / 2;
    const midY = (source.y + target.y) / 2;
    const perpX = -dy / dist;
    const perpY = dx / dist;
    const curveOffset = dist * curvature;

    let controlX = midX + perpX * curveOffset;
    let controlY = midY + perpY * curveOffset;

    for (const existing of edges) {
      if (
        (existing.sourceId === rel.source_character_id && existing.targetId === rel.target_character_id) ||
        (existing.sourceId === rel.target_character_id && existing.targetId === rel.source_character_id)
      ) {
        controlX = midX - perpX * curveOffset;
        controlY = midY - perpY * curveOffset;
      }
    }

    edges.push({
      id: rel.edge_id,
      sourceId: rel.source_character_id,
      targetId: rel.target_character_id,
      relationKind: rel.relation_kind,
      summary: rel.summary,
      tension: rel.tension,
      sourceX: source.x,
      sourceY: source.y,
      targetX: target.x,
      targetY: target.y,
      controlX,
      controlY,
    });
  }
  return edges;
}

const NODE_RADIUS = 28;
const NODE_STROKE = 2;

export function RelationshipMapGraph({
  characters,
  relationships,
  onDeleteRelationship,
  className = '',
}: RelationshipMapGraphProps) {
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const characterMap = useMemo(() => {
    const map = new Map<string, CharacterProfile>();
    for (const char of characters) {
      map.set(char.character_id, char);
    }
    return map;
  }, [characters]);

  const graphNodes = useMemo(() => {
    const involvedIds = new Set<string>();
    for (const rel of relationships) {
      involvedIds.add(rel.source_character_id);
      involvedIds.add(rel.target_character_id);
    }

    const nodes: GraphNode[] = [];
    for (const id of involvedIds) {
      const char = characterMap.get(id);
      if (!char) continue;
      const connections = relationships.filter(
        (r) => r.source_character_id === id || r.target_character_id === id,
      ).length;
      nodes.push({
        id: char.character_id,
        name: char.display_name,
        role: char.role_in_story,
        connections,
        x: 0,
        y: 0,
      });
    }

    return computeLayout(nodes, dimensions.width, dimensions.height);
  }, [characterMap, relationships, dimensions]);

  const nodeMap = useMemo(() => {
    const map = new Map<string, GraphNode>();
    for (const node of graphNodes) {
      map.set(node.id, node);
    }
    return map;
  }, [graphNodes]);

  const graphEdges = useMemo(
    () => computeEdges(relationships, nodeMap),
    [relationships, nodeMap],
  );

  const handleDeleteEdge = useCallback(
    (edgeId: string, e: React.MouseEvent) => {
      e.stopPropagation();
      onDeleteRelationship?.(edgeId);
    },
    [onDeleteRelationship],
  );

  const isSubGraph = characters.length > graphNodes.length;

  if (relationships.length === 0) {
    return (
      <div
        ref={containerRef}
        className={`relative flex items-center justify-center bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 ${className}`}
      >
        <div className="text-center py-12">
          <div className="mx-auto w-12 h-12 mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <Users className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">No relationships defined yet</p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-1 max-w-sm mx-auto">
            Create relationships between characters to visualize how they connect in your story.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`relative bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}
    >
      <svg
        width="100%"
        height="100%"
        className="absolute inset-0"
        style={{ minHeight: 300 }}
      >
        <defs>
          {Array.from(new Set(relationships.map((r) => r.relation_kind))).map((kind) => {
            const { color } = getStyleForRelationKind(kind as string);
            return (
              <marker
                key={`arrow-${kind}`}
                id={`arrow-${kind}`}
                viewBox="0 0 10 10"
                refX="28"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
              </marker>
            );
          })}
        </defs>

        {graphEdges.map((edge) => {
          const { color, icon: Icon } = getStyleForRelationKind(edge.relationKind);
          const isHovered = hoveredEdge === edge.id;
          const edgeColor = isHovered ? color : `${color}99`;
          const strokeWidth = isHovered ? 2.5 : 1.5;
          const d = `M ${edge.sourceX} ${edge.sourceY} Q ${edge.controlX} ${edge.controlY} ${edge.targetX} ${edge.targetY}`;

          return (
            <g key={edge.id}>
              <path
                d={d}
                fill="none"
                stroke={edgeColor}
                strokeWidth={strokeWidth}
                onMouseEnter={() => setHoveredEdge(edge.id)}
                onMouseLeave={() => setHoveredEdge(null)}
                className="cursor-pointer transition-all"
              />
              {isHovered && (
                <g>
                  <path
                    d={d}
                    fill="none"
                    stroke={color}
                    strokeWidth={4}
                    opacity={0.15}
                    className="pointer-events-none"
                  />
                  {onDeleteRelationship && (
                    <g
                      transform={`translate(${edge.controlX}, ${edge.controlY - 12})`}
                      className="cursor-pointer"
                      onClick={(e) => handleDeleteEdge(edge.id, e)}
                    >
                      <rect
                        x="-10"
                        y="-10"
                        width="20"
                        height="20"
                        rx="4"
                        fill="#ef4444"
                        className="hover:opacity-80 transition-opacity"
                      />
                      <X className="w-3 h-3 text-white absolute" style={{ top: 4, left: 4 }} />
                    </g>
                  )}
                </g>
              )}
              <g
                transform={`translate(${(edge.sourceX + edge.targetX) / 2}, ${(edge.sourceY + edge.targetY) / 2})`}
                className="pointer-events-none"
              >
                <foreignObject width="100" height="40" x="-50" y="-20">
                  <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-white/90 dark:bg-gray-800/90 shadow-sm border border-gray-200/50">
                    <Icon className="w-2.5 h-2.5" style={{ color }} />
                    <span className="text-[8px] font-medium text-gray-600 dark:text-gray-300 whitespace-nowrap">
                      {edge.relationKind}
                    </span>
                  </div>
                </foreignObject>
              </g>
            </g>
          );
        })}

        {graphNodes.map((node) => {
          const isHovered = hoveredNode === node.id;
          const isDimmed = hoveredNode !== null && !isHovered && !graphEdges.some(
            (e) =>
              ((e.sourceId === hoveredNode && e.targetId === node.id) ||
                (e.targetId === hoveredNode && e.sourceId === node.id)),
          );

          return (
            <g
              key={node.id}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              className="cursor-pointer"
            >
              <circle
                cx={node.x}
                cy={node.y}
                r={NODE_RADIUS}
                fill={isHovered ? '#f1f5f9' : '#ffffff'}
                stroke={isDimmed ? '#e2e8f0' : '#cbd5e1'}
                strokeWidth={NODE_STROKE}
                className="transition-all"
                style={{ opacity: isDimmed ? 0.5 : 1 }}
              />
              <text
                x={node.x}
                y={node.y + 1}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-xs font-semibold fill-gray-800 dark:fill-gray-200 pointer-events-none select-none"
                style={{ fontSize: '10px', opacity: isDimmed ? 0.5 : 1 }}
              >
                {node.name.length > 10 ? node.name.slice(0, 9) + '\u2026' : node.name}
              </text>
              <text
                x={node.x}
                y={node.y + NODE_RADIUS + 14}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-[8px] fill-gray-400 dark:fill-gray-500 pointer-events-none select-none"
                style={{ fontSize: '8px', opacity: isDimmed ? 0.3 : 1 }}
              >
                {node.role.length > 14 ? node.role.slice(0, 13) + '\u2026' : node.role}
              </text>
            </g>
          );
        })}
      </svg>

      {isSubGraph && (
        <div className="absolute top-3 left-3 px-2.5 py-1 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md">
          <div className="flex items-center gap-1.5">
            <AlertCircle className="w-3 h-3 text-amber-500" />
            <span className="text-xs text-amber-700 dark:text-amber-400">
              Showing {graphNodes.length} of {characters.length} characters
            </span>
          </div>
        </div>
      )}

      <div className="absolute bottom-3 left-3 flex flex-wrap gap-1.5">
        {Array.from(new Set(relationships.map((r) => r.relation_kind)))
          .slice(0, 8)
          .map((kind) => {
            const { color, icon: Icon } = getStyleForRelationKind(kind as string);
            return (
              <div
                key={kind}
                className="flex items-center gap-1 px-2 py-0.5 bg-white/90 dark:bg-gray-800/90 rounded-full border border-gray-200/50 shadow-sm"
              >
                <Icon className="w-2.5 h-2.5" style={{ color }} />
                <span className="text-[9px] text-gray-600 dark:text-gray-300 whitespace-nowrap">
                  {kind}
                </span>
              </div>
            );
          })}
      </div>

      {hoveredEdge && (
        <EdgeTooltip edge={graphEdges.find((e) => e.id === hoveredEdge)!} />
      )}
    </div>
  );
}

function EdgeTooltip({ edge }: { edge: GraphEdge }) {
  const { color } = getStyleForRelationKind(edge.relationKind);

  return (
    <div
      className="fixed z-50 pointer-events-none px-3 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 max-w-xs"
      style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-xs font-semibold text-gray-800 dark:text-gray-200">{edge.relationKind}</span>
      </div>
      <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3">{edge.summary}</p>
      {edge.tension && (
        <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1 italic">
          Tension: {edge.tension}
        </p>
      )}
    </div>
  );
}
