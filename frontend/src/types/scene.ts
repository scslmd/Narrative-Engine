export interface Scene {
  id: string;
  title: string;
  purpose: string;
  activeCharacters: string[];
  hasConflict: boolean;
  manuscriptLocation?: string;
}
