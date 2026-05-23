import { useState } from 'react';
import type { RelationshipEdge } from '../../../types/characters';

export function useRelationshipEditing() {
  const [showCreateRelationship, setShowCreateRelationship] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState<RelationshipEdge | null>(null);
  return {
    showCreateRelationship,
    setShowCreateRelationship,
    editingRelationship,
    setEditingRelationship,
  };
}
