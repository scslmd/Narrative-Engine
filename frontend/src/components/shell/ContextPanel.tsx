import React from 'react';

export interface ContextPanelTab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
}

export interface ContextPanelProps {
  tabs: ContextPanelTab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  title?: string;
}

export function ContextPanel({ tabs, activeTab, onTabChange, title }: ContextPanelProps) {
  const activeContent = tabs.find((t) => t.id === activeTab)?.content;
  const activeLabel = tabs.find((t) => t.id === activeTab)?.label;

  return (
    <div className="flex h-full flex-col">
      <div
        className="flex items-center gap-1 overflow-x-auto border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] px-2 py-2"
        role="tablist"
        aria-label="Context panel tabs"
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => onTabChange(tab.id)}
              className={`relative rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm ring-1 ring-[var(--border-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'
              }`}
            >
              {tab.icon && <span className="mr-1">{tab.icon}</span>}
              {tab.label}
            </button>
          );
        })}
      </div>
      {title || activeLabel ? (
        <div className="border-b border-[var(--border-primary)] px-4 py-3">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            {title ?? activeLabel}
          </h2>
        </div>
      ) : null}
      <div className="flex-1 overflow-y-auto p-4" id={`context-panel-${activeTab}`}>
        {activeContent}
      </div>
    </div>
  );
}
