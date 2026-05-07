import { Edit3, Save, X, Sparkles } from 'lucide-react';
import type { ManuscriptDocument, RevisionSuggestion } from '../../types/drafting';
import type { ManuscriptAssistKind, TextRange } from '../../types/manuscriptAssist';

interface MarkdownRenderProps {
  content: string;
  isDark: boolean;
}

/** Lightweight markdown renderer for manuscript read mode. Handles headings, inline code, and paragraphs. */
function renderMarkdown({ content, isDark }: MarkdownRenderProps) {
  if (!content) return <span className={isDark ? 'text-slate-600' : 'text-slate-400'}>(No content)</span>;

  const headingBase = isDark ? 'text-slate-100 font-semibold' : 'text-slate-900 font-semibold';
  const codeBg = isDark ? 'bg-slate-800 text-amber-300' : 'bg-slate-100 text-amber-700';

  const renderInlineCode = (line: string, keyPrefix: string) => {
    const parts = line.split(/(`[^`]+`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={keyPrefix + '-' + i} className={`px-1.5 py-0.5 rounded text-xs font-mono ${codeBg}`}>
            {part.slice(1, -1)}
          </code>
        );
      }
      return <span key={keyPrefix + '-' + i}>{part}</span>;
    });
  };

  const paragraphs = content.split(/\n\n+/);
  const elements: JSX.Element[] = [];
  let idx = 0;

  for (const para of paragraphs) {
    const trimmed = para.trim();
    if (!trimmed) continue;

    // Heading: # ## ###
    const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)$/m);
    if (headingMatch) {
      const level = headingMatch[1].length as 1 | 2 | 3;
      const text = headingMatch[2];
      const sizes: Record<number, string> = {
        1: 'text-xl mt-6 mb-3',
        2: 'text-lg mt-5 mb-2',
        3: 'text-base mt-4 mb-2',
      };
      elements.push(
        <p key={idx} className={`${headingBase} ${sizes[level]}`}>
          {renderInlineCode(text, `h${idx}`)}
        </p>,
      );
      idx++;
      continue;
    }

    // Regular paragraph (may contain newlines within)
    const lines = trimmed.split('\n');
    elements.push(
      <p key={idx} className={`text-sm leading-relaxed mb-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
        {lines.map((line, li) => (
          <span key={li}>
            {renderInlineCode(line, `p${idx}-${li}`)}
            {li < lines.length - 1 && <br />}
          </span>
        ))}
      </p>,
    );
    idx++;
  }

  return <>{elements}</>;
}

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
  onSelectionChange?: (start: number, end: number, content: string) => void;
  onAssistRequest?: (kind: ManuscriptAssistKind, instruction: string) => void;
  selectedRange?: TextRange | null;
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
  onSelectionChange,
  onAssistRequest,
  selectedRange,
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
            {onAssistRequest && (
              <>
                <button
                  onClick={() => onAssistRequest('developmental_review', 'Review this document for developmental improvements.')}
                  className="rounded-md px-2.5 py-1 text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 transition-colors"
                >
                  Assist: Review
                </button>
                <button
                  onClick={() => onAssistRequest('line_edit_selection', 'Tighten and polish this selected passage.')}
                  disabled={!selectedRange}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    selectedRange
                      ? 'bg-violet-600 text-white hover:bg-violet-500'
                      : 'bg-slate-300 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  Assist: Selection
                </button>
                <button
                  onClick={() => onAssistRequest('fork_from_selection', 'Fork a new variant from this selected passage.')}
                  disabled={!selectedRange}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    selectedRange
                      ? 'bg-amber-600 text-white hover:bg-amber-500'
                      : 'bg-slate-300 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  Fork Selection
                </button>
              </>
            )}
          </div>
          <main className={`flex-1 overflow-hidden`}>
            <textarea
              value={editContent}
              onChange={(e) => onContentChange(e.target.value)}
              onSelect={(e) => {
                const target = e.currentTarget;
                onSelectionChange?.(target.selectionStart ?? 0, target.selectionEnd ?? 0, target.value);
              }}
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
          <div className="max-w-none">
            {renderMarkdown({ content: document.content, isDark })}
          </div>
        </main>
      )}
    </>
  );
}
