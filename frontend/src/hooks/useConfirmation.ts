import { useCallback, useState } from 'react';

export interface ConfirmOptions {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

export interface ConfirmationResult {
  confirm: (message: string, options?: ConfirmOptions) => Promise<boolean>;
  isOpen: boolean;
  message: string;
  options: ConfirmOptions;
  onConfirm: () => void;
  onCancel: () => void;
}

const defaultOptions: ConfirmOptions = {
  title: 'Confirm',
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  danger: false,
};

export function useConfirmation(): ConfirmationResult {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [options, setOptions] = useState<ConfirmOptions>(defaultOptions);
  const [resolvePromise, setResolvePromise] = useState<{
    resolve: (value: boolean) => void;
  } | null>(null);

  const confirm = useCallback(
    (message: string, options?: ConfirmOptions): Promise<boolean> => {
      setMessage(message);
      setOptions({ ...defaultOptions, ...options });
      setIsOpen(true);

      return new Promise<boolean>((resolve) => {
        setResolvePromise({ resolve });
      });
    },
    [],
  );

  const onConfirm = useCallback(() => {
    setIsOpen(false);
    resolvePromise?.resolve(true);
    setResolvePromise(null);
  }, [resolvePromise]);

  const onCancel = useCallback(() => {
    setIsOpen(false);
    resolvePromise?.resolve(false);
    setResolvePromise(null);
  }, [resolvePromise]);

  return { confirm, isOpen, message, options, onConfirm, onCancel };
}
