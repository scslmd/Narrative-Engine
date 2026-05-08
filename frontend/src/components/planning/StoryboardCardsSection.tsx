import { Trash2 } from 'lucide-react';
import { Section } from './ui';
import { useIsDark } from './hooks';
import type { StoryboardCard } from '../../types/planning';
import type { ApiError } from '../../lib/api';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingState } from '../ui/LoadingState';
import { EmptyState } from '../ui/EmptyState';

export interface StoryboardCardsSectionProps {
  cards: StoryboardCard[];
  isLoading: boolean;
  error: ApiError | null;
  onRetry: () => void;
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
  editOpenId: string | null;
  editTitle: string;
  editContent: string;
  editType: string;
  onEditOpen: (card: StoryboardCard) => void;
  onEditClose: () => void;
  onEditTitleChange: (value: string) => void;
  onEditContentChange: (value: string) => void;
  onEditTypeChange: (value: string) => void;
  onUpdate: (cardId: string) => void;
  onDelete: (cardId: string) => void;
  onReorder: (columnId: string, orderedIds: string[]) => void;
  onUpdateButtonDisabled: boolean;
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
  editOpenId,
  editTitle,
  editContent,
  editType,
  onEditOpen,
  onEditClose,
  onEditTitleChange,
  onEditContentChange,
  onEditTypeChange,
  onUpdate,
  onDelete,
  onReorder,
  onUpdateButtonDisabled,
  error,
  onRetry,
}: StoryboardCardsSectionProps) {
  const isDark = useIsDark();
  const inputClass = `text-sm px-2 py-1 rounded border w-40 ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`;
  const selectClass = `text-sm px-2 py-1 rounded border ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`;
  const editInputClass = `text-xs px-2 py-1 rounded border w-full ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`;
  const editSelectClass = `text-xs px-2 py-1 rounded border w-full ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`;
  const cardClass = `p-3 rounded-lg border cursor-grab active:cursor-grabbing ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`;

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>, cardId: string) => {
    e.dataTransfer.setData('application/card-id', cardId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>, targetCardId: string) => {
    e.preventDefault();
    const draggedCardId = e.dataTransfer.getData('application/card-id');
    if (!draggedCardId || draggedCardId === targetCardId) return;

    const newOrder = [...cards];
    const dragIndex = newOrder.findIndex((c) => c.card_id === draggedCardId);
    const dropIndex = newOrder.findIndex((c) => c.card_id === targetCardId);
    if (dragIndex < 0 || dropIndex < 0) return;

    const [removed] = newOrder.splice(dragIndex, 1);
    newOrder.splice(dropIndex, 0, removed);

    const columnId = cards.find((c) => c.card_id === targetCardId)?.column_id ?? 'default';
    const orderedIds = newOrder.filter((c) => c.column_id === columnId).map((c) => c.card_id);
    onReorder(columnId, orderedIds);
  };

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
      {error ? (
        <ErrorBanner error={error} onRetry={onRetry} />
      ) : (
        <LoadingState isLoading={isLoading}>
          {cards.length === 0 ? (
            <EmptyState title="No storyboard cards" description="Capture ideas, scenes, and plot points." actionLabel="Add Card" onAction={onCreateOpen} />
          ) : (
            <div className="space-y-2">
              {cards.map((card) => (
                <div
                  key={card.card_id}
                  className={cardClass}
                  draggable
                  onDragStart={(e) => handleDragStart(e, card.card_id)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, card.card_id)}
                >
                  {editOpenId === card.card_id ? (
                    <div className="flex flex-col gap-2">
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => onEditTitleChange(e.target.value)}
                        placeholder="Card title"
                        className={editInputClass}
                      />
                      <textarea
                        value={editContent}
                        onChange={(e) => onEditContentChange(e.target.value)}
                        placeholder="Card content (optional)"
                        rows={2}
                        className={`text-xs px-2 py-1 rounded border w-full resize-none ${isDark ? 'bg-slate-900 border-slate-700 text-slate-200' : 'bg-white border-gray-300 text-gray-900'}`}
                      />
                      <select
                        value={editType}
                        onChange={(e) => onEditTypeChange(e.target.value)}
                        className={editSelectClass}
                      >
                        <option value="idea">Idea</option>
                        <option value="scene">Scene</option>
                        <option value="character">Character</option>
                        <option value="location">Location</option>
                        <option value="plot">Plot Point</option>
                      </select>
                      <div className="flex gap-2">
                        <button
                          onClick={() => onUpdate(card.card_id)}
                          disabled={!editTitle.trim() || onUpdateButtonDisabled}
                          className="text-xs px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50"
                        >
                          Save
                        </button>
                        <button
                          onClick={onEditClose}
                          className={`text-xs px-3 py-1 rounded border ${isDark ? 'border-gray-600' : 'border-gray-300'}`}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium">{card.title}</div>
                        {card.content && <p className="text-sm mt-1 text-body">{card.content}</p>}
                        {card.tags.length > 0 && (
                          <div className="flex gap-1 mt-1 flex-wrap">
                            {card.tags.map((tag) => (
                              <span key={tag} className={`text-xs px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>{tag}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={() => onEditOpen(card)}
                          className={`text-xs px-2 py-0.5 rounded ${isDark ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800' : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'}`}
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => {
                            if (window.confirm('Delete this card?')) {
                              onDelete(card.card_id);
                            }
                          }}
                          className={`p-0.5 rounded transition-colors ${isDark ? 'text-red-400 hover:text-red-300 hover:bg-slate-800' : 'text-red-400 hover:text-red-600 hover:bg-red-50'}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${isDark ? 'bg-purple-950 text-purple-300' : 'bg-purple-100 text-purple-700'}`}>
                          {card.card_type}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </LoadingState>
      )}
    </Section>
  );
}
