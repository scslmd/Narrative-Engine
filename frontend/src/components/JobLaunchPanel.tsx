import { useState } from 'react';
import { useCreateJob, useJobs } from '../hooks/useJobs';
import { useThemeStore } from '../stores/themeStore';
import { Rocket, Code, Cpu, Layers, Play, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

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
  const hasProcessingJob = jobs?.some(
    (j) => j.status === 'PROCESSING' || j.status === 'PENDING'
  );
  const selectedPhaseOption = phases.find((p) => p.value === selectedPhase);
  const styles = useJobLaunchPanelStyles(isDark);

  return (
    <div className={`rounded-xl border ${styles.cardClass} shadow-card flex flex-col h-full`}>
      <PanelHeader
        headerTextColor={styles.headerTextColor}
        headingColor={styles.headingColor}
        headerBg={styles.headerBg}
      />
      <div className="p-3 space-y-3">
        <PhaseSelector
          phases={phases}
          selectedPhase={selectedPhase}
          onSelect={(phase: string) => setSelectedPhase(phase as 'P-100' | 'P-200' | 'P-300' | 'P-400')}
          disabled={createJob.isPending || Boolean(hasProcessingJob)}
          selectedOption={selectedPhaseOption}
          isDark={isDark}
          styles={styles}
        />
        <LaunchButton
          onClick={() => createJob.mutate(selectedPhase)}
          disabled={createJob.isPending || Boolean(hasProcessingJob)}
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

function useJobLaunchPanelStyles(isDark: boolean) {
  const cardClass = isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200';
  const headerBg = isDark ? 'border-slate-800' : 'border-slate-200';
  const headerTextColor = isDark ? 'text-indigo-400' : 'text-indigo-500';
  const headingColor = isDark ? 'text-slate-200' : 'text-slate-800';
  const labelColor = isDark ? 'text-slate-400' : 'text-slate-500';
  const phaseDescColor = isDark ? 'text-slate-400' : 'text-slate-500';
  return { cardClass, headerBg, headerTextColor, headingColor, labelColor, phaseDescColor };
}

interface PanelHeaderProps {
  headerTextColor: string;
  headingColor: string;
  headerBg: string;
}

function PanelHeader({ headerTextColor, headingColor, headerBg }: PanelHeaderProps): React.ReactElement {
  return (
    <div className={`flex items-center gap-2 px-4 py-3 border-b ${headerBg}`}>
      <Rocket className={`w-4 h-4 ${headerTextColor}`} />
      <h3 className={`text-sm font-semibold ${headingColor}`}>Launch Job</h3>
    </div>
  );
}

interface PhaseSelectorProps {
  phases: PhaseOption[];
  selectedPhase: string;
  onSelect: (phase: string) => void;
  disabled: boolean;
  selectedOption?: { description: string };
  isDark: boolean;
  styles: { labelColor: string; phaseDescColor: string };
}

function PhaseSelector({
  phases, selectedPhase, onSelect, disabled,
  selectedOption, isDark, styles,
}: PhaseSelectorProps): React.ReactElement {
  return (
    <>
      <div>
        <label className={`block text-xs font-semibold uppercase tracking-wider mb-2 ${styles.labelColor}`}>Phase</label>
        <div className="grid grid-cols-2 gap-1.5">
          {phases.map((phase) => (
            <PhaseButton
              key={phase.value}
              phase={phase}
              isSelected={selectedPhase === phase.value}
              onSelect={() => onSelect(phase.value)}
              disabled={disabled}
              isDark={isDark}
            />
          ))}
        </div>
      </div>
      {selectedOption && (
        <p className={`text-xs ${styles.phaseDescColor}`}>{selectedOption.description}</p>
      )}
    </>
  );
}

interface PhaseButtonProps {
  phase: PhaseOption;
  isSelected: boolean;
  onSelect: () => void;
  disabled: boolean;
  isDark: boolean;
}

function PhaseButton({ phase, isSelected, onSelect, disabled, isDark }: PhaseButtonProps): React.ReactElement {
  const Icon = phase.icon;
  const selectedClass = `bg-gradient-to-r ${phase.gradient} text-white shadow-sm`;
  const unselectedClass = isDark
    ? 'bg-slate-800/50 text-slate-400 hover:bg-slate-800 hover:text-slate-300'
    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-800';
  const commonClass = 'flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-all duration-150 text-xs';
  const disabledClass = 'disabled:opacity-50 disabled:cursor-not-allowed';

  return (
    <button
      onClick={onSelect}
      disabled={disabled}
      className={`${commonClass} ${isSelected ? selectedClass : unselectedClass} ${disabledClass}`}
    >
      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
      <span className="font-medium">{phase.label}</span>
    </button>
  );
}

interface LaunchButtonProps {
  onClick: () => void;
  disabled: boolean;
  isLaunching: boolean;
  hasProcessingJob: boolean;
  isDark: boolean;
}

function LaunchButton({
  onClick, disabled,
  isLaunching, hasProcessingJob, isDark,
}: LaunchButtonProps): React.ReactElement {
  const baseClass = 'w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-150 disabled:opacity-60';
  const processingClass = isDark ? 'bg-slate-800 text-slate-500 cursor-not-allowed' : 'bg-slate-100 text-slate-400 cursor-not-allowed';
  const normalClass = 'bg-gradient-to-r from-indigo-500 to-violet-600 text-white hover:from-indigo-600 hover:to-violet-700 shadow-sm hover:shadow-md';

  return (
    <button onClick={onClick} disabled={disabled} className={`${baseClass} ${hasProcessingJob ? processingClass : normalClass}`}>
      {getLaunchButtonContent(isLaunching, hasProcessingJob)}
    </button>
  );
}

function getLaunchButtonContent(isLaunching: boolean, hasProcessingJob: boolean): React.ReactNode {
  if (isLaunching) {
    return (
      <>
        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        Launching...
      </>
    );
  }
  if (hasProcessingJob) {
    return (
      <>
        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
        Job Running
      </>
    );
  }
  return <Play className="w-3.5 h-3.5" />;
}

interface RecentJobsListProps {
  jobs: Array<{
    job_id: string;
    phase: string;
    status: string;
    created_at?: string;
    updated_at?: string;
    current_step?: string;
    detail?: string;
    progress_current?: number;
    progress_total?: number;
    error?: string;
  }>;
  isDark: boolean;
}

function RecentJobsList({ jobs, isDark }: RecentJobsListProps): React.ReactElement {
  return (
    <div className={`border-t pt-3 ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
      <h4 className="text-xs font-semibold uppercase tracking-wider mb-2 text-slate-500">Recent Jobs</h4>
      <ul className="space-y-1.5">
        {jobs.map((job) => (
          <JobItem key={job.job_id} job={job} isDark={isDark} />
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
    created_at?: string;
    updated_at?: string;
    current_step?: string;
    detail?: string;
    progress_current?: number;
    progress_total?: number;
    error?: string;
  };
  isDark: boolean;
}

function JobItem({ job, isDark }: JobItemProps): React.ReactElement {
  const statusColor = getStatusColor(job.status, isDark);
  const isProcessing = job.status === 'PROCESSING';
  const isFailed = job.status === 'FAILED';
  const isCompleted = job.status === 'COMPLETED';
  const [expanded, setExpanded] = useState(false);
  const elapsed = formatElapsed(job.created_at, job.updated_at);

  return (
    <li className={`rounded-md overflow-hidden ${isDark ? 'bg-slate-800/40' : 'bg-slate-50'}`}>
      <div className="flex items-center justify-between text-xs px-2 py-1.5">
        <span className="text-body">{job.phase}</span>
        <span className={`font-medium ${statusColor}`}>
          {isProcessing ? (
            <span className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
              {job.status}
            </span>
          ) : (
            job.status
          )}
        </span>
      </div>
      {(isFailed || isCompleted) && (
        <button
          onClick={() => setExpanded(!expanded)}
          className={`w-full flex items-center gap-1.5 px-2 py-1 text-xs transition-colors ${isFailed ? (isDark ? 'text-amber-400 hover:bg-slate-700/50' : 'text-amber-600 hover:bg-slate-100') : (isDark ? 'text-slate-500 hover:bg-slate-700/50' : 'text-slate-400 hover:bg-slate-100')}`}
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {isFailed && <AlertTriangle className="w-3 h-3" />}
          {isFailed ? getErrorSummary(job.error) : `Details · ${elapsed}`}
        </button>
      )}
      {expanded && (
        <div className={`px-2 pb-2 text-xs space-y-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          {isFailed && getErrorDetail(job.error, job.detail, isDark)}
          {isCompleted && (
            <>
              <div>{job.detail || 'Phase completed.'}</div>
              <div>Processed in {elapsed}{job.current_step ? ` (${job.current_step})` : ''}</div>
            </>
          )}
        </div>
      )}
      {isProcessing && job.current_step && (
        <div className={`px-2 pb-1.5 text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
          Step: {job.current_step} · Running for {elapsed}
          {job.progress_total && job.progress_current !== undefined && (
            <span className="ml-1">({job.progress_current}/{job.progress_total})</span>
          )}
        </div>
      )}
    </li>
  );
}

const ERROR_MESSAGES: Record<string, { summary: string; detail: (raw?: string, isDark?: boolean) => React.ReactNode }> = {
  INFERENCE_TRUNCATED: {
    summary: 'Response truncated — increase max_tokens',
    detail: (raw, isDark) => (
      <div className="space-y-1">
        {raw && <p>{raw}</p>}
        <p>
          Fix: add <code className={`px-1 py-0.5 rounded ${isDark ? 'bg-slate-600' : 'bg-slate-200'}`}>NARRATIVE_MAX_TOKENS_DEFAULT=8192</code> to your .env file, then restart the server.
        </p>
      </div>
    ),
  },
  INFERENCE_TIMEOUT: {
    summary: 'LLM request timed out',
    detail: (raw) => (
      <div className="space-y-1">
        {raw && <p>{raw}</p>}
        <p>Increase NARRATIVE_INFERENCE_TIMEOUT_SECONDS in .env (default: 120s).</p>
      </div>
    ),
  },
  INFERENCE_TRANSPORT_FAILURE: {
    summary: 'Cannot reach LLM server',
    detail: (raw) => (
      <div className="space-y-1">
        {raw && <p>{raw}</p>}
        <p>Check that llama.cpp is running and NARRATIVE_INFERENCE_BASE_URL in .env is correct.</p>
      </div>
    ),
  },
  INFERENCE_CIRCUIT_OPEN: {
    summary: 'LLM circuit breaker open — too many failures',
    detail: (raw) => (
      <div className="space-y-1">
        {raw && <p>{raw}</p>}
        <p>LLM server has been failing repeatedly. Fix the underlying issue and wait for the circuit to reset, or restart the server.</p>
      </div>
    ),
  },
  INVALID_RESPONSE_SHAPE: {
    summary: 'LLM returned unexpected response format',
    detail: (raw) => raw ? <p>{raw}</p> : null,
  },
  INVALID_JSON_RESPONSE: {
    summary: 'LLM returned invalid JSON',
    detail: (raw) => raw ? <p>{raw}</p> : null,
  },
  RUNTIME_CONFIGURATION_ERROR: {
    summary: 'Inference backend not configured',
    detail: (raw) => (
      <div className="space-y-1">
        {raw && <p>{raw}</p>}
        <p>Set NARRATIVE_INFERENCE_BACKEND and NARRATIVE_INFERENCE_BASE_URL in .env.</p>
      </div>
    ),
  },
};

function getErrorSummary(error?: string): string {
  if (error && ERROR_MESSAGES[error]) return ERROR_MESSAGES[error].summary;
  if (error) return error.replace(/_/g, ' ');
  return 'Unknown error';
}

function getErrorDetail(error?: string, detail?: string, isDark = false): React.ReactNode {
  if (error && ERROR_MESSAGES[error]) return ERROR_MESSAGES[error].detail(detail, isDark);
  return detail ? <p>{detail}</p> : <p>No error details available.</p>;
}

function formatElapsed(created?: string, updated?: string): string {
  if (!created || !updated) return '—';
  const start = new Date(created).getTime();
  const end = new Date(updated).getTime();
  const seconds = Math.round((end - start) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}

function getStatusColor(status: string, isDark: boolean): string {
  switch (status) {
    case 'COMPLETED': return isDark ? 'text-emerald-400' : 'text-emerald-600';
    case 'FAILED': return isDark ? 'text-red-400' : 'text-red-600';
    case 'PROCESSING': return isDark ? 'text-blue-400' : 'text-blue-600';
    default: return 'text-slate-500';
  }
}
