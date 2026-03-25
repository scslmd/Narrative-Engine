import { clsx } from 'clsx';
import SkeletonText from './SkeletonText';

interface SkeletonCardProps {
  withHeader?: boolean;
  withFooter?: boolean;
  className?: string;
}

export default function SkeletonCard({
  withHeader = true,
  withFooter = false,
  className,
}: SkeletonCardProps) {
  return (
    <div className={clsx('bg-white rounded-lg shadow p-4 space-y-3', className)}>
      {withHeader && (
        <SkeletonText lines={1} width="60%" height={5} />
      )}

      <SkeletonText lines={3} height={4} />

      {withFooter && (
        <div className="flex gap-2 pt-2">
          <SkeletonText lines={1} width={30} height={3} />
          <SkeletonText lines={1} width={30} height={3} />
        </div>
      )}
    </div>
  );
}
