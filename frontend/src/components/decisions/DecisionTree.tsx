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

  const handleSelectOption = (optionId: string, nextNodeId?: string) => {
    console.log('Selected option:', optionId);
    if (nextNodeId) {
      setCurrentNodeId(nextNodeId);
    }
  };

  const handleReset = () => {
    setCurrentNodeId(null);
  };

  if (isLoading) {
    return <div className="text-gray-500">Loading decision tree...</div>;
  }

  if (nodes.length === 0) {
    return (
      <div className="border rounded-lg p-8 text-center bg-gray-50">
        <p className="text-gray-600">No decision nodes defined</p>
      </div>
    );
  }

  const currentNode = currentNodeId ? nodes.find(n => n.node_id === currentNodeId) : null;
  const rootNode = nodes[0]; // Assume first node is root for now

  return (
    <div className="space-y-4">
      {currentPath && (
        <div className="flex items-center gap-2 text-sm bg-gray-100 rounded p-3">
          <span className="text-gray-600">Current path:</span>
          <span className="font-medium">{currentPath.nodes.join(' → ')}</span>
          <button
            onClick={handleReset}
            className="ml-auto px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Reset
          </button>
        </div>
      )}

      {!currentNode && (
        <div className="mb-4">
          <h3 className="font-semibold text-gray-900 mb-2">Start from root:</h3>
          <DecisionNode
            node={rootNode}
            isActive={false}
            onSelectOption={(optionId, nextNodeId) => {
              handleSelectOption(optionId, nextNodeId);
            }}
          />
        </div>
      )}

      {currentNode && (
        <>
          <h3 className="font-semibold text-gray-900">Current decision point:</h3>
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
        <h3 className="font-semibold text-gray-900 mb-2">All decision points:</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {nodes.map(node => (
            <button
              key={node.node_id}
              onClick={() => setCurrentNodeId(node.node_id)}
              className={`w-full text-left px-3 py-2 rounded ${currentNode?.node_id === node.node_id ? 'bg-blue-100 border border-blue-300' : 'hover:bg-gray-100'}`}
            >
              <span className="text-sm font-medium">{node.decision_point}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
