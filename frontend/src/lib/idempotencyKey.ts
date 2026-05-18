const STORAGE_PREFIX = 'idem:';
const DEFAULT_TTL_MS = 30_000;

/**
 * Generate or retrieve a scoped idempotency key with TTL.
 * Within the TTL window, the same key is returned for the same scope.
 * After TTL expires, a fresh key is generated.
 *
 * @param scope - Unique scope string (e.g., "job:P-100:project-abc")
 * @param ttlMs - Time-to-live in milliseconds (default 30s)
 * @returns Idempotency key string
 */
export function idempotencyKey(scope: string, ttlMs: number = DEFAULT_TTL_MS): string {
  const storageKey = `${STORAGE_PREFIX}${scope}`;

  try {
    const stored = sessionStorage.getItem(storageKey);
    if (stored) {
      const [key, timestamp] = stored.split(':');
      if (Date.now() - Number(timestamp) < ttlMs) {
        return key;
      }
    }
  } catch {
    // sessionStorage unavailable (e.g., test environment) - fall through
  }

  const newKey = `${scope}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  try {
    sessionStorage.setItem(storageKey, `${newKey}:${Date.now()}`);
  } catch {
    // sessionStorage unavailable - return key without persistence
  }

  return newKey;
}
