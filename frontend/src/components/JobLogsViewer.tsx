import { useState, useEffect, useRef } from 'react';
import { useJobLogs } from '../hooks/useJobs';

interface Props {
  jobId: string;
}

export function JobLogsViewer({ jobId }: Props): React.ReactElement {
  const { data: logs, isLoading } = useJobLogs(jobId);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isAutoScrolling, setIsAutoScrolling] = useState(true);

  useEffect(() => {
    if (isAutoScrolling && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isAutoScrolling]);

  const handleLogsContainerScroll = (): void => {
    const container = document.getElementById('logs-container');
    if (container) {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const nearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setIsAutoScrolling(nearBottom);
    }
  };

  const copyToClipboard = (): void => {
    if (logs) {
      const logText = logs.entries.map(e => `[${e.timestamp}] [${e.level}] ${e.message}`).join('\n');
      navigator.clipboard.writeText(logText);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg shadow overflow-hidden flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <h3 className="text-sm font-medium text-white">Job Logs</h3>
        <button
          onClick={copyToClipboard}
          disabled={!logs || logs.entries.length === 0}
          className="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50"
        >
          Copy
        </button>
      </div>

      <div
        id="logs-container"
        onScroll={handleLogsContainerScroll}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm"
      >
        {isLoading ? (
          <p className="text-gray-500">Loading logs...</p>
        ) : logs && logs.entries.length > 0 ? (
          <>
            <pre className="text-green-400 whitespace-pre-wrap">{logs.entries.map(e => `[${e.timestamp}] [${e.level}] ${e.message}`).join('\n')}</pre>
            <div ref={logsEndRef} />
          </>
        ) : (
          <p className="text-gray-500">No logs available</p>
        )}
      </div>

      {isAutoScrolling && (
        <div className="px-4 py-1 bg-blue-600 text-white text-xs text-center">
          Auto-scrolling enabled
        </div>
      )}
    </div>
  );
}
