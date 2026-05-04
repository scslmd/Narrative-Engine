import { describe, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import { exportProject, submitExportImport, getExportImportStatus } from './projectIO';

vi.mock('../lib/download', () => ({
  downloadBlob: vi.fn(),
  downloadTextFile: vi.fn(),
  downloadJsonFile: vi.fn(),
}));

const mockSubmitResponse = { import_id: 'imp-1', status: 'pending' };

const mockProgressResponse = {
  import_id: 'imp-1',
  status: 'running',
  phase: 'validating_zip',
  export_version: null,
  created_at: null,
  original_project_id: null,
  result: null,
  error: null,
};

describe('exportProject', () => {
  it('exports project as blob download (200)', async () => {
    const blob = new Blob(['fake zip'], { type: 'application/zip' });
    server.use(
      http.post('/projects/proj-1/export', () =>
        new Response(blob, {
          status: 200,
          headers: {
            'content-type': 'application/zip',
            'content-disposition': 'attachment; filename="test-export.zip"',
          },
        }),
      ),
    );

    await expect(exportProject('proj-1')).resolves.toBeUndefined();
  });
});

describe('submitExportImport', () => {
  it('submits ZIP file and returns import_id (202)', async () => {
    server.use(
      http.post('/projects/import-export', () =>
        HttpResponse.json(mockSubmitResponse, { status: 202 }),
      ),
    );

    const file = new File(['zip content'], 'test.zip', { type: 'application/zip' });
    const result = await submitExportImport(file, 'Test Project');
    expect(result.import_id).toBe('imp-1');
    expect(result.status).toBe('pending');
  });

  it('submits without projectName when omitted (202)', async () => {
    server.use(
      http.post('/projects/import-export', () =>
        HttpResponse.json(mockSubmitResponse, { status: 202 }),
      ),
    );

    const file = new File(['zip content'], 'test.zip', { type: 'application/zip' });
    const result = await submitExportImport(file);
    expect(result.import_id).toBe('imp-1');
  });
});

describe('getExportImportStatus', () => {
  it('returns progress state (200)', async () => {
    server.use(
      http.get('/projects/export/imp-1', () =>
        HttpResponse.json(mockProgressResponse, { status: 200 }),
      ),
    );

    const result = await getExportImportStatus('imp-1');
    expect(result.status).toBe('running');
    expect(result.phase).toBe('validating_zip');
  });

  it('returns completed state with result (200)', async () => {
    const completed = {
      ...mockProgressResponse,
      status: 'completed',
      phase: null,
      export_version: 1,
      created_at: '2026-05-04T00:00:00Z',
      original_project_id: 'proj-1',
      result: { project_id: 'imported-proj', project_name: 'Test Project', export_version: 1 },
    };
    server.use(
      http.get('/projects/export/imp-2', () =>
        HttpResponse.json(completed, { status: 200 }),
      ),
    );

    const result = await getExportImportStatus('imp-2');
    expect(result.status).toBe('completed');
    expect(result.result?.project_id).toBe('imported-proj');
  });

  it('returns failed state with error (200)', async () => {
    const failed = {
      ...mockProgressResponse,
      status: 'failed',
      phase: null,
      error: 'Invalid ZIP file format',
    };
    server.use(
      http.get('/projects/export/imp-3', () =>
        HttpResponse.json(failed, { status: 200 }),
      ),
    );

    const result = await getExportImportStatus('imp-3');
    expect(result.status).toBe('failed');
    expect(result.error).toBe('Invalid ZIP file format');
  });
});
