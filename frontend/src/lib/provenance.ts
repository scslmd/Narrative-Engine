import type { Provenance } from '../types/provenance';

export function formatProvenance(provenance: Provenance): string {
  const parts = [];

  if (provenance.provider) {
    parts.push(provenance.provider);
  }

  if (provenance.model) {
    parts.push(provenance.model);
  }

  if (provenance.backendName) {
    parts.push(provenance.backendName);
  }

  if (provenance.backendVersion) {
    parts.push(`v${provenance.backendVersion}`);
  }

  return parts.join(' • ');
}

export function getProviderIcon(provider?: string): string {
  const icons: Record<string, string> = {
    openai: 'O',
    anthropic: 'A',
    local: '⚡',
    cohere: 'C',
    google: 'G',
  };

  if (!provider) return '?';
  return icons[provider.toLowerCase()] || '?';
}
