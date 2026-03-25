import { useEffect, useState } from 'react';
import { toast } from '../../lib/toast';
import type { Toast as ToastType } from '../../types/toast';
import Toast from './Toast';

export default function ToastContainer() {
  const [toastsList, setToastsList] = useState<ToastType[]>([]);

  useEffect(() => {
    return toast.subscribe(() => {
      setToastsList((prev) => [...prev]);
    });
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setToastsList((prev) => prev.filter((t) => {
        const now = Date.now();
        const createdAt = parseInt(t.id, 36) || now;
        return now - createdAt < t.duration;
      }));
    }, 100);

    return () => clearInterval(interval);
  }, []);

  if (toastsList.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toastsList.map((toastItem) => (
        <Toast key={toastItem.id} toast={toastItem} />
      ))}
    </div>
  );
}
