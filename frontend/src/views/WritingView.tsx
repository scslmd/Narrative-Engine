import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AidsPanel } from '../components/aids/AidsPanel';
import type { ManuscriptDocument, DraftArtifact } from '../types/drafting';
import type { RevisionSuggestion } from '../types/aids';
import { getManuscriptDocuments, getDraftArtifacts, getRevisionSuggestions } from '../services/drafting';

export function WritingView() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId?: string }>();
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

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
    [manuscriptQuery.data]
  );
  const draftArtifacts = (draftsQuery.data as DraftArtifact[]) ?? [];
  const revisionSuggestions = (suggestionsQuery.data as RevisionSuggestion[]) ?? [];

  useEffect(() => {
    if (manuscriptDocuments.length === 0) {
      setSelectedDocumentId(null);
      return;
    }

    if (chapterId) {
      const docForChapter = manuscriptDocuments.find(
        (doc: ManuscriptDocument) => doc.chapter_id === chapterId
      );

      if (docForChapter) {
        if (docForChapter.document_id !== selectedDocumentId) {
          setSelectedDocumentId(docForChapter.document_id);
        }
        return;
      }
    }

    const selectedDocumentStillExists = manuscriptDocuments.some(
      (doc: ManuscriptDocument) => doc.document_id === selectedDocumentId
    );

    if (!selectedDocumentStillExists) {
      setSelectedDocumentId(manuscriptDocuments[0].document_id);
    }
  }, [manuscriptDocuments, chapterId, selectedDocumentId]);

  const selectedDocument = manuscriptDocuments.find(
    (doc: ManuscriptDocument) => doc.document_id === selectedDocumentId
  );

  if (!projectId) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-gray-500">No project selected</p>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-white overflow-y-auto p-4">
        <h3 className="font-semibold text-gray-900 mb-4">Manuscript Documents</h3>
        
        {manuscriptQuery.isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
            ))}
          </div>
        )}

        {!manuscriptQuery.isLoading && manuscriptDocuments.length === 0 && (
          <p className="text-sm text-gray-500">This project has no manuscript records. Create manuscripts via the drafting workflow.</p>
        )}

        {!manuscriptQuery.isLoading && manuscriptDocuments.length > 0 && (
          <div className="space-y-2">
            {manuscriptDocuments.map((doc) => (
              <button
                key={doc.document_id}
                onClick={() => setSelectedDocumentId(doc.document_id)}
                className={`w-full text-left p-3 rounded border transition-colors ${
                  selectedDocumentId === doc.document_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-sm text-gray-900">{doc.title}</div>
                {doc.chapter_id && (
                  <div className="text-xs text-gray-500 mt-1">Chapter: {doc.chapter_id}</div>
                )}
                <div className="text-xs text-gray-400 mt-1">Version: {doc.version}</div>
              </button>
            ))}
          </div>
        )}

        <h3 className="font-semibold text-gray-900 mb-4 mt-6">Draft Artifacts</h3>
        
        {draftsQuery.isLoading && (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse"></div>
            ))}
          </div>
        )}

        {!draftsQuery.isLoading && draftArtifacts.length === 0 && (
          <p className="text-sm text-gray-500">No draft artifacts for this project. Drafting jobs create these records.</p>
        )}

        {!draftsQuery.isLoading && draftArtifacts.length > 0 && (
          <div className="space-y-2">
            {draftArtifacts.map((artifact) => (
              <div key={artifact.artifact_id} className="p-3 rounded border border-gray-200 bg-gray-50">
                <div className="font-medium text-sm text-gray-900">{artifact.title}</div>
                <div className="text-xs text-gray-500 mt-1">{artifact.status}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 flex flex-col bg-white overflow-hidden">
        {selectedDocument ? (
          <>
            <header className="border-b px-4 py-3">
              <h2 className="text-lg font-semibold text-gray-900">{selectedDocument.title}</h2>
              {selectedDocument.chapter_id && (
                <p className="text-sm text-gray-500">Chapter: {selectedDocument.chapter_id}</p>
              )}
            </header>

            <main className="flex-1 overflow-y-auto p-4">
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800">
                  {selectedDocument.content || '(No content)'}
                </pre>
              </div>
            </main>
          </>
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className="text-sm text-gray-500">Select a document from the left pane to populate this viewer.</p>
          </div>
        )}
      </div>

      <AidsPanel
        projectId={projectId}
        suggestions={revisionSuggestions}
      />
    </div>
  );
}
