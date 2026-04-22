import { Section, EmptyState, WorkspaceStatus } from './ui';
import { useIsDark } from './hooks';
import type { StoryboardCard } from '../../types/planning';

export interface StoryboardCardsSectionProps {
  cards: StoryboardCard[];
  isLoading: boolean;
  createOpen: boolean;
  createTitle: string;
  createContent: string;
  createType: string;
  onCreateOpen: () => void;
  onCreateClose: () => void;
  onCreateTitleChange: (value: string) => void;
  onCreateContentChange: (value: string) => void;
  onCreateTypeChange: (value: string) => void;
  onCreate: () => void;
  onCreateButtonDisabled: boolean;
}

export function StoryboardCardsSection({
  cards,
  isLoading,
  createOpen,
  createTitle,
  createContent,
  createType,
  onCreateOpen,
  onCreateClose,
  onCreateTitleChange,
  onCreateContentChange,
  onCreateTypeChange,
  onCreate,
  onCreateButtonDisabled,
}: StoryboardCardsSectionProps) {
  const isDark = useIsDark();
  const inputClass = `text-sm px-2 py-1 rounded border w-40 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`;
  const selectClass = `text-sm px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`;

  return (
    <Section
      title="Storyboard Cards"
      count={cards.length}
      actions={
        <div className="flex justify-end mb-2">
          {!createOpen ? (
            <button
              onClick={onCreateOpen}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${isDark ? 'bg-purple-950 text-purple-300 hover:bg-purple-900' : 'bg-purple-50 text-purple-700 hover:bg-purple-100'}`}
            >
              + New Card
            </button>
          ) : (
            <div className="flex flex-col gap-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Card title"
                  value={createTitle}
                  onChange={(e) => onCreateTitleChange(e.target.value)}
                  className={inputClass}
                />
                <select
                  value={createType}
                  onChange={(e) => onCreateTypeChange(e.target.value)}
                  className={selectClass}
                >
                  <option value="idea">Idea</option>
                  <option value="scene">Scene</option>
                  <option value="character">Character</option>
                  <option value="location">Location</option>
                  <option value="plot">Plot Point</option>
                </select>
                <button
                  onClick={onCreate}
                  disabled={onCreateButtonDisabled}
                  className="text-xs px-2.5 py-1 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-40"
                >
                  Create
                </button>
                <button onClick={onCreateClose} className={`text-xs px-2 py-1 rounded-md ${isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-700'}`}>
                  Cancel
                </button>
              </div>
              <textarea
                placeholder="Card content (optional)"
                value={createContent}
                onChange={(e) => onCreateContentChange(e.target.value)}
                rows={2}
                className={`text-sm px-2 py-1 rounded border resize-none ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
              />
            </div>
          )}
        </div>
      }
    >
      {isLoading ? (
        <WorkspaceStatus title="Loading storyboard cards" detail="Fetching storyboard cards..." />
      ) : cards.length === 0 ? (
        <EmptyState text="No storyboard cards yet. Create cards to capture ideas, scenes, and plot points." />
      ) : (
        <div className="space-y-2">
          {cards.map((card) => (
            <div key={card.card_id} className={`p-3 rounded-lg border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-medium">{card.title}</div>
                  {card.content && <p className={`text-sm mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{card.content}</p>}
                  {card.tags.length > 0 && (
                    <div className="flex gap-1 mt-1 flex-wrap">
                      {card.tags.map((tag) => (
                        <span key={tag} className={`text-xs px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${isDark ? 'bg-purple-950 text-purple-300' : 'bg-purple-100 text-purple-700'}`}>
                  {card.card_type}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}
