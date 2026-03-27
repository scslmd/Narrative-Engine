import { useEffect } from 'react';
import { useWorkspaceStore } from '../../stores/workspaceStore';

interface WorkspaceNotesProps {
  projectId: string;
}

export default function WorkspaceNotes({ projectId }: WorkspaceNotesProps) {
  const { currentProjectId, notes, lastUpdated, setCurrentProjectId, updateNotes } = useWorkspaceStore();

  useEffect(() => {
    if (projectId && projectId !== currentProjectId) {
      setCurrentProjectId(projectId);
    }
  }, [projectId, currentProjectId, setCurrentProjectId]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateNotes(e.target.value);
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="border-b px-4 py-2 bg-yellow-50 flex items-center justify-between">
        <span className="text-sm font-medium text-yellow-800">
          Personal notes (not saved to project)
        </span>
        
        {lastUpdated && (
          <span className="text-xs text-yellow-700">
            Saved {new Date(lastUpdated).toLocaleTimeString()}
          </span>
        )}
      </div>

      <textarea
        value={notes}
        onChange={handleChange}
        placeholder="Add your personal notes here... These are stored locally and won't be saved to the project."
        className="w-full p-4 h-64 resize-none focus:outline-none text-gray-700"
      />
    </div>
  );
}
