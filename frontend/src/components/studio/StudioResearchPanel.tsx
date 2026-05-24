import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { WorkspaceStatus } from '../planning/ui';
import {
  createResearchItem,
  deleteResearchItem,
  getResearchItems,
} from '../../services/research';
import type { ResearchItem, ResearchItemCreateRequest } from '../../types/research';

interface StudioResearchPanelProps {
  projectId: string;
}

export function StudioResearchPanel({ projectId }: StudioResearchPanelProps) {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newSourceUrl, setNewSourceUrl] = useState('');
  const [newSourceType, setNewSourceType] = useState('other');

  const { data: items = [], isLoading, error } = useQuery<ResearchItem[]>({
    queryKey: ['research-items', projectId],
    queryFn: () => getResearchItems(projectId),
    enabled: Boolean(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (req: ResearchItemCreateRequest) => createResearchItem(req),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['research-items', projectId] });
      setNewTitle('');
      setNewContent('');
      setNewSourceUrl('');
      setNewSourceType('other');
      setIsCreating(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => deleteResearchItem(itemId, projectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['research-items', projectId] });
    },
  });

  if (isLoading) {
    return <WorkspaceStatus title="Loading research" detail="Fetching research items." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load research"
        detail="Research items are unavailable."
        tone="error"
      />
    );
  }

  if (isCreating) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex shrink-0 items-center justify-between px-2.5 py-1 border-b border-[var(--border-primary)]">
          <span className="text-[9px] text-[var(--text-tertiary)]">New Research Item</span>
          <button
            onClick={() => {
              setIsCreating(false);
              setNewTitle('');
              setNewContent('');
              setNewSourceUrl('');
              setNewSourceType('other');
            }}
            className="text-[9px] text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          >
            Cancel
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2.5 space-y-2.5">
          <input
            type="text"
            placeholder="Title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-400"
          />

          <textarea
            placeholder="Content"
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            rows={6}
            className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
          />

          <input
            type="text"
            placeholder="Source URL (optional)"
            value={newSourceUrl}
            onChange={(e) => setNewSourceUrl(e.target.value)}
            className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-400"
          />

          <select
            value={newSourceType}
            onChange={(e) => setNewSourceType(e.target.value)}
            className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-400"
          >
            <option value="book">Book</option>
            <option value="article">Article</option>
            <option value="website">Website</option>
            <option value="interview">Interview</option>
            <option value="other">Other</option>
          </select>

          <button
            disabled={!newTitle.trim() || !newContent.trim() || createMutation.isPending}
            onClick={() =>
              createMutation.mutate({
                project_id: projectId,
                title: newTitle.trim(),
                content: newContent.trim(),
                source_url: newSourceUrl.trim() || null,
                source_type: newSourceType,
              })
            }
            className="w-full px-2 py-1.5 text-xs font-medium rounded bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between px-2.5 py-1 border-b border-[var(--border-primary)]">
        <span className="text-[9px] text-[var(--text-tertiary)]">
          {items.length} items
        </span>
        <button
          onClick={() => setIsCreating(true)}
          className="px-1.5 py-0.5 bg-blue-500 text-white text-[9px] font-medium rounded hover:bg-blue-600 transition-colors"
        >
          New
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <div className="grid grid-cols-1 gap-2">
          {items.map((item) => (
            <div
              key={item.item_id}
              className="rounded-lg border p-2.5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
            >
              <div className="flex items-start justify-between">
                <h3 className="text-xs font-medium text-slate-900 dark:text-slate-100 truncate pr-2">
                  {item.title}
                </h3>
                <button
                  onClick={() => deleteMutation.mutate(item.item_id)}
                  className="shrink-0 text-[9px] text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors"
                >
                  Archive
                </button>
              </div>

              <p className="text-[10px] mt-0.5 text-slate-500 dark:text-slate-400 line-clamp-2">
                {item.content}
              </p>

              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                  {item.source_type}
                </span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                  {item.status}
                </span>
                {item.source_url && (
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[9px] text-blue-500 hover:text-blue-700 dark:hover:text-blue-400 transition-colors truncate"
                  >
                    Source
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>

        {items.length === 0 && (
          <div className="text-center py-4 text-[10px] text-slate-500 dark:text-slate-400">
            No research items. Create one to track references and sources.
          </div>
        )}
      </div>
    </div>
  );
}
