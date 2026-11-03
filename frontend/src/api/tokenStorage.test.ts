import { describe, expect, it } from 'vitest';
import { createTokenStorage } from './tokenStorage';

// sessionStorage with nothing but the Storage methods we use
class FakeStorage {
  items = new Map<string, string>();
  getItem(key: string) {
    return this.items.get(key) ?? null;
  }
  setItem(key: string, value: string) {
    this.items.set(key, value);
  }
  removeItem(key: string) {
    this.items.delete(key);
  }
}

const fakeStorage = () => new FakeStorage() as FakeStorage & Storage;

function pageEvent(type: string, persisted = false) {
  return Object.assign(new Event(type), { persisted });
}

describe('token storage', () => {
  it('a reload gets the token back', () => {
    const storage = fakeStorage();
    const page = new EventTarget();
    createTokenStorage(storage, page).set('t1');

    page.dispatchEvent(pageEvent('pagehide')); // reloading
    const afterReload = createTokenStorage(storage, new EventTarget());

    expect(afterReload.get()).toBe('t1');
  });

  it('a duplicate of an open tab gets no token', () => {
    const storage = fakeStorage();
    storage.setItem('reconnect_token', 't1'); // left by the previous load of this tab
    const original = createTokenStorage(storage, new EventTarget());

    // "Duplicate tab" copies the storage as it is now
    const copy = fakeStorage();
    storage.items.forEach((value, key) => copy.setItem(key, value));
    const duplicate = createTokenStorage(copy, new EventTarget());

    expect(original.get()).toBe('t1');
    expect(duplicate.get()).toBeNull();
  });

  it('a page restored from the back/forward cache takes the token out of the storage again', () => {
    const storage = fakeStorage();
    const page = new EventTarget();
    createTokenStorage(storage, page).set('t1');

    page.dispatchEvent(pageEvent('pagehide'));
    page.dispatchEvent(pageEvent('pageshow', true));

    expect(storage.getItem('reconnect_token')).toBeNull();
  });
});
