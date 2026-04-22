import { useState } from 'react';
import { useCreateJob, useJobs } from '../hooks/useJobs';
import { useThemeStore } from '../stores/themeStore';
import { Rocket, Code, Cpu, Layers, Play } from 'lucide-react';

interface Props {
  projectId: string;
}

interface PhaseOption {
  value: 'P-100' | 'P-200' | 'P-300' | 'P-400';
  label: string;
  description: string;
  icon: typeof Rocket;
  gradient: string;
}

const phases: PhaseOption[] = [
  { value: 'P-100', label: 'Architect', description: 'Build project architecture', icon: Rocket, gradient: 'from-blue-500 to-blue-600' },
  { value: 'P-200', label: 'Sequencer', description: 'Plan story sequence', icon: Layers, gradient: 'from-emerald-500 to-emerald-600' },
  { value: 'P-300', label: 'Drafter', description: 'Draft narrative content', icon: Code, gradient: 'from-violet-500 to-violet-600' },
  { value: 'P-400', label: 'Compiler', description: 'Compile and finalize', icon: Cpu, gradient: 'from-amber-500 to-amber-600' },
];

export function JobLaunchPanel({ projectId }: Props): React.ReactElement {
  const createJob = useCreateJob(projectId);
  const { data: jobs } = useJobs(projectId);
  const [selectedPhase, setSelectedPhase] = useState<'P-100' | 'P-200' | 'P-300' | 'P-400'>('P-100');
  const { mode } = useThemeStore();
  const isDark = ['dark', 'midnight', 'forest', 'ocean'].includes(mode);

  const handleLaunch = (): void => {
    createJob.mutate(selectedPhase);
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'COMPLETED': return isDark ? 'text-emerald-400' : 'text-emerald-600';
      case 'FAILED': return isDark ? 'text-red-400' : 'text-red-600';
      case 'PROCESSING': return isDark ? 'text-blue-400' : 'text-blue-600';
      default: return isDark ? 'text-slate-500' : 'text-slate-500';
    }
  };

  const hasProcessingJob = jobs?.some(
    (job) => job.status === 'PROCESSING' || job.status === 'PENDING'
  );

  const selectedPhaseOption = phases.find(p => p.value === selectedPhase);

  return (
    <div className={`rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col h-full`}>
      <div className={`flex items-center gap-2 px-4 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
        <Rocket className={`w-4 h-4 ${isDark ? 'text-indigo-400' : 'text-indigo-500'}`} />
        <h3 className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>Launch Job</h3>
      </div>

      <div className="p-3 space-y-3">
        <div>
          <label className={`block text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
            Phase
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {phases.map((phase) => {
              const Icon = phase.icon;
              const isSelected = selectedPhase === phase.value;
              return (
                <button
                  key={phase.value}
                  onClick={() => setSelectedPhase(phase.value)}
                  disabled={createJob.isPending || hasProcessingJob}
                  className={`flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-all duration-150 text-xs ${
                    isSelected
                      ? `bg-gradient-to-r ${phase.gradient} text-white shadow-sm`
                      : isDark
                        ? 'bg-slate-800/50 text-slate-400 hover:bg-slate-800 hover:text-slate-300'
                        : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-800'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="font-medium">{phase.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {selectedPhaseOption && (
          <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
            {selectedPhaseOption.description}
          </p>
        )}

        <button
          onClick={handleLaunch}
          disabled={createJob.isPending || hasProcessingJob}
          className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-150 ${
            hasProcessingJob
              ? isDark ? 'bg-slate-800 text-slate-500 cursor-not-allowed' : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white hover:from-indigo-600 hover:to-violet-700 shadow-sm hover:shadow-md'
          } disabled:opacity-60`}
        >
          {createJob.isPending ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Launching...
            </>
          ) : hasProcessingJob ? (
            <>
              <div className={`w-2 h-2 rounded-full bg-blue-500 animate-pulse`} />
              Job Running
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5" />
              Launch {selectedPhaseOption?.label}
            </>
          )}
        </button>

        {jobs && jobs.length > 0 && (
          <div className={`border-t pt-3 ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
              Recent Jobs
            </h4>
            <ul className="space-y-1.5">
              {jobs.slice(0, 4).map((job) => (
                <li key={job.job_id} className={`flex items-center justify-between text-xs px-2 py-1.5 rounded-md ${isDark ? 'bg-slate-800/40' : 'bg-slate-50'}`}>
                  <span className={isDark ? 'text-slate-400' : 'text-slate-600'}>{job.phase}</span>
                  <span className={`font-medium ${getStatusColor(job.status)}`}>
                    {job.status === 'PROCESSING' ? (
                      <span className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                        {job.status}
                      </span>
                    ) : (
                      job.status
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
