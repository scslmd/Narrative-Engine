import { clsx } from 'clsx';

interface SkeletonTextProps {
  lines?: number;
  width?: string | number;
  height?: string | number;
  className?: string;
}

export default function SkeletonText({
  lines = 1,
  width = 'full',
  height = 4,
  className,
}: SkeletonTextProps) {
  return (
    <div className={clsx('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="animate-pulse bg-gray-200 rounded"
          style={{
            width: typeof width === 'string' ? width : `${width}%`,
            height: typeof height === 'string' ? height : `${height}px`,
          }}
        />
      ))}
    </div>
  );
}
