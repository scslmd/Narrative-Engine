import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { WorkspaceStatus } from '../planning/ui';
import {
  analyzeDocument,
  exportManuscript,
  getExportStatus,
  getPolishReports,
} from '../../services/polish';
import type { ExportStatus, PolishReport } from '../../types/polish';

interface StudioPolishPanelProps {
  projectId: string;
}

export function StudioPolishPanel({ projectId }: StudioPolishPanelProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'analyze' | 'reports' | 'export'>('analyze');
  const [documentId, setDocumentId] = useState('');
  const [documentText, setDocumentText] = useState('');
  const [exportFormat, setExportFormat] = useState('markdown');
  const [exportIncludeFrontmatter, setExportIncludeFrontmatter] = useState(false);
  const [exportIncludeToc, setExportIncludeToc] = useState(false);
  const [exportDocumentId, setExportDocumentId] = useState('');
  const [lastExportId, setLastExportId] = useState<string | null>(null);

  const { data: reports = [], isLoading: reportsLoading } = useQuery<PolishReport[]>({
    queryKey: ['polish-reports', projectId],
    queryFn: () => getPolishReports(projectId),
    enabled: Boolean(projectId) && activeTab === 'reports',
  });

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeDocument({ project_id: projectId, document_id: documentId, text: documentText }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['polish-reports', projectId] });
      setDocumentText('');
      setDocumentId('');
    },
  });

  const exportMutation = useMutation({
    mutationFn: () =>
      exportManuscript(projectId, exportDocumentId, {
        format: exportFormat,
        include_frontmatter: exportIncludeFrontmatter,
        include_toc: exportIncludeToc,
      }),
    onSuccess: (data) => {
      setLastExportId(data.export_id);
      void queryClient.invalidateQueries({ queryKey: ['polish-reports', projectId] });
    },
  });

  const exportStatusQuery = useQuery<ExportStatus>({
    queryKey: ['polish-export', lastExportId],
    queryFn: () => getExportStatus(lastExportId!, projectId),
    enabled: Boolean(lastExportId),
    refetchInterval: 2000,
  });

  if (activeTab === 'reports' && reportsLoading) {
    return <WorkspaceStatus title="Loading reports" detail="Fetching polish reports." />;
  }

  return (
    <div className="flex h-full flex-col">
    <div className="flex shrink-0 border-b border-[var(--border-primary)]">
        {(['analyze', 'reports', 'export'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-2 py-1 text-[9px] font-medium transition-colors ${
              activeTab === tab
                ? 'text-violet-600 dark:text-violet-400 border-b-2 border-violet-500'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-2.5">
        {activeTab === 'analyze' && (
          <AnalyzeTab
            documentId={documentId}
            onDocumentIdChange={setDocumentId}
            documentText={documentText}
            onDocumentTextChange={setDocumentText}
            isPending={analyzeMutation.isPending}
            error={analyzeMutation.error}
            onAnalyze={() => void analyzeMutation.mutateAsync()}
          />
        )}

        {activeTab === 'reports' && (
          <ReportsTab reports={reports} />
        )}

        {activeTab === 'export' && (
          <ExportTab
            exportDocumentId={exportDocumentId}
            onExportDocumentIdChange={setExportDocumentId}
            exportFormat={exportFormat}
            onExportFormatChange={setExportFormat}
            exportIncludeFrontmatter={exportIncludeFrontmatter}
            onExportIncludeFrontmatterChange={setExportIncludeFrontmatter}
            exportIncludeToc={exportIncludeToc}
            onExportIncludeTocChange={setExportIncludeToc}
            isPending={exportMutation.isPending}
            onExport={() => void exportMutation.mutateAsync()}
            exportStatus={exportStatusQuery.data}
          />
        )}
      </div>
    </div>
  );
}

interface AnalyzeTabProps {
  documentId: string;
  onDocumentIdChange: (v: string) => void;
  documentText: string;
  onDocumentTextChange: (v: string) => void;
  isPending: boolean;
  error: Error | null;
  onAnalyze: () => void;
}

function AnalyzeTab({ documentId, onDocumentIdChange, documentText, onDocumentTextChange, isPending, error, onAnalyze }: AnalyzeTabProps) {
  return (
    <div className="space-y-2.5">
      <input
        type="text"
        placeholder="Document ID"
        value={documentId}
        onChange={(e) => onDocumentIdChange(e.target.value)}
        className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-violet-400"
      />

      <textarea
        placeholder="Paste document text for analysis..."
        value={documentText}
        onChange={(e) => onDocumentTextChange(e.target.value)}
        rows={12}
        className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-violet-400 resize-none"
      />

      <button
        disabled={!documentText.trim() || !documentId.trim() || isPending}
        onClick={onAnalyze}
        className="w-full px-2 py-1.5 text-xs font-medium rounded bg-violet-500 text-white hover:bg-violet-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {isPending ? 'Analyzing...' : 'Analyze'}
      </button>

      {error && (
        <p className="text-[10px] text-red-500">
          {error.message}
        </p>
      )}
    </div>
  );
}

interface ReportsTabProps {
  reports: PolishReport[];
}

function ReportsTab({ reports }: ReportsTabProps) {
  if (reports.length === 0) {
    return (
      <div className="text-center py-4 text-[10px] text-slate-500 dark:text-slate-400">
        No polish reports. Run an analysis to generate one.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-2">
      {reports.map((report) => (
        <div
          key={report.report_id}
          className="rounded-lg border p-2.5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-900 dark:text-slate-100">
              {report.document_id}
            </span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-violet-100 text-violet-700 dark:bg-violet-900 dark:text-violet-300">
              Score: {report.readability_score.toFixed(1)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-1 mt-2">
            <Metric label="Words" value={report.word_count} />
            <Metric label="Sentences" value={report.sentence_count} />
            <Metric label="Avg Length" value={report.avg_sentence_length.toFixed(1)} />
            <Metric label="Passive Voice" value={report.passive_voice_count} />
          </div>

          {report.repetitive_words.length > 0 && (
            <div className="mt-2">
              <p className="text-[9px] text-slate-500 dark:text-slate-400">Repetitive words:</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {report.repetitive_words.map((word) => (
                  <span
                    key={word}
                    className="text-[9px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                  >
                    {word}
                  </span>
                ))}
              </div>
            </div>
          )}

          {report.style_issues.length > 0 && (
            <div className="mt-2">
              <p className="text-[9px] text-slate-500 dark:text-slate-400">Style issues:</p>
              <ul className="mt-1 space-y-0.5">
                {report.style_issues.map((issue) => (
                  <li key={issue} className="text-[9px] text-red-500 dark:text-red-400">
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[9px] mt-2 text-slate-400 dark:text-slate-500">
            {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}

interface MetricProps {
  label: string;
  value: string | number;
}

function Metric({ label, value }: MetricProps) {
  return (
    <div className="text-[9px] px-1.5 py-0.5 rounded bg-slate-50 dark:bg-slate-800">
      <span className="text-slate-500 dark:text-slate-400">{label}:</span>{' '}
      <span className="font-medium text-slate-700 dark:text-slate-200">{value}</span>
    </div>
  );
}

interface ExportTabProps {
  exportDocumentId: string;
  onExportDocumentIdChange: (v: string) => void;
  exportFormat: string;
  onExportFormatChange: (v: string) => void;
  exportIncludeFrontmatter: boolean;
  onExportIncludeFrontmatterChange: (v: boolean) => void;
  exportIncludeToc: boolean;
  onExportIncludeTocChange: (v: boolean) => void;
  isPending: boolean;
  onExport: () => void;
  exportStatus: ExportStatus | undefined;
}

function ExportTab({
  exportDocumentId,
  onExportDocumentIdChange,
  exportFormat,
  onExportFormatChange,
  exportIncludeFrontmatter,
  onExportIncludeFrontmatterChange,
  exportIncludeToc,
  onExportIncludeTocChange,
  isPending,
  onExport,
  exportStatus,
}: ExportTabProps) {
  return (
    <div className="space-y-2.5">
      <input
        type="text"
        placeholder="Document ID"
        value={exportDocumentId}
        onChange={(e) => onExportDocumentIdChange(e.target.value)}
        className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-violet-400"
      />

      <select
        value={exportFormat}
        onChange={(e) => onExportFormatChange(e.target.value)}
        className="w-full px-2 py-1 text-xs rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-violet-400"
      >
        <option value="markdown">Markdown</option>
        <option value="html">HTML</option>
        <option value="pdf">PDF</option>
        <option value="docx">DOCX</option>
      </select>

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={exportIncludeFrontmatter}
          onChange={(e) => onExportIncludeFrontmatterChange(e.target.checked)}
          className="w-3 h-3 rounded border-slate-300 dark:border-slate-600 text-violet-500 focus:ring-violet-400"
        />
        <span className="text-[10px] text-slate-600 dark:text-slate-300">Include frontmatter</span>
      </label>

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={exportIncludeToc}
          onChange={(e) => onExportIncludeTocChange(e.target.checked)}
          className="w-3 h-3 rounded border-slate-300 dark:border-slate-600 text-violet-500 focus:ring-violet-400"
        />
        <span className="text-[10px] text-slate-600 dark:text-slate-300">Include table of contents</span>
      </label>

      <button
        disabled={!exportDocumentId.trim() || isPending}
        onClick={onExport}
        className="w-full px-2 py-1.5 text-xs font-medium rounded bg-violet-500 text-white hover:bg-violet-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {isPending ? 'Exporting...' : 'Export'}
      </button>

      {exportStatus && (
        <div className="rounded-lg border p-2.5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-900 dark:text-slate-100">
              Export Status
            </span>
            <span className={`text-[9px] px-1.5 py-0.5 rounded ${
              exportStatus.status === 'completed'
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300'
                : exportStatus.status === 'failed'
                  ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                  : 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300'
            }`}>
              {exportStatus.status}
            </span>
          </div>

          <div className="mt-1.5 space-y-1">
            <p className="text-[10px] text-slate-500 dark:text-slate-400">
              Format: {exportStatus.format}
            </p>
            {exportStatus.artifact_path && (
              <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">
                Path: {exportStatus.artifact_path}
              </p>
            )}
            {exportStatus.error_message && (
              <p className="text-[10px] text-red-500">
                {exportStatus.error_message}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
