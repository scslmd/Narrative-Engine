import { useState, useEffect, useCallback, useRef } from 'react';

interface BrainDumpCanvasProps {
  sessionId: string | null;
  onSave?: (rawText: string) => void;
  onOrganize?: () => void;
  initialTitle?: string | null;
  initialState?: 'active' | 'organized' | 'archived';
}

const ORGANIZE_TEXT_THRESHOLD = 100;

export function BrainDumpCanvas({
  sessionId,
  onSave,
  onOrganize,
  initialTitle,
  initialState = 'active',
}: BrainDumpCanvasProps) {
  const [title, setTitle] = useState(initialTitle ?? '');
  const [text, setText] = useState('');
  const [savedText, setSavedText] = useState('');
  const [showControls, setShowControls] = useState(false);
  const [titleSet, setTitleSet] = useState(initialTitle !== undefined && initialTitle !== null);
  const [wordCount, setWordCount] = useState(0);
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (savedText) {
      setText(savedText);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    setWordCount(text.trim() ? text.trim().split(/\s+/).length : 0);
  }, [text]);

  const debouncedSave = useCallback(
    (newText: string) => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      autoSaveTimerRef.current = setTimeout(() => {
        onSave?.(newText);
        setSavedText(newText);
      }, 2000);
    },
    [onSave],
  );

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setText(newText);
    debouncedSave(newText);
  };

  const handleTitleSubmit = () => {
    if (title.trim()) {
      setTitleSet(true);
    }
  };

  const handleTitleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleTitleSubmit();
    }
  };

  const showOrganize =
    onOrganize && text.length > ORGANIZE_TEXT_THRESHOLD && initialState === 'active';

  const handleOrganize = () => {
    if (onOrganize) {
      onOrganize();
    }
  };

  return (
    <div
      className="flex flex-col h-full relative select-text"
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(false)}
    >
      {/* Top bar - title setup or title display */}
      {!titleSet ? (
        <div className="absolute top-6 left-0 right-0 z-10 flex justify-center pointer-events-none">
          <div className="pointer-events-auto bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl px-8 py-6 shadow-lg max-w-xl w-full">
            <h2 className="text-center text-lg font-medium text-[var(--text-primary)] mb-4">
              Name your brain dump
            </h2>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={handleTitleKeyDown}
              placeholder="e.g., Character ideas, Plot concepts..."
              autoFocus
              className="w-full px-4 py-3 text-center text-lg bg-transparent border-b border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary-accent)] placeholder:text-[var(--text-secondary)]"
            />
            <p className="text-center text-sm text-[var(--text-secondary)] mt-3">
              Or press Enter to start blank
            </p>
          </div>
        </div>
      ) : null}

      {/* Main textarea */}
      <div className="flex-1 overflow-hidden">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          placeholder={titleSet ? 'Start typing your ideas...' : 'Name your dump above, then start typing...'}
          className={`w-full h-full p-6 resize-none bg-transparent border-none outline-none text-[var(--text-primary)] leading-relaxed ${
            titleSet ? '' : 'opacity-30 pointer-events-none'
          }`}
          style={{
            fontSize: '1.125rem',
            minHeight: '100%',
          }}
          autoFocus={titleSet}
          spellCheck={false}
        />
      </div>

      {/* Controls overlay */}
      {(showControls || text.length > 0) && (
        <div
          className={`absolute bottom-0 left-0 right-0 flex items-center justify-between px-4 py-2 transition-opacity duration-200 ${
            showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-secondary)]">
              {wordCount} {wordCount === 1 ? 'word' : 'words'}
            </span>
            {savedText && text !== savedText && (
              <span className="text-xs text-[var(--text-warning)]">editing...</span>
            )}
            {!savedText && !text && (
              <span className="text-xs text-[var(--text-secondary)]">blank session</span>
            )}
          </div>

          {showOrganize && (
            <button
              onClick={handleOrganize}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--primary-accent)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity shadow-md"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
                <path d="M5 3v4" />
                <path d="M19 17v4" />
                <path d="M3 5h4" />
                <path d="M17 19h4" />
              </svg>
              Organize with AI
            </button>
          )}
        </div>
      )}
    </div>
  );
}
