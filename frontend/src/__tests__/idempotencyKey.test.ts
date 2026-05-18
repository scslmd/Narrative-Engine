import { describe, it, expect, beforeEach, vi } from 'vitest';
import { idempotencyKey } from '../lib/idempotencyKey';

describe('idempotencyKey', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('returns same key within TTL for same scope', () => {
    const key1 = idempotencyKey('test-scope');
    const key2 = idempotencyKey('test-scope');
    expect(key1).toBe(key2);
  });

  it('returns different key for different scopes', () => {
    const key1 = idempotencyKey('scope-a');
    const key2 = idempotencyKey('scope-b');
    expect(key1).not.toBe(key2);
  });

  it('returns new key after TTL expires', () => {
    vi.useFakeTimers();
    const key1 = idempotencyKey('ttl-scope');
    vi.advanceTimersByTime(31_000);
    const key2 = idempotencyKey('ttl-scope');
    expect(key2).not.toBe(key1);
    vi.useRealTimers();
  });

  it('includes scope prefix in key', () => {
    const key = idempotencyKey('my-scope');
    expect(key.startsWith('my-scope-')).toBe(true);
  });

  it('handles missing sessionStorage gracefully', () => {
    const orig = globalThis.sessionStorage;
    // @ts-expect-error - simulating unavailable sessionStorage
    delete globalThis.sessionStorage;
    expect(() => idempotencyKey('graceful')).not.toThrow();
    globalThis.sessionStorage = orig;
  });
});
