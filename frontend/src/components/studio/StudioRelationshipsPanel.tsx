import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { RelationshipEditModal } from '../characters/RelationshipEditModal';
import { RelationshipForm } from '../characters/RelationshipForm';
import { RelationshipList } from '../characters/RelationshipList';
import { RelationshipMapGraph } from '../characters/RelationshipMapGraph';
import { WorkspaceStatus } from '../planning/ui';
import { getCharacters } from '../../services/characters';
import { getRelationships } from '../../services/relationships';
import { useRelationships } from '../../hooks/useRelationships';
import type { RelationshipEdge } from '../../types/characters';

interface StudioRelationshipsPanelProps {
  projectId: string;
}

export function StudioRelationshipsPanel({ projectId }: StudioRelationshipsPanelProps) {
  const queryClient = useQueryClient();
  const [showCreateRelationship, setShowCreateRelationship] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState<RelationshipEdge | null>(null);
  const relationshipHook = useRelationships(projectId);

  const charactersQuery = useQuery({
    queryKey: ['studio', 'relationship-characters', projectId],
    queryFn: () => getCharacters(projectId),
    enabled: Boolean(projectId),
  });

  const relationshipsQuery = useQuery({
    queryKey: ['studio', 'relationships', projectId],
    queryFn: () => getRelationships(projectId),
    enabled: Boolean(projectId),
  });

  const characters = useMemo(
    () => charactersQuery.data ?? [],
    [charactersQuery.data],
  );

  const relationships = useMemo(
    () => relationshipsQuery.data ?? [],
    [relationshipsQuery.data],
  );

  const characterNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const character of characters) {
      map[character.character_id] = character.display_name;
    }
    return map;
  }, [characters]);

  const isLoading = charactersQuery.isLoading || relationshipsQuery.isLoading;
  const error = charactersQuery.error || relationshipsQuery.error;

  if (isLoading) {
    return (
      <WorkspaceStatus
        title="Loading relationships"
        detail="Fetching characters and relationships..."
      />
    );
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load relationships"
        detail="Please try again later."
        tone="error"
      />
    );
  }

  const invalidateStudioQueries = async () => {
    await queryClient.invalidateQueries({ queryKey: ['studio', 'relationships', projectId] });
  };

  return (
     <div className="flex h-full flex-col">
        <div className="flex shrink-0 items-center justify-between px-3 py-2 border-b border-[var(--border-primary)]">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            Relationships
          </h2>
          <button
            type="button"
            onClick={() => setShowCreateRelationship(true)}
            className="px-2 py-0.5 text-[9px] font-medium rounded bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add Relationship
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
          {showCreateRelationship && (
            <RelationshipForm
              characters={characters}
              isSubmitting={relationshipHook.isCreating}
              onSubmit={async (data) => {
                await relationshipHook.createRelationship(data);
                await invalidateStudioQueries();
                setShowCreateRelationship(false);
              }}
              onCancel={() => setShowCreateRelationship(false)}
            />
          )}

          <RelationshipMapGraph
            characters={characters}
            relationships={relationships}
            onDeleteRelationship={async (edgeId) => {
              await relationshipHook.deleteRelationship(edgeId);
              await invalidateStudioQueries();
            }}
            onEditRelationship={(edgeId) =>
              setEditingRelationship(
                relationships.find((r) => r.edge_id === edgeId) ?? null,
              )
            }
            className="h-56"
          />

          <RelationshipList
            relationships={relationships}
            characterNames={characterNameMap}
            onDeleteRelationship={async (edgeId) => {
              await relationshipHook.deleteRelationship(edgeId);
              await invalidateStudioQueries();
            }}
            onUpdateRelationship={(edgeId) =>
              setEditingRelationship(
                relationships.find((r) => r.edge_id === edgeId) ?? null,
              )
            }
          />

          {editingRelationship && (
            <RelationshipEditModal
              isOpen={!!editingRelationship}
              relationship={editingRelationship}
              characters={characters}
              isSaving={relationshipHook.isUpdating}
              isDeleting={relationshipHook.isDeleting}
              onClose={() => setEditingRelationship(null)}
              onSave={async (edgeId, data) => {
                await relationshipHook.updateRelationship(edgeId, data);
                await invalidateStudioQueries();
                setEditingRelationship(null);
              }}
              onDelete={async (edgeId) => {
                await relationshipHook.deleteRelationship(edgeId);
                await invalidateStudioQueries();
                setEditingRelationship(null);
              }}
            />
          )}
        </div>
      </div>
  );
}
