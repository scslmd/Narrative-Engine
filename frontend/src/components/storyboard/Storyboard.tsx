import { useStoryboard } from '../../hooks/useStoryboard';
import SceneCard from './SceneCard';
import ErrorBoundary from '../ErrorBoundary';

interface StoryboardProps {
  projectId?: string;
}

export default function Storyboard({ projectId }: StoryboardProps) {
  const { scenes, loading, navigateToScene } = useStoryboard(projectId);

  if (!projectId) {
    return (
      <div className="p-4 text-center">
        <p className="text-sm text-gray-500">Select a project to view storyboard</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-100">
      <div className="px-4 py-3 border-b bg-white">
        <h2 className="font-semibold text-gray-900">Storyboard</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg p-3 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-100 rounded w-full mb-1"></div>
                <div className="h-3 bg-gray-100 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : scenes.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500 mb-2">No scenes yet</p>
            <button className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors">
              Generate Storyboard
            </button>
          </div>
        ) : (
          scenes.map((scene) => (
            <ErrorBoundary key={scene.id}>
              <SceneCard scene={scene} onClick={navigateToScene} />
            </ErrorBoundary>
          ))
        )}
      </div>
    </div>
  );
}
