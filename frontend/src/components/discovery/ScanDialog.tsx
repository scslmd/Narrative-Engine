import { useState } from 'react';
import type { CascadeScanRequest } from '../../types/discovery';

interface ScanDialogProps {
  projectId: string;
  onSubmit: (request: CascadeScanRequest) => void;
  onClose: () => void;
  isLoading?: boolean;
}

export function ScanDialog({ projectId, onSubmit, onClose, isLoading }: ScanDialogProps) {
  const [text, setText] = useState('');
  const [chunkSize, setChunkSize] = useState(8000);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      project_id: projectId,
      manuscript_text: text,
      chunk_size: chunkSize,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-2xl mx-4" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Scan Manuscript</h2>
        <form onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Manuscript Text</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full h-64 p-3 border rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600 resize-none focus:ring-2 focus:ring-blue-500"
            placeholder="Paste your manuscript or chapter text here..."
            required
            minLength={50}
          />
          <div className="mt-4 flex items-center gap-4">
            <label className="text-sm text-gray-700 dark:text-gray-300">Chunk size (words):</label>
            <input
              type="number"
              value={chunkSize}
              onChange={(e) => setChunkSize(Number(e.target.value))}
              min={1000}
              max={50000}
              step={1000}
              className="w-24 p-1 border rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600"
            />
          </div>
          <div className="mt-6 flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
              Cancel
            </button>
            <button type="submit" disabled={isLoading || text.length < 50} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
              {isLoading ? 'Scanning...' : 'Start Scan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
