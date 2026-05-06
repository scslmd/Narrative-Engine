import type { ErrorInfo, ErrorType } from '../types/error';
import { ApiError } from './api';

export function classifyError(error: unknown): ErrorType {
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return 'network';
  }
  if (error instanceof ApiError) {
    if (error.status >= 500) return 'server';
    if (error.status === 404) return 'not-found';
    if (error.status === 401 || error.status === 403) return 'auth';
    if (error.status >= 400 && error.status < 500) return 'validation';
  }
  return 'unknown';
}

export function isNetworkError(error: unknown): boolean {
  return error instanceof TypeError && error.message.includes('fetch');
}

export function getStatusCode(error: unknown): number | undefined {
  if (error instanceof ApiError) {
    return error.status;
  }
  return undefined;
}

export function getErrorTitle(error: unknown, statusCode?: number): string {
  const status = statusCode ?? getStatusCode(error);
  
  if (isNetworkError(error)) return 'Connection Error';
  if (status === 401) return 'API Key Required';
  if (status === 403) return 'Access Denied';
  if (status === 404) return 'Not Found';
  if (status === 409) return 'Conflict';
  if (status && status >= 500) return 'Server Error';
  if (status && status >= 400) return `Bad Request (${status})`;
  return 'Something Went Wrong';
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function formatErrorMessage(error: unknown, statusCode?: number): string {
  const status = statusCode ?? getStatusCode(error);
  
  if (!status) return error instanceof Error ? error.message : 'An unexpected error occurred';
  if (status === 401) return 'API key required. Create one in Settings > API Keys, then set the NARRATIVE_API_KEY environment variable on your server. See User Guide §Authentication.';
  if (status === 403) return 'You do not have permission to access this resource';
  if (status === 404) return 'The requested resource was not found';
  if (status === 409) return 'This operation cannot be completed due to a conflict';
  if (status >= 500) return 'A server error occurred. Please try again later.';
  if (status >= 400) return `Bad request: ${error}`;
  return error instanceof Error ? error.message : 'An unexpected error occurred';
}

export function logError(component: string, error: unknown, info?: Partial<ErrorInfo>): void {
  console.error(`[${component}] Error:`, error);
  if (info?.componentStack) {
    console.error('Component stack:', info.componentStack);
  }
}
