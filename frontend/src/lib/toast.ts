import type { Toast, ToastType } from '../types/toast';

const MAX_TOASTS = 3;
const DEFAULT_DURATION = 5000;

let toasts: Toast[] = [];
let listeners: Set<() => void> = new Set();

function notify() {
  listeners.forEach((listener) => listener());
}

export function addToast(type: ToastType, message: string, duration?: number): string {
  const id = Math.random().toString(36).substring(2, 9);
  
  const toast: Toast = {
    id,
    type,
    message,
    duration: duration ?? DEFAULT_DURATION,
  };

  toasts.push(toast);

  if (toasts.length > MAX_TOASTS) {
    toasts = toasts.slice(-MAX_TOASTS);
  }

  notify();

  if (toast.duration > 0) {
    setTimeout(() => removeToast(id), toast.duration);
  }

  return id;
}

export function removeToast(id: string): void {
  toasts = toasts.filter((t) => t.id !== id);
  notify();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export const toast = {
  success: (message: string, duration?: number) => addToast('success', message, duration),
  error: (message: string, duration?: number) => addToast('error', message, duration),
  warning: (message: string, duration?: number) => addToast('warning', message, duration),
  info: (message: string, duration?: number) => addToast('info', message, duration),
  remove: removeToast,
  subscribe,
};
