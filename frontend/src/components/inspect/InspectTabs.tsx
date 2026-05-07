import { useState, useEffect, useCallback } from 'react';
import StepTimeline from './StepTimeline';
import ArtifactLineage from './ArtifactLineage';
import type { InspectContext } from '../../types/inspect';
import { getAttempts } from '../../services/jobs';
import { getCheckerAttempts } from '../../services/checker';
import type { AttemptHistoryItem } from '../../types/inspect';

interface InspectTabsProps {
  context: InspectContext;
}

type TabKey = 'steps' | 'lineage' | 'attempts';

export default function InspectTabs({ context }: InspectTabsProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('steps');
  const [attempts, setAttempts] = useState<AttemptHistoryItem[]>([]);
  const [attemptsLoading, setAttemptsLoading] = useState(false);
  const [attemptsError, setAttemptsError] = useState<string | null>(null);

  const loadAttempts = useCallback(async () => {
    setAttemptsLoading(true);
    setAttemptsError(null);
    
    try {
      const response = context.runKind === 'pipeline_job'
        ? await getAttempts(context.jobId)
        : await getCheckerAttempts(context.jobId);
      
      setAttempts(response.items || []);
    } catch (err) {
      setAttemptsError(err instanceof Error ? err.message : 'Unknown error');
      setAttempts([]);
    } finally {
      setAttemptsLoading(false);
    }
  }, [context.jobId, context.runKind]);

  useEffect(() => {
    if (activeTab === 'attempts') {
      loadAttempts();
    }
  }, [activeTab, loadAttempts]);

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'steps', label: 'Steps' },
    { key: 'lineage', label: 'Lineage' },
    { key: 'attempts', label: 'Attempts' },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="border-b px-4">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 hover:dark:text-slate-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'steps' && <StepTimeline context={context} />}
        {activeTab === 'lineage' && <ArtifactLineage context={context} />}
        {activeTab === 'attempts' && (
          <div className="p-4">
            {attemptsLoading && (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <div key={i} className="bg-white dark:bg-slate-800 rounded-lg p-4 border animate-pulse">
                    <div className="h-5 bg-gray-200 dark:bg-slate-600 rounded w-1/3 mb-2"></div>
                    <div className="h-4 bg-gray-200 dark:bg-slate-600 rounded w-2/3"></div>
                  </div>
                ))}
              </div>
            )}
            
            {attemptsError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-700 text-sm">{attemptsError}</p>
              </div>
            )}
            
            {!attemptsLoading && !attemptsError && attempts.length === 0 && (
              <div className="text-center text-sm text-gray-500 dark:text-slate-400">
                No execution attempts found for this job. Run the job to see attempt history.
              </div>
            )}
            
            {!attemptsLoading && !attemptsError && attempts.length > 0 && (
              <div className="space-y-3">
                {attempts.map((attempt) => (
                  <div key={attempt.attempt_number} className="bg-white dark:bg-slate-800 rounded-lg p-4 border">
                    <h4 className="font-medium text-gray-900 dark:text-slate-100 mb-2">
                      Attempt #{attempt.attempt_number}
                    </h4>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                      <span className="text-gray-500 dark:text-slate-400">Status:</span>
                      <span className={`font-medium ${
                        attempt.status === 'COMPLETED' ? 'text-green-600' :
                        attempt.status === 'FAILED' ? 'text-red-600' :
                        'text-yellow-600'
                      }`}>
                        {attempt.status}
                      </span>
                      
                      {attempt.started_at && (
                        <>
                          <span className="text-gray-500 dark:text-slate-400">Started:</span>
                          <span className="text-gray-700 dark:text-slate-300">{new Date(attempt.started_at).toLocaleString()}</span>
                        </>
                      )}
                      
                      {attempt.finished_at && (
                        <>
                          <span className="text-gray-500 dark:text-slate-400">Finished:</span>
                          <span className="text-gray-700 dark:text-slate-300">{new Date(attempt.finished_at).toLocaleString()}</span>
                        </>
                      )}
                      
                      {attempt.finish_reason && (
                        <>
                          <span className="text-gray-500 dark:text-slate-400">Finish Reason:</span>
                          <span className="text-gray-700 dark:text-slate-300">{attempt.finish_reason}</span>
                        </>
                      )}
                      
                      {attempt.error_code && (
                        <>
                          <span className="text-gray-500 dark:text-slate-400">Error Code:</span>
                          <span className="text-red-600">{attempt.error_code}</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
