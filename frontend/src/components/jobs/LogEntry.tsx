interface LogEntryProps {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR';
  message: string;
}

export default function LogEntry({ timestamp, level, message }: LogEntryProps) {
  const getLevelStyles = () => {
    switch (level) {
      case 'INFO':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'ERROR':
        return 'bg-red-100 text-red-700 border-red-200';
    }
  };

  const formatTimestamp = (ts: string) => {
    try {
      const date = new Date(ts);
      return date.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3,
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="flex gap-3 py-1 text-sm">
      <span className="text-gray-500 font-mono text-xs whitespace-nowrap w-24">
        {formatTimestamp(timestamp)}
      </span>
      
      <span className={`px-2 py-0.5 rounded border text-xs font-medium flex-shrink-0 ${getLevelStyles()}`}>
        {level}
      </span>
      
      <span className="flex-1 font-mono break-all">{message}</span>
    </div>
  );
}
