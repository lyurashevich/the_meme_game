// Where the reconnect token lives between page loads.
//
// sessionStorage belongs to one tab, so every tab is its own player, and a reload keeps the player.
// One catch: "Duplicate tab" copies sessionStorage, and two tabs with one token would be one player
// fighting over a single connection. So while the page is open the token is kept only in memory and
// written to the storage just as the page goes away (reload, close, navigating off). A duplicate of a
// live tab then finds nothing and becomes a new player.

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
