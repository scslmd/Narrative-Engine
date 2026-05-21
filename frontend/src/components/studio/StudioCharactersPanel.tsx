import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CharacterBuilder } from '../characters/CharacterBuilder';
import { WorkspaceStatus } from '../planning/ui';
import { createCanonAnnotation, getCanonAnnotations } from '../../services/canonCustomization';
import { createCharacter, getCharacter, getCharacters, updateCharacter } from '../../services/characters';
import type { CanonAnnotationKind } from '../../types/canonCustomization';
import type { CharacterProfile, CharacterProfileCreateRequest, CharacterProfileUpdateRequest } from '../../types/characters';

type CharacterEditorMode = 'list' | 'create' | 'edit';

function omitKeys<T extends object>(value: T, keys: string[]): Partial<T> {
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).filter(([key]) => !keys.includes(key)),
  ) as Partial<T>;
}

interface StudioCharactersPanelProps {
  projectId: string;
}

export function StudioCharactersPanel({ projectId }: StudioCharactersPanelProps) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<CharacterEditorMode>('list');
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);

  const charactersQuery = useQuery({
    queryKey: ['studio', 'characters', projectId],
    queryFn: () => getCharacters(projectId),
    enabled: Boolean(projectId),
  });

  const selectedCharacterQuery = useQuery({
    queryKey: ['studio', 'character', projectId, selectedCharacterId],
    queryFn: () => getCharacter(selectedCharacterId || '', projectId),
    enabled: Boolean(projectId) && Boolean(selectedCharacterId) && mode === 'edit',
  });

  const characters = useMemo(
    () => charactersQuery.data ?? [],
    [charactersQuery.data],
  );

  const canonAnnotationsQuery = useQuery({
    queryKey: ['studio', 'canon', 'annotations', projectId, 'characters'],
    queryFn: () => getCanonAnnotations(projectId, { target_kind: 'character' }),
    enabled: Boolean(projectId),
  });

  const canonAnnotationMutation = useMutation({
    mutationFn: createCanonAnnotation,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['studio', 'canon', 'annotations', projectId, 'characters'],
      });
    },
  });

  const handleAnnotateField = async (
    targetId: string,
    fieldPath: string,
    annotationKind: CanonAnnotationKind,
    note: string,
  ) => {
    await canonAnnotationMutation.mutateAsync({
      project_id: projectId,
      target_kind: 'character',
      target_id: targetId,
      field_path: fieldPath,
      annotation_kind: annotationKind,
      note,
    });
  };

  const saveMutation = useMutation({
    mutationFn: (character: Partial<CharacterProfile>) => {
      const payload = omitKeys(character, ['project_id', 'character_id', 'relationship_edges']);
      const characterId = character.character_id;

      if (mode === 'edit' && selectedCharacterId) {
        return updateCharacter(
          selectedCharacterId,
          projectId,
          payload as CharacterProfileUpdateRequest,
        );
      }

      if (!characterId?.trim()) {
        throw new Error('Character ID is required.');
      }

      return createCharacter({
        project_id: projectId,
        character_id: characterId.trim(),
        ...(payload as Omit<CharacterProfileCreateRequest, 'project_id' | 'character_id'>),
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['studio', 'characters', projectId] });
      setMode('list');
      setSelectedCharacterId(null);
    },
  });

  if (charactersQuery.error) {
    return (
      <WorkspaceStatus
        title="Could not load characters"
        detail="Character profiles are unavailable."
        tone="error"
      />
    );
  }

  if (mode === 'list') {
    return (
      <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] p-5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Characters</h2>
            <p className="text-sm mt-0.5 text-slate-500 dark:text-slate-400">
              {characters.length} profiles
            </p>
          </div>
          <button
            onClick={() => {
              setSelectedCharacterId(null);
              setMode('create');
            }}
            className="px-3 py-1.5 bg-gradient-to-r from-pink-500 to-pink-600 text-white text-xs font-medium rounded-lg hover:from-pink-600 hover:to-pink-700 shadow-sm transition-all"
          >
            New Character
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {characters.map((character) => (
            <button
              key={character.character_id}
              onClick={() => {
                setSelectedCharacterId(character.character_id);
                setMode('edit');
              }}
              className="text-left rounded-lg border p-4 cursor-pointer transition-all duration-150 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-pink-300 dark:hover:border-slate-700 hover:shadow-card"
            >
              <h3 className="font-medium text-slate-900 dark:text-slate-100">
                {character.display_name}
              </h3>
              <p className="text-sm mt-1 text-slate-500 dark:text-slate-400">
                {character.role_in_story}
              </p>
            </button>
          ))}
        </div>

        {characters.length === 0 && (
          <div className="text-center py-8 text-sm text-slate-500 dark:text-slate-400">
            No character profiles configured. Create a character to start building the cast.
          </div>
        )}
      </div>
    );
  }

  if (mode === 'create') {
    return (
      <CharacterBuilder
        projectId={projectId}
        onSave={(character) => saveMutation.mutate(character)}
        canonAnnotations={canonAnnotationsQuery.data ?? []}
        onAnnotateField={handleAnnotateField}
        onCancel={() => {
          setMode('list');
          setSelectedCharacterId(null);
        }}
      />
    );
  }

  const selectedCharacter = selectedCharacterId
    ? characters.find((c) => c.character_id === selectedCharacterId)
    : null;

  if (!selectedCharacter && !selectedCharacterQuery.data) {
    return (
      <WorkspaceStatus
        title="Character not found"
        detail="Return to the list and choose another profile."
        tone="error"
      />
    );
  }

  return (
    <CharacterBuilder
      projectId={projectId}
      character={selectedCharacterQuery.data ?? selectedCharacter ?? undefined}
      onSave={(character) => saveMutation.mutate(character)}
      canonAnnotations={canonAnnotationsQuery.data ?? []}
      onAnnotateField={handleAnnotateField}
      onCancel={() => {
        setMode('list');
        setSelectedCharacterId(null);
      }}
    />
  );
}
