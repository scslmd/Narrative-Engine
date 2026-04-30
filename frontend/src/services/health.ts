import api from '../lib/api';

export interface HealthIssue {
  component: string;
  error: string;
}

export interface HealthStatus {
  isReady: boolean;
  isLlmAvailable: boolean;
  backendType: string;
  issues: HealthIssue[];
}

export async function checkHealth(): Promise<HealthStatus> {
  try {
    const response = await api.get('/health/ready');
    const data = response.data;
    const backendType = data?.components?.inference?.backend ?? 'unknown';
    return {
      isReady: true,
      isLlmAvailable: backendType !== 'stub',
      backendType,
      issues: [],
    };
  } catch (error: unknown) {
    const err = error as { response?: { data?: { issues?: HealthIssue[]; detail?: { issues?: HealthIssue[] } } } };
    const detail = err.response?.data;
    const issues = (typeof detail === 'object' && detail !== null && 'issues' in detail)
      ? (detail as { issues: HealthIssue[] }).issues
      : ((detail as { detail?: { issues?: HealthIssue[] } })?.detail?.issues ?? []);
    return {
      isReady: false,
      isLlmAvailable: false,
      backendType: 'unknown',
      issues,
    };
  }
}
