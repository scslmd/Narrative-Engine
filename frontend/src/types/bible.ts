export type BibleEntryType = 'character' | 'location' | 'rule' | 'object' | 'concept';

export interface BibleEntry {
  id: string;
  type: BibleEntryType;
  title: string;
  summary: string;
  details?: string;
}
