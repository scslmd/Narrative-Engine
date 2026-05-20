import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getCanonProfiles, getCanonAnnotations } from '../../services/canonCustomization';
import type { CanonAnnotation, CanonCustomizationProfile } from '../../types/canonCustomization';
import { WorkspaceStatus } from '../planning/ui';

interface StudioCanonPanelProps {
  projectId: string;
}

type CanonTab = 'profiles' | 'annotations';

const ANNOTATION_KIND_COLORS: Record<string, string> = {
  locked: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  soft_guidance: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  mutable: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  forbidden_contradiction: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  generation_note: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
};

function ProfileRow({ profile }: { profile: CanonCustomizationProfile }) {
  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-3 space-y-1">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-[var(--text-primary)]">
          {profile.name || profile.profile_id}
        </h4>
      </div>
      {profile.description && (
        <p className="text-[10px] text-[var(--text-tertiary)] line-clamp-2">
          {profile.description}
        </p>
      )}
    </div>
  );
}

function AnnotationRow({ annotation }: { annotation: CanonAnnotation }) {
  const kindColor = ANNOTATION_KIND_COLORS[annotation.annotation_kind] || 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';

  return (
    <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] p-3 space-y-1">
      <div className="flex items-center gap-2">
        <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium ${kindColor}`}>
          {annotation.annotation_kind}
        </span>
        <span className="text-[10px] text-[var(--text-tertiary)]">
          {annotation.target_kind}: {annotation.target_id}
        </span>
      </div>
      {annotation.field_path && (
        <p className="text-[10px] font-mono text-[var(--text-secondary)]">
          {annotation.field_path}
        </p>
      )}
      {annotation.note && (
        <p className="text-[10px] text-[var(--text-secondary)] line-clamp-2">
          {annotation.note}
        </p>
      )}
    </div>
  );
}

export function StudioCanonPanel({ projectId }: StudioCanonPanelProps) {
  const [activeTab, setActiveTab] = useState<CanonTab>('profiles');

  const profilesQuery = useQuery({
    queryKey: ['studio', 'canon', 'profiles', projectId],
    queryFn: () => getCanonProfiles(projectId),
    enabled: Boolean(projectId),
  });

  const annotationsQuery = useQuery({
    queryKey: ['studio', 'canon', 'annotations', projectId],
    queryFn: () => getCanonAnnotations(projectId),
    enabled: Boolean(projectId),
  });

  const profiles = useMemo(
    () => (profilesQuery.data as CanonCustomizationProfile[] | undefined) ?? [],
    [profilesQuery.data],
  );

  const annotations = useMemo(
    () => (annotationsQuery.data as CanonAnnotation[] | undefined) ?? [],
    [annotationsQuery.data],
  );

  const isLoading = profilesQuery.isLoading || annotationsQuery.isLoading;
  const error = profilesQuery.error || annotationsQuery.error;

  if (isLoading) {
    return <WorkspaceStatus title="Loading canon" detail="Fetching canon data..." />;
  }

  if (error) {
    return (
      <WorkspaceStatus
        title="Could not load canon"
        detail="Canon data is unavailable."
        tone="error"
      />
    );
  }

  return (
    <div data-canon-panel className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Canon</h3>
        <div className="flex gap-1">
          {(['profiles', 'annotations'] as CanonTab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-md px-2 py-0.5 text-[10px] font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] ring-1 ring-[var(--border-primary)]'
                  : 'text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
              }`}
            >
              {tab === 'profiles' ? `${profiles.length}` : `${annotations.length}`}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'profiles' ? (
        profiles.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-[var(--text-tertiary)]">No canon profiles.</p>
            <p className="mt-1 text-xs text-[var(--text-tertiary)]">
              Create profiles to manage canon scope.
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {profiles.map((profile) => (
              <ProfileRow key={profile.profile_id} profile={profile} />
            ))}
          </div>
        )
      ) : annotations.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">No annotations.</p>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">
            Annotations appear when you flag canon fields.
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {annotations.map((annotation) => (
            <AnnotationRow key={annotation.annotation_id} annotation={annotation} />
          ))}
        </div>
      )}
    </div>
  );
}
