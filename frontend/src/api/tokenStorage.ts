// Where the reconnect token lives between page loads.
//
// The storage is given by the caller: localStorage (shared by the site's tabs, so a closed tab can be
// opened again as the same player) or sessionStorage (one per tab, so every tab is its own player).
//
// Either way two open tabs must never share a token: they would be one player fighting over a single
// connection. A second tab sees the shared localStorage, and "Duplicate tab" copies sessionStorage.
// So while the page is open the token is kept only in memory and written to the storage just as the
// page goes away (reload, close, navigating off). A tab opened meanwhile finds nothing and becomes a
// new player.

const TOKEN_KEY = 'reconnect_token';

export interface TokenStorage {
  get: () => string | null;
  set: (token: string) => void;
}

export function createTokenStorage(storage: Storage, page: EventTarget): TokenStorage {
  let token = storage.getItem(TOKEN_KEY);
  storage.removeItem(TOKEN_KEY); // claimed by this page

  // pagehide: the page is being left. pageshow with `persisted`: the browser brought the very same
  // page back from its back/forward cache, so it takes the token back out of the storage again.
  page.addEventListener('pagehide', () => {
    if (token) storage.setItem(TOKEN_KEY, token);
  });
  page.addEventListener('pageshow', (event) => {
    if ((event as PageTransitionEvent).persisted) storage.removeItem(TOKEN_KEY);
  });

  return {
    get: () => token,
    set: (newToken) => {
      token = newToken;
    },
  };
}
