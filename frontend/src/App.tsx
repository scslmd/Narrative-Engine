import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ProjectList } from './views/ProjectList'
import { Workspace } from './views/Workspace'
import { PlanningView, WritingView, ReviewView, InspectView } from './views/PlanningView'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
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
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
