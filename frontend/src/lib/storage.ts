const STORAGE_PREFIX = 'narrative-engine';

export function getStorageKey(projectId: string, key: string): string {
  return `${STORAGE_PREFIX}:${projectId}:${key}`;
}

export function setItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
  }
}

export function getItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch (error) {
    console.error('Failed to read from localStorage:', error);
    return null;
  }
}

export function removeItem(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Failed to remove from localStorage:', error);
  }
}

export function clearProjectStorage(projectId: string): void {
  const prefix = `${STORAGE_PREFIX}:${projectId}:`;
  
  Object.keys(localStorage).forEach((key) => {
    if (key.startsWith(prefix)) {
      localStorage.removeItem(key);
    }
  });
}
