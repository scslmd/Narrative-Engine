import { useUIStore } from '../../stores/uiStore';
import InspectTabs from './InspectTabs';

export default function InspectMode() {
  const { inspectContext, setMode, setInspectContext } = useUIStore();

  const handleBackToManuscript = () => {
    setMode('write');
    setInspectContext(null);
  };

  if (!inspectContext) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-gray-500">Select a job to inspect</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <header className="border-b px-4 py-3 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Inspect Job</h2>
            <p className="text-sm text-gray-500">Job ID: {inspectContext.jobId}</p>
          </div>

          <button
            onClick={handleBackToManuscript}
            className="px-4 py-2 bg-white border rounded hover:bg-gray-50 text-sm"
          >
            Back to Manuscript
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        <InspectTabs context={inspectContext} />
      </main>
    </div>
  );
}
