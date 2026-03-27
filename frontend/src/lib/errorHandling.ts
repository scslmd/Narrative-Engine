import type { ErrorInfo, ErrorType } from '../types/error';

export function classifyError(error: unknown): ErrorType {
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return 'network';
  }
  return 'unknown';
}

export function isNetworkError(error: unknown): boolean {
  return error instanceof TypeError && error.message.includes('fetch');
}

export function getErrorTitle(error: unknown, statusCode?: number): string {
  if (isNetworkError(error)) return 'Connection Error';
  if (statusCode === 404) return 'Not Found';
  if (statusCode === 500) return 'Server Error';
  if (statusCode && statusCode >= 400 && statusCode < 500) return `Bad Request (${statusCode})`;
  return 'Something Went Wrong';
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function formatErrorMessage(error: unknown, statusCode?: number): string {
  if (!statusCode) return error instanceof Error ? error.message : 'An unexpected error occurred';
  if (statusCode === 404) return 'Resource not found';
  if (statusCode === 500) return 'Server error';
  if (statusCode >= 400 && statusCode < 500) return `Bad request: ${error}`;
  return error instanceof Error ? error.message : 'An unexpected error occurred';
}

export function logError(component: string, error: unknown, info?: Partial<ErrorInfo>): void {
  console.error(`[${component}] Error:`, error);
  if (info?.componentStack) {
    console.error('Component stack:', info.componentStack);
  }
}
