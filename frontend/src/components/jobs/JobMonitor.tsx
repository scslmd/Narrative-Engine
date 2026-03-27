import { useState } from 'react';
import { useJobMonitor } from '../../hooks/useJobMonitor';
import JobStatusIndicator from './JobStatusIndicator';
import JobProgress from './JobProgress';
import JobLogsViewer from './JobLogsViewer';

type Tab = 'status' | 'logs';

export default function JobMonitor() {
  const { jobId, isVisible, status, progress, isPolling, currentPhase, currentStep, error, onDismiss } = useJobMonitor();
  const [activeTab, setActiveTab] = useState<Tab>('status');

  if (!isVisible || !jobId) return null;

  const isTerminal = status === 'COMPLETED' || status === 'FAILED';

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-4 flex-1">
          <span className="text-sm font-mono text-gray-600">{jobId}</span>
          
          <JobStatusIndicator status={status} isPolling={isPolling} />

          {!isTerminal && progress !== null && (
            <div className="w-32">
              <JobProgress progress={progress} currentPhase={currentPhase} currentStep={currentStep} />
            </div>
          )}

          {error && !isTerminal && (
            <span className="text-sm text-red-600">{error}</span>
          )}
        </div>

        <button
          onClick={onDismiss}
          className="p-1 hover:bg-gray-100 rounded"
          title="Close monitor"
        >
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {!isTerminal && (
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('status')}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'status'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Status
          </button>

          <button
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'logs'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Logs
          </button>
        </div>
      )}

      {activeTab === 'logs' && !isTerminal && (
        <div className="h-48">
          <JobLogsViewer jobId={jobId} />
        </div>
      )}
    </div>
  );
}
