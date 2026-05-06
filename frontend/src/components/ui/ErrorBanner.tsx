import { useEffect, useState } from 'react';
import { X, AlertCircle, ShieldAlert } from 'lucide-react';
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

  const isAuthError = error.status === 401;

  return (
    <div className={`flex items-start gap-3 px-4 py-3 border rounded-lg ${isAuthError ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200'}`}>
      {isAuthError ? (
        <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
      ) : (
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${isAuthError ? 'text-amber-900' : 'text-red-800'}`}>
          {isAuthError ? 'API key required' : error.status ? `[${error.status}] ${error.message}` : error.message}
        </p>
        {isAuthError && (
          <p className="text-xs text-amber-700 mt-1">
            This feature requires API authentication. Create a key in <strong>Settings &gt; API Keys</strong>, then set the <code className="px-1 py-0.5 bg-amber-100 rounded text-[10px]">NARRATIVE_API_KEY</code> environment variable on your server. See <strong>User Guide §Authentication</strong>.
          </p>
        )}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {onRetry && (
          <button
            onClick={onRetry}
            className={`text-sm font-medium transition-colors ${isAuthError ? 'text-amber-700 hover:text-amber-900' : 'text-red-700 hover:text-red-900'}`}
          >
            Retry
          </button>
        )}
        <button
          onClick={() => setVisible(false)}
          className="opacity-60 hover:opacity-100 transition-opacity"
          aria-label="Dismiss"
        >
          <X className={`w-4 h-4 ${isAuthError ? 'text-amber-500' : 'text-red-500'}`} />
        </button>
      </div>
    </div>
  );
}
