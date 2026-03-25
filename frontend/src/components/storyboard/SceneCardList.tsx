import { useNavigate } from 'react-router-dom';
import type { Scene } from '../../types/scene';
import SceneCard from './SceneCard';

interface SceneCardListProps {
  scenes: Scene[];
}

export default function SceneCardList({ scenes }: SceneCardListProps) {
  const navigate = useNavigate();

  const handleSceneClick = (scene: Scene) => {
    console.log(`Navigation event: Jump to scene ${scene.scene_id}`);
    navigate(`/project/${scene.chapter_number}/scene/${scene.scene_id}`);
  };

  if (!scenes || scenes.length === 0) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500 mb-2">No scenes yet</p>
        <button
          onClick={() => navigate('/planning')}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Create in Planning Board
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {scenes.map((scene) => (
        <SceneCard
          key={scene.scene_id}
          scene={scene}
          onClick={() => handleSceneClick(scene)}
        />
      ))}
    </div>
  );
}
