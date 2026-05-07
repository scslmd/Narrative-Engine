import { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info, TriangleAlert } from 'lucide-react';
import { useToastStore, type ToastType } from '../../stores/toastStore';

const VARIANT_STYLES: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const VARIANT_ICON: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle className="w-5 h-5 text-green-500" />,
  error: <AlertCircle className="w-5 h-5 text-red-500" />,
  warning: <TriangleAlert className="w-5 h-5 text-yellow-500" />,
  info: <Info className="w-5 h-5 text-blue-500" />,
};

export function ToastContainer(): React.ReactElement {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) {
    return <></>;
  }

  return (
    <div className="fixed top-4 right-4 z-[300] flex flex-col gap-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={removeToast} />
      ))}
    </div>
  );
}

interface ToastProps {
  toast: { id: string; message: string; type: ToastType };
  onDismiss: (id: string) => void;
}

function Toast({ toast, onDismiss }: ToastProps): React.ReactElement {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onDismiss(toast.id), 300);
    }, 5000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 border rounded-lg shadow-lg transition-opacity duration-300 ${
        visible ? 'opacity-100' : 'opacity-0'
      } ${VARIANT_STYLES[toast.type]}`}
    >
      {VARIANT_ICON[toast.type]}
      <span className="text-sm flex-1">{toast.message}</span>
      <button
        onClick={() => onDismiss(toast.id)}
        className="opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
