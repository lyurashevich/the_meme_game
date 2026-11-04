// The connection to the game server. Knows nothing about React or the screens:
// it keeps the socket open, reconnects when it drops, and pairs every action
// with the server's reply to it.
import type { ActionName, Actions, ErrorPayload, ServerMessage } from '../protocol';

export type ConnectionStatus = 'connecting' | 'online' | 'offline';

// The server answered an action with `error`, or there was no answer at all
export class ActionError extends Error {
  readonly code: string;
  readonly details?: unknown[];

  constructor({ code, message, details }: ErrorPayload) {
    super(message);
    this.name = 'ActionError';
    this.code = code;
    this.details = details;
  }
}

const RECONNECT_BASE_DELAY_MS = 1000;
const RECONNECT_MAX_DELAY_MS = 30_000;
const ACTION_TIMEOUT_MS = 10_000;

interface PendingAction {
  resolve: (result: unknown) => void;
  reject: (error: ActionError) => void;
  timer: ReturnType<typeof setTimeout>;
}

export interface GameSocketOptions {
  url: () => string; // asked again before every attempt: the reconnect token may have changed
  onMessage: (message: ServerMessage) => void; // every event that is not a reply to an action
  onStatus: (status: ConnectionStatus) => void;
  createSocket?: (url: string) => WebSocket; // tests pass a fake one
  random?: () => number;
}

export class GameSocket {
  private socket: WebSocket | null = null;
  private status: ConnectionStatus = 'offline';
  private attempt = 0; // failed attempts in a row, for the backoff
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closedByUs = false;
  private lastRequestId = 0;
  private pending = new Map<string, PendingAction>();
  private readonly options: GameSocketOptions;

  constructor(options: GameSocketOptions) {
    this.options = options;
  }

  connect(): void {
    if (this.socket) return; // already connected or connecting
    this.closedByUs = false;
    this.setStatus('connecting');

    const createSocket = this.options.createSocket ?? ((url) => new WebSocket(url));
    const socket = createSocket(this.options.url());
    this.socket = socket;

    socket.onopen = () => {
      this.attempt = 0;
      this.setStatus('online');
    };
    socket.onmessage = (event) => this.handleMessage(event.data);
    // onclose comes after a failed attempt too, so reconnecting is handled in one place
    socket.onclose = () => {
      if (this.socket !== socket) return;
      this.socket = null;
      this.failPending('connection_lost', 'Связь с сервером прервалась');
      this.setStatus('offline');
      if (!this.closedByUs) this.scheduleReconnect();
    };
  }

  // For trying things out: break the connection the way a lost network would, so it reconnects
  simulateDrop(): void {
    this.socket?.close();
  }

  close(): void {
    this.closedByUs = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.socket?.close();
  }

  // Send an action and wait for its ack. The generic parameter ties the event name
  // to its payload and result: send('join_room', { room_id }) resolves to { room_id }.
  send<E extends ActionName>(event: E, payload: Actions[E]['payload']): Promise<Actions[E]['result']> {
    const socket = this.socket;
    if (!socket || this.status !== 'online') {
      return Promise.reject(new ActionError({ code: 'not_connected', message: 'Нет связи с сервером' }));
    }

    // Unique within the page, that's all the server needs: it only echoes it back
    const requestId = String(++this.lastRequestId);

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(requestId);
        reject(new ActionError({ code: 'timeout', message: 'Сервер не ответил' }));
      }, ACTION_TIMEOUT_MS);

      this.pending.set(requestId, { resolve: resolve as (result: unknown) => void, reject, timer });
      socket.send(JSON.stringify({ event, request_id: requestId, payload }));
    });
  }

  private handleMessage(data: unknown): void {
    let message: ServerMessage;
    try {
      message = JSON.parse(String(data));
    } catch {
      console.error('Not a JSON message from the server', data);
      return;
    }

    if (message.event === 'ack' || message.event === 'error') {
      const pending = message.request_id ? this.pending.get(message.request_id) : undefined;
      if (!pending) {
        // e.g. the action already timed out, or the server couldn't read the request at all
        if (message.event === 'error') console.error('Server error', message.payload);
        return;
      }
      this.pending.delete(message.request_id!);
      clearTimeout(pending.timer);
      if (message.event === 'ack') pending.resolve(message.payload);
      else pending.reject(new ActionError(message.payload));
      return;
    }

    this.options.onMessage(message);
  }

  // Wait longer after every failure in a row: 1 s, 2 s, 4 s ... up to 30 s. The random part
  // keeps a crowd of clients from knocking on a restarted server all at the same moment.
  private scheduleReconnect(): void {
    const random = this.options.random ?? Math.random;
    const delay = Math.min(RECONNECT_MAX_DELAY_MS, RECONNECT_BASE_DELAY_MS * 2 ** this.attempt);
    this.attempt += 1;
    this.reconnectTimer = setTimeout(
      () => {
        this.reconnectTimer = null;
        this.connect();
      },
      delay * (0.5 + random() / 2),
    );
  }

  private failPending(code: string, message: string): void {
    for (const { reject, timer } of this.pending.values()) {
      clearTimeout(timer);
      reject(new ActionError({ code, message }));
    }
    this.pending.clear();
  }

  private setStatus(status: ConnectionStatus): void {
    this.status = status;
    this.options.onStatus(status);
  }
}
