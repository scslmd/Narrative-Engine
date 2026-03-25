import { useProjectSequence } from '../hooks/useProjects';
import { SkeletonCard } from './skeleton';

interface Props {
  projectId: string;
}

export function SequenceViewer({ projectId }: Props): React.ReactElement {
  const { data: sequence, isLoading } = useProjectSequence(projectId);

  if (isLoading) {
    return <SkeletonCard />;
  }

  if (!sequence || !sequence.beats || sequence.beats.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
        <p className="text-gray-500">No sequence available. Run the Sequencer phase first.</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Story Sequence</h2>

      <div className="space-y-3 max-h-[calc(100vh-20rem)] overflow-y-auto pr-2">
        {sequence.beats.map((beat, index) => (
          <BeatCard key={beat.beat_id || index} beat={beat} index={index + 1} />
        ))}
      </div>

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500">
        {sequence.beats.length} beats • Updated: {new Date(sequence.updated_at).toLocaleString()}
      </div>
    </div>
  );
}

interface BeatCardProps {
  beat: {
    beat_id?: string;
    beat_number: number;
    title: string;
    description: string;
    purpose?: string;
    emotional_tone?: string;
  };
  index: number;
}

function BeatCard({ beat, index }: BeatCardProps): React.ReactElement {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-2">
      <div className="flex items-center gap-3">
        <span className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
          {index}
        </span>
        <h3 className="font-medium text-gray-900 dark:text-white">{beat.title}</h3>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 pl-11 whitespace-pre-wrap">
        {beat.description}
      </p>

      {beat.purpose && (
        <div className="pl-11 space-y-1">
          <p className="text-xs text-gray-500 dark:text-gray-500">
            <span className="font-medium">Purpose:</span> {beat.purpose}
          </p>
        </div>
      )}

      {beat.emotional_tone && (
        <div className="pl-11">
          <p className="text-xs text-gray-500 dark:text-gray-500">
            <span className="font-medium">Emotional Tone:</span> {beat.emotional_tone}
          </p>
        </div>
      )}
    </div>
  );
}
