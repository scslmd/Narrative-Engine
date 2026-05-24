import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronRight, Edit3, Save, X, Sparkles, Wand2, Type, Minus, Plus } from 'lucide-react';
import type { ManuscriptDocument, RevisionSuggestion } from '../../types/drafting';
import type { ManuscriptAssistKind, TextRange } from '../../types/manuscriptAssist';
import { ASSIST_ACTIONS, ASSIST_CATEGORIES, type AssistAction } from '../../lib/assistActions';
import { SelectionToolbar } from './SelectionToolbar';
import { useSettingsStore, type EditorFontFamily, type EditorFontSize } from '../../stores/settingsStore';

interface MarkdownRenderProps {
  content: string;
  isDark: boolean;
  fontClass: string;
}

/** Render inline markdown formatting: bold, italic, strikethrough, links, inline code. */
function renderInline(text: string, keyPrefix: string, isDark: boolean) {
  const codeBg = isDark ? 'bg-slate-800 text-amber-300' : 'bg-slate-100 text-amber-700';
  const linkColor = isDark ? 'text-violet-400' : 'text-violet-600';

  // Split by all inline patterns at once
  const parts = text.split(/(\*\*\*([^*]+)\*\*\*|\*\*([^*]+)\*\*|___([^_]+)___|__([^_]+)__|\*([^*]+)\*|_([^_]+)_|~~([^~]+)~~|\[([^\]]+)\]\(([^)]+)\)|`([^`]+)`)/g);
  if (parts.length === 1) return <span key={keyPrefix}>{parts[0]}</span>;

  const elements: JSX.Element[] = [];
  let i = 0;
  while (i < parts.length) {
    const part = parts[i];
    if (!part) { i++; continue; }

    // Bold+italic ***text***
    if (part.startsWith('***') && part.endsWith('***')) {
      elements.push(<strong key={keyPrefix + '-' + i} className="font-bold italic">{part.slice(3, -3)}</strong>);
      i++; continue;
    }
    // Bold **text**
    if (part.startsWith('**') && part.endsWith('**')) {
      elements.push(<strong key={keyPrefix + '-' + i} className="font-bold">{part.slice(2, -2)}</strong>);
      i++; continue;
    }
    // Bold __text__
    if (part.startsWith('__') && part.endsWith('__')) {
      elements.push(<strong key={keyPrefix + '-' + i} className="font-bold">{part.slice(2, -2)}</strong>);
      i++; continue;
    }
    // Italic ___text___ or *text* or _text_
    if (part.startsWith('___') && part.endsWith('___')) {
      elements.push(<em key={keyPrefix + '-' + i} className="italic">{part.slice(3, -3)}</em>);
      i++; continue;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      elements.push(<em key={keyPrefix + '-' + i} className="italic">{part.slice(1, -1)}</em>);
      i++; continue;
    }
    if (part.startsWith('_') && part.endsWith('_')) {
      elements.push(<em key={keyPrefix + '-' + i} className="italic">{part.slice(1, -1)}</em>);
      i++; continue;
    }
    // Strikethrough ~~text~~
    if (part.startsWith('~~') && part.endsWith('~~')) {
      elements.push(<del key={keyPrefix + '-' + i} className="line-through opacity-70">{part.slice(2, -2)}</del>);
      i++; continue;
    }
    // Link [text](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      elements.push(
        <a key={keyPrefix + '-' + i} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className={`${linkColor} underline hover:opacity-80`}>
          {linkMatch[1]}
        </a>,
      );
      i++; continue;
    }
    // Inline code `text`
    if (part.startsWith('`') && part.endsWith('`')) {
      elements.push(<code key={keyPrefix + '-' + i} className={`px-1.5 py-0.5 rounded text-xs font-mono ${codeBg}`}>{part.slice(1, -1)}</code>);
      i++; continue;
    }
    elements.push(<span key={keyPrefix + '-' + i}>{part}</span>);
    i++;
  }
  return <>{elements}</>;
}

/** Lightweight markdown renderer for manuscript read mode. Handles headings, bold, italic, strikethrough, lists, blockquotes, links, inline code, code blocks, and horizontal rules. */
function renderMarkdown({ content, isDark, fontClass }: MarkdownRenderProps) {
  if (!content) return <span className="text-muted">(No content)</span>;

  const headingBase = isDark ? 'text-slate-100 font-semibold' : 'text-slate-900 font-semibold';
  const textColor = isDark ? 'text-slate-300' : 'text-slate-700';
  const quoteColor = isDark ? 'border-slate-600 text-slate-400' : 'border-slate-300 text-slate-500';

  const lines = content.split('\n');
  const elements: JSX.Element[] = [];
  let lineIdx = 0;
  let elementIdx = 0;

  while (lineIdx < lines.length) {
    const line = lines[lineIdx];

    // Skip empty lines
    if (!line.trim()) {
      lineIdx++;
      continue;
    }

    // Horizontal rule
    if (/^(\*{3,}|-{3,}|_{3,})\s*$/.test(line.trim())) {
      elements.push(
        <hr key={`hr-${elementIdx}`} className={`my-4 border-0 ${isDark ? 'border-slate-700' : 'border-slate-200'}`} data-line={lineIdx} />,
      );
      elementIdx++;
      lineIdx++;
      continue;
    }

    // Heading: # ## ###
    const headingMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length as 1 | 2 | 3;
      const text = headingMatch[2];
      const sizes: Record<number, string> = {
        1: 'text-xl mt-6 mb-3',
        2: 'text-lg mt-5 mb-2',
        3: 'text-base mt-4 mb-2',
      };
      elements.push(
        <div key={`h-${elementIdx}`} data-line={lineIdx}>
          <p className={`${headingBase} ${sizes[level]}`}>
            {renderInline(text, `h${elementIdx}`, isDark)}
          </p>
        </div>,
      );
      elementIdx++;
      lineIdx++;
      continue;
    }

    // Blockquote: > text
    if (line.startsWith('>')) {
      const quoteLines: string[] = [];
      while (lineIdx < lines.length && lines[lineIdx].startsWith('>')) {
        quoteLines.push(lines[lineIdx].replace(/^>\s?/, ''));
        lineIdx++;
      }
      elements.push(
        <blockquote key={`bq-${elementIdx}`} data-line={lineIdx} className={`border-l-4 ${quoteColor} pl-4 my-3 italic`}>
          {quoteLines.map((qLine, i) => (
            <span key={i}>
              {renderInline(qLine, `bq${elementIdx}-${i}`, isDark)}
              <br />
            </span>
          ))}
        </blockquote>,
      );
      elementIdx++;
      continue;
    }

    // Unordered list: - item or * item
    if (/^(\s*[-*])\s+/.test(line)) {
      const listItems: string[] = [];
      while (lineIdx < lines.length && /^(\s*[-*])\s+/.test(lines[lineIdx])) {
        listItems.push(lines[lineIdx].replace(/^\s*[-*]\s+/, ''));
        lineIdx++;
      }
      elements.push(
        <ul key={`ul-${elementIdx}`} data-line={lineIdx} className={`list-disc pl-6 my-3 space-y-1 ${textColor}`}>
          {listItems.map((item, i) => (
            <li key={i}>{renderInline(item, `li${elementIdx}-${i}`, isDark)}</li>
          ))}
        </ul>,
      );
      elementIdx++;
      continue;
    }

    // Ordered list: 1. item
    if (/^\s*\d+\.\s+/.test(line)) {
      const listItems: string[] = [];
      while (lineIdx < lines.length && /^\s*\d+\.\s+/.test(lines[lineIdx])) {
        listItems.push(lines[lineIdx].replace(/^\s*\d+\.\s+/, ''));
        lineIdx++;
      }
      elements.push(
        <ol key={`ol-${elementIdx}`} data-line={lineIdx} className={`list-decimal pl-6 my-3 space-y-1 ${textColor}`}>
          {listItems.map((item, i) => (
            <li key={i}>{renderInline(item, `oli${elementIdx}-${i}`, isDark)}</li>
          ))}
        </ol>,
      );
      elementIdx++;
      continue;
    }

    // Code block: ```...```
    if (line.startsWith('```')) {
      const codeLines: string[] = [];
      lineIdx++;
      while (lineIdx < lines.length && !lines[lineIdx].startsWith('```')) {
        codeLines.push(lines[lineIdx]);
        lineIdx++;
      }
      const codeBg = isDark ? 'bg-slate-800' : 'bg-slate-100';
      const codeText = isDark ? 'text-slate-300' : 'text-slate-700';
      elements.push(
        <pre key={`code-${elementIdx}`} data-line={lineIdx} className={`${codeBg} ${codeText} rounded-lg p-4 my-3 overflow-x-auto font-mono text-xs leading-relaxed`}>
          <code>{codeLines.join('\n')}</code>
        </pre>,
      );
      elementIdx++;
      lineIdx++;
      continue;
    }

    // Regular paragraph - collect consecutive non-empty, non-special lines
    const paraLines: string[] = [];
    while (lineIdx < lines.length && lines[lineIdx].trim() &&
      !lines[lineIdx].match(/^(#{1,3}|>\s|(\s*[-*])\s|(\s*\d+\.)\s|```)/)) {
      paraLines.push(lines[lineIdx]);
      lineIdx++;
    }

    if (paraLines.length > 0) {
      elements.push(
        <p key={`p-${elementIdx}`} data-line={lineIdx} className={`${fontClass} leading-relaxed mb-3 ${textColor}`}>
          {paraLines.map((pLine, i) => (
            <span key={i}>
              {renderInline(pLine, `p${elementIdx}-${i}`, isDark)}
              {i < paraLines.length - 1 && <br />}
            </span>
          ))}
        </p>,
      );
      elementIdx++;
    }
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
  const [selectionState, setSelectionState] = useState<{ start: number; end: number } | null>(null);
  const { editorFontFamily, editorFontSize, setEditorFontFamily, setEditorFontSize } = useSettingsStore();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey;

      if (ctrl && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (isEditing) {
          onSave();
        }
      }

      if (ctrl && e.key.toLowerCase() === 'e') {
        e.preventDefault();
        if (!isEditing) {
          onEdit();
        }
      }

      if (e.key === 'Escape' && isEditing) {
        onCancel();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isEditing, onSave, onEdit, onCancel]);

  const editorFontClass = useMemo(() => {
    const familyClass = editorFontFamily === 'serif' ? 'font-serif' : editorFontFamily === 'mono' ? 'font-mono' : 'font-sans';
    const sizeClass = editorFontSize === 'small' ? 'text-xs' : editorFontSize === 'large' ? 'text-base' : 'text-sm';
    return `${familyClass} ${sizeClass}`;
  }, [editorFontFamily, editorFontSize]);

  const cycleFontSize = useCallback(() => {
    const sizes: EditorFontSize[] = ['small', 'medium', 'large'];
    const current = useSettingsStore.getState().editorFontSize;
    const next = sizes[(sizes.indexOf(current) + 1) % sizes.length];
    setEditorFontSize(next);
  }, [setEditorFontSize]);

  // Scroll to target line when outline item is clicked
  useEffect(() => {
    if (scrollTarget === null) return;

    if (!isEditing) {
      const el = scrollContainerRef.current?.querySelector(`[data-line="${scrollTarget}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } else {
      const lines = (editContent || '').split('\n');
      const targetLine = Math.min(scrollTarget, lines.length - 1);
      const lineHeight = 20;
      const scrollTop = targetLine * lineHeight - 40;
      scrollContainerRef.current?.scrollTo({ top: Math.max(0, scrollTop), behavior: 'smooth' });
    }
  }, [scrollTarget, isEditing, editContent]);

  const handleSelect = useCallback((e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    const start = target.selectionStart ?? 0;
    const end = target.selectionEnd ?? 0;
    setSelectionState({ start, end });
    onSelectionChange?.(start, end, target.value);

    if (start !== end) {
      const rect = target.getBoundingClientRect();
      const textBefore = target.value.slice(0, start);
      const lines = textBefore.split('\n');
      const lineIndex = lines.length - 1;
      const charInLine = lines[lineIndex].length;
      const lineHeight = 24;
      const charWidth = 8;
      const x = rect.left + charInLine * charWidth + 24;
      const y = rect.top + lineIndex * lineHeight - 80;
      setToolbarPosition({ x, y: Math.max(8, y) });
    }
  }, [onSelectionChange]);

  return (
    <>
      <header className={`flex items-center justify-between px-5 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
        <div className="flex items-center gap-3">
          <h2 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Editor</h2>
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
                {document.title}{document.display_title ? ` — ${document.display_title}` : ''}
              </h2>
              {document.chapter_id && (
                <p className="text-xs mt-0.5 text-subtle">Chapter: {document.chapter_id}</p>
              )}
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Type className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
            <select
              value={editorFontFamily}
              onChange={(e) => setEditorFontFamily(e.target.value as EditorFontFamily)}
              className={`text-xs rounded-md border px-1.5 py-1 outline-none focus:ring-1 focus:ring-blue-500 ${isDark ? 'bg-slate-800 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
            >
              <option value="default">Sans</option>
              <option value="serif">Serif</option>
              <option value="mono">Mono</option>
            </select>
            <button
              onClick={cycleFontSize}
              className={`p-1 rounded-md transition-colors ${isDark ? 'hover:bg-slate-700 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              title={`Font size: ${editorFontSize}`}
            >
              {editorFontSize === 'large' ? <Minus className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            </button>
          </div>
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
              title="Edit (Ctrl+E)"
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
              title="Save (Ctrl+S)"
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
              className={`w-full h-full p-6 resize-none outline-none leading-relaxed ${editorFontClass} ${
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
          <div className={`max-w-none ${editorFontClass}`}>
            {renderMarkdown({ content: document.content, isDark, fontClass: editorFontClass })}
          </div>
        </main>
      )}
    </>
  );
}
