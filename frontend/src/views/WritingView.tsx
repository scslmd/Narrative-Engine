import { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { FileText, BookOpen, Code, Edit3, Save, X, Sparkles } from 'lucide-react';
import { toast } from '../lib/toast';
import { AidsPanel } from '../components/aids/AidsPanel';
import type { ManuscriptDocument, DraftArtifact } from '../types/drafting';
import type { RevisionSuggestion } from '../types/aids';
import {
  getManuscriptDocuments,
  getDraftArtifacts,
  getRevisionSuggestions,
  updateManuscriptContent,
  triggerManuscriptReview,
  createRevisionSuggestion,
} from '../services/drafting';
import { useThemeStore } from '../stores/themeStore';

export function WritingView() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId?: string }>();
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const queryClient = useQueryClient();
  const { mode } = useThemeStore();
  const isDark = mode === 'dark';

  const manuscriptQuery = useQuery({
    queryKey: ['manuscript-documents', projectId],
    queryFn: () => getManuscriptDocuments(projectId!),
    enabled: !!projectId,
  });

  const draftsQuery = useQuery({
    queryKey: ['draft-artifacts', projectId],
    queryFn: () => getDraftArtifacts(projectId!),
    enabled: !!projectId,
  });

  const suggestionsQuery = useQuery({
    queryKey: ['revision-suggestions', projectId, selectedDocumentId ?? 'all'],
    queryFn: () => getRevisionSuggestions(projectId!, selectedDocumentId ?? undefined),
    enabled: !!projectId && !!selectedDocumentId,
  });

  const manuscriptDocuments = useMemo(
    () => (manuscriptQuery.data as ManuscriptDocument[]) ?? [],
    [manuscriptQuery.data],
  );
  const draftArtifacts = (draftsQuery.data as DraftArtifact[]) ?? [];
  const revisionSuggestions = useMemo(
    () => (suggestionsQuery.data as RevisionSuggestion[]) ?? [],
    [suggestionsQuery.data],
  );

  const openSuggestions = useMemo(
    () => revisionSuggestions.filter((s) => s.status === 'REQUESTED' || s.status === 'PENDING'),
    [revisionSuggestions],
  );

  useEffect(() => {
    if (manuscriptDocuments.length === 0) {
      setSelectedDocumentId(null);
      return;
    }

    if (chapterId) {
      const docForChapter = manuscriptDocuments.find(
        (doc: ManuscriptDocument) => doc.chapter_id === chapterId,
      );

      if (docForChapter) {
        if (docForChapter.document_id !== selectedDocumentId) {
          setSelectedDocumentId(docForChapter.document_id);
        }
        return;
      }
    }

    const selectedDocumentStillExists = manuscriptDocuments.some(
      (doc: ManuscriptDocument) => doc.document_id === selectedDocumentId,
    );

    if (!selectedDocumentStillExists) {
      setSelectedDocumentId(manuscriptDocuments[0].document_id);
    }
  }, [manuscriptDocuments, chapterId, selectedDocumentId]);

  const selectedDocument = manuscriptDocuments.find(
    (doc: ManuscriptDocument) => doc.document_id === selectedDocumentId,
  );

  const handleEdit = useCallback(() => {
    if (selectedDocument) {
      setEditContent(selectedDocument.content);
      setIsEditing(true);
    }
  }, [selectedDocument]);

  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setEditContent('');
  }, []);

  const handleSave = useCallback(async () => {
    if (!selectedDocumentId || !projectId) return;
    try {
      await updateManuscriptContent(selectedDocumentId, projectId, editContent);
      await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
      await queryClient.invalidateQueries({ queryKey: ['revision-suggestions', projectId, selectedDocumentId] });
      setIsEditing(false);
      setEditContent('');

      try {
        const findings = await triggerManuscriptReview(selectedDocumentId, projectId);
        if (findings.length > 0) {
          toast.success(`Manuscript saved. ${findings.length} review finding(s) added.`);
        } else {
          toast.success('Manuscript saved. Review complete - no issues found.');
        }
      } catch {
        toast.success('Manuscript saved. Review queued.');
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save manuscript');
    }
  }, [selectedDocumentId, projectId, editContent, queryClient]);

  const handleSuggestionAccept = useCallback(
    async (suggestionId: string) => {
      if (!selectedDocument || !projectId) return;
      const suggestion = revisionSuggestions.find((s) => s.suggestion_id === suggestionId);
      if (!suggestion) return;

      const updatedContent = selectedDocument.content.replace(
        suggestion.source_text,
        suggestion.proposed_text,
      );

      try {
        await updateManuscriptContent(selectedDocument.document_id, projectId, updatedContent);
        await queryClient.invalidateQueries({ queryKey: ['manuscript-documents', projectId] });
        await queryClient.invalidateQueries({ queryKey: ['revision-suggestions', projectId, selectedDocument.document_id] });
        if (isEditing) {
          setEditContent(updatedContent);
        }
        toast.success('Suggestion applied');
      } catch {
        toast.error('Failed to apply suggestion');
      }
    },
    [selectedDocument, projectId, revisionSuggestions, queryClient, isEditing],
  );

  const handleSuggestionReject = useCallback(
    async (suggestionId: string) => {
      if (!selectedDocumentId || !projectId) return;
      const suggestion = revisionSuggestions.find((s) => s.suggestion_id === suggestionId);
      if (!suggestion) return;

      try {
        await createRevisionSuggestion({
          suggestion_id: suggestion.suggestion_id,
          project_id: projectId,
          target_document_id: selectedDocumentId,
          source_text: suggestion.source_text,
          proposed_text: suggestion.proposed_text,
          rationale: suggestion.rationale,
          source_context: suggestion.source_context,
          status: 'REJECTED',
        });
        await queryClient.invalidateQueries({ queryKey: ['revision-suggestions', projectId, selectedDocumentId] });
        toast.success('Suggestion rejected');
      } catch {
        toast.error('Failed to reject suggestion');
      }
    },
    [selectedDocumentId, projectId, revisionSuggestions, queryClient],
  );

  const wordCount = useMemo(() => {
    if (!selectedDocument) return 0;
    const text = isEditing ? editContent : selectedDocument.content;
    return text.trim() ? text.trim().split(/\s+/).length : 0;
  }, [selectedDocument, editContent, isEditing]);

  const charCount = useMemo(() => {
    if (!selectedDocument) return 0;
    const text = isEditing ? editContent : selectedDocument.content;
    return text.length;
  }, [selectedDocument, editContent, isEditing]);


  if (!projectId) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-slate-500">No project selected</p>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4">
      <div className={`w-72 flex-shrink-0 rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col overflow-hidden`}>
        <div className={`flex items-center gap-2 px-4 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <FileText className={`w-4 h-4 ${isDark ? 'text-blue-400' : 'text-blue-500'}`} />
          <h3 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>Manuscripts</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {manuscriptQuery.isLoading && (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className={`h-16 rounded-lg animate-shimmer ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}></div>
              ))}
            </div>
          )}

          {!manuscriptQuery.isLoading && manuscriptDocuments.length === 0 && (
            <div className={`text-center py-6 ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
              <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-xs">No manuscript records yet</p>
              <p className="text-xs mt-1">Create manuscripts via the drafting workflow.</p>
            </div>
          )}

          {!manuscriptQuery.isLoading && manuscriptDocuments.length > 0 && (
            manuscriptDocuments.map((doc) => (
              <button
                key={doc.document_id}
                onClick={() => {
                  setSelectedDocumentId(doc.document_id);
                  setIsEditing(false);
                  setEditContent('');
                }}
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
                {doc.chapter_id && (
                  <div className={`text-xs mt-1 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Chapter: {doc.chapter_id}</div>
                )}
                <div className={`text-xs mt-0.5 ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>v{doc.version}</div>
              </button>
            ))
          )}
        </div>

        <div className={`border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <div className={`px-4 py-2.5 border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            <div className={`flex items-center gap-2 mb-2 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              <Code className="w-3.5 h-3.5" />
              <h3 className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Drafts</h3>
              <span className={`ml-auto text-xs ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>({draftArtifacts.length})</span>
            </div>
          </div>

          <div className="px-3 pb-3 space-y-1.5 max-h-40 overflow-y-auto">
            {draftsQuery.isLoading && (
              <div className="space-y-1.5">
                {[1, 2].map((i) => (
                  <div key={i} className={`h-10 rounded-md animate-shimmer ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}></div>
                ))}
              </div>
            )}

            {!draftsQuery.isLoading && draftArtifacts.length === 0 && (
              <p className={`text-xs ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>No drafts yet</p>
            )}

            {!draftsQuery.isLoading && draftArtifacts.length > 0 && (
              draftArtifacts.map((artifact) => (
                <div key={artifact.artifact_id} className={`p-2 rounded-md ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
                  <div className={`font-medium text-xs ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{artifact.title}</div>
                  <div className={`text-[10px] mt-0.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{artifact.status}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className={`flex-1 rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col overflow-hidden`}>
        {selectedDocument ? (
          <>
            <header className={`flex items-center justify-between px-5 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
              <div>
                <h2 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>{selectedDocument.title}</h2>
                {selectedDocument.chapter_id && (
                  <p className={`text-xs mt-0.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Chapter: {selectedDocument.chapter_id}</p>
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
                    v{selectedDocument.version}
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
                    onClick={handleEdit}
                    className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                      isDark
                        ? 'bg-blue-600 hover:bg-blue-500 text-white'
                        : 'bg-blue-600 hover:bg-blue-500 text-white'
                    }`}
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
                    onClick={handleSave}
                    className="flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
                  >
                    <Save className="w-3.5 h-3.5" />
                    Save
                  </button>
                  <button
                    onClick={handleCancel}
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
                    onChange={(e) => setEditContent(e.target.value)}
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
                    {selectedDocument.content || <span className={isDark ? 'text-slate-600' : 'text-slate-400'}>(No content)</span>}
                  </pre>
                </div>
              </main>
            )}
          </>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <BookOpen className={`w-10 h-10 mx-auto mb-3 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
              <p className={`text-sm ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>Select a manuscript from the sidebar</p>
            </div>
          </div>
        )}
      </div>

      <AidsPanel
        projectId={projectId}
        suggestions={revisionSuggestions}
        onSuggestionAccept={handleSuggestionAccept}
        onSuggestionReject={handleSuggestionReject}
      />
    </div>
  );
}
