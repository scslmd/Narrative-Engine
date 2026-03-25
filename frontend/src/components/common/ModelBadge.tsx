interface ModelBadgeProps {
  model?: string;
}

export default function ModelBadge({ model }: ModelBadgeProps) {
  if (!model) return null;

  const truncated = model.length > 20 ? `${model.slice(0, 17)}...` : model;

  return (
    <span 
      className="inline-flex items-center px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-xs"
      title={model}
    >
      {truncated}
    </span>
  );
}
