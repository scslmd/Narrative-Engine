import type { ErrorInfo } from '../types/error';
import { getErrorTitle, getErrorMessage, isNetworkError } from '../lib/errorHandling';

interface FallbackProps {
  error: Error;
  errorInfo: ErrorInfo;
  onRetry: () => void;
}

export default function Fallback({ error, errorInfo, onRetry }: FallbackProps) {
  const title = getErrorTitle(error, errorInfo.statusCode);
  const message = isNetworkError(error) 
    ? 'Check your connection and try again'
    : getErrorMessage(error);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
      <svg className="w-16 h-16 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>

      <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
      
      <p className="text-gray-600 mb-4 max-w-md">{message}</p>

      {errorInfo.statusCode && (
        <p className="text-sm text-gray-500 mb-4">Status code: {errorInfo.statusCode}</p>
      )}

      <div className="flex gap-3">
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
        >
          Retry
        </button>

        <a
          href="https://github.com/anomalyco/opencode/issues"
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
        >
          Report Issue
        </a>
      </div>

      <details className="mt-6 text-left max-w-lg w-full">
        <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
          Technical details
        </summary>
        
        <div className="mt-2 p-4 bg-gray-100 rounded text-xs font-mono overflow-auto max-h-64">
          <p className="font-semibold mb-2">Error:</p>
          <pre className="text-gray-700 whitespace-pre-wrap">{errorInfo.errorMessage}</pre>
          
          {errorInfo.componentStack && (
            <>
              <p className="font-semibold mt-3 mb-2">Component Stack:</p>
              <pre className="text-gray-600 whitespace-pre-wrap">{errorInfo.componentStack}</pre>
            </>
          )}
        </div>
      </details>
    </div>
  );
}
