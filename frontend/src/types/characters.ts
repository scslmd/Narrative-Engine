export interface CharacterRecord {
  character_id: string;
  project_id: string;
  name: string;
  description: string;
  personality: string;
  motivation: string;
  conflict: string;
  arc: string;
  role: 'PROTAGONIST' | 'ANTAGONIST' | 'DEUTERAGONIST' | 'SUPPORTING' | 'TERTIARY';
  is_antagonist: boolean;
  created_at: string;
  updated_at: string;
}

export interface CharacterRelationship {
  relationship_id: string;
  project_id: string;
  character_id_a: string;
  character_id_b: string;
  relationship_type: string;
  description: string;
  created_at: string;
}
