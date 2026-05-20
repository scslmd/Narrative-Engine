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

/** Maps panel keys to workflow stages for stage bar awareness. */
export const panelToStage: Record<string, 'planning' | 'writing' | 'review'> = {
  structure: 'planning',
  chapters: 'planning',
  ideas: 'planning',
  canon: 'planning',
  generation: 'planning',
  manuscripts: 'writing',
  drafts: 'writing',
  characters: 'writing',
  relationships: 'writing',
  worldBible: 'writing',
  arcs: 'writing',
  notes: 'writing',
  jobs: 'writing',
  suggestions: 'writing',
  review: 'review',
  inspect: 'review',
}

function studioUrl(projectId: string, params: Record<string, string>): string {
  const search = new URLSearchParams(params).toString();
  return search
    ? `/workspace/${projectId}/studio?${search}`
    : `/workspace/${projectId}/studio`;
}

export const routes = {
  home: '/',
  workspace: (projectId: string) => `/workspace/${projectId}`,
  studio: (projectId: string) => `/workspace/${projectId}/studio`,

  // Canonical routes — navigate directly to studio with query params
  plan: (projectId: string) => studioUrl(projectId, { tab: 'structure' }),
  write: (projectId: string, chapterId?: string) =>
    studioUrl(projectId, { tab: 'manuscripts', ...(chapterId && { chapterId }) }),
  review: (projectId: string) => studioUrl(projectId, { tab: 'review' }),
  inspect: (projectId: string, jobId?: string) =>
    studioUrl(projectId, { tab: 'inspect', ...(jobId && { jobId }) }),
  braindump: (projectId: string) => studioUrl(projectId, { tab: 'ideas' }),
  canon: (projectId: string) => studioUrl(projectId, { tab: 'canon' }),
  generate: (projectId: string) => studioUrl(projectId, { tab: 'generation' }),

  // Direct studio tab helper
  studioTab: (projectId: string, tab: string, extra?: Record<string, string>) =>
    studioUrl(projectId, { tab, ...extra }),
} as const

/** Legacy route URLs — preserved for backward-compat checks and old bookmarks. */
export const routesLegacy = {
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
