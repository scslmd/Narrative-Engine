import { useState, useEffect, useRef } from 'react';
import { submitImport, getImportStatus } from '../../services/storyImport';
import { submitMythosExtraction, getExtractionStatus as getMythosExtractionStatus } from '../../services/mythosExtraction';
import { submitPatternExtraction, getExtractionStatus as getPatternExtractionStatus } from '../../services/patternExtraction';
import type { PatternExtractionRequest } from '../../types/patternExtraction';
import { X, Upload, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '../../hooks/useToast';
import { useHealthCheck } from '../../hooks/useHealthCheck';

interface StoryImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ImportMode = 'story' | 'mythos' | 'patterns';

export function StoryImportModal({ isOpen, onClose }: StoryImportModalProps): React.ReactElement {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const { checkBeforeImport } = useHealthCheck();
  const [projectName, setProjectName] = useState('');
  const [storyText, setStoryText] = useState('');
  const [genre, setGenre] = useState('');
  const [tone, setTone] = useState('');
  const [importMode, setImportMode] = useState<ImportMode>('story');
  const [sourceCorpus, setSourceCorpus] = useState('');
  const [generationMode, setGenerationMode] = useState<'same_world' | 'transposed' | 'pure_pattern'>('same_world');
  const [patternSourceType, setPatternSourceType] = useState<'narrative' | 'mythology'>('narrative');
  const [patternGenMode, setPatternGenMode] = useState<'same_world' | 'new_characters' | 'transposed' | 'pure_pattern'>('same_world');
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [importId, setImportId] = useState<string | null>(null);
  const [importPhase, setImportPhase] = useState('');
  const [extractionId, setExtractionId] = useState<string | null>(null);
  const [extractionPhase, setExtractionPhase] = useState('');
  const [chaptersProcessed, setChaptersProcessed] = useState(0);
  const [totalChapters, setTotalChapters] = useState(0);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const MIN_STORY_LENGTH = 50;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setWarnings([]);
    await checkBeforeImport();

    if (storyText.length < MIN_STORY_LENGTH) {
      setError(`Story text must be at least ${MIN_STORY_LENGTH} characters.`);
      return;
    }

    if (importMode === 'story' && !projectName.trim()) {
      setError('Project name is required.');
      return;
    }

    setIsImporting(true);

    try {
      if (importMode === 'patterns') {
        const patternRequest: PatternExtractionRequest = {
          text: storyText,
          source_type: patternSourceType,
          generation_mode: patternGenMode,
          source_corpus: sourceCorpus.trim() || null,
        };
        const submit = await submitPatternExtraction(patternRequest);
        setExtractionId(submit.extraction_id);
        setExtractionPhase('Extracting patterns...');

        pollRef.current = setInterval(async () => {
          try {
            const progress = await getPatternExtractionStatus(submit.extraction_id);
            setExtractionPhase(progress.phase || 'Processing...');

            if (progress.status === 'completed') {
              if (pollRef.current) clearInterval(pollRef.current);
              setIsImporting(false);
              setExtractionId(null);
              addToast('Patterns extracted successfully', 'success');
              navigate('/workspace/plan');
              queryClient.invalidateQueries({ queryKey: ['projects'] });
              onClose();
            } else if (progress.status === 'failed') {
              if (pollRef.current) clearInterval(pollRef.current);
              setIsImporting(false);
              setExtractionId(null);
              const errorMsg = progress.error || 'Pattern extraction failed';
              setError(errorMsg);
              addToast(errorMsg, 'error');
            }
          } catch {
            // Keep polling on transient errors
          }
        }, 2000);

        return;
      } else if (importMode === 'mythos') {
        const mythosSubmit = await submitMythosExtraction({
          text: storyText,
          source_corpus: sourceCorpus.trim() || null,
          generation_mode: generationMode,
        });
        setExtractionId(mythosSubmit.extraction_id);
        setExtractionPhase('Extracting mythos...');

        pollRef.current = setInterval(async () => {
          try {
            const progress = await getMythosExtractionStatus(mythosSubmit.extraction_id);
            setExtractionPhase(progress.phase || 'Processing...');

            if (progress.status === 'completed' && progress.result) {
              if (pollRef.current) clearInterval(pollRef.current);
              setIsImporting(false);
              setExtractionId(null);
              addToast('Mythos extracted successfully', 'success');
              navigate(`/workspace/${progress.result.project_id}`);
              queryClient.invalidateQueries({ queryKey: ['projects'] });
              onClose();
            } else if (progress.status === 'failed') {
              if (pollRef.current) clearInterval(pollRef.current);
              setIsImporting(false);
              setExtractionId(null);
              const errorMsg = progress.error || 'Mythos extraction failed';
              setError(errorMsg);
              addToast(errorMsg, 'error');
            }
          } catch {
            // Keep polling on transient errors
          }
        }, 2000);

        return;
      } else {
        const formData = new FormData();
        formData.append('story_text', storyText);
        formData.append('project_name', projectName.trim());
        if (genre.trim()) formData.append('genre', genre.trim());
        if (tone.trim()) formData.append('tone', tone.trim());

        const submit = await submitImport(formData);
        setImportId(submit.import_id);
        setImportPhase('Starting import...');

        pollRef.current = setInterval(async () => {
          try {
            const progress = await getImportStatus(submit.import_id);
            setImportPhase(progress.phase || 'Processing...');
            setChaptersProcessed(progress.chapters_processed);
            setTotalChapters(progress.total_estimated_chapters);

            if (progress.status === 'completed' && progress.result) {
              if (pollRef.current) clearInterval(pollRef.current);
              setIsImporting(false);
              setImportId(null);

              addToast(`Import completed${progress.result.chapters_processed ? ` (${progress.result.chapters_processed} chapters)` : ''}`, 'success');

              if (progress.result.warnings?.length > 0) {
                setWarnings(progress.result.warnings);
              }
              navigate(`/workspace/${progress.result.project_id}`);
              queryClient.invalidateQueries({ queryKey: ['projects'] });
              onClose();
            } else if (progress.status === 'failed') {
              if (pollRef.current) clearInterval(pollRef.current);
              setIsImporting(false);
              setImportId(null);
              addToast(progress.error || 'Import failed', 'error');
              setError(progress.error || 'Import failed');
            }
          } catch {
            // Keep polling on transient errors
          }
        }, 2000);

        return;
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Import failed unexpectedly.';
      setError(message);
    } finally {
      setIsImporting(false);
    }
  };

  if (!isOpen) return <></>;

  const charCount = storyText.length;
  const wordCount = storyText.trim() ? storyText.trim().split(/\s+/).length : 0;
  const estimatedTime = charCount > 30000
    ? `${Math.ceil(charCount / 10000 * 2)}-${Math.ceil(charCount / 10000 * 4)} min`
    : charCount > 5000
      ? '1-3 min'
      : '< 1 min';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl border bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-card">
        <div className="sticky top-0 flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Import Existing Story</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="flex gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
            <button type="button" onClick={() => setImportMode('story')}
              className={`flex-1 px-2 py-2 text-xs font-medium rounded-md transition-colors ${
                importMode === 'story'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}>
              Import Story
            </button>
            <button type="button" onClick={() => setImportMode('mythos')}
              className={`flex-1 px-2 py-2 text-xs font-medium rounded-md transition-colors ${
                importMode === 'mythos'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}>
              Extract Mythos
            </button>
            <button type="button" onClick={() => setImportMode('patterns')}
              className={`flex-1 px-2 py-2 text-xs font-medium rounded-md transition-colors ${
                importMode === 'patterns'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}>
              Extract Patterns
            </button>
          </div>

          <p className="text-sm text-slate-500">
            {importMode === 'story'
              ? 'Paste a completed story and the system will analyze it, extract structured data, and create a project with foundation, characters, world bible, arcs, imported planning artifacts, and chapter packets. Drafts are created later in the drafting workflow.'
              : importMode === 'mythos'
                ? 'Paste mythology texts and the system will extract archetypal patterns, narrative structures, cosmic rules, and symbolic motifs for pattern-based story generation.'
                : 'Paste a story or mythological text to extract reusable narrative patterns, then generate a new project using those patterns.'}
          </p>

          {importMode === 'story' && (
            <>
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <span className="w-3.5 h-3.5">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                  </span>
                  Project Name
                </label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  required={importMode === 'story'}
                  placeholder="Enter project title..."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    <span className="w-3.5 h-3.5">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
                    </span>
                    Genre
                  </label>
                  <input
                    type="text"
                    value={genre}
                    onChange={(e) => setGenre(e.target.value)}
                    placeholder="e.g., Fantasy"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    <span className="w-3.5 h-3.5">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/></svg>
                    </span>
                    Tone
                  </label>
                  <input
                    type="text"
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    placeholder="e.g., Dark and Gritty"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                  />
                </div>
              </div>
            </>
          )}

          {importMode === 'mythos' && (
            <>
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <span className="w-3.5 h-3.5">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                  </span>
                  Source Corpus <span className="font-normal normal-case tracking-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={sourceCorpus}
                  onChange={(e) => setSourceCorpus(e.target.value)}
                  placeholder="e.g., Greek Mythology, Lovecraftian Canon"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <span className="w-3.5 h-3.5">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/></svg>
                  </span>
                  Generation Mode
                </label>
                <div className="flex gap-2">
                  {([
                    { value: 'same_world' as const, label: 'Same World' },
                    { value: 'transposed' as const, label: 'Transposed' },
                    { value: 'pure_pattern' as const, label: 'Pure Pattern' },
                  ]).map((mode) => (
                    <button
                      key={mode.value}
                      type="button"
                      onClick={() => setGenerationMode(mode.value)}
                      className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
                        generationMode === mode.value
                          ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300'
                          : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-600'
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {importMode === 'patterns' && (
            <>
              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <span className="w-3.5 h-3.5">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                  </span>
                  Source Type
                </label>
                <div className="flex gap-2">
                  {([
                    { value: 'narrative' as const, label: 'Narrative' },
                    { value: 'mythology' as const, label: 'Mythology' },
                  ]).map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setPatternSourceType(opt.value)}
                      className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
                        patternSourceType === opt.value
                          ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300'
                          : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-600'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <span className="w-3.5 h-3.5">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/></svg>
                  </span>
                  Generation Mode
                </label>
               <div className="flex gap-2">
                    {(patternSourceType === 'mythology'
                      ? [
                          { value: 'same_world' as const, label: 'Same World' },
                          { value: 'transposed' as const, label: 'Transposed' },
                          { value: 'pure_pattern' as const, label: 'Pure Pattern' },
                        ]
                      : [
                          { value: 'same_world' as const, label: 'Same World' },
                          { value: 'new_characters' as const, label: 'New Characters' },
                          { value: 'transposed' as const, label: 'Transposed' },
                        ]
                    ).map((mode) => (
                      <button
                        key={mode.value}
                        type="button"
                        onClick={() => setPatternGenMode(mode.value)}
                        className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
                          patternGenMode === mode.value
                            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300'
                            : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-600'
                        }`}
                      >
                        {mode.label}
                      </button>
                    ))}
                  </div>
              </div>

              <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <span className="w-3.5 h-3.5">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                  </span>
                  Source Corpus <span className="font-normal normal-case tracking-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={sourceCorpus}
                  onChange={(e) => setSourceCorpus(e.target.value)}
                  placeholder="e.g., Greek Mythology, Lovecraftian Canon"
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                />
              </div>
            </>
          )}

          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <Upload className="w-3.5 h-3.5" />
              {importMode === 'story' ? 'Story Text' : importMode === 'mythos' ? 'Mythology Text' : 'Source Text'}
              <span className={`text-xs font-normal ${storyText.length < MIN_STORY_LENGTH ? 'text-amber-500' : 'text-emerald-500'}`}>
                ({storyText.length} / {MIN_STORY_LENGTH} min)
              </span>
            </label>
            <textarea
              value={storyText}
              onChange={(e) => setStoryText(e.target.value)}
              required
              rows={12}
              placeholder={
                importMode === 'story'
                  ? 'Paste your completed story here. The system will analyze and extract structured data including characters, world elements, arcs, and more.'
                  : importMode === 'mythos'
                    ? 'Paste mythology or mythological texts here. The system will extract archetypal patterns, narrative structures, cosmic rules, and symbolic motifs.'
                    : 'Paste a story or mythological text here. The system will extract reusable narrative patterns for generating new stories.'
              }
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm px-3 py-2.5 text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 resize-none font-mono"
            />

          {importMode === 'story' && storyText && (
            <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
              <span>{charCount.toLocaleString()} characters</span>
              <span>{wordCount.toLocaleString()} words</span>
              <span>~{estimatedTime} to process</span>
              {charCount > 100000 && (
                <span className="text-amber-600">Large file — may take longer</span>
              )}
            </div>
          )}
          </div>

          {importMode === 'story' && (
            <>
              <div
                className="mt-4 flex items-center justify-center px-6 py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 cursor-pointer transition-colors"
                onClick={() => document.getElementById('file-upload')?.click()}
              >
                <div className="text-center">
                  <Upload className="w-6 h-6 mx-auto text-gray-400" />
                  <p className="mt-2 text-sm text-gray-500">
                    {uploadedFileName || 'Drop a .txt or .md file, or click to browse'}
                  </p>
                </div>
              </div>
              <input
                id="file-upload"
                type="file"
                accept=".txt,.md"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setUploadedFileName(file.name);
                    const reader = new FileReader();
                    reader.onload = (ev) => {
                      setStoryText(ev.target?.result as string);
                    };
                    reader.readAsText(file);
                  }
                }}
              />
            </>
          )}

          {error && (
            <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800">
              <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}

          {error && !isImporting && (
            <button
              type="button"
              onClick={() => {
                setError(null);
                handleSubmit(new Event('submit') as unknown as React.FormEvent);
              }}
              className="mt-2 px-4 py-1.5 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
            >
              Retry Import
            </button>
          )}

          {warnings.length > 0 && (
            <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
              <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
              <div className="text-sm text-amber-700 dark:text-amber-400">
                <p className="font-medium mb-1">Warnings during import:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            </div>
          )}

          {isImporting && (
            <div className="flex flex-col items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
              <p className="mt-4 text-sm text-gray-600">
                {extractionPhase || importPhase || 'Analyzing...'}
              </p>
              {totalChapters > 0 && (
                <div className="mt-2 w-full max-w-xs">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Chapter {chaptersProcessed} of {totalChapters}</span>
                    <span>{Math.round((chaptersProcessed / totalChapters) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${(chaptersProcessed / totalChapters) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              {importId && (
                <button
                  type="button"
                  onClick={() => {
                    if (pollRef.current) clearInterval(pollRef.current);
                    setIsImporting(false);
                    setImportId(null);
                  }}
                  className="mt-4 text-sm text-gray-500 hover:text-gray-700"
                >
                  Cancel (import will continue in background)
                </button>
              )}
              {extractionId && (
                <button
                  type="button"
                  onClick={() => {
                    if (pollRef.current) clearInterval(pollRef.current);
                    setIsImporting(false);
                    setExtractionId(null);
                  }}
                  className="mt-4 text-sm text-gray-500 hover:text-gray-700"
                >
                  Cancel (extraction will continue in background)
                </button>
              )}
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isImporting}
              className="px-5 py-2.5 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-60"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isImporting}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-violet-600 text-white text-sm font-medium rounded-lg hover:from-indigo-600 hover:to-violet-700 shadow-sm hover:shadow-md transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Upload className="w-4 h-4" />
              {isImporting ? 'Processing...' : importMode === 'mythos' ? 'Extract Mythos' : importMode === 'patterns' ? 'Extract Patterns & Create Project' : 'Import Story'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
