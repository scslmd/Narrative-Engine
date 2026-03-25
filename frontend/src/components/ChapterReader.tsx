import { useState } from 'react';
import { useProjectChapters, useChapterContent } from '../hooks/useProjects';
import { SkeletonCard } from './skeleton';

interface Props {
  projectId: string;
}

export function ChapterReader({ projectId }: Props): React.ReactElement {
  const { data: chapters, isLoading: loadingChapters } = useProjectChapters(projectId);
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  const { data: content, isLoading: loadingContent } = useChapterContent(selectedChapterId || '');

  if (loadingChapters) {
    return <SkeletonCard />;
  }

  if (!chapters || chapters.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
        <p className="text-gray-500">No chapters available. Run the Drafter phase first.</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 h-full flex flex-col">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Chapters</h2>

      <div className="flex flex-1 gap-4 overflow-hidden">
        <div className="w-48 flex-shrink-0 overflow-y-auto space-y-2 pr-2">
          {chapters.map((chapter) => (
            <button
              key={chapter.chapter_id}
              onClick={() => setSelectedChapterId(chapter.chapter_id)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                selectedChapterId === chapter.chapter_id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white'
              }`}
            >
              <p className="font-medium text-sm">{chapter.title || `Chapter ${chapter.chapter_number}`}</p>
              <p className={`text-xs mt-1 ${selectedChapterId === chapter.chapter_id ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}`}>
                {chapter.beat_count} beats
              </p>
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto">
          {selectedChapterId && content ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {chapters.find((c) => c.chapter_id === selectedChapterId)?.title || 'Chapter'}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Updated: {new Date(content.updated_at).toLocaleString()}
                </p>
              </div>

              <div className="prose prose-sm dark:prose-invert max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-gray-800 dark:text-gray-200">
                  {content.content}
                </pre>
              </div>
            </div>
          ) : loadingContent ? (
            <SkeletonCard />
          ) : (
            <p className="text-gray-500 text-center py-8">Select a chapter to view</p>
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700 mt-4 text-xs text-gray-500">
        {chapters.length} chapters total
      </div>
    </div>
  );
}
