import api from '../lib/api';
import type {
  MaintenanceScanResult,
  MaintenanceCleanupResult,
  AuditLogTruncationResult,
  DatabaseCompactionResult,
} from '../types/maintenance';

export async function scanOrphans(): Promise<MaintenanceScanResult> {
  const response = await api.get('/projects/maintenance/scan');
  return response.data;
}

export async function cleanupOrphans(projectIds: string[]): Promise<MaintenanceCleanupResult> {
  const response = await api.post('/projects/maintenance/cleanup', { project_ids: projectIds });
  return response.data;
}

export async function truncateAuditLog(retainLines?: number): Promise<AuditLogTruncationResult> {
  const body = retainLines ? { retain_lines: retainLines } : {};
  const response = await api.post('/projects/maintenance/audit-log/truncate', body);
  return response.data;
}

export async function compactDatabase(): Promise<DatabaseCompactionResult> {
  const response = await api.post('/projects/maintenance/database/compact');
  return response.data;
}
