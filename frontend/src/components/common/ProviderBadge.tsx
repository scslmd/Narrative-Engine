interface ProviderBadgeProps {
  provider?: string;
}

const PROVIDER_ICONS: Record<string, string> = {
  openai: 'O',
  anthropic: 'A',
  local: '⚡',
  cohere: 'C',
  google: 'G',
};

export default function ProviderBadge({ provider }: ProviderBadgeProps) {
  if (!provider) return null;

  const normalized = provider.toLowerCase();
  const icon = PROVIDER_ICONS[normalized] || '?';

  return (
    <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-gray-200 text-gray-700 text-xs font-bold">
      {icon}
    </span>
  );
}
