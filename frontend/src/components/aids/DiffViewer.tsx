import { useMemo } from 'react';
import { computeDiff, getDiffSummary } from '../../lib/diff';
import type { DiffChange } from '../../types/aids';

interface DiffViewerProps {
  originalText?: string | null;
  modifiedText?: string | null;
  originalLabel?: string;
  modifiedLabel?: string;
  inline?: boolean;
  emptyStateTitle?: string;
  emptyStateDescription?: string;
}

export function DiffViewer({
  originalText,
  modifiedText,
  originalLabel = 'Original',
  modifiedLabel = 'Modified',
  inline = false,
  emptyStateTitle = 'No comparison selected',
  emptyStateDescription = 'Select a suggestion or compare target to inspect the diff.',
}: DiffViewerProps) {
  const hasComparisonTarget = originalText !== undefined && modifiedText !== undefined;

  const diff = useMemo(() => {
    if (!hasComparisonTarget) {
      return null;
    }

    return computeDiff(originalText ?? '', modifiedText ?? '');
  }, [hasComparisonTarget, originalText, modifiedText]);

  const summary = useMemo(() => {
    if (!diff) {
      return null;
    }

    return getDiffSummary(diff);
  }, [diff]);

  if (!diff || !summary) {
    return <EmptyDiffState title={emptyStateTitle} description={emptyStateDescription} />;
  }

  if (diff.changes.length === 0) {
    return (
      <EmptyDiffState
        title="No text to compare"
        description="The selected item does not contain any source or proposed text content."
      />
    );
  }

  if (inline) {
    return <InlineDiff changes={diff.changes} summary={summary} />;
  }

  return (
    <SideBySideDiff
      diff={diff}
      summary={summary}
      originalLabel={originalLabel}
      modifiedLabel={modifiedLabel}
    />
  );
}

function SideBySideDiff({
  diff,
  summary,
  originalLabel,
  modifiedLabel,
}: {
  diff: ReturnType<typeof computeDiff>;
  summary: ReturnType<typeof getDiffSummary>;
  originalLabel: string;
  modifiedLabel: string;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 p-3">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-600">{summary.additions} additions</span>
          <span className="text-gray-600">{summary.deletions} deletions</span>
          <span className="text-gray-600">{summary.replacements} replacements</span>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-2 border-b border-gray-200 bg-gray-100 text-sm font-medium text-gray-700">
          <div className="border-r border-gray-200 px-3 py-2">{originalLabel}</div>
          <div className="px-3 py-2">{modifiedLabel}</div>
        </div>

        <div className="divide-y divide-gray-100 font-mono text-sm">
          {diff.changes.map((change, index) => (
            <div key={`${change.type}-${index}`} className="grid grid-cols-2">
              <div className={`min-h-[2.5rem] border-r border-gray-100 px-3 py-2 ${getCellClass(change.type, 'original')}`}>
                <pre className="whitespace-pre-wrap break-words">{change.originalText || '\u00A0'}</pre>
              </div>
              <div className={`min-h-[2.5rem] px-3 py-2 ${getCellClass(change.type, 'modified')}`}>
                <pre className="whitespace-pre-wrap break-words">{change.modifiedText || '\u00A0'}</pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function InlineDiff({
  changes,
  summary,
}: {
  changes: DiffChange[];
  summary: ReturnType<typeof getDiffSummary>;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-4 border-b border-gray-200 bg-gray-50 p-3 text-sm">
        <span className="text-green-600">+{summary.additions}</span>
        <span className="text-red-600">-{summary.deletions}</span>
        <span className="text-yellow-600">~{summary.replacements}</span>
      </div>

      <div className="flex-1 overflow-auto p-2 font-mono text-sm">
        <pre className="whitespace-pre-wrap break-words">
          {changes.map((change, index) => (
            <span key={`${change.type}-${index}`} className={getChangeClass(change.type)}>
              {formatInlineChange(change)}
            </span>
          ))}
        </pre>
      </div>
    </div>
  );
}

function EmptyDiffState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex h-full items-center justify-center p-6 text-center text-gray-500">
      <div className="max-w-sm">
        <p className="text-sm font-medium text-gray-700">{title}</p>
        <p className="mt-2 text-sm">{description}</p>
      </div>
    </div>
  );
}

function getChangeClass(type: DiffChange['type']): string {
  switch (type) {
    case 'delete':
      return 'bg-red-100 text-red-800 line-through';
    case 'insert':
      return 'bg-green-100 text-green-800';
    case 'replace':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'text-gray-700';
  }
}

function formatInlineChange(change: DiffChange): string {
  switch (change.type) {
    case 'equal':
      return change.originalText;
    case 'delete':
      return `- ${change.originalText}`;
    case 'insert':
      return `+ ${change.modifiedText}`;
    case 'replace':
      return `- ${change.originalText}\n+ ${change.modifiedText}`;
  }
}

function getCellClass(type: DiffChange['type'], side: 'original' | 'modified'): string {
  if (type === 'equal') {
    return 'text-gray-700';
  }

  if (type === 'replace') {
    return 'bg-yellow-100 text-yellow-800';
  }

  if (type === 'delete') {
    return side === 'original' ? 'bg-red-100 text-red-800 line-through' : 'bg-gray-50 text-gray-400';
  }

  return side === 'modified' ? 'bg-green-100 text-green-800' : 'bg-gray-50 text-gray-400';
}
