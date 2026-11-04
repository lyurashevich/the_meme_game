import { describe, expect, it } from 'vitest';
import type { ChatMessage, RoomState, RoomSummary, Session } from '../protocol';
import { applyServerMessage, type GameData } from './gameStore';

const session = (player_id = 'p1'): Session => ({
  player_id,
  reconnect_token: 'token',
  username: 'Neo',
  avatar_id: 'cat',
});

const chatMessage = (text: string): ChatMessage => ({
  player_id: 'p2',
  username: 'Trinity',
  text,
  timestamp: '2026-11-03T12:00:00Z',
});

const roomState = (roomId: string, chat?: ChatMessage[]): RoomState => ({
  server_time: '2026-11-03T12:00:00Z',
  room: {
    id: roomId,
    name: 'Room',
    owner_id: 'p1',
    max_players: 10,
    settings: { round_time_limit: 60, max_rounds: null, score_to_win: null },
  },
  players: [],
  game: null,
  ...(chat ? { chat } : {}),
});

const ROOMS: RoomSummary[] = [];

const data = (changes: Partial<GameData> = {}): GameData => ({
  connection: 'online',
  me: session(),
  rooms: [],
  roomState: null,
  roundWinner: null,
  gameEnded: null,
  syncing: false,
  ...changes,
});

// Apply the message the way the store does: merge the changes into the old data
const apply = (before: GameData, message: Parameters<typeof applyServerMessage>[1]): GameData => ({
  ...before,
  ...applyServerMessage(before, message),
});

describe('room_state and the chat', () => {
  it('takes the history from the first snapshot', () => {
    const after = apply(data(), { event: 'room_state', payload: roomState('r1', [chatMessage('hi')]) });

    expect(after.roomState?.chat).toEqual([chatMessage('hi')]);
  });

  it('keeps the chat when later snapshots come without it', () => {
    const before = data({ roomState: roomState('r1', [chatMessage('hi')]) });

    const after = apply(before, { event: 'room_state', payload: roomState('r1') });

    expect(after.roomState?.chat).toEqual([chatMessage('hi')]);
  });

  it("doesn't carry the chat over to another room", () => {
    const before = data({ roomState: roomState('r1', [chatMessage('hi')]) });

    const after = apply(before, { event: 'room_state', payload: roomState('r2') });

    expect(after.roomState?.chat).toEqual([]);
  });

  it('appends new messages, keeping the latest 100', () => {
    let state = data({ roomState: roomState('r1', []) });
    for (let i = 0; i < 105; i++) {
      state = apply(state, { event: 'chat_message', payload: chatMessage(`m${i}`) });
    }

    expect(state.roomState?.chat).toHaveLength(100);
    expect(state.roomState?.chat?.at(-1)?.text).toBe('m104');
    expect(state.roomState?.chat?.[0].text).toBe('m5');
  });
});

describe('where the player is', () => {
  it('leaving the room clears it', () => {
    const after = apply(data({ roomState: roomState('r1') }), { event: 'you_left_room', payload: { room_id: 'r1' } });

    expect(after.roomState).toBeNull();
  });

  it('leaving the room forgets the results of its last game', () => {
    const before = data({
      roomState: roomState('r1'),
      gameEnded: { room_id: 'r1', reason: 'owner_ended', final_scores: {}, winner_ids: [] },
    });

    const after = apply(before, { event: 'you_left_room', payload: { room_id: 'r1' } });

    expect(after.gameEnded).toBeNull();
  });

  it('the room list on its own does not take the player out of the room', () => {
    const after = apply(data({ roomState: roomState('r1') }), { event: 'rooms_list', payload: ROOMS });

    expect(after.roomState).not.toBeNull();
  });

  it('after a reconnect, the room list instead of the room means the room is gone', () => {
    let state = data({ roomState: roomState('r1') });

    state = apply(state, { event: 'session', payload: session('p1') });
    state = apply(state, { event: 'rooms_list', payload: ROOMS });

    expect(state.roomState).toBeNull();
    expect(state.syncing).toBe(false);
  });

  it('after a reconnect into the same room, everything stays', () => {
    let state = data({ roomState: roomState('r1', [chatMessage('hi')]) });

    state = apply(state, { event: 'session', payload: session('p1') });
    state = apply(state, { event: 'room_state', payload: roomState('r1', [chatMessage('hi')]) });
    state = apply(state, { event: 'rooms_list', payload: ROOMS }); // a later list changes nothing

    expect(state.roomState?.room.id).toBe('r1');
  });

  it('a new player id (the old session expired) starts from scratch', () => {
    const before = data({
      roomState: roomState('r1'),
      gameEnded: { room_id: 'r1', reason: 'owner_ended', final_scores: {}, winner_ids: [] },
    });

    const after = apply(before, { event: 'session', payload: session('p-new') });

    expect(after.me?.player_id).toBe('p-new');
    expect(after.roomState).toBeNull();
    expect(after.gameEnded).toBeNull();
    expect(after.connection).toBe('online');
  });
});
