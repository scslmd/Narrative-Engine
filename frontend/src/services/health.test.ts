import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { checkHealth } from './health';

describe('checkHealth', () => {
  it('returns parsed health status with llama.cpp backend', async () => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.json({
          components: { inference: { backend: 'llama.cpp' } },
        });
      }),
    );

    const result = await checkHealth();

    expect(result).toEqual({
      isReady: true,
      isLlmAvailable: true,
      backendType: 'llama.cpp',
      issues: [],
    });
  });

  it('detects stub backend as unavailable', async () => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.json({
          components: { inference: { backend: 'stub' } },
        });
      }),
    );

    const result = await checkHealth();

    expect(result).toEqual({
      isReady: true,
      isLlmAvailable: false,
      backendType: 'stub',
      issues: [],
    });
  });

  it('returns degraded status on server error (500)', async () => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
      }),
    );

    const result = await checkHealth();

    expect(result).toEqual({
      isReady: false,
      isLlmAvailable: false,
      backendType: 'unknown',
      issues: [],
    });
  });

  it('returns degraded status on network error', async () => {
    server.use(
      http.get('/health/ready', () => {
        return HttpResponse.error();
      }),
    );

    const result = await checkHealth();

    expect(result).toEqual({
      isReady: false,
      isLlmAvailable: false,
      backendType: 'unknown',
      issues: [],
    });
  });
});
