import type { Severity } from '../../types/review';

interface SeverityBadgeProps {
  severity: Severity;
}

const severityColors = {
  low: 'bg-blue-100 text-blue-800 border-blue-300',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  critical: 'bg-red-100 text-red-800 border-red-300',
} as const;

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${severityColors[severity]}`}>
      {severity.toUpperCase()}
    </span>
  );
}
