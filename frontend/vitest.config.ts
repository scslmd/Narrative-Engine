import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    globals: false,
    environment: 'jsdom',
    setupFiles: ['src/__tests__/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    exclude: ['src/**/*.d.ts'],
    testTimeout: 10000,
    hookTimeout: 5000,
  },
});
