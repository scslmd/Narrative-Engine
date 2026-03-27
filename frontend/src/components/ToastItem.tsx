import { useEffect } from 'react';
import { useToastStore, ToastType } from '../stores/toastStore';

interface Props {
  id: string;
  message: string;
  type: ToastType;
}

export function ToastItem({ id, message, type }: Props): React.ReactElement {
  const removeToast = useToastStore((state) => state.removeToast);

  useEffect(() => {
    const timer = setTimeout(() => {
      removeToast(id);
    }, 5000);

    return () => clearTimeout(timer);
  }, [id, removeToast]);

  const getIcon = (): string => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      default:
        return 'ℹ';
    }
  };

  const getBgClass = (): string => {
    switch (type) {
      case 'success':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'warning':
        return 'bg-yellow-500';
      default:
        return 'bg-blue-500';
    }
  };

  const handleClose = (e: React.MouseEvent): void => {
    e.stopPropagation();
    removeToast(id);
  };

  return (
    <div
      className={`${getBgClass()} text-white px-4 py-3 rounded-lg shadow-lg flex items-start gap-3 min-w-[300px] max-w-md animate-slide-in`}
      role="alert"
    >
      <span className="text-xl">{getIcon()}</span>
      <p className="flex-1 text-sm">{message}</p>
      <button
        onClick={handleClose}
        className="hover:bg-white/20 rounded p-1 transition-colors"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
}
