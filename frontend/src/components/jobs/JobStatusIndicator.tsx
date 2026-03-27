import type { JobStatusResponse } from '../../types/job';

interface JobStatusIndicatorProps {
  status: JobStatusResponse['status'] | null;
  isPolling?: boolean;
}

export default function JobStatusIndicator({ status, isPolling }: JobStatusIndicatorProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'QUEUED':
        return 'bg-gray-100 text-gray-700 border-gray-300';
      case 'RUNNING':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'COMPLETED':
        return 'bg-green-100 text-green-700 border-green-300';
      case 'FAILED':
        return 'bg-red-100 text-red-700 border-red-300';
      default:
        return 'bg-gray-50 text-gray-500 border-gray-200';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'QUEUED':
        return <span className="w-2 h-2 rounded-full bg-gray-400" />;
      case 'RUNNING':
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
