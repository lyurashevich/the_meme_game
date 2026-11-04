import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ServerMessage } from '../protocol';
import { ActionError, GameSocket, type ConnectionStatus } from './GameSocket';

// Stands in for the browser's WebSocket: records what is sent and lets the test
// play the server's part (open, receive a message, drop the connection).
class FakeSocket {
  url: string;
  sent: { event: string; request_id: string; payload: unknown }[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  send(data: string) {
    this.sent.push(JSON.parse(data));
  }

  close() {
    this.onclose?.();
  }

  // the server's side
  open() {
    this.onopen?.();
  }
  receive(message: object) {
    this.onmessage?.({ data: JSON.stringify(message) });
  }
  drop() {
    this.onclose?.();
  }
}

function setup(options: { url?: () => string } = {}) {
  const sockets: FakeSocket[] = [];
  const statuses: ConnectionStatus[] = [];
  const messages: ServerMessage[] = [];

  const client = new GameSocket({
    url: options.url ?? (() => 'ws://test/ws'),
    onStatus: (status) => statuses.push(status),
    onMessage: (message) => messages.push(message),
    createSocket: (url) => {
      const socket = new FakeSocket(url);
      sockets.push(socket);
      return socket as unknown as WebSocket;
    },
    random: () => 1, // no jitter: the delays are exactly 1 s, 2 s, 4 s...
  });

  const latest = () => sockets[sockets.length - 1];
  return { client, sockets, statuses, messages, latest };
}

function connected() {
  const env = setup();
  env.client.connect();
  env.latest().open();
  return env;
}

beforeEach(() => {
  vi.useFakeTimers(); // setTimeout only fires when the test moves the clock
});

afterEach(() => {
  vi.useRealTimers();
});

describe('connecting', () => {
  it('reports connecting, then online', () => {
    const { statuses } = connected();

    expect(statuses).toEqual(['connecting', 'online']);
  });

  it('a second connect() does not open a second socket', () => {
    const { client, sockets } = connected();

    client.connect();

    expect(sockets).toHaveLength(1);
  });
});

describe('actions', () => {
  it('sends the envelope and resolves with the ack payload', async () => {
    const { client, latest } = connected();

    const reply = client.send('join_room', { room_id: 'r1' });
    const sent = latest().sent[0];
    latest().receive({ event: 'ack', request_id: sent.request_id, payload: { room_id: 'r1' } });

    expect(sent).toEqual({ event: 'join_room', request_id: sent.request_id, payload: { room_id: 'r1' } });
    await expect(reply).resolves.toEqual({ room_id: 'r1' });
  });

  it('matches replies by request_id, whatever order they come in', async () => {
    const { client, latest } = connected();

    const first = client.send('chat_message', { text: 'one' });
    const second = client.send('join_room', { room_id: 'r2' });
    const [firstSent, secondSent] = latest().sent;
    latest().receive({ event: 'ack', request_id: secondSent.request_id, payload: { room_id: 'r2' } });
    latest().receive({ event: 'ack', request_id: firstSent.request_id, payload: {} });

    expect(firstSent.request_id).not.toEqual(secondSent.request_id);
    await expect(second).resolves.toEqual({ room_id: 'r2' });
    await expect(first).resolves.toEqual({});
  });

  it('rejects with the code and message from an error reply', async () => {
    const { client, latest } = connected();

    const reply = client.send('start_game', {});
    latest().receive({
      event: 'error',
      request_id: latest().sent[0].request_id,
      payload: { code: 'not_enough_players', message: 'Need at least 3 players' },
    });

    await expect(reply).rejects.toEqual(expect.objectContaining({ code: 'not_enough_players' }));
    await expect(reply).rejects.toBeInstanceOf(ActionError);
  });

  it('rejects right away when not connected', async () => {
    const { client, latest } = setup();
    client.connect(); // still connecting

    await expect(client.send('start_game', {})).rejects.toEqual(expect.objectContaining({ code: 'not_connected' }));
    expect(latest().sent).toHaveLength(0);
  });

  it('rejects when the server does not answer in time', async () => {
    const { client } = connected();

    const reply = client.send('start_game', {});
    vi.advanceTimersByTime(10_000);

    await expect(reply).rejects.toEqual(expect.objectContaining({ code: 'timeout' }));
  });

  it('rejects what is still waiting when the connection drops', async () => {
    const { client, latest } = connected();

    const reply = client.send('start_game', {});
    latest().drop();

    await expect(reply).rejects.toEqual(expect.objectContaining({ code: 'connection_lost' }));
  });
});

describe('events', () => {
  it('passes everything that is not a reply on', () => {
    const { latest, messages } = connected();

    latest().receive({ event: 'rooms_list', payload: [] });
    latest().receive({ event: 'ack', request_id: 'nobody-waits-for-this', payload: {} });

    expect(messages).toEqual([{ event: 'rooms_list', payload: [] }]);
  });
});

describe('reconnecting', () => {
  it('waits longer after every failure in a row, up to 30 s', () => {
    const { client, sockets, latest } = setup();
    client.connect();

    const waits: number[] = [];
    for (let i = 0; i < 7; i++) {
      latest().drop(); // the attempt failed
      const before = sockets.length;
      let waited = 0;
      while (sockets.length === before) {
        vi.advanceTimersByTime(500);
        waited += 500;
      }
      waits.push(waited);
    }

    expect(waits).toEqual([1000, 2000, 4000, 8000, 16000, 30000, 30000]);
  });

  it('starts from the short delay again once a connection succeeded', () => {
    const { client, sockets, latest } = setup();
    client.connect();
    latest().drop();
    vi.advanceTimersByTime(1000);
    latest().drop();
    vi.advanceTimersByTime(2000); // two failures: the next wait would be 4 s

    latest().open();
    latest().drop();
    vi.advanceTimersByTime(1000);

    expect(sockets).toHaveLength(4);
  });

  it('asks for the url again, so a new reconnect token is used', () => {
    let token = 'old';
    const { client, sockets, latest } = setup({ url: () => `ws://test/ws?reconnect_token=${token}` });
    client.connect();
    latest().open();

    token = 'new';
    latest().drop();
    vi.advanceTimersByTime(1000);

    expect(sockets.map((socket) => socket.url)).toEqual([
      'ws://test/ws?reconnect_token=old',
      'ws://test/ws?reconnect_token=new',
    ]);
  });

  it('does not reconnect after close()', () => {
    const { client, sockets, statuses } = connected();

    client.close();
    vi.advanceTimersByTime(60_000);

    expect(sockets).toHaveLength(1);
    expect(statuses.at(-1)).toBe('offline');
  });
});
