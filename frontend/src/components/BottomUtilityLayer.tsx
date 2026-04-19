import { useState } from 'react';
import { useJobs } from '../hooks/useJobs';
import { JobLogsViewer } from './JobLogsViewer';
import { ChevronDown, ChevronUp, Activity, Loader2, CheckCircle2, XCircle } from 'lucide-react';

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className="w-3 h-3 text-emerald-500" />;
      case 'FAILED': return <XCircle className="w-3 h-3 text-red-500" />;
      case 'PROCESSING': return <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />;
      default: return <Activity className={`w-3 h-3 ${status === 'PENDING' ? 'text-amber-500' : 'text-slate-500'}`} />;
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
    <div className="fixed bottom-0 left-0 right-0 z-[200]">
      {!isExpanded ? (
        <div
          onClick={() => setIsExpanded(true)}
          className={`flex items-center justify-between px-4 py-1.5 cursor-pointer border-t transition-colors ${
            hasActiveJobs
              ? 'bg-gradient-to-r from-slate-900 to-slate-800 border-slate-700 hover:from-slate-800 hover:to-slate-700'
              : 'bg-slate-900 border-slate-800 hover:bg-slate-800'
          }`}
        >
          <div className="flex items-center gap-3">
            {hasActiveJobs && (
              <span className="flex items-center gap-1.5 text-xs text-blue-400">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                Jobs running
              </span>
            )}
            {recentJobs.map((job) => (
              <button
                key={job.job_id}
                onClick={(e) => {
                  e.stopPropagation();
                  handleJobSelect(job.job_id);
                }}
                className="flex items-center gap-1.5 text-xs group"
              >
                {getStatusIcon(job.status)}
                <span className="text-slate-400 group-hover:text-slate-200">{getPhaseLabel(job.phase)}</span>
                <span className="text-slate-600">/</span>
                <span className={`uppercase ${
                  job.status === 'COMPLETED' ? 'text-emerald-400' :
                  job.status === 'FAILED' ? 'text-red-400' :
                  job.status === 'PROCESSING' ? 'text-blue-400' :
                  'text-amber-400'
                }`}>
                  {job.status}
                </span>
              </button>
            ))}
          </div>

          <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
        </div>
      ) : (
        <div className="h-56 bg-slate-900 border-t border-slate-800 flex flex-col">
          <div className={`flex items-center justify-between px-4 py-2 border-b ${'border-slate-800'}`}>
            <h3 className="text-xs font-semibold text-slate-300">Job Monitor</h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              <span>Close</span>
              <ChevronUp className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex flex-1 overflow-hidden">
            <div className={`w-56 border-r ${'border-slate-800'} overflow-y-auto`}>
              <ul className="py-1.5">
                {jobs.map((job) => (
                  <li key={job.job_id}>
                    <button
                      onClick={() => setSelectedJobId(job.job_id)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors ${
                        selectedJobId === job.job_id
                          ? 'bg-slate-800 text-white'
                          : 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {getStatusIcon(job.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{getPhaseLabel(job.phase)}</p>
                        <p className="text-[10px] text-slate-600">
                          {new Date(job.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex-1 bg-slate-950">
              {selectedJobId ? (
                <JobLogsViewer jobId={selectedJobId} />
              ) : (
                <div className="flex items-center justify-center h-full text-slate-600 text-xs">
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
