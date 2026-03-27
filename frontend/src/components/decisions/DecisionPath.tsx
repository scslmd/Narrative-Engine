import type { StoryDecisionPath } from '../../types/decisions';

interface DecisionPathProps {
  path: StoryDecisionPath;
  nodes: Array<{ node_id: string; decision_point: string }>;
}

export function DecisionPath({ path, nodes }: DecisionPathProps) {
  return (
    <div className="flex items-center flex-wrap gap-2 text-sm">
      {path.nodes.map((nodeId, index) => {
        const node = nodes.find(n => n.node_id === nodeId);
        if (!node) return null;

        return (
          <span key={nodeId} className="inline-flex items-center">
            <span className={`px-2 py-1 rounded ${index === path.nodes.length - 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
              {node.decision_point}
            </span>
            {index < path.nodes.length - 1 && (
              <span className="mx-1 text-gray-400">→</span>
            )}
          </span>
        );
      })}
    </div>
  );
}
