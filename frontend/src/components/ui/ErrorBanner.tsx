import { useEffect, useState } from 'react';
import { X, AlertCircle } from 'lucide-react';
import type { ApiError } from '../../lib/api';

interface ErrorBannerProps {
  error: ApiError | null;
  onRetry?: () => void;
}

export function ErrorBanner({ error, onRetry }: ErrorBannerProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (!error) return;
    setVisible(true);
    const timer = setTimeout(() => {
      setVisible(false);
    }, 30000);
    return () => clearTimeout(timer);
  }, [error]);

  if (!error || !visible) return null;

  const message = error.status ? `[${error.status}] ${error.message}` : error.message;

  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-lg">
      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
      <span className="text-sm text-red-800 flex-1">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-sm font-medium text-red-700 hover:text-red-900 transition-colors"
        >
          Retry
        </button>
      )}
      <button
        onClick={() => setVisible(false)}
        className="opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4 text-red-500" />
      </button>
    </div>
  );
}
