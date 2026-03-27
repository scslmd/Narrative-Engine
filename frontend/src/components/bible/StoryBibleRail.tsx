import { useEffect } from 'react';
import { useBibleStore } from '../../stores/bibleStore';
import BibleEntryList from './BibleEntryList';

interface StoryBibleRailProps {
  projectId?: string;
}

export default function StoryBibleRail({ projectId }: StoryBibleRailProps) {
  const { currentProjectId, setCurrentProjectId } = useBibleStore();

  useEffect(() => {
    if (projectId && projectId !== currentProjectId) {
      setCurrentProjectId(projectId);
    }
  }, [projectId, currentProjectId, setCurrentProjectId]);

  if (!projectId) {
    return (
      <div className="h-full flex flex-col bg-gray-100">
        <div className="px-4 py-3 border-b bg-white">
          <h2 className="font-semibold text-gray-900">Story Bible</h2>
        </div>
        
        <div className="p-4 text-center">
          <p className="text-sm text-gray-500">Select a project to view story bible</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-100">
      <div className="px-4 py-3 border-b bg-white">
        <h2 className="font-semibold text-gray-900">Story Bible</h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        <BibleEntryList projectId={projectId} />
      </div>
    </div>
  );
}
