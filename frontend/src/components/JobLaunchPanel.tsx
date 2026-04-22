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
  {
    value: 'P-100',
    label: 'Architect',
    description: 'Build project architecture',
    icon: Rocket,
    gradient: 'from-blue-500 to-blue-600',
  },
  {
    value: 'P-200',
    label: 'Sequencer',
    description: 'Plan story sequence',
    icon: Layers,
    gradient: 'from-emerald-500 to-emerald-600',
  },
  {
    value: 'P-300',
    label: 'Drafter',
    description: 'Draft narrative content',
    icon: Code,
    gradient: 'from-violet-500 to-violet-600',
  },
  {
    value: 'P-400',
    label: 'Compiler',
    description: 'Compile and finalize',
    icon: Cpu,
    gradient: 'from-amber-500 to-amber-600',
  },
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

  const hasProcessingJob = jobs?.some(
    (job) => job.status === 'PROCESSING' || job.status === 'PENDING'
  );

  const selectedPhaseOption = phases.find(p => p.value === selectedPhase);

  const cardClass = isDark
    ? 'bg-slate-900 border-slate-800'
    : 'bg-white border-slate-200'
  const headerClass = isDark
    ? 'border-slate-800'
    : 'border-slate-200'
  const headerTextColor = isDark
    ? 'text-indigo-400'
    : 'text-indigo-500'
  const headingColor = isDark
    ? 'text-slate-200'
    : 'text-slate-800'
  const labelColor = 'text-slate-500'
  const phaseDescColor = isDark
    ? 'text-slate-500'
    : 'text-slate-400'

  return (
    <div className={`rounded-xl border ${cardClass} shadow-card flex flex-col h-full`}>
      <div className={`flex items-center gap-2 px-4 py-3 border-b ${headerClass}`}>
        <Rocket className={`w-4 h-4 ${headerTextColor}`} />
        <h3 className={`text-sm font-semibold ${headingColor}`}>
          Launch Job
        </h3>
      </div>

      <div className="p-3 space-y-3">
        <div>
          <label className={`block text-xs font-semibold uppercase tracking-wider mb-2 ${labelColor}`}>
            Phase
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {phases.map((phase) => (
              <PhaseButton
                key={phase.value}
                phase={phase}
                isSelected={selectedPhase === phase.value}
                onSelect={() => setSelectedPhase(phase.value)}
                disabled={createJob.isPending || Boolean(hasProcessingJob)}
                isDark={isDark}
              />
            ))}
          </div>
        </div>

        {selectedPhaseOption && (
          <p className={`text-xs ${phaseDescColor}`}>
            {selectedPhaseOption.description}
          </p>
        )}

        <LaunchButton
          onClick={handleLaunch}
          disabled={createJob.isPending || Boolean(hasProcessingJob)}
          selectedPhase={selectedPhaseOption?.label}
          isLaunching={createJob.isPending}
          hasProcessingJob={Boolean(hasProcessingJob)}
          isDark={isDark}
        />

        {jobs && jobs.length > 0 && (
          <RecentJobsList jobs={jobs.slice(0, 4)} isDark={isDark} />
        )}
      </div>
    </div>
  );
}

interface PhaseButtonProps {
  phase: PhaseOption;
  isSelected: boolean;
  onSelect: () => void;
  disabled: boolean;
  isDark: boolean;
}

function PhaseButton({
  phase, isSelected, onSelect, disabled, isDark,
}: PhaseButtonProps): React.ReactElement {
  const Icon = phase.icon;
  const selectedClass = `bg-gradient-to-r ${phase.gradient} text-white shadow-sm`
  const unselectedClass = isDark
    ? 'bg-slate-800/50 text-slate-400 hover:bg-slate-800 hover:text-slate-300'
    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-800'

  return (
    <button
      onClick={onSelect}
      disabled={disabled}
      className={`flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-all duration-150 text-xs ${
        isSelected ? selectedClass : unselectedClass
      } disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
      <span className="font-medium">{phase.label}</span>
    </button>
  );
}

interface LaunchButtonProps {
  onClick: () => void;
  disabled: boolean;
  selectedPhase?: string;
  isLaunching: boolean;
  hasProcessingJob: boolean;
  isDark: boolean;
}

function LaunchButton({
  onClick, disabled, selectedPhase,
  isLaunching, hasProcessingJob, isDark,
}: LaunchButtonProps): React.ReactElement {
  const baseClass = [
    'w-full flex items-center justify-center gap-2',
    'px-4 py-2.5 text-sm font-medium',
    'rounded-lg transition-all duration-150',
    'disabled:opacity-60',
  ].join(' ')

  const processingClass = isDark
    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
  const normalClass = [
    'bg-gradient-to-r from-indigo-500 to-violet-600',
    'text-white hover:from-indigo-600 hover:to-violet-700',
    'shadow-sm hover:shadow-md',
  ].join(' ')

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClass} ${
        hasProcessingJob ? processingClass : normalClass
      }`}
    >
      {isLaunching ? (
        <>
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          Launching...
        </>
      ) : hasProcessingJob ? (
        <>
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          Job Running
        </>
      ) : (
        <>
          <Play className="w-3.5 h-3.5" />
          Launch {selectedPhase}
        </>
      )}
    </button>
  );
}

interface RecentJobsListProps {
  jobs: Array<{
    job_id: string;
    phase: string;
    status: string;
  }>;
  isDark: boolean;
}

function RecentJobsList({ jobs, isDark }: RecentJobsListProps): React.ReactElement {
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'COMPLETED': return isDark ? 'text-emerald-400' : 'text-emerald-600';
      case 'FAILED': return isDark ? 'text-red-400' : 'text-red-600';
      case 'PROCESSING': return isDark ? 'text-blue-400' : 'text-blue-600';
      default: return 'text-slate-500';
    }
  };

  return (
    <div className={`border-t pt-3 ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
      <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
        'text-slate-500'
      }`}>
        Recent Jobs
      </h4>
      <ul className="space-y-1.5">
        {jobs.map((job) => (
          <JobItem key={job.job_id} job={job} isDark={isDark} getStatusColor={getStatusColor} />
        ))}
      </ul>
    </div>
  );
}

interface JobItemProps {
  job: {
    job_id: string;
    phase: string;
    status: string;
  };
  isDark: boolean;
  getStatusColor: (status: string) => string;
}

function JobItem({ job, isDark, getStatusColor }: JobItemProps): React.ReactElement {
  return (
    <li className={`flex items-center justify-between text-xs px-2 py-1.5 rounded-md ${
      isDark ? 'bg-slate-800/40' : 'bg-slate-50'
    }`}>
      <span className={isDark ? 'text-slate-400' : 'text-slate-600'}>
        {job.phase}
      </span>
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
  );
}
