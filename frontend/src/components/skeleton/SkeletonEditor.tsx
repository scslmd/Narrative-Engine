import { clsx } from 'clsx';
import SkeletonText from './SkeletonText';

interface SkeletonEditorProps {
  className?: string;
}

export default function SkeletonEditor({ className }: SkeletonEditorProps) {
  return (
    <div className={clsx('bg-white rounded-lg shadow overflow-hidden', className)}>
      <div className="border-b px-4 py-2 flex gap-2">
        <SkeletonText lines={1} width={40} height={3} />
        <SkeletonText lines={1} width={40} height={3} />
        <SkeletonText lines={1} width={40} height={3} />
      </div>

      <div className="p-4 space-y-2">
        <SkeletonText lines={8} height={4} />
      </div>
    </div>
  );
}
