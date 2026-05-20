import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate, useParams, useLocation } from 'react-router-dom'
import { ToastProvider } from './hooks/useToast'
import { ToastContainer } from './components/ui/Toast'
import { Layout } from './components/Layout'
import { ProjectList } from './views/ProjectList'
import { Workspace } from './views/Workspace'
import { GuidedSetupView } from './views/GuidedSetupView'
import { StudioView } from './views/StudioView'
import { useHealthCheck } from './hooks/useHealthCheck'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

// --- Redirect components for backward compatibility ---

function PlanRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=structure`} replace />;
}

function ReviewRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=review`} replace />;
}

function InspectRedirect() {
  const { projectId, jobId } = useParams();
  const params = new URLSearchParams({ tab: 'inspect' });
  if (jobId) params.set('jobId', jobId);
  return <Navigate to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

function BrainDumpRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=ideas`} replace />;
}

function CanonRedirect() {
  const { projectId } = useParams();
  const { search } = useLocation();
  const params = new URLSearchParams(search);
  // Only extract known canon subtabs; drop unknown params to avoid leaking noise
  const knownSubtabs = ['mythos', 'patterns', 'packet'];
  const canonTab = params.get('tab');
  const newParams = new URLSearchParams({ tab: 'canon' });
  if (canonTab && knownSubtabs.includes(canonTab)) newParams.set('subtab', canonTab);
  return <Navigate to={`/workspace/${projectId}/studio?${newParams.toString()}`} replace />;
}

function GenerateRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/workspace/${projectId}/studio?tab=generation`} replace />;
}

function WriteRedirect() {
  const { projectId, chapterId } = useParams();
  const params = new URLSearchParams({ tab: 'manuscripts' });
  if (chapterId) params.set('chapterId', chapterId);
  return <Navigate to={`/workspace/${projectId}/studio?${params.toString()}`} replace />;
}

function AppInner() {
  useHealthCheck();
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/setup-wizard" element={<GuidedSetupView />} />
          <Route path="/workspace/:projectId" element={<Workspace />}>
            <Route index element={<Navigate to="studio" replace />} />
            <Route path="studio" element={<StudioView />} />
            {/* Backward-compatible redirects — old routes still work for bookmarks */}
            <Route path="plan" element={<PlanRedirect />} />
            <Route path="write" element={<WriteRedirect />} />
            <Route path="write/:chapterId" element={<WriteRedirect />} />
            <Route path="review" element={<ReviewRedirect />} />
            <Route path="inspect" element={<InspectRedirect />} />
            <Route path="inspect/:jobId" element={<InspectRedirect />} />
            <Route path="braindump" element={<BrainDumpRedirect />} />
            <Route path="canon" element={<CanonRedirect />} />
            <Route path="generate" element={<GenerateRedirect />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
      <ToastContainer />
    </BrowserRouter>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AppInner />
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App
