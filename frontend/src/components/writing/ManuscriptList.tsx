import { BookOpen } from 'lucide-react';
import type { ManuscriptDocument } from '../../types/drafting';

/** Extract the first markdown heading from content, stripping P-300-style phase prefixes. */
function extractHeading(content: string): string | null {
  const match = content.match(/^#\s+(?:P-\d+\s*[|–-]\s*)?(.+)$/m);
  return match?.[1]?.trim() || null;
}

interface ManuscriptListProps {
  documents: ManuscriptDocument[];
  selectedDocumentId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  isDark: boolean;
}

export function ManuscriptList({ documents, selectedDocumentId, isLoading, onSelect, isDark }: ManuscriptListProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className={`h-16 rounded-lg animate-shimmer ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}></div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-6 text-muted">
        <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-40" />
        <p className="text-xs">No manuscript records yet</p>
        <p className="text-xs mt-1">Create manuscripts via the drafting workflow.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => {
        const heading = extractHeading(doc.content);
        return (
          <button
            key={doc.document_id}
            onClick={() => onSelect(doc.document_id)}
            className={`w-full text-left p-3 rounded-lg border transition-all duration-150 ${
              selectedDocumentId === doc.document_id
                ? isDark
                  ? 'border-blue-500/50 bg-blue-950/30 shadow-sm'
                  : 'border-blue-400 bg-blue-50/50 shadow-sm'
                : isDark
                  ? 'border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
                  : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
            }`}
          >
            <div className={`font-medium text-sm ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{doc.title}</div>
            {heading && (
              <div className={`text-xs mt-0.5 truncate ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{heading}</div>
            )}
            <div className="text-xs mt-0.5 text-muted">v{doc.version}</div>
          </button>
        );
      })}
    </div>
  );
}
