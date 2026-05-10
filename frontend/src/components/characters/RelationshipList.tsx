import { useState, useMemo } from 'react';
import type { CharacterProfile, RelationshipEdge } from '../../types/characters';
import { RelationshipEditModal } from './RelationshipEditModal';
import {
  Users,
  Heart,
  Sword,
  BookOpen,
  Shield,
  Trash2,
  MapPin,
  AlertCircle,
  Compass,
  Pencil,
} from 'lucide-react';

interface RelationshipListProps {
  relationships: RelationshipEdge[];
  characterNames: Record<string, string>;
  characters?: CharacterProfile[];
  onDeleteRelationship?: (edgeId: string) => void | Promise<void>;
  onUpdateRelationship?: (edgeId: string, updates: {
    relation_kind?: string;
    summary?: string;
    tension?: string | null;
    notes?: string | null;
  }) => void | Promise<void>;
  className?: string;
}

const RELATION_KIND_STYLES: Record<string, { color: string; bg: string; icon: typeof Users }> = {
  'ALLY': { color: '#059669', bg: 'bg-emerald-50 dark:bg-emerald-900/20', icon: Users },
  'ALLIED': { color: '#059669', bg: 'bg-emerald-50 dark:bg-emerald-900/20', icon: Users },
  'ENEMY': { color: '#dc2626', bg: 'bg-red-50 dark:bg-red-900/20', icon: Sword },
  'FOE': { color: '#dc2626', bg: 'bg-red-50 dark:bg-red-900/20', icon: Sword },
  'ENEMIES': { color: '#dc2626', bg: 'bg-red-50 dark:bg-red-900/20', icon: Sword },
  'LOVER': { color: '#db2777', bg: 'bg-pink-50 dark:bg-pink-900/20', icon: Heart },
  'LOVED': { color: '#db2777', bg: 'bg-pink-50 dark:bg-pink-900/20', icon: Heart },
  'ROMANCE': { color: '#db2777', bg: 'bg-pink-50 dark:bg-pink-900/20', icon: Heart },
  'PARTNER': { color: '#db2777', bg: 'bg-pink-50 dark:bg-pink-900/20', icon: Heart },
  'FRIEND': { color: '#7c3aed', bg: 'bg-violet-50 dark:bg-violet-900/20', icon: Users },
  'FRIENDS': { color: '#7c3aed', bg: 'bg-violet-50 dark:bg-violet-900/20', icon: Users },
  'MENTOR': { color: '#d97706', bg: 'bg-amber-50 dark:bg-amber-900/20', icon: BookOpen },
  'MENTORED': { color: '#d97706', bg: 'bg-amber-50 dark:bg-amber-900/20', icon: BookOpen },
  'TEACHER': { color: '#d97706', bg: 'bg-amber-50 dark:bg-amber-900/20', icon: BookOpen },
  'MASTER': { color: '#d97706', bg: 'bg-amber-50 dark:bg-amber-900/20', icon: BookOpen },
  'FAMILY': { color: '#ea580c', bg: 'bg-orange-50 dark:bg-orange-900/20', icon: Users },
  'SIBLING': { color: '#ea580c', bg: 'bg-orange-50 dark:bg-orange-900/20', icon: Users },
  'PARENT': { color: '#ea580c', bg: 'bg-orange-50 dark:bg-orange-900/20', icon: Users },
  'CHILD': { color: '#ea580c', bg: 'bg-orange-50 dark:bg-orange-900/20', icon: Users },
  'RELATIVE': { color: '#ea580c', bg: 'bg-orange-50 dark:bg-orange-900/20', icon: Users },
  'RIVAL': { color: '#e11d48', bg: 'bg-rose-50 dark:bg-rose-900/20', icon: Shield },
  'COMPETITOR': { color: '#e11d48', bg: 'bg-rose-50 dark:bg-rose-900/20', icon: Shield },
  'MERCENARY': { color: '#0891b2', bg: 'bg-cyan-50 dark:bg-cyan-900/20', icon: Sword },
  'GUARDIAN': { color: '#0d9488', bg: 'bg-teal-50 dark:bg-teal-900/20', icon: Shield },
  'PROTECTOR': { color: '#0d9488', bg: 'bg-teal-50 dark:bg-teal-900/20', icon: Shield },
  'SUBORDINATE': { color: '#9333ea', bg: 'bg-purple-50 dark:bg-purple-900/20', icon: Users },
  'SERVANT': { color: '#9333ea', bg: 'bg-purple-50 dark:bg-purple-900/20', icon: Users },
  'WORLD': { color: '#475569', bg: 'bg-slate-50 dark:bg-slate-900/20', icon: MapPin },
  'OTHER': { color: '#4b5563', bg: 'bg-gray-50 dark:bg-gray-800/50', icon: Compass },
};

function getStyleForKind(kind: string) {
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
  return { color: '#4b5563', bg: 'bg-gray-50 dark:bg-gray-800/50', icon: Compass };
}

export function RelationshipList({
  relationships,
  characterNames,
  characters = [],
  onDeleteRelationship,
  onUpdateRelationship,
  className = '',
}: RelationshipListProps) {
  const [editingEdge, setEditingEdge] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const editingRel = useMemo(
    () => relationships.find((r) => r.edge_id === editingEdge) ?? null,
    [relationships, editingEdge],
  );

  const sortedRelationships = useMemo(
    () => [...relationships].sort((a, b) => a.relation_kind.localeCompare(b.relation_kind)),
    [relationships],
  );

  if (relationships.length === 0) {
    return (
      <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
        <div className="text-center py-8">
          <div className="mx-auto w-10 h-10 mb-3 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <Users className="w-5 h-5 text-gray-400" />
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">No relationships defined</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Relationships ({relationships.length})
        </h3>
      </div>

      <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-[500px] overflow-y-auto">
        {sortedRelationships.map((rel) => {
          const style = getStyleForKind(rel.relation_kind);
          const Icon = style.icon;
          const sourceName = characterNames[rel.source_character_id] ?? rel.source_character_id;
          const targetName = characterNames[rel.target_character_id] ?? rel.target_character_id;

          return (
            <div
              key={rel.edge_id}
              className="group px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${style.bg}`}>
                  <Icon className="w-3 h-3" style={{ color: style.color }} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-xs font-medium text-gray-800 dark:text-gray-200">
                      {sourceName}
                    </span>
                    <span className="text-xs text-gray-400 dark:text-gray-500">—</span>
                    <span className="text-xs font-medium text-gray-800 dark:text-gray-200">
                      {targetName}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span
                      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${style.bg} border-gray-200 dark:border-gray-700`}
                      style={{ color: style.color }}
                    >
                      {rel.relation_kind}
                    </span>
                    {rel.tension && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400">
                        <AlertCircle className="w-2.5 h-2.5" />
                        {rel.tension}
                      </span>
                    )}
                  </div>

                  {rel.summary && (
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1.5 line-clamp-2">
                      {rel.summary}
                    </p>
                  )}

                  {rel.notes && (
                    <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1 italic">
                      {rel.notes}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  {onUpdateRelationship && (
                    <button
                      onClick={() => setEditingEdge(rel.edge_id)}
                      className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                      title="Edit relationship"
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {onDeleteRelationship && (
                    <button
                      onClick={async () => await onDeleteRelationship(rel.edge_id)}
                      className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      title="Delete relationship"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {editingRel && (
        <RelationshipEditModal
          relationship={editingRel}
          characters={characters}
          isSaving={isSaving}
          isDeleting={isDeleting}
          isOpen={!!editingRel}
          onClose={() => setEditingEdge(null)}
          onSave={async (edgeId, data) => {
            if (onUpdateRelationship) {
              setIsSaving(true);
              try {
                await onUpdateRelationship(edgeId, data);
                setEditingEdge(null);
              } finally {
                setIsSaving(false);
              }
            }
          }}
          onDelete={async (edgeId) => {
            if (onDeleteRelationship) {
              setIsDeleting(true);
              try {
                await onDeleteRelationship(edgeId);
                setEditingEdge(null);
              } finally {
                setIsDeleting(false);
              }
            }
          }}
        />
      )}
    </div>
  );
}
