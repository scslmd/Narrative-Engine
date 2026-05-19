import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { Search, Link as LinkIcon, X } from 'lucide-react';
import { FindingsList } from '../components/review';
import { InspectRunLinksList } from '../components/inspectLinks';
import { createInspectLink } from '../services/inspectLinks';
import { ViewShell } from '../components/shell/ViewShell';
import { ViewTabs } from '../components/shell/ViewTabs';

interface InspectLinkFormData {
  link_id: string;
  object_kind: string;
  object_id: string;
  logical_run_id: string;
  run_id: string;
  run_kind: string;
}

export function ReviewView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<'findings' | 'links'>('findings');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<InspectLinkFormData>({
    link_id: '',
    object_kind: '',
    object_id: '',
    logical_run_id: '',
    run_id: '',
    run_kind: 'pipeline_job',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: InspectLinkFormData) =>
      createInspectLink({
        ...data,
        project_id: projectId || '',
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['review', 'inspect-links', projectId] });
      setShowCreateForm(false);
      setFormData({
        link_id: '',
        object_kind: '',
        object_id: '',
        logical_run_id: '',
        run_id: '',
        run_kind: 'pipeline_job',
      });
      setFormError(null);
    },
    onError: (err: Error) => {
      setFormError(err.message || 'Failed to create inspect link');
    },
  });

  const handleResetForm = useCallback(() => {
    setShowCreateForm(false);
    setFormData({
      link_id: '',
      object_kind: '',
      object_id: '',
      logical_run_id: '',
      run_id: '',
      run_kind: 'pipeline_job',
    });
    setFormError(null);
  }, []);

  const handleCreateSubmit = useCallback(() => {
    const hasEmptyFields = Object.values(formData).some(v => v.trim() === '');
    if (hasEmptyFields) {
      setFormError('All fields are required');
      return;
    }
    createMutation.mutate(formData);
  }, [formData, createMutation]);

  if (!projectId) {
    return <div className="text-sm text-[var(--text-secondary)]">No project selected</div>;
  }

  const tabs = [
    { id: 'findings', label: 'Findings', icon: <Search className="w-3.5 h-3.5" /> },
    { id: 'links', label: 'Inspect Run Links', icon: <LinkIcon className="w-3.5 h-3.5" /> },
  ];

  return (
    <ViewShell title="Review" subtitle={projectId}>
      <div className="flex flex-col h-full">
        <ViewTabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as 'findings' | 'links')}
        />
        <main className="flex-1 overflow-y-auto">
          {activeTab === 'findings' && (
            <div className="p-4">
              <FindingsList projectId={projectId} />
            </div>
          )}
          {activeTab === 'links' && (
            <div className="p-4 space-y-4 text-[var(--text-primary)]">
              {!showCreateForm ? (
                <div className="flex justify-end mb-2">
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="text-xs px-2.5 py-1 rounded-md font-medium transition-colors bg-[var(--color-primary-subtle)] text-[var(--color-primary)] hover:bg-[var(--color-primary-border)]"
                  >
                    + New Link
                  </button>
                </div>
              ) : (
                <div className="p-4 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)]">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-[var(--text-primary)]">Create Inspect Run Link</h4>
                    <button onClick={handleResetForm} className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex flex-col gap-2">
                    <div className="flex gap-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-medium text-[var(--text-tertiary)]">Link ID</label>
                        <input
                          type="text"
                          placeholder="link-1"
                          value={formData.link_id}
                          onChange={(e) => setFormData(prev => ({ ...prev, link_id: e.target.value }))}
                          className="text-xs px-2 py-1.5 rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] outline-none focus:border-[var(--color-primary)] w-32"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-medium text-[var(--text-tertiary)]">Object Kind</label>
                        <input
                          type="text"
                          placeholder="chapter-plan"
                          value={formData.object_kind}
                          onChange={(e) => setFormData(prev => ({ ...prev, object_kind: e.target.value }))}
                          className="text-xs px-2 py-1.5 rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] outline-none focus:border-[var(--color-primary)] w-40"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-medium text-[var(--text-tertiary)]">Object ID</label>
                        <input
                          type="text"
                          placeholder="abc-123"
                          value={formData.object_id}
                          onChange={(e) => setFormData(prev => ({ ...prev, object_id: e.target.value }))}
                          className="text-xs px-2 py-1.5 rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] outline-none focus:border-[var(--color-primary)] w-32"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-medium text-[var(--text-tertiary)]">Logical Run ID</label>
                        <input
                          type="text"
                          placeholder="run-001"
                          value={formData.logical_run_id}
                          onChange={(e) => setFormData(prev => ({ ...prev, logical_run_id: e.target.value }))}
                          className="text-xs px-2 py-1.5 rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] outline-none focus:border-[var(--color-primary)] w-32"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-medium text-[var(--text-tertiary)]">Run ID</label>
                        <input
                          type="text"
                          placeholder="job-abc"
                          value={formData.run_id}
                          onChange={(e) => setFormData(prev => ({ ...prev, run_id: e.target.value }))}
                          className="text-xs px-2 py-1.5 rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] outline-none focus:border-[var(--color-primary)] w-32"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-medium text-[var(--text-tertiary)]">Run Kind</label>
                        <input
                          type="text"
                          placeholder="pipeline_job"
                          value={formData.run_kind}
                          onChange={(e) => setFormData(prev => ({ ...prev, run_kind: e.target.value }))}
                          className="text-xs px-2 py-1.5 rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] outline-none focus:border-[var(--color-primary)] w-32"
                        />
                      </div>
                    </div>
                    {formError && (
                      <p className="text-xs text-[var(--color-danger)]">{formError}</p>
                    )}
                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={handleCreateSubmit}
                        disabled={createMutation.isPending}
                        className="text-xs px-2.5 py-1.5 rounded-md bg-[var(--color-success)] text-white hover:opacity-90 disabled:opacity-40 font-medium"
                      >
                        {createMutation.isPending ? 'Creating...' : 'Create'}
                      </button>
                      <button
                        onClick={handleResetForm}
                        className="text-xs px-2.5 py-1.5 rounded-md font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--bg-tertiary)]"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
              <InspectRunLinksList projectId={projectId} />
            </div>
          )}
        </main>
      </div>
    </ViewShell>
  );
}
