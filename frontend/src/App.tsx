import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastProvider } from './hooks/useToast'
import { ToastContainer } from './components/ui/Toast'
import { Layout } from './components/Layout'
import { ProjectList } from './views/ProjectList'
import { Workspace } from './views/Workspace'
import { PlanningView } from './views/PlanningView'
import { WritingView } from './views/WritingView'
import { ReviewView } from './views/ReviewView'
import { InspectView } from './views/InspectView'
import { BrainDumpView } from './views/BrainDumpView'
import { GenerationView } from './views/GenerationView'
import { CanonView } from './views/CanonView'
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
            <Route path="plan" element={<PlanningView />} />
            <Route path="write" element={<WritingView />} />
            <Route path="write/:chapterId" element={<WritingView />} />
            <Route path="review" element={<ReviewView />} />
            <Route path="inspect" element={<InspectView />} />
            <Route path="inspect/:jobId" element={<InspectView />} />
            <Route path="braindump" element={<BrainDumpView />} />
            <Route path="canon" element={<CanonView />} />
            <Route path="generate" element={<GenerationView />} />
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
