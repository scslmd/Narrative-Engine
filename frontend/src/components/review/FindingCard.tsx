import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { CheckerFinding } from '../../types/review';
import { getInspectLinks } from '../../services/inspectLinks';
import { getFinding } from '../../services/review';
import { useToastStore } from '../../stores/toastStore';
import { useUIStore } from '../../stores/uiStore';
import { SeverityBadge } from './SeverityBadge';
import { DecisionForm } from './DecisionForm';
import { DecisionHistory } from './DecisionHistory';

interface FindingCardProps {
  finding: CheckerFinding;
  projectId: string;
  onSelect?: (finding: CheckerFinding) => void;
}

export function FindingCard({ finding, projectId, onSelect }: FindingCardProps) {
  const navigate = useNavigate();
  const addToast = useToastStore((state) => state.addToast);
  const setInspectContext = useUIStore((state) => state.setInspectContext);
  const [expanded, setExpanded] = useState(false);
  const [showDecisionForm, setShowDecisionForm] = useState(false);
  const [isResolvingInspectRun, setIsResolvingInspectRun] = useState(false);
  const [hydratedFinding, setHydratedFinding] = useState<CheckerFinding | null>(null);

  const handleCardClick = () => {
    if (!expanded) {
      void getFinding(finding.finding_id, projectId).then((loaded) => {
        setHydratedFinding(loaded);
      });
    }
    if (onSelect) {
      onSelect(finding);
    }
    setExpanded(!expanded);
  };

  const hasValidInspectTarget =
    Boolean(finding.source_object_kind) &&
    Boolean(finding.source_object_id);

  const handleJumpToSource = async () => {
    if (!hasValidInspectTarget) return;

    setIsResolvingInspectRun(true);

    try {
      const links = await getInspectLinks(
        projectId,
        finding.source_object_kind,
        finding.source_object_id,
      );
      const primaryLink = links[0];

      if (!primaryLink?.run_id) {
        addToast('No inspect run is linked to this finding source yet', 'warning');
        return;
      }

      const runKind: 'pipeline_job' | 'role_model_check' = 
        primaryLink.run_kind === 'role_model_check' ? 'role_model_check' : 'pipeline_job';
      
      setInspectContext({
        jobId: primaryLink.run_id,
        runKind,
        attemptNumber: primaryLink.attempt_number ?? undefined,
      });

      navigate(`/workspace/${projectId}/inspect/${primaryLink.run_id}`);
    } catch (error) {
      addToast(error instanceof Error ? error.message : 'Failed to open inspect run', 'error');
    } finally {
      setIsResolvingInspectRun(false);
    }
  };

  const handleDecisionSuccess = () => {
    setShowDecisionForm(false);
  };

  return (
    <div 
      className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={handleCardClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <SeverityBadge severity={finding.severity} />
            <span className="text-sm text-gray-500">{finding.source_object_kind}</span>
          </div>
          
          <h4 className="font-medium text-gray-900 line-clamp-2">
            {finding.summary}
          </h4>

          {expanded && (
            <div className="mt-3 space-y-2">
              <p className="text-sm text-gray-600">{hydratedFinding?.details ?? finding.details}</p>
              
              {finding.source_context && (
                <div className="bg-gray-100 rounded p-2 text-xs font-mono overflow-x-auto">
                  {finding.source_context}
                </div>
              )}

              <div className="flex gap-2 mt-2">
                <button 
                  className={`px-3 py-1.5 text-sm rounded ${
                    hasValidInspectTarget 
                      ? 'bg-blue-600 text-white hover:bg-blue-700' 
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleJumpToSource();
                  }}
                  disabled={!hasValidInspectTarget || isResolvingInspectRun}
                  title={!hasValidInspectTarget ? 'No inspectable source available' : ''}
                >
                  {isResolvingInspectRun ? 'Opening...' : 'Jump to Source'}
                </button>

                <button 
                  className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowDecisionForm(!showDecisionForm);
                  }}
                >
                  {showDecisionForm ? 'Hide Decision Form' : 'Record Decision'}
                </button>
              </div>

              {showDecisionForm && (
                <DecisionForm finding={finding} onSuccess={handleDecisionSuccess} />
              )}

              <DecisionHistory findingId={finding.finding_id} />
            </div>
          )}
        </div>

        <span className="text-xs text-gray-400">
          {new Date().toLocaleDateString()}
        </span>
      </div>
    </div>
  );
}
