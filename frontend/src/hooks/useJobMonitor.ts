import { useJobStatus } from './useJobStatus';
import { useJobStore } from '../stores/jobStore';

export function useJobMonitor() {
  const { activeJobId, isVisible, hide } = useJobStore();
  const statusData = useJobStatus(activeJobId);

  return {
    jobId: activeJobId,
    isVisible,
    ...statusData,
    onDismiss: hide,
  };
}
