import { useParams, useSearchParams } from 'react-router-dom';
import { CanonWorkshop } from '../components/canon/CanonWorkshop';
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
    return <div className="text-sm text-slate-500">Loading canon workspace...</div>;
  }

  if (controller.isError) {
    if (controller.isAuthError) {
      return (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-2">
          <p className="text-sm font-medium text-amber-900">API key required</p>
          <p className="text-sm text-amber-800">
            The Canon Workshop requires API authentication. Create an API key in{' '}
            <button className="font-semibold text-amber-900 underline hover:no-underline cursor-pointer">Settings &gt; API Keys</button>, then set the <code className="px-1 py-0.5 bg-amber-100 rounded text-xs">NARRATIVE_API_KEY</code> environment variable on your server to enable these features.
          </p>
          <p className="text-xs text-amber-700">See <strong>User Guide §Authentication</strong> for setup instructions.</p>
        </div>
      );
    }

    return <div className="text-sm text-red-600">Failed to load canon workspace data.</div>;
  }

  return <CanonWorkshop projectId={projectId} initialTab={initialTab} controller={controller} />;
}
