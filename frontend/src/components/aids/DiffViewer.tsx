import { useMemo } from 'react';
import { computeDiff, getDiffSummary } from '../../lib/diff';
import type { DiffChange } from '../../lib/diff';

interface DiffViewerProps {
  originalText: string;
  modifiedText: string;
  originalLabel?: string;
  modifiedLabel?: string;
  inline?: boolean;
}

export function DiffViewer({
  originalText,
  modifiedText,
  originalLabel = 'Original',
  modifiedLabel = 'Modified',
  inline = false,
}: DiffViewerProps) {
  const diff = useMemo(() => computeDiff(originalText, modifiedText), [originalText, modifiedText]);
  const summary = useMemo(() => getDiffSummary(diff), [diff]);

  if (inline) {
    return <InlineDiff changes={diff.changes} summary={summary} />;
  }

  return <SideBySideDiff diff={diff} summary={summary} originalLabel={originalLabel} modifiedLabel={modifiedLabel} />;
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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-600">{summary.additions} additions</span>
          <span className="text-gray-600">{summary.deletions} deletions</span>
          <span className="text-gray-600">{summary.replacements} replacements</span>
        </div>
      </div>

      {/* Diff panels */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col min-w-0">
          <div className="px-3 py-2 bg-gray-100 border-b border-gray-200 text-sm font-medium text-gray-700">
            {originalLabel}
          </div>
          <div className="flex-1 overflow-auto p-2 font-mono text-sm">
            <pre className="whitespace-pre-wrap break-words">
              {diff.changes.map((change, idx) => (
                <span key={idx} className={getChangeClass(change.type)}>
                  {change.value}
                </span>
              ))}
            </pre>
          </div>
        </div>

        <div className="flex-1 flex flex-col min-w-0 border-l border-gray-200">
          <div className="px-3 py-2 bg-gray-100 border-b border-gray-200 text-sm font-medium text-gray-700">
            {modifiedLabel}
          </div>
          <div className="flex-1 overflow-auto p-2 font-mono text-sm">
            <pre className="whitespace-pre-wrap break-words">
              {diff.changes.map((change, idx) => (
                <span key={idx} className={getChangeClass(change.type)}>
                  {change.value}
                </span>
              ))}
            </pre>
          </div>
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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-4 p-3 bg-gray-50 border-b border-gray-200 text-sm">
        <span className="text-green-600">+{summary.additions}</span>
        <span className="text-red-600">-{summary.deletions}</span>
        <span className="text-yellow-600">~{summary.replacements}</span>
      </div>

      {/* Diff content */}
      <div className="flex-1 overflow-auto p-2 font-mono text-sm">
        <pre className="whitespace-pre-wrap break-words">
          {changes.map((change, idx) => (
            <span key={idx} className={getChangeClass(change.type)}>
              {change.value}
            </span>
          ))}
        </pre>
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
