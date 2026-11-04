import { AlertTriangle, X } from 'lucide-react';
import { useToastStore } from '../store/toastStore';

export default function Toasts() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);

  return (
    // aria-live: screen readers read out what appears here without moving the focus
    <div aria-live="polite" className="fixed bottom-4 right-4 z-[60] flex flex-col items-end gap-2 max-w-sm">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="alert"
          className="flex items-start gap-2 rounded-2xl border-2 border-[#242426] bg-[#E8BAA8] px-3.5 py-2.5 text-xs font-bold text-[#52291E] shadow-[3px_3px_0px_#242426]"
        >
          <AlertTriangle className="w-4 h-4 shrink-0 mt-px" />
          <span className="flex-1">{toast.text}</span>
          <button
            onClick={() => dismiss(toast.id)}
            aria-label="Закрыть"
            className="shrink-0 opacity-70 hover:opacity-100 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
