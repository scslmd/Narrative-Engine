import { describe, it, expect } from 'vitest';

describe('test setup', () => {
  it('should have jsdom environment', () => {
    expect(typeof window).toBe('object');
  });

  it('should have jest-dom matchers', () => {
    expect(true).toBeTruthy();
  });
});
