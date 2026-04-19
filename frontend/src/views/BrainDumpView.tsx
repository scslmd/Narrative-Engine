import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BrainDumpCanvas } from '../components/braindump/BrainDumpCanvas';
import {
  getBrainDumpSessions,
  createBrainDumpSession,
  updateBrainDumpSession,
  organizeBrainDumpSession,
} from '../services/braindump';
import type { BrainDumpOrganizeResponse } from '../types/braindump';
import { toast } from '../lib/toast';

const QUERY_KEY = ['braindump-sessions'];

export function BrainDumpView() {
  const { projectId } = useParams<{ projectId: string }>();
  const resolvedProjectId = projectId ?? '';
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [organizeResult, setOrganizeResult] = useState<BrainDumpOrganizeResponse | null>(null);

  const { data: sessions, isLoading, error } = useQuery({
    queryKey: [...QUERY_KEY, projectId],
    queryFn: () => getBrainDumpSessions(resolvedProjectId),
    staleTime: 10_000,
    enabled: !!projectId,
  });

  const createMutation = useMutation({
    mutationFn: (payload: { project_id: string; title?: string | null; raw_text?: string }) =>
      createBrainDumpSession(payload),
    onSuccess: (session) => {
      setActiveSessionId(session.session_id);
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, projectId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { sessionId: string; projectId: string; raw_text: string }) =>
      updateBrainDumpSession(payload.sessionId, payload.projectId, { raw_text: payload.raw_text }),
  });

  const organizeMutation = useMutation({
    mutationFn: (sessionId: string) =>
      organizeBrainDumpSession(sessionId, resolvedProjectId),
    onSuccess: (result) => {
      setOrganizeResult(result);
      queryClient.invalidateQueries({ queryKey: [...QUERY_KEY, projectId] });
    },
    onError: () => {
      toast.error('Failed to organize brain dump. Please try again.');
    },
  });

  // Auto-select existing session or create one
  useEffect(() => {
    if (sessions && sessions.length > 0 && !activeSessionId) {
      const active = sessions.find((s) => s.state === 'active');
      setActiveSessionId(active?.session_id ?? sessions[0].session_id);
    }
  }, [sessions, activeSessionId]);

  // Create session if none exists
  useEffect(() => {
    if (!sessions || sessions.length === 0 || activeSessionId || !projectId) {
      return;
    }
    createMutation.mutate({ project_id: projectId });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, sessions, activeSessionId]);

  const activeSession = useMemo(
    () => sessions?.find((s) => s.session_id === activeSessionId),
    [sessions, activeSessionId],
  );

  const handleSave = (rawText: string) => {
    if (activeSessionId) {
      updateMutation.mutate({
        sessionId: activeSessionId,
        projectId: resolvedProjectId,
        raw_text: rawText,
      });
    }
  };

  const handleOrganize = () => {
    if (activeSessionId) {
      organizeMutation.mutate(activeSessionId);
    }
  };

  // Show organize summary
  if (organizeResult) {
    const entries = Object.entries(organizeResult.categorized_items)
      .filter(([, items]) => items.length > 0)
      .map(([type, items]) => `${items.length} ${type}`)
      .join(', ');

    return (
      <div className="flex flex-col h-full">
        <div className="p-4 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)]">
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
            Organized {organizeResult.total_items} items
          </h2>
          <p className="text-sm text-[var(--text-secondary)]">{entries}</p>
          <button
            onClick={() => setOrganizeResult(null)}
            className="mt-2 text-sm text-[var(--primary-accent)] hover:underline"
          >
            Continue editing
          </button>
        </div>
        <div className="flex-1 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {Object.entries(organizeResult.categorized_items)
              .filter(([, items]) => items.length > 0)
              .map(([type, items]) => (
                <div
                  key={type}
                  className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg p-3"
                >
                  <h3 className="text-sm font-medium text-[var(--text-primary)] mb-2 capitalize">
                    {type.replace('_', ' ')}
                  </h3>
                  <ul className="space-y-1">
                    {items.map((item) => (
                      <li key={item.item_id} className="text-xs text-[var(--text-secondary)] line-clamp-2">
                        {item.content}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
          </div>
        </div>
      </div>
    );
  }

  if (!projectId) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-[var(--text-secondary)]">No project selected.</p>
      </div>
    );
  }

  // Loading state
  if (isLoading || !activeSession) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-[var(--text-secondary)]">Loading brain dump session...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-400">Failed to load brain dump session.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <BrainDumpCanvas
        sessionId={activeSessionId}
        onSave={handleSave}
        onOrganize={handleOrganize}
        initialTitle={activeSession.title}
        initialState={activeSession.state}
      />
    </div>
  );
}
