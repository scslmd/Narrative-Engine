import { Edit3, Save, X, Sparkles } from 'lucide-react';
import type { ManuscriptDocument, RevisionSuggestion } from '../../types/drafting';

interface ManuscriptEditorProps {
  document: ManuscriptDocument;
  isEditing: boolean;
  editContent: string;
  wordCount: number;
  charCount: number;
  openSuggestions: RevisionSuggestion[];
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onContentChange: (content: string) => void;
  isDark: boolean;
}

export function ManuscriptEditor({
  document,
  isEditing,
  editContent,
  wordCount,
  charCount,
  openSuggestions,
  onEdit,
  onSave,
  onCancel,
  onContentChange,
  isDark,
}: ManuscriptEditorProps) {
  return (
    <>
      <header className={`flex items-center justify-between px-5 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
        <div>
          <h2 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>{document.title}</h2>
          {document.chapter_id && (
            <p className={`text-xs mt-0.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Chapter: {document.chapter_id}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isEditing && (
            <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              {wordCount} words / {charCount} chars
            </span>
          )}
          {!isEditing && (
            <span className={`text-xs px-2 py-1 rounded-md ${isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>
              v{document.version}
            </span>
          )}
          {openSuggestions.length > 0 && !isEditing && (
            <div className="flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{openSuggestions.length}</span>
            </div>
          )}
          {!isEditing && (
            <button
              onClick={onEdit}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors bg-blue-600 hover:bg-blue-500 text-white`}
            >
              <Edit3 className="w-3.5 h-3.5" />
              Edit
            </button>
          )}
        </div>
      </header>

      {isEditing ? (
        <>
          <div className={`flex items-center gap-2 px-5 py-2 border-b ${isDark ? 'border-slate-800 bg-slate-900/50' : 'border-slate-200 bg-slate-50'}`}>
            <button
              onClick={onSave}
              className="flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
            >
              <Save className="w-3.5 h-3.5" />
              Save
            </button>
            <button
              onClick={onCancel}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                isDark
                  ? 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                  : 'bg-slate-200 hover:bg-slate-300 text-slate-700'
              }`}
            >
              <X className="w-3.5 h-3.5" />
              Cancel
            </button>
          </div>
          <main className={`flex-1 overflow-hidden`}>
            <textarea
              value={editContent}
              onChange={(e) => onContentChange(e.target.value)}
              className={`w-full h-full p-6 resize-none outline-none text-sm leading-relaxed ${
                isDark
                  ? 'bg-slate-900 text-slate-300'
                  : 'bg-white text-slate-800'
              }`}
              spellCheck
              placeholder="Start writing or paste your content here..."
            />
          </main>
        </>
      ) : (
        <main className={`flex-1 overflow-y-auto p-6`}>
          <div className={`prose max-w-none ${isDark ? 'text-slate-300' : 'text-slate-800'}`}>
            <pre className={`whitespace-pre-wrap font-sans text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              {document.content || <span className={isDark ? 'text-slate-600' : 'text-slate-400'}>(No content)</span>}
            </pre>
          </div>
        </main>
      )}
    </>
  );
}
