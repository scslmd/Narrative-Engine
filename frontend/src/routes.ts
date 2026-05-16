export type WorkspaceMode = 'studio' | 'plan' | 'write' | 'review' | 'inspect' | 'braindump' | 'generate' | 'canon'

export interface RouteState {
  mode: WorkspaceMode
  projectId: string | null
  chapterId: string | null
}

export const modeToStage: Record<WorkspaceMode, 'planning' | 'writing' | 'review'> = {
  studio: 'writing',
  braindump: 'planning',
  plan: 'planning',
  canon: 'planning',
  generate: 'planning',
  write: 'writing',
  review: 'review',
  inspect: 'review',
}

export const routes = {
  home: '/',
  workspace: (projectId: string) => `/workspace/${projectId}`,
  studio: (projectId: string) => `/workspace/${projectId}/studio`,
  plan: (projectId: string) => `/workspace/${projectId}/plan`,
  write: (projectId: string, chapterId?: string) => 
    chapterId ? `/workspace/${projectId}/write/${chapterId}` : `/workspace/${projectId}/write`,
  review: (projectId: string) => `/workspace/${projectId}/review`,
  inspect: (projectId: string, jobId?: string) => 
    jobId ? `/workspace/${projectId}/inspect/${jobId}` : `/workspace/${projectId}/inspect`,
  braindump: (projectId: string) => `/workspace/${projectId}/braindump`,
  canon: (projectId: string) => `/workspace/${projectId}/canon`,
  generate: (projectId: string) => `/workspace/${projectId}/generate`,
} as const
