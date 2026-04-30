import { http, HttpResponse } from 'msw';

export const handlers = [
  // Default handlers - tests can override with server.use()
  http.get('/health/ready', () => {
    return HttpResponse.json({ components: { inference: { backend: 'llama.cpp' } } });
  }),
];
