import { useEffect } from 'react';

interface ConfirmDialogProps {
  title: string;
  text: string;
  confirmLabel: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

// "Are you sure?" for things that can't be undone. Shown only while it's in the page.
export default function ConfirmDialog({
  title,
  text,
  confirmLabel,
  cancelLabel = 'Отмена',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  // Esc means "no". The listener is on the whole page, so it is removed when the dialog goes away.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onCancel]);

  return (
    // A click on the dark backdrop cancels; clicks inside the window don't reach it (stopPropagation)
    <div
      className="fixed inset-0 z-50 bg-[#242426]/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onCancel}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-text"
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-sm bg-[#FAF7F2] border-2 border-[#242426] rounded-3xl p-6 shadow-[6px_6px_0px_#242426]"
      >
        <h3 id="confirm-title" className="text-lg font-black text-[#242426] mb-1">
          {title}
        </h3>
        <p id="confirm-text" className="text-sm text-[#55524B] mb-5">
          {text}
        </p>

        <div className="flex items-center gap-3">
          {/* The safe choice gets the focus, so a stray Enter doesn't do the irreversible thing */}
          <button
            type="button"
            autoFocus
            onClick={onCancel}
            className="flex-1 py-2.5 rounded-xl border-2 border-[#242426] bg-[#ECE8DE] font-bold text-xs text-[#44413A] hover:bg-[#E2DDD2] cursor-pointer"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="flex-1 py-2.5 rounded-xl border-2 border-[#242426] bg-[#E8BAA8] font-black text-xs text-[#52291E] shadow-[2px_2px_0px_#242426] hover:bg-[#E0A792] cursor-pointer"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
