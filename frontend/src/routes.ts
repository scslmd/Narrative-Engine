export type WorkspaceMode = 'plan' | 'write' | 'review' | 'inspect'

export interface RouteState {
  mode: WorkspaceMode
  projectId: string | null
  chapterId: string | null
}

export const routes = {
  home: '/',
  workspace: (projectId: string) => `/workspace/${projectId}`,
  plan: (projectId: string) => `/workspace/${projectId}/plan`,
  write: (projectId: string, chapterId?: string) => 
    chapterId ? `/workspace/${projectId}/write/${chapterId}` : `/workspace/${projectId}/write`,
  review: (projectId: string) => `/workspace/${projectId}/review`,
  inspect: (projectId: string, jobId?: string) => 
    jobId ? `/workspace/${projectId}/inspect/${jobId}` : `/workspace/${projectId}/inspect`,
} as const