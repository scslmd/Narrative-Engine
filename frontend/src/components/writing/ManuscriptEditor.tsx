import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronDown, ChevronRight, Edit3, Save, X, Sparkles, Wand2 } from 'lucide-react';
import type { ManuscriptDocument, RevisionSuggestion } from '../../types/drafting';
import type { ManuscriptAssistKind, TextRange } from '../../types/manuscriptAssist';
import { ASSIST_ACTIONS, ASSIST_CATEGORIES, type AssistAction } from '../../lib/assistActions';
import { SelectionToolbar } from './SelectionToolbar';

interface MarkdownRenderProps {
  content: string;
  isDark: boolean;
}

function extractChapterTitle(content: string): string | null {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

/** Lightweight markdown renderer for manuscript read mode. Handles headings, inline code, and paragraphs. */
function renderMarkdown({ content, isDark }: MarkdownRenderProps) {
  if (!content) return <span className="text-muted">(No content)</span>;

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
  let lineCounter = 0;

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
      const anchorId = `heading-${lineCounter}`;
      elements.push(
        <div key={idx} id={anchorId} data-line={lineCounter}>
          <p className={`${headingBase} ${sizes[level]}`}>
            {renderInlineCode(text, `h${idx}`)}
          </p>
        </div>,
      );
      idx++;
      lineCounter += para.split('\n').length;
      continue;
    }

    // Regular paragraph (may contain newlines within)
    const lines = trimmed.split('\n');
    elements.push(
      <p key={idx} data-line={lineCounter} className={`text-sm leading-relaxed mb-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
        {lines.map((line, li) => (
          <span key={li}>
            {renderInlineCode(line, `p${idx}-${li}`)}
            {li < lines.length - 1 && <br />}
          </span>
        ))}
      </p>,
    );
    idx++;
    lineCounter += lines.length;
  }

  return <>{elements}</>;
}

interface AssistDropdownProps {
  selectedRange: TextRange | null | undefined;
  isDark: boolean;
  onSelect: (kind: ManuscriptAssistKind, instruction: string) => void;
}

const SENSORY_KINDS: Set<string> = new Set([
  'expand_sensory_sight',
  'expand_sensory_sound',
  'expand_sensory_smell',
  'expand_sensory_texture',
  'expand_sensory_taste',
  'expand_metaphor',
  'expand_show_dont_tell',
]);

function AssistDropdown({ selectedRange, isDark, onSelect }: AssistDropdownProps) {
  const hasSelection = !!(selectedRange && selectedRange.end_offset > selectedRange.start_offset);
  const [open, setOpen] = useState(false);
  const [sensoryMenu, setSensoryMenu] = useState<{ x: number; y: number } | null>(null);

  const renderAction = useCallback((action: AssistAction) => (
    <button
      key={action.kind}
      className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs transition-colors ${
        isDark
          ? 'text-slate-300 hover:bg-slate-700'
          : 'text-slate-700 hover:bg-slate-50'
      }`}
      onClick={() => {
        onSelect(action.kind, action.instructionTemplate(selectedRange!));
        setOpen(false);
        setSensoryMenu(null);
      }}
      title={action.description}
    >
      <Wand2 className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
      <span>{action.label}</span>
    </button>
  ), [isDark, onSelect, selectedRange]);

  return (
    <div className="relative">
      <button
        disabled={!hasSelection}
        onClick={() => hasSelection && setOpen((o) => !o)}
        className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
          hasSelection
            ? isDark
              ? 'bg-violet-600 text-white hover:bg-violet-500'
              : 'bg-violet-600 text-white hover:bg-violet-500'
            : 'bg-slate-300 text-slate-500 cursor-not-allowed dark:bg-slate-700 dark:text-slate-400'
        }`}
      >
        <Wand2 className="w-3.5 h-3.5" />
        Assist
        {open
          ? <ChevronDown className="w-3 h-3" />
          : <ChevronRight className="w-3 h-3" />
        }
      </button>
      {open && hasSelection && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => { setOpen(false); setSensoryMenu(null); }} />
          <div
            className={`absolute right-0 z-50 mt-1 min-w-[260px] rounded-lg border p-2 shadow-lg ${
              isDark ? 'border-slate-700 bg-slate-800' : 'border-slate-200 bg-white'
            }`}
          >
            {ASSIST_CATEGORIES.map((category) => {
              const sensoryActions = category.actions.filter((a) => SENSORY_KINDS.has(a.kind));
              const otherActions = category.actions.filter((a) => !SENSORY_KINDS.has(a.kind));
              return (
                <div key={category.label}>
                  <div className={`px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    {category.label}
                  </div>
                  {otherActions.map(renderAction)}
                  {sensoryActions.length > 0 && (
                    <div className="mb-1">
                      <button
                        className={`flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-left text-xs font-medium transition-colors ${
                          isDark
                            ? 'text-slate-400 hover:bg-slate-700'
                            : 'text-slate-500 hover:bg-slate-50'
                        }`}
                        onContextMenu={(e) => {
                          e.preventDefault();
                          setSensoryMenu({ x: e.clientX, y: e.clientY });
                        }}
                      >
                        <ChevronRight className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                        <span>Sensory detail</span>
                        <span className={`ml-auto text-[10px] ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>right-click</span>
                      </button>
                      {sensoryMenu && (
                        <div
                          className={`fixed z-[60] min-w-[180px] rounded-lg border p-2 shadow-xl ${
                            isDark ? 'border-slate-600 bg-slate-700' : 'border-slate-200 bg-white'
                          }`}
                          style={{ left: sensoryMenu.x, top: sensoryMenu.y }}
                        >
                          {sensoryActions.map(renderAction)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
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
  scrollTarget: number | null;
  isDark: boolean;
  chapterSelectOptions?: Array<{ document_id: string; title: string }>;
  selectedChapterId?: string | null;
  isLoadingChapterSelect?: boolean;
  onChapterSelect?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
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
  scrollTarget,
  isDark,
  chapterSelectOptions,
  selectedChapterId,
  isLoadingChapterSelect,
  onChapterSelect,
}: ManuscriptEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollContainerRef = useRef<HTMLElement>(null);
  const [toolbarPosition, setToolbarPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  // Persist selection across focus changes so toolbar clicks don't lose it
  const [selectionState, setSelectionState] = useState<{ start: number; end: number } | null>(null);

  // Scroll to target line when outline item is clicked
  useEffect(() => {
    if (scrollTarget === null) return;

    if (!isEditing) {
      // Read mode: find element with matching data-line attribute
      const el = scrollContainerRef.current?.querySelector(`[data-line="${scrollTarget}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } else {
      // Edit mode: calculate position from line number
      const lines = (editContent || '').split('\n');
      const targetLine = Math.min(scrollTarget, lines.length - 1);
      const lineHeight = 20; // approximate for text-sm leading-relaxed
      const scrollTop = targetLine * lineHeight - 40; // offset for header
      scrollContainerRef.current?.scrollTo({ top: Math.max(0, scrollTop), behavior: 'smooth' });
    }
  }, [scrollTarget, isEditing, editContent]);

  const handleSelect = useCallback((e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    const start = target.selectionStart ?? 0;
    const end = target.selectionEnd ?? 0;
    setSelectionState({ start, end });
    onSelectionChange?.(start, end, target.value);

    // Calculate toolbar position above the selection
    if (start !== end) {
      const rect = target.getBoundingClientRect();
      const textBefore = target.value.slice(0, start);
      const lines = textBefore.split('\n');
      const lineIndex = lines.length - 1;
      const charInLine = lines[lineIndex].length;
      const lineHeight = 24; // matches leading-relaxed text-sm (~1.5rem)
      const charWidth = 8; // approximate monospace-ish width for text-sm
      const x = rect.left + charInLine * charWidth + 24; // 24px padding
      const y = rect.top + lineIndex * lineHeight - 80; // above selection, account for padding
      setToolbarPosition({ x, y: Math.max(8, y) });
    }
  }, [onSelectionChange]);

  return (
    <>
      <header className={`flex items-center justify-between px-5 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
        <div>
          {chapterSelectOptions && chapterSelectOptions.length > 0 ? (
            <select
              value={selectedChapterId || ''}
              onChange={onChapterSelect}
              disabled={isLoadingChapterSelect}
              className={`text-sm font-semibold rounded-md border px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500 ${isDark ? 'bg-slate-800 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
            >
              {chapterSelectOptions.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {doc.title}
                </option>
              ))}
            </select>
          ) : (
            <>
              <h2 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                {document.title}{(() => { const t = extractChapterTitle(document.content); return t ? ` — ${t}` : ''; })()}
              </h2>
              {document.chapter_id && (
                <p className="text-xs mt-0.5 text-subtle">Chapter: {document.chapter_id}</p>
              )}
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isEditing && (
            <span className="text-xs text-subtle">
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
                <AssistDropdown
                  selectedRange={selectionState ? {
                    start_offset: selectionState.start,
                    end_offset: selectionState.end,
                    selected_text: editContent.slice(selectionState.start, selectionState.end),
                    anchor_before: editContent.slice(Math.max(0, selectionState.start - 120), selectionState.start),
                    anchor_after: editContent.slice(selectionState.end, selectionState.end + 120),
                  } : null}
                  isDark={isDark}
                  onSelect={(kind, instruction) => onAssistRequest(kind, instruction)}
                />
              </>
            )}
          </div>
          <main ref={scrollContainerRef} className={`flex-1 overflow-hidden relative`}>
            <textarea
              ref={textareaRef}
              value={editContent}
              onChange={(e) => onContentChange(e.target.value)}
              onSelect={handleSelect}
              className={`w-full h-full p-6 resize-none outline-none text-sm leading-relaxed ${
                isDark
                  ? 'bg-slate-900 text-slate-300'
                  : 'bg-white text-slate-800'
              }`}
              spellCheck
              placeholder="Start writing or paste your content here..."
            />
            {onAssistRequest && selectionState && selectionState.end > selectionState.start && (
              <SelectionToolbar
                actions={ASSIST_ACTIONS}
                visible
                position={toolbarPosition}
                onClick={(kind, instruction) => onAssistRequest(kind, instruction)}
              />
            )}
          </main>
        </>
      ) : (
        <main ref={scrollContainerRef} className={`flex-1 overflow-y-auto p-6`}>
          <div className="max-w-none">
            {renderMarkdown({ content: document.content, isDark })}
          </div>
        </main>
      )}
    </>
  );
}
