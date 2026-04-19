import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Search, Link as LinkIcon } from 'lucide-react';
import { FindingsList } from '../components/review';
import { InspectRunLinksList } from '../components/inspectLinks';
import { useThemeStore } from '../stores/themeStore';

export function ReviewView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<'findings' | 'links'>('findings');
  const { mode } = useThemeStore();
  const isDark = mode === 'dark';

  if (!projectId) {
    return <div className={`text-sm ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>No project selected</div>;
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
          <div className="p-5">
            <InspectRunLinksList projectId={projectId} />
          </div>
        )}
      </main>
    </div>
  );
}
