import { useState, useRef, useEffect } from 'react';
import { useJobLogs } from '../../hooks/useJobLogs';
import LogEntry from './LogEntry';

interface JobLogsViewerProps {
  jobId: string;
}

type LogLevel = 'All' | 'INFO' | 'WARNING' | 'ERROR';

export default function JobLogsViewer({ jobId }: JobLogsViewerProps) {
  const { logs, isLoading } = useJobLogs(jobId);
  const [filterLevel, setFilterLevel] = useState<LogLevel>('All');
  const [searchText, setSearchText] = useState('');
  const [pauseAutoScroll, setPauseAutoScroll] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!pauseAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, pauseAutoScroll]);

  const filteredLogs = logs.filter((log) => {
    const matchesLevel = filterLevel === 'All' || log.level === filterLevel;
    const matchesSearch = searchText === '' || 
      log.message.toLowerCase().includes(searchText.toLowerCase());
    return matchesLevel && matchesSearch;
  });

  const exportLogs = () => {
    const content = logs.map((log) => 
      `${log.timestamp} | ${log.level} | ${log.message}`
    ).join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `job-${jobId}-logs.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3 py-2 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-24" />
            <div className="h-4 bg-gray-200 rounded w-16" />
            <div className="flex-1 h-4 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b space-y-3">
        <div className="flex items-center gap-2">
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value as LogLevel)}
            className="px-2 py-1 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="All">All Levels</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>

          <input
            type="text"
            placeholder="Search logs..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="flex-1 px-2 py-1 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
          />

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={pauseAutoScroll}
              onChange={(e) => setPauseAutoScroll(e.target.checked)}
            />
            Pause auto-scroll
          </label>

          <button
            onClick={exportLogs}
            disabled={logs.length === 0}
            className="px-3 py-1 text-sm bg-gray-100 border rounded hover:bg-gray-200 disabled:opacity-50"
          >
            Export Logs
          </button>
        </div>

        <p className="text-xs text-gray-500">
          {filteredLogs.length} of {logs.length} entries shown
        </p>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-2 bg-gray-50">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No logs available yet
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <LogEntry key={index} {...log} />
          ))
        )}
      </div>
    </div>
  );
}
