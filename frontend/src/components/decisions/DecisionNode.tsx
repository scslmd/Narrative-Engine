import type { StoryDecisionNode } from '../../types/decisions';

interface DecisionNodeProps {
  node: StoryDecisionNode;
  isActive: boolean;
  onSelectOption: (optionId: string, nextNodeId?: string) => void;
}

export function DecisionNode({ node, isActive, onSelectOption }: DecisionNodeProps) {
  return (
    <div className={`border-2 rounded-lg p-4 ${isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'}`}>
      <h4 className="font-semibold text-gray-900 mb-3">{node.decision_point}</h4>

      <div className="space-y-2">
        {node.options.map(option => (
          <button
            key={option.option_id}
            onClick={() => onSelectOption(option.option_id, option.next_node_id)}
            className="w-full text-left px-3 py-2 bg-white border rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <span className="text-sm text-gray-700">{option.label}</span>
          </button>
        ))}
      </div>

      {isActive && (
        <div className="mt-3 text-xs text-blue-600">Current decision point</div>
      )}
    </div>
  );
}
