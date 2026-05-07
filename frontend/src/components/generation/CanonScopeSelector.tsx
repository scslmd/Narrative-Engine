import type { CharacterProfile } from '../../types/characters';
import type { WorldBibleEntry } from '../../types/bible';
import type { CanonScope } from '../../types/storyGeneration';

interface CanonScopeSelectorProps {
  scope: CanonScope;
  characters: CharacterProfile[];
  worldEntries: WorldBibleEntry[];
  onChange: (scope: CanonScope) => void;
}

export function CanonScopeSelector({ scope, characters, worldEntries, onChange }: CanonScopeSelectorProps) {
  const toggleCharacter = (characterId: string) => {
    const next = scope.character_ids.includes(characterId)
      ? scope.character_ids.filter((item) => item !== characterId)
      : [...scope.character_ids, characterId];
    onChange({ ...scope, character_ids: next });
  };
  const toggleWorld = (entryType: string, title: string) => {
    const exists = scope.world_bible_refs.some((item) => item.entry_type === entryType && item.title === title);
    const next = exists
      ? scope.world_bible_refs.filter((item) => !(item.entry_type === entryType && item.title === title))
      : [...scope.world_bible_refs, { entry_type: entryType, title }];
    onChange({ ...scope, world_bible_refs: next });
  };
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold mb-2 text-slate-900 dark:text-slate-100">Characters</h3>
        <div className="flex flex-wrap gap-2">
          {characters.map((character) => (
            <button
              key={character.character_id}
              type="button"
              onClick={() => toggleCharacter(character.character_id)}
              className={`px-2 py-1 rounded border text-xs transition-colors ${
                 scope.character_ids.includes(character.character_id)
                   ? 'bg-emerald-600 text-white border-emerald-600'
                   : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-600'
               }`}
            >
              {character.display_name}
            </button>
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold mb-2 text-slate-900 dark:text-slate-100">World Bible</h3>
        <div className="flex flex-wrap gap-2">
          {worldEntries.map((entry) => {
            const selected = scope.world_bible_refs.some(
              (item) => item.entry_type === entry.entry_type && item.title === entry.title,
            );
            return (
              <button
                key={`${entry.entry_type}:${entry.title}`}
                type="button"
                onClick={() => toggleWorld(entry.entry_type, entry.title)}
                className={`px-2 py-1 rounded border text-xs transition-colors ${selected ? 'bg-sky-600 text-white border-sky-600' : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400 dark:hover:border-slate-600'}`}
              >
                {entry.title}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
