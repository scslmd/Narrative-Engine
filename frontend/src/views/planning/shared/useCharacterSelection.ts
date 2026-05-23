import { useState } from 'react';

export function useCharacterSelection() {
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);
  return { selectedCharacterId, setSelectedCharacterId };
}
