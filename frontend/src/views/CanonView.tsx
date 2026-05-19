import { useParams, useSearchParams } from 'react-router-dom';
import { CanonWorkshop } from '../components/canon/CanonWorkshop';
import { ViewShell } from '../components/shell/ViewShell';
import { useCanonController } from '../domains/canon/useCanonController';

export function CanonView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams] = useSearchParams();

  const tabParam = searchParams.get('tab');
  const initialTab =
    tabParam === 'mythos' || tabParam === 'patterns' || tabParam === 'packet'
      ? tabParam
      : 'overview';

  const controller = useCanonController(projectId || '');

  if (!projectId) {
    return <div className="text-sm text-slate-500">No project selected.</div>;
  }

  if (controller.isLoading) {
    return (
      <ViewShell title="Canon" subtitle={projectId}>
        <div className="flex items-center justify-center h-full">
          <p className="text-sm text-[var(--text-secondary)]">Loading canon workspace...</p>
        </div>
      </ViewShell>
    );
  }

  if (controller.isError) {
    if (controller.isAuthError) {
      return (
        <ViewShell title="Canon" subtitle={projectId}>
          <div className="flex items-center justify-center h-full">
            <div className="rounded-lg border border-[var(--color-warning-border)] bg-[var(--color-warning-subtle)] p-4 space-y-2 max-w-md text-center">
              <p className="text-sm font-medium text-[var(--color-warning)]">API key required</p>
              <p className="text-sm text-[var(--text-secondary)]">
                The Canon Workshop requires API authentication. Create an API key in{' '}
                <button className="font-semibold text-[var(--color-warning)] underline hover:no-underline cursor-pointer">Settings &gt; API Keys</button>, then set the <code className="px-1 py-0.5 bg-[var(--bg-tertiary)] rounded text-xs">NARRATIVE_API_KEY</code> environment variable on your server to enable these features.
              </p>
              <p className="text-xs text-[var(--text-tertiary)]">See <strong>User Guide §Authentication</strong> for setup instructions.</p>
            </div>
          </div>
        </ViewShell>
      );
    }

    return (
      <ViewShell title="Canon" subtitle={projectId}>
        <div className="flex items-center justify-center h-full">
          <p className="text-sm text-[var(--color-danger)]">Failed to load canon workspace data.</p>
        </div>
      </ViewShell>
    );
  }

  return (
    <ViewShell title="Canon" subtitle={projectId}>
      <CanonWorkshop projectId={projectId} initialTab={initialTab} controller={controller} />
    </ViewShell>
  );
}
