import { useState } from 'react';

interface PayloadBuilderProps {
  initialPayload?: Record<string, unknown>;
  onPayloadChange: (payload: Record<string, unknown>) => void;
}

const DEFAULT_PAYLOADS: Record<string, string> = {
  'P-100': JSON.stringify({ project_id: '', story_brief: '' }, null, 2),
  'P-200': JSON.stringify({ project_id: '', chapter_packet: {} }, null, 2),
  'P-300': JSON.stringify({ project_id: '', sequence_id: '' }, null, 2),
  'P-400': JSON.stringify({ project_id: '', manuscript_parts: [] }, null, 2),
};

export default function PayloadBuilder({ initialPayload, onPayloadChange }: PayloadBuilderProps) {
  const [jsonText, setJsonText] = useState<string>(JSON.stringify(initialPayload || {}, null, 2));
  const [error, setError] = useState<string | null>(null);

  const handleTextChange = (text: string) => {
    setJsonText(text);
    
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
        setError(null);
        onPayloadChange(parsed);
      } else {
        setError('Payload must be a JSON object');
      }
    } catch (e) {
      setError(`Invalid JSON: ${e instanceof Error ? e.message : 'Parse error'}`);
    }
  };

  const loadDefault = (phase: string) => {
    const defaultJson = DEFAULT_PAYLOADS[phase as keyof typeof DEFAULT_PAYLOADS] || '{}';
    setJsonText(defaultJson);
    
    try {
      const parsed = JSON.parse(defaultJson);
      setError(null);
      onPayloadChange(parsed);
    } catch (e) {
      setError('Error loading default payload');
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">Payload JSON</label>
        
        <select
          onChange={(e) => e.target.value && loadDefault(e.target.value)}
          defaultValue=""
          className="text-xs border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">Load default...</option>
          <option value="P-100">Architect (P-100)</option>
          <option value="P-200">Sequencer (P-200)</option>
          <option value="P-300">Drafter (P-300)</option>
          <option value="P-400">Compiler (P-400)</option>
        </select>
      </div>

      <div className={`relative ${error ? 'border-red-300' : 'border-gray-200'} rounded-lg`}>
        <textarea
          value={jsonText}
          onChange={(e) => handleTextChange(e.target.value)}
          rows={12}
          className="w-full p-3 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
          placeholder='{"project_id": "...", ...}'
        />

        {error && (
          <div className="absolute bottom-2 right-2 px-3 py-1 bg-red-100 text-red-700 rounded text-xs">
            {error}
          </div>
        )}
      </div>

      <p className="text-xs text-gray-500">
        Valid JSON object required. Use the dropdown to load phase-specific templates.
      </p>
    </div>
  );
}
