import type { ErrorInfo } from '../types/error';

export function logError(error: Error, info: ErrorInfo): void {
  console.error('Component error:', {
    message: error.message,
    errorMessage: info.errorMessage,
    statusCode: info.statusCode,
    componentStack: info.componentStack,
  });
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred';
}

export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes('network') ||
      error.message.includes('fetch') ||
      error.message.includes('Failed to fetch')
    );
  }
  
  return false;
}

export function getErrorTitle(error: unknown, statusCode?: number): string {
  if (isNetworkError(error)) {
    return 'Connection Error';
  }
  
  if (statusCode === 404) {
    return 'Not Found';
  }
  
  if (statusCode === 500) {
    return 'Server Error';
  }
  
  if (statusCode && statusCode >= 400 && statusCode < 500) {
    return `Client Error (${statusCode})`;
  }
  
  if (statusCode && statusCode >= 500) {
    return `Server Error (${statusCode})`;
  }
  
  return 'Something went wrong';
}
