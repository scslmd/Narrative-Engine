import { useState, useEffect } from 'react';
import type { Scene } from '../types/scene';

const MOCK_SCENES: Scene[] = [
  {
    id: '1',
    title: 'The Awakening',
    purpose: 'Introduce protagonist in their ordinary world before the inciting incident',
    activeCharacters: ['Alex Chen'],
    hasConflict: false,
    manuscriptLocation: 'chapter-001.md',
  },
  {
    id: '2',
    title: 'The Call',
    purpose: 'Present the opportunity that will change everything',
    activeCharacters: ['Alex Chen', 'Mysterious Stranger'],
    hasConflict: true,
    manuscriptLocation: 'chapter-002.md',
  },
  {
    id: '3',
    title: 'Crossing the Threshold',
    purpose: 'Protagonist commits to the journey and leaves their comfort zone',
    activeCharacters: ['Alex Chen'],
    hasConflict: true,
    manuscriptLocation: 'chapter-003.md',
  },
];

export function useStoryboard(projectId?: string) {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const loadScenes = async () => {
      if (!projectId) {
        setScenes([]);
        setLoading(false);
        return;
      }

      setLoading(true);

      try {
        await new Promise((resolve) => setTimeout(resolve, 500));
        if (!cancelled) {
          setScenes(MOCK_SCENES);
        }
      } catch {
        if (!cancelled) {
          setScenes([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadScenes();

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const navigateToScene = (scene: Scene) => {
    return scene.manuscriptLocation ?? null;
  };

  return { scenes, loading, navigateToScene };
}
