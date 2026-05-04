import api from '../lib/api';
import { downloadBlob } from '../lib/download';
import type { ExportImportSubmitResponse, ExportImportProgressResponse } from '../types/projectIO';

export async function exportProject(projectId: string): Promise<void> {
  const response = await api.post(`/projects/${projectId}/export`, null, {
    responseType: 'blob',
    timeout: 600_000,
  });

  const contentDisposition = response.headers['content-disposition'] || '';
  const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
  const filename = filenameMatch ? filenameMatch[1] : 'project-export.zip';

  downloadBlob(response.data as Blob, filename);
}

export async function submitExportImport(
  file: File,
  projectName?: string,
): Promise<ExportImportSubmitResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (projectName) {
    formData.append('project_name', projectName);
  }

  const response = await api.post('/projects/import-export', formData);

  return response.data;
}

export async function getExportImportStatus(
  importId: string,
): Promise<ExportImportProgressResponse> {
  const response = await api.get(`/projects/export/${importId}`);
  return response.data;
}
