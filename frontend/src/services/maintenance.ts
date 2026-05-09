import api from '../lib/api';
import type {
  MaintenanceScanResult,
  MaintenanceCleanupResult,
  AuditLogTruncationResult,
  DatabaseCompactionResult,
} from '../types/maintenance';

export async function scanOrphans(): Promise<MaintenanceScanResult> {
  const response = await api.get('/v1/projects/maintenance/scan');
  return response.data;
}

export async function cleanupOrphans(projectIds: string[]): Promise<MaintenanceCleanupResult> {
  const response = await api.post('/v1/projects/maintenance/cleanup', { project_ids: projectIds });
  return response.data;
}

export async function truncateAuditLog(retainLines?: number): Promise<AuditLogTruncationResult> {
  const body = retainLines ? { retain_lines: retainLines } : {};
  const response = await api.post('/v1/projects/maintenance/audit-log/truncate', body);
  return response.data;
}

export async function compactDatabase(): Promise<DatabaseCompactionResult> {
  const response = await api.post('/v1/projects/maintenance/database/compact');
  return response.data;
}

