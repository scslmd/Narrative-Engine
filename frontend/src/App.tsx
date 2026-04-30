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
import { useHealthCheck } from './hooks/useHealthCheck'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

function App() {
  useHealthCheck();

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<ProjectList />} />
              <Route path="/workspace/:projectId" element={<Workspace />}>
                <Route index element={<Navigate to="plan" replace />} />
                <Route path="plan" element={<PlanningView />} />
                <Route path="write" element={<WritingView />} />
                <Route path="write/:chapterId" element={<WritingView />} />
                <Route path="review" element={<ReviewView />} />
                <Route path="inspect" element={<InspectView />} />
                <Route path="inspect/:jobId" element={<InspectView />} />
                <Route path="braindump" element={<BrainDumpView />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
          <ToastContainer />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  )
}

export default App
