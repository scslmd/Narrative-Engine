import { useCallback, useState } from 'react';
import { ChevronDown, ChevronRight, Eye, Ear, Hand, UtensilsCrossed, Sparkles, Wand2, Zap, ArrowRight, GitBranch, BookOpen, Flower2 } from 'lucide-react';
import type { AssistAction } from '../../lib/assistActions';
import type { ManuscriptAssistKind } from '../../types/manuscriptAssist';

const SENSORY_KINDS: Set<string> = new Set([
  'expand_sensory_sight',
  'expand_sensory_sound',
  'expand_sensory_smell',
  'expand_sensory_texture',
  'expand_sensory_taste',
  'expand_metaphor',
  'expand_show_dont_tell',
]);

const ACTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  line_edit_selection: Wand2,
  expand_sensory_sight: Eye,
  expand_sensory_sound: Ear,
  expand_sensory_smell: Flower2,
  expand_sensory_texture: Hand,
  expand_sensory_taste: UtensilsCrossed,
  expand_metaphor: Sparkles,
  expand_show_dont_tell: BookOpen,
  compress_selection: Zap,
  rewrite_selection_same_voice: Wand2,
  alternate_selection: GitBranch,
  continue_from_selection: ArrowRight,
  fork_from_selection: GitBranch,
};

interface SelectionToolbarProps {
  actions: AssistAction[];
  visible: boolean;
  position: { x: number; y: number };
  onClick: (kind: ManuscriptAssistKind, instruction: string) => void;
}

export function SelectionToolbar({ actions, visible, position, onClick }: SelectionToolbarProps) {
  const [sensoryOpen, setSensoryOpen] = useState(false);

  const handleActionClick = useCallback(
    (action: AssistAction) => {
      onClick(action.kind, action.instructionTemplate({} as never));
    },
    [onClick],
  );

  if (!visible) {
    return null;
  }

  const sensoryActions = actions.filter((a) => SENSORY_KINDS.has(a.kind));
  const otherActions = actions.filter((a) => !SENSORY_KINDS.has(a.kind));

  // Group non-sensory actions by category for display
  const grouped: Record<string, AssistAction[]> = {};
  for (const action of otherActions) {
    const cat = action.kind.startsWith('continue') ? 'continue' : 'rewrite';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(action);
  }

  return (
    <div
      role="toolbar"
      aria-label="Selection actions"
      className="absolute z-50 flex flex-col gap-1 rounded-lg border bg-white p-2 shadow-lg dark:border-slate-700 dark:bg-slate-800"
      style={{ left: `${position.x}px`, top: `${position.y}px` }}
    >
      {/* Sensory submenu */}
      {sensoryActions.length > 0 && (
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="flex items-center gap-1 rounded px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-700 transition-colors"
            onClick={() => setSensoryOpen((o) => !o)}
          >
            {sensoryOpen
              ? <ChevronDown className="h-3 w-3" />
              : <ChevronRight className="h-3 w-3" />
            }
            Sensory detail
          </button>
        </div>
      )}
      {sensoryOpen && sensoryActions.length > 0 && (
        <div className="ml-4 flex flex-col gap-0.5">
          {sensoryActions.map((action) => {
            const Icon = ACTION_ICONS[action.kind] ?? Sparkles;
            return (
              <button
                key={action.kind}
                type="button"
                className="flex items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
                onClick={() => handleActionClick(action)}
                title={action.description}
              >
                <Icon className="h-3.5 w-3.5 flex-shrink-0 opacity-60" />
                <span>{action.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Grouped actions */}
      {Object.entries(grouped).map(([category, categoryActions]) => (
        categoryActions.length > 0 && (
          <div key={category}>
            <div className="px-1 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {category}
            </div>
            {categoryActions.map((action) => {
              const Icon = ACTION_ICONS[action.kind] ?? Wand2;
              return (
                <button
                  key={action.kind}
                  type="button"
                  className="flex items-center gap-2 rounded px-2 py-1.5 text-left text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
                  onClick={() => handleActionClick(action)}
                  title={action.description}
                >
                  <Icon className="h-3.5 w-3.5 flex-shrink-0 opacity-60" />
                  <span>{action.label}</span>
                </button>
              );
            })}
          </div>
        )
      ))}
    </div>
  );
}
