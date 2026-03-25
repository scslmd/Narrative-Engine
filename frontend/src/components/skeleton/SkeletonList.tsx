import { clsx } from 'clsx';
import SkeletonCard from './SkeletonCard';

interface SkeletonListProps {
  count?: number;
  className?: string;
}

export default function SkeletonList({ count = 5, className }: SkeletonListProps) {
  return (
    <div className={clsx('space-y-3', className)}>
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonCard key={index} />
      ))}
    </div>
  );
}
