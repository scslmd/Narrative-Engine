import type {
  ExportStatus,
  PolishAnalyzeRequest,
  PolishReport,
  PolishReportListResponse,
} from '../types/polish';
import api from '../lib/api';

export async function analyzeDocument(
  request: PolishAnalyzeRequest,
): Promise<PolishReport> {
  const response = await api.post('/story-development/polish/analyze', request);

  return response.data;
}

export async function getPolishReports(
  projectId: string,
  documentId?: string,
): Promise<PolishReport[]> {
  const params: Record<string, string> = { project_id: projectId };
  if (documentId) params.document_id = documentId;

  const response = await api.get('/story-development/polish/reports', { params });

  const data: PolishReportListResponse = response.data;
  return data.items;
}

export async function exportManuscript(
  projectId: string,
  documentId: string,
  options: {
    format: string;
    include_frontmatter?: boolean;
    include_toc?: boolean;
    stylesheet?: string | null;
  },
): Promise<ExportStatus> {
  const response = await api.post('/story-development/polish/export', {
    project_id: projectId,
    document_id: documentId,
    ...options,
  });

  return response.data;
}

export async function getExportStatus(
  exportId: string,
  projectId?: string,
): Promise<ExportStatus> {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;

  const response = await api.get(`/story-development/polish/export/${exportId}`, { params });

  return response.data;
}
