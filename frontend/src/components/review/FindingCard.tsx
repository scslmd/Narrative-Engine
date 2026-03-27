import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { CheckerFinding, ReviewDecision } from '../../types/review';
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
  const [expanded, setExpanded] = useState(false);
  const [showDecisionForm, setShowDecisionForm] = useState(false);

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(finding);
    }
    setExpanded(!expanded);
  };

  const handleJumpToSource = () => {
    if (finding.source_object_id) {
      navigate(`/workspace/${projectId}/inspect?object=${finding.source_object_id}&kind=${finding.source_object_kind}`);
    }
  };

  const handleDecisionSuccess = (decision: ReviewDecision) => {
    console.log('Decision recorded:', decision.decision_id);
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
              <p className="text-sm text-gray-600">{finding.details}</p>
              
              {finding.source_context && (
                <div className="bg-gray-100 rounded p-2 text-xs font-mono overflow-x-auto">
                  {finding.source_context}
                </div>
              )}

              <div className="flex gap-2 mt-2">
                <button 
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleJumpToSource();
                  }}
                >
                  Jump to Source
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
