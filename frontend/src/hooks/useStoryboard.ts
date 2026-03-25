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
    if (projectId) {
      loadScenes();
    } else {
      setScenes([]);
      setLoading(false);
    }
  }, [projectId]);

  const loadScenes = async () => {
    setLoading(true);
    
    try {
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      if (projectId) {
        setScenes(MOCK_SCENES);
      } else {
        setScenes([]);
      }
    } catch (error) {
      console.error('Failed to load storyboard:', error);
      setScenes([]);
    } finally {
      setLoading(false);
    }
  };

  const navigateToScene = (scene: Scene) => {
    if (scene.manuscriptLocation) {
      console.log(`Navigating to manuscript location: ${scene.manuscriptLocation}`);
    } else {
      console.log(`No manuscript location for scene: ${scene.title}`);
    }
  };

  return { scenes, loading, navigateToScene };
}
