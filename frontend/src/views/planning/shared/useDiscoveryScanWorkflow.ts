import { useState } from 'react';

export function useDiscoveryScanWorkflow() {
  const [showScanDialog, setShowScanDialog] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  return { showScanDialog, setShowScanDialog, activeJobId, setActiveJobId };
}
