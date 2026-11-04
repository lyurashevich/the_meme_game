import { useEffect } from 'react';

/** While `active`, the Esc key calls `onClose`, as in any window. */
export function useCloseOnEscape(active: boolean, onClose: () => void) {
  useEffect(() => {
    if (!active) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [active, onClose]);
}
