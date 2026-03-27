export interface ErrorInfo {
  componentStack?: string;
  errorMessage?: string;
  statusCode?: number;
}

export type ErrorType = 'network' | 'api' | 'unknown';
