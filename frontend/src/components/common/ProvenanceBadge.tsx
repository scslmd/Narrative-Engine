import { type Provenance } from '../../types/provenance';
import ProviderBadge from './ProviderBadge';
import ModelBadge from './ModelBadge';

interface ProvenanceBadgeProps {
  provenance: Provenance;
  compact?: boolean;
}

export default function ProvenanceBadge({ provenance, compact = false }: ProvenanceBadgeProps) {
  const { provider, model, backendName, backendVersion } = provenance;

  if (compact) {
    return (
      <div className="inline-flex items-center gap-1">
        <ProviderBadge provider={provider} />
        {model && <ModelBadge model={model} />}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 p-2 bg-gray-50 rounded border text-xs">
      <div className="flex items-center gap-2">
        <ProviderBadge provider={provider} />
        {model && <ModelBadge model={model} />}
      </div>

      {(backendName || backendVersion) && (
        <div className="text-gray-500">
          {backendName && <span>{backendName}</span>}
          {backendName && backendVersion && <span> • </span>}
          {backendVersion && <span>v{backendVersion}</span>}
        </div>
      )}
    </div>
  );
}
