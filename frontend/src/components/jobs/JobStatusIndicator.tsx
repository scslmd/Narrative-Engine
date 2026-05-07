import type { JobStatusResponse } from '../../types/job';

interface JobStatusIndicatorProps {
  status: JobStatusResponse['status'] | null;
  isPolling?: boolean;
}

export default function JobStatusIndicator({ status, isPolling }: JobStatusIndicatorProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'PENDING':
        return 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 border-gray-300 dark:border-slate-600';
      case 'PROCESSING':
        return 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-800';
      case 'COMPLETED':
        return 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 border-green-300 dark:border-green-800';
      case 'FAILED':
        return 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-300 dark:border-red-800';
      default:
        return 'bg-gray-50 dark:bg-slate-900 text-gray-500 dark:text-slate-400 border-gray-200 dark:border-slate-700';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'PENDING':
        return <span className="w-2 h-2 rounded-full bg-gray-400" />;
      case 'PROCESSING':
        return isPolling ? (
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
          </span>
        ) : (
          <span className="w-2 h-2 rounded-full bg-blue-500" />
        );
      case 'COMPLETED':
        return <span className="w-2 h-2 rounded-full bg-green-500" />;
      case 'FAILED':
        return <span className="w-2 h-2 rounded-full bg-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium ${getStatusStyles()}`}>
      {getStatusIcon()}
      <span>{status || 'Unknown'}</span>
    </div>
  );
}
