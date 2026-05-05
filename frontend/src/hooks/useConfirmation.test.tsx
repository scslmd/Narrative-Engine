import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useConfirmation } from './useConfirmation';

describe('useConfirmation', () => {
  it('returns confirm function and isOpen state (initially false)', () => {
    const { result } = renderHook(() => useConfirmation());

    expect(result.current.confirm).toBeDefined();
    expect(typeof result.current.confirm).toBe('function');
    expect(result.current.isOpen).toBe(false);
    expect(result.current.message).toBe('');
    expect(result.current.options.title).toBe('Confirm');
    expect(result.current.options.confirmLabel).toBe('Confirm');
    expect(result.current.options.cancelLabel).toBe('Cancel');
    expect(result.current.options.danger).toBe(false);
  });

  it('resolves true when confirmed', () => {
    const { result } = renderHook(() => useConfirmation());

    let confirmPromise: Promise<boolean> | undefined;

    act(() => {
      confirmPromise = result.current.confirm('Are you sure?');
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.message).toBe('Are you sure?');

    act(() => {
      result.current.onConfirm();
    });

    expect(result.current.isOpen).toBe(false);

    expect(confirmPromise).resolves.toBe(true);
  });
});
