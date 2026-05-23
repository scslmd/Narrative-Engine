import { useState } from 'react';

export function usePlanningTabNavigation<T extends string>(defaultTab: T) {
  const [activeTab, setActiveTab] = useState<T>(defaultTab);
  return { activeTab, setActiveTab };
}
