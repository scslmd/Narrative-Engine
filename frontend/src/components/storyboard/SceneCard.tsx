import type { Scene } from '../../types/scene';

interface SceneCardProps {
  scene: Scene;
  onClick: (scene: Scene) => void;
}

export default function SceneCard({ scene, onClick }: SceneCardProps) {
  return (
    <button
      onClick={() => onClick(scene)}
      className="w-full text-left bg-white hover:bg-gray-50 border rounded-lg p-3 transition-colors shadow-sm"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="font-medium text-gray-900 text-sm flex-1">{scene.title}</h4>
        
        {scene.hasConflict && (
          <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Conflict
          </span>
        )}
      </div>

      <p className="text-xs text-gray-600 mb-2 line-clamp-2">{scene.purpose}</p>

      {scene.activeCharacters.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {scene.activeCharacters.map((character) => (
            <span key={character} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-blue-50 text-blue-700">
              {character}
            </span>
          ))}
        </div>
      )}

      {scene.manuscriptLocation && (
        <p className="mt-2 text-xs text-gray-400 truncate">
          📄 {scene.manuscriptLocation}
        </p>
      )}
    </button>
  );
}
