import { useState, useEffect, useRef } from 'react';
import { submitExportImport, getExportImportStatus } from '../../services/projectIO';
import { X, Upload, AlertCircle } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '../../hooks/useToast';

interface ImportProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ImportProjectModal({
  isOpen,
  onClose,
}: ImportProjectModalProps): React.ReactElement {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const [projectName, setProjectName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  useEffect(() => {
    if (!isOpen) {
      setProjectName('');
      setFile(null);
      setFileName(null);
      setError(null);
      setPhase('');
    }
  }, [isOpen]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.zip')) {
      setError('Only .zip files are accepted.');
      return;
    }

    setFile(selectedFile);
    setFileName(selectedFile.name);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!file) {
      setError('Please select a ZIP file.');
      return;
    }

    if (!projectName.trim()) {
      setError('Project name is required.');
      return;
    }

    setIsImporting(true);

    try {
      const submit = await submitExportImport(file, projectName.trim());

      pollRef.current = setInterval(async () => {
        try {
          const progress = await getExportImportStatus(submit.import_id);
          setPhase(progress.phase || 'Processing...');

          if (progress.status === 'completed' && progress.result) {
            if (pollRef.current) clearInterval(pollRef.current);
            setIsImporting(false);
            addToast(`Project imported: ${progress.result.project_name}`, 'success');
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            onClose();
          } else if (progress.status === 'failed') {
            if (pollRef.current) clearInterval(pollRef.current);
            setIsImporting(false);
            const errorMsg = progress.error || 'Import failed';
            setError(errorMsg);
            addToast(errorMsg, 'error');
          }
        } catch {
          // Keep polling on transient errors
        }
      }, 2000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Import failed unexpectedly.';
      setError(message);
    } finally {
      if (!isImporting && pollRef.current) {
        clearInterval(pollRef.current);
        setIsImporting(false);
      }
    }
  };

  if (!isOpen) return <></>;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-xl border bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-card">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Import Project</h2>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <Upload className="w-3.5 h-3.5" />
              ZIP File
            </label>
            {fileName ? (
              <div className="flex items-center justify-between px-3 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
                <span className="text-sm text-slate-700 dark:text-slate-300">{fileName}</span>
                <button type="button" onClick={() => { setFile(null); setFileName(null); }} className="text-slate-400 hover:text-red-500">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center px-6 py-8 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg hover:border-indigo-400 dark:hover:border-indigo-500 cursor-pointer transition-colors">
                <Upload className="w-6 h-6 text-slate-400 mb-2" />
                <span className="text-sm text-slate-500">Click to browse or drag a .zip file</span>
                <input type="file" accept=".zip" onChange={handleFileSelect} className="hidden" />
              </label>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Project Name
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Enter project name..."
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
            />
          </div>

          {error && (
            <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800">
              <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}

          {isImporting && (
            <div className="flex flex-col items-center py-6">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
              <p className="mt-3 text-sm text-slate-500">{phase || 'Processing...'}</p>
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button type="button" onClick={onClose} disabled={isImporting} className="px-5 py-2.5 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-60">
              Cancel
            </button>
            <button type="submit" disabled={isImporting || !file} className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-600 text-white text-sm font-medium rounded-lg hover:from-indigo-600 hover:to-violet-700 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed">
              <Upload className="w-4 h-4" />
              {isImporting ? 'Processing...' : 'Import Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
