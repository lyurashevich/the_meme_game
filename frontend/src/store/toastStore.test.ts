import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { showToast, useToastStore } from './toastStore';

const texts = () => useToastStore.getState().toasts.map((toast) => toast.text);

beforeEach(() => {
  vi.useFakeTimers();
  useToastStore.setState({ toasts: [] });
});

afterEach(() => {
  vi.useRealTimers();
});

describe('toasts', () => {
  it('go away on their own after 5 s', () => {
    showToast('Комната полная');

    vi.advanceTimersByTime(4999);
    expect(texts()).toEqual(['Комната полная']);
    vi.advanceTimersByTime(1);
    expect(texts()).toEqual([]);
  });

  it('the same text does not pile up but stays longer', () => {
    showToast('Нет связи');
    vi.advanceTimersByTime(4000);
    showToast('Нет связи');

    expect(texts()).toEqual(['Нет связи']);
    vi.advanceTimersByTime(4000);
    expect(texts()).toEqual(['Нет связи']); // 8 s since the first one, 4 s since the second
    vi.advanceTimersByTime(1000);
    expect(texts()).toEqual([]);
  });

  it('different texts are shown together, and each can be closed', () => {
    showToast('Первая');
    showToast('Вторая');
    const [first] = useToastStore.getState().toasts;

    useToastStore.getState().dismiss(first.id);

    expect(texts()).toEqual(['Вторая']);
  });
});
