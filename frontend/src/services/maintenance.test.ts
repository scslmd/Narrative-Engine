import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { scanOrphans, cleanupOrphans, truncateAuditLog, compactDatabase } from './maintenance';
import type { MaintenanceScanResult, MaintenanceCleanupResult, AuditLogTruncationResult, DatabaseCompactionResult } from '../types/maintenance';

const mockScanResult: MaintenanceScanResult = {
  orphaned_dirs: [
    { project_id: 'proj-orphan-1', project_name: 'Orphaned Project', kind: 'orphaned_dir', size_bytes: 4096 },
  ],
  db_only: [
    { project_id: 'proj-db-1', project_name: 'DB Only Project', kind: 'db_only', size_bytes: 2048 },
  ],
  disk_only: [
    { project_id: 'proj-disk-1', project_name: null, kind: 'disk_only', size_bytes: 8192 },
  ],
  summary: {
    audit_log_lines: 50000,
    audit_log_retain_lines: 10000,
    database_size_bytes: 1048576,
    checker_report_files: 12,
    total_jobs: 250,
    total_checker_runs: 80,
  },
};

const mockCleanupResult: MaintenanceCleanupResult = {
  removed: 2,
  errors: [{ project_id: 'proj-error-1', error: 'Permission denied' }],
};

const mockTruncateResult: AuditLogTruncationResult = {
  truncated: 40000,
  retained: 10000,
};

const mockCompactResult: DatabaseCompactionResult = {
  before_bytes: 1048576,
  after_bytes: 524288,
};

describe('maintenance service', () => {
  describe('scanOrphans', () => {
    it('returns scan result with summary', async () => {
      server.use(
        http.get('/v1/projects/maintenance/scan', () => {
          return HttpResponse.json(mockScanResult);
        }),
      );

      const result = await scanOrphans();

      expect(result.orphaned_dirs).toHaveLength(1);
      expect(result.db_only).toHaveLength(1);
      expect(result.disk_only).toHaveLength(1);
      expect(result.summary.total_jobs).toBe(250);
      expect(result.summary.audit_log_lines).toBe(50000);
    });

    it('throws ApiError on 500 error', async () => {
      server.use(
        http.get('/v1/projects/maintenance/scan', () => {
          return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
        }),
      );

      await expect(scanOrphans()).rejects.toThrow();
    });
  });

  describe('cleanupOrphans', () => {
    it('sends project_ids and returns cleanup result', async () => {
      server.use(
        http.post('/v1/projects/maintenance/cleanup', async ({ request }) => {
          const body = (await request.json()) as { project_ids: string[] };
          expect(body.project_ids).toEqual(['proj-1', 'proj-2']);
          return HttpResponse.json(mockCleanupResult);
        }),
      );

      const result = await cleanupOrphans(['proj-1', 'proj-2']);

      expect(result.removed).toBe(2);
      expect(result.errors).toHaveLength(1);
    });
  });

  describe('truncateAuditLog', () => {
    it('sends retain_lines and returns truncation result', async () => {
      server.use(
        http.post('/v1/projects/maintenance/audit-log/truncate', async ({ request }) => {
          const body = (await request.json()) as { retain_lines?: number };
          expect(body.retain_lines).toBe(5000);
          return HttpResponse.json(mockTruncateResult);
        }),
      );

      const result = await truncateAuditLog(5000);

      expect(result.truncated).toBe(40000);
      expect(result.retained).toBe(10000);
    });
  });

  describe('compactDatabase', () => {
    it('sends empty body and returns compaction result', async () => {
      server.use(
        http.post('/v1/projects/maintenance/database/compact', async ({ request }) => {
          const text = await request.text();
          expect(text).toBe('');
          return HttpResponse.json(mockCompactResult);
        }),
      );

      const result = await compactDatabase();

      expect(result.before_bytes).toBe(1048576);
      expect(result.after_bytes).toBe(524288);
    });
  });
});

