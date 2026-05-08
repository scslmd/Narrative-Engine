import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { Search, Link as LinkIcon, X } from 'lucide-react';
import { FindingsList } from '../components/review';
import { InspectRunLinksList } from '../components/inspectLinks';
import { createInspectLink } from '../services/inspectLinks';
import { useThemeStore } from '../stores/themeStore';
import { resolveEffectiveMode } from '../theme/theme';

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
  const { mode, _systemTick } = useThemeStore();
  void _systemTick;
  const isDark = resolveEffectiveMode(mode) === 'dark';

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
    return <div className="text-sm text-subtle">No project selected</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <div className={`border-b ${isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-white/60'} px-4 py-2`}>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab('findings')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150 ${
              activeTab === 'findings'
                ? 'bg-amber-600 text-white shadow-sm'
                : isDark
                  ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100/80'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            Findings
          </button>
          <button
            onClick={() => setActiveTab('links')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150 ${
              activeTab === 'links'
                ? 'bg-amber-600 text-white shadow-sm'
                : isDark
                  ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100/80'
            }`}
          >
            <LinkIcon className="w-3.5 h-3.5" />
            Inspect Run Links
          </button>
        </div>
      </div>

      <main className="flex-1 overflow-y-auto">
        {activeTab === 'findings' && (
          <div className="p-5">
            <FindingsList projectId={projectId} />
          </div>
        )}
        {activeTab === 'links' && (
          <div className={`p-5 space-y-4 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
            {!showCreateForm ? (
              <div className="flex justify-end mb-2">
                <button
                  onClick={() => setShowCreateForm(true)}
                  className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-indigo-950 text-indigo-300 hover:bg-indigo-900' : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'}`}
                >
                  + New Link
                </button>
              </div>
            ) : (
              <div className={`p-4 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold">Create Inspect Run Link</h4>
                  <button onClick={handleResetForm} className={`text-xs ${isDark ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600'}`}>
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex flex-col gap-2">
                  <div className="flex gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-medium text-subtle">Link ID</label>
                      <input
                        type="text"
                        placeholder="link-1"
                        value={formData.link_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, link_id: e.target.value }))}
                        className={`text-xs px-2 py-1.5 rounded border outline-none focus:border-indigo-500 w-32 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-medium text-subtle">Object Kind</label>
                      <input
                        type="text"
                        placeholder="chapter-plan"
                        value={formData.object_kind}
                        onChange={(e) => setFormData(prev => ({ ...prev, object_kind: e.target.value }))}
                        className={`text-xs px-2 py-1.5 rounded border outline-none focus:border-indigo-500 w-40 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-medium text-subtle">Object ID</label>
                      <input
                        type="text"
                        placeholder="abc-123"
                        value={formData.object_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, object_id: e.target.value }))}
                        className={`text-xs px-2 py-1.5 rounded border outline-none focus:border-indigo-500 w-32 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-medium text-subtle">Logical Run ID</label>
                      <input
                        type="text"
                        placeholder="run-001"
                        value={formData.logical_run_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, logical_run_id: e.target.value }))}
                        className={`text-xs px-2 py-1.5 rounded border outline-none focus:border-indigo-500 w-32 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-medium text-subtle">Run ID</label>
                      <input
                        type="text"
                        placeholder="job-abc"
                        value={formData.run_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, run_id: e.target.value }))}
                        className={`text-xs px-2 py-1.5 rounded border outline-none focus:border-indigo-500 w-32 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-medium text-subtle">Run Kind</label>
                      <input
                        type="text"
                        placeholder="pipeline_job"
                        value={formData.run_kind}
                        onChange={(e) => setFormData(prev => ({ ...prev, run_kind: e.target.value }))}
                        className={`text-xs px-2 py-1.5 rounded border outline-none focus:border-indigo-500 w-32 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
                      />
                    </div>
                  </div>
                  {formError && (
                    <p className="text-xs text-red-500">{formError}</p>
                  )}
                  <div className="flex gap-2 pt-1">
                    <button
                      onClick={handleCreateSubmit}
                      disabled={createMutation.isPending}
                      className="text-xs px-2.5 py-1.5 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 font-medium"
                    >
                      {createMutation.isPending ? 'Creating...' : 'Create'}
                    </button>
                    <button
                      onClick={handleResetForm}
                      className={`text-xs px-2.5 py-1.5 rounded-md font-medium ${isDark ? 'text-slate-400 hover:text-slate-200 bg-slate-800' : 'text-slate-500 hover:text-slate-700 bg-slate-100'}`}
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
  );
}
