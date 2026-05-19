import React from 'react';

export interface ViewTab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

export interface ViewTabsProps {
  tabs: ViewTab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}

export function ViewTabs({ tabs, activeTab, onTabChange, className = '' }: ViewTabsProps) {
  return (
    <div
      className={`flex items-center gap-1 border-b border-[var(--border-primary)] px-4 py-2 ${className}`}
      role="tablist"
      aria-label="View tabs"
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-controls={`view-tab-panel-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all duration-150 ${
              isActive
                ? 'bg-[var(--color-primary)] text-white shadow-sm'
                : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            {tab.icon && <span className="flex items-center">{tab.icon}</span>}
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
