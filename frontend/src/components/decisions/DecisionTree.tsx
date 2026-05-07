import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { StoryDecisionNode, StoryDecisionPath } from '../../types/decisions';
import { getDecisions, getDecisionPath } from '../../services/decisions';
import { DecisionNode } from './DecisionNode';

interface DecisionTreeProps {
  projectId: string;
}

export function DecisionTree({ projectId }: DecisionTreeProps) {
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);

  const { data: nodes = [], isLoading } = useQuery<StoryDecisionNode[]>({
    queryKey: ['decisions', projectId],
    queryFn: () => getDecisions(projectId),
  });

  const { data: currentPath } = useQuery<StoryDecisionPath | null>({
    queryKey: ['decision-path', currentNodeId],
    queryFn: () => (currentNodeId ? getDecisionPath(currentNodeId) : Promise.resolve(null)),
    enabled: !!currentNodeId,
  });

  const handleSelectOption = (_optionId: string, nextNodeId?: string) => {
    if (nextNodeId) {
      setCurrentNodeId(nextNodeId);
    }
  };

  const handleReset = () => {
    setCurrentNodeId(null);
  };

  if (isLoading) {
    return <div className="text-gray-500 dark:text-slate-400">Loading decision tree...</div>;
  }

  if (nodes.length === 0) {
    return (
      <div className="border rounded-lg p-8 text-center bg-gray-50 dark:bg-slate-900">
        <p className="text-gray-600 dark:text-slate-400">No decision nodes defined</p>
      </div>
    );
  }

  const currentNode = currentNodeId ? nodes.find(n => n.node_id === currentNodeId) : null;
  // Root nodes have no parent_node_id
  const rootNodes = nodes.filter(n => !n.parent_node_id);

  return (
    <div className="space-y-4">
      {currentPath && (
        <div className="flex items-center gap-2 text-sm bg-gray-100 dark:bg-slate-700 rounded p-3">
          <span className="text-gray-600 dark:text-slate-400">Current path:</span>
          <span className="font-medium">{currentPath.nodes.join(' → ')}</span>
          <button
            onClick={handleReset}
            className="ml-auto px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Reset
          </button>
        </div>
      )}

      {!currentNode && rootNodes.length > 0 && (
        <div className="mb-4">
          <h3 className="font-semibold text-gray-900 dark:text-slate-100 mb-2">Start from root:</h3>
          {rootNodes.map((node) => (
            <DecisionNode
              key={node.node_id}
              node={node}
              isActive={false}
              onSelectOption={(optionId, nextNodeId) => {
                handleSelectOption(optionId, nextNodeId);
              }}
            />
          ))}
        </div>
      )}

      {currentNode && (
        <>
          <h3 className="font-semibold text-gray-900 dark:text-slate-100">Current decision point:</h3>
          <DecisionNode
            node={currentNode}
            isActive={true}
            onSelectOption={(optionId, nextNodeId) => {
              handleSelectOption(optionId, nextNodeId);
            }}
          />
        </>
      )}

      <div className="border-t pt-4">
        <h3 className="font-semibold text-gray-900 dark:text-slate-100 mb-2">All decision points:</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {nodes.map(node => (
            <button
              key={node.node_id}
              onClick={() => setCurrentNodeId(node.node_id)}
              className={`w-full text-left px-3 py-2 rounded ${currentNode?.node_id === node.node_id ? 'bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-600' : 'hover:bg-gray-100 dark:hover:bg-slate-600'}`}
            >
              <span className="text-sm font-medium">{node.decision_point}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
