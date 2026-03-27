import { useState } from 'react';
import { useJobs } from '../hooks/useJobs';
import { JobLogsViewer } from './JobLogsViewer';

interface Props {
  projectId: string;
}

export function BottomUtilityLayer({ projectId }: Props): React.ReactElement | null {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const { data: jobs } = useJobs(projectId);

  const hasActiveJobs = jobs?.some(
    (job) => job.status === 'PROCESSING' || job.status === 'PENDING'
  );

  const getPhaseLabel = (phase: string): string => {
    switch (phase) {
      case 'P-100': return 'Architect';
      case 'P-200': return 'Sequencer';
      case 'P-300': return 'Drafter';
      case 'P-400': return 'Compiler';
      default: return phase;
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'COMPLETED': return 'bg-green-600';
      case 'FAILED': return 'bg-red-600';
      case 'PROCESSING': return 'bg-blue-600 animate-pulse';
      default: return 'bg-gray-600';
    }
  };

  const handleJobSelect = (jobId: string): void => {
    setSelectedJobId(jobId);
    setIsExpanded(true);
  };

  if (!jobs || jobs.length === 0) {
    return null;
  }

  const recentJobs = jobs.slice(0, 3);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 z-50">
      {!isExpanded ? (
        <div
          onClick={() => setIsExpanded(true)}
          className="flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center gap-4">
            {hasActiveJobs && (
              <span className="flex items-center gap-2 text-sm text-blue-400">
                <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                Jobs running...
              </span>
            )}
            {recentJobs.map((job) => (
              <button
                key={job.job_id}
                onClick={(e) => {
                  e.stopPropagation();
                  handleJobSelect(job.job_id);
                }}
                className="flex items-center gap-2 text-sm"
              >
                <span className={`w-2 h-2 rounded-full ${getStatusColor(job.status)}`} />
                <span className="text-gray-300">{getPhaseLabel(job.phase)}</span>
                <span className="text-gray-500">•</span>
                <span className="text-gray-400 uppercase text-xs">{job.status}</span>
              </button>
            ))}
          </div>

          <span className="text-xs text-gray-500">Click to expand</span>
        </div>
      ) : (
        <div className="flex flex-col h-64">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
            <h3 className="text-sm font-medium text-white">Job Monitor</h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            </button>
          </div>

          <div className="flex flex-1 overflow-hidden">
            <div className="w-64 border-r border-gray-700 overflow-y-auto">
              <ul className="py-2">
                {jobs.map((job) => (
                  <li key={job.job_id}>
                    <button
                      onClick={() => setSelectedJobId(job.job_id)}
                      className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors ${
                        selectedJobId === job.job_id
                          ? 'bg-blue-600'
                          : 'hover:bg-gray-700'
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full ${getStatusColor(job.status)}`} />
                      <div className="flex-1">
                        <p className="text-sm text-white">{getPhaseLabel(job.phase)}</p>
                        <p className="text-xs text-gray-400">
                          {new Date(job.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex-1 bg-gray-900">
              {selectedJobId ? (
                <JobLogsViewer jobId={selectedJobId} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  Select a job to view logs
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
