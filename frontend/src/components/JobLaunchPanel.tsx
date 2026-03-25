import { useState } from 'react';
import { useCreateJob, useJobs } from '../hooks/useJobs';

interface Props {
  projectId: string;
}

export function JobLaunchPanel({ projectId }: Props): React.ReactElement {
  const createJob = useCreateJob();
  const { data: jobs } = useJobs(projectId);
  const [selectedPhase, setSelectedPhase] = useState<'P-100' | 'P-200' | 'P-300' | 'P-400'>('P-100');

  const handleLaunch = (): void => {
    createJob.mutate({ project_id: projectId, phase: selectedPhase });
  };

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
      case 'COMPLETED': return 'text-green-600 dark:text-green-400';
      case 'FAILED': return 'text-red-600 dark:text-red-400';
      case 'PROCESSING': return 'text-blue-600 dark:text-blue-400 animate-pulse';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const hasProcessingJob = jobs?.some(
    (job) => job.status === 'PROCESSING' || job.status === 'PENDING'
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Launch Job</h3>

      <div className="space-y-2">
        <label htmlFor="phase" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Phase
        </label>
        <select
          id="phase"
          value={selectedPhase}
          onChange={(e) => setSelectedPhase(e.target.value as 'P-100' | 'P-200' | 'P-300' | 'P-400')}
          disabled={createJob.isPending || hasProcessingJob}
          className="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
        >
          <option value="P-100">P-100: Architect</option>
          <option value="P-200">P-200: Sequencer</option>
          <option value="P-300">P-300: Drafter</option>
          <option value="P-400">P-400: Compiler</option>
        </select>
      </div>

      <button
        onClick={handleLaunch}
        disabled={createJob.isPending || hasProcessingJob}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {createJob.isPending ? 'Launching...' : `Launch ${getPhaseLabel(selectedPhase)}`}
      </button>

      {jobs && jobs.length > 0 && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Recent Jobs</h4>
          <ul className="space-y-2 max-h-48 overflow-y-auto">
            {jobs.slice(0, 5).map((job) => (
              <li key={job.job_id} className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">{getPhaseLabel(job.phase)}</span>
                <span className={`font-medium ${getStatusColor(job.status)}`}>
                  {job.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
