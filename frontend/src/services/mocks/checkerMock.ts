import type { ModelCatalog, RoleModelCheckStatus } from '../../types/checker';

export function getMockModelCatalog(): Promise<ModelCatalog> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        workflow_order: ['architect', 'sequencer', 'drafter', 'compiler'],
        discovered_models: [
          { role: 'architect', model_id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
          { role: 'architect', model_id: 'claude-3-opus', name: 'Claude 3 Opus' },
          { role: 'sequencer', model_id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
          { role: 'sequencer', model_id: 'llama-3-70b', name: 'Llama 3 70B' },
          { role: 'drafter', model_id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
          { role: 'drafter', model_id: 'claude-3-opus', name: 'Claude 3 Opus' },
          { role: 'compiler', model_id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
        ],
      });
    }, 500);
  });
}

export function runMockChecker(_projectId: string, _models: Record<string, string>): Promise<RoleModelCheckStatus> { // eslint-disable-line @typescript-eslint/no-unused-vars
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        run_id: `mock-run-${Date.now()}`,
        status: 'QUEUED',
        attempt_number: 1,
      });
    }, 500);
  });
}

export function getMockCheckerStatus(runId: string): Promise<RoleModelCheckStatus> {
  return new Promise((resolve) => {
    setTimeout(() => {
      const statuses: RoleModelCheckStatus['status'][] = ['QUEUED', 'RUNNING', 'COMPLETED'];
      const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];

      resolve({
        run_id: runId,
        status: randomStatus,
        attempt_number: 1,
        progress_current: randomStatus === 'RUNNING' ? Math.floor(Math.random() * 100) : undefined,
        progress_total: randomStatus === 'RUNNING' ? 100 : undefined,
      });
    }, 300);
  });
}

export function retryMockChecker(runId: string): Promise<RoleModelCheckStatus> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        run_id: runId,
        status: 'QUEUED',
        attempt_number: 2,
      });
    }, 500);
  });
}
