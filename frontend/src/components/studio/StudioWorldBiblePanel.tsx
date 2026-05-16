import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { WorldBibleWorkspace } from '../bible/WorldBibleWorkspace';
import { WorkspaceStatus } from '../planning/ui';
import { createWorldBibleEntry, getWorldBibleEntries, updateWorldBibleEntry } from '../../services/worldBible';
import type { WorldBibleEntry, WorldBibleEntryCreateRequest, WorldBibleEntryUpdateRequest } from '../../types/bible';

interface StudioWorldBiblePanelProps {
  projectId: string;
}

function omitKeys<T extends object>(value: T, keys: string[]): Partial<T> {
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).filter(([key]) => !keys.includes(key)),
  ) as Partial<T>;
}

export function StudioWorldBiblePanel({ projectId }: StudioWorldBiblePanelProps) {
  const queryClient = useQueryClient();

  const { data: entries = [], isLoading, error } = useQuery<WorldBibleEntry[]>({
    queryKey: ['studio', 'world-bible', projectId],
    queryFn: () => getWorldBibleEntries(projectId),
  });

  const addMutation = useMutation({
    mutationFn: (request: WorldBibleEntryCreateRequest) => createWorldBibleEntry(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio', 'world-bible', projectId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (params: {
      entryType: string;
      originalTitle: string;
      updates: WorldBibleEntryUpdateRequest;
    }) =>
      updateWorldBibleEntry(params.entryType, params.originalTitle, projectId, params.updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio', 'world-bible', projectId] });
    },
  });

  if (isLoading) {
    return <WorkspaceStatus title="Loading world bible" detail="Fetching world bible entries." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load world bible"
        detail="World bible entries are unavailable."
        tone="error"
      />
    );
  }

  return (
    <WorldBibleWorkspace
      projectId={projectId}
      entries={entries}
      onEntryAdd={(request) => addMutation.mutate(request)}
      onEntryUpdate={(entry, originalTitle) => {
        const updates = omitKeys(entry, ['entry_id', 'project_id', 'entry_type']);
        updateMutation.mutate({
          entryType: entry.entry_type,
          originalTitle,
          updates,
        });
      }}
      canonAnnotations={[]}
      onAnnotateField={async () => undefined}
    />
  );
}
